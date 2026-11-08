"""ROOT:60 kiểm dữ liệu giả, không actual corpus/solver/NN."""
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import hashlib, importlib.util, json, os, sys, threading, time
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
worker_gate()
os.chdir(R)
start=time.perf_counter();timer=threading.Timer(140,lambda:os._exit(124));timer.daemon=True;timer.start()
out=P/'edge-artifact-cross-ready02';out.mkdir(exist_ok=False)
allocation=json.loads((P/'edge_artifact_cross_ready02_allocation.json').read_bytes())
pins=allocation['source_pins'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(R/n)==h for n,h in pins.items())
def write(name,v):
    with open(out/name,'x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
write('source_before.json',pins)
envkeys=('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES',
         'NVIDIA_VISIBLE_DEVICES','PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTEST_ADDOPTS','PYTEST_PLUGINS')
oldenv={k:os.environ.get(k) for k in envkeys}
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',
                  NVIDIA_VISIBLE_DEVICES='void',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTEST_PLUGINS='')
spec=importlib.util.spec_from_file_location('metadata_only_reviewed_worker',P/'method24_worker01.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
guard=w.Guard(w._memory_api(),w.CAPS,time.perf_counter()+140,time.time()+140)
guard.left()
metadata=w.native_windows_metadata(guard)
forbidden=[]
def audit(event,args):
    if event=='subprocess.Popen' or event=='os.system' or event.startswith('os.spawn') or event.startswith('socket.') and event!='socket.gethostname':
        forbidden.append(event);raise RuntimeError('data-only checks prohibit process/network')
    if event=='import' and str(args[0]).split('.')[0] in ('torch','sklearn','scipy','pandas','joblib','modal','boto3'):
        forbidden.append('import:'+str(args[0]));raise RuntimeError('data-only checks prohibit model/solver imports')
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        name=os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        for relative in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','experiments','venv','.wsl','research_tracking/runs'):
            base=os.path.normcase(str(R/relative))
            if name==base or name.startswith(base+os.sep):
                forbidden.append('actual/protected_data');raise RuntimeError('fixtures may not open actual data/evidence')
sys.addaudithook(audit)
stop=threading.Event();monitor_errors=[]
def monitor():
    while not stop.wait(.1):
        try:guard.left()
        except BaseException as e:
            monitor_errors.append(str(e));write('resource-failure.json',dict(error=str(e),models=0,solver_fits=0));os._exit(125)
thread=threading.Thread(target=monitor,daemon=True);thread.start()
def journal(v):
    v['elapsed_seconds']=time.perf_counter()-start
    # built-in open: fixtures deliberately patch Path.open for reader boundaries.
    with open(out/'case_events.jsonl','a',encoding='utf-8') as f:f.write(json.dumps(v)+'\n');f.flush();os.fsync(f.fileno())
class Journal:
    def pytest_runtest_logstart(self,nodeid,location):journal(dict(event='start',nodeid=nodeid))
    def pytest_runtest_logreport(self,report):journal(dict(event=report.when,nodeid=report.nodeid,outcome=report.outcome))
rc=None;error=None
try:
    import pytest
    with open(out/'pytest.log','x',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
        rc=int(pytest.main(['tests/shared_kt/test_edge_confidence_artifact.py','tests/shared_kt/test_rq1_cross_ready.py',
            '-q','-p','no:cacheprovider','--basetemp='+str(R/'artifacts/akt/local-tests/eacr02'),
            '--junitxml='+str(out/'junit.xml')],plugins=[Journal()]))
except BaseException as e:error=dict(type=type(e).__name__,message=str(e))
finally:
    stop.set();thread.join(timeout=.5);timer.cancel()
    for k,v in oldenv.items():
        if v is None:os.environ.pop(k,None)
        else:os.environ[k]=v
    after={n:sha(R/n) for n in pins}
    guard.left()
    try:
        tree=ET.parse(out/'junit.xml').getroot()
        counts={k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    except BaseException as e:counts=None;error=error or dict(type=type(e).__name__,message=str(e))
    result=dict(pytest_exit_code=rc,counts=counts,error=error,source_before=pins,source_after=after,
        source_unchanged=after==pins,environment_restored=oldenv=={k:os.environ.get(k) for k in envkeys},
        native_os_metadata=metadata,forbidden_attempts=forbidden,monitor_stopped=not thread.is_alive(),
        monitor_errors=monitor_errors,resources=guard.summary(),elapsed_seconds=time.perf_counter()-start,
        unexpected_heavy_modules=[n for n in ('torch','sklearn','scipy','pandas','joblib','modal') if n in sys.modules],
        model_calls=0,solver_fits=0,actual_corpus_reads=0,
        scope_vi='60manufacturedcases; NumPycho sharedgraphtypes, không actualloader/cachedanalysis/corpus/model. ActualWindowsmetadata riêng, fit-phasePopen bị cấm.')
    write('result.json',result)
ok=rc==0 and counts==dict(tests=60,failures=0,errors=0,skipped=0) and error is None
ok=ok and after==pins and result['environment_restored'] and not forbidden and not result['unexpected_heavy_modules']
ok=ok and result['monitor_stopped'] and not monitor_errors and metadata['phase_closed'] and metadata['outside_phase_popen_attempts']==0
print(json.dumps(dict(status='PURE_CHILD_COMPLETE_PENDING_OUTER' if ok else 'REJECTED_PURE_CHILD',counts=counts)))
raise SystemExit(0 if ok else 1)
