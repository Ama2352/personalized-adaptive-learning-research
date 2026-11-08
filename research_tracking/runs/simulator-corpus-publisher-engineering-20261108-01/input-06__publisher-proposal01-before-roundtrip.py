"""Publish ba research roles đã có; không collect/train hoặc cấp quyền thực thi.

DONE là logical completion marker, không filesystem transaction/crash guarantee.
Provenance là consistency binding trên caller/workspace hợp tác, không attestation.
"""
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import time

from .akt.resources import memory_snapshot
from .simulator_bridge import SimulatorBank, SimulatorItem, identity_hash
from .simulator_data import ObservableTrajectory
from .simulator_research_collection import (COLLECTOR_PATH, COLLECTOR_VERSION, EVENT_STRIDE,
    PROTOCOL_PATH, ResearchCollectionLimits, ResearchCollectionRecipe,
    ResearchCollectionResult, source_inventory)
from .simulator_research_data import (DEVELOPMENT_ROLES, PROTOCOL_ID, ResearchSplitPlan,
    ResearchProvenance, ShardLimits, audit_research_shard)

ROOT = Path(__file__).resolve().parents[2]
PUBLISHER_PATH = 'src/knowledge_tracing/simulator_corpus_publisher.py'
PUBLISHER_VERSION = 'simulator-corpus-publisher-v1'
INPUT_NAMES = ('corpus.json', 'bank.json', 'plan.json', 'train.jsonl', 'train.manifest.json',
               'selection.jsonl', 'selection.manifest.json', 'calibration.jsonl', 'calibration.manifest.json')


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(value):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'lowercase SHA256 required')


def _same(left, right):
    return identity_hash(left) == identity_hash(right)


def _digest(payload):
    return hashlib.sha256(payload).hexdigest()


