"""Một integration read-only thật, chờ ROOT duyệt; không solver/NN/oracle."""
from pathlib import Path
from dataclasses import asdict
import hashlib, importlib.util, json, os, sys, threading, time

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
START, WALL = time.perf_counter(), time.time()
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import worker_gate, safe
owner = worker_gate()
assert len(sys.argv) == 2
packet_sha = sys.argv[1]
packet_path = P/'edge_artifact_native02_expectation.json'
raw = packet_path.read_bytes()
assert len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == packet_sha
a = json.loads(raw)
out = safe(P/'edge-artifact-native02')
out.mkdir(exist_ok=False)

def write(name, value):
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n').encode()
    assert len(payload) <= 131072
    with open(out/name, 'xb') as handle:
        handle.write(payload); handle.flush(); os.fsync(handle.fileno())

def sha(path):
    assert path.stat().st_size <= 262144
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sources():
    return {name: sha(safe(R/name)) for name in a['source_pins']}

timer = threading.Timer(23.5, lambda: os._exit(124)); timer.daemon = True; timer.start()
stop = threading.Event(); thread = None; guard = None
error = None; result = None; before = None; after = None; metadata = None
forbidden = []; monitor_errors = []
try:
    before = sources(); assert before == a['source_pins']; write('source_before.json', before)
    assert a['caps'] == dict(whole_seconds=30, owned_seconds=27, cleanup_seconds=3,
        worker_seconds=23, reader_seconds=20, max_rss_bytes=536870912, min_available_ram_bytes=1073741824)
    sys.path.insert(0, str(R/'src'))
    spec = importlib.util.spec_from_file_location('reviewed_metadata_resource_only', P/'method24_worker01.py')
    w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
    guard = w.Guard(w._memory_api(), dict(max_rss_bytes=536870912, min_available_ram_bytes=1073741824),
                    START+23, WALL+23)
    guard.left()
    # Cùng bootstrap Windows thật đã review; không fake OS, nằm trong owned Job.
    metadata = w.native_windows_metadata(guard)
    corpus_root = R/'artifacts/simulator/corpora'
    bank_path = safe(R/a['bank']['path'])
    bundle_path = safe(R/a['accepted_bundle']['path'])
    def audit(event, args):
        if event == 'subprocess.Popen' or event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
            forbidden.append(event); raise RuntimeError('read-only integration prohibits process/network')
        if event == 'import' and str(args[0]).split('.')[0] in ('torch', 'sklearn', 'scipy', 'pandas', 'joblib', 'modal', 'boto3'):
            forbidden.append('import:'+str(args[0])); raise RuntimeError('model/solver import prohibited')
        if event in ('open', 'os.listdir', 'os.scandir') and args and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.path.abspath(os.fsdecode(args[0])))
            prohibited = any(path.is_relative_to(R/n) for n in ('dataset', 'artifacts/bkt_baseline', 'experiments', 'venv', '.wsl'))
            prohibited |= path.is_relative_to(corpus_root) and not (event == 'open' and path == bank_path)
            prohibited |= 'oracle' in tuple(x.lower() for x in path.parts)
            prohibited |= path.is_relative_to(R/'research_tracking/runs') and not (event == 'open' and path == bundle_path)
            if event == 'open':
                flags = args[2] if len(args) > 2 and type(args[2]) is int else 0
                writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                prohibited |= writing and not path.is_relative_to(out)
            if prohibited:
                forbidden.append('protected_data'); raise RuntimeError('non-bank corpus/protected evidence access prohibited')
    sys.addaudithook(audit)
    def watch():
        while not stop.wait(.05):
            try: guard.left()
            except BaseException as exc:
                monitor_errors.append(type(exc).__name__+': '+str(exc))
                write('resource-failure.json', dict(error=monitor_errors[-1])); os._exit(125)
    thread = threading.Thread(target=watch, daemon=True); thread.start()
    from knowledge_tracing.edge_confidence_artifact import (Method24ArtifactRef, Method24TrainingBinding,
        Method24ReadLimits, load_method24_scores)
    from knowledge_tracing.simulator_bridge import SimulatorBank, SimulatorItem, identity_hash
    from knowledge_tracing.shared_kt import PrerequisiteGraph
    assert sha(bundle_path) == a['accepted_bundle']['sha256']
    bundle = json.loads(bundle_path.read_bytes())
    assert len(bundle['outputs_sha256']) == 113
    assert bundle['native']['run_sha256'] == a['artifact']['outer_run_sha256']
    assert bundle['native']['request_sha256'] == a['artifact']['request_sha256']
    assert bundle['native']['source11_sha256'] == a['expected_training']['source_files_sha256']
    bank_raw = bank_path.read_bytes()
    assert len(bank_raw) <= 32768 and hashlib.sha256(bank_raw).hexdigest() == a['bank']['sha256']
    bank_json = json.loads(bank_raw)
    assert set(bank_json) == {'schema_version', 'environment_id', 'items'} and bank_json['schema_version'] == 1
    bank = SimulatorBank(bank_json['environment_id'], tuple(SimulatorItem(**v) for v in bank_json['items']))
    assert len(bank.items) == 84 and bank.identity == a['bank']['identity']
    assert identity_hash(bank.identity) == a['expected_training']['domain_sha256']
    training = dict(a['expected_training'])
    for name in ('public_files_sha256', 'source_files_sha256', 'runtime_files_sha256'):
        training[name] = tuple(sorted(training[name].items()))
    expected = Method24TrainingBinding(**training)
    graph = PrerequisiteGraph.from_edges(a['declared_graph']['nodes'], a['declared_graph']['edges'])
    assert len(graph.nodes) == 28 and len(graph.edges) == 31
    guard.left()
    loaded = load_method24_scores(Method24ArtifactRef(**a['artifact']), expected_training=expected, bank=bank,
        declared_graph=graph, graph_binding='method24_learned', limits=Method24ReadLimits(**a['read_limits']))
    guard.left()
    assert len(loaded.edge_scores) == 31 and all(x.supported and x.score is not None for x in loaded.edge_scores)
    assert loaded.training == expected and loaded.actual_solver_calls == loaded.processed_fit_slots == 2352
    # Không chạy lại greedy selection: fidelity delegated tới producer/source đã pin.
    write('summary.json', dict(status='ACTUAL_ARTIFACT_READ_ONLY_LOADED_NOT_MODEL_TRAINED', identity=loaded.identity,
        scores=[asdict(x) for x in loaded.edge_scores], graph_binding=loaded.graph_binding,
        semantics=loaded.score_semantics, fit_scope=loaded.fit_scope, oracle_inputs_used=loaded.oracle_inputs_used,
        declared_nodes=loaded.declared_nodes, declared_edges=loaded.declared_edges,
        lineage=asdict(expected), verified_artifacts_sha256=loaded.artifacts_sha256,
        prepared_sha256=loaded.prepared_sha256, producer_result_sha256=loaded.producer_result_sha256,
        exported_graph_sha256=loaded.exported_graph_sha256, bank_raw_sha256=a['bank']['sha256'],
        original_solver_calls=loaded.actual_solver_calls, new_solver_calls=0, model_calls=0,
        greedy_fidelity='DELEGATED_TO_PINNED_REVIEWED_PRODUCER_NOT_INDEPENDENT_RECOMPUTATION'))
    after = sources(); assert after == before == a['source_pins']; write('source_after.json', after)
    assert sha(bank_path) == a['bank']['sha256'] and sha(bundle_path) == a['accepted_bundle']['sha256']
    guard.left()
