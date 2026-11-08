"""Đề xuất ROOT-only:33checkpoint fixtures, worker83/owned87/outer90; chưa chạy."""
import time
START = time.perf_counter()
WALL = time.time()
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import functools
import hashlib
import json
import os
import platform
import sys
import threading
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
PACKET = P/'sakt_research_checkpoint02_allocation.json'
need_argv = len(sys.argv) == 2
PACKET_SHA = sys.argv[1] if need_argv else None
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import worker_gate


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


timer = threading.Timer(83, lambda: os._exit(124))
timer.daemon = True
timer.start()
owner = worker_gate()  # No native/domain import before actual worker GO.
out = P/'sakt-research-checkpoint02'
out.mkdir(exist_ok=False)
os.chdir(R)
raw = PACKET.read_bytes()
need(need_argv and len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == PACKET_SHA, 'reviewed allocation bytes')
allocation = json.loads(raw)
pins = allocation['source_pins']
need(len(pins) == allocation['source_count'] and all(sha(R/name) == digest for name, digest in pins.items()), 'reviewed source pins')
need(all(not (R/name).exists() for name in allocation['absent_source_paths']), 'namespace source absence changed')
def gate_sources():
    reference = allocation['frozen_gate_reference']
    need(sha(R/reference['path']) == reference['sha256'], 'frozen154 reference bytes')
    need(json.loads((R/reference['path']).read_bytes())['gate_build_hashes'] == reference['gate_build_hashes'], 'frozen154 reference mapping')
    values = {name: sha(R/name) for name in reference['gate_build_hashes']}
    need(len(values) == 154 and values == reference['gate_build_hashes'], 'existing frozen154 source drift')
    return values
gate_before = gate_sources()
base_temp = R/'artifacts/akt/local-tests/skrc02'
need(not base_temp.exists(), 'exclusive pytest basetemp already exists')


def write(name, value):
    with (out/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


write('reservation.json', dict(kind='SAKT_RESEARCH_CHECKPOINT_SYNTHETIC_PERSISTENCE_CHECK_ONLY', expected_cases=33,
    counter_caps=allocation['counter_caps'], expected_core_counts=allocation['expected_core_counts'], actual_native_counts=None,
    allocation_sha256=PACKET_SHA, source_before=pins,
    note_vi='Hardmax3logical Adam bodies; actual constructors/forward/backward/save/load/restore đều đếm, không giả0. Handmetadata only, không research-fit.'))
envkeys = ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
           'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS')
env_before = {key: os.environ.get(key) for key in envkeys}
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
    CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    PYTEST_ADDOPTS='', PYTEST_PLUGINS='')
phase = ['windows_metadata']
metadata_calls, forbidden = [], []
system_cmd = None


def audit(event, args):
    if event == 'subprocess.Popen':
        if phase[0] == 'windows_metadata':
            try:
                need(type(args[0]) is str and type(args[1]) is str and system_cmd is not None,
                     'metadata executable/command strings required')
                need(len(metadata_calls) < 3, 'metadata command count cap before launch')
                fixed = os.path.normcase(os.path.abspath(str(system_cmd)))
                allowed = {fixed.casefold()+' /c "ver"', '"'+fixed.casefold()+'" /c "ver"'}
                need(os.path.normcase(os.path.abspath(args[0])) == fixed
                     and args[1].strip().casefold() in allowed, 'exact system cmd plus literal ver only')
            except BaseException:
                forbidden.append('blocked_windows_metadata_command')
                raise
            metadata_calls.append(dict(executable=args[0], command=args[1]))
            return
        forbidden.append(event); raise RuntimeError('no test subprocess')
    if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
        forbidden.append(event); raise RuntimeError('no process/network operation')
    if event == 'import':
        name = str(args[0])
        if (name.split('.')[0] in ('sklearn','modal','boto3') or name in (
                'knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection',
                'knowledge_tracing.akt.model','knowledge_tracing.akt.training')):
            forbidden.append('import:'+name); raise RuntimeError('undeclared solver/cloud/teacher/model import')
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        for rel in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
            base = os.path.normcase(str(R/rel))
            if path == base or path.startswith(base+os.sep):
                forbidden.append('protected_or_actual_data'); raise RuntimeError('no actual/protected corpus/artifact reads')
        if event == 'open' and Path(path).suffix in ('.pt','.pth','.ckpt','.safetensors'):
            if not Path(path).is_relative_to(base_temp):
                forbidden.append('historical_checkpoint_io'); raise RuntimeError('only newly manufactured basetemp checkpoint I/O')


