"""Một worker Method24 hữu hạn; ROOT phải review request trước chạy.

Stdlib trước worker_gate; không collector/oracle/Torch/NN. Public corpus reader
audit9publicfiles+DONE rồi chỉ TRAIN đi vào optimization. RAM polling cooperative,
không hard OS quota; outer/ownedJob cleanup+terminal acceptance vẫn bắt buộc.
"""
import argparse
from dataclasses import asdict
import builtins
import csv
import hashlib
import importlib
import io
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
PREP_REL = 'artifacts/akt/local-tests/akt-research-runner-20261108-01'
CONFIG = PREP_REL + '/method24_config01.json'
PROFILE = PREP_REL + '/method24_runtime_profile01.json'
REQUEST = PREP_REL + '/method24_request01.json'
OUTPUT = PREP_REL + '/method24-native01'
SELF = PREP_REL + '/method24_worker01.py'
OUTER = PREP_REL + '/run_method24_native01.py'
SOURCES = (SELF, OUTER, 'src/knowledge_tracing/edge_confidence.py',
    'src/knowledge_tracing/simulator_corpus_reader.py', 'src/knowledge_tracing/simulator_research_data.py',
    'src/knowledge_tracing/simulator_data.py', 'src/knowledge_tracing/simulator_bridge.py',
    'src/knowledge_tracing/akt/resources.py', 'scripts/research/windows_owned_worker.py', 'src/knowledge_tracing/__init__.py',
    'src/knowledge_tracing/akt/__init__.py')
PUBLIC = ('corpus.json', 'bank.json', 'plan.json', 'train.jsonl', 'train.manifest.json',
    'selection.jsonl', 'selection.manifest.json', 'calibration.jsonl', 'calibration.manifest.json', 'DONE.json')
DATA_FILES = ('recipe.json', 'folds.json', 'fit-ledger.jsonl', 'baseline-oof.csv', 'edge-oof.csv',
              'learner-deltas.csv', 'edges.jsonl', 'graph.json')
OUTPUT_FILES = ('reservation.json', 'runtime.json', 'resources.json', 'input-source-inventory.json',
                *DATA_FILES, 'worker_result.json', 'DONE.json')
COUNTS = dict(train_learners=48, train_events=10080, concepts=28, edges=756,
              fit_slots=2352, oof_rows=272160, baseline_oof_rows=10080, dag_budget=31, source_files=11)
RECIPE = dict(method_id='train-lagged-edge-confidence-v1',seed=42,folds=3,laplace_alpha=1.,support_scale=5.,
              C=1.,tol=1e-6,max_iter=200,clip=1e-6,bootstrap_replicates=200,min_eligible_learners=20)
CAPS = dict(outer_seconds=120, active_seconds=110, cleanup_seconds=3, outer_finalization_seconds=7,
    export_reserve_seconds=8, max_rss_bytes=536870912, min_available_ram_bytes=1073741824,
    poll_seconds=.1, max_total_output_bytes=134217728, max_oof_file_bytes=100663296, max_stdout_stderr_bytes=65536)
PACKAGES = {'numpy': ('numpy', '2.5.4', 'numpy'), 'sklearn': ('scikit_learn', '1.9.1', 'sklearn'),
    'scipy': ('scipy', '1.18.1', 'scipy'), 'joblib': ('joblib', '1.6.0', 'joblib'),
    'threadpoolctl': ('threadpoolctl', '3.7.0', 'threadpoolctl.py'), 'psutil': ('psutil', '7.2.2', 'psutil'),
    'pandas': ('pandas', '3.0.6', 'pandas')}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def valid_sha(value):
    need(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'lowercase SHA256 required')


def safe(relative):
    need(type(relative) is str and relative and '\\' not in relative and ':' not in relative, 'relative POSIX path required')
    parts = Path(relative).parts
    need(not Path(relative).is_absolute() and '..' not in parts and '.' not in parts, 'unsafe relative path')
    need(ROOT.resolve() == ROOT.absolute() and not ROOT.is_symlink() and not getattr(ROOT, 'is_junction', lambda:False)(), 'physical fixed ROOT')
    path = ROOT
    for part in parts:
        path /= part
        need(not path.is_symlink() and not getattr(path, 'is_junction', lambda:False)(), 'path alias')
    need(path.resolve().is_relative_to(ROOT.resolve()), 'outside fixed ROOT')
    return path


