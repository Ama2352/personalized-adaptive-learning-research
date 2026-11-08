"""Requested-role research collector using Paper2 equations, not fixture caps.

No final-event collection, estimator/model, fitted-role promotion or output writes.
Limits are cooperative checks, not a hard process quota/kill guarantee. Frozen
fixture code is reused only for semantic/provenance helpers, never its generator.
"""
from dataclasses import asdict, dataclass
import csv
import hashlib
import math
from pathlib import Path
import struct
import time

import numpy as np
import pandas as pd

from .akt.resources import memory_snapshot
from .paper2_reference import ROOT, PACKAGE, NOTEBOOK, load_reference
from .simulator_bridge import ItemQuery, Observation, SimulatorBank, SimulatorItem, identity_hash
from .simulator_collection import canonical_source_provenance, environment_semantics
from .simulator_data import ObservableTrajectory
from .simulator_research_data import (DEVELOPMENT_ROLES, ResearchSplitPlan, ResearchProvenance,
                                      ShardLimits, audit_research_shard)

COLLECTOR_VERSION = 'paper2-research-role-collector-v1'
RNG_NAMESPACE = COLLECTOR_VERSION + ':independent-channels'
EVENT_STRIDE = 1000000  # Stable address slots, not an adopted trajectory length.
MAX_SOURCE_ROW = 2**63 - 1
MAX_UNIX_SECONDS = pd.Timestamp.max.value // 1000000000
PROTOCOL_PATH = 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'
COLLECTOR_PATH = 'src/knowledge_tracing/simulator_research_collection.py'


def source_inventory():
    """Fixed local source allowlist; expected digests must be supplied separately."""
    paths = [NOTEBOOK, ROOT/PROTOCOL_PATH, Path(__file__),
             ROOT/'src/knowledge_tracing/paper2_reference.py',
             ROOT/'src/knowledge_tracing/simulator_collection.py',
             ROOT/'src/knowledge_tracing/simulator_research_data.py',
             ROOT/'src/knowledge_tracing/simulator_data.py',
             ROOT/'src/knowledge_tracing/simulator_bridge.py',
             ROOT/'src/knowledge_tracing/akt/resources.py']
    paths += [PACKAGE/'data/simulator_inputs'/name for name in
              ('nodes.csv', 'edges.csv', 'question_bank.csv', 'concept_to_chapter_map.csv')]
    result = {}
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('source must be a regular in-workspace allowlisted file')
        result[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(result.items()))


@dataclass(frozen=True)
class ResearchCollectionRecipe:
    policy: str
    events_per_learner: int
    start_unix_seconds: int
    gap_seconds: int

    def __post_init__(self):
        # Concrete oracle-free implementations; no arbitrary callable receives the environment.
        if self.policy not in ('uniform_items', 'cyclic_items_seeded_offset'):
            raise ValueError('unsupported concrete observable logging policy')
        if (type(self.events_per_learner) is not int or not 1 <= self.events_per_learner <= EVENT_STRIDE
                or type(self.start_unix_seconds) is not int or self.start_unix_seconds < 0
                or type(self.gap_seconds) is not int or self.gap_seconds < 1):
            raise ValueError('explicit finite workload/clock required within stable source-row slots')
        last_second = self.start_unix_seconds + self.events_per_learner*self.gap_seconds
        # pandas may wrap unsigned-sized inputs rather than raise: reject in Python first.
        if last_second > MAX_UNIX_SECONDS:
            raise ValueError('clock exceeds supported UTC timestamp range')
        pd.to_datetime(last_second, unit='s', utc=True)

    @property
    def identity(self):
        return identity_hash({'collector': COLLECTOR_VERSION, 'clock': 'unix_seconds_utc', **asdict(self)})


@dataclass(frozen=True)
class ResearchCollectionLimits:
    max_learners: int
    max_events_per_learner: int
    max_total_events: int
    max_wall_seconds: float
    max_rss_bytes: int
    min_available_ram_bytes: int

    def __post_init__(self):
        ShardLimits(self.max_learners, self.max_events_per_learner, self.max_total_events)
        if (type(self.max_wall_seconds) not in (int, float) or not math.isfinite(self.max_wall_seconds)
                or not 0 < self.max_wall_seconds <= 600
                or type(self.max_rss_bytes) is not int or not 64*1024**2 <= self.max_rss_bytes <= 2*1024**3
                or type(self.min_available_ram_bytes) is not int or self.min_available_ram_bytes < 1024**3):
            raise ValueError('explicit bounded wall/RSS/free-RAM resource limits required')

    def shard_limits(self):
        return ShardLimits(self.max_learners, self.max_events_per_learner, self.max_total_events)