except BaseException as exc:
    error = dict(type=type(exc).__name__, message=str(exc))
finally:
    stop.set()
    if thread is not None: thread.join(timeout=.5)
    try:
        if guard is not None: guard.left()
    except BaseException as exc:
        error = error or dict(type=type(exc).__name__, message=str(exc))
    elapsed = max(time.perf_counter()-START, time.time()-WALL)
    unexpected = [n for n in ('torch', 'sklearn', 'scipy', 'pandas', 'joblib', 'modal') if n in sys.modules]
    ok = error is None and after == before == a['source_pins'] and not forbidden and not unexpected and not monitor_errors
    ok = ok and thread is not None and not thread.is_alive() and metadata is not None and metadata['phase_closed']
    ok = ok and metadata['outside_phase_popen_attempts'] == 0 and elapsed < 23
    result = dict(status='READ_ONLY_COMPLETE_PENDING_OUTER' if ok else 'REJECTED_READ_ONLY', error=error,
        expectation_sha256=packet_sha, source_before=before, source_after=after, source_unchanged=before == after,
        forbidden_attempts=forbidden, unexpected_heavy_modules=unexpected, native_os_metadata=metadata,
        resources=None if guard is None else guard.summary(), monitor_errors=monitor_errors,
        monitor_stopped=thread is not None and not thread.is_alive(), elapsed_seconds=elapsed,
        score_count=31 if ok else None, model_calls=0, new_solver_calls=0, owner=owner,
        scope_vi='Một loader call trên artifact thật; chỉ bank public, không learner/labels/oracle; không chứng minh hiệu quả CG-AKT.')
    write('result.json', result)
    files = {n: sha(out/n) for n in ('source_before.json', 'source_after.json', 'summary.json', 'result.json') if (out/n).exists()}
    write('output-manifest.json', dict(schema_version=1, files_sha256=files, expectation_sha256=packet_sha))
    # Sau publication vẫn fail-closed; outer đo lại toàn bộ elapsed và cleanup.
    if max(time.perf_counter()-START, time.time()-WALL) >= 23:
        write('postbudget_failure.json', dict(status='REJECTED_POSTPUBLICATION_TIME')); ok = False
    timer.cancel()
print(json.dumps(dict(status=result['status'], error=error, score_count=result['score_count'])))
raise SystemExit(0 if ok else 1)
