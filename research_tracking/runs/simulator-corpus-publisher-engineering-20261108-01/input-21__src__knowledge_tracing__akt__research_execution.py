"""Guard metadata CPU A0 research; không import Torch/model, không chạy trainer.

Corpus v1 dùng paths cố định, observable bytes chỉ stream-hash, oracle/không mở.
Receipts là consistency binding hợp tác; không phải chữ ký hoặc capability không
thể giả. Future research entry phải consume guard trước lazy model import.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import time

from . import authorization as native_auth
from .config import AKTConfig, PROJECT_ROOT, validate_config
from ..simulator_bridge import identity_hash
from ..simulator_research_data import ResearchSplitPlan, ResearchProvenance

PROTOCOL_ID = 'S04A-S05B-GROUP-V1-20261108'
SCOPE = 'simulator-research-a0-selected-refit-calibration-v1'
ROLES = ('train', 'selection', 'calibration')
PROTOCOL_PATH = 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'
PHASES = ('selection_fit', 'refit90', 'calibration_predict', 'temperature_fit')


def _require(ok, message):
    if not ok: raise ValueError(message)


def _sha(value):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'SHA256 required')


def _text(value):
    _require(type(value) is str and bool(value.strip()), 'nonempty text required')


def _positive(value):
    _require(type(value) is int and 1 <= value < 2**63, 'positive integer budget/count required')


def _jsonable(value):
    return json.loads(json.dumps(value, default=str, sort_keys=True, allow_nan=False))


def _same_json(left, right):
    return identity_hash(left) == identity_hash(right)


def _path(root, relative):
    _require(type(relative) is str and '\\' not in relative and ':' not in relative, 'relative POSIX path required')
    p = PurePosixPath(relative)
    _require(bool(p.parts) and not p.is_absolute() and p.as_posix() == relative and '..' not in p.parts, 'unsafe path')
    cursor = root
    _require(root.is_dir() and not root.is_symlink() and root.resolve() == root.absolute(), 'physical project root required')
    for part in p.parts:
        cursor = cursor / part
        _require(not cursor.is_symlink(), 'symlink metadata/input/output path')
    return cursor


def _hash_file(path, *, cap):
    _require(path.is_file() and not path.is_symlink(), 'regular bounded file required')
    size = path.stat().st_size
    _require(0 <= size <= cap, 'input byte budget exceeded')
    digest = hashlib.sha256(); total = 0
    with path.open('rb') as stream:
        while block := stream.read(65536):
            total += len(block); _require(total <= cap, 'input byte budget exceeded while hashing')
            digest.update(block)
    _require(total == size == path.stat().st_size, 'input size changed during hashing')
    return digest.hexdigest(), total


def _read_json(path, cap):
    digest, size = _hash_file(path, cap=cap)
    with path.open('rb') as stream:
        raw = stream.read(cap+1)
    _require(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest, 'metadata changed during read')
    def unique(pairs):
        value={}
        for key,item in pairs:
            _require(key not in value, 'duplicate JSON key')
            value[key]=item
        return value
    def invalid_constant(value):
        raise ValueError('nonfinite JSON constant: '+value)
    value = json.loads(raw,object_pairs_hook=unique,parse_constant=invalid_constant)
    _require(type(value) is dict, 'JSON object required')
    return value, digest, size


@dataclass(frozen=True)
class ResearchResourceBudget:
    train_learners: int
    selection_learners: int
    calibration_learners: int
    train_targets: int
    selection_targets: int
    calibration_targets: int
    max_events_per_learner: int
    max_optimizer_steps: int
    max_optimized_targets: int
    max_training_seconds: float
    max_wall_seconds: float
    max_rss_bytes: int
    min_available_ram_bytes: int
    max_checkpoint_bytes: int
    max_prediction_bytes: int
    max_input_bytes: int

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name not in ('max_training_seconds', 'max_wall_seconds'): _positive(value)
            else: _require(type(value) in (int, float) and math.isfinite(value) and value > 0, 'finite explicit time budget required')
        _require(self.max_training_seconds <= self.max_wall_seconds, 'training time exceeds wall budget')
        _require(self.min_available_ram_bytes >= 1024**3, 'research retains at least1GiB available-RAM floor')
        _require(self.train_learners == 8*self.selection_learners and self.selection_learners == self.calibration_learners,
                 'exact80/10/10 learner allocation required')
        for role in ROLES:
            _require(getattr(self, role+'_targets') <= getattr(self, role+'_learners')*self.max_events_per_learner,
                     'role targets exceed declared event limit')


@dataclass(frozen=True)
class ResearchRuntimeEvidence:
    runtime_report: str
    runtime_report_sha256: str
    lock_file: str
    lock_sha256: str
    gate_pointer: str
    gate_pointer_sha256: str
    gate_report_sha256: str
    gate_log_sha256: str

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name.endswith('sha256'): _sha(value)
            else: _text(value)


@dataclass(frozen=True)
class SimulatorResearchSpec:
    native_config: AKTConfig
    corpus_id: str
    expected_corpus_sha256: str
    expected_protocol_sha256: str
    budget: ResearchResourceBudget

    def __post_init__(self):
        _require(type(self.native_config) is AKTConfig and type(self.budget) is ResearchResourceBudget, 'typed config/budget required')
        _require(type(self.corpus_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', self.corpus_id), 'corpus ID required')
        _sha(self.expected_corpus_sha256); _sha(self.expected_protocol_sha256)
        validate_config(self.native_config)
        c, b = self.native_config, self.budget
        _require(c.phase == 'simulator-research' and c.project_root == PROJECT_ROOT, 'explicit simulator-research CPU scope required')
        expected = dict(max_train_users=b.train_learners+b.selection_learners,
            max_val_users=max(b.selection_learners,b.calibration_learners),
            max_targets_per_side=b.train_targets+b.selection_targets,
            max_total_targets=b.train_targets+b.selection_targets+b.calibration_targets,
            max_steps=b.max_optimizer_steps,max_seconds=b.max_training_seconds,max_wall_seconds=b.max_wall_seconds,
            max_rss_bytes=b.max_rss_bytes,min_available_ram_bytes=b.min_available_ram_bytes)
        _require(all(getattr(c, name) == value for name, value in expected.items()), 'native caps must exactly match cumulative research budget')

    @property
    def identity(self):
        return identity_hash(_jsonable(asdict(self)))


def _native_evidence(spec, evidence):
    """Reuse source/runtime/Gate validators only; never default BKT identity()."""
    root = spec.native_config.project_root
    paths = {name: _path(root,getattr(evidence,name)) for name in ('runtime_report','lock_file','gate_pointer')}
    preflight = root/'artifacts/akt/preflight'
    _require(paths['runtime_report'].parent == preflight and paths['gate_pointer'].parent == preflight, 'runtime/Gate paths must be preflight metadata')
    lock = paths['lock_file']
    _require((lock.parent == root and re.fullmatch('requirements-akt[^/]*[.]txt',lock.name))
             or lock.is_relative_to(root/'artifacts/akt'), 'selected lock outside AKT dependency paths')
    for name, field in [('runtime_report','runtime_report_sha256'),('lock_file','lock_sha256'),('gate_pointer','gate_pointer_sha256')]:
        _require(_hash_file(paths[name],cap=spec.budget.max_input_bytes)[0] == getattr(evidence,field), 'runtime/lock/Gate byte binding mismatch')
    venv = root/'.venv'
    _require(venv.is_dir() and not venv.is_symlink() and venv.resolve() == venv.absolute(), 'physical same-root environment required')
    # No Git environment redirection from a caller; launcher may pass only these read-only safeguards.
    allowed = {'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_TERMINAL_PROMPT':'0',
               'GIT_OPTIONAL_LOCKS':'0','GIT_ALLOW_PROTOCOL':'__NO_TRANSPORT__'}
    _require(all(k in allowed and v == allowed[k] for k,v in os.environ.items() if k.startswith(('GIT_','GH_'))), 'inherited Git/credential configuration rejected')
    _require(os.environ.get('CUDA_VISIBLE_DEVICES','') in ('','-1') and os.environ.get('NVIDIA_VISIBLE_DEVICES','') in ('','none','void'), 'CPU research cannot expose CUDA devices')
    runtime = native_auth.preflight(spec.native_config,project_root=root,
        runtime_report_path=paths['runtime_report'],lock_file=lock)
    report = runtime['runtime']
    _require(report.get('runtime_schema_version') == 2 and report.get('device') == 'cpu'
             and report.get('cuda_available') is False, 'research requires explicit fresh schema2 CPU runtime')
    gate = native_auth.require_gate2_evidence(spec.native_config,project_root=root,
        gate2_report=paths['gate_pointer'],lock_file=lock)
    _require(gate['pointer_sha256'] == evidence.gate_pointer_sha256 and gate['report_sha256'] == evidence.gate_report_sha256
             and gate['test_log_sha256'] == evidence.gate_log_sha256, 'Gate receipt mismatch')
    _require(runtime['runtime_report_sha256'] == evidence.runtime_report_sha256 and runtime['lock_sha256'] == evidence.lock_sha256,
             'runtime receipt mismatch')
    return dict(runtime=runtime,gate=gate,build_hashes=native_auth.gate2_build_hashes(root))


def _bank(value):
    _require(set(value) == {'schema_version','environment_id','items'} and type(value['schema_version']) is int and value['schema_version'] == 1, 'bank schema')
    _text(value['environment_id']); rows=value['items']
    _require(type(rows) is list and len(rows) == 84, 'complete84item bank required')
    normalized=[]; concepts={}
    for row in rows:
        _require(type(row) is dict and set(row) == {'item_id','concept_id','difficulty'}, 'bank item schema')
        _text(row['item_id']); _text(row['concept_id'])
        _require(type(row['difficulty']) in (int,float) and row['difficulty'] in (1050,1200,1350), 'reference difficulty')
        normalized.append({**row,'difficulty':float(row['difficulty'])})
        concepts.setdefault(row['concept_id'],[]).append(float(row['difficulty']))
    _require(len({r['item_id'] for r in normalized}) == 84 and len(concepts) == 28
             and all(sorted(v) == [1050.,1200.,1350.] for v in concepts.values()), 'bank coverage/uniqueness')
    identity=dict(schema_version=1,environment_id=value['environment_id'],input_unit='item_id',
                  item_bank_sha256=identity_hash(sorted(normalized,key=lambda r:r['item_id'])))
    return identity_hash(identity)


def _plan(value, spec, corpus):
    _require(set(value) == {'schema_version','recipe','manifest'} and type(value['schema_version']) is int and value['schema_version'] == 1
             and type(value['manifest']) is dict and type(value['recipe']) is dict, 'restartable plan schema')
    recipe=value['recipe']
    _require(set(recipe) == {'namespace','root_seed','development_learners','final_learners','protocol_sha256'}, 'plan constructor recipe schema')
    reconstructed=ResearchSplitPlan(**recipe)
    _require(_same_json(reconstructed.manifest(),value['manifest']), 'plan recipe/declared manifest mismatch')
    plan=value['manifest']; b=spec.budget
    _require(set(plan) == {'protocol_id','research_plan_sha256','split_plan_sha256','protocol_sha256',
             'role_counts','assignments','refit_roles','calibration_in_refit','final_events_read','scope'}, 'plan manifest schema')
    _require(plan.get('protocol_id') == PROTOCOL_ID and plan.get('protocol_sha256') == spec.expected_protocol_sha256
             and plan.get('research_plan_sha256') == corpus['research_plan_sha256'], 'plan/protocol identity mismatch')
    for name in ('research_plan_sha256','split_plan_sha256'): _sha(plan.get(name))
    _require(plan.get('refit_roles') == ['train','selection'] and plan.get('calibration_in_refit') is False
             and plan.get('final_events_read') is False, 'plan role leakage')
    counts=plan.get('role_counts')
    _require(type(counts) is dict and set(counts) == set(ROLES)|{'final'}, 'plan counts')
    for v in counts.values(): _positive(v)
    _require(all(counts[r] == getattr(b,r+'_learners') for r in ROLES), 'plan/corpus budget counts')
    assignments=plan.get('assignments')
    _require(type(assignments) is list and len(assignments) == sum(counts.values()), 'plan assignments population')
    learners={r:[] for r in (*ROLES,'final')}; family_role={}; seen=set(); seeds=set()
    for row in assignments:
        _require(type(row) is dict and set(row) == {'learner_id','role','seed_family','stream_seeds'}, 'assignment schema')
        _text(row['learner_id']); _text(row['seed_family']); role=row['role']
        _require(role in learners and row['learner_id'] not in seen, 'duplicate/unknown learner role')
        seen.add(row['learner_id']); learners[role].append(row['learner_id'])
        _require(family_role.setdefault(row['seed_family'],role) == role, 'seed-family crosses roles')
        streams=row['stream_seeds']
        _require(type(streams) is list and len(streams) == 3 and all(type(x) is list and len(x) == 2 for x in streams)
                 and {x[0] for x in streams} == {'latent','response','behavior'}, 'stream seed schema')
        for _,seed in streams:
            _require(type(seed) is int and 0 <= seed < 2**64 and seed not in seeds, 'stream seed collision/type')
            seeds.add(seed)
    _require(all(len(learners[r]) == counts[r] for r in learners), 'incomplete role assignment')
    return {r:sorted(learners[r]) for r in ROLES}


def _role_provenance(manifest, *, role, corpus, recipe, profile_sha256, plan_manifest):
    """Reconstruct typed observable provenance, never collector or oracle inputs."""
    value=manifest.get('provenance')
    _require(type(value) is dict and set(value) == set(ResearchProvenance.__dataclass_fields__), 'role provenance schema')
    values=dict(value); bindings=values['source_bindings']
    _require(type(bindings) is list and all(type(row) is list and len(row) == 2 for row in bindings), 'provenance source bindings schema')
    values['source_bindings']=tuple(tuple(row) for row in bindings)
    provenance=ResearchProvenance(**values)
    _sha(manifest.get('provenance_sha256'))
    _require(provenance.identity == manifest['provenance_sha256'], 'provenance identity mismatch')
    raw={k:recipe[k] for k in ('policy','events_per_learner','start_unix_seconds','gap_seconds')}
    # Source-pinned ResearchCollectionRecipe.identity formula; no NumPy/pandas collector import.
    raw_identity=identity_hash({'collector':recipe['collector_version'],'clock':'unix_seconds_utc',**raw})
    composite=identity_hash({'recipe':raw,'recipe_sha256':raw_identity,'profile_metadata_sha256':profile_sha256})
    expected=dict(role=role,research_plan_sha256=corpus['research_plan_sha256'],
        split_plan_sha256=plan_manifest['split_plan_sha256'],bank_sha256=corpus['domain_sha256'],
        environment_graph_sha256=corpus['environment_graph_sha256'],
        collection_recipe_sha256=composite,collection_policy_id=recipe['collector_version']+':'+recipe['policy'],
        timestamp_unit='unix_seconds_utc',timezone='UTC',logging_policy_oracle_access=False)
    _require(all(_same_json(value[k],v) for k,v in expected.items()), 'provenance role/plan/domain/graph/policy/recipe mismatch')
    source_bindings=dict(provenance.source_bindings)
    sources=corpus['source_inventory']
    collector='src/knowledge_tracing/simulator_research_collection.py'
    _require(set(source_bindings) == {'collector','environment','source_inventory'}
             and collector in sources and source_bindings['collector'] == sources[collector]
             and source_bindings['source_inventory'] == identity_hash(sources), 'provenance collector/source inventory binding mismatch')
    return provenance,source_bindings['environment']


def _corpus(spec, native):
    root=spec.native_config.project_root; base=_path(root,'artifacts/simulator/corpora/'+spec.corpus_id)
    failure=_path(root,base.relative_to(root).as_posix()+'/failure.json')
    done_path=_path(root,base.relative_to(root).as_posix()+'/DONE.json')
    _require(done_path.is_file() and not failure.exists(), 'complete DONE and absence of failure required')
    cap=spec.budget.max_input_bytes; corpus,path_sha,used=_read_json(base/'corpus.json',cap)
    _require(path_sha == spec.expected_corpus_sha256, 'corpus.json SHA mismatch')
    required={'schema_version','domain','no_junyi_fold','protocol_id','protocol_sha256','bank_sha256','domain_sha256',
              'plan_sha256','research_plan_sha256','environment_graph_sha256','normalized_recipe','normalized_recipe_sha256',
              'source_inventory','roles'}
    _require(set(corpus) == required and type(corpus['schema_version']) is int and corpus['schema_version'] == 1 and corpus['domain'] == 'simulator'
             and corpus['no_junyi_fold'] is True, 'closed simulator corpus schema/no Junyi fold required')
    _require(corpus['protocol_id'] == PROTOCOL_ID and corpus['protocol_sha256'] == spec.expected_protocol_sha256, 'corpus/protocol mismatch')
    for key in ('bank_sha256','domain_sha256','plan_sha256','research_plan_sha256','environment_graph_sha256','normalized_recipe_sha256'): _sha(corpus[key])
    bindings={'corpus.json':path_sha}
    for filename,field in [('bank.json','bank_sha256'),('plan.json','plan_sha256')]:
        value,digest,size=_read_json(_path(root,base.relative_to(root).as_posix()+'/'+filename),cap-used)
        used+=size; _require(digest == corpus[field], 'bank/plan bytes mismatch'); bindings[filename]=digest
        if filename == 'bank.json': _require(_bank(value) == corpus['domain_sha256'], 'bank domain mismatch')
        else:
            learners=_plan(value,spec,corpus)
            plan_manifest=value['manifest']
    recipe=corpus['normalized_recipe']
    _require(type(recipe) is dict and set(recipe) == {'collector_version','policy','events_per_learner',
        'start_unix_seconds','gap_seconds','timestamp_unit','timezone'}, 'normalized recipe schema')
    _text(recipe['collector_version']); _text(recipe['policy'])
    _positive(recipe['events_per_learner']); _positive(recipe['gap_seconds'])
    _require(type(recipe['start_unix_seconds']) is int and recipe['start_unix_seconds'] >= 0
             and recipe['timestamp_unit'] == 'unix_seconds_utc' and recipe['timezone'] == 'UTC'
             and recipe['events_per_learner'] <= spec.budget.max_events_per_learner
             and identity_hash(recipe) == corpus['normalized_recipe_sha256'], 'normalized recipe/clock mismatch')
    sources=corpus['source_inventory']
    _require(type(sources) is dict and sources, 'corpus source inventory required')
    for name,digest in sources.items():
        _sha(digest)
        _require((name == PROTOCOL_PATH and digest == spec.expected_protocol_sha256)
                 or native['build_hashes'].get(name) == digest, 'corpus source differs from current source-bound Gate')
    _require(type(corpus['roles']) is dict and set(corpus['roles']) == set(ROLES), 'exact development roles only; no final files')
    environment_semantics_sha256=None
    for role in ROLES:
        entry=corpus['roles'][role]
        _require(type(entry) is dict and set(entry) == {'observable_file','observable_sha256','manifest_file','manifest_sha256','learners','targets','profile_sha256'}, 'role entry schema')
        _require(entry['observable_file'] == role+'.jsonl' and entry['manifest_file'] == role+'.manifest.json', 'fixed observable/manifest filenames')
        for field in ('observable_sha256','manifest_sha256','profile_sha256'): _sha(entry[field])
        _require(type(entry['learners']) is int and entry['learners'] == getattr(spec.budget,role+'_learners')
                 and type(entry['targets']) is int and entry['targets'] == getattr(spec.budget,role+'_targets')
                 and entry['targets'] == entry['learners']*recipe['events_per_learner'], 'role counts/targets do not match budget/recipe')
        role_path=lambda filename:_path(root,base.relative_to(root).as_posix()+'/'+filename)
        manifest,digest,size=_read_json(role_path(entry['manifest_file']),cap-used);used+=size
        _require(digest == entry['manifest_sha256'], 'role manifest SHA mismatch')
        bindings[entry['manifest_file']]=digest
        expected=dict(schema_version=1,role=role,research_plan_sha256=corpus['research_plan_sha256'],
            domain_sha256=corpus['domain_sha256'],environment_graph_sha256=corpus['environment_graph_sha256'],
            normalized_recipe_sha256=corpus['normalized_recipe_sha256'],source_inventory_sha256=identity_hash(sources),
            profile_sha256=entry['profile_sha256'],learner_ids=learners[role],targets=entry['targets'],
            observable_sha256=entry['observable_sha256'],timestamp_unit='unix_seconds_utc',timezone='UTC',logging_policy_oracle_access=False)
        _require(set(manifest) == set(expected)|{'provenance','provenance_sha256'}, 'role manifest16-key restart schema')
        _require(_same_json({k:manifest[k] for k in expected},expected), 'cross-role graph/recipe/source/clock/learners/provenance mismatch')
        provenance,semantics=_role_provenance(manifest,role=role,corpus=corpus,recipe=recipe,
            profile_sha256=entry['profile_sha256'],plan_manifest=plan_manifest)
        if environment_semantics_sha256 is None: environment_semantics_sha256=semantics
        _require(semantics == environment_semantics_sha256, 'environment semantics differ across roles')
        digest,size=_hash_file(role_path(entry['observable_file']),cap=cap-used);used+=size
        _require(digest == entry['observable_sha256'], 'observable bytes SHA mismatch')
        bindings[entry['observable_file']]=digest
    done,done_sha,size=_read_json(done_path,cap-used);used+=size
    _require(set(done) == {'schema_version','status','corpus_sha256','files_sha256'}
             and type(done['schema_version']) is int and done['schema_version'] == 1
             and done['status'] == 'COMPLETE_SIMULATOR_CORPUS' and done['corpus_sha256'] == spec.expected_corpus_sha256
             and _same_json(done['files_sha256'],bindings), 'DONE exact9input inventory mismatch')
    _require(not failure.exists() and _hash_file(done_path,cap=cap)[0] == done_sha, 'publication changed or failed during audit')
    # No directory glob/listing, no open of oracle/ or any final event path.
    return dict(corpus_root=base.relative_to(root).as_posix(),files_sha256=bindings,input_bytes=used,
                done_sha256=done_sha,
                domain_sha256=corpus['domain_sha256'],research_plan_sha256=corpus['research_plan_sha256'],
                normalized_recipe_sha256=corpus['normalized_recipe_sha256'],source_inventory=sources,
                environment_semantics_sha256=environment_semantics_sha256,
                final_event_files_opened=False,oracle_files_opened=False,observable_labels_parsed=False,
                actual_observable_schema_reaudit_required_before_model=True)


def prepare_research_identity(spec, evidence):
    _require(type(spec) is SimulatorResearchSpec and type(evidence) is ResearchRuntimeEvidence, 'typed research spec/runtime evidence required')
    # Reconstruct immutable spec to validate against current config checks after source changes.
    SimulatorResearchSpec(**{k:getattr(spec,k) for k in spec.__dataclass_fields__})
    started=time.monotonic(); wall_started=time.time(); root=spec.native_config.project_root
    protocol=_path(root,PROTOCOL_PATH)
    _require(_hash_file(protocol,cap=spec.budget.max_input_bytes)[0] == spec.expected_protocol_sha256, 'actual protocol21 bytes mismatch')
    with protocol.open('rb') as stream:
        protocol_raw=stream.read(spec.budget.max_input_bytes+1)
    _require(len(protocol_raw) <= spec.budget.max_input_bytes and hashlib.sha256(protocol_raw).hexdigest() == spec.expected_protocol_sha256,
             'protocol changed during bounded read')
    protocol_text=protocol_raw.decode('utf-8')
    _require('ADOPTED_GROUP_METHOD_V1' in protocol_text and 'S04-A' in protocol_text and 'S05-Plan B' in protocol_text,
             'adopted protocol21 marker mismatch')
    output=_path(root,spec.native_config.output_dir.relative_to(root).as_posix())
    native=_native_evidence(spec,evidence); corpus=_corpus(spec,native)
    result=_jsonable(dict(schema_version=1,scope=SCOPE,input_domain='simulator',junyi_fold_used=False,
        status='PREPARED_IDENTITY_NOT_EXECUTION_AUTHORITY',spec_sha256=spec.identity,
        config_sha256=native_auth.config_hash(spec.native_config),protocol_id=PROTOCOL_ID,
        protocol_sha256=spec.expected_protocol_sha256,corpus=corpus,native_evidence=native,
        resource_budget=asdict(spec.budget),runtime_evidence=asdict(evidence),output=str(output),
        permitted_phases=PHASES,legacy_outer_fold_field_unused=True,
        run_purpose='a0_single_candidate_lifecycle_pilot',candidate_allocation=['A0'],
        system_selector='NOT_RUN_MAIN_MATRIX_DEFERRED_BEFORE_ANY_MAIN_REFIT'))
    _require(max(time.monotonic()-started,time.time()-wall_started) <= spec.budget.max_wall_seconds, 'preflight wall budget exceeded')
    return result


@dataclass(frozen=True)
class AuthorizedResearchExecution:
    spec: SimulatorResearchSpec
    evidence: ResearchRuntimeEvidence
    authorization_file: str
    authorization_sha256: str
    approval_reference: str
    identity_json: str

    def revalidate(self):
        root=self.spec.native_config.project_root
        _require(_hash_file(_path(root,self.authorization_file),cap=self.spec.budget.max_input_bytes)[0] == self.authorization_sha256,
                 'authorization changed after validation')
        current=prepare_research_identity(self.spec,self.evidence)
        _require(_same_json(current,json.loads(self.identity_json)), 'authorized inputs/source/runtime changed')
        return current


def require_research_authorization(spec,evidence,*,authorization_file,expected_authorization_sha256):
    _require(type(spec) is SimulatorResearchSpec and type(evidence) is ResearchRuntimeEvidence, 'typed research spec/runtime evidence required')
    _sha(expected_authorization_sha256)
    _require(spec.native_config.execution_enabled is True, 'execution flag alone is insufficient; explicit enabled config required')
    root=spec.native_config.project_root; path=_path(root,authorization_file)
    _require(path.is_relative_to(root/'experiments/akt/authorizations') or path.is_relative_to(root/'artifacts/akt'), 'authorization outside approved AKT paths')
    value,digest,_=_read_json(path,spec.budget.max_input_bytes)
    _require(digest == expected_authorization_sha256, 'authorization artifact SHA mismatch')
    identity=prepare_research_identity(spec,evidence)
    fields={'schema_version','decision','scope','run_id','config_sha256','spec_sha256','identity','caps','requested_phases','approval_reference'}
    _require(set(value) == fields and type(value['schema_version']) is int and value['schema_version'] == 1
             and value['decision'] == 'AUTHORIZE_BOUNDED_SIMULATOR_RESEARCH' and value['scope'] == SCOPE,
             'closed research authorization scope/schema required; no GatePASS/boolean authority')
    _text(value['approval_reference'])
    _require(len(value['approval_reference']) <= 256 and value['run_id'] == spec.native_config.run_id
             and value['config_sha256'] == native_auth.config_hash(spec.native_config) and value['spec_sha256'] == spec.identity
             and _same_json(value['identity'],identity) and _same_json(value['caps'],asdict(spec.budget))
             and value['requested_phases'] == list(PHASES), 'authorization does not match exact source/inputs/config/caps')
    _require(not spec.native_config.output_dir.exists(), 'research output already exists; no overwrite/retry/resume')
    return AuthorizedResearchExecution(spec,evidence,authorization_file,digest,value['approval_reference'],
        json.dumps(identity,sort_keys=True,separators=(',',':'),allow_nan=False))
