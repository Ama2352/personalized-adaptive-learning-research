"""ROOT: đúng43cases dự kiến, stubs; không fit/runtime/real corpus."""
from pathlib import Path
import sys,os,json,hashlib,time,platform,threading
from contextlib import redirect_stdout,redirect_stderr
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()
os.chdir(R)
out=P/'method24-pure03';out.mkdir(exist_ok=False)
files=[P/name for name in ('method24_worker01.py','run_method24_native01.py','method24_config01.json',
    'method24_runtime_profile01.json','test_method24_native01.py')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={p.name:sha(p) for p in files}
(out/'source_before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
start=time.perf_counter();timer=threading.Timer(140,lambda:os._exit(124));timer.daemon=True;timer.start()
envkeys=('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES',
    'PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS')
env_before={k:os.environ.get(k) for k in envkeys}
os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='',CUDA_VISIBLE_DEVICES='')
attempted=[]
def audit(event,args):
    if event=='subprocess.Popen':
        attempted.append(event);raise AssertionError('pure Method24 checks cannot start subprocess')
sys.addaudithook(audit)
old=platform._syscmd_ver;oldcache=getattr(platform,'_uname_cache',None)
native_version=tuple(sys.getwindowsversion().platform_version)
platform._syscmd_ver=lambda system='',release='',version='',supported_platforms=():('Windows',str(native_version[0]),'.'.join(map(str,native_version)))
platform._uname_cache=None
def journal(event):
    event['elapsed_seconds']=time.perf_counter()-start
    with (out/'case_events.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(event,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
class Journal:
    def pytest_runtest_logstart(self,nodeid,location):journal(dict(event='start',nodeid=nodeid))
    def pytest_runtest_logreport(self,report):journal(dict(event=report.when,nodeid=report.nodeid,outcome=report.outcome,duration=report.duration))
rc=None
try:
    import pytest
    with (out/'pytest.log').open('x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        rc=int(pytest.main([str(P/'test_method24_native01.py'),'-q','-p','no:cacheprovider',
            '--basetemp='+str(R/'artifacts/akt/local-tests/m24p03'),
            '--junitxml='+str(out/'junit.xml')],plugins=[Journal()]))
finally:
    timer.cancel();platform._syscmd_ver=old;platform._uname_cache=oldcache
    for key,value in env_before.items():
        if value is None:os.environ.pop(key,None)
        else:os.environ[key]=value
    after={p.name:sha(p) for p in files}
    result=dict(pytest_exit_code=rc,elapsed_seconds=time.perf_counter()-start,source_before=before,source_after=after,
        source_unchanged=before==after,actual_subprocess_attempts=attempted,
        heavy_modules_loaded=[name for name in ('numpy','pandas','sklearn','scipy','torch') if name in sys.modules],
        environment_restored=env_before=={k:os.environ.get(k) for k in envkeys},
        test_only_windows_metadata_native_version=native_version,
        scope_vi='Pure tmpFS/stubs, không actualsolver/corpus/NN/Gate/runtimeacceptance; Timer cooperative, outer ownedJob bắtbuộc.')
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
assert before==after and not attempted and not result['heavy_modules_loaded'] and result['environment_restored']
raise SystemExit(rc)
