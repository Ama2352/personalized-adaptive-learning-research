"""ROOT-only: CPU checkpoint08,18fixture/4Adam; owned-Job family monitor."""
import time
PERF, WALL, MONO = time.perf_counter, time.time, time.monotonic
START, START_WALL, START_MONO = PERF(), WALL(), MONO()
import ctypes
from ctypes import wintypes
from contextlib import redirect_stdout, redirect_stderr
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import threading
import tempfile
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
PACKET = P/'graph_checkpoint_native08_allocation.json'
OUT = P/'graph-checkpoint-native08'
TMP = R/'artifacts/akt/local-tests/gcn08'
sys.path.insert(0, str(R/'scripts/research'))
from windows_owned_worker import worker_gate, Kernel, MAX_PROCESSES


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_metadata(packet,pin):
    ref=packet['current_metadata_acceptance'];path=R/ref['path'];metadata_packet=R/ref['packet_path']
    need(path.is_file() and sha(path)==pin==ref['sha256'] and sha(metadata_packet)==ref['packet_sha256'],'actual external cold299 receipt/packet SHA')
    actual=json.loads(path.read_bytes());definition=json.loads(metadata_packet.read_bytes());child=actual['child_result'];receipt=actual['receipt']
    need(actual['status']=='ACCEPTED_BATCHC_METADATA_TESTS_NOT_NATIVE' and actual['mode']=='tests' and actual['attempt']=='06'
         and actual['errors']==[] and actual['packet_sha256']==ref['packet_sha256'],'actual accepted current cold299 tests')
    need(receipt['accepted'] is True and receipt['returncode']==0 and receipt['cleanup_accepted'] is True
         and receipt['job_active_after_cleanup']==0 and receipt['actual_worker_in_job_before_GO'] is True
         and receipt['popen_handle_closed'] is True and receipt['errors']==receipt['cleanup_errors']==[],'cold299 genuine owned cleanup')
    need(child['accepted'] is True and child['pytest_exit_code']==0 and child['counts']==dict(tests=299,failures=0,errors=0,skipped=0)
         and child['test_protocol_entries']==child['test_body_entries']==299 and child['denied']==child['collection_errors']==[]
         and child['error'] is None and child['environment_and_sys_restored'] is True
         and child['actual_scientific_modules_absent'] is True,'cold299 actual bodies/0FES/no scientific imports')
    need(child['nodeids']==definition['expected_nodeids'] and len(set(child['nodeids']))==299
         and child['actual_checkpoint_nodeids']==definition['checkpoint38_reference']['expected_nodeids']
         and len(child['actual_checkpoint_nodeids'])==38 and child['deselected_nodeids']==definition['deselect_nodeids'],'exact current38 subset/current299 IDs')
    need(all(name in definition['source_pins'] and definition['source_pins'][name]==packet['source_pins'][name]
             for name in packet['mainc_applied_paths']),'actual current eight MainC source/test bindings')
    for key,values in (('source',definition['source_pins']),('runtime',definition['runtime_pins'])):
        need(actual[key+'_before']==actual[key+'_after']==child[key+'_before']==child[key+'_after']==values,'cold299 stable actual '+key)
        for name,digest in values.items():
            need(sha(Path(name) if Path(name).is_absolute() else R/name)==digest,'cold299 current '+key+' file drift')
            if name in packet['source_pins']:need(packet['source_pins'][name]==digest,'shared current source identity')
    collection_path=R/ref['collection_path'];need(sha(collection_path)==actual['collection_outer_sha256']==ref['collection_sha256'],'actual same-source cold299 collection')
    collection=json.loads(collection_path.read_bytes());observed=collection['child_result']
    need(collection['status']=='ACCEPTED_BATCHC_COLLECTION_ONLY_NOT_TEST_PASS' and collection['errors']==[]
         and observed['accepted'] is True and observed['test_protocol_entries']==observed['test_body_entries']==0
         and observed['nodeids']==child['nodeids'] and collection['source_after']==definition['source_pins']
         and collection['runtime_after']==definition['runtime_pins'] and collection['receipt']['accepted'] is True
         and collection['receipt']['cleanup_accepted'] is True and collection['receipt']['job_active_after_cleanup']==0,
         'actual299 collection0body is distinct from tests299')
    for relative in (ref['path'],ref['child_result_path'],ref['collection_path'],ref['collection_child_path']):
        need(not (R/relative).with_name('postwrite_rejection.json').exists(),'no current metadata postwrite rejection')
    return actual


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
    return max(PERF()-START, WALL()-START_WALL, MONO()-START_MONO)


