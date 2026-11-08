"""GRAPH19 producer/consumer: mới OS process, không lifecycle resume."""
import time
START, WALL = time.perf_counter(), time.time()
from contextlib import redirect_stdout, redirect_stderr
import functools
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import random
import shutil
import struct
import subprocess
import sys
import threading
from dataclasses import asdict, replace

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
PACKET = P/'graph_checkpoint_fresh_process01_allocation.json'
ROLE = sys.argv[2] if len(sys.argv) == 4 else None
OUT = P/('graph19-fresh-'+str(ROLE)+'01')
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import worker_gate


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def monitor_file_size(path):
    """Bỏ qua CHỈ pending biến mất lúc publish; final bytes vẫn kiểm strict.

    stat sau is_file cũng phân biệt directory thật với nonpending đã mất trong
    race. Không nuốt PermissionError/OSError khác hoặc tên pending tùy ý.
    """
    try:
        if path.is_file():
            return path.stat().st_size
        path.stat()  # Directory được bỏ qua; missing nonpending vẫn phải fail.
        return None
    except FileNotFoundError:
        if path.name in ('state.pt.pending', 'metadata.json.pending', 'COMPLETE.json.pending'):
            return None
        raise


def elapsed():
    return max(time.perf_counter()-START, time.time()-WALL)


def write(name, value):
    with open(OUT/name, 'x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


timer = threading.Timer(53, lambda: os._exit(124)); timer.daemon = True; timer.start()
owner = worker_gate()
need(ROLE in ('producer','consumer') and len(sys.argv) == 4, 'reviewed packetSHA/typedrole/externalhandoffSHA required')
need((ROLE == 'producer' and sys.argv[3] == '-') or ROLE == 'consumer' and re.fullmatch('[0-9a-f]{64}',sys.argv[3]), 'role-specific handoff argument')
raw = PACKET.read_bytes(); need(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == sys.argv[1], 'native packet bytes')
packet = json.loads(raw); pins = packet['source_pins']; caps = packet['allocation']['roles'][ROLE]['counter_caps']
need(packet['allocation']['producer_run_id']=='graph19-fresh-producer-20261109-01'
    and packet['allocation']['consumer_run_id']=='graph19-fresh-consumer-20261109-01', 'fixed fresh experiment namespaces')
need(all(sha(R/n) == h for n,h in pins.items()), 'native source pins')
need(all(sha(Path(n)) == h for n,h in packet['runtime_pins'].items()), 'native runtime component pins')
need(not OUT.exists(), 'exclusive fresh process role output')
OUT.mkdir(); os.chdir(R)
write('reservation.json', dict(kind=packet['kind'], allocation_sha256=sys.argv[1], source_before=pins,
    role=ROLE, call_caps=caps, actual_calls=None, owner=owner,
    scope_vi='Handmade fullE1 producer plus fullE2 control/restored; no realcorpus/selectedfit/midcursor/lifecycle resume.'))
envkeys = ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
    'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS')
env_before = {k:os.environ.get(k) for k in envkeys}
git_before_env = {k:v for k,v in os.environ.items() if k.startswith('GIT_')}
for key in git_before_env: os.environ.pop(key, None)
os.environ.update(packet['local_git_provenance']['process_config'])
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
    CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTEST_ADDOPTS='', PYTEST_PLUGINS='')
phase = ['windows_metadata']; metadata_calls = []; forbidden = []; git_calls = []
cuda_queries = dict(total=0, counts_by_phase_kind={}, first_samples=[], true_results=0)
system_cmd = None; native_begin = None; git_round = 0
root_native = R/'artifacts/akt/dependencies/upstream'
tails = [('rev-parse','HEAD'), ('status','--porcelain','--untracked-files=all'), ('remote','get-url','origin')]
for name in ('akt.py','README.md','LICENSE'): tails.extend([('hash-object',name), ('rev-parse','HEAD:'+name)])
tails.append(('rev-parse','HEAD^{tree}'))
git_allow = {subprocess.list2cmdline(['git','-C',str(root_native),*tail]) for tail in tails}
need(len(git_allow) == 10, 'exact10 Git commands each genuine construction')
owned_run = [None]
checkpoint_root = R/packet['allocation']['producer_checkpoint_directory']
leafs = {'epoch-1'}
file_names = {'state.pt','metadata.json','COMPLETE.json','failure.json',
    'state.pt.pending','metadata.json.pending','COMPLETE.json.pending'}


def own_checkpoint_path(path, *, mkdir=False):
    base = R/'experiments/akt/results'
    if not path.is_relative_to(base): return False
    parts = path.relative_to(base).parts
    if not parts or parts[0] != packet['allocation']['producer_run_id']: return False
    candidate = base/parts[0]
    if owned_run[0] is None:
        if ROLE == 'producer': need(mkdir and not candidate.exists(), 'fresh producer run before first mkdir')
        else: need(not mkdir and candidate.is_dir(), 'consumer reads exact externally pinned producer run')
        owned_run[0] = candidate
    if candidate != owned_run[0]: return False
    return len(parts) == 1 or len(parts) == 2 and parts[1] == 'checkpoints' or (
        len(parts) in (3,4) and parts[1] == 'checkpoints' and parts[2] in leafs
        and (len(parts) == 3 or parts[3] in file_names))


