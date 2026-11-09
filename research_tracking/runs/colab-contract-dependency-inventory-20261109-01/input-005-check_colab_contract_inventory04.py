"""ROOT-only pure8 local inventory checks, không ZIP build/export hoặc remote."""
import time
START,WALL=time.perf_counter(),time.time()
from contextlib import redirect_stdout,redirect_stderr
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import sys
import threading
import xml.etree.ElementTree as ET
import zipfile

R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
PACKET=P/'colab_contract_inventory04_allocation.json'
OUT=P/'colab-contract-inventory04'
TMP=R/'artifacts/akt/local-tests/cbd04'
RUNTIME_TEMP=OUT/'runtime-temp'
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate,safe


def need(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def write(name,value):
    with (OUT/name).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


timer=threading.Timer(53,lambda:os._exit(124));timer.daemon=True;timer.start()
owner=worker_gate()
need(len(sys.argv)==2,'exact ROOT packet SHA required')
safe(PACKET);raw=PACKET.read_bytes()
need(len(raw)<=65536 and hashlib.sha256(raw).hexdigest()==sys.argv[1],'reviewed packet bytes')
packet=json.loads(raw)
pins,inputs,runtimes=packet['source_pins'],packet['fixture_input_pins'],packet['runtime_pins']
need(all(sha(safe(R/n))==h for n,h in pins.items()) and all(sha(safe(R/n))==h for n,h in inputs.items())
     and all(sha(Path(n))==h for n,h in runtimes.items()),'preflight source/input/runtime pins')
need(not OUT.exists() and not TMP.exists(),'exclusive output/short basetemp; no overwrite/retry')
safe(OUT).mkdir();safe(TMP);os.chdir(R)
safe(RUNTIME_TEMP).mkdir(exist_ok=False)  # Separate from pytest basetemp deletion domain.
write('reservation.json',dict(kind=packet['kind'],expected_tests=8,source_before=pins,fixture_inputs_before=inputs,
    runtime_before=runtimes,allocation_sha256=sys.argv[1],owner=owner,
    global_source_inventory_stability_claim=False,scope_vi=packet['scope_vi']))
envkeys=('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
    'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS',
    'TEMP','TMP','TMPDIR')
before_env={k:os.environ.get(k) for k in envkeys}
tempfile_module_before=sys.modules.get('tempfile')
tempfile_cache_before=None if tempfile_module_before is None else tempfile_module_before.tempdir
if tempfile_module_before is not None:tempfile_module_before.tempdir=None
runtime_temp_actual=None
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',
    NVIDIA_VISIBLE_DEVICES='void',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='',
    TEMP=str(RUNTIME_TEMP),TMP=str(RUNTIME_TEMP),TMPDIR=str(RUNTIME_TEMP))
phase=['windows_metadata'];commands=[];denied=[];system_cmd=None
blocked={'torch','numpy','pandas','scipy','sklearn','pyBKT','joblib','modal','boto3','knowledge_tracing'}
source_reads=set()
allowed_devnull=[]
blocked_write_details=[]
source_dirs=tuple(R/n for n in ('src/knowledge_tracing','scripts/akt','scripts/research',
                              'tests/akt','tests/shared_kt','tests/gam_kt'))
fixed_files={R/name for name in inputs}


def allow_metadata_devnull(raw_path,mode,flags,*,phase,allowed_count):
    """Exact os.open sink only; never normalize a file path into device authority."""
    harmless=getattr(os,'O_NOINHERIT',0)|getattr(os,'O_CLOEXEC',0)
    return (type(raw_path) is str and raw_path==os.devnull and mode is None
        and type(flags) is int and flags & (os.O_WRONLY|os.O_RDWR)==os.O_RDWR
        and flags & ~(os.O_RDWR|harmless)==0
        and phase=='windows_metadata' and type(allowed_count) is int and 0<=allowed_count<3)