def write(name, value):
    with open(OUT/name, 'x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


owner = worker_gate()
timer = threading.Timer(max(.001,110-elapsed()), lambda: os._exit(124)); timer.daemon = True; timer.start()
need(len(sys.argv) == 3, 'reviewed native packet SHA and actual cold299 outer SHA required')
raw = PACKET.read_bytes(); need(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == sys.argv[1], 'native packet bytes')
packet = json.loads(raw); pins = packet['source_pins']; caps = packet['counter_caps']
need(len(pins) == packet['source_count'] and all(sha(R/n) == h for n,h in pins.items()), 'native source pins')
need(all(sha(Path(n)) == h for n,h in packet['runtime_pins'].items()), 'native runtime component pins')
metadata_prerequisite=current_metadata(packet,sys.argv[2])
need(not OUT.exists() and not TMP.exists(), 'exclusive native attempt only')
OUT.mkdir(); os.chdir(R)
write('reservation.json', dict(kind=packet['kind'], allocation_sha256=sys.argv[1], source_before=pins,
    expected_cases=18, call_caps=caps, actual_calls=None, owner=owner,metadata_receipt_sha256=sys.argv[2],
    scope_vi='One complete E1=8windows48targets2batches; partial continuation control/restored24each. No actual corpus, no fullE2/lifecycle resume.'))
envkeys = ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
    'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS','TEMP','TMP','TMPDIR')
env_before = {k:os.environ.get(k) for k in envkeys}
temporary = OUT/'runtime-temp'; temporary.mkdir()
tempdir_before = tempfile.tempdir
os.environ.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary))
tempfile.tempdir = None
git_before_env = {k:v for k,v in os.environ.items() if k.startswith('GIT_')}
for key in git_before_env: os.environ.pop(key, None)
os.environ.update(packet['local_git_provenance']['process_config'])
os.environ.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
    CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTEST_ADDOPTS='', PYTEST_PLUGINS='')
phase = ['windows_metadata']; metadata_calls = []; forbidden = []; git_calls = []
active_node=[None];stopper_entries={};stopper_counts=dict(constructors=0,observe=0);corpus_reader_attempts=[0]
cuda_queries = dict(total=0, counts_by_phase_kind={}, first_samples=[], true_results=0)
system_cmd = None; native_begin = None; git_round = 0
root_native = R/'artifacts/akt/dependencies/upstream'
tails = [('rev-parse','HEAD'), ('status','--porcelain','--untracked-files=all'), ('remote','get-url','origin')]
for name in ('akt.py','README.md','LICENSE'): tails.extend([('hash-object',name), ('rev-parse','HEAD:'+name)])
tails.append(('rev-parse','HEAD^{tree}'))
git_allow = {subprocess.list2cmdline(['git','-C',str(root_native),*tail]) for tail in tails}
need(len(git_allow) == 10, 'exact10 Git commands each genuine construction')
owned_run = [None]
leafs = {'epoch-1', *('authenticated-invalid-'+n for n in
    ('missing_positive','python_rng','numpy_rng','torch_rng','mode_bool','mode_name'))}
file_names = {'state.pt','metadata.json','COMPLETE.json','failure.json',
    'state.pt.pending','metadata.json.pending','COMPLETE.json.pending'}