def hash_file(relative, *, cap=33554432, check=lambda: None):
    path = safe(relative)
    need(path.is_file() and path.stat().st_size <= cap, 'bounded regular file required')
    digest, count = hashlib.sha256(), 0
    with path.open('rb') as handle:
        while chunk := handle.read(65536):
            count += len(chunk)
            need(count <= cap, 'read byte cap')
            digest.update(chunk)
            check()
    need(path.stat().st_size == count, 'file size drift')
    return digest.hexdigest()


def read_json(relative, expected, cap=262144):
    valid_sha(expected)
    path = safe(relative)
    with path.open('rb') as handle:
        raw = handle.read(cap+1)
    need(len(raw) <= cap and hashlib.sha256(raw).hexdigest() == expected, 'bounded JSON SHA mismatch')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite JSON: ' + value)
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=bad)
    need(type(value) is dict, 'JSON object required')
    return value


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))+'\n').encode()


def validate_profile(profile):
    need(type(profile) is dict and set(profile) == {'schema_version', 'scope', 'lock_relative', 'lock_sha256',
        'protocol_relative', 'protocol_sha256', 'entry_sha256', 'cfg_sha256', 'method_source_sha256', 'extra_sources', 'packages', 'limits_vi'}, 'runtime profile schema')
    need(type(profile['schema_version']) is int and profile['schema_version'] == 1 and
         profile['lock_relative'] == 'requirements-akt.lock.txt' and
         profile['protocol_relative'] == 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md', 'fixed runtime inputs')
    files = {profile['lock_relative']:profile['lock_sha256'], profile['protocol_relative']:profile['protocol_sha256'],
             '.venv/Scripts/python.exe':profile['entry_sha256'], '.venv/pyvenv.cfg':profile['cfg_sha256']}
    need(type(profile['extra_sources']) is dict and set(profile['extra_sources']) == {
         '.venv/Lib/site-packages/sklearn/linear_model/_logistic.py'}, 'one public solver source binding')
    files.update(profile['extra_sources'])
    need(type(profile['packages']) is dict and set(profile['packages']) == set(PACKAGES), 'selected seven package profiles')
    for module, (distribution, version, location) in PACKAGES.items():
        item = profile['packages'][module]
        need(type(item) is dict and set(item) == {'distribution', 'version', 'required', 'metadata_relative', 'metadata_sha256',
            'record_relative', 'record_sha256', 'module_relative', 'module_sha256'}, 'package profile schema')
        prefix = '.venv/Lib/site-packages/'
        origin = prefix + location + ('' if location.endswith('.py') else '/__init__.py')
        need(item['version'] == version and type(item['required']) is bool and item['required'] == (module != 'pandas') and
             item['metadata_relative'] == prefix+distribution+'-'+version+'.dist-info/METADATA' and
             item['record_relative'] == prefix+distribution+'-'+version+'.dist-info/RECORD' and
             item['module_relative'] == origin, 'fixed package paths/versions')
        for kind in ('metadata', 'record', 'module'):
            files[item[kind+'_relative']] = item[kind+'_sha256']
    for name, digest in files.items():
        valid_sha(digest)
        need(hash_file(name) == digest, 'runtime file drift: '+name)
    valid_sha(profile['method_source_sha256'])
    return files


def validate_request(relative, expected_sha):
    need(relative == REQUEST, 'fixed Method24 request only')
    request = read_json(relative, expected_sha)
    need(set(request) == {'schema_version', 'purpose', 'approval_reference', 'config_sha256', 'source_sha256',
        'runtime_profile_sha256', 'public_sha256', 'output_relative', 'source_count'}, 'closed request schema')
    need(type(request['schema_version']) is int and request['schema_version'] == 1 and
         request['purpose'] == 'method24_train_only_conditional_surrogate' and
         type(request['approval_reference']) is str and request['approval_reference'].strip(), 'reviewed purpose/reference')
    # Reject unapproved source paths BEFORE opening any path from this mapping.
    need(type(request['source_count']) is int and request['source_count'] == 11 and
         type(request['source_sha256']) is dict and set(request['source_sha256']) == set(SOURCES), 'exact eleven source paths required')
    config = read_json(CONFIG, request['config_sha256'])
    need(set(config) == {'schema_version', 'purpose', 'corpus', 'recipe', 'counts', 'caps', 'scope_vi'} and
         type(config['schema_version']) is int and config['schema_version'] == 1 and
         config['purpose'] == request['purpose'] and encode(config['counts']) == encode(COUNTS) and
         encode(config['caps']) == encode(CAPS) and encode(config['recipe']) == encode(RECIPE), 'fixed config/counts/caps/recipe')
    c = config['corpus']
    need(set(c) == {'id', 'corpus_sha256', 'done_sha256', 'plan_sha256', 'train_provenance_sha256', 'train_observable_sha256',
        'prior_inventory_relative', 'prior_inventory_sha256'} and c['id'] == 'grade10-development-lifecycle01-20261108' and
        c['prior_inventory_relative'] == 'artifacts/akt/local-tests/development-corpus-20261108-01/canonical-corpus-inventory01.json', 'fixed corpus inputs')
    prior = read_json(c['prior_inventory_relative'], c['prior_inventory_sha256'])
    prefix = 'artifacts/simulator/corpora/'+c['id']+'/'
    expected_public = {name:prior['files'][prefix+name]['sha256'] for name in PUBLIC}
    need(type(request['public_sha256']) is dict and request['public_sha256'] == expected_public and
         expected_public['corpus.json'] == c['corpus_sha256'] and expected_public['DONE.json'] == c['done_sha256'] and
         expected_public['train.jsonl'] == c['train_observable_sha256'], 'public input identities')
    need(request['output_relative'] == OUTPUT and not safe(OUTPUT).exists(), 'exclusive fixed output directory')
    profile = read_json(PROFILE, request['runtime_profile_sha256'])
    runtime_files = validate_profile(profile)
    for name, digest in request['source_sha256'].items():
        valid_sha(digest)
        need(hash_file(name, cap=262144) == digest, 'source drift: '+name)
    need(request['source_sha256']['src/knowledge_tracing/edge_confidence.py'] == profile['method_source_sha256'], 'method/runtime profile binding')
    need(not safe(prefix+'failure.json').exists(), 'canonical corpus failure override')
    for name, digest in expected_public.items():
        need(hash_file(prefix+name) == digest, 'public input drift: '+name)
    return request, config, profile, runtime_files


class Guard:
    def __init__(self, memory, caps, deadline_perf, deadline_wall):
        self.memory, self.caps = memory, caps
        self.deadline_perf, self.deadline_wall = deadline_perf, deadline_wall
        self.samples = 0
        self.peak_rss = 0
        self.minimum_available = None

    def left(self):
        remaining = min(self.deadline_perf-time.perf_counter(), self.deadline_wall-time.time())
        need(math.isfinite(remaining) and remaining > 0, 'active global deadline')
        sample = self.memory()
        rss, peak, free = sample['process_rss_bytes'], sample['process_peak_rss_bytes'], sample['system_available_ram_bytes']
        need(type(rss) is int and rss >= 0 and (peak is None or type(peak) is int and peak >= 0) and
             type(free) is int and free >= 0, 'valid memory telemetry')
        self.samples += 1
        self.peak_rss = max(self.peak_rss, rss, peak or 0)
        self.minimum_available = free if self.minimum_available is None else min(free, self.minimum_available)
        need(self.peak_rss <= self.caps['max_rss_bytes'], 'worker RSS/peak cap')
        need(free >= self.caps['min_available_ram_bytes'], 'worker available RAM floor')
        remaining = min(self.deadline_perf-time.perf_counter(), self.deadline_wall-time.time())
        need(remaining > 0, 'active deadline after telemetry')
        return remaining

    def summary(self):
        return dict(samples=self.samples, observed_peak_rss_bytes=self.peak_rss,
                    observed_minimum_available_ram_bytes=self.minimum_available,
                    guard_scope='observed polling plus inline checks, not hard OS quota')


class Writer:
    def __init__(self, directory, caps, guard):
        self.directory, self.caps, self.guard = directory, caps, guard
        self.files, self.bytes = {}, 0

    def chunks(self, name, chunks):
        need(name in OUTPUT_FILES and name not in self.files, 'fixed exclusive output filename')
        path = self.directory/name
        count = 0
        cap = self.caps['max_oof_file_bytes'] if name == 'edge-oof.csv' else self.caps['max_total_output_bytes']
        with path.open('xb') as handle:
            buffer = bytearray()
            for chunk in chunks:
                need(type(chunk) is bytes, 'bytes-only writer')
                count += len(chunk)
                self.bytes += len(chunk)
                need(count <= cap and self.bytes <= self.caps['max_total_output_bytes'], 'output byte cap')
                buffer.extend(chunk)
                if len(buffer) >= 65536:
                    need(handle.write(buffer) == len(buffer), 'short output write')
                    buffer.clear()
                    self.guard.left()
            if buffer:
                need(handle.write(buffer) == len(buffer), 'short output write')
            self.guard.left()
            handle.flush()
            os.fsync(handle.fileno())
        rel = path.relative_to(ROOT).as_posix()
        self.files[name] = dict(sha256=hash_file(rel, cap=cap, check=self.guard.left), bytes=count)

    def json(self, name, value):
        self.chunks(name, (encode(value),))

    def csv(self, name, header, rows):
        def lines():
            for values in (header,):
                buffer = io.StringIO(newline='')
                csv.writer(buffer, lineterminator='\n').writerow(values)
                yield buffer.getvalue().encode()
            for values in rows:
                buffer = io.StringIO(newline='')
                csv.writer(buffer, lineterminator='\n').writerow('' if v is None else format(v,'.17g') if type(v) is float else v for v in values)
                yield buffer.getvalue().encode()
        self.chunks(name, lines())


class Monitor:
    def __init__(self, guard, directory):
        self.guard, self.directory = guard, directory
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        def watch():
            while not self.stop_event.wait(self.guard.caps['poll_seconds']):
                try:
                    self.guard.left()
                except Exception as error:
                    try:
                        with (self.directory/'resource-failure.json').open('xb') as handle:
                            handle.write(encode(dict(status='REJECTED_RESOURCE_MONITOR', reason=str(error),
                                reservation_solver_calls=2352, actual_solver_calls=None, resources=self.guard.summary())))
                            handle.flush();os.fsync(handle.fileno())
                    finally:
                        os._exit(125)  # Exact current owned worker; helper cleans its Job.
        self.thread = threading.Thread(target=watch, daemon=True, name='method24-observed-resource-guard')
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=.5)
            need(not self.thread.is_alive(), 'resource monitor shutdown unverified')