sys.addaudithook(audit)
caps = allocation['counter_caps']
expected = allocation['expected_core_counts']
started = {key: 0 for key in caps}
returned = started.copy()
restores = []
resources = dict(observed_peak_rss_bytes=0, observed_minimum_available_ram_bytes=None, samples=0)
stop = threading.Event()
monitor = None
monitor_errors = []
original_error = None
rc, counts, xml_error, metadata, torch_info = None, None, None, None, None
methods_restored = True
runtime_restored = True
torch_threads_before = None
memory_lock = threading.Lock()


def patch(obj, name, value):
    restores.append((obj, name, getattr(obj, name), name in vars(obj)))
    setattr(obj, name, value)


def denied(label):
    def call(*args, **kwargs):
        forbidden.append(label)
        raise RuntimeError('forbidden native operation: '+label)
    return call


def counted(key, original, validate=None):
    @functools.wraps(original)
    def call(*args, **kwargs):
        started[key] += 1
        journal(dict(event='native_reserved', counter=key, count=started[key]))
        need(started[key] <= caps[key], 'native reservation exceeded: '+key)
        if validate is not None:
            validate(*args, **kwargs)
        result = original(*args, **kwargs)
        returned[key] += 1
        journal(dict(event='native_body_returned', counter=key, count=returned[key]))
        return result
    return call