class ResearchCollectionFailure(RuntimeError):
    """Retains work counters on failure; never returns a usable partial corpus."""
    def __init__(self, cause, receipt):
        super().__init__(str(cause))
        self.receipt = receipt


@dataclass(frozen=True)
class ResearchCollectionResult:
    bank: SimulatorBank
    trajectories: tuple[ObservableTrajectory, ...]
    provenance: ResearchProvenance
    oracle_sidecar: dict
    manifest: dict


def _guard(started, limits):
    if time.perf_counter() - started >= limits.max_wall_seconds:
        raise TimeoutError('research collector cooperative wall limit')
    sample = memory_snapshot()
    rss = sample['process_rss_bytes']
    peak = sample['process_peak_rss_bytes']
    available = sample['system_available_ram_bytes']
    if (type(rss) is not int or rss < 0 or (peak is not None and (type(peak) is not int or peak < 0))
            or type(available) is not int or available < 0):
        raise ValueError('unknown/invalid memory telemetry')
    if max(rss, peak or 0) > limits.max_rss_bytes:
        raise MemoryError('research collector RSS limit')
    if available < limits.min_available_ram_bytes:
        raise MemoryError('research collector free-RAM floor')
    if time.perf_counter() - started >= limits.max_wall_seconds:
        raise TimeoutError('research collector cooperative wall limit after telemetry')
    return sample


def _bank_and_graph(reference):
    provenance = canonical_source_provenance(reference['provenance'])
    sources = provenance['inputs']
    question_path = next(ROOT/name for name in sources if name.endswith('/question_bank.csv'))
    edge_path = next(ROOT/name for name in sources if name.endswith('/edges.csv'))
    with question_path.open(encoding='utf-8-sig', newline='') as stream:
        items = tuple(SimulatorItem(r['question_id'], r['concept_id'], float(r['elo_difficulty']))
                      for r in csv.DictReader(stream))
    with edge_path.open(encoding='utf-8-sig', newline='') as stream:
        edges = [(r['source'], r['target']) for r in csv.DictReader(stream)]
    nodes = sorted(reference['environment']['nodes'])
    if (len(edges) != len(set(edges)) or any(a not in nodes or b not in nodes for a, b in edges)
            or set(i.concept_id for i in items) != set(nodes)):
        raise ValueError('native source graph/bank mismatch')
    semantics = environment_semantics(reference)
    bank = SimulatorBank('paper2-grade10-research-' + identity_hash(semantics), items)
    return bank, identity_hash({'nodes': nodes, 'edges': sorted(edges)}), semantics


def _channels(assignment):
    seeds = dict(assignment.stream_seeds)
    selected = {'outcome': int(identity_hash([RNG_NAMESPACE, seeds['response'], 'outcome'])[:16], 16),
                'learning': int(identity_hash([RNG_NAMESPACE, seeds['response'], 'learning'])[:16], 16),
                'behavior': int(identity_hash([RNG_NAMESPACE, seeds['behavior'], 'behavior'])[:16], 16)}
    if len(set(selected.values())) != 3:
        raise ValueError('derived RNG channel seeds collide')
    return {name: np.random.Generator(np.random.PCG64(seed)) for name, seed in selected.items()}, selected