def install_access_guards(corpus_id):
    base = safe('artifacts/simulator/corpora/'+corpus_id)
    observed = dict(public_opens=set(), forbidden_imports=[], subprocess_attempts=0)
    def audit(event, args):
        if event == 'subprocess.Popen':
            observed['subprocess_attempts'] += 1
            raise RuntimeError('worker cannot create child process')
        if event in ('open', 'os.listdir', 'os.scandir') and args and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).absolute()
            if path.is_relative_to(base):
                need(event == 'open' and path.parent == base and path.name in PUBLIC, 'oracle/nonpublic corpus access denied')
                observed['public_opens'].add(path.name)
    original = builtins.__import__
    def imported(name, *args, **kwargs):
        if name.split('.')[0] == 'torch' or name in ('knowledge_tracing.paper2_reference',
            'knowledge_tracing.simulator_research_collection', 'knowledge_tracing.simulator_collection',
            'knowledge_tracing.simulator_corpus_publisher'):
            observed['forbidden_imports'].append(name)
            raise RuntimeError('teacher/NN/publisher import forbidden')
        return original(name, *args, **kwargs)
    sys.addaudithook(audit)
    builtins.__import__ = imported
    return observed


def runtime_origins(profile, guard, *, import_required):
    origins = {}
    for name, item in profile['packages'].items():
        if import_required and item['required']:
            importlib.import_module(name)
            guard.left()
        module = sys.modules.get(name)
        if module is None:
            need(not item['required'], 'required module not loaded')
            continue
        origin = safe(item['module_relative'])
        need(Path(module.__file__).absolute() == origin and Path(module.__file__).resolve() == origin.resolve()
             and module.__version__ == item['version'], 'actual version/origin mismatch: '+name)
        origins[name] = dict(version=module.__version__, origin=item['module_relative'], sha256=hash_file(item['module_relative']))
    need('torch' not in sys.modules, 'Torch must stay unimported')
    return origins