def journal(value):
    value['elapsed_seconds'] = max(time.perf_counter()-START, time.time()-WALL)
    value['native_started'] = started.copy()
    value['native_body_returned'] = returned.copy()
    with (out/'case_events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False)+'\n'); stream.flush(); os.fsync(stream.fileno())


class Journal:
    def pytest_runtest_logstart(self, nodeid, location):
        journal(dict(event='start', nodeid=nodeid))
    def pytest_runtest_logreport(self, report):
        journal(dict(event=report.when, nodeid=report.nodeid, outcome=report.outcome, seconds=report.duration))


try:
    # Native platform bootstrap is inherited by this worker's owned Job.
    # No platform._syscmd_ver/cache fixture replacement.
    begun = time.perf_counter()
    need(sys.platform == 'win32' and type(os.environ.get('SystemRoot')) is str, 'native Windows SystemRoot required')
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_absolute() and '..' not in system_cmd.parts and system_cmd.is_file()
         and not system_cmd.is_symlink() and not getattr(system_cmd, 'is_junction', lambda: False)(), 'actual system cmd file required')
    metadata = dict(public_api='platform.uname', allowed_executable=str(system_cmd), commands=metadata_calls,
                    inside_owned_job=True, phase_closed=False)
    try:
        actual = platform.uname()
        metadata.update(system=actual.system, release=actual.release, version=actual.version, machine=actual.machine)
    finally:
        phase[0] = 'tests'
        metadata.update(phase_closed=True, seconds=time.perf_counter()-begun)
    need(actual.system == 'Windows' and len(metadata_calls) <= 3, 'native Windows metadata')
    import psutil
    process = psutil.Process()

    def memory():
        with memory_lock:
            info = process.memory_info()
            available = int(psutil.virtual_memory().available)
            peak = max(int(info.rss), int(info.peak_wset))
            resources['observed_peak_rss_bytes'] = max(resources['observed_peak_rss_bytes'], peak)
            old = resources['observed_minimum_available_ram_bytes']
            resources['observed_minimum_available_ram_bytes'] = available if old is None else min(old, available)
            resources['samples'] += 1
            need(available >= 1024**3 and peak <= 512*1024**2, 'observed RAM bound')
            return available

    available_start = memory()  # Before Torch/model import.
    resources['pre_torch_available_ram_bytes'] = available_start

    def watch():
        while not stop.wait(.1):
            try:
                memory()
            except BaseException as error:
                monitor_errors.append(str(error))
                try:
                    write('resource-failure.json', dict(error=str(error), resources=resources,
                        native_started=started, native_body_returned=returned))
                finally:
                    os._exit(125)

    monitor = threading.Thread(target=watch, daemon=True)
    monitor.start()
    sys.path.insert(0, str(R/'src'))
    import torch
    need(torch.__version__ == '2.7.1+cpu' and torch.version.cuda is None and not torch.cuda.is_initialized(), 'CPU Torch profile')
    need(Path(torch.__file__).resolve().is_relative_to((R/'.venv').resolve()), 'isolated Torch origin')
    torch_threads_before = torch.get_num_threads()
    torch.set_num_threads(2)
    torch_info = dict(version=torch.__version__, origin=torch.__file__, cuda_build=torch.version.cuda,
        cuda_initialized=False, threads_during=2, interop_threads=torch.get_num_interop_threads(),
        python=sys.version, executable=sys.executable, prefix=sys.prefix)
    import numpy as np
    need(np.__version__ == '2.5.4' and Path(np.__file__).resolve().is_relative_to((R/'.venv').resolve()), 'isolated pinned NumPy')
    torch_info.update(numpy_version=np.__version__, numpy_origin=np.__file__)
    memory()  # After heavy import, before any test model.
    from knowledge_tracing.sakt.model import SAKTCore
    from knowledge_tracing.sakt import training as engineering

    def tiny_constructor(self, config, *args, **kwargs):
        need(config.d_model == 4 and config.num_heads == 1 and config.head_dim == 4
             and config.max_length <= 3 and config.num_items <= 3, 'tiny fixture model geometry')
    def cpu_forward(self, batch):
        need(batch.item_ids.device.type == 'cpu' and batch.item_ids.shape[0] <= 32
             and batch.item_ids.shape[1] <= 3 and all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in self.parameters()), 'CPU FP32 tiny forward')
    patch(SAKTCore, '__init__', counted('constructors', SAKTCore.__init__, tiny_constructor))
    patch(SAKTCore, 'forward', counted('forwards', SAKTCore.forward, cpu_forward))
    # Chỉ public autograd logical calls; không đếm lặp Tensor.__torch_function__.
    patch(torch.autograd, 'backward', counted('logical_backwards', torch.autograd.backward))
    patch(torch.optim.Adam, '__init__', counted('adam_constructors', torch.optim.Adam.__init__))
    patch(torch.optim.Adam, 'step', counted('adam_steps', torch.optim.Adam.step))
    patch(torch.optim.SGD, '__init__', denied('unallocated SGD constructor'))
    patch(torch.optim.SGD, 'step', denied('unallocated SGD step'))
    patch(torch.optim.AdamW, '__init__', denied('AdamW constructor'))
    patch(engineering, 'train_synthetic_sakt', denied('train_synthetic_sakt'))
    patch(engineering, 'evaluate_sakt', denied('evaluate_sakt engineering path'))
    def safe_load(*args, **kwargs):
        need(kwargs.get('weights_only') is True and kwargs.get('map_location') == 'cpu', 'strict weights_only CPU deserialization')
    patch(torch, 'save', counted('torch_save_calls', torch.save))
    patch(torch, 'load', counted('torch_load_calls', torch.load, safe_load))
    patch(torch.nn.Module, 'load_state_dict', counted('model_state_restores', torch.nn.Module.load_state_dict))
    patch(torch.optim.Optimizer, 'load_state_dict', counted('optimizer_state_restores', torch.optim.Optimizer.load_state_dict))
    from knowledge_tracing import simulator_corpus_reader as corpus_reader
    patch(corpus_reader, 'read_public_research_corpus', denied('actual corpus reader'))
    for name in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all'):
        patch(torch.cuda, name, denied('CUDA execution:'+name))
    patch(torch.Tensor, 'cuda', denied('Tensor.cuda'))
    patch(torch.nn.Module, 'cuda', denied('Module.cuda'))
    import pytest
    with (out/'pytest.log').open('x', encoding='utf-8') as log, redirect_stdout(log), redirect_stderr(log):
        rc = int(pytest.main(['tests/sakt/test_research_checkpoint.py','-q','-p','no:cacheprovider',
            '--basetemp='+str(base_temp),'--junitxml='+str(out/'junit.xml')], plugins=[Journal()]))
    memory()
except BaseException as error:
    original_error = dict(type=type(error).__name__, message=str(error))
