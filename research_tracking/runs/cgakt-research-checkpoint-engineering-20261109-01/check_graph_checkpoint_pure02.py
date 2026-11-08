"""ROOT-only: cold import +35metadata cases; không Torch/NumPy/model/checkpoint load."""
import time
START, WALL = time.perf_counter(), time.time()
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import threading
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
PACKET = P/'graph_checkpoint_pure02_allocation.json'
OUT = P/'graph-checkpoint-pure02'
TMP = R/'artifacts/akt/local-tests/gcp02'
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import worker_gate


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def write(name, value):
    with open(OUT/name, 'x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


timer = threading.Timer(53, lambda: os._exit(124)); timer.daemon = True; timer.start()
owner = worker_gate()  # Actual Job membership/GO trước framework/domain imports.
need(len(sys.argv) == 2, 'exact reviewed packet SHA argument required')
raw = PACKET.read_bytes()
need(len(raw) <= 65536 and hashlib.sha256(raw).hexdigest() == sys.argv[1], 'reviewed packet byte SHA')
packet = json.loads(raw)
pins, runtime_pins = packet['source_pins'], packet['runtime_pins']
need(all(sha(R/n) == h for n,h in pins.items()) and all(sha(Path(n)) == h for n,h in runtime_pins.items()), 'pre-source/runtime drift')
need(not OUT.exists() and not TMP.exists(), 'exclusive child output/basetemp; no retry/overwrite')
OUT.mkdir(); os.chdir(R)
write('reservation.json', dict(kind=packet['kind'], expected_cases=35, source_before=pins,
    runtime_before=runtime_pins, allocation_sha256=sys.argv[1], owner=owner,
    framework_tensor_model_optimizer_forward_save_load_caps=packet['call_caps'],
    scope_vi='Metadata-only manufactured raw bytes in owned tmp, không .pt deserialization hoặc native/model/corpus.'))
envkeys = ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
    'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS')
env_before = {k: os.environ.get(k) for k in envkeys}
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
    CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    PYTEST_ADDOPTS='', PYTEST_PLUGINS='')
phase = ['native_windows_metadata']; metadata_calls = []; forbidden = []; system_cmd = None
blocked_imports = {'torch','numpy','pandas','scipy','sklearn','joblib','modal','boto3'}


def audit(event, args):
    if event == 'import' and str(args[0]).split('.')[0] in blocked_imports:
        forbidden.append('import:'+str(args[0])); raise RuntimeError('pure worker framework import forbidden')
    if event == 'subprocess.Popen':
        if phase[0] == 'native_windows_metadata':
            fixed = os.path.normcase(os.path.abspath(str(system_cmd)))
            allowed = {fixed.casefold()+' /c "ver"', '"'+fixed.casefold()+'" /c "ver"'}
            need(system_cmd is not None and len(metadata_calls) < 3 and type(args[0]) is str and type(args[1]) is str
                and os.path.normcase(os.path.abspath(args[0])) == fixed and args[1].strip().casefold() in allowed,
                'only bounded actual Windows version metadata command')
            metadata_calls.append(dict(executable=args[0], command=args[1])); return
        forbidden.append(event); raise RuntimeError('no pure test subprocess')
    if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
        forbidden.append(event); raise RuntimeError('no child/network operation')
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0], (str,bytes,os.PathLike)):
        path = Path(os.path.abspath(os.fsdecode(args[0])))
        for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
            if path == R/relative or path.is_relative_to(R/relative):
                forbidden.append('protected_or_actual_data'); raise RuntimeError('pure scope excludes actual/protected artifacts')
        if event == 'open' and path.suffix in ('.pt','.pth','.ckpt','.safetensors') and not path.is_relative_to(TMP):
            forbidden.append('external_checkpoint_bytes'); raise RuntimeError('only manufactured raw .pt bytes inside owned tmp')