def export_result(writer, result, graph, prepared, config):
    need(len(result.fit_records) == 2352 and len(result.oof_rows) == 272160 and len(result.edges) == 756,
         'whole fit/OOF/edge population required')
    result.assert_integrity()
    writer.json('recipe.json', asdict(result.recipe))
    writer.json('folds.json', dict(prepared_sha256=prepared.identity, folds=prepared.folds, learner_ids=prepared.learner_ids))
    writer.chunks('fit-ledger.jsonl', (encode(asdict(r)) for r in result.fit_records))
    baseline = {}
    for row in result.oof_rows:
        key = row.learner_id, row.source_row, row.child_id, row.heldout_fold
        value = row.correct, row.base_probability
        need(key not in baseline or baseline[key] == value, 'baseline OOF reuse parity mismatch')
        baseline[key] = value
    need(len(baseline) == 10080, 'baseline full population mismatch')
    writer.csv('baseline-oof.csv', ('learner_id','source_row','child_id','heldout_fold','y','base_probability'),
        ((*key,*baseline[key]) for key in sorted(baseline)))
    writer.csv('edge-oof.csv', ('parent_id','child_id','learner_id','source_row','heldout_fold','y','eligible',
        'base_probability','augmented_probability','paired_delta','reason'),
        ((r.parent_id,r.child_id,r.learner_id,r.source_row,r.heldout_fold,r.correct,int(r.eligible),
          r.base_probability,r.augmented_probability,r.paired_delta,r.reason) for r in result.oof_rows))
    writer.csv('learner-deltas.csv', ('parent_id','child_id','learner_id','paired_delta'),
        ((edge.parent_id,edge.child_id,learner,delta) for edge in result.edges for learner,delta in edge.learner_deltas))
    writer.chunks('edges.jsonl', (encode(asdict(e)) for e in result.edges))
    need(graph.status in ('SUPPORTED_DAG', 'UNSUPPORTED_EDGE_BUDGET') and
         (graph.status != 'SUPPORTED_DAG' or len(graph.edges) == config['counts']['dag_budget']), 'graph status/budget')
    writer.json('graph.json', asdict(graph))


