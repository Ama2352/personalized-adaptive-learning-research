"""ROOT worker:18fixture CG-AKT,80s trong owned87/outer90; source-only/chưa dispatch."""
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
import shutil
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
PACKET = P/'cgakt_research_model02_allocation.json'
PACKET_SHA = '423144d833b7f77f1cebacd5ed8e5f1a9e13e4e0477630b33509f03f6d3391f6'
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import worker_gate


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


timer = threading.Timer(80, lambda: os._exit(124))
timer.daemon = True
timer.start()
owner = worker_gate()  # No native/domain import before actual worker GO.
out = P/'cgakt-research-model02'
out.mkdir(exist_ok=False)
os.chdir(R)
raw = PACKET.read_bytes()
need(hashlib.sha256(raw).hexdigest() == PACKET_SHA, 'reviewed allocation bytes')
allocation = json.loads(raw)
pins = allocation['source_pins']
need(len(pins) == 28 and all(sha(R/name) == digest for name, digest in pins.items()), 'reviewed source pins')
need(all(not (R/name).exists() for name in allocation['absent_source_paths']), 'namespace source absence changed')
base_temp = R/'artifacts/akt/local-tests/cgm01'
need(not base_temp.exists(), 'exclusive pytest basetemp already exists')


def write(name, value):
    with (out/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


write('reservation.json', dict(kind='CGAKT_RECIPE26_TINY_ENGINEERING_ONLY', expected_cases=18,
    expected_native_counts=allocation['expected_native_counts'], actual_native_counts=None,
    allocation_sha256=PACKET_SHA, source_before=pins,
    note_vi='18fixture/8Architecture.forward/5logicalbackwards/0optimizer; RAMhypothesis1GiBRSS/2GiBfree chưa đo; không maintraining.'))
envkeys = ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
           'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS')
env_before = {key: os.environ.get(key) for key in envkeys}
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
    CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
    PYTEST_ADDOPTS='', PYTEST_PLUGINS='')
phase = ['windows_metadata']
metadata_calls, forbidden, git_calls, cuda_queries = [], [], [], []
raw_tensor_backward = dict(started=0, returned=0)
loader_observation = dict(original_calls=0, cache_used=False)
git_before = git_after = None
native_source_before = native_source_after = None
root_native = R/'artifacts/akt/dependencies/upstream'
git_commands = [('rev-parse','HEAD'), ('status','--porcelain','--untracked-files=all'),
    ('remote','get-url','origin')]
for native_name in ('akt.py','README.md','LICENSE'):
    git_commands.extend([('hash-object',native_name), ('rev-parse','HEAD:'+native_name)])
git_commands.append(('rev-parse','HEAD^{tree}'))
git_allowlist = {subprocess.list2cmdline(['git','-C',str(root_native),*tail]) for tail in git_commands}
need(len(git_allowlist) == 10, 'exact10local provenance commands')
git_environment_before = {k: v for k,v in os.environ.items() if k.startswith('GIT_')}
for key in list(git_environment_before):
    os.environ.pop(key, None)
os.environ.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.fsmonitor', GIT_CONFIG_VALUE_0='false',
    GIT_CONFIG_KEY_1='safe.directory', GIT_CONFIG_VALUE_1=root_native.as_posix(),
    GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0')
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
        if phase[0] == 'local_git_provenance':
            try:
                # Windows shell=False may report executable=None; retain the
                # raw audit value, not a fabricated resolved process identity.
                need((args[0] is None or type(args[0]) is str and args[0] == 'git') and type(args[1]) is str
                     and args[1] in git_allowlist and len(git_calls) < 10,
                     'only exact10read-only local Git source commands')
                need(args[1] not in [row['command'] for row in git_calls], 'no duplicate Git command')
            except BaseException:
                forbidden.append('blocked_local_git_command')
                raise
            git_calls.append(dict(executable=args[0], command=args[1], resolved_executable=shutil.which('git')))
            return
        forbidden.append(event); raise RuntimeError('no test subprocess')
    if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
        forbidden.append(event); raise RuntimeError('no process/network operation')
    if event == 'import':
        name = str(args[0])
        if (name.split('.')[0] in ('sklearn','modal','boto3') or name in (
                'knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection',
                'knowledge_tracing.akt.training','knowledge_tracing.akt.research_runner',
                'knowledge_tracing.edge_confidence','knowledge_tracing.simulator_corpus_reader',
                'knowledge_tracing.gam_kt.original_junyi')):
            forbidden.append('import:'+name); raise RuntimeError('undeclared solver/cloud/teacher/model import')
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        for rel in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
            base = os.path.normcase(str(R/rel))
            if path == base or path.startswith(base+os.sep):
                forbidden.append('protected_or_actual_data'); raise RuntimeError('no actual/protected corpus/artifact reads')
        if event == 'open' and Path(path).suffix in ('.pt','.pth','.ckpt','.safetensors'):
            forbidden.append('checkpoint_io'); raise RuntimeError('no checkpoint I/O')


