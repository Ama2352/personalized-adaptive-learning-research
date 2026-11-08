"""ROOT: đúng2 public solver fits trên16hàng tự dựng; không corpus/confidence."""
import time
START=time.perf_counter();WALL=time.time()
from pathlib import Path
import hashlib,importlib.util,json,os,sys,threading,warnings
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import worker_gate
owner=worker_gate()
out=P/'method24-solver-smoke01';out.mkdir(exist_ok=False)
pins={'method24_worker01.py':'4afbf824b845f8d518ea4eab43978df01672580ce4d77fa61597a8696f0e0705',
      'method24_runtime_profile01.json':'c008d6a734c53152b33ad4b6a99a3657528c33c71606dd265dc4b61ef8387bc8'}
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def write(name,value):
    with (out/name).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
for name,h in pins.items():need(sha(P/name)==h,'reviewed source/profile drift')
before={str((P/name).relative_to(R).as_posix()):h for name,h in pins.items()}
before['src/knowledge_tracing/edge_confidence.py']='a91aec2558d1fa63c18212aadda265e2dd0e01f369756447022b21bacfc235e9'
need(sha(R/'src/knowledge_tracing/edge_confidence.py')==before['src/knowledge_tracing/edge_confidence.py'],'method source drift')
before[Path(__file__).relative_to(R).as_posix()]=sha(Path(__file__))
write('reservation.json',dict(kind='MANUFACTURED_PUBLIC_SOLVER_ABI_ONLY',fit_slots=2,actual_fit_attempts=None,
    rows_per_fit=16,feature_counts=[4,6],active_seconds=25,outer_seconds=30,max_rss_bytes=512*1024**2,
    minimum_available_ram_bytes=1024**3,no_corpus=True,confidence_or_graph_outputs=False,sources=before))