def _domain_api():
    from knowledge_tracing import edge_confidence
    from knowledge_tracing import simulator_corpus_reader
    return edge_confidence, simulator_corpus_reader


def _memory_api():
    from knowledge_tracing.akt.resources import memory_snapshot
    return memory_snapshot


def owned_launch_manifest(args, owner, request):
    """Bridge only this helper-owned absolute manifest, not arbitrary abs input."""
    from windows_owned_worker import safe as owned_safe, bounded as owned_bounded
    relative = PREP_REL+'/method24-owned01/launch.json'
    expected = ROOT/relative
    candidate = Path(os.environ['KLTN_WINDOWS_LAUNCH_MANIFEST'])
    need(candidate.is_absolute() and candidate == expected, 'exact reviewed owned absolute manifest path required')
    path = owned_safe(candidate)  # Existing helper's physical ROOT/alias guards.
    need(path == expected and path.relative_to(ROOT).as_posix() == relative, 'owned manifest relocation forbidden')
    payload = owned_bounded(path, 32768)  # Single bounded payload; no alternate absolute reader.
    launch = json.loads(payload)
    expected_argv = ['--request',args.request,'--request-sha256',args.request_sha256,
        '--active-deadline-perf',repr(args.active_deadline_perf),'--active-deadline-wall',repr(args.active_deadline_wall)]
    need(type(launch) is dict and type(launch.get('schema_version')) is int and launch['schema_version'] == 1 and
         launch.get('nonce') == owner['nonce'] and launch.get('parent') == owner['parent_owner'] and
         launch.get('job_name') == owner['job_name'] and launch.get('worker_relative') == SELF and
         launch.get('worker_sha256') == request['source_sha256'][SELF] and
         launch.get('helper_sha256') == request['source_sha256']['scripts/research/windows_owned_worker.py'] and
         launch.get('worker_args') == expected_argv and launch.get('entry') == str(ROOT/'.venv/Scripts/python.exe') and
         launch.get('approval_reference') == request['approval_reference'], 'owned manifest parent/source/nonce/argv mismatch')
    return launch