def own_checkpoint_path(path, *, mkdir=False):
    base = R/'experiments/akt/results'
    if not path.is_relative_to(base): return False
    parts = path.relative_to(base).parts
    if not parts or re.fullmatch(r'graph11-handmade-[0-9a-f]{10}', parts[0]) is None: return False
    candidate = base/parts[0]
    if owned_run[0] is None:
        need(mkdir and not candidate.exists(), 'owned fresh test run must be captured before first mkdir')
        owned_run[0] = candidate
    if candidate != owned_run[0]: return False
    return len(parts) == 1 or len(parts) == 2 and parts[1] == 'checkpoints' or (
        len(parts) in (3,4) and parts[1] == 'checkpoints' and parts[2] in leafs
        and (len(parts) == 3 or parts[3] in file_names))


def stopper_opaque_path(path):
    if active_node[0] not in packet['stopper_nodeids'] or not path.is_relative_to(TMP):return False
    parts=path.relative_to(TMP).parts
    return len(parts)==9 and parts[1:7]==('fixture-main','experiments','akt','results','parent','checkpoints') \
        and parts[7] in ('epoch-1','epoch-2') and parts[8]=='state.pt' and path.resolve().is_relative_to(TMP.resolve())


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
            need(git_round in (1,2) and len(previous) < 10 and args[1] in git_allow and args[1] not in previous
                and (args[0] is None or args[0] == 'git'), 'exact10unique read-only Git commands per real loader')
            git_calls.append(dict(round=git_round, executable=args[0], command=args[1])); return
        forbidden.append(event); raise RuntimeError('no undeclared test subprocess')
    if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
        forbidden.append(event); raise RuntimeError('no child/network operation')
    if event == 'import':
        name = str(args[0])
        if name.split('.')[0] in ('sklearn','modal','boto3') or name in (
            'knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection',
            'knowledge_tracing.edge_confidence',
            'knowledge_tracing.akt.research_runner','knowledge_tracing.gam_kt.original_junyi'):
            forbidden.append('import:'+name); raise RuntimeError('no teacher/corpus/solver/research runner')
    if event in ('open','os.listdir','os.scandir','os.mkdir') and args and isinstance(args[0], (str,bytes,os.PathLike)):
        path = Path(os.path.abspath(os.fsdecode(args[0])))
        if path == R/'experiments' or path.is_relative_to(R/'experiments'):
            if not own_checkpoint_path(path, mkdir=event == 'os.mkdir'):
                forbidden.append('unowned_experiment_io'); raise RuntimeError('only newly owned seven checkpoint leaves, no general experiments reads')
        for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','venv','.wsl'):
            if path == R/relative or path.is_relative_to(R/relative):
                forbidden.append('protected_or_actual_data'); raise RuntimeError('no actual/protected artifacts')
        if event == 'open' and path.suffix in ('.pt','.pth','.ckpt','.safetensors'):
            need(stopper_opaque_path(path) or owned_run[0] is not None and own_checkpoint_path(path),
                 'only native owned checkpoint or exact opaque stopper fixture bytes')


sys.addaudithook(audit)
import method_patch_observer02 as observer
patches = observer.MethodPatches()
started = {k:0 for k in caps}; returned = started.copy()
timings = dict(adam_body_seconds=[], tracker_pre_seconds=[], tracker_post_seconds=[],
    state_validation_seconds=[], adapter_optimizer_seconds=[], adapter_total_seconds=[])
targets = []; loaders = []; raw_backwards = dict(started=0,returned=0)
stop = threading.Event(); monitor = None; monitor_errors = []
resources = dict(samples=0, observed_peak_rss_bytes=0, observed_minimum_available_ram_bytes=None)
resources.update(observed_peak_family_rss_bytes=0, maximum_sampled_job_processes=0, exited_during_sample=0,
    scope='EXACT_OWNED_JOB_MEMBERS_SAMPLED_RSS_WITH_WORKER_WINDOWS_HIGH_WATER_NOT_OS_QUOTA')