def _alias(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def _path(relative):
    _require(type(relative) is str and '\\' not in relative and ':' not in relative, 'relative POSIX path required')
    parts = PurePosixPath(relative)
    _require(parts.parts and not parts.is_absolute() and '..' not in parts.parts
             and parts.as_posix() == relative, 'unsafe publication path')
    _require(ROOT.is_dir() and not _alias(ROOT) and ROOT.resolve() == ROOT.absolute(), 'physical fixed ROOT required')
    cursor = ROOT
    for part in parts.parts:
        cursor = cursor / part
        _require(not _alias(cursor), 'publication/source path alias forbidden')
    return cursor


@dataclass(frozen=True)
class CorpusPublicationLimits:
    max_file_bytes: int
    max_total_bytes: int
    max_oracle_bytes: int
    shard_limits: ShardLimits
    max_wall_seconds: float
    max_rss_bytes: int
    min_available_ram_bytes: int

    def __post_init__(self):
        _require(type(self.shard_limits) is ShardLimits, 'explicit typed shard limits required')
        ShardLimits(**asdict(self.shard_limits))
        for value in (self.max_file_bytes, self.max_total_bytes, self.max_oracle_bytes,
                      self.max_rss_bytes, self.min_available_ram_bytes):
            _require(type(value) is int and 0 < value < 2**63, 'explicit positive byte/resource caps required')
        _require(self.max_file_bytes <= self.max_total_bytes and self.max_oracle_bytes <= self.max_total_bytes,
                 'file/oracle caps exceed total publication cap')
        _require(type(self.max_wall_seconds) in (int, float) and math.isfinite(self.max_wall_seconds)
                 and 0 < self.max_wall_seconds <= 600, 'bounded explicit publication wall cap required')
        _require(64*1024**2 <= self.max_rss_bytes <= 2*1024**3
                 and self.min_available_ram_bytes >= 1024**3, 'publication retains RSS/free-RAM safeguards')


@dataclass(frozen=True)
class CorpusPublicationReceipt:
    corpus_id: str
    corpus_path: str
    corpus_sha256: str
    done_sha256: str
    files: tuple[tuple[str, str, int], ...]
    audit_json: str
    source_inventory_json: str
    publisher_sha256: str
    elapsed_seconds: float
    status: str = field(default='PUBLISHED_OBSERVABLE_CORPUS_NOT_MODEL_FITTED', init=False)

    def payload(self):
        return json.loads(json.dumps(asdict(self), allow_nan=False))

    @property
    def identity(self):
        return identity_hash(self.payload())


class CorpusPublicationFailure(RuntimeError):
    def __init__(self, cause, receipt):
        super().__init__(str(cause))
        self.receipt = receipt


def _guard(started, limits):
    if time.perf_counter() - started >= limits.max_wall_seconds:
        raise TimeoutError('publisher cooperative wall cap')
    sample = memory_snapshot()
    rss, peak, available = (sample['process_rss_bytes'], sample['process_peak_rss_bytes'],
                            sample['system_available_ram_bytes'])
    _require(type(rss) is int and rss >= 0 and type(available) is int and available >= 0
             and (peak is None or type(peak) is int and peak >= 0), 'unknown/invalid publication memory telemetry')
    if max(rss, peak or 0) > limits.max_rss_bytes:
        raise MemoryError('publisher RSS cap')
    if available < limits.min_available_ram_bytes:
        raise MemoryError('publisher free-RAM floor')
    if time.perf_counter() - started >= limits.max_wall_seconds:
        raise TimeoutError('publisher wall cap after telemetry')


def _current_sources(expected, protocol_sha):
    _require(type(expected) is dict and expected, 'externally pinned collection sources required')
    for name, digest in expected.items():
        _sha(digest)
        path = _path(name)
        _require(path.is_file(), 'regular pinned collection source required')
    _require(source_inventory() == expected and expected.get(PROTOCOL_PATH) == protocol_sha,
             'collection source/protocol drift')
    _require(_digest(_path(PROTOCOL_PATH).read_bytes()) == protocol_sha, 'actual protocol bytes mismatch')
    writer = _path(PUBLISHER_PATH)
    _require(writer.is_file(), 'regular publisher source required')
    return _digest(writer.read_bytes())


def _validate_results(plan, results, expected_sources, limits, started):
    _require(type(plan) is ResearchSplitPlan and type(results) is dict
             and set(results) == set(DEVELOPMENT_ROLES), 'typed plan and exact three development roles required')
    fresh = ResearchSplitPlan(plan.namespace, plan.root_seed, plan.development_learners,
                             plan.final_learners, plan.protocol_sha256)
    _require(_same(plan.manifest(), fresh.manifest()), 'plan/seed assignment drift')
    assignments = fresh.split_plan.assignments()
    by_learner = {a.learner_id: a for a in assignments}
    ordinal = {a.learner_id: i for i, a in enumerate(assignments)}
    total = 0
    rows_seen = set()
    audits, profiles_by_role, normalized = {}, {}, None
    bank, graph, semantics = None, None, None
    for role in DEVELOPMENT_ROLES:
        _guard(started, limits)
        result = results[role]
        _require(type(result) is ResearchCollectionResult and type(result.bank) is SimulatorBank
                 and type(result.provenance) is ResearchProvenance and type(result.trajectories) is tuple
                 and type(result.manifest) is dict and type(result.oracle_sidecar) is dict,
                 'exact typed collection result/observable metadata required')
        _require(type(result.bank.items) is tuple and all(type(i) is SimulatorItem for i in result.bank.items),
                 'exact bank item schema required')
        SimulatorBank(result.bank.environment_id, tuple(SimulatorItem(**asdict(i)) for i in result.bank.items))
        manifest, provenance = result.manifest, result.provenance
        _require(manifest.get('schema_version') == 1 and type(manifest.get('schema_version')) is int
                 and manifest.get('status') == 'COMPLETE_REQUESTED_ROLE_NOT_MODEL_FITTED'
                 and manifest.get('role') == role and manifest.get('collector_version') == COLLECTOR_VERSION,
                 'complete matching collector role/version required')
        _require(_same(manifest.get('sources_before'), expected_sources)
                 and _same(manifest.get('sources_after'), expected_sources), 'collector source inventory mismatch')
        _require(manifest.get('plan_sha256') == fresh.identity
                 and _same(manifest.get('domain'), result.bank.identity)
                 and _same(manifest.get('provenance'), asdict(provenance))
                 and manifest.get('provenance_sha256') == provenance.identity
                 and manifest.get('logging_policy_oracle_access') is False, 'collector plan/domain/provenance mismatch')
        recipe = ResearchCollectionRecipe(**manifest['recipe'])
        current_recipe = dict(collector_version=COLLECTOR_VERSION, **asdict(recipe),
                              timestamp_unit='unix_seconds_utc', timezone='UTC')
        if normalized is None:
            normalized, bank = current_recipe, result.bank
            graph, semantics = manifest['environment_graph_sha256'], manifest['environment_semantics']
        _require(_same(current_recipe, normalized) and _same(result.bank.identity, bank.identity)
                 and manifest['environment_graph_sha256'] == graph
                 and _same(manifest['environment_semantics'], semantics), 'cross-role bank/graph/normalized recipe mismatch')
        _require(provenance.environment_graph_sha256 == graph
                 and dict(provenance.source_bindings) == dict(collector=expected_sources[COLLECTOR_PATH],
                      environment=identity_hash(semantics), source_inventory=identity_hash(expected_sources))
                 and provenance.collection_policy_id == COLLECTOR_VERSION + ':' + recipe.policy,
                 'source/world/policy provenance mismatch')
        sidecar = result.oracle_sidecar
        _require(set(sidecar) == {'scope', 'learners'} and type(sidecar['learners']) is dict
                 and sidecar['scope'] == 'oracle evaluation only; forbidden as model features'
                 and identity_hash(sidecar) == manifest.get('oracle_sidecar_sha256'), 'oracle sidecar identity/schema mismatch')
        expected_learners = {a.learner_id for a in assignments if a.role == role}
        _require(set(sidecar['learners']) == expected_learners, 'oracle learner/role population mismatch')
        profiles = {learner: sidecar['learners'][learner]['profile'] for learner in expected_learners}
        _require(all(type(p) is str and p.strip() for p in profiles.values()), 'explicit role profiles required')
        profiles_by_role[role] = identity_hash(profiles)
        composite = identity_hash(dict(recipe=asdict(recipe), recipe_sha256=recipe.identity,
                                      profile_metadata_sha256=identity_hash(profiles)))
        _require(manifest.get('profile_metadata_sha256') == identity_hash(profiles)
                 and manifest.get('recipe_sha256') == composite and provenance.collection_recipe_sha256 == composite,
                 'role profile/composite recipe binding mismatch')
        _require(len(result.trajectories) <= limits.shard_limits.max_learners, 'publisher learner cap')
        count = 0
        for trajectory in result.trajectories:
            _guard(started, limits)
            _require(type(trajectory) is ObservableTrajectory, 'exact observable trajectory required')
            _require(len(trajectory.observations) == recipe.events_per_learner
                     and len(trajectory.observations) <= limits.shard_limits.max_events_per_learner,
                     'recipe/per-learner event cap mismatch')
            ObservableTrajectory.from_payload(asdict(trajectory))
            learner = trajectory.learner_id
            _require(learner in expected_learners, 'foreign/final observable learner')
            details = sidecar['learners'][learner]
            _require(_same(details['assignment'], asdict(by_learner[learner]))
                     and type(details['events']) is list
                     and len(details['events']) == len(trajectory.observations), 'oracle assignment/event population mismatch')
            for rank, (observation, detail) in enumerate(zip(trajectory.observations, details['events'])):
                query = observation.query
                _require(query.timestamp == recipe.start_unix_seconds + (rank + 1)*recipe.gap_seconds
                         and query.source_row == ordinal[learner]*EVENT_STRIDE + rank + 1
                         and query.source_row not in rows_seen, 'observable clock/source-row drift or collision')
                _require(_same(detail['query'], asdict(query))
                         and type(detail['oracle_result']['y']) is int
                         and detail['oracle_result']['y'] == observation.correct, 'observable/oracle query/outcome mismatch')
                rows_seen.add(query.source_row)
                count += 1
            total += len(trajectory.observations)
            _require(total <= limits.shard_limits.max_total_events, 'publisher total event cap')
        original_limits = ResearchCollectionLimits(**manifest['limits'])
        audit = audit_research_shard(result.trajectories, plan=fresh, bank=bank, role=role,
            provenance=provenance, expected_provenance_sha256=provenance.identity,
            limits=original_limits.shard_limits(), reference_items=bank.item_ids)
        _require(_same(audit, manifest['audit']), 'collector audit drift')
        _require(audit['reference_complete'] is True, 'complete reference coverage required for publication')
        for name in ('interact_attempts', 'interact_returns', 'completed_events'):
            _require(type(manifest.get(name)) is int and manifest[name] == count, 'collector event counters incomplete')
        _require(type(manifest.get('completed_learners')) is int
                 and manifest['completed_learners'] == len(expected_learners), 'collector learner counters incomplete')
        audits[role] = audit
    return fresh, bank, graph, normalized, profiles_by_role, audits


def _seal(value, *, jsonl, started, limits):
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    buffer = bytearray()
    checked = 0
    for row in value if jsonl else (value,):
        for chunk in encoder.iterencode(row):
            encoded = chunk.encode('utf-8')
            _require(len(buffer) + len(encoded) + 1 <= limits.max_file_bytes, 'publication file byte cap')
            buffer.extend(encoded)
            if len(buffer) - checked >= 65536:
                _guard(started, limits)
                checked = len(buffer)
        buffer.extend(b'\n')
    _guard(started, limits)
    return bytes(buffer)


def _write_file(path, payload):
    import os
    with path.open('xb') as stream:
        _require(stream.write(payload) == len(payload), 'short publication write')
        stream.flush()
        os.fsync(stream.fileno())


def _readback(path, payload):
    _require(path.is_file() and not _alias(path), 'regular published file required')
    with path.open('rb') as stream:
        current = stream.read(len(payload) + 1)
    _require(len(current) == len(payload) and _digest(current) == _digest(payload), 'publication readback SHA/size mismatch')


def publish_research_corpus(plan, results_by_role, *, corpus_id, expected_sources,
                            expected_protocol_sha256, limits):
    """Giữ directory partial khi lỗi; không resume/overwrite hoặc collect thêm."""
    started = time.perf_counter()
    owned, done_created, base = False, False, None
    stage, written, sources_before, writer_sha = 'prevalidate', [], {}, None
    try:
        _require(type(limits) is CorpusPublicationLimits, 'explicit publisher limits required')
        CorpusPublicationLimits(**{**asdict(limits), 'shard_limits': limits.shard_limits})
        _require(type(corpus_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', corpus_id), 'safe corpus ID required')
        _sha(expected_protocol_sha256)
        relative = 'artifacts/simulator/corpora/' + corpus_id
        base = _path(relative)
        _require(not base.exists(), 'existing corpus/partial cannot be overwritten or retried')
        _guard(started, limits)
        _require(type(expected_sources) is dict, 'exact external source inventory required')
        sources_before = dict(expected_sources)
        writer_sha = _current_sources(sources_before, expected_protocol_sha256)
        _require(type(plan) is ResearchSplitPlan and plan.protocol_sha256 == expected_protocol_sha256,
                 'plan actual protocol binding mismatch')
        plan, bank, graph, recipe, profiles, audits = _validate_results(plan, results_by_role, sources_before, limits, started)
        sealed = {}
        def add(name, value, *, jsonl=False):
            payload = _seal(value, jsonl=jsonl, started=started, limits=limits)
            total = sum(len(p) for p in sealed.values()) + len(payload)
            oracle = sum(len(p) for n, p in sealed.items() if n.startswith('oracle/'))
            if name.startswith('oracle/'):
                oracle += len(payload)
            _require(total <= limits.max_total_bytes and oracle <= limits.max_oracle_bytes,
                     'total/oracle publication byte cap')
            sealed[name] = payload
        add('bank.json', dict(schema_version=1, environment_id=bank.environment_id,
                              items=[asdict(i) for i in sorted(bank.items, key=lambda i: i.item_id)]))
        add('plan.json', dict(schema_version=1, manifest=plan.manifest()))
        roles = {}
        for role in DEVELOPMENT_ROLES:
            result = results_by_role[role]
            trajectories = sorted(result.trajectories, key=lambda row: row.learner_id)
            add(role+'.jsonl', (asdict(row) for row in trajectories), jsonl=True)
            target_count = sum(len(row.observations) for row in trajectories)
            manifest = dict(schema_version=1, role=role, research_plan_sha256=plan.identity,
                domain_sha256=identity_hash(bank.identity), environment_graph_sha256=graph,
                normalized_recipe_sha256=identity_hash(recipe), source_inventory_sha256=identity_hash(sources_before),
                profile_sha256=profiles[role], learner_ids=[row.learner_id for row in trajectories], targets=target_count,
                observable_sha256=_digest(sealed[role+'.jsonl']), timestamp_unit='unix_seconds_utc', timezone='UTC',
                logging_policy_oracle_access=False)
            add(role+'.manifest.json', manifest)
            roles[role] = dict(observable_file=role+'.jsonl', observable_sha256=_digest(sealed[role+'.jsonl']),
                manifest_file=role+'.manifest.json', manifest_sha256=_digest(sealed[role+'.manifest.json']),
                learners=len(trajectories), targets=target_count, profile_sha256=profiles[role])
            add('oracle/'+role+'.json', result.oracle_sidecar)
            add('oracle/'+role+'.collection.json', result.manifest)
        corpus = dict(schema_version=1, domain='simulator', no_junyi_fold=True, protocol_id=PROTOCOL_ID,
            protocol_sha256=expected_protocol_sha256, bank_sha256=_digest(sealed['bank.json']),
            domain_sha256=identity_hash(bank.identity), plan_sha256=_digest(sealed['plan.json']),
            research_plan_sha256=plan.identity, environment_graph_sha256=graph, normalized_recipe=recipe,
            normalized_recipe_sha256=identity_hash(recipe), source_inventory=sources_before, roles=roles)
        add('corpus.json', corpus)
        add('oracle/publication-inventory.json', dict(schema_version=1, publisher_version=PUBLISHER_VERSION,
            publisher_sha256=writer_sha, source_inventory=sources_before, audits=audits,
            files={name:dict(sha256=_digest(p), bytes=len(p)) for name,p in sorted(sealed.items())},
            scope='publication/coverage only; not corpus diversity, model fit, or execution authority'))
        add('DONE.json', dict(schema_version=1, status='COMPLETE_SIMULATOR_CORPUS',
            corpus_sha256=_digest(sealed['corpus.json']),
            files_sha256={name:_digest(sealed[name]) for name in INPUT_NAMES}))
        _require(_current_sources(sources_before, expected_protocol_sha256) == writer_sha, 'publisher/source drift before mkdir')
        _guard(started, limits)
        stage = 'write'
        _path(relative).parent.mkdir(parents=True, exist_ok=True)
        base = _path(relative)
        base.mkdir(exist_ok=False)
        owned = True
        (base/'oracle').mkdir()
        for name, payload in sealed.items():
            if name == 'DONE.json':
                continue
            _guard(started, limits)
            path = _path(relative+'/'+name)
            _write_file(path, payload)
            written.append(dict(path=name,sha256=_digest(payload),bytes=len(payload)))
            _readback(path,payload)
        stage = 'commit'
        for name, payload in sealed.items():
            if name != 'DONE.json':
                _readback(_path(relative+'/'+name),payload)
        _require({p.relative_to(base).as_posix() for p in base.rglob('*')}
                 == (set(sealed)-{'DONE.json'})|{'oracle'}, 'unexpected file/directory before DONE')
        _require(_current_sources(sources_before, expected_protocol_sha256) == writer_sha, 'publisher/source drift before DONE')
        # All potentially expensive readback/source/resource checks precede marker.
        audit_json = json.dumps(audits,sort_keys=True,allow_nan=False,separators=(',',':'))
        sources_json = json.dumps(sources_before,sort_keys=True,separators=(',',':'))
        files = tuple((name,_digest(payload),len(payload)) for name,payload in sorted(sealed.items()))
        _guard(started,limits)
        stage = 'DONE'
        _write_file(_path(relative+'/DONE.json'),sealed['DONE.json'])
        done_created = True
        _readback(_path(relative+'/DONE.json'),sealed['DONE.json'])
        elapsed = time.perf_counter()-started
        if elapsed >= limits.max_wall_seconds:
            raise TimeoutError('publisher final wall cap after DONE')
        return CorpusPublicationReceipt(corpus_id,relative,_digest(sealed['corpus.json']),
            _digest(sealed['DONE.json']),files,audit_json,sources_json,writer_sha,elapsed)
    except Exception as error:
        receipt = dict(status='FAILED_NO_USABLE_CORPUS',corpus_id=corpus_id,stage=stage,
            original_error_type=type(error).__name__,error=str(error),files_written=written,
            source_inventory=sources_before,publisher_sha256=writer_sha,
            owned_directory=owned,done_created=done_created,elapsed_seconds=time.perf_counter()-started,
            rollback=False,automatic_retry=False,model_or_collector_calls=0)
        if owned:
            try:
                payload=(json.dumps(receipt,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
                _write_file(_path(base.relative_to(ROOT).as_posix()+'/failure.json'),payload)
                receipt['failure_receipt_persisted']=True
            except Exception as failure_error:
                receipt['failure_receipt_persisted']=False
                receipt['failure_receipt_error_type']=type(failure_error).__name__
        raise CorpusPublicationFailure(error,receipt) from error
