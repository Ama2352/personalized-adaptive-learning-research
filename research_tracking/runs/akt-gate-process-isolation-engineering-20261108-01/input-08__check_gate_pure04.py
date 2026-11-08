"""ROOT: đúng 76 fixture cases, không actual Gate/model/corpus; owned Job ngoài."""
from pathlib import Path
from contextlib import redirect_stdout,redirect_stderr
import hashlib,json,os,platform,sys,time
WALL=time.perf_counter;UTC=time.time
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()
os.chdir(R);out=P/'gate_pure04';out.mkdir(exist_ok=False)
names=('scripts/akt/refresh_gate2.py','tests/akt/test_gate2_refresh.py',
       'src/knowledge_tracing/akt/authorization.py','src/knowledge_tracing/akt/config.py',
       'src/knowledge_tracing/akt/provenance.py','src/knowledge_tracing/akt/__init__.py',
       'src/knowledge_tracing/__init__.py','scripts/research/windows_owned_worker.py')
sha=lambda name:hashlib.sha256((R/name).read_bytes()).hexdigest()
before={name:sha(name) for name in names};start=WALL();env_before=dict(os.environ)
(out/'before.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
os.environ.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='',CUDA_VISIBLE_DEVICES='')
attempts=[];protected_attempts=[]
protected=tuple(os.path.normcase(str(R/p)) for p in ('dataset','artifacts/bkt_baseline','venv','.wsl','artifacts/simulator/corpora'))
def audit(event,args):
    if event=='subprocess.Popen':
        attempts.append(event);raise AssertionError('pure Gate fixtures cannot launch subprocesses')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        name=os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        if any(name==base or name.startswith(base+os.sep) for base in protected):
            protected_attempts.append(name);raise AssertionError('real/protected data forbidden in pure Gate tests')
sys.addaudithook(audit)
old=platform._syscmd_ver;oldcache=getattr(platform,'_uname_cache',None)
native_version=tuple(sys.getwindowsversion().platform_version)
platform._syscmd_ver=lambda system='',release='',version='',supported_platforms=():('Windows',str(native_version[0]),'.'.join(map(str,native_version)))
platform._uname_cache=None
sys.path.insert(0,str(R/'src'))
collected=[];reports=[]
def journal(value):
    value['elapsed_seconds']=WALL()-start
    with (out/'case_events.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();os.fsync(f.fileno())
class Journal:
    def pytest_collection_modifyitems(self,session,config,items):
        collected.extend(item.nodeid for item in items)
        if len(collected)!=76 or len(set(collected))!=76:raise ValueError('expected exact76unique cases')
        journal(dict(event='collected',nodeids=collected))
    def pytest_runtest_logstart(self,nodeid,location):journal(dict(event='start',nodeid=nodeid))
    def pytest_runtest_logreport(self,report):
        reports.append(dict(event=report.when,nodeid=report.nodeid,outcome=report.outcome,duration=report.duration))
        journal(reports[-1].copy())
rc=None
try:
    import pytest
    with (out/'pytest.log').open('x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        rc=int(pytest.main(['tests/akt/test_gate2_refresh.py','-q','-p','no:cacheprovider',
                           '--basetemp='+str(R/'artifacts/akt/local-tests/g24p04'),
                           '--junitxml='+str(out/'junit.xml')],plugins=[Journal()]))
finally:
    platform._syscmd_ver=old;platform._uname_cache=oldcache
    os.environ.clear();os.environ.update(env_before)
    after={name:sha(name) for name in names}
    result=dict(pytest_exit_code=rc,elapsed_seconds=WALL()-start,source_before=before,source_after=after,
                source_unchanged=before==after,actual_subprocess_attempts=attempts,protected_data_attempts=protected_attempts,
                heavy_modules_loaded=[name for name in ('torch','numpy','pandas','sklearn','scipy') if name in sys.modules],
                environment_restored=env_before==dict(os.environ),collected_nodeids=collected,
                report_count=len(reports),actual_full_gate=False,actual_model_calls=0,
                scope_vi='76purefixtures, no inchildTimer/globalclock patch. Fresh237sowned Job includes5scleanup, parent240total. Không fullGate/runtime/CUDA acceptance.')
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raise SystemExit(rc)