def audit(event, args):
    if event == 'subprocess.Popen':
        if phase[0] == 'windows_metadata':
            fixed = os.path.normcase(os.path.abspath(str(system_cmd)))
            allowed = {fixed.casefold()+' /c "ver"', '"'+fixed.casefold()+'" /c "ver"'}
            need(system_cmd is not None and len(metadata_calls) < 3 and type(args[0]) is str and type(args[1]) is str
                and os.path.normcase(os.path.abspath(args[0])) == fixed and args[1].strip().casefold() in allowed,
                'only actual bounded Windows version command')
            metadata_calls.append(dict(executable=args[0], command=args[1])); return
        if phase[0] == 'local_git_provenance':
            previous = [r['command'] for r in git_calls if r['round'] == git_round]
            need(git_round == 1 and len(previous) < 10 and args[1] in git_allow and args[1] not in previous
                and (args[0] is None or args[0] == 'git'), 'exact10unique read-only Git commands per real loader')
            git_calls.append(dict(round=git_round, executable=args[0], command=args[1])); return
        forbidden.append(event); raise RuntimeError('no undeclared test subprocess')
    if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
        forbidden.append(event); raise RuntimeError('no child/network operation')
    if event == 'import':
        name = str(args[0])
        if name.split('.')[0] in ('sklearn','modal','boto3') or name in (
            'knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection',
            'knowledge_tracing.simulator_corpus_reader','knowledge_tracing.edge_confidence',
            'knowledge_tracing.akt.research_runner','knowledge_tracing.gam_kt.original_junyi'):
            forbidden.append('import:'+name); raise RuntimeError('no teacher/corpus/solver/research runner')
    if event in ('open','os.listdir','os.scandir','os.mkdir') and args and isinstance(args[0], (str,bytes,os.PathLike)):
        path = Path(os.path.abspath(os.fsdecode(args[0])))
        if path == R/'experiments' or path.is_relative_to(R/'experiments'):
            if not own_checkpoint_path(path, mkdir=event == 'os.mkdir'):
                forbidden.append('unowned_experiment_io'); raise RuntimeError('only fixed new producer E1 checkpoint, no general experiments reads')
            if ROLE == 'consumer' and (event == 'os.mkdir' or event == 'open' and
                ((isinstance(args[1],str) and any(c in args[1] for c in 'wax+')) or
                 type(args[2]) is int and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))):
                forbidden.append('consumer_checkpoint_write'); raise RuntimeError('consumer reads only externally bound producer checkpoint')
        for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','venv','.wsl'):
            if path == R/relative or path.is_relative_to(R/relative):
                forbidden.append('protected_or_actual_data'); raise RuntimeError('no actual/protected artifacts')
        if event == 'open' and path.suffix in ('.pt','.pth','.ckpt','.safetensors'):
            need(owned_run[0] is not None and own_checkpoint_path(path), 'only declared fresh native fixture checkpoint bytes')


sys.addaudithook(audit)
import method_patch_observer02 as observer
patches = observer.MethodPatches()
started = {k:0 for k in caps}; returned = started.copy()
timings = dict(adam_body_seconds=[], tracker_pre_seconds=[], tracker_post_seconds=[],
    state_validation_seconds=[], adapter_optimizer_seconds=[], adapter_total_seconds=[])
targets = []; loaders = []; raw_backwards = dict(started=0,returned=0)
stop = threading.Event(); monitor = None; monitor_errors = []
resources = dict(samples=0, observed_peak_rss_bytes=0, observed_minimum_available_ram_bytes=None)
memory_lock = threading.Lock()
metadata = torch_info = None; original_error = None
source_after = {}; restoration = None; proof = None; old_threads = old_dtype = None
tracker = None


def native_guard():
    if native_begin is not None: need(time.perf_counter()-native_begin < 45, 'native work45s allocation')


