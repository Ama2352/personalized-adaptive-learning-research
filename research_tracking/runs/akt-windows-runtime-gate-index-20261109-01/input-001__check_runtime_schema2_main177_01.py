"""ROOT-owned worker54s, thực thi nguyên public runtime CLI bằng runpy sau GO."""
import time
START, WALL = time.perf_counter(), time.time()
from pathlib import Path
import hashlib
from importlib.machinery import PathFinder
import json
import os
import platform
import runpy
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP/'runtime-schema2-main177-01'
TARGET = ROOT/'artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json'
GLOBAL = ROOT/'artifacts/akt/preflight/gate2-current.json'
LEGACY = ROOT/'artifacts/akt/preflight/runtime-v2.json'
UPSTREAM = ROOT/'artifacts/akt/dependencies/upstream'
LOCK = ROOT/'requirements-akt.lock.txt'
CLI = ROOT/'scripts/akt/check_runtime.py'
GIT = Path('C:/Program Files/Git/cmd/git.exe')
PACKET = PREP/'runtime_schema2_main177_01_packet.json'
PACKET_SHA = 'e4d97a562f4140bfe7b3dbba8bdefda4746ef93d718b6586fc995ac6a31206a9'


def need(ok, message):
    if not ok: raise ValueError(message)


def elapsed(): return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path, value):
    with safe(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main():
    sys.path.insert(0,str(ROOT/'scripts/research'))
    global safe
    from windows_owned_worker import worker_gate,safe
    owner = worker_gate()
    need(Path(sys.prefix).resolve() == ROOT/'.venv' and sys.platform == 'win32','actual isolated Windows prefix')
    need(sha(PACKET) == PACKET_SHA,'ROOT-reviewed allocation packet')
    packet = json.loads(PACKET.read_bytes())
    pins = packet['source_pins']
    need(not OUT.exists() and not TARGET.exists(),'exclusive native runtime output')
    need(all(sha(safe(ROOT/name)) == value for name,value in pins.items()),'native source/lock/upstream prehash')
    need(not any(name in sys.modules for name in ('torch','numpy')),'fresh native library import')
    expected_env = packet['git_environment']
    need({key:value for key,value in os.environ.items() if key.startswith(('GIT_','GH_'))} == expected_env,
         'exact caller-supplied reviewed Win03 Git process profile')
    actual_git = shutil.which('git')
    need(actual_git and os.path.normcase(os.path.abspath(actual_git)) == os.path.normcase(str(GIT))
         and sha(GIT) == packet['git_executable_sha256'],'actual reviewed Git image')
    for directory in (ROOT,Path(sys.executable).parent,Path(sys._base_executable).parent):
        need(not any((directory/name).exists() for name in ('git.exe','git.com','git.cmd','git.bat')),'shadow Git rejected')
    global_before = safe(GLOBAL).read_bytes()
    legacy_before = safe(LEGACY).read_bytes()
    need(hashlib.sha256(global_before).hexdigest() == packet['global_pointer_sha256']
         and hashlib.sha256(legacy_before).hexdigest() == packet['legacy_runtime_sha256'],'historical metadata identities')
    safe(OUT).mkdir()
    environment = dict(os.environ)
    original_cache = tempfile.tempdir
    runtime_temp = OUT/'runtime-temp'; runtime_temp.mkdir()
    for key in ('TEMP','TMP','TMPDIR'): os.environ[key] = str(runtime_temp)
    tempfile.tempdir = None
    write(OUT/'before.json',dict(source_pins=pins,global_pointer_sha256=packet['global_pointer_sha256'],
        legacy_runtime_sha256=packet['legacy_runtime_sha256'],owner=owner,packet_sha256=PACKET_SHA))
    phase = ['WINDOWS_METADATA']
    commands, forbidden = [], []
    system_cmd = Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_file() and not system_cmd.is_symlink() and not system_cmd.is_junction(),'actual systemcmd')
    fixed = os.path.normcase(os.path.abspath(str(system_cmd)))
    ver_commands = {fixed.casefold()+' /c "ver"','"'+fixed.casefold()+'" /c "ver"'}
    git_suffixes = [('rev-parse','HEAD'),('status','--porcelain','--untracked-files=all'),('remote','get-url','origin')]
    for name in ('akt.py','README.md','LICENSE'):
        git_suffixes.extend([('hash-object',name),('rev-parse','HEAD:'+name)])
    git_suffixes.append(('rev-parse','HEAD^{tree}'))
    expected_git = [subprocess.list2cmdline(['git','-C',str(UPSTREAM),*suffix]) for suffix in git_suffixes]
    git_calls, ver_calls = [], []
    changing_profile = [False]
    def audit(event, values):
        if event == 'sys.setprofile' and not changing_profile[0]:
            forbidden.append(event); raise RuntimeError('profile replacement denied')
        if event == 'subprocess.Popen':
            if (phase[0] == 'NATIVE_CLI' and len(git_calls)<10 and values[0] in (None,'git')
                    and values[1] == expected_git[len(git_calls)]):
                row = dict(raw_executable=values[0],command=values[1],phase=phase[0])
                git_calls.append(row); commands.append(row); return
            if (phase[0] in ('WINDOWS_METADATA','NATIVE_CLI') and len(ver_calls)<3
                    and type(values[0]) is str and type(values[1]) is str
                    and os.path.normcase(os.path.abspath(values[0])) == fixed and values[1].strip().casefold() in ver_commands):
                row = dict(raw_executable=values[0],command=values[1],phase=phase[0])
                ver_calls.append(row); commands.append(row); return
            forbidden.append(event); raise RuntimeError('only original provenance and bounded platform commands')
        if event == 'os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event != 'socket.gethostname':
            forbidden.append(event); raise RuntimeError('network/process denied')
        if event == 'import' and str(values[0]).split('.')[0] in ('sklearn','scipy','duckdb','pandas','pyBKT','modal','boto3'):
            forbidden.append('import:'+str(values[0])); raise RuntimeError('unneeded model/data/cloud import')
        if event in ('open','os.listdir','os.scandir') and values and isinstance(values[0],(str,bytes,os.PathLike)):
            name = os.path.normcase(os.path.abspath(os.fsdecode(values[0])))
            for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl'):
                base = os.path.normcase(str(ROOT/relative))
                if name == base or name.startswith(base+os.sep):
                    forbidden.append('protected_data'); raise RuntimeError('no actual data/model inputs')
    sys.addaudithook(audit)
    try:
        native_windows = platform.uname()._asdict()
    finally:
        phase[0] = 'NO_SUBPROCESS'
    import psutil
    process = psutil.Process(); born = process.create_time()
    resources = dict(samples=0,peak_rss_bytes=0,minimum_available_ram_bytes=None)
    stop = threading.Event()
    def sample():
        need(process.create_time() == born,'actual owned worker identity')
        memory = process.memory_info(); available = int(psutil.virtual_memory().available)
        resources['samples'] += 1
        resources['peak_rss_bytes'] = max(resources['peak_rss_bytes'],memory.rss,getattr(memory,'peak_wset',0))
        prior = resources['minimum_available_ram_bytes']
        resources['minimum_available_ram_bytes'] = available if prior is None else min(prior,available)
        need(resources['peak_rss_bytes'] <= 1024**3 and available >= 2*1024**3,'runtime1GiB/free2GiB bounds')
    def watch():
        while not stop.wait(.1):
            try: sample()
            except BaseException as error:
                write(OUT/'resource-failure.json',dict(error=repr(error),resources=resources)); os._exit(125)
    sample(); monitor = threading.Thread(target=watch,daemon=True); monitor.start()
    timer = threading.Timer(max(.001,54.-elapsed()),lambda:os._exit(124)); timer.daemon=True; timer.start()
    counters = dict(model_constructor=0,forward=0,backward=0,optimizer_constructor=0,optimizer_step=0,
                    teacher=0,solver=0,cuda_execution=0)
    availability, pending = [], {}
    def blocked(category, module, name):
        counters[category] += 1
        write(OUT/'call-guard-failure.json',dict(category=category,module=module,name=name,counters=counters))
        os._exit(126)
    def profile(frame,event,arg):
        module = frame.f_globals.get('__name__',''); name = frame.f_code.co_name
        if module == 'torch.cuda' and name == 'is_available':
            if event == 'call':
                caller = frame.f_back
                filename = Path(caller.f_code.co_filename).resolve()
                origin = 'upstream_module' if filename == UPSTREAM/'akt.py' and caller.f_code.co_name == '<module>' else (
                    'runtime_report' if filename == CLI and caller.f_code.co_name == 'inspect_runtime' else None)
                if origin is None or any(row['origin'] == origin for row in availability):
                    blocked('cuda_execution',module,'unexpected availability callsite')
                row = dict(origin=origin,caller_file=str(filename),caller_line=caller.f_lineno,returned=False)
                pending[id(frame)] = row; availability.append(row)
            elif event == 'return':
                row = pending.pop(id(frame),None)
                if row is None or arg is not False: blocked('cuda_execution',module,'nonfalse/unpaired availability return')
                row.update(returned=True,value=arg)
            return
        if event == 'c_call':
            function_name = getattr(arg,'__name__','')
            function_module = getattr(arg,'__module__','') or ''
            receiver_module = getattr(type(getattr(arg,'__self__',None)),'__module__','')
            if (function_name == 'cuda' and receiver_module.startswith('torch')) or function_module.startswith('torch') and function_name.startswith('_cuda_'):
                blocked('cuda_execution',function_module,function_name)
            return
        if event != 'call': return
        if module.startswith('torch.cuda') and name in ('init','_lazy_init','set_device','synchronize','current_device','device_count','get_device_properties'):
            blocked('cuda_execution',module,name)
        obj = frame.f_locals.get('self')
        neural = obj is not None and any(cls.__module__ == 'torch.nn.modules.module' and cls.__name__ == 'Module' for cls in type(obj).__mro__)
        if name == '__init__' and neural: blocked('model_constructor',module,name)
        if name in ('forward','_call_impl') and neural: blocked('forward',module,name)
        if name in ('backward','_engine_run_backward') and module.startswith('torch'): blocked('backward',module,name)
        if name == '__init__' and module.startswith('torch.optim'): blocked('optimizer_constructor',module,name)
        if name == 'step' and module.startswith('torch.optim'): blocked('optimizer_step',module,name)
        if name in ('fit','partial_fit','fit_predict','_fit_logistic') and module.startswith(('sklearn','pyBKT','knowledge_tracing.edge_confidence')): blocked('solver',module,name)
        if module.startswith(('knowledge_tracing.simulator_collection','knowledge_tracing.simulator_research_collection')) and name.startswith('collect'): blocked('teacher',module,name)
    original_profile, original_thread = sys.getprofile(),threading.getprofile()
    need(original_profile is None and original_thread is None,'cold profiler scope')
    original_argv,original_path = sys.argv[:],sys.path[:]
    original_bytecode = sys.dont_write_bytecode
    package_origins = {}
    for name in ('torch','numpy'):
        spec = PathFinder.find_spec(name,sys.path)
        need(spec is not None and spec.origin and Path(spec.origin).resolve().is_relative_to((ROOT/'.venv').resolve()),
             'no-exec package origin discovery within actual venv')
        package_origins[name] = dict(path=str(Path(spec.origin).resolve()),sha256=sha(Path(spec.origin)))
    errors, report, library = [],None,None
    command = [str(CLI),'--upstream',str(UPSTREAM),'--device','cpu','--lock-file',str(LOCK),'--output',str(TARGET)]
    try:
        changing_profile[0] = True
        sys.setprofile(profile); threading.setprofile(profile); changing_profile[0] = False
        phase[0] = 'NATIVE_CLI'
        sys.argv = command
        runpy.run_path(str(CLI),run_name='__main__')
        phase[0] = 'NO_SUBPROCESS'
        need(sys.getprofile() is profile and threading.getprofile() is profile,'native CLI retained observers')
        report = json.loads(TARGET.read_bytes())
        need(report['runtime_schema_version'] == 2 and report['device'] == 'cpu' and report['cuda_available'] is False
             and report['python_prefix'] == str((ROOT/'.venv').resolve()) and report['project_root'] == str(ROOT.resolve())
             and report['lock_sha256'] == pins['requirements-akt.lock.txt'],'actual native schema2 prefix/root/device/lock')
        need(len(git_calls) == 10 and len(availability) == 2 and not pending
             and all(row['returned'] and row['value'] is False for row in availability),'actual provenance/availability calls')
        import torch,numpy
        need(torch.version.cuda is None and not torch.cuda.is_initialized(),'CPU library and no CUDA initialization')
        library = dict(torch_version=str(torch.__version__),cuda_build=torch.version.cuda,cuda_initialized=torch.cuda.is_initialized())
        need(all(Path(module.__file__).resolve().is_relative_to((ROOT/'.venv').resolve()) for module in (torch,numpy)),
             'actual runtime module origins')
        need(all(str(Path(module.__file__).resolve()) == package_origins[name]['path']
                 and sha(Path(module.__file__)) == package_origins[name]['sha256']
                 for name,module in (('torch',torch),('numpy',numpy))), 'runtime package entry origins/bytes beforeafter')
        need(all(sha(safe(ROOT/name)) == value for name,value in pins.items()),'source/lock/upstream posthash')
        need(GLOBAL.read_bytes() == global_before and LEGACY.read_bytes() == legacy_before,'historical metadata exact after')
    except BaseException as error: errors.append(dict(type=type(error).__name__,message=str(error)))
    finally:
        phase[0] = 'NO_SUBPROCESS'
        changing_profile[0] = True
        sys.setprofile(original_profile); threading.setprofile(original_thread); changing_profile[0] = False
        sys.argv = original_argv; sys.path[:] = original_path
        stop.set(); monitor.join(timeout=.5)
        try: sample()
        except BaseException as error: errors.append(dict(type=type(error).__name__,message=str(error)))
        os.environ.clear(); os.environ.update(environment); tempfile.tempdir = original_cache
        restored = sys.getprofile() is original_profile and threading.getprofile() is original_thread
        accepted = (not errors and not forbidden and not any(counters.values()) and restored
                    and not monitor.is_alive() and dict(os.environ) == environment and tempfile.tempdir is original_cache
                    and sys.dont_write_bytecode == original_bytecode and elapsed()<54)
        write(OUT/'result.json',dict(status='NATIVE_SCHEMA2_RUNTIME_PENDING_OUTER' if accepted else 'REJECTED_NATIVE_RUNTIME',
            accepted=accepted,errors=errors,forbidden=forbidden,counters=counters,availability_queries=availability,
            commands=commands,git_commands=git_calls,platform_commands=ver_calls,native_windows=native_windows,
            owner=owner,report_path=TARGET.relative_to(ROOT).as_posix(),report_sha256=sha(TARGET) if TARGET.exists() else None,
            report=report,cpu_library_observation=library,source_before=pins,source_after={name:sha(ROOT/name) for name in pins},resources=resources,
            profiler_restored=restored,argv_restored=sys.argv==original_argv,path_restored=sys.path==original_path,
            environment_restored=dict(os.environ)==environment,temp_cache_restored=tempfile.tempdir is original_cache,
            bytecode_setting_restored=sys.dont_write_bytecode==original_bytecode,monitor_stopped=not monitor.is_alive(),
            package_entries_before=package_origins,
            global_pointer_unchanged=GLOBAL.read_bytes()==global_before,legacy_runtime_unchanged=LEGACY.read_bytes()==legacy_before,
            packet_sha256=PACKET_SHA,native_command=command,elapsed_seconds=elapsed(),worker_cap_seconds=54))
        if elapsed()>=54: write(OUT/'postwrite-rejection.json',dict(elapsed_seconds=elapsed())); accepted=False
        timer.cancel()
    raise SystemExit(0 if accepted else 1)


if __name__ == '__main__': main()