attempts=[];forbidden=[]
def audit(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.') and event!='socket.gethostname':
        forbidden.append(event);raise RuntimeError('process/network forbidden in solver smoke')
    if event=='import' and str(args[0]).split('.')[0] in ('torch','knowledge_tracing'):
        forbidden.append('import:'+str(args[0]));raise RuntimeError('NN/domain imports forbidden in ABI smoke')
    if event in ('open','os.listdir','os.scandir') and args and isinstance(args[0],(str,bytes,os.PathLike)):
        path=os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        for rel in ('dataset','artifacts/bkt_baseline','artifacts/simulator/corpora','venv','.wsl'):
            base=os.path.normcase(str(R/rel))
            if path==base or path.startswith(base+os.sep):
                forbidden.append('protected_data');raise RuntimeError('no corpus or protected data in ABI smoke')
sys.addaudithook(audit)
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
spec=importlib.util.spec_from_file_location('reviewed_method24_runtime_for_smoke',P/'method24_worker01.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
profile=json.loads((P/'method24_runtime_profile01.json').read_bytes())
selected_sources=module.validate_profile(profile)
import psutil
process=psutil.Process()
def memory():
    info=process.memory_info();return dict(process_rss_bytes=int(info.rss),process_peak_rss_bytes=int(info.peak_wset),system_available_ram_bytes=int(psutil.virtual_memory().available))
caps=dict(max_rss_bytes=512*1024**2,min_available_ram_bytes=1024**3,poll_seconds=.1)
guard=module.Guard(memory,caps,START+25,WALL+25);lock=threading.Lock()
def check():
    with lock:return guard.left()
check();stop=threading.Event()
def watch():
    while not stop.wait(.1):
        try:check()
        except Exception as e:
            try:write('resource-failure.json',dict(status='REJECTED_RESOURCE',error=str(e),fit_slots=2,actual_fit_attempts=len(attempts),resources=guard.summary()))
            finally:os._exit(125)
thread=threading.Thread(target=watch,daemon=True);thread.start()
fit_results=[]
try:
    imported_at=time.perf_counter();origins=module.runtime_origins(profile,guard,import_required=True)
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.exceptions import ConvergenceWarning
    from threadpoolctl import threadpool_info,threadpool_limits
    import_seconds=time.perf_counter()-imported_at
    patterns=((.2,.1,.4,.2),(.8,.7,.6,.8),(.4,.3,.5,.4),(.6,.6,.5,.7))
    labels_by_pattern=((0,0,0,1),(1,1,1,0),(0,1,0,1),(1,0,0,1))
    row_ids=tuple('synthetic-abi-'+str(i) for i in range(16))
    x=tuple(patterns[i%4] for i in range(16))
    y=tuple(labels_by_pattern[i%4][i//4] for i in range(16))
    xa=tuple((*row,.1+.1*(i%3),.2+.15*(i%4)) for i,row in enumerate(x))
    need(set(y)=={0,1} and len(set(row_ids))==16,'manufactured population')
    pools=[]
    with threadpool_limits(limits=1):
        pools=threadpool_info();need(all(t['num_threads']==1 for t in pools),'thread1 mismatch')
        for label,features in (('baseline',x),('augmented',xa)):
            check()
            model=LogisticRegression(C=1.,l1_ratio=0.,solver='lbfgs',tol=1e-6,max_iter=200,
                fit_intercept=True,class_weight=None,random_state=42,warm_start=False,verbose=0)
            attempts.append(label)
            with (out/'fit-attempts.jsonl').open('a',encoding='utf-8') as ledger:
                ledger.write(json.dumps(dict(attempt=len(attempts),label=label,rows=16))+'\n');ledger.flush();os.fsync(ledger.fileno())
            begun=time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always');model.fit(np.asarray(features,dtype=np.float64),np.asarray(y,dtype=np.int64))
            fit_seconds=time.perf_counter()-begun;check()
            predicted_at=time.perf_counter();prob=model.predict_proba(np.asarray(features,dtype=np.float64));predict_seconds=time.perf_counter()-predicted_at
            need(not any(issubclass(w.category,ConvergenceWarning) for w in caught),'convergence warning')
            need(list(model.classes_)==[0,1] and 0<int(model.n_iter_[0])<200,'classes/iterations')
            need(model.coef_.shape==(1,len(features[0])) and np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(),'parameter finiteness')
            need(prob.shape==(16,2) and np.isfinite(prob).all() and ((prob>=0)&(prob<=1)).all()
                 and np.allclose(prob.sum(axis=1),1.,rtol=0,atol=1e-12),'probability population')
            fit_results.append(dict(label=label,rows=16,features=len(features[0]),classes=model.classes_.tolist(),
                iterations=int(model.n_iter_[0]),warning_types=[type(w.message).__name__ for w in caught],
                coefficients=model.coef_[0].tolist(),intercept=float(model.intercept_[0]),probabilities=prob.tolist(),
                fit_seconds=fit_seconds,predict_seconds=predict_seconds))
            del model,prob;check()
    need(attempts==['baseline','augmented'] and len(fit_results)==2,'exact2public fits')
    for name,h in before.items():need(sha(R/name)==h,'source changed after fits')
    need(module.validate_profile(profile)==selected_sources,'selected runtime files changed')
    need(module.runtime_origins(profile,guard,import_required=False)==origins,'actual module origins changed')
    need(not forbidden and 'torch' not in sys.modules and 'knowledge_tracing' not in sys.modules,'forbidden access/import')
    check();stop.set();thread.join(timeout=.5);need(not thread.is_alive(),'monitor cleanup')
    write('result.json',dict(status='TWO_PUBLIC_SOLVER_FITS_PENDING_OUTER_ACCEPTANCE',fit_results=fit_results,
        row_ids=row_ids,labels=y,import_seconds=import_seconds,actual_origins=origins,threadpools_during_fit=pools,
        resources=guard.summary(),source_before=before,source_after={name:sha(R/name) for name in before},
        profile_selected_sources=selected_sources,fit_attempts=2,fit_completions=2,actual_corpus_reads=0,
        actual_neural_calls=0,forbidden_attempts=forbidden,monitor_thread_stopped=True,
        elapsed_seconds=max(time.perf_counter()-START,time.time()-WALL),active_cap_seconds=25,
        scope_vi='16hàng tự dựng,2publicfits; khôngconfidence/graph/OOF research hoặc forecast2352fits.'))
    check()
except BaseException as error:
    stop.set();thread.join(timeout=.5)
    write('failure.json',dict(status='REJECTED_PUBLIC_SOLVER_SMOKE',error_type=type(error).__name__,error=str(error),fit_attempts=len(attempts),fit_completions=len(fit_results),resources=guard.summary()))
    raise