job_api = job_handle = None
job_query_handle_closed = False
memory_lock = threading.Lock()
rc = counts = metadata = torch_info = None; original_error = xml_error = None
source_after = {}; restoration = None; native_proof = None; old_threads = old_dtype = None


def native_guard():
    if native_begin is not None: need(PERF()-native_begin < 100, 'native work100s allocation')


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
    import psutil
    process = psutil.Process()
    job_api = Kernel()
    job_handle = job_api.check(job_api.k.OpenJobObjectW(0x0004,False,owner['job_name']))
    need(job_api.contains(job_api.k.GetCurrentProcess(),job_handle),'same actual owned Job before family sampling')
    class ProcessList(ctypes.Structure):
        _fields_ = [('assigned',wintypes.DWORD),('listed',wintypes.DWORD),('pids',ctypes.c_size_t*MAX_PROCESSES)]
    def family_rss():
        row = ProcessList()
        job_api.check(job_api.k.QueryInformationJobObject(job_handle,3,ctypes.byref(row),ctypes.sizeof(row),None))
        need(0<row.listed==row.assigned<=MAX_PROCESSES,'complete bounded owned Job PID list')
        pids = [int(row.pids[i]) for i in range(row.listed)]
        need(process.pid in pids and len(pids)==len(set(pids)),'actual worker in unique Job family snapshot')
        total = 0
        for pid in pids:
            handle = job_api.k.OpenProcess(0x1000,False,pid)
            if not handle:
                need(not psutil.pid_exists(pid),'live Job process could not be queried')
                resources['exited_during_sample']+=1
                continue
            try:
                need(job_api.contains(handle,job_handle),'sampled PID still belongs to exact owned Job')
                token = job_api.token(handle)
                child = psutil.Process(pid)
                need(abs(child.create_time()-token['create_time'])<=1e-5,'sampled process creation identity')
                total+=int(child.memory_info().rss)
            except psutil.NoSuchProcess:
                resources['exited_during_sample']+=1
            finally:
                job_api.close(handle)
        resources['maximum_sampled_job_processes']=max(resources['maximum_sampled_job_processes'],len(pids))
        return total
    def memory():
        with memory_lock:
            info = process.memory_info(); peak = max(int(info.rss),int(info.peak_wset))
            family = family_rss(); available = int(psutil.virtual_memory().available)
            resources['samples']+=1
            resources['observed_peak_rss_bytes']=max(resources['observed_peak_rss_bytes'],peak)
            resources['observed_peak_family_rss_bytes']=max(resources['observed_peak_family_rss_bytes'],family)
            old = resources['observed_minimum_available_ram_bytes']
            resources['observed_minimum_available_ram_bytes']=available if old is None else min(old,available)
            need(peak<=1024**3 and family<=1024**3 and available>=2*1024**3,'owned family/worker/free RAM bounds')
            for path in OUT.iterdir():
                size = monitor_file_size(path)
                if size is not None: need(size<=1024**2,'small native log/metadata cap')
            if owned_run[0] is not None and owned_run[0].exists():
                sizes=[size for path in owned_run[0].rglob('*') if (size:=monitor_file_size(path)) is not None]
                need(len(sizes)<=28 and sum(sizes)<=512*1024**2,'bounded seven-leaf native fixture storage')
    memory()
    def watch():
        while not stop.wait(.1):
            try:memory()
            except BaseException as error:
                monitor_errors.append(str(error))
                try:write('resource-failure.json',dict(error=str(error),resources=resources,started=started,returned=returned))
                finally:os._exit(125)
    monitor=threading.Thread(target=watch,daemon=True);monitor.start()
    need(sys.platform == 'win32' and type(os.environ.get('SystemRoot')) is str, 'native Windows SystemRoot')
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_file() and not system_cmd.is_symlink(), 'actual system cmd')
    try:
        actual = platform.uname(); metadata = dict(system=actual.system, machine=actual.machine,
            release=actual.release, version=actual.version, commands=metadata_calls, fixture_replaced=False)
    finally: phase[0] = 'tests'
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
    from knowledge_tracing.akt import research_graph_checkpoint as checkpoint, research_graph_model as graph, upstream
    from knowledge_tracing.akt import training as actual_training, research_main_execution as main_execution
    from knowledge_tracing import simulator_corpus_reader as corpus_reader
    from knowledge_tracing import edge_confidence_artifact as scores
    static = [(graph,'build_native'), (upstream,'load_upstream'), (graph.ResearchGraphAKTAdapter,'__init__'),
        (graph.ResearchGraphAKTAdapter,'step'), (graph.ResearchGraphNative,'__init__'), (torch.nn.Linear,'__init__'),
        (torch.autograd,'backward'), (torch.autograd,'grad'), (torch.Tensor,'backward'),
        (torch.optim.Adam,'__init__'), (torch.optim.Adam,'step'), (torch.optim.Adam,'load_state_dict'),
        (graph.ResearchGraphNative,'load_state_dict'), (torch.optim.AdamW,'__init__'), (torch.optim.AdamW,'step'),
        (torch.optim.SGD,'__init__'), (torch.optim.SGD,'step'), (torch.nn.utils,'clip_grad_norm_'),
        (torch,'save'), (torch,'load'), (checkpoint,'_torch'), (checkpoint,'_validate_states'),
        (checkpoint.GraphAdamParticipation,'_pre'), (checkpoint.GraphAdamParticipation,'_post'),
        (scores,'load_method24_scores'), (torch.cuda,'is_available'), (torch.cuda,'is_initialized'),
        (actual_training.EarlyStopping,'__init__'),(actual_training.EarlyStopping,'observe'),
        (corpus_reader,'read_public_research_corpus'),(main_execution,'read_public_research_corpus'),
        (torch.Tensor,'cuda'), (torch.nn.Module,'cuda'),
        *((torch.cuda,n) for n in ('init','_lazy_init','set_device','synchronize','manual_seed','manual_seed_all'))]
    patches.capture_many(static)
    def stopper_method(name,original,cap):
        @functools.wraps(original)
        def call(*args,**kwargs):
            need(active_node[0] in packet['stopper_nodeids'],'actual stopping helper only in two exact nodes')
            stopper_counts[name]+=1;need(stopper_counts[name]<=cap,'bounded actual stopping helper '+name)
            return original(*args,**kwargs)
        return call
    patches.patch(actual_training.EarlyStopping,'__init__',stopper_method('constructors',actual_training.EarlyStopping.__init__,4))
    patches.patch(actual_training.EarlyStopping,'observe',stopper_method('observe',actual_training.EarlyStopping.observe,8))
    def deny_corpus(*args,**kwargs):
        corpus_reader_attempts[0]+=1
        return denied('actual public corpus reader body')(*args,**kwargs)
    patches.patch(corpus_reader,'read_public_research_corpus',deny_corpus)
    patches.patch(main_execution,'read_public_research_corpus',deny_corpus)
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
    def checkpoint_torch(*args, **kwargs):
        previous = phase[0]; phase[0] = 'checkpoint_metadata'
        try: return real_checkpoint_torch(*args, **kwargs)
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
        begun = time.perf_counter(); targets.append(dict(reserved=24, returned=None))
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
    import pytest
    from _pytest.junitxml import mangle_test_address
    collected_nodeids=[]
    class Journal:
        def pytest_collection_finish(self,session):
            collected_nodeids.extend(item.nodeid for item in session.items)
            mapped=[]
            for node in collected_nodeids:
                names=mangle_test_address(node);mapped.append('.'.join(names[:-1])+'::'+names[-1])
            need(len(mapped)==len(set(mapped))==18 and sorted(mapped)==sorted(packet['expected_junit_ids'])
                 and collected_nodeids==packet['expected_nodeids'], 'exact fresh physical18 collection before fixture/native bodies')
            need(not any(started.values()),'no counted native work before collection complete')
            write('collection.json',dict(nodeids=collected_nodeids,junit_ids=mapped,native_started=started.copy()))
        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_protocol(self,item,nextitem):
            active_node[0]=item.nodeid
            before=(started.copy(),returned.copy(),stopper_counts.copy())
            try:
                yield
            finally:
                if item.nodeid in packet['stopper_nodeids']:
                    unchanged=started==before[0] and returned==before[1]
                    stopper_entries[item.nodeid]=dict(zero_native_and_serialization_delta=unchanged,
                        constructors=stopper_counts['constructors']-before[2]['constructors'],
                        observe=stopper_counts['observe']-before[2]['observe'])
                    need(unchanged,'stopper metadata cannot consume additional NN/serialization work')
                active_node[0]=None
        def pytest_runtest_logreport(self, report): journal(dict(kind=report.when,nodeid=report.nodeid,outcome=report.outcome))
    with open(OUT/'pytest.log', 'x', encoding='utf-8') as log:
        with redirect_stdout(log), redirect_stderr(log):
            rc = int(pytest.main([*packet['expected_nodeids'],'-q','--noconftest',
                '-o','addopts=','--log-file='+str(OUT/'pytest-file.log'),'-p','no:cacheprovider','--basetemp',str(TMP),'--junitxml',str(OUT/'junit.xml')], plugins=[Journal()]))
    module = sys.modules.get('test_research_graph_checkpoint')
    need(module is not None and Path(module.__file__).resolve() == R/'tests/akt/test_research_graph_checkpoint.py', 'actual native test module')
    native_proof = module.NATIVE_PROOF; write('native-proof.json', native_proof)
    need(stopper_counts==dict(constructors=4,observe=8) and set(stopper_entries)==set(packet['stopper_nodeids'])
         and all(row['zero_native_and_serialization_delta'] for row in stopper_entries.values())
         and corpus_reader_attempts==[0],'actual stopping helper/no new native work/no actual corpus')
    memory()