def collect_research_role(plan, *, role, profiles, recipe, limits, expected_sources):
    """Collect exactly one requested development role from the actual environment.

Profiles, base theta, uniforms and final states remain solely in oracle sidecar.
No default counts/policies/clock/budgets; final rejected before any source access.
"""
    if role not in DEVELOPMENT_ROLES:
        raise ValueError('final events forbidden in research development collector')
    if (type(plan) is not ResearchSplitPlan or type(recipe) is not ResearchCollectionRecipe
            or type(limits) is not ResearchCollectionLimits or type(profiles) is not dict
            or type(expected_sources) is not dict):
        raise ValueError('typed explicit plan/recipe/limits/profiles/source pins required')
    all_assignments = plan.split_plan.assignments()  # Includes final metadata, never final events.
    assignments = tuple(a for a in all_assignments if a.role == role)
    if (set(profiles) != {a.learner_id for a in assignments}
            or any(type(value) is not str for value in profiles.values())):
        raise ValueError('profiles must match exactly the requested-role learners')
    count = len(assignments)*recipe.events_per_learner
    if (len(assignments) > limits.max_learners or recipe.events_per_learner > limits.max_events_per_learner
            or count > limits.max_total_events or len(all_assignments)*EVENT_STRIDE > MAX_SOURCE_ROW):
        raise ValueError('declared role workload/source-row address exceeds caller resource limits')
    started = time.perf_counter()
    sources_before = {}
    counters = {'interact_attempts': 0, 'interact_returns': 0, 'completed_events': 0, 'completed_learners': 0}
    try:
        _guard(started, limits)  # Before loading/compiling native source.
        sources_before = source_inventory()
        if (sources_before != expected_sources or sources_before.get(PROTOCOL_PATH) != plan.protocol_sha256):
            raise ValueError('expected source/protocol inventory mismatch')
        reference = load_reference()
        _guard(started, limits)
        scope = reference['environment']
        if any(p not in scope['PERSONAS'] for p in profiles.values()):
            raise ValueError('unknown native persona')
        bank, graph_sha, semantics = _bank_and_graph(reference)
        difficulties = {}
        for item in bank.items:
            difficulties.setdefault(item.concept_id, []).append(item.difficulty)
        if (len(bank.items) != 84 or len(difficulties) != 28
                or any(sorted(d) != [1050., 1200., 1350.] for d in difficulties.values())):
            raise ValueError('research reference bank must have exactly 28 concepts and three difficulties')
        source_meta = canonical_source_provenance(reference['provenance'])
        recorded = {source_meta['notebook']: source_meta['notebook_sha256'], **source_meta['inputs']}
        if any(sources_before.get(name) != digest for name, digest in recorded.items()):
            raise ValueError('loaded native reference differs from expected source inventory')
        recipe_binding = identity_hash({'recipe': asdict(recipe), 'recipe_sha256': recipe.identity,
                                       'profile_metadata_sha256': identity_hash(profiles)})
        policy_id = COLLECTOR_VERSION + ':' + recipe.policy
        provenance = ResearchProvenance(role, plan.identity, plan.split_plan.identity,
            identity_hash(bank.identity), graph_sha,
            (('collector', sources_before[COLLECTOR_PATH]), ('environment', identity_hash(semantics)),
             ('source_inventory', identity_hash(sources_before))), recipe_binding, policy_id,
            'unix_seconds_utc', 'UTC', False)
        ordinal = {a.learner_id: i for i, a in enumerate(all_assignments)}
        trajectories, oracle = [], {}
        for assignment in assignments:
            _guard(started, limits)
            seeds = dict(assignment.stream_seeds)
            base = scope['persona_base_abilities'](profiles[assignment.learner_id], seeds['latent'])
            environment = scope['LatentStudentEnvironment'](base)
            channels, derived_seeds = _channels(assignment)
            before_states = {name: generator.bit_generator.state for name, generator in channels.items()}
            hashes = {name: hashlib.sha256() for name in ('outcome', 'learning')}
            offset = (int(channels['behavior'].integers(len(bank.items)))
                      if recipe.policy == 'cyclic_items_seeded_offset' else 0)
            observations, details = [], []
            for rank in range(recipe.events_per_learner):
                _guard(started, limits)
                index = (int(channels['behavior'].integers(len(bank.items))) if recipe.policy == 'uniform_items'
                         else (offset+rank) % len(bank.items))
                item = bank.items[index]
                seconds = recipe.start_unix_seconds + (rank+1)*recipe.gap_seconds
                timestamp = pd.to_datetime(seconds, unit='s', utc=True)
                outcome, learning = float(channels['outcome'].random()), float(channels['learning'].random())
                hashes['outcome'].update(struct.pack('>d', outcome))
                hashes['learning'].update(struct.pack('>d', learning))
                counters['interact_attempts'] += 1
                result = environment.interact(item.concept_id, item.difficulty, timestamp, outcome, learning)
                counters['interact_returns'] += 1
                if type(result) is not dict or type(result.get('y')) is not int or result['y'] not in (0, 1):
                    raise ValueError('native environment returned an invalid binary outcome')
                source_row = ordinal[assignment.learner_id]*EVENT_STRIDE + rank+1
                query = ItemQuery(item.item_id, seconds, source_row)
                observations.append(Observation(query, result['y']))
                details.append({'query': asdict(query), 'oracle_result': dict(result),
                                'outcome_uniform': outcome, 'learning_uniform': learning})
                counters['completed_events'] += 1
                _guard(started, limits)  # Reject even if final native call itself overruns.
            trajectories.append(ObservableTrajectory(assignment.learner_id, plan.split_plan.identity,
                identity_hash(bank.identity), policy_id, tuple(observations)))
            oracle[assignment.learner_id] = {'profile': profiles[assignment.learner_id],
                'assignment': asdict(assignment), 'initial_state': dict(base), 'events': details,
                'final_snapshot': environment.snapshot(timestamp), 'channel_seeds': derived_seeds,
                'channel_state_before': before_states,
                'channel_state_after': {name: generator.bit_generator.state for name, generator in channels.items()},
                'outcome_learning_prefix_encoding': 'IEEE754 float64 big-endian concatenation',
                'outcome_learning_sha256': {name: digest.hexdigest() for name, digest in hashes.items()}}
            counters['completed_learners'] += 1
        _guard(started, limits)
        audit = audit_research_shard(tuple(trajectories), plan=plan, bank=bank, role=role,
            provenance=provenance, expected_provenance_sha256=provenance.identity,
            limits=limits.shard_limits(), reference_items=bank.item_ids)
        sources_after = source_inventory()
        if sources_after != sources_before:
            raise ValueError('source inventory drift during research collection')
        sidecar = {'scope': 'oracle evaluation only; forbidden as model features', 'learners': oracle}
        manifest = {'schema_version': 1, 'status': 'COMPLETE_REQUESTED_ROLE_NOT_MODEL_FITTED',
            'collector_version': COLLECTOR_VERSION, 'role': role, 'plan_sha256': plan.identity,
            'recipe': asdict(recipe), 'recipe_sha256': recipe_binding, 'limits': asdict(limits),
            'domain': bank.identity, 'environment_semantics': semantics,
            'environment_graph_sha256': graph_sha, 'provenance': asdict(provenance),
            'provenance_sha256': provenance.identity, 'sources_before': sources_before, 'sources_after': sources_after,
            'logging_policy_oracle_access': False, 'profile_metadata_sha256': identity_hash(profiles),
            'source_row_formula': 'global_plan_learner_ordinal*1000000+rank+1',
            'clock': {'unit': 'unix_seconds_utc', 'timezone': 'UTC', 'first_event': 'start+gap'},
            'rng_namespace': RNG_NAMESPACE, 'numpy_version': np.__version__, 'pandas_version': pd.__version__,
            'audit': audit, 'oracle_sidecar_sha256': identity_hash(sidecar), **counters,
            'elapsed_seconds': time.perf_counter()-started,
            'scope': 'actual requested-role observations if called; not a fit/calibration/final readiness certificate'}
        _guard(started, limits)
        manifest['elapsed_seconds'] = time.perf_counter()-started
        if manifest['elapsed_seconds'] >= limits.max_wall_seconds:
            raise TimeoutError('research collector final elapsed exceeds cooperative limit')
        return ResearchCollectionResult(bank, tuple(trajectories), provenance, sidecar, manifest)
    except Exception as error:
        try:
            after = source_inventory() if sources_before else {}
        except Exception as source_error:
            after = {'unavailable': repr(source_error)}
        receipt = {'status': 'FAILED_NO_USABLE_ROLE_RESULT', 'role': role, **counters,
            'elapsed_seconds': time.perf_counter()-started, 'original_error_type': type(error).__name__,
            'original_error': str(error), 'sources_before': sources_before, 'sources_after': after,
            'plan_sha256': plan.identity, 'recipe_sha256': recipe.identity, 'limits': asdict(limits),
            'partial_environment_work_rolled_back': False, 'automatic_retry': False,
            'resource_scope': 'cooperative stage/operator checks, not hardkill/peak-allocation attestation'}
        raise ResearchCollectionFailure(error, receipt) from error