finally:
    phase[0] = 'finalization'
    stop.set()
    if monitor is not None:
        monitor.join(timeout=.5)
    for obj, name, original, had_own in reversed(restores):
        try:
            if had_own:
                setattr(obj, name, original)
            else:
                delattr(obj, name)
            methods_restored = methods_restored and getattr(obj, name) is original and (name in vars(obj)) == had_own
        except BaseException as error:
            methods_restored = False
            original_error = original_error or dict(type=type(error).__name__, message=str(error))
    if torch_threads_before is not None:
        try:
            torch.set_num_threads(torch_threads_before)
            torch_info['threads_after'] = torch.get_num_threads()
            torch_info['cuda_initialized_after'] = torch.cuda.is_initialized()
            runtime_restored = torch_info['threads_after'] == torch_threads_before
        except BaseException as error:
            runtime_restored = False
            original_error = original_error or dict(type=type(error).__name__, message=str(error))
    for key, value in env_before.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    try:
        tree = ET.parse(out/'junit.xml').getroot()
        counts = {key: sum(int(s.get(key, '0')) for s in tree.iter('testsuite'))
                  for key in ('tests','failures','errors','skipped')}
        need(len(list(tree.iter('testcase'))) == counts['tests'], 'XML testcase count')
    except BaseException as error:
        xml_error = dict(type=type(error).__name__, message=str(error))
    source_after, absent_after, packet_after, gate_after = {}, False, None, {}
    try:
        source_after = {name: sha(R/name) for name in pins}
        absent_after = all(not (R/name).exists() for name in allocation['absent_source_paths'])
        packet_after = sha(PACKET)
        gate_after = gate_sources()
        if monitor is not None:
            memory()
    except BaseException as error:
        original_error = original_error or dict(type=type(error).__name__, message=str(error))
    elapsed = max(time.perf_counter()-START, time.time()-WALL)
    result = dict(status='PENDING_OUTER_ACCEPTANCE', pytest_exit_code=rc, counts=counts,
        native_started=started, native_body_returned=returned, expected_core_counts=expected, counter_caps=caps,
        source_before=pins, source_after=source_after, source_unchanged=pins == source_after,
        allocation_sha256=PACKET_SHA, allocation_sha256_after=packet_after, namespace_absence_unchanged=absent_after,
        frozen154_before=gate_before, frozen154_after=gate_after, frozen154_unchanged=gate_before==gate_after,
        native_os_metadata=metadata, metadata_phase_closed=phase[0] != 'windows_metadata',
        forbidden_attempts=forbidden, resources=resources,
        methods_restored=methods_restored, runtime_restored=runtime_restored,
        environment_restored=env_before == {k: os.environ.get(k) for k in envkeys},
        monitor_stopped=monitor is None or not monitor.is_alive(), monitor_errors=monitor_errors,
        torch_profile=torch_info, original_exception=original_error, junit_error=xml_error,
        elapsed_seconds=elapsed, child_timer_seconds=83,
        scope_vi='33handmade checkpoint fixtures; actual native/serialization counters, hard3Adamupdates, no actualcorpus/teacher/GPU/selectedfitted/modelselection. Frozen154 source-only guard không currentGate acceptance; cooperativeRAM, fullGate floor4GiB không đổi.')
    accepted = (rc == 0 and counts == dict(tests=33, failures=0, errors=0, skipped=0)
        and started == returned and all(returned[k] == v for k,v in expected.items())
        and all(0 < returned[k] <= caps[k] for k in ('torch_save_calls','torch_load_calls','model_state_restores','optimizer_state_restores'))
        and not forbidden and original_error is None and xml_error is None
        and methods_restored and runtime_restored and result['environment_restored'] and result['monitor_stopped'] and not monitor_errors
        and result['source_unchanged'] and result['frozen154_unchanged'] and absent_after and packet_after == PACKET_SHA
        and 0 < resources['observed_peak_rss_bytes'] <= 512*1024**2
        and resources['observed_minimum_available_ram_bytes'] is not None
        and resources['observed_minimum_available_ram_bytes'] >= 1024**3 and elapsed < 83
        and torch_info is not None and not torch.cuda.is_initialized())
    result['status'] = 'ACCEPTED_CHILD_FIXTURES_PENDING_OUTER' if accepted else 'REJECTED_CHILD_FIXTURE'
    write('result.json', result)
    if max(time.perf_counter()-START, time.time()-WALL) >= 83:
        write('postwrite_rejection.json', dict(status='REJECTED_CHILD_POSTWRITE_BUDGET'))
        accepted = False
    timer.cancel()
raise SystemExit(0 if accepted else 1)