except BaseException as error:
    original_error = dict(type=type(error).__name__, message=str(error))
finally:
    stop.set()
    if monitor is not None: monitor.join(timeout=.5)
    if job_handle is not None and (monitor is None or not monitor.is_alive()):
        try:
            job_api.close(job_handle)
            job_query_handle_closed=True
        except BaseException as error:original_error=original_error or dict(type=type(error).__name__,message=str(error))
    try: restoration = patches.restore()
    except BaseException as error: original_error = original_error or dict(type=type(error).__name__, message=str(error))
    try:
        if old_threads is not None: torch.set_num_threads(old_threads)
        if old_dtype is not None: need(torch.get_default_dtype() == old_dtype, 'default dtype restored by fixture validation')
        if torch_info is not None:
            torch_info['threads_after'] = torch.get_num_threads()
            torch_info['cuda_initialized_after'] = torch.cuda.is_initialized()
    except BaseException as error: original_error = original_error or dict(type=type(error).__name__, message=str(error))
    for key in list(os.environ):
        if key.startswith('GIT_'): os.environ.pop(key, None)
    os.environ.update(git_before_env)
    tempfile.tempdir=tempdir_before
    for key,value in env_before.items():
        if value is None: os.environ.pop(key,None)
        else: os.environ[key] = value
    try:
        tree = ET.parse(OUT/'junit.xml').getroot()
        counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        cases = list(tree.iter('testcase'))
        need(len(cases) == counts['tests'], 'exact JUnit population')
        actual_ids = [case.get('classname')+'::'+case.get('name') for case in cases]
        need(len(actual_ids) == len(set(actual_ids)) and sorted(actual_ids) == sorted(packet['expected_junit_ids']),
             'same18 physical JUnit identities, no additional or missing cases')
    except BaseException as error: xml_error = dict(type=type(error).__name__,message=str(error))
    runtime_after = {}
    try:
        source_after = {n:sha(R/n) for n in pins}
        runtime_after = {n:sha(Path(n)) for n in packet['runtime_pins']}
        need(actual_git is not None and sha(Path(actual_git)) == packet['local_git_provenance']['sha256'], 'real Git executable unchanged')
        current_metadata(packet,sys.argv[2])
    except BaseException as error: original_error = original_error or dict(type=type(error).__name__,message=str(error))
    accepted = rc == 0 and counts == dict(tests=18,failures=0,errors=0,skipped=0) and started == returned == caps
    accepted = accepted and original_error is None and xml_error is None and not forbidden and not monitor_errors and (monitor is None or not monitor.is_alive()) and job_query_handle_closed
    accepted = accepted and restoration is not None and restoration['accepted'] is True and source_after == pins and sha(PACKET) == sys.argv[1]
    accepted = accepted and runtime_after == packet['runtime_pins'] and cuda_queries['true_results'] == 0
    accepted = accepted and torch_info is not None and torch_info['threads_after'] == old_threads and torch_info['cuda_initialized_after'] is False
    accepted = accepted and len(git_calls) == 20 and len(loaders) == 2 and all(r['original'] and not r['cached'] for r in loaders)
    accepted = accepted and native_proof is not None and native_proof.get('completed_epoch') == dict(epoch=1,targets=48,windows=8,batches=2,optimizer_steps=2)
    accepted = accepted and len(targets) == 4 and sum(r['returned'] or 0 for r in targets) == 96
    accepted = accepted and native_begin is not None and PERF()-native_begin < 100 and elapsed() < 110
    accepted = accepted and stopper_counts==dict(constructors=4,observe=8) and len(stopper_entries)==2 and corpus_reader_attempts==[0]
    result = dict(status='ACCEPTED_CHILD_CHECKPOINT18_PENDING_OUTER' if accepted else 'REJECTED_CHECKPOINT18_KEEP_ALL', counts=counts,
        expected_junit_ids=packet['expected_junit_ids'],
        pytest_exit_code=rc, original_error=original_error, junit_error=xml_error, native_started=started, native_body_returned=returned,
        source_before=pins, source_after=source_after, runtime_before=packet['runtime_pins'], runtime_after=runtime_after,
        allocation_sha256=sys.argv[1], packet_sha256_after=sha(PACKET),
        local_git_calls=git_calls, original_loaders=loaders, cuda_false_queries=cuda_queries, declared_cuda_query_cap=packet['cuda_false_query_cap'],
        target_observations=targets, timings=timings, raw_backward_dispatch=raw_backwards, native_proof=native_proof,
        stopper_counts=stopper_counts,stopper_per_node=stopper_entries,actual_corpus_reader_attempts=corpus_reader_attempts[0],
        current_metadata_receipt_sha256=sys.argv[2],
        timing_scope_vi='real Adam body wrapper vs registered tracker hooks/state-audit/adapter optimizer_seconds; not throughput/cost projection.',
        resources=resources, monitor_errors=monitor_errors, monitor_stopped=monitor is None or not monitor.is_alive(), forbidden_attempts=forbidden,
        actual_collected_nodeids=collected_nodeids if 'collected_nodeids' in globals() else [],
        owned_job_query_handle_closed=job_query_handle_closed,
        method_restoration=restoration, native_os_metadata=metadata, torch_profile=torch_info,
        environment_restored=env_before == {k:os.environ.get(k) for k in envkeys} and tempfile.tempdir==tempdir_before and git_before_env == {k:v for k,v in os.environ.items() if k.startswith('GIT_')},
        owned_run=None if owned_run[0] is None else owned_run[0].relative_to(R).as_posix(),
        elapsed_seconds=elapsed(), native_work_seconds=None if native_begin is None else time.perf_counter()-native_begin,
        scope_vi='Fresh containers in SAME owned process; completeE1 persistence+controlled partial continuation; NOT fresh-OS-process/lifecycle/main/fitted research proof.')
    write('result.json', result)
    if elapsed() >= 110:
        write('postwrite_rejection.json',dict(status='REJECTED_CHILD_POSTWRITE_TIME',elapsed_seconds=elapsed())); accepted = False
    timer.cancel()
raise SystemExit(0 if accepted else 1)
