"""ROOT: kiểm round-trip calibrator/reference bank bằng stubs; không neural fit."""
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import hashlib, json, os, platform, sys, threading, time

R=Path(__file__).resolve().parents[4]; P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()
os.chdir(R); out=P/'sakt_research_data01'; out.mkdir(exist_ok=False)
names=('src/knowledge_tracing/sakt/research_data.py','src/knowledge_tracing/sakt/__init__.py',
       'src/knowledge_tracing/sakt/training_data.py','tests/sakt/test_research_data.py',
       'src/knowledge_tracing/akt/research_simulator_data.py','src/knowledge_tracing/simulator_corpus_reader.py')
sha=lambda name:hashlib.sha256((R/name).read_bytes()).hexdigest()
before={name:sha(name) for name in names}
(out/'before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
start=time.perf_counter(); timer=threading.Timer(52,lambda:os._exit(124)); timer.daemon=True; timer.start()
keys=('PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS','CUDA_VISIBLE_DEVICES')
env_before={key:os.environ.get(key) for key in keys}
os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='',CUDA_VISIBLE_DEVICES='')
attempted=[]
def audit(event,args):
    if event=='import' and str(args[0]).split('.')[0]=='torch':raise AssertionError('no Torch in SAKT data fixture')
    if event.startswith('socket.') and event!='socket.gethostname':
        raise AssertionError('network forbidden for local metric fixture')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        for rel in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','venv','.wsl'):
            base=os.path.normcase(str(R/rel))
            if path==base or path.startswith(base+os.sep):raise AssertionError('real/protected data forbidden')
    if event=='subprocess.Popen':
        attempted.append(event); raise AssertionError('pure binding checks cannot launch a subprocess')
sys.addaudithook(audit)
old=platform._syscmd_ver; oldcache=getattr(platform,'_uname_cache',None)
native_version=tuple(sys.getwindowsversion().platform_version)
platform._syscmd_ver=lambda system='',release='',version='',supported_platforms=():('Windows',str(native_version[0]),'.'.join(map(str,native_version)))
platform._uname_cache=None
sys.path.insert(0,str(R/'src'))
import psutil
mem_start=psutil.virtual_memory().available
if mem_start<1024**3:raise ValueError('metric fixture requires1GiB available')
rc=None
try:
    import pytest
    with (out/'pytest.log').open('x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        rc=int(pytest.main(['tests/sakt/test_research_data.py','-q','-p','no:cacheprovider',
                           '--basetemp='+str(R/'artifacts/akt/local-tests/skrd01'),
                           '--junitxml='+str(out/'junit.xml')]))
finally:
    timer.cancel(); platform._syscmd_ver=old; platform._uname_cache=oldcache
    for key,value in env_before.items():
        if value is None:os.environ.pop(key,None)
        else:os.environ[key]=value
    after={name:sha(name) for name in names}
    result=dict(pytest_exit_code=rc,elapsed_seconds=time.perf_counter()-start,source_before=before,source_after=after,
                source_unchanged=before==after,actual_subprocess_attempts=attempted,
                heavy_modules_loaded=[name for name in ('torch',) if name in sys.modules],
                environment_restored=env_before=={key:os.environ.get(key) for key in keys},
                model_calls=0,solver_fits=0,available_ram_start=mem_start,available_ram_end=psutil.virtual_memory().available,process_peak_rss_bytes=getattr(psutil.Process().memory_info(),'peak_wset',None),scope_vi='20data fixtures; real public SAKT package, NumPy only, no NN/model/solver/realcorpus.')
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(rc)