sys.addaudithook(audit)
stop = threading.Event(); monitor = None; monitor_errors = []
resources = dict(samples=0, observed_peak_rss_bytes=0, observed_minimum_available_ram_bytes=None)
memory_lock = threading.Lock()
metadata = canary = None; rc = counts = None; original_error = junit_error = None
source_after = runtime_after = {}; alias = None
try:
    need(not blocked_imports.intersection(sys.modules), 'cold framework-free worker required')
    need(sys.platform == 'win32' and type(os.environ.get('SystemRoot')) is str, 'native Windows metadata expected')
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_absolute() and system_cmd.is_file() and not system_cmd.is_symlink()
        and not getattr(system_cmd, 'is_junction', lambda: False)(), 'native system cmd')
    try:
        actual = platform.uname()
        metadata = dict(system=actual.system, release=actual.release, version=actual.version, machine=actual.machine,
            public_api='platform.uname', fixture_replaced=False, commands=metadata_calls, inside_owned_job=True)
        need(actual.system == 'Windows', 'Windows metadata result')
    finally:
        phase[0] = 'tests_no_subprocess'
    import psutil
    need(Path(psutil.__file__).resolve() == Path(packet['runtime_origins']['psutil']).resolve(), 'pinned psutil import origin')
    process = psutil.Process()
    def memory():
        with memory_lock:
            info = process.memory_info(); peak = max(int(info.rss), int(info.peak_wset))
            available = int(psutil.virtual_memory().available)
            resources['samples'] += 1; resources['observed_peak_rss_bytes'] = max(resources['observed_peak_rss_bytes'], peak)
            previous = resources['observed_minimum_available_ram_bytes']
            resources['observed_minimum_available_ram_bytes'] = available if previous is None else min(previous, available)
            need(peak <= 1024**3 and available >= 2*1024**3, 'observed pure worker RAM bounds')
    memory()
    def watch():
        while not stop.wait(.1):
            try: memory()
            except BaseException as error:
                monitor_errors.append(type(error).__name__+': '+str(error))
                try: write('resource-failure.json', dict(resources=resources, error=monitor_errors[-1]))
                finally: os._exit(125)
    monitor = threading.Thread(target=watch, daemon=True); monitor.start()
    sys.path.insert(0, str(R/'src'))
    module = importlib.import_module('knowledge_tracing.akt.research_graph_checkpoint')
    need(Path(module.__file__).resolve() == R/'src/knowledge_tracing/akt/research_graph_checkpoint.py', 'pinned checkpoint module origin')
    alias = module.GraphCheckpointLimits
    need(not blocked_imports.intersection(sys.modules), 'cold checkpoint import unexpectedly loaded framework')
    canary = dict(module=module.__name__, source_sha256=sha(Path(module.__file__)),
        numpy_loaded=False, torch_loaded=False, fresh_import_accepted=True)
    write('cold_import.json', canary)
    import pytest
    need(Path(pytest.__file__).resolve() == Path(packet['runtime_origins']['pytest']).resolve(), 'pinned pytest import origin')
    command = ['tests/akt/test_research_graph_checkpoint.py', '-q', '-k', 'not native', '--noconftest',
        '-p', 'no:cacheprovider', '--basetemp', str(TMP), '--junitxml', str(OUT/'junit.xml')]
    class Journal:
        def pytest_runtest_logreport(self, report):
            with open(OUT/'case_events.jsonl', 'a', encoding='utf-8') as stream:
                stream.write(json.dumps(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome,
                    elapsed_seconds=elapsed()), ensure_ascii=False)+'\n'); stream.flush(); os.fsync(stream.fileno())
    with open(OUT/'pytest.log', 'x', encoding='utf-8') as log:
        with redirect_stdout(log), redirect_stderr(log): rc = int(pytest.main(command, plugins=[Journal()]))
    need(module.GraphCheckpointLimits is alias, 'cached class identity drift')
    need(not blocked_imports.intersection(sys.modules), 'framework imported during pure metadata fixtures')
    memory()
except BaseException as error:
    original_error = dict(type=type(error).__name__, message=str(error))
finally:
    stop.set()
    if monitor is not None: monitor.join(timeout=min(1., max(.001, 53.-elapsed())))
    monitor_stopped = monitor is None or not monitor.is_alive()
    try:
        tree = ET.parse(OUT/'junit.xml').getroot()
        counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        need(len(list(tree.iter('testcase'))) == counts['tests'], 'JUnit exact testcase count')
    except BaseException as error: junit_error = dict(type=type(error).__name__, message=str(error))
    try:
        source_after = {n:sha(R/n) for n in pins}; runtime_after = {n:sha(Path(n)) for n in runtime_pins}
        need(source_after == pins and runtime_after == runtime_pins and sha(PACKET) == sys.argv[1], 'post source/runtime/packet drift')
        need(all(p.stat().st_size <= 1024**2 for p in OUT.iterdir() if p.is_file()), 'small pure output file cap')
    except BaseException as error:
        if original_error is None: original_error = dict(type=type(error).__name__, message=str(error))
    for key, value in env_before.items():
        if value is None: os.environ.pop(key, None)
        else: os.environ[key] = value
    accepted = original_error is None and junit_error is None and not forbidden and not monitor_errors and monitor_stopped
    accepted = accepted and rc == 0 and counts == dict(tests=35,failures=0,errors=0,skipped=0) and elapsed() < 53
    result = dict(status='ACCEPTED_35_METADATA_CASES_PENDING_OUTER' if accepted else 'REJECTED_KEEP_ALL',
        counts=counts, pytest_exit_code=rc, original_error=original_error, junit_error=junit_error,
        source_before=pins, source_after=source_after, runtime_before=runtime_pins, runtime_after=runtime_after,
        allocation_sha256=sys.argv[1], cold_import=canary, held_class_identity_stable=alias is not None and module.GraphCheckpointLimits is alias,
        native_windows_metadata=metadata, metadata_phase_closed=phase[0] == 'tests_no_subprocess',
        forbidden_attempts=forbidden, resources=resources, monitor_errors=monitor_errors, monitor_stopped=monitor_stopped,
        environment_restored=all(os.environ.get(k) == v for k,v in env_before.items()),
        verified_no_framework_imports=not blocked_imports.intersection(sys.modules),
        declared_call_caps=packet['call_caps'], elapsed_seconds=elapsed(), worker_cap_seconds=53,
        scope_vi='35pure metadata fixtures+fresh import. Không constructTensor/model/Adam/forward/backward/Torchsave/load; raw .pt bytes fixture only; no native research/Gate claim.')
    write('result.json', result)
    if elapsed() >= 53:
        write('postwrite_rejection.json', dict(status='REJECTED_CHILD_POSTWRITE_TIME', elapsed_seconds=elapsed())); accepted = False
    timer.cancel()
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_ALL', counts=counts, elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
