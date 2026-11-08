"""SOURCE-ONLY proposal: public provenance audit, complete TRAIN80 hash cost; no NN."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
from dataclasses import asdict
import csv
import gc
import hashlib
import json
import os
import platform
import sys
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = PREP/'graph_context_hash_benchmark02_config.json'
OUT = PREP/'graph-context-hash-benchmark02'
PACKET_SHA = sys.argv[1] if len(sys.argv) == 2 else None
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate, safe


def need(ok, message):
    if not ok:
        raise ValueError(message)


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def sha(path):
    safe(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(65536):
            digest.update(block)
    return digest.hexdigest()


owner = worker_gate()
need(PACKET.stat().st_size <= 131072 and sha(PACKET) == PACKET_SHA, 'exact reviewed config bytes')
packet = json.loads(PACKET.read_bytes())
need(packet['scope'] == 'SIMULATOR_DEVELOPMENT_AUDIT_TRAIN80_HASH_COST_NO_NEURAL', 'fixed operational scope')
need(packet['passes'] == ['full', 'fast', 'fast', 'full'], 'fixed ABBA workload')
pins = packet['source_pins']
need(all(sha(ROOT/name) == digest for name, digest in pins.items()), 'prospective source pin drift')
need(not OUT.exists(), 'exclusive attempt only; no retry/overwrite')
OUT.mkdir()


def write(name, value):
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
    need(len(raw) <= packet['limits']['max_output_file_bytes'], 'small output cap')
    with (OUT/name).open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


journal = (OUT/'events.jsonl').open('xb')


def event(phase, **values):
    raw = (json.dumps(dict(phase=phase, seconds=elapsed(), **values), sort_keys=True, allow_nan=False)+'\n').encode()
    need(journal.tell()+len(raw) <= packet['limits']['max_journal_bytes'], 'bounded journal')
    journal.write(raw); journal.flush(); os.fsync(journal.fileno())


write('reservation.json', dict(kind=packet['scope'], config_sha256=PACKET_SHA,
    corpus_reads='all3 Development roles for canonical provenance audit; no final/oracle',
    context_work='complete TRAIN80 only; no selectedfit/evaluation/tuning',
    counts=packet['counts'], passes=packet['passes'], model_calls=0,
    active_call_counts='UNKNOWN_IF_NO_TERMINAL_RESULT; journal reservation is not body return', source_before=pins))
env = dict(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
           CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTHONDONTWRITEBYTECODE='1')
os.environ.update(env)
need(elapsed() < packet['limits']['worker_seconds'], 'original worker deadline before timer')
timer = threading.Timer(packet['limits']['worker_seconds']-elapsed(), lambda: os._exit(124))
timer.daemon = True; timer.start()
forbidden = []
phase = ['actual_os_metadata']
system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
metadata_calls = []
input_root = ROOT/'artifacts/simulator/corpora'/packet['corpus_id']
allowed_public = set(packet['public_inputs_sha256'])


def audit(action, args):
    if action == 'import' and str(args[0]).split('.')[0] in {'torch', 'tensorflow', 'jax', 'sklearn', 'scipy', 'pandas', 'joblib'}:
        forbidden.append('forbidden_import'); raise RuntimeError('no neural/solver import')
    if action == 'import' and str(args[0]) in {'knowledge_tracing.paper2_reference',
            'knowledge_tracing.simulator_collection', 'knowledge_tracing.simulator_research_collection'}:
        forbidden.append('teacher_collector_import'); raise RuntimeError('no teacher/collector execution')
    if action == 'subprocess.Popen':
        fixed = os.path.normcase(os.path.abspath(str(system_cmd)))
        allowed = {fixed.casefold()+' /c "ver"', '"'+fixed.casefold()+'" /c "ver"'}
        if not (phase[0] == 'actual_os_metadata' and len(metadata_calls) < 3
                and type(args[0]) is str and type(args[1]) is str
                and os.path.normcase(os.path.abspath(args[0])) == fixed
                and args[1].strip().casefold() in allowed):
            forbidden.append('undeclared_child'); raise RuntimeError('only bounded literal cmd ver during metadata')
        metadata_calls.append(dict(executable=args[0], command=args[1]))
    if (action.startswith('socket.') and action != 'socket.gethostname') or action in ('os.system', 'os.posix_spawn') or action.startswith('os.spawn'):
        forbidden.append('network_or_shell'); raise RuntimeError('no network/shell')
    if action == 'open' and args and isinstance(args[0], (str, bytes)):
        name = os.fsdecode(args[0]).replace('\\', '/').lower()
        if any(token in name for token in ('/dataset/', '/oracle/', '/holdout/', '/realdata/')):
            forbidden.append('protected_read'); raise RuntimeError('protected input rejected')
        if '/artifacts/simulator/corpora/' in name:
            path = Path(os.fsdecode(args[0])).absolute()
            if path.parent != input_root or path.name not in allowed_public:
                forbidden.append('nonpublic_corpus_read'); raise RuntimeError('only exact published public files')


sys.addaudithook(audit)
error = None; calls = []; stages = []; source_after = None; input_after = None
counts = dict(full_payload=0, selected_record_hash=0, window_input_hash=0, source_inventory=0)
resources = dict(samples=0, observed_peak_rss_bytes=0, observed_minimum_available_ram_bytes=None)
monitor_stop = threading.Event(); resource_failure = []; originals = None
resource_lock = threading.Lock()
completed_calls = 0; expected_evidence = {}; index = seal = None
reader_complete = False

try:
    # Real OS APIs in the owned Job; not a fabricated platform fallback.
    uname = platform.uname(); processor = platform.processor()
    import psutil
    runtime = dict(uname=uname._asdict(), processor=processor, executable=sys.executable, prefix=sys.prefix,
        python=sys.version, environment=env, package_origins={}, actual_metadata_commands=metadata_calls)
    need(Path(sys.prefix).resolve() == ROOT/'.venv' and Path(sys.executable) == ROOT/'.venv/Scripts/python.exe', 'repository venv runtime')
    need(list(sys.version_info[:3]) == packet['python_version'], 'reviewed Python ABI/version')
    phase[0] = 'data_benchmark_no_children'

    def sample():
        with resource_lock:
            info = psutil.Process().memory_info(); available = int(psutil.virtual_memory().available)
            peak = max(int(info.rss), int(getattr(info, 'peak_wset', info.rss)))
            resources['samples'] += 1
            resources['observed_peak_rss_bytes'] = max(resources['observed_peak_rss_bytes'], peak)
            old = resources['observed_minimum_available_ram_bytes']
            resources['observed_minimum_available_ram_bytes'] = available if old is None else min(old, available)
            if peak > packet['limits']['max_rss_bytes'] or available < packet['limits']['min_available_ram_bytes']:
                resource_failure.append('memory bound'); raise RuntimeError('observed memory bound')

    def guard():
        need(elapsed() < packet['limits']['worker_seconds'] and not resource_failure, 'worker time/resource bound')
        sample()

    def monitor():
        while not monitor_stop.wait(.025):
            try: sample()
            except BaseException as caught:
                resource_failure.append(type(caught).__name__); return
    sample()
    watcher = threading.Thread(target=monitor, daemon=True); watcher.start()
    sys.path.insert(0, str(ROOT/'src'))
    from knowledge_tracing.simulator_corpus_reader import CorpusReadLimits, read_public_research_corpus
    from knowledge_tracing.akt import research_simulator_data as data
    from knowledge_tracing.akt import research_graph_context as context
    from knowledge_tracing.akt import research_graph_condition as condition
    from knowledge_tracing.akt.types import WindowInputs
    from knowledge_tracing.simulator_bridge import identity_hash
    import numpy as np
    for name, module in (('numpy', np), ('psutil', psutil)):
        expected = packet['packages'][name]
        need(module.__version__ == expected['version'] and Path(module.__file__).resolve() == (ROOT/expected['module_path']).resolve(), 'exact package version/origin')
        runtime['package_origins'][name] = dict(version=module.__version__, file=module.__file__, sha256=sha(Path(module.__file__)))
    need(not any(n in sys.modules for n in ('torch', 'pandas', 'sklearn')), 'no model/solver loaded')
    write('runtime.json', runtime)
    phase[0] = 'canonical_all3_development_roles_provenance_read'
    guard(); event('public_reader_start')
    started = time.perf_counter()
    corpus = read_public_research_corpus(packet['corpus_id'], expected_corpus_sha256=packet['public_inputs_sha256']['corpus.json'],
        expected_done_sha256=packet['public_inputs_sha256']['DONE.json'], limits=CorpusReadLimits(**packet['reader_limits']))
    stages.append(dict(stage='canonical_all3_role_provenance_read', seconds=time.perf_counter()-started))
    reader_complete = True
    metadata = {role: corpus.role_data(role).audit['audit'] for role in ('train', 'selection', 'calibration')}
    need(metadata['train']['learners'] == 48 and metadata['train']['targets'] == 10080, 'complete TRAIN80 population')
    event('public_reader_returned', roles_read=['train', 'selection', 'calibration'], train_targets=10080)
    role = corpus.role_data('train'); bank, plan = corpus.bank, corpus.plan
    binding = condition.GraphTrain80Binding(packet['corpus_id'], packet['public_inputs_sha256']['corpus.json'],
        packet['public_inputs_sha256']['DONE.json'], plan.identity, role.provenance.identity,
        packet['public_inputs_sha256']['train.jsonl'], identity_hash(bank.identity),
        metadata['train']['shard_sha256'], metadata['selection']['shard_sha256'], metadata['calibration']['shard_sha256'])
    shard = data.ResearchAKTShard(plan, bank, 'train', role.trajectories, role.provenance,
        role.provenance.identity, corpus.limits.shard_limits)
    with (ROOT/packet['expert_edges_path']).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        need(reader.fieldnames == ['source', 'target'], 'fixed expert graph schema')
        edges = tuple(sorted((row['source'], row['target']) for row in reader))
    setup = condition.prepare_research_graph_condition(variant='A1', graph_mode='expert_declared', bank=bank,
        nodes=tuple(sorted({item.concept_id for item in bank.items})), edges=edges, train80=binding,
        expected_sources=tuple(sorted(packet['condition_sources'].items())), topology_source_sha256=packet['source_pins'][packet['expert_edges_path']])
    del corpus; gc.collect()  # No selection/calibration trajectories retained during benchmark.
    phase[0] = 'complete_train80_context_build'
    guard(); started = time.perf_counter()
    phase_data = data.prepare_research_phase('select_train80', shards=(shard,))
    encoding = data.fit_research_encoding(phase_data)
    index = context.prepare_research_graph_context(phase_data, encoding, setup,
        limits=context.ResearchGraphContextLimits(**packet['context_limits']),
        fit80_encoding_sha256=encoding.identity, context=100, target_block=100)
    stages.append(dict(stage='train80_encoding_and_context_build', seconds=time.perf_counter()-started))
    windows = tuple(data.iter_research_windows(phase_data, encoding, context=100, target_block=100, training=False))
    need(all(type(w) is WindowInputs for w in windows), 'TRAIN80 exact known WindowInputs; no OOV')
    need(len(windows) == packet['counts']['windows'] and index.full_targets == packet['counts']['targets'], 'complete canonical window/target population')
    groups = tuple(windows[i:i+packet['counts']['batch_windows']] for i in range(0, len(windows), packet['counts']['batch_windows']))
    need(len(groups) == packet['counts']['groups'] and sum(int(w.target_mask.sum()) for w in windows) == 10080, 'all canonical TRAIN80 groups')
    phase[0] = 'full_boundary_and_seal'
    guard(); started = time.perf_counter(); seal = index.seal_for_access()
    stages.append(dict(stage='full_attach_and_manifest_seal', seconds=time.perf_counter()-started))
    root_sha = seal.root_sha256
    originals = context.ResearchGraphContextIndex._payload, context.identity_hash, context.source_inventory
    def payload_counted(self):
        counts['full_payload'] += 1; return originals[0](self)
    def hash_counted(value):
        if type(value) is dict and set(value) == {'window_id', 'learner_id', 'inputs_sha256', 'contexts'}:
            counts['selected_record_hash'] += 1
        if type(value) is dict and set(value) == {'window_id', 'user_ids', 'arrays'}:
            counts['window_input_hash'] += 1
        return originals[1](value)
    def source_counted():
        counts['source_inventory'] += 1; return originals[2]()
    context.ResearchGraphContextIndex._payload = payload_counted
    context.identity_hash = hash_counted; context.source_inventory = source_counted
    for pass_number, mode in enumerate(packet['passes']):
        phase[0] = 'ABBA_'+str(pass_number)+'_'+mode
        event('pass_start', pass_number=pass_number, mode=mode)
        for group_number, group in enumerate(groups):
            guard(); before = dict(counts)
            event('call_reserved', pass_number=pass_number, group_number=group_number, mode=mode)
            started = time.perf_counter()
            evidence = index.for_windows(group, access_seal=seal) if mode == 'fast' else index.for_windows(group)
            seconds = time.perf_counter()-started
            delta = {name: counts[name]-before[name] for name in counts}
            completed_calls += 1
            event('call_body_returned', pass_number=pass_number, group_number=group_number, mode=mode, call_seconds=seconds)
            need(delta['full_payload'] == (0 if mode == 'fast' else 1)
                 and delta['selected_record_hash'] == (len(group) if mode == 'fast' else 0)
                 and delta['window_input_hash'] == len(group) and delta['source_inventory'] > 0, 'actual serializer/record/source work count')
            parity_start = time.perf_counter()
            evidence_sha = identity_hash([[None if e is None else asdict(e) for e in row] for row in evidence])
            if pass_number == 0: expected_evidence[group_number] = evidence_sha
            need(evidence_sha == expected_evidence[group_number], 'same selected evidence/output across ABBA')
            calls.append(dict(pass_number=pass_number, mode=mode, group_number=group_number,
                window_ids=[w.window_id for w in group], seconds=seconds, counters=delta, evidence_sha256=evidence_sha,
                parity_check_seconds=time.perf_counter()-parity_start))
            guard()
    phase[0] = 'full_final_boundary_audit'
    guard(); started = time.perf_counter(); index.assert_integrity()
    stages.append(dict(stage='full_final_boundary_audit', seconds=time.perf_counter()-started))
    need(index.content_sha256 == root_sha and completed_calls == packet['counts']['calls'], 'full canonical ABBA complete')
except BaseException as caught:
    error = dict(type=type(caught).__name__, message=str(caught), phase=phase[0])
finally:
    if originals is not None:
        context.ResearchGraphContextIndex._payload, context.identity_hash, context.source_inventory = originals
    monitor_stop.set()
    if 'watcher' in globals(): watcher.join(timeout=1)
    journal.flush(); journal.close()

try:
    source_after = {name: sha(ROOT/name) for name in pins}
    input_after = {name: sha(input_root/name) for name in packet['public_inputs_sha256']}
    need(source_after == pins and input_after == packet['public_inputs_sha256'] and sha(PACKET) == PACKET_SHA, 'source/public inputs/config prepost stability')
    need(not forbidden and not resource_failure and ('watcher' not in globals() or not watcher.is_alive()), 'scope/monitor guards')
    need(elapsed() < packet['limits']['worker_seconds'], 'worker finalization budget')
except BaseException as caught:
    if error is None: error = dict(type=type(caught).__name__, message=str(caught), phase='final_guards')
write('bench_calls.json', calls); write('resources.json', resources)
result = dict(status='ACCEPTED_TRAIN80_HASH_BENCHMARK_PENDING_OUTER' if error is None else 'REJECTED_KEEP_PARTIAL',
    error=error, config_sha256=PACKET_SHA, source_before=pins, source_after=source_after,
    public_input_sha256_after=input_after, all3_development_roles_audited=reader_complete,
    benchmark_scope='TRAIN80 only; no labelsfit/metrics/modelselection/calibration; no teacher/oracle/Holdout',
    completed_calls=completed_calls, expected_calls=packet['counts']['calls'], counters=counts, stages=stages,
    index_root_sha256=None if seal is None else seal.root_sha256,
    full_targets=None if index is None else index.full_targets, windows=None if index is None else len(index.windows),
    resources=resources, forbidden=forbidden, resource_errors=resource_failure, monitor_stopped=not ('watcher' in globals() and watcher.is_alive()),
    instrumentation_restored=True, no_torch_loaded='torch' not in sys.modules, new_independent_N=0,
    seconds=elapsed(), worker_cap_seconds=packet['limits']['worker_seconds'])
write('result.json', result)
accepted = error is None
try:
    if 'sample' in globals(): sample()
    need(elapsed() < packet['limits']['worker_seconds'] and not resource_failure, 'postpublication time/RAM verdict')
except BaseException as late:
    write('postwrite_rejection.json', dict(status='REJECTED_WORKER_POSTWRITE_BUDGET_OR_RESOURCE',
        seconds=elapsed(), error_type=type(late).__name__, error=str(late)))
    accepted = False
timer.cancel()
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_PARTIAL', completed_calls=completed_calls, seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