sys.addaudithook(audit)
expected = allocation['expected_native_counts']
started = {key: 0 for key in expected}
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
        need(started[key] <= expected[key], 'native reservation exceeded: '+key)
        if validate is not None:
            validate(*args, **kwargs)
        result = original(*args, **kwargs)
        returned[key] += 1
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
            for name, cap_key in (('pytest.log','max_log_bytes'), ('junit.xml','max_junit_bytes'), ('case_events.jsonl','max_case_journal_bytes')):
                path = out/name
                need(not path.exists() or path.stat().st_size <= allocation[cap_key], 'bounded output bytes:'+name)
            need(available >= 2*1024**3 and peak <= 1024**3, 'observed RAM bound')
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
    from knowledge_tracing.akt import research_graph_model as graph
    from knowledge_tracing.akt import upstream
    from knowledge_tracing import edge_confidence_artifact as scores_reader

    def availability():
        need(phase[0] == 'local_git_provenance' and len(cuda_queries) < 1,
             'only declared upstream availability query')
        actual = real_available()
        cuda_queries.append(dict(phase=phase[0], result=actual))
        need(actual is False, 'actual CPU availability must be false')
        return actual

    real_available = torch.cuda.is_available
    patch(torch.cuda, 'is_available', availability)
    original_build = graph.build_native
    original_loader = upstream.load_upstream

    def observed_loader(root, *, device):
        need(phase[0] == 'local_git_provenance' and root == root_native and device == 'cpu', 'real loader scope')
        loader_observation['original_calls'] += 1
        need(loader_observation['original_calls'] == 1, 'one genuine module load only')
        loaded = original_loader(root, device=device)  # Always executes original; never returns a cache.
        def native_constructor(self, *args, **kwargs):
            need(not args and kwargs.get('n_question') == 3 and kwargs.get('n_pid') == 0
                 and kwargs.get('d_model') == 256 and kwargs.get('n_blocks') == 1
                 and kwargs.get('n_heads') == 8 and kwargs.get('d_ff') == 1024
                 and kwargs.get('final_fc_dim') == 512 and kwargs.get('dropout') == .05
                 and kwargs.get('model_type') == 'akt' and kwargs.get('separate_qa') is False,
                 'actual pinned AKT constructor arguments')
        patch(loaded.AKT, '__init__', counted('backbone_constructors', loaded.AKT.__init__, native_constructor))
        return loaded

    patch(upstream, 'load_upstream', observed_loader)

    def backbone(config, *, n_items):
        global git_before, git_after, native_source_before, native_source_after
        need(phase[0] == 'tests' and n_items == 3 and config.d_model == 256
             and config.heads == 8 and config.blocks == 1 and config.d_ff == 1024
             and config.final_fc == 512 and config.dropout == .05 and config.context == config.target_block == 100
             and config.max_length == 200 and config.device == 'cpu'
             and config.source_root == root_native, 'exact research CPU constructor geometry')
        actual_git = shutil.which('git')
        need(actual_git is not None and os.path.normcase(actual_git) == os.path.normcase(allocation['local_git_provenance']['executable']),
             'actual PATH Git origin')
        git_before = sha(Path(actual_git))
        need(git_before == allocation['local_git_provenance']['sha256'], 'pinned real Git executable')
        # Literal git must not be shadowed in the project/venv/application cwd.
        for directory in (R, Path(sys.executable).parent, Path(sys._base_executable).parent):
            need(not any((directory/name).exists() for name in ('git.exe','git.com','git.cmd','git.bat')),
                 'local Git executable shadow')
        native_source_before = {name: sha(root_native/name) for name in ('akt.py','README.md','LICENSE')}
        phase[0] = 'local_git_provenance'
        try:
            native = original_build(config, n_items=n_items)  # REAL load_upstream + REAL verify_upstream.
        finally:
            phase[0] = 'tests'
            git_after = sha(Path(actual_git))
            native_source_after = {name: sha(root_native/name) for name in ('akt.py','README.md','LICENSE')}
        need(git_before == git_after and native_source_before == native_source_after
             and len(git_calls) == 10 and {row['command'] for row in git_calls} == git_allowlist,
             'actual local provenance source/commands unchanged')
        architecture = type(native.model)
        def forward_geometry(self, q_embed, qa_embed):
            need(q_embed.shape == qa_embed.shape and q_embed.ndim == 3
                 and 1 <= q_embed.shape[0] <= 2 and 1 <= q_embed.shape[1] <= 6
                 and q_embed.shape[2] == 256 and q_embed.device.type == qa_embed.device.type == 'cpu'
                 and q_embed.dtype == qa_embed.dtype == torch.float32, 'bounded CPU2x6 native forward')
        patch(architecture, 'forward', counted('forwards', architecture.forward, forward_geometry))
        return native

    patch(graph, 'build_native', backbone)
    patch(graph.ResearchGraphNative, '__init__',
          counted('wrapper_constructors', graph.ResearchGraphNative.__init__))
    linear_init = torch.nn.Linear.__init__
    def linear(self, in_features, out_features, *args, **kwargs):
        if (in_features, out_features) == (4, 1):
            return counted('gate_constructors', linear_init)(self, in_features, out_features, *args, **kwargs)
        return linear_init(self, in_features, out_features, *args, **kwargs)
    patch(torch.nn.Linear, '__init__', linear)
    tensor_backward = torch.Tensor.backward
    def raw_backward(*args, **kwargs):
        raw_tensor_backward['started'] += 1
        need(raw_tensor_backward['started'] <= 20, 'raw dispatch observation cap, not logical backward allowance')
        result = tensor_backward(*args, **kwargs)
        raw_tensor_backward['returned'] += 1
        return result
    patch(torch.Tensor, 'backward', raw_backward)
    patch(torch.autograd, 'backward', counted('logical_backwards', torch.autograd.backward))
    patch(torch.autograd, 'grad', denied('undeclared autograd.grad'))
    patch(torch.optim.Adam, '__init__', counted('adam_constructors', torch.optim.Adam.__init__))
    patch(torch.optim.Adam, 'step', counted('adam_steps', torch.optim.Adam.step))
    for optimizer_type in (torch.optim.AdamW, torch.optim.SGD):
        patch(optimizer_type, '__init__', denied('undeclared optimizer constructor'))
        patch(optimizer_type, 'step', denied('undeclared optimizer step'))
    patch(scores_reader, 'load_method24_scores', denied('actual Method24 artifact parser'))
    patch(torch, 'save', denied('torch.save'))
    patch(torch, 'load', denied('torch.load'))
    for name in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all'):
        patch(torch.cuda, name, denied('CUDA execution:'+name))
    patch(torch.Tensor, 'cuda', denied('Tensor.cuda'))
    patch(torch.nn.Module, 'cuda', denied('Module.cuda'))
    import pytest
    with (out/'pytest.log').open('x', encoding='utf-8') as log, redirect_stdout(log), redirect_stderr(log):
        rc = int(pytest.main(['tests/akt/test_research_graph_model.py','-q','-p','no:cacheprovider',
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
    for key in list(os.environ):
        if key.startswith('GIT_'):
            os.environ.pop(key, None)
    os.environ.update(git_environment_before)
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
    testcase_names = []
    if xml_error is None:
        testcase_names = [case.get('name') for case in tree.iter('testcase')]
        if len(set(testcase_names)) != 18 or set(testcase_names) != set(allocation['expected_test_names']):
            xml_error = dict(type='PopulationMismatch', message='exact18 reviewed test names required')
    source_after, absent_after, packet_after = {}, False, None
    try:
        source_after = {name: sha(R/name) for name in pins}
        absent_after = all(not (R/name).exists() for name in allocation['absent_source_paths'])
        packet_after = sha(PACKET)
        if monitor is not None:
            memory()
    except BaseException as error:
        original_error = original_error or dict(type=type(error).__name__, message=str(error))
    elapsed = max(time.perf_counter()-START, time.time()-WALL)
    result = dict(status='PENDING_OUTER_ACCEPTANCE', pytest_exit_code=rc, counts=counts,
        native_started=started, native_body_returned=returned, expected_native_counts=expected,
        testcase_names=testcase_names, raw_tensor_backward_dispatch=raw_tensor_backward,
        local_git_provenance=dict(commands=git_calls, expected_commands=10, git_sha256_before=git_before,
            git_sha256_after=git_after, native_source_before=native_source_before, native_source_after=native_source_after,
            original_loader_used=loader_observation['original_calls'] == 1,
            original_loader_calls=loader_observation['original_calls'], cached_module_used=loader_observation['cache_used']),
        upstream_cuda_availability=cuda_queries,
        source_before=pins, source_after=source_after, source_unchanged=pins == source_after,
        allocation_sha256=PACKET_SHA, allocation_sha256_after=packet_after, namespace_absence_unchanged=absent_after,
        native_os_metadata=metadata, metadata_phase_closed=phase[0] != 'windows_metadata',
        forbidden_attempts=forbidden, resources=resources,
        methods_restored=methods_restored, runtime_restored=runtime_restored,
        environment_restored=(env_before == {k: os.environ.get(k) for k in envkeys}
            and git_environment_before == {k:v for k,v in os.environ.items() if k.startswith('GIT_')}),
        monitor_stopped=monitor is None or not monitor.is_alive(), monitor_errors=monitor_errors,
        torch_profile=torch_info, original_exception=original_error, junit_error=xml_error,
        elapsed_seconds=elapsed, child_timer_seconds=80,
        scope_vi='18fixture CPU researchgeometry256,2x6tokens,8Architectureforwards/5logicalbackwards/0optimizer. Actualupstreamavailabilityfalse,not0queries/whole-syscallattestation.1GiBRSS/2GiBfreecooperativemonitorresourcehypothesis;7fullcachehash/trainbatchblocks maintraining.')
    accepted = (rc == 0 and counts == dict(tests=18, failures=0, errors=0, skipped=0)
        and started == returned == expected and not forbidden and original_error is None and xml_error is None
        and methods_restored and runtime_restored and result['environment_restored'] and result['monitor_stopped'] and not monitor_errors
        and result['source_unchanged'] and absent_after and packet_after == PACKET_SHA
        and len(git_calls) == 10 and {row['command'] for row in git_calls} == git_allowlist
        and git_before == git_after == allocation['local_git_provenance']['sha256']
        and native_source_before == native_source_after
        and loader_observation == dict(original_calls=1, cache_used=False)
        and len(cuda_queries) == 1 and cuda_queries[0]['result'] is False
        and 0 < resources['observed_peak_rss_bytes'] <= 1024**3
        and resources['observed_minimum_available_ram_bytes'] is not None
        and resources['observed_minimum_available_ram_bytes'] >= 2*1024**3 and elapsed < 80
        and torch_info is not None and not torch.cuda.is_initialized())
    result['status'] = 'ACCEPTED_CHILD_FIXTURES_PENDING_OUTER' if accepted else 'REJECTED_CHILD_FIXTURE'
    write('result.json', result)
    if max(time.perf_counter()-START, time.time()-WALL) >= 80:
        write('postwrite_rejection.json', dict(status='REJECTED_CHILD_POSTWRITE_BUDGET'))
        accepted = False
    timer.cancel()
raise SystemExit(0 if accepted else 1)