def journal(value):
    with open(OUT/'case_events.jsonl', 'a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(elapsed_seconds=elapsed(), started=started.copy(), returned=returned.copy(), **value))+'\n')
        stream.flush(); os.fsync(stream.fileno())


def counted(key, function):
    @functools.wraps(function)
    def call(*args, **kwargs):
        native_guard(); started[key] += 1
        journal(dict(kind='native_started', counter=key))
        need(started[key] <= caps[key], 'native call cap:'+key)
        result = function(*args, **kwargs)
        returned[key] += 1; journal(dict(kind='native_body_returned', counter=key)); native_guard()
        return result
    return call


def denied(label):
    def call(*args, **kwargs):
        forbidden.append(label); raise RuntimeError('forbidden native operation:'+label)
    return call


def timed(key, function):
    @functools.wraps(function)
    def call(*args, **kwargs):
        if key == 'state_validation_seconds': need(len(timings[key]) < 128, 'bounded full-state audit observations')
        begun = time.perf_counter()
        try: return function(*args, **kwargs)
        finally: timings[key].append(time.perf_counter()-begun)
    return call


try:
    need(sys.platform == 'win32' and type(os.environ.get('SystemRoot')) is str, 'native Windows SystemRoot')
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_file() and not system_cmd.is_symlink(), 'actual system cmd')
    try:
        actual = platform.uname(); metadata = dict(system=actual.system, machine=actual.machine,
            release=actual.release, version=actual.version, commands=metadata_calls, fixture_replaced=False)
    finally: phase[0] = 'tests'
    import psutil
    process = psutil.Process()
    def memory():
        with memory_lock:
            info = process.memory_info(); peak = max(int(info.rss), int(info.peak_wset)); available = int(psutil.virtual_memory().available)
            resources['samples'] += 1; resources['observed_peak_rss_bytes'] = max(resources['observed_peak_rss_bytes'], peak)
            old = resources['observed_minimum_available_ram_bytes']; resources['observed_minimum_available_ram_bytes'] = available if old is None else min(old, available)
            need(peak <= 1024**3 and available >= 2*1024**3, 'observed native memory bounds')
            for p in OUT.iterdir():
                size = monitor_file_size(p)
                if size is not None: need(size <= 1024**2, 'small native log/metadata cap')
            if owned_run[0] is not None and owned_run[0].exists():
                sizes = [size for p in owned_run[0].rglob('*') if (size := monitor_file_size(p)) is not None]
                need(len(sizes) <= 6 and sum(sizes) <= 70*1024**2, 'bounded one-checkpoint storage')
    memory()
    def watch():
        while not stop.wait(.1):
            try: memory()
            except BaseException as error:
                monitor_errors.append(str(error))
                try: write('resource-failure.json', dict(error=str(error), resources=resources, started=started, returned=returned))
                finally: os._exit(125)
    monitor = threading.Thread(target=watch, daemon=True); monitor.start()
    sys.path.insert(0, str(R/'src'))
    import torch
    import numpy as np
    need(torch.__version__ == '2.7.1+cpu' and torch.version.cuda is None and not torch.cuda.is_initialized(), 'actual CPU Torch profile')
    need(np.__version__ == '2.5.4' and Path(torch.__file__).resolve().is_relative_to(R/'.venv')
        and Path(np.__file__).resolve().is_relative_to(R/'.venv'), 'pinned framework origins')
    old_threads, old_dtype = torch.get_num_threads(), torch.get_default_dtype()
    need(old_dtype == torch.float32, 'actual FP32 startup'); torch.set_num_threads(2)
    torch_info = dict(version=torch.__version__, origin=torch.__file__, numpy_version=np.__version__,
        numpy_origin=np.__file__, threads_during=2, cuda_build=torch.version.cuda)
    runtime = packet['runtime_profile']
    need(runtime['runtime_byte_pins']==packet['runtime_pins'],'shared profile binds actual checked runtime bytes')
    need(torch_info['version'] == runtime['torch_version'] and torch_info['numpy_version'] == runtime['numpy_version']
        and list(sys.version_info[:3]) == runtime['python_version'] and sys.byteorder == runtime['byteorder']
        and metadata['system'] == runtime['system'] and metadata['machine'] == runtime['machine']
        and torch.get_num_threads() == runtime['threads'] and torch.get_default_dtype() == torch.float32,
        'shared actual CPU runtime profile')
    from knowledge_tracing.akt import research_graph_checkpoint as checkpoint, research_graph_model as graph, upstream
    from knowledge_tracing import edge_confidence_artifact as scores
    need(upstream._process_device is None, 'fresh OS process must start without prior native upstream construction')
    static = [(graph,'build_native'), (upstream,'load_upstream'), (graph.ResearchGraphAKTAdapter,'__init__'),
        (graph.ResearchGraphAKTAdapter,'step'), (graph.ResearchGraphNative,'__init__'), (torch.nn.Linear,'__init__'),
        (torch.autograd,'backward'), (torch.autograd,'grad'), (torch.Tensor,'backward'),
        (torch.optim.Adam,'__init__'), (torch.optim.Adam,'step'), (torch.optim.Adam,'load_state_dict'),
        (graph.ResearchGraphNative,'load_state_dict'), (torch.optim.AdamW,'__init__'), (torch.optim.AdamW,'step'),
        (torch.optim.SGD,'__init__'), (torch.optim.SGD,'step'), (torch.nn.utils,'clip_grad_norm_'),
        (torch,'save'), (torch,'load'), (checkpoint,'_torch'), (checkpoint,'_validate_states'),
        (checkpoint.GraphAdamParticipation,'_pre'), (checkpoint.GraphAdamParticipation,'_post'),
        (scores,'load_method24_scores'), (torch.cuda,'is_available'), (torch.cuda,'is_initialized'),
        (torch.Tensor,'cuda'), (torch.nn.Module,'cuda'),
        *((torch.cuda,n) for n in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all'))]
    patches.capture_many(static)
    real_available, real_initialized = torch.cuda.is_available, torch.cuda.is_initialized
    def cuda_query(kind, original):
        def call():
            need(phase[0] in ('local_git_provenance','checkpoint_metadata','adam_constructor','adam_step','serialization')
                and cuda_queries['total'] < packet['cuda_false_query_cap'], 'only declared bounded real CPU metadata query')
            value = original(); cuda_queries['total'] += 1
            key = phase[0]+':'+kind
            cuda_queries['counts_by_phase_kind'][key] = cuda_queries['counts_by_phase_kind'].get(key,0)+1
            if len(cuda_queries['first_samples']) < 16: cuda_queries['first_samples'].append(dict(kind=kind, phase=phase[0], actual=value))
            if value is not False: cuda_queries['true_results'] += 1
            need(value is False, 'real CPU metadata query must remain false'); return value
        return call
    patches.patch(torch.cuda, 'is_available', cuda_query('is_available', real_available))
    patches.patch(torch.cuda, 'is_initialized', cuda_query('is_initialized', real_initialized))
    real_checkpoint_torch = checkpoint._torch
    def checkpoint_torch():
        previous = phase[0]; phase[0] = 'checkpoint_metadata'
        try: return real_checkpoint_torch()
        finally: phase[0] = previous
    patches.patch(checkpoint, '_torch', checkpoint_torch)
    for name, key in (('_pre','tracker_pre_seconds'), ('_post','tracker_post_seconds')):
        patches.patch(checkpoint.GraphAdamParticipation, name, timed(key, getattr(checkpoint.GraphAdamParticipation, name)))
    patches.patch(checkpoint, '_validate_states', timed('state_validation_seconds', checkpoint._validate_states))
    actual_git = shutil.which('git')
    need(actual_git is not None and os.path.normcase(actual_git) == os.path.normcase(packet['local_git_provenance']['executable'])
        and sha(Path(actual_git)) == packet['local_git_provenance']['sha256'], 'pinned real Git executable')
    for directory in (R, Path(sys.executable).parent, Path(sys._base_executable).parent):
        need(not any((directory/name).exists() for name in ('git.exe','git.com','git.cmd','git.bat')), 'no shadow Git executable')
    normalization = packet['local_git_provenance']['normalization_evidence']
    need(sha(R/normalization['path']) == normalization['sha256'], 'historical EOL-normalization probe binding')
    real_loader = upstream.load_upstream
    def loader(root, *, device):
        need(phase[0] == 'local_git_provenance' and device == 'cpu' and root == root_native, 'genuine CPU loader scope')
        loaded = real_loader(root, device=device); loaders.append(dict(round=git_round, original=True, cached=False))
        patches.patch(loaded.AKT, '__init__', counted('backbone_constructors', loaded.AKT.__init__))
        def forward(self, q_embed, qa_embed, original=loaded.Architecture.forward):
            need(q_embed.shape == qa_embed.shape and tuple(q_embed.shape) == (4,6,256)
                and q_embed.device.type == qa_embed.device.type == 'cpu' and q_embed.dtype == qa_embed.dtype == torch.float32,
                'exact four-by-six native geometry')
            return original(self, q_embed, qa_embed)
        patches.patch(loaded.Architecture, 'forward', counted('forwards', forward))
        return loaded
    patches.patch(upstream, 'load_upstream', loader)
    real_build = graph.build_native
    def build(config, *, n_items):
        global git_round
        need(n_items == 3 and config.device == 'cpu' and config.d_model == 256 and config.dropout == .05
            and config.source_root == root_native, 'frozen research backbone config')
        git_round += 1; phase[0] = 'local_git_provenance'
        try: result = real_build(config, n_items=n_items)
        finally: phase[0] = 'tests'
        need(len([r for r in git_calls if r['round'] == git_round]) == 10, 'all10real Git commands executed per construction')
        return result
    patches.patch(graph, 'build_native', build)
    real_ctor = graph.ResearchGraphAKTAdapter.__init__
    def ctor(self, *args, **kwargs):
        global native_begin
        if native_begin is None: native_begin = time.perf_counter()
        need(kwargs['condition'].variant == 'A3' and kwargs['config'].max_steps == 4, 'two actual A3 containers only')
        return real_ctor(self, *args, **kwargs)
    patches.patch(graph.ResearchGraphAKTAdapter, '__init__', counted('adapter_constructors', ctor))
    patches.patch(graph.ResearchGraphNative, '__init__', counted('wrapper_constructors', graph.ResearchGraphNative.__init__))
    real_linear = torch.nn.Linear.__init__
    def linear(self, in_features, out_features, *args, **kwargs):
        function = counted('gate_constructors', real_linear) if (in_features,out_features) == (4,1) else real_linear
        return function(self, in_features, out_features, *args, **kwargs)
    patches.patch(torch.nn.Linear, '__init__', linear)
    real_step = graph.ResearchGraphAKTAdapter.step
    def adapter_step(self, batch, optimizer):
        need(tuple(batch.q_data.shape) == (4,6) and int((batch.loss_targets >= 0).sum()) == 24, '24targets per declared native step')
        begun = time.perf_counter(); targets.append(dict(reserved=24, returned=None,
            input_sha256=graph._batch_sha(batch),window_ids=list(self._ticket.window_ids)))
        row = targets[-1]; result = real_step(self,batch,optimizer)
        row['returned'] = result['valid_targets']; need(result['stepped'] and result['valid_targets'] == 24, 'all24targets optimized')
        timings['adapter_optimizer_seconds'].append(result['optimizer_seconds']); timings['adapter_total_seconds'].append(time.perf_counter()-begun)
        return result
    patches.patch(graph.ResearchGraphAKTAdapter, 'step', counted('adapter_steps', adapter_step))
    for method, key in (('__init__','adam_constructors'), ('step','adam_steps')):
        original = getattr(torch.optim.Adam, method)
        def adam(self, *args, original=original, method=method, **kwargs):
            previous = phase[0]; phase[0] = 'adam_constructor' if method == '__init__' else 'adam_step'
            begun = time.perf_counter()
            try: return original(self,*args,**kwargs)
            finally:
                if method == 'step': timings['adam_body_seconds'].append(time.perf_counter()-begun)
                phase[0] = previous
        patches.patch(torch.optim.Adam, method, counted(key, adam))
    real_backward = torch.Tensor.backward
    def raw_backward(*args, **kwargs):
        raw_backwards['started'] += 1; need(raw_backwards['started'] <= 16, 'raw backward dispatch guard')
        result = real_backward(*args, **kwargs); raw_backwards['returned'] += 1; return result
    patches.patch(torch.Tensor, 'backward', raw_backward)
    patches.patch(torch.autograd, 'backward', counted('logical_backwards', torch.autograd.backward))
    patches.patch(torch.autograd, 'grad', denied('extra autograd.grad'))
    patches.patch(torch.nn.utils, 'clip_grad_norm_', counted('clip_calls', torch.nn.utils.clip_grad_norm_))
    for method, key in (('save','torch_save'),('load','torch_load')):
        original = getattr(torch, method)
        def serialization(*args, original=original, method=method, **kwargs):
            if method == 'load': need(kwargs.get('weights_only') is True and kwargs.get('map_location') == 'cpu', 'weights_only CPU load only')
            previous = phase[0]; phase[0] = 'serialization'
            try: return original(*args, **kwargs)
            finally: phase[0] = previous
        patches.patch(torch, method, counted(key, serialization))
    patches.patch(graph.ResearchGraphNative, 'load_state_dict', counted('model_restore', graph.ResearchGraphNative.load_state_dict))
    patches.patch(torch.optim.Adam, 'load_state_dict', counted('adam_restore', torch.optim.Adam.load_state_dict))
    for optimizer_type in (torch.optim.AdamW, torch.optim.SGD):
        patches.patch(optimizer_type, '__init__', denied('other optimizer constructor')); patches.patch(optimizer_type, 'step', denied('other optimizer step'))
    patches.patch(scores, 'load_method24_scores', denied('real Method24 artifact read'))
    for name in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all'):
        patches.patch(torch.cuda, name, denied('CUDA execution:'+name))
    patches.patch(torch.Tensor, 'cuda', denied('Tensor.cuda')); patches.patch(torch.nn.Module, 'cuda', denied('Module.cuda'))
    # Reuse ONLY data factory; never run native_case/pytest or negative payloads.
    fixture_path = R/'tests/akt/test_research_graph_checkpoint.py'
    spec = importlib.util.spec_from_file_location('_graph19_data_factory_only',fixture_path)
    fixture_module = importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)
    case = fixture_module._handmade()
    from knowledge_tracing.akt import training
    from knowledge_tracing.akt.tensors import collate_windows
    allocation = packet['allocation']
    run_id = allocation['producer_run_id'] if ROLE == 'producer' else allocation['consumer_run_id']
    config = replace(case['config'],run_id=run_id,output_dir=R/'experiments/akt/results'/run_id,max_steps=4)
    budget = dict(max_steps=2,max_targets=48,max_seconds=45.,max_rss_bytes=1024**3,min_available_ram_bytes=2*1024**3)
    # One prescribed seed, not a seed search. Constructor fork does not consume
    # the producer dropout stream; consumer later restores the exact saved RNG.
    random.seed(42);np.random.seed(42);torch.random.default_generator.manual_seed(42)
    active,inactive = [],[]
    for entry in case['entries']:
        records = case['index'].for_windows((entry.window,))[0]
        supported = any(e is not None and any(p.support>0 and p.confidence>0 for p in e.audit.parents) for e in records)
        (active if supported else inactive).append(entry)
    need(len(active)==len(inactive)==4,'fixed handmade4active/4inactive windows')
    permutation=list(range(8));random.Random(config.seed+1).shuffle(permutation)
    full_order=[None]*8
    for position,entry in zip(permutation,inactive+active):full_order[position]=entry
    plan = dict(phase_index_sha256=case['index'].identity,encoding_sha256=case['encoding'].identity,
        condition_sha256=case['condition'].identity,full_window_ids=[e.window.window_id for e in case['entries']],
        epoch1_factory_order=[e.window.window_id for e in full_order],epoch1_shuffle_seed=43,
        epoch2_full_factory_order=[e.window.window_id for e in full_order],epoch2_shuffle_seed=44,
        readout_canonical_order=[e.window.window_id for e in active],geometry=[4,6])
    need(all(plan[name]==value for name,value in allocation['phase_binding'].items()),'externally pinned actual handmade phase/condition/encoding')
    def rng_digest():
        value=checkpoint._rng()
        return dict(scheme='python_numpy_json_and_torch_cpu_rawbytes_v1',python=value_sha(value['python']),
            numpy=value_sha(value['numpy']),torch=hashlib.sha256(value['torch'].numpy().tobytes()).hexdigest())
    def sink(event):
        with open(OUT/'participation_events.jsonl','a',encoding='utf-8') as stream:
            stream.write(json.dumps(dict(role=ROLE,elapsed_seconds=elapsed(),**event))+'\n');stream.flush();os.fsync(stream.fileno())
    handoff = producer = None
    if ROLE == 'consumer':
        handoff_path=P/'graph19-fresh-parent01/handoff.json'
        need(handoff_path.stat().st_size<=2*1024**2 and sha(handoff_path)==sys.argv[3],'external parent handoff bytes')
        handoff=json.loads(handoff_path.read_bytes())
        need(handoff['kind']=='TRUSTED_OWNED_PARENT_HANDOFF_NOT_EXECUTION_OR_SELECTION_AUTHORITY'
            and handoff['packet_sha256']==sys.argv[1] and handoff['producer_reaped_job_empty'] is True,'typed exact parenthandoff')
        producer_path=P/'graph19-fresh-producer01/result.json'
        need(sha(producer_path)==handoff['producer_result_sha256'],'externally bound producer result')
        producer=json.loads(producer_path.read_bytes())
        need(producer['status']=='ACCEPTED_GRAPH19_PRODUCER_PENDING_PARENT' and producer['proof']['plan']==plan,
            'same exact source/input/sampler plan; no relabelled phase')
        need(producer['source_before']==producer['source_after']==pins and producer['packet_sha256']==sys.argv[1]
            and producer['proof']['checkpoint']==handoff['checkpoint'],'handoff producer source/checkpoint identity')
        producer_receipt=P/'graph19-fresh-parent01/producer_owned_receipt.json'
        need(sha(producer_receipt)==handoff['producer_receipt_sha256'],'externally bound owned producer cleanup receipt')
        profile=checkpoint.GraphCheckpointProfile(**producer['proof']['profile'])
        expected_profile=dict(protocol21_sha256=packet['source_pins'][checkpoint.PROTOCOL21_PATH],
            protocol26_sha256=checkpoint.RECIPE_SHA256,runtime_receipt_sha256=packet['historical_runtime_receipt']['sha256'],
            runtime_profile_sha256=value_sha(runtime),candidate_allocation_sha256=value_sha(allocation),
            purpose='selected_fit_candidate',external_system_freeze_sha256=None)
        need(all(asdict(profile)[key]==value for key,value in expected_profile.items()),'meaningful shared profile/allocation bindings')
        identity=checkpoint.graph_checkpoint_identity(config=config,encoding=case['encoding'],condition=case['condition'],
            index=case['index'],profile=profile)
        need(identity==producer['proof']['identity'],'reconstructed typed graph identity before model ctor/load')
        inspected=checkpoint.inspect_graph_epoch_state(checkpoint_root,expected_identity=identity,
            expected_complete_sha256=handoff['checkpoint']['complete_sha256'],limits=fixture_module.LIMITS)
    with torch.random.fork_rng(devices=[]),torch.device('cpu'):
        torch.random.default_generator.manual_seed(42)
        adapter=graph.ResearchGraphAKTAdapter(config=config,encoding=case['encoding'],index=case['index'],condition=case['condition'])
    optimizer=torch.optim.Adam(adapter.native.parameters(),lr=config.lr,betas=config.betas,eps=config.eps,weight_decay=config.weight_decay)
    initial=checkpoint._state_sha(adapter.native.backbone.state_dict())
    need(initial==allocation['initial_backbone_sha256'],'externally pinned seed42 initialbackbone before any update')
    if ROLE=='producer':
        tracker=checkpoint.GraphAdamParticipation(adapter,optimizer,event_sink=sink)
        profile=checkpoint.GraphCheckpointProfile(packet['source_pins'][checkpoint.PROTOCOL21_PATH],checkpoint.RECIPE_SHA256,
            packet['historical_runtime_receipt']['sha256'],value_sha(runtime),initial,value_sha(allocation),'selected_fit_candidate',None)
        identity=checkpoint.graph_checkpoint_identity(config=config,encoding=case['encoding'],condition=case['condition'],index=case['index'],profile=profile)
        tracker.begin_epoch(1)
        stats=training.train_epoch(adapter,lambda:iter(full_order),optimizer=optimizer,epoch=1,budget=budget,
            batch_factory=tracker.collate,progress_callback=tracker.progress)
        receipt=tracker.finish_epoch(stats)
        need(stats.windows_processed==8 and stats.valid_targets==48 and stats.optimizer_steps==2,'actual fullE1 coverage')
        e1_rng=rng_digest();e1_modes=[(name,m.training) for name,m in adapter.native.named_modules()]
        parent=checkpoint_root.parent;parent.mkdir(parents=True,exist_ok=False)
        reference=checkpoint.save_graph_epoch_state(checkpoint_root,adapter=adapter,optimizer=optimizer,
            participation=tracker,epoch_receipt=receipt,expected_identity=identity,profile=profile,limits=fixture_module.LIMITS)
        need(rng_digest()==e1_rng,'save must preserve producer three RNG states')
        checkpoint_ref=dict(directory=checkpoint_root.relative_to(R).as_posix(),complete_sha256=reference.complete_sha256,
            metadata_sha256=reference.metadata_sha256,checkpoint_sha256=reference.checkpoint_sha256,
            checkpoint_bytes=(checkpoint_root/'state.pt').stat().st_size)
        e1_counters=dict(completed_epochs=tracker.completed_epochs,body_returns=tracker.returned,
            optimized_targets=tracker.optimized_targets,parameter_participation=dict(tracker.counts),
            model_sha256=receipt.model_sha256,adam_sha256=receipt.optimizer_sha256)
        direct_restored=None
    else:
        need(initial==profile.initial_backbone_sha256,'fresh consumer initialbackbone before restore')
        e1_rng=producer['proof']['e1_rng_digests'];e1_modes=producer['proof']['e1_module_modes']
        random.seed(981);np.random.seed(982);torch.random.default_generator.manual_seed(983)
        for name,m in adapter.native.named_modules():m.training=not dict(e1_modes)[name]
        perturbed=rng_digest()
        need(all(perturbed[k]!=e1_rng[k] for k in ('python','numpy','torch'))
            and any(m.training!=dict(e1_modes)[name] for name,m in adapter.native.named_modules()),'actual three RNG/mode perturbation witness')
        tracker=checkpoint.restore_graph_epoch_state(inspected,fresh_adapter=adapter,fresh_owned_optimizer=optimizer,
            expected_identity=identity,profile=profile,limits=fixture_module.LIMITS,event_sink=sink)
        need(rng_digest()==e1_rng and [[name,m.training] for name,m in adapter.native.named_modules()]==e1_modes,
            'immediate freshprocess RNG/modes exact restore before forward')
        direct_restored=True;checkpoint_ref=producer['proof']['checkpoint'];e1_counters=producer['proof']['e1_counters']
        need(tracker.returned==2 and tracker.completed_epochs==1 and tracker.optimized_targets==48,'restored completeE1 counters')
        need(checkpoint._state_sha(adapter.native.state_dict())==e1_counters['model_sha256']
            and checkpoint._optimizer_sha(optimizer.state_dict())==e1_counters['adam_sha256'],'exact E1 state before continuation')
    tracker.begin_epoch(2)
    e2=training.train_epoch(adapter,lambda:iter(full_order),optimizer=optimizer,epoch=2,budget=budget,
        batch_factory=tracker.collate,progress_callback=tracker.progress)
    e2_receipt=tracker.finish_epoch(e2)
    need(e2.complete and e2.windows_processed==8 and e2.valid_targets==48 and e2.optimizer_steps==2
        and e2_receipt.completed_epochs==2 and tracker.returned==4 and tracker.optimized_targets==96,
        'actual fullE2 coverage/accounting, not a manually chosen partialbatch')
    need(not adapter._failed and not tracker.failed and adapter._ticket is None and adapter.native._call is None,
        'healthy no-pending state after fullE2')
    e2_ledger=dict(complete=True,completed_epochs=2,epoch_windows=e2.windows_processed,epoch_targets=e2.valid_targets,
        epoch_optimizer_steps=e2.optimizer_steps,tracker_cumulative_bodies=tracker.returned,
        tracker_cumulative_targets=tracker.optimized_targets,windows_sha256=e2_receipt.windows_sha256,
        targets_sha256=e2_receipt.targets_sha256,ordered_batches_sha256=e2_receipt.ordered_batches_sha256,
        actual_ordered_inputs=targets[-2:],sampler_seed=config.seed+2)
    windows=tuple(e.window for e in active)
    batch=collate_windows(windows,n_items=len(adapter.encoding.vocabulary.values),device='cpu',targets=[e.targets for e in active])
    evidence=adapter.index.for_windows(windows)
    modes=[(m,m.training) for m in adapter.native.modules()];before_readout_rng=rng_digest()
    try:
        with torch.random.fork_rng(devices=[]),torch.inference_mode():
            adapter.native.eval();adapter.native.bind(batch,evidence,enabled=True)
            loss,probabilities,count=adapter.native(batch.q_data,batch.qa_data,batch.loss_targets)
            readout=dict(probability_fp32_uint32=probabilities.detach().contiguous().numpy().view(np.uint32).tolist(),
                loss_fp32_hex=struct.pack('<f',float(loss.item())).hex(),count=int(count.item()),
                input_sha256=graph._batch_sha(batch),window_ids=[w.window_id for w in windows])
    finally:
        adapter.native.clear_context()
        for module,mode in modes:module.training=mode
    need(rng_digest()==before_readout_rng,'readout RNG isolation')
    proof=dict(kind='HANDMADE_FRESH_OS_PROCESS_STATE_NOT_LIFECYCLE',role=ROLE,plan=plan,profile=asdict(profile),identity=identity,
        initial_backbone_sha256=initial,checkpoint=checkpoint_ref,e1_rng_digests=e1_rng,e1_module_modes=e1_modes,e1_counters=e1_counters,
        immediate_three_rng_modes_restored=direct_restored,full_epoch2=e2_ledger,
        physical_optimizer_bodies=returned['adam_steps'],tracker_cumulative_bodies=tracker.returned,
        final_model_sha256=checkpoint._state_sha(adapter.native.state_dict()),final_adam_sha256=checkpoint._optimizer_sha(optimizer.state_dict()),
        final_rng_digests=rng_digest(),final_module_modes=[(name,m.training) for name,m in adapter.native.named_modules()],readout=readout,
        fitted_research_model=False,lifecycle_resume_supported=False,sampler_resume_supported=False,
        meaning_vi='Freshprocess completeE1 state transfer+fullE2 sample/state parity, không selectedfit/main/lifecycle/midcursor/final/corpus.')
    if ROLE=='consumer':
        for key in ('full_epoch2','final_model_sha256','final_adam_sha256','final_rng_digests','final_module_modes','readout'):
            need(json.loads(canonical(proof[key]))==producer['proof'][key],'freshprocess exact continuation parity:'+key)
    write('proof.json',proof);memory()
except BaseException as error:
    original_error=dict(type=type(error).__name__,message=str(error))
finally:
    if tracker is not None:
        try:tracker.close()
        except BaseException as error:original_error=original_error or dict(type=type(error).__name__,message=str(error))
    stop.set()
    if monitor is not None:monitor.join(timeout=.5)
    try:restoration=patches.restore()
    except BaseException as error:original_error=original_error or dict(type=type(error).__name__,message=str(error))
    try:
        if old_threads is not None:torch.set_num_threads(old_threads)
        if old_dtype is not None:need(torch.get_default_dtype()==old_dtype,'defaultdtype restored')
        if torch_info is not None:torch_info.update(threads_after=torch.get_num_threads(),cuda_initialized_after=torch.cuda.is_initialized())
    except BaseException as error:original_error=original_error or dict(type=type(error).__name__,message=str(error))
    for key in list(os.environ):
        if key.startswith('GIT_'):os.environ.pop(key,None)
    os.environ.update(git_before_env)
    for key,value in env_before.items():
        if value is None:os.environ.pop(key,None)
        else:os.environ[key]=value
    runtime_after={}
    try:
        source_after={n:sha(R/n) for n in pins};runtime_after={n:sha(Path(n)) for n in packet['runtime_pins']}
        need(actual_git is not None and sha(Path(actual_git))==packet['local_git_provenance']['sha256'],'realGit bytes unchanged')
    except BaseException as error:original_error=original_error or dict(type=type(error).__name__,message=str(error))
    accepted=original_error is None and started==returned==caps and proof is not None and not forbidden and not monitor_errors
    accepted=accepted and restoration is not None and restoration['accepted'] is True and source_after==pins and runtime_after==packet['runtime_pins']
    accepted=accepted and len(git_calls)==10 and len(loaders)==1 and loaders[0]['original'] and not loaders[0]['cached']
    accepted=accepted and cuda_queries['true_results']==0 and torch_info is not None and torch_info['cuda_initialized_after'] is False
    accepted=accepted and native_begin is not None and time.perf_counter()-native_begin<45 and elapsed()<53 and (monitor is None or not monitor.is_alive())
    result=dict(status=('ACCEPTED_GRAPH19_'+ROLE.upper()+'_PENDING_PARENT') if accepted else 'REJECTED_GRAPH19_KEEP_ALL',role=ROLE,
        original_error=original_error,owner=owner,proof=proof,native_started=started,native_body_returned=returned,
        source_before=pins,source_after=source_after,runtime_before=packet['runtime_pins'],runtime_after=runtime_after,
        packet_sha256=sys.argv[1],packet_sha256_after=sha(PACKET),handoff_sha256=sys.argv[3] if ROLE=='consumer' else None,
        metadata=metadata,torch_profile=torch_info,local_git_calls=git_calls,original_loaders=loaders,cuda_false_queries=cuda_queries,
        resources=resources,monitor_errors=monitor_errors,monitor_stopped=monitor is None or not monitor.is_alive(),
        method_restoration=restoration,forbidden_attempts=forbidden,target_observations=targets,timings=timings,
        environment_restored=env_before=={k:os.environ.get(k) for k in envkeys} and git_before_env=={k:v for k,v in os.environ.items() if k.startswith('GIT_')},
        elapsed_seconds=elapsed(),native_work_seconds=None if native_begin is None else time.perf_counter()-native_begin,
        scope_vi='One distinctOSworker stage; parent must verify predecessor cleanup/processidentity/hashhandoff. No lifecycle/actualcorpus/GPU.')
    write('result.json',result)
    if elapsed()>=53:
        write('postwrite_rejection.json',dict(status='REJECTED_WORKER_POSTWRITE_BUDGET',elapsed_seconds=elapsed()));accepted=False
    timer.cancel()
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_GRAPH19_KEEP_ALL',role=ROLE,native_counts=returned,elapsed_seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