def run(args, owner):
    need(type(owner) is dict and owner.get('status') == 'OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE' and
         owner.get('worker', {}).get('pid') == os.getpid(), 'exact current owned worker required before writes')
    need(all(type(v) in (int,float) and math.isfinite(v) for v in (args.active_deadline_perf, args.active_deadline_wall)), 'explicit active deadlines')
    request, config, profile, runtime_files = validate_request(args.request, args.request_sha256)
    launch = owned_launch_manifest(args, owner, request)
    deadline_perf = min(args.active_deadline_perf, launch['active_deadline'])
    need(0 < deadline_perf-time.perf_counter() <= 110 and 0 < args.active_deadline_wall-time.time() <= 110, 'bounded remaining active allowance')
    sys.path.insert(0, str(ROOT/'src'))
    guard = Guard(_memory_api(), config['caps'], deadline_perf, args.active_deadline_wall)
    guard.left()  # Before output directory, domain/NumPy/SciPy/sklearn imports.
    output = safe(OUTPUT)
    output.mkdir(parents=True, exist_ok=False)
    writer = Writer(output, config['caps'], guard)
    monitor = Monitor(guard, output)
    result = prepared = None
    try:
        writer.json('reservation.json', dict(status='RESERVED_NOT_ACTUAL_FIT_COUNTS', fit_slots=2352,
            solver_calls=None, oof_rows=272160, teacher_calls=0, neural_optimizer_steps=0,
            automatic_retry=False, request_sha256=args.request_sha256, owner=owner))
        monitor.start()
        # Helper deliberately freezes2threads; this phase explicitly overrides1 before imports.
        os.environ.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                          CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void')
        access = install_access_guards(config['corpus']['id'])
        ec, reader = _domain_api()
        guard.left()
        recipe = ec.EdgeConfidenceRecipe(**config['recipe'])
        c = config['corpus']
        public = reader.read_public_research_corpus(c['id'], expected_corpus_sha256=c['corpus_sha256'],
            expected_done_sha256=c['done_sha256'], limits=reader.CorpusReadLimits(33554432,67108864,262144,48,210,12600,min(20.,guard.left())))
        guard.left()
        need(public.plan.identity == c['plan_sha256'], 'public plan binding')
        prepared = ec.prepare_train_lagged_rows(public.role_data('train'), public.bank, public.plan,
            expected_train_provenance_sha256=c['train_provenance_sha256'], expected_train_observable_sha256=c['train_observable_sha256'],
            recipe=recipe, limits=ec.EdgePreparationLimits(48,210,10080,min(20.,guard.left())))
        need(len(prepared.learner_ids) == 48 and len(prepared.rows) == 10080 and len(prepared.concepts) == 28, 'actual TRAIN geometry')
        del public  # No selection/calibration data passed to optimizer or retained for ranking.
        origins_before = runtime_origins(profile, guard, import_required=True)
        guard.left()
        threadpool = sys.modules['threadpoolctl']
        with threadpool.threadpool_limits(limits=1):
            pools = threadpool.threadpool_info()
            need(type(pools) is list and 0 < len(pools) <= 16 and all(type(p.get('num_threads')) is int and p['num_threads'] == 1 for p in pools),
                 'single-thread pool proof required')
            remaining = guard.left()-config['caps']['export_reserve_seconds']
            need(remaining > 0, 'export reserve leaves no fit allowance')
            result = ec.fit_crossfit_edge_confidence(prepared, expected_prepared_sha256=prepared.identity,
                runtime=ec.EdgeRuntimeBinding(profile['packages']['sklearn']['version'],profile['packages']['numpy']['version'],
                    profile['lock_sha256'],profile['method_source_sha256']),
                limits=ec.EdgeFitLimits(2352,272160,min(110.,remaining)))
            guard.left()
        graph = ec.select_positive_dag(result, edge_budget=31)
        guard.left()
        export_result(writer, result, graph, prepared, config)
        origins_after = runtime_origins(profile, guard, import_required=False)  # Captures legitimate optional pandas too.
        writer.json('runtime.json', dict(origins_before=origins_before, origins_after=origins_after, threadpools=pools,
            environment_threads={key:os.environ[key] for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')},
            profile_sha256=request['runtime_profile_sha256'], sys_executable=sys.executable, prefix=sys.prefix,
            scope='Selected package origin/version and metadata hashes, not full-site byte attestation'))
        sources_after = {name:hash_file(name,cap=262144,check=guard.left) for name in SOURCES}
        runtime_after = {name:hash_file(name,check=guard.left) for name in runtime_files}
        prefix = 'artifacts/simulator/corpora/'+c['id']+'/'
        public_after = {name:hash_file(prefix+name,check=guard.left) for name in PUBLIC}
        need(sources_after == request['source_sha256'] and runtime_after == runtime_files and public_after == request['public_sha256'], 'source/runtime/public drift')
        need(hash_file(CONFIG) == request['config_sha256'] and hash_file(PROFILE) == request['runtime_profile_sha256'] and
             hash_file(REQUEST) == args.request_sha256 and not safe(prefix+'failure.json').exists(), 'request/config/corpus failure override')
        need(set(access['public_opens']) == set(PUBLIC) and not access['forbidden_imports'] and not access['subprocess_attempts'], 'access scope mismatch')
        writer.json('input-source-inventory.json', dict(sources_before=request['source_sha256'],sources_after=sources_after,
            runtime_before=runtime_files,runtime_after=runtime_after,public_before=request['public_sha256'],public_after=public_after,
            train_only_optimization=True, public_schema_audit_roles=['train','selection','calibration'], oracle_files_opened=False))
        monitor.stop()
        guard.left()
        writer.json('resources.json', guard.summary())
        writer.json('worker_result.json', dict(status='COMPLETE_CONDITIONAL_SURROGATE_PENDING_OUTER_ACCEPTANCE',
            owner=owner,request_sha256=args.request_sha256,config_sha256=request['config_sha256'],
            result_sha256=result.identity,prepared_sha256=prepared.identity,processed_fit_slots=len(result.fit_records),
            actual_solver_calls=sum(r.solver_called for r in result.fit_records),oof_rows=len(result.oof_rows),
            edge_summaries=len(result.edges),supported_edges=sum(e.supported for e in result.edges),graph_status=graph.status,
            graph_edges=len(graph.edges),teacher_calls=0,neural_optimizer_steps=0,modal_spend_usd=0,
            resources=guard.summary(),outer_acceptance_required=True,data_sha256={k:v for k,v in writer.files.items() if k in DATA_FILES}))
        writer.json('DONE.json', dict(schema_version=1,status='COMPLETE_METHOD24_PENDING_OUTER_ACCEPTANCE',
            request_sha256=args.request_sha256,files_sha256={k:v['sha256'] for k,v in writer.files.items()}))
        guard.left()
        return 0
    except Exception as error:
        try:
            monitor.stop()
        except Exception:
            pass
        with (output/'failure.log').open('x',encoding='utf-8') as handle:
            traceback.print_exc(file=handle)
        failure = dict(status='REJECTED_KEEP_PARTIAL_NO_RETRY',type=type(error).__name__,reason=str(error),
            reserved_solver_calls=2352,actual_solver_calls=None if result is None else sum(r.solver_called for r in result.fit_records),
            partial_fit_slots=None if not hasattr(error,'fit_records') else len(error.fit_records),resources=guard.summary())
        with (output/'failure.json').open('xb') as handle:
            handle.write(encode(failure));handle.flush();os.fsync(handle.fileno())
        return 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True)
    parser.add_argument('--request-sha256',required=True)
    parser.add_argument('--active-deadline-perf',required=True,type=float)
    parser.add_argument('--active-deadline-wall',required=True,type=float)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner = worker_gate()
    return run(args, owner)


if __name__ == '__main__':
    raise SystemExit(main())
