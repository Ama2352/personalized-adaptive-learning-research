"""Admission selected-only GKT29, stdlib trước model; candidate chưa apply.

Đọc bằng chứng thật từ file đã ghim SHA. Không gọi A0 authorization/preflight,
không dùng metadata stage cấp quyền. Hash/token là consistency hợp tác, không
capability chống caller độc hại. Public reader/phase audits còn bắt buộc trước NN.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ET

from knowledge_tracing import simulator_corpus_reader as public_reader
from knowledge_tracing.simulator_bridge import identity_hash
from knowledge_tracing.research_admission import MainSelectionContext
from knowledge_tracing.akt import authorization as runtime_helpers
from knowledge_tracing.akt.research_execution import _path, _hash_file, _read_json

ROOT = public_reader.ROOT
SCOPE = 'gkt_main_selected_only_v1'
RECIPE_ID = 'gkt-grade10-static-expert-r32-bn-d5-v1'
RECIPE_PATH = 'docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md'
RECIPE_SHA256 = '059c98909c38856afd830d1cd296ce8875682ba9c7c226ad923c432e4328ce64'
PHASES = ('select_train80', 'raw_selection10')
OBJECTIVE = 'gkt29_raw_response_pooled_binary64_log_loss_v1'
_SEAL = object()
SOURCE_NAMES = (
    'src/knowledge_tracing/__init__.py', 'src/knowledge_tracing/akt/__init__.py',
    'src/knowledge_tracing/sakt/__init__.py', 'src/knowledge_tracing/gam_kt/__init__.py',
    'src/knowledge_tracing/gkt/__init__.py', 'src/knowledge_tracing/gkt/config.py',
    'src/knowledge_tracing/gkt/core.py', 'src/knowledge_tracing/gkt/recurrent.py',
    'src/knowledge_tracing/gkt/training.py',
    'src/knowledge_tracing/gkt/research_data.py', 'src/knowledge_tracing/gkt/research_training.py',
    'src/knowledge_tracing/gkt/research_checkpoint.py', 'src/knowledge_tracing/gkt/research_execution.py',
    'src/knowledge_tracing/gkt/research_runner.py', 'src/knowledge_tracing/akt/training.py',
    'src/knowledge_tracing/gkt/research_model.py', 'src/knowledge_tracing/sakt/training.py',
    'src/knowledge_tracing/sakt/research_checkpoint.py',
    'src/knowledge_tracing/sakt/config.py', 'src/knowledge_tracing/sakt/model.py',
    'src/knowledge_tracing/sakt/tensors.py', 'src/knowledge_tracing/sakt/training_data.py',
    'src/knowledge_tracing/sakt/research_data.py', 'src/knowledge_tracing/sakt/research_training.py',
    'src/knowledge_tracing/akt/research_simulator_data.py', 'src/knowledge_tracing/simulator_bridge.py',
    'src/knowledge_tracing/akt/research_execution.py', 'src/knowledge_tracing/akt/authorization.py',
    'src/knowledge_tracing/akt/filesystem.py', 'src/knowledge_tracing/akt/resources.py',
    'src/knowledge_tracing/simulator_corpus_reader.py', 'src/knowledge_tracing/research_admission.py',
    'src/knowledge_tracing/research_selection.py', 'src/knowledge_tracing/gam_kt/evaluation.py',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
    'docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md',
    'docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md', RECIPE_PATH,
    'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md',
    'docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json',
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'lowercase SHA256 required')


def canonical(value):
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))


def positive(value):
    need(type(value) is int and 0 < value < 2**63, 'positive bounded integer required')


@dataclass(frozen=True)
class GKTSelectedRecipe:
    recipe_id: str = RECIPE_ID
    state_dim: int = 32
    embedding_dim: int = 32
    message_dim: int = 32
    dropout: float = .5
    bn_eps: float = 1e-5
    bn_momentum: float = .1
    batch_size: int = 4
    lr: float = .001
    betas: tuple = (.9, .999)
    eps: float = 1e-8
    weight_decay: float = 0.
    max_grad_norm: float = 1.
    seed: int = 42
    max_epochs: int = 50
    patience: int = 5
    min_delta: float = .0001

    def __post_init__(self):
        expected = (RECIPE_ID, 32, 32, 32, .5, 1e-5, .1, 4, .001,
                    (.9, .999), 1e-8, 0., 1., 42, 50, 5, .0001)
        values = tuple(asdict(self).values())
        need(values == expected and all(type(v) is type(e) for v, e in zip(values, expected)),
             'exact adopted GKT29 numerical recipe required')


@dataclass(frozen=True)
class FilePin:
    path: str
    sha256: str

    def __post_init__(self):
        sha(self.sha256)
        need(type(self.path) is str and self.path and '\\' not in self.path and ':' not in self.path,
             'relative POSIX evidence path required')


@dataclass(frozen=True)
class GKTComponentAcceptance:
    kind: str
    outer: FilePin
    child: FilePin
    owned: FilePin
    junit: FilePin

    def __post_init__(self):
        need(self.kind in ('model11', 'trainer8', 'checkpoint28'), 'known GKT native component proof required')
        for pin in (self.outer, self.child, self.owned, self.junit):
            need(type(pin) is FilePin, 'typed actual component artifact pin required')
            pin.__post_init__()


@dataclass(frozen=True)
class GKTSelectedEvidence:
    runtime: FilePin
    gate_pointer: FilePin
    lock: FilePin
    components: tuple
    runtime_files: tuple

    def __post_init__(self):
        for pin in (self.runtime, self.gate_pointer, self.lock):
            need(type(pin) is FilePin, 'typed actual runtime/Gate/lock pin required')
            pin.__post_init__()
        need(type(self.components) is tuple and len(self.components) == 3
             and all(type(c) is GKTComponentAcceptance for c in self.components)
             and {c.kind for c in self.components} == {'model11', 'trainer8', 'checkpoint28'}, 'all three GKT component proofs required')
        for component in self.components:
            component.__post_init__()
        need(type(self.runtime_files) is tuple and 4 <= len(self.runtime_files) <= 128
             and all(type(pin) is FilePin for pin in self.runtime_files)
             and len({pin.path for pin in self.runtime_files}) == len(self.runtime_files), 'actual isolated runtime file pins required')
        for pin in self.runtime_files:
            pin.__post_init__()


@dataclass(frozen=True)
class GKTSelectedBudget:
    train_learners: int
    selection_learners: int
    calibration_learners: int
    train_targets: int
    selection_targets: int
    calibration_targets: int
    max_optimizer_steps: int
    max_optimized_targets: int
    max_prediction_targets: int
    max_training_prefix_events: int
    max_prediction_prefix_events: int
    max_model_calls: int
    max_training_seconds: float
    max_wall_seconds: float
    max_worker_rss_bytes: int
    min_available_ram_bytes: int
    prelaunch_available_ram_bytes: int
    max_metadata_bytes: int
    max_source_file_bytes: int
    max_checkpoint_bytes: int
    max_tensor_bytes: int
    max_output_bytes: int
    cpu_threads: int

    def __post_init__(self):
        for name, value in asdict(self).items():
            if name.endswith('_seconds'):
                need(type(value) is float and math.isfinite(value) and value > 0, 'explicit finite seconds required')
            else:
                positive(value)
        need(self.train_learners == 8*self.selection_learners
             and self.selection_learners == self.calibration_learners, 'exact80/10/10 allocation required')
        need(self.max_training_seconds <= self.max_wall_seconds
             and self.min_available_ram_bytes >= 2*1024**3
             and self.prelaunch_available_ram_bytes >= max(4*1024**3, self.min_available_ram_bytes)
             and 1 <= self.cpu_threads <= 8, 'CPU time/RAM/thread profile required')


@dataclass(frozen=True)
class GKTSelectedExecutionSpec:
    run_id: str
    context: MainSelectionContext
    recipe: GKTSelectedRecipe
    corpus_id: str
    corpus_sha256: str
    done_sha256: str
    topology: FilePin
    read_limits_json: str
    expected_sources: tuple
    budget: GKTSelectedBudget

    def __post_init__(self):
        need(type(self.run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', self.run_id), 'safe new run ID required')
        need(type(self.corpus_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}', self.corpus_id), 'safe fixed corpus ID required')
        need(type(self.context) is MainSelectionContext and self.context.environment_id == 'grade10_simulator', 'Grade10 main context required')
        self.context.validate()
        need(type(self.recipe) is GKTSelectedRecipe and type(self.budget) is GKTSelectedBudget, 'typed recipe and budget required')
        self.recipe.__post_init__(); self.budget.__post_init__()
        sha(self.corpus_sha256); sha(self.done_sha256)
        need(type(self.topology) is FilePin, 'actual expert topology file pin required')
        self.topology.__post_init__()
        need(self.topology.path.startswith('artifacts/akt/') and self.topology.path.endswith('.json'),
             'explicit public topology metadata under artifacts/akt required')
        limits = public_reader.CorpusReadLimits(**json.loads(self.read_limits_json))
        need(limits.max_wall_seconds <= self.budget.max_wall_seconds, 'reader exceeds whole allowance')
        need(type(self.expected_sources) is tuple and 1 <= len(self.expected_sources) <= 1024
             and all(type(row) is tuple and len(row) == 2 for row in self.expected_sources)
             and tuple(sorted(dict(self.expected_sources).items())) == self.expected_sources,
             'unique sorted explicit source inventory required')
        sources = dict(self.expected_sources)
        need(set(SOURCE_NAMES) <= set(sources), 'all GKT/shared method sources required')
        need(sources[RECIPE_PATH] == RECIPE_SHA256
             and sources['docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md'] == self.context.protocol21_sha256
             and sources['docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md'] == self.context.recipe26_sha256
             and sources['docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json'] == self.context.allocation_sha256,
             'adopted method/matrix source bindings required')
        need(self.budget.max_optimizer_steps >= self.recipe.max_epochs*((self.budget.train_learners+3)//4)
             and self.budget.max_optimized_targets >= self.recipe.max_epochs*self.budget.train_targets
             and self.budget.max_prediction_targets >= (self.recipe.max_epochs+1)*self.budget.selection_targets
             and self.budget.max_model_calls >= self.recipe.max_epochs*((self.budget.train_learners+3)//4)
                 +2*(self.recipe.max_epochs+1)*((self.budget.selection_learners+3)//4),
             'reserve whole declared selected workload')
        for name, digest in self.expected_sources:
            need(name in SOURCE_NAMES or (name.startswith(('src/knowledge_tracing/', 'scripts/', 'tests/gkt/'))
                 and name.endswith('.py')), 'only explicit source files, never data/oracle paths')
            _path(ROOT, name); sha(digest)

    @property
    def identity(self):
        return identity_hash(asdict(self))

    @property
    def output(self):
        return _path(ROOT, 'experiments/gkt/results/'+self.run_id)


def _read(pin, cap):
    path = _path(ROOT, pin.path)
    need(path.suffix == '.json' and (path.is_relative_to(ROOT/'artifacts/akt')
         or path.is_relative_to(ROOT/'research_tracking/runs')), 'bounded runtime/acceptance JSON role required')
    value, digest, _ = _read_json(path, cap)
    need(digest == pin.sha256, 'actual evidence byte SHA mismatch')
    return canonical(value)


def _component(ref, sources, cap):
    outer, child, owned = (_read(pin, cap) for pin in (ref.outer, ref.child, ref.owned))
    count, status, child_status = {
        'model11': (11, 'ACCEPTED_GKT11_CPU_COMPUTE_NOT_FITTED', 'ACCEPTED_GKT11_CPU_COMPUTE_PENDING_OUTER'),
        'trainer8': (8, 'ACCEPTED_GKT8_TRAINER_CPU_COMPUTE_NOT_FITTED', 'ACCEPTED_GKT8_TRAINER_CPU_COMPUTE_PENDING_OUTER'),
        'checkpoint28': (28, 'ACCEPTED_GKT28_CPU_EPOCH_CHECKPOINT_NOT_LIFECYCLE_FIT', 'ACCEPTED_GKT28_CHECKPOINT_CPU_PENDING_OUTER'),
    }[ref.kind]
    counts = dict(tests=count, failures=0, errors=0, skipped=0)
    need(outer['status'] == status and outer['errors'] == [] and outer['counts'] == child['counts'] == counts
         and child['status'] == child_status and child['pytest_exit_code'] == 0
         and outer['child_result'] == child and outer['owned_receipt'] == owned
         and child['source_before'] == child['source_after'] == outer['source_before'] == outer['source_after']
         and child['runtime_before'] == child['runtime_after'] == outer['runtime_before'] == outer['runtime_after']
         and child['error'] is None and child['junit_error'] is None
         and child['forbidden'] == child['monitor_errors'] == [] and child['monitor_stopped'] is True
         and child['environment_restored'] is True and child['method_restoration']['accepted'] is True
         and child['method_restoration']['restore_errors'] == []
         and child['counters'] == child['expected_counters'],
         'genuine GKT component acceptance required')
    need(all(type(v) is int for value in (outer['counts'], child['counts']) for v in value.values()),
         'component counts must be exact integers')
    need(owned['accepted'] is True and owned['returncode'] == 0 and owned['cleanup_accepted'] is True
         and owned['job_active_after_cleanup'] == 0 and owned['popen_handle_closed'] is True
         and owned['actual_worker_in_job_before_GO'] is True and owned['errors'] == owned['cleanup_errors'] == [],
         'component owned terminal/cleanup required')
    worker = Path(owned['command'][2])
    need(worker.is_relative_to(ROOT/'artifacts/akt/local-tests')
         and _hash_file(_path(ROOT,worker.relative_to(ROOT).as_posix()), cap=cap)[0] == owned['worker_sha256'],
         'actual component worker source binding')
    critical = ['src/knowledge_tracing/gkt/'+name for name in ('config.py','core.py','recurrent.py','research_model.py')]
    if ref.kind != 'model11':
        critical += ['src/knowledge_tracing/gkt/'+name for name in ('research_data.py','research_training.py','training.py')]
    if ref.kind == 'checkpoint28':
        critical += ['src/knowledge_tracing/gkt/research_checkpoint.py','src/knowledge_tracing/sakt/research_checkpoint.py']
    need(all(child['source_after'].get(name) == sources[name] for name in critical), 'current GKT component bytes differ')
    junit = _path(ROOT,ref.junit.path)
    need(junit.suffix == '.xml' and junit.parent == _path(ROOT,ref.child.path).parent
         and _hash_file(junit,cap=cap)[0] == ref.junit.sha256
         and outer['outputs']['junit.xml']['sha256'] == ref.junit.sha256, 'actual hash-bound component JUnit')
    cases = list(ET.fromstring(junit.read_bytes()).iter('testcase'))
    need(len(cases) == count and len({(c.get('classname'),c.get('name')) for c in cases}) == count
         and not any(list(c.iter(tag)) for c in cases for tag in ('failure','error','skipped')),
         'exact physical component cases, no failed/skipped descendants')
    for pin in (ref.outer, ref.child):
        need(not _path(ROOT, pin.path).with_name('postwrite_rejection.json').exists(), 'component late rejection')
    return canonical(asdict(ref))


def _inspect(spec, evidence):
    spec.__post_init__(); evidence.__post_init__()
    b = spec.budget
    sources = dict(spec.expected_sources)
    for name, digest in sources.items():
        need(_hash_file(_path(ROOT, name), cap=b.max_source_file_bytes)[0] == digest, 'current source drift')
    need(sources[RECIPE_PATH] == RECIPE_SHA256, 'adopted recipe30 bytes required')
    runtime = _read(evidence.runtime, b.max_metadata_bytes)
    lock = _path(ROOT, evidence.lock.path)
    need(lock == ROOT/'requirements-akt.lock.txt'
         and _hash_file(lock, cap=b.max_source_file_bytes)[0] == evidence.lock.sha256, 'actual isolated lock binding')
    environment = ROOT/'.venv'
    _path(ROOT, '.venv')
    runtime_helpers.validate_runtime_interpreter(environment, executable=sys.executable, prefix=sys.prefix, platform_id=sys.platform)
    need(runtime.get('runtime_schema_version') == 2 and runtime.get('device') == 'cpu'
         and runtime.get('cuda_available') is False and runtime.get('platform_id') == sys.platform
         and Path(runtime['project_root']).resolve() == ROOT
         and Path(runtime['python_prefix']).resolve() == environment
         and os.path.normcase(runtime['python']) == os.path.normcase(sys.executable)
         and Path(runtime['lock_file']).resolve() == lock and runtime['lock_sha256'] == evidence.lock.sha256,
         'genuine schema2 CPU runtime for current interpreter/root/lock required')
    for key in ('torch_origin', 'numpy_origin'):
        origin = Path(runtime[key])
        need(origin.is_absolute() and origin.resolve().is_relative_to(environment), 'runtime package origin outside venv')
    expected_runtime = {Path(sys.executable).relative_to(ROOT).as_posix(), '.venv/pyvenv.cfg',
        Path(runtime['torch_origin']).relative_to(ROOT).as_posix(), Path(runtime['numpy_origin']).relative_to(ROOT).as_posix()}
    need(expected_runtime <= {pin.path for pin in evidence.runtime_files}, 'interpreter/config/package origin pins missing')
    for pin in evidence.runtime_files:
        lexical = ROOT/pin.path
        entry = environment/('bin/python' if sys.platform == 'linux' else 'Scripts/python.exe')
        if sys.platform == 'linux' and lexical == entry:
            path = lexical.resolve(strict=True)
            need(path == Path(sys._base_executable).resolve(strict=True), 'approved lexical venv/base interpreter binding')
        else:
            path = _path(ROOT, pin.path)
            need(path.is_relative_to(environment), 'runtime pin outside physical venv')
        need(_hash_file(path, cap=b.max_source_file_bytes)[0] == pin.sha256, 'current isolated runtime file drift')
    pointer = _read(evidence.gate_pointer, b.max_metadata_bytes)
    need(set(pointer) == {'schema_version', 'evidence_file', 'evidence_sha256', 'test_log_file', 'test_log_sha256'}
         and type(pointer['schema_version']) is int and pointer['schema_version'] == 1, 'closed Gate pointer')
    base = _path(ROOT, evidence.gate_pointer.path).parent
    need(base == ROOT/'artifacts/akt/preflight', 'canonical Gate directory required')
    for key in ('evidence_file', 'test_log_file'):
        need(type(pointer[key]) is str and Path(pointer[key]).name == pointer[key], 'Gate member leaf required')
    need(pointer['evidence_file'].startswith('gate2-') and pointer['evidence_file'].endswith('.json')
         and pointer['test_log_file'].startswith('gate2-tests-') and pointer['test_log_file'].endswith('.log'),
         'canonical Gate member names required')
    report_path, log_path = base/pointer['evidence_file'], base/pointer['test_log_file']
    report, digest, _ = _read_json(report_path, b.max_metadata_bytes)
    need(digest == pointer['evidence_sha256']
         and _hash_file(log_path, cap=b.max_source_file_bytes)[0] == pointer['test_log_sha256'], 'Gate report/log SHA')
    runtime_helpers.validate_gate2_elapsed_budget(report['elapsed_seconds'], report['timeout_seconds'])
    build = runtime_helpers.gate2_build_hashes(ROOT)
    if sys.platform == 'linux':
        need(report.get('execution_profile') == dict(schema_version=1, platform_id='linux', project_root=str(ROOT),
             python=sys.executable, python_prefix=sys.prefix, writer_sha256=build['scripts/akt/refresh_gate2.py']),
             'actual same-root Linux Gate writer/profile membership required')
    counts = report['test_result']
    need(type(report['schema_version']) is int and report['schema_version'] == 1 and report['status'] == 'PASS'
         and report['suite'] == 'tests/akt tests/shared_kt' and type(counts['passed']) is int and counts['passed'] > 0
         and all(type(counts[k]) is int and counts[k] == 0 for k in ('failed', 'errors', 'skipped'))
         and report['build_hashes'] == build and report['lock_sha256'] == evidence.lock.sha256
         and report['source_commit'] == runtime['source']['commit']
         and report['test_log_sha256'] == pointer['test_log_sha256'], 'actual current-source shared Gate required')
    components = [_component(ref, sources, b.max_metadata_bytes) for ref in evidence.components]
    topology_path = _path(ROOT,spec.topology.path)
    topology, topology_sha, _ = _read_json(topology_path,b.max_metadata_bytes)
    need(topology_sha == spec.topology.sha256 and set(topology) == {'nodes','edges'}
         and type(topology['nodes']) is list and len(topology['nodes']) == 28
         and all(type(n) is str and n for n in topology['nodes'])
         and sorted(set(topology['nodes'])) == topology['nodes']
         and type(topology['edges']) is list and len(topology['edges']) <= 28*27
         and all(type(e) is list and len(e) == 2 and all(type(n) is str and n in topology['nodes'] for n in e)
                 and e[0] != e[1] for e in topology['edges'])
         and sorted({tuple(e) for e in topology['edges']}) == [tuple(e) for e in topology['edges']],
         'closed actual directed concept28 expert topology')
    pending = set(topology['nodes'])
    while pending:
        roots = {n for n in pending if not any(c == n and p in pending for p,c in topology['edges'])}
        need(bool(roots),'expert topology cycle')
        pending.difference_update(roots)
    corpus_root = 'artifacts/simulator/corpora/'+spec.corpus_id+'/'
    done, digest, _ = _read_json(_path(ROOT, corpus_root+'DONE.json'), b.max_metadata_bytes)
    need(digest == spec.done_sha256 and done['status'] == 'COMPLETE_SIMULATOR_CORPUS'
         and done['corpus_sha256'] == spec.corpus_sha256 and set(done['files_sha256']) == set(public_reader.PUBLIC_FILES)
         and not _path(ROOT, corpus_root+'failure.json').exists(), 'complete public corpus required')
    for name, digest in done['files_sha256'].items():
        need(_hash_file(_path(ROOT, corpus_root+name), cap=json.loads(spec.read_limits_json)['max_file_bytes'])[0] == digest,
             'public corpus bytes drift')
    need(done['files_sha256']['corpus.json'] == spec.corpus_sha256, 'external corpus SHA')
    corpus, _, _ = _read_json(_path(ROOT, corpus_root+'corpus.json'), b.max_metadata_bytes)
    need(corpus['protocol_sha256'] == spec.context.protocol21_sha256
         and corpus['bank_sha256'] == spec.context.bank_sha256
         and corpus['domain_sha256'] == spec.context.domain_sha256
         and corpus['research_plan_sha256'] == spec.context.split_sha256, 'corpus/context metadata mismatch')
    need(all(sources.get(name, build.get(name)) == pin for name, pin in corpus['source_inventory'].items()),
         'actual producer dependency bytes differ from corpus provenance')
    return canonical(dict(scope=SCOPE, candidate_id='GKT', recipe_sha256=RECIPE_SHA256, spec_sha256=spec.identity,
        sources_sha256=identity_hash(sources), source_files=sources, runtime_sha256=evidence.runtime.sha256,
        runtime_files=[asdict(pin) for pin in evidence.runtime_files],
        gate_pointer=asdict(evidence.gate_pointer), gate_report_sha256=pointer['evidence_sha256'],
        components=components, topology=asdict(spec.topology), public_files=done['files_sha256'], done_sha256=spec.done_sha256,
        context=asdict(spec.context), caps=asdict(b), refit_allowed=False, calibration_allowed=False))


def prepare_gkt_selected_identity(spec, evidence):
    """Inspection thực từ file, chưa cấp permission và không tạo model/data view."""
    need(type(spec) is GKTSelectedExecutionSpec and type(evidence) is GKTSelectedEvidence, 'typed GKT inspection required')
    return _inspect(spec, evidence)


class AuthorizedGKTSelectedExecution:
    def __init__(self, spec, evidence, authorization_path, authorization_sha256, identity, started, seal):
        need(seal is _SEAL, 'use actual closed GKT authorization factory')
        self.spec, self.evidence = spec, evidence
        self.authorization_path, self.authorization_sha256 = authorization_path, authorization_sha256
        self.identity_json = json.dumps(identity, sort_keys=True, allow_nan=False)
        self.started = started

    def guard(self, training_seconds=0.):
        need(type(training_seconds) in (int, float) and math.isfinite(training_seconds) and training_seconds >= 0,
             'finite cumulative training time required')
        elapsed = max(time.perf_counter()-self.started[0], time.time()-self.started[1])
        b = self.spec.budget
        need(elapsed < b.max_wall_seconds and training_seconds < b.max_training_seconds, 'cumulative GKT wall/train deadline')
        from knowledge_tracing.akt.resources import memory_snapshot
        sample = memory_snapshot()
        need(max(sample['process_rss_bytes'], sample['process_peak_rss_bytes'] or 0) <= b.max_worker_rss_bytes
             and sample['system_available_ram_bytes'] >= b.min_available_ram_bytes, 'GKT worker/free RAM budget')

    def revalidate(self, training_seconds=0.):
        self.guard(training_seconds)
        need(_inspect(self.spec, self.evidence) == json.loads(self.identity_json), 'authorized GKT source/runtime/input drift')
        need(_hash_file(self.authorization_path, cap=self.spec.budget.max_metadata_bytes)[0] == self.authorization_sha256,
             'GKT authorization changed')
        self.guard(training_seconds)


def require_gkt_selected_authorization(spec, evidence, *, authorization_file, expected_authorization_sha256):
    """Chỉ closed file/bindings thật; không grant từ bool hoặc metadata stage."""
    need(type(spec) is GKTSelectedExecutionSpec and type(evidence) is GKTSelectedEvidence, 'typed GKT admission required')
    sha(expected_authorization_sha256)
    started = (time.perf_counter(), time.time())
    authpath = _path(ROOT, authorization_file)
    need(authpath.is_relative_to(ROOT/'experiments/gkt/authorizations')
         or authpath.is_relative_to(ROOT/'artifacts/akt'), 'GKT authorization file role')
    auth, digest, _ = _read_json(authpath, spec.budget.max_metadata_bytes)
    fields = {'schema_version', 'scope', 'decision', 'run_id', 'spec_sha256', 'recipe_sha256',
              'identity', 'caps', 'requested_phases', 'approval_reference'}
    need(digest == expected_authorization_sha256 and set(auth) == fields
         and type(auth['schema_version']) is int and auth['schema_version'] == 1
         and auth['scope'] == SCOPE and auth['decision'] == 'AUTHORIZE_BOUNDED_GKT_MAIN_SELECTED_ONLY'
         and auth['run_id'] == spec.run_id and auth['spec_sha256'] == spec.identity
         and auth['recipe_sha256'] == RECIPE_SHA256 and auth['requested_phases'] == list(PHASES)
         and identity_hash(auth['caps']) == identity_hash(asdict(spec.budget))
         and type(auth['approval_reference']) is str and 0 < len(auth['approval_reference'].strip()) <= 256,
         'actual closed GKT authorization required; no A0 or stage grant')
    need(not spec.output.exists() and spec.output.parent.is_dir(), 'fresh owned GKT result path required')
    identity = _inspect(spec, evidence)
    need(identity_hash(auth['identity']) == identity_hash(identity), 'authorization identity mismatch')
    actual = AuthorizedGKTSelectedExecution(spec, evidence, authpath, digest, identity, started, _SEAL)
    actual.guard()
    from knowledge_tracing.akt.resources import memory_snapshot
    need(memory_snapshot()['system_available_ram_bytes'] >= spec.budget.prelaunch_available_ram_bytes,
         'GKT preallocation RAM floor')
    return actual