def audit(event,args):
    if event=='import' and str(args[0]).split('.')[0] in blocked:
        denied.append('import:'+str(args[0]));raise RuntimeError('metadata inventory cannot import scientific/domain modules')
    if event=='subprocess.Popen':
        if phase[0]=='windows_metadata':
            fixed=os.path.normcase(os.path.abspath(str(system_cmd)))
            allowed={fixed.casefold()+' /c "ver"','"'+fixed.casefold()+'" /c "ver"'}
            need(system_cmd is not None and len(commands)<3 and type(args[0]) is str and type(args[1]) is str
                 and os.path.normcase(os.path.abspath(args[0]))==fixed and args[1].strip().casefold() in allowed,
                 'only exact bounded native Windows version command')
            commands.append(dict(executable=args[0],command=args[1]));return
        denied.append(event);raise RuntimeError('no subprocess after metadata phase')
    if event=='os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event!='socket.gethostname':
        denied.append(event);raise RuntimeError('no process/network')
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        if event=='open' and allow_metadata_devnull(args[0],args[1],args[2],
                phase=phase[0],allowed_count=len(allowed_devnull)):
            allowed_devnull.append(dict(raw_path=args[0],mode=args[1],flags=args[2],phase=phase[0]))
            return
        path=Path(os.path.abspath(os.fsdecode(args[0])))
        if event=='open' and path.suffix.lower() in ('.zip','.pt','.pth','.ckpt','.safetensors','.parquet'):
            denied.append('archive_checkpoint_or_dataset');raise RuntimeError('no ZIP/checkpoint/Parquet bytes')
        if path==TMP or path.is_relative_to(TMP):
            return  # Manufactured files in owned short pytest directory, never production inputs.
        if event=='open':
            mode=args[1] if len(args)>1 else None
            flags=args[2] if len(args)>2 and type(args[2]) is int else 0
            writing=(type(mode) is str and any(c in mode for c in 'wax+')) or bool(
                flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing and not path.is_relative_to(OUT):
                blocked_write_details.append(dict(raw_path=os.fsdecode(args[0]),raw_path_type=type(args[0]).__name__,
                    mode=mode,flags=flags,phase=phase[0]))
                denied.append('write_outside_owned_outputs');raise RuntimeError('no source/fixture/runtime writes')
        for name in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','venv','.wsl','research_tracking/runs'):
            if path==R/name or path.is_relative_to(R/name):
                denied.append('protected_or_actual_data');raise RuntimeError('no actual/protected data')
        if path==R/'experiments' or path.is_relative_to(R/'experiments'):
            if event!='open' or path not in fixed_files:
                denied.append('training_artifact');raise RuntimeError('only exact3 public experiments configs allowed')
        if path==R/'docs' or path.is_relative_to(R/'docs'):
            if event=='open' and path not in fixed_files:
                denied.append('undeclared_doc');raise RuntimeError('only fixed public contract documents allowed')
        if event=='open':
            if path.is_relative_to(R/'paper1') or path.is_relative_to(R/'paper2'):
                if path not in fixed_files:
                    denied.append('undeclared_paper_file');raise RuntimeError('only fixed public paper source inputs')
            if path.suffix=='.py' and any(path.is_relative_to(base) for base in source_dirs):
                source_reads.add(path.relative_to(R).as_posix())


sys.addaudithook(audit)
original_zip_init=zipfile.ZipFile.__init__
zip_counts=dict(constructor_started=0,read_constructor_returned=0,write_attempts=0)
def observed_zip_init(self,file,mode='r',*args,**kwargs):
    zip_counts['constructor_started']+=1
    if mode in ('w','x','a'):
        zip_counts['write_attempts']+=1;raise RuntimeError('ZIP writer forbidden in local inventory checks')
    result=original_zip_init(self,file,mode,*args,**kwargs)
    zip_counts['read_constructor_returned']+=1
    return result
zipfile.ZipFile.__init__=observed_zip_init
stop=threading.Event();monitor=None;monitor_errors=[]
resources=dict(samples=0,observed_peak_rss_bytes=0,observed_minimum_available_ram_bytes=None)
lock=threading.Lock();metadata=canary=None;rc=counts=None;error=junit_error=None
after={};inputs_after={};runtime_after={}
try:
    need(not blocked.intersection(sys.modules),'fresh scientific/domain-free worker')
    system_cmd=Path(os.environ['SystemRoot'])/'System32/cmd.exe'
    need(system_cmd.is_absolute() and system_cmd.is_file() and not system_cmd.is_symlink()
         and not getattr(system_cmd,'is_junction',lambda:False)(),'actual system cmd')
    try:
        actual=platform.uname()
        need(actual.system=='Windows','actual Windows metadata')
        metadata=dict(system=actual.system,version=actual.version,commands=commands,fixture_replaced=False,inside_owned_job=True)
    finally:phase[0]='inventory_tests_no_subprocess'
    import tempfile
    runtime_temp_actual=tempfile.gettempdir()
    need(Path(runtime_temp_actual)==RUNTIME_TEMP,'stdlib bootstrap temp must be exact fresh owned runtime-temp')
    import psutil
    need(Path(psutil.__file__).resolve()==Path(packet['runtime_origins']['psutil']).resolve(),'actual psutil origin')
    process=psutil.Process()
    def memory():
        with lock:
            info=process.memory_info();peak=max(int(info.rss),int(info.peak_wset));available=int(psutil.virtual_memory().available)
            resources['samples']+=1;resources['observed_peak_rss_bytes']=max(resources['observed_peak_rss_bytes'],peak)
            previous=resources['observed_minimum_available_ram_bytes']
            resources['observed_minimum_available_ram_bytes']=available if previous is None else min(previous,available)
            need(peak<=1024**3 and available>=2*1024**3,'observed pure RAM bounds')
    memory()
    def watch():
        while not stop.wait(.1):
            try:memory()
            except BaseException as failure:
                monitor_errors.append(type(failure).__name__+': '+str(failure))
                try:write('resource-failure.json',dict(resources=resources,error=monitor_errors[-1]))
                finally:os._exit(125)
    monitor=threading.Thread(target=watch,daemon=True);monitor.start()
    definitions=runpy.run_path(str(R/'scripts/akt/build_colab_bundle.py'))  # Definitions only; never main/collect here.
    need(definitions['ROOT']==R and tuple(definitions['RESEARCH_CONTRACT_FILES'])==tuple(packet['fixed_contract_paths']),
         'real builder root/fixed allowlist')
    canary=dict(builder_definition_sha256=sha(R/'scripts/akt/build_colab_bundle.py'),scientific_modules_present=[],
        main_invoked=False,bundle_contents_invoked_by_canary=False,zip_counts_before_tests=zip_counts.copy())
    write('cold-canary.json',canary)
    sys.path.insert(0,str(R))
    import pytest
    need(Path(pytest.__file__).resolve()==Path(packet['runtime_origins']['pytest']).resolve(),'actual pytest origin')
    argv=['tests/akt/test_colab_bundle.py','-q','--noconftest','-p','no:cacheprovider',
          '--basetemp',str(TMP),'--junitxml',str(OUT/'junit.xml'),'--log-file='+str(OUT/'pytest-file.log')]
    class Journal:
        def pytest_runtest_logreport(self,report):
            with (OUT/'case_events.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,seconds=elapsed()))+'\n')
                stream.flush();os.fsync(stream.fileno())
    with (OUT/'pytest.log').open('x',encoding='utf-8') as log:
        with redirect_stdout(log),redirect_stderr(log):rc=int(pytest.main(argv,plugins=[Journal()]))
    memory()
except BaseException as original:error=dict(type=type(original).__name__,message=str(original))
finally:
    stop.set()
    if monitor is not None:monitor.join(timeout=min(1.,max(.001,53.-elapsed())))
    monitor_stopped=monitor is None or not monitor.is_alive()
    try:
        tree=ET.parse(OUT/'junit.xml').getroot()
        counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
        need(len(list(tree.iter('testcase')))==counts['tests'],'actual JUnit case count')
    except BaseException as original:junit_error=dict(type=type(original).__name__,message=str(original))
    try:
        after={n:sha(safe(R/n)) for n in pins};inputs_after={n:sha(safe(R/n)) for n in inputs};runtime_after={n:sha(Path(n)) for n in runtimes}
        need(after==pins and inputs_after==inputs and runtime_after==runtimes and sha(PACKET)==sys.argv[1],
             'selected source/input/runtime/packet drift')
    except BaseException as original:
        if error is None:error=dict(type=type(original).__name__,message=str(original))
    observer_intact=zipfile.ZipFile.__init__ is observed_zip_init
    zipfile.ZipFile.__init__=original_zip_init
    restored=zipfile.ZipFile.__init__ is original_zip_init
    tempfile_module_after=sys.modules.get('tempfile')
    if tempfile_module_after is not None:tempfile_module_after.tempdir=tempfile_cache_before
    tempfile_cache_restored=(tempfile_module_after is None and tempfile_module_before is None) or (
        tempfile_module_after is not None and tempfile_module_after.tempdir==tempfile_cache_before
        and (tempfile_module_before is None or tempfile_module_after is tempfile_module_before))
    for key,value in before_env.items():
        if value is None:os.environ.pop(key,None)
        else:os.environ[key]=value
    present=sorted(n for n in sys.modules if n.split('.')[0] in blocked)
    accepted=error is None and junit_error is None and not denied and not present and not monitor_errors and monitor_stopped
    accepted=accepted and observer_intact and restored and tempfile_cache_restored and zip_counts['write_attempts']==0 and rc==0
    accepted=accepted and counts==dict(tests=8,failures=0,errors=0,skipped=0) and elapsed()<53
    result=dict(status='ACCEPTED_8_LOCAL_INVENTORY_CASES_PENDING_OUTER' if accepted else 'REJECTED_KEEP_ALL',
        counts=counts,pytest_exit_code=rc,original_error=error,junit_error=junit_error,source_before=pins,source_after=after,
        fixture_inputs_before=inputs,fixture_inputs_after=inputs_after,runtime_before=runtimes,runtime_after=runtime_after,
        allocation_sha256=sys.argv[1],native_windows_metadata=metadata,metadata_phase_closed=phase[0]=='inventory_tests_no_subprocess',
        forbidden_attempts=denied,scientific_modules_present=present,zip_observer_counts=zip_counts,
        zip_observer_intact_before_restore=observer_intact,zip_method_restored=restored,
        allowed_metadata_devnull_events=allowed_devnull,blocked_write_details=blocked_write_details,
        runtime_temp=dict(path=str(RUNTIME_TEMP),actual_gettempdir=runtime_temp_actual,
            separate_from_pytest_basetemp=RUNTIME_TEMP!=TMP,tempfile_cache_was_loaded=tempfile_module_before is not None,
            cache_before=None if tempfile_cache_before is None else os.fsdecode(tempfile_cache_before),
            cache_before_type=type(tempfile_cache_before).__name__,cache_restored=tempfile_cache_restored),
        cold_canary=canary,resources=resources,monitor_errors=monitor_errors,monitor_stopped=monitor_stopped,
        environment_restored=all(os.environ.get(k)==v for k,v in before_env.items()),elapsed_seconds=elapsed(),
        observed_source_read_paths=sorted(source_reads),global_source_inventory_stability_claim=False,
        scope_vi='Local inventory in memory+synthetic tmpFS; selected dependencies stable, incidental WIP source bytes not a global freeze. No ZIP writer/build/export/remote/model/Gate authority.')
    write('result.json',result)
    if elapsed()>=53:write('postwrite_rejection.json',dict(status='REJECTED_POSTWRITE_TIME',seconds=elapsed()));accepted=False
    timer.cancel()
print(json.dumps(dict(status=result['status'] if accepted else 'REJECTED_KEEP_ALL',counts=counts,seconds=elapsed())))
raise SystemExit(0 if accepted else 1)
