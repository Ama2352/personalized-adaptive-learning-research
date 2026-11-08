"""Operational benchmark SOURCE ONLY: manufactured state, no native model/data.

Separate<=5s allocation; the prior native60s batch stays closed at56.3709122.
Tuple views here cover fabricated types only, not certified native NumPy states.
"""
import time
START,WALL=time.perf_counter(),time.time()
import argparse
from collections import Counter,deque
import copy
from dataclasses import dataclass,field,is_dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import traceback

ROOT=Path(__file__).resolve().parents[4]
PREP=Path(__file__).resolve().parent
PLAN=PREP/'mastery_observer_microbenchmark_plan01.json'
OUT=PREP/'mastery-observer-microbenchmark-attempt01'
HELPER=ROOT/'scripts/research/windows_owned_worker.py'
MEMORY_LENGTH=38  # Exact frozen loader28nodes+3chapters+7; np.float32 source, not64.


def need(ok,message):
    if not ok:raise ValueError(message)


def elapsed():return max(time.perf_counter()-START,time.time()-WALL)


def sha(path):
    need(path.is_file() and not path.is_symlink() and not getattr(path,'is_junction',lambda:False)()
         and path.stat().st_size<=131072,'small physical operational source/receipt')
    with path.open('rb') as f:raw=f.read(131073)
    need(len(raw)<=131072,'bounded payload')
    return hashlib.sha256(raw).hexdigest()


def write(path,value):
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


@dataclass
class ManufacturedArray:
    raw:bytes
    shape:tuple=(MEMORY_LENGTH,)
    dtype:str='float32'


@dataclass
class ManufacturedTimestamp:
    timestamp_iso:str
    timestamp_ns:int


@dataclass
class ManufacturedMemoryState:
    theta:float
    memory:ManufacturedArray
    pi_task:float=1.
    pi_time:float=.05
    attempts:int=0
    last_timestamp:ManufacturedTimestamp|None=None
    recent_outcomes:deque=field(default_factory=lambda:deque(maxlen=8))
    ever_mastered:bool=False
    currently_mastered:bool=False
    times_forgotten:int=0


def manufacture():
    """Deterministic bytes/scalars only; not policy, fitted state or native array."""
    states={}
    for i in range(28):
        raw=struct.pack('<38f',*((i+j)/128 for j in range(38)))
        need(len(raw)==152,'38float32bytes')
        states[f'C{i:02d}']=ManufacturedMemoryState(theta=1100.+i/8,memory=ManufacturedArray(raw),
            pi_task=.2+(i%10)/100,pi_time=.05,attempts=i%9,
            last_timestamp=None if i%2 else ManufacturedTimestamp('2026-01-01T00:00:00+00:00',1767225600000000000),
            recent_outcomes=deque([j%2 for j in range(i%9)],maxlen=8),ever_mastered=bool(i%2),
            currently_mastered=bool(i%3==0),times_forgotten=i%4)
    return dict(use_graph_context=True,name='Graph-GAM-KT',states=states,
        r_pos=.60,r_neg=1.,q_task=.04,q_time=.04,time_decay_rate=.02,
        theta_lr=80.,memory_lr=1.,item_weight=.80,graph_weight=.35,
        selection_counts=Counter({f'C{i:02d}':i%7 for i in range(28)}),
        question_counts=Counter({f'Q{i:02d}':i%4 for i in range(84)}),
        current_chapter='CH1',recent_concepts=deque(['C01','C02','C03'],maxlen=3))


def legacy_state_data(v):
    """Same JSONshape pattern; ManufacturedArray/Timestamp stand in for np/pd."""
    if type(v) is ManufacturedArray:
        return dict(array_shape=list(v.shape),dtype=v.dtype,bytes_sha256=hashlib.sha256(v.raw).hexdigest())
    if type(v) is ManufacturedTimestamp:return dict(timestamp_iso=v.timestamp_iso,timestamp_ns=v.timestamp_ns)
    if type(v) is float:
        need(math.isfinite(v),'finite manufactured floats');return {'float_hex':v.hex()}
    if isinstance(v,dict):return {str(k):legacy_state_data(x) for k,x in v.items()}
    if isinstance(v,deque):return dict(deque_maxlen=v.maxlen,items=[legacy_state_data(x) for x in v])
    if isinstance(v,(list,tuple)):return [legacy_state_data(x) for x in v]
    if is_dataclass(v):return legacy_state_data(vars(v))
    if v is None or type(v) in (str,int,bool):return v
    raise TypeError('unknown manufactured field')


def legacy_fingerprint(v):
    raw=json.dumps(legacy_state_data(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def immutable_view(v):
    """All fabricated fields, floatbits and fullmemorybytes; no JSON or SHA."""
    if type(v) is ManufacturedArray:return ('array',v.shape,v.dtype,v.raw)
    if type(v) is ManufacturedTimestamp:return ('timestamp',v.timestamp_iso,v.timestamp_ns)
    if type(v) is float:
        need(math.isfinite(v),'finite manufactured floats');return ('floatbits',struct.pack('>d',v))
    if isinstance(v,dict):
        need(all(type(k) is str for k in v),'string-key manufactured schema')
        return ('dict',tuple((k,immutable_view(v[k])) for k in sorted(v)))
    if isinstance(v,deque):return ('deque',v.maxlen,tuple(immutable_view(x) for x in v))
    if isinstance(v,(list,tuple)):return ('sequence',tuple(immutable_view(x) for x in v))
    if is_dataclass(v):return immutable_view(vars(v))
    if v is None:return ('none',)
    if type(v) in (str,int,bool):return (type(v).__name__,v)
    raise TypeError('unknown manufactured field')


def fixtures(check):
    original=manufacture();clone=copy.deepcopy(original);old=legacy_fingerprint(original);view=immutable_view(original)
    need(legacy_fingerprint(clone)==old and immutable_view(clone)==view,'equal manufactured states agree')
    need(legacy_fingerprint(0.)!=legacy_fingerprint(-0.) and immutable_view(0.)!=immutable_view(-0.),'signedzero floatbits preserved')
    cases=[]
    def changed(label,change):
        check();value=copy.deepcopy(original);change(value)
        a,b=legacy_fingerprint(value)!=old,immutable_view(value)!=view
        need(a and b,'singlefield mutation detection '+label)
        cases.append(dict(field=label,legacy_detected=a,view_detected=b))
    for name,value in (('theta',1201.),('pi_task',.4),('pi_time',.07),('attempts',99),
        ('last_timestamp',None),('recent_outcomes',deque([1],maxlen=8)),('ever_mastered',True),
        ('currently_mastered',False),('times_forgotten',7)):
        changed('MemoryState.'+name,lambda p,n=name,v=value:setattr(p['states']['C00'],n,v))
    changed('memory.raw',lambda p:setattr(p['states']['C00'].memory,'raw',b'\x01'+p['states']['C00'].memory.raw[1:]))
    changed('memory.shape',lambda p:setattr(p['states']['C00'].memory,'shape',(19,2)))
    changed('memory.dtype',lambda p:setattr(p['states']['C00'].memory,'dtype','>f4'))
    changed('selector.selection_counts',lambda p:p['selection_counts'].__setitem__('C00',99))
    changed('selector.question_counts',lambda p:p['question_counts'].__setitem__('Q00',99))
    changed('selector.current_chapter',lambda p:p.__setitem__('current_chapter','CH2'))
    changed('selector.recent_concepts',lambda p:p['recent_concepts'].append('C04'))
    changed('parameter.graph_weight',lambda p:p.__setitem__('graph_weight',.36))
    changed('new_unmapped_field',lambda p:setattr(p['states']['C00'],'new_field',1))
    changed('deque.maxlen',lambda p:setattr(p['states']['C00'],'recent_outcomes',deque([],maxlen=7)))
    check();return original,clone,dict(equal_state=True,mutation_cases=cases,mutation_count=len(cases),
        legacy_fixture_sha256=old,all_fabricated_fields_used=True,native_schema_coverage_claimed=False)


def representation_trial(original,clone,fn,count,check):
    start=time.perf_counter();checks=0
    for i in range(count):
        check();a,b,c,d=fn(original),fn(clone),fn(clone),fn(original)
        need(a==b==c==d,'same four readonly representations')
        checks+=1
    seconds=time.perf_counter()-start;check()
    return dict(seconds=seconds,iterations=count,full_state_representation_calls=4*count,equalities=checks)


def dummy_leaf(x):return x+1


def dummy_branch(x,invoke):return invoke('leaf',dummy_leaf,x)+invoke('leaf',dummy_leaf,x+1)


def ledger_trial(count,global_profile,check):
    before=sys.getprofile();need(before is None,'STOP preexisting profiler')
    calls=Counter();returns=Counter();callback_events=0
    codes={dummy_leaf.__code__:'leaf',dummy_branch.__code__:'branch'}
    def callback(frame,event,arg):
        nonlocal callback_events
        callback_events+=1
        # Reproduce broad source02 routing, not an optimized/new native observer.
        if event in ('call','return'):
            name=codes.get(frame.f_code)
            if name:(calls if event=='call' else returns)[name]+=1
            if event=='call' and str(frame.f_globals.get('__name__','')).startswith(('numpy.random','random')):
                raise RuntimeError('unexpected RNG namespace')
        elif event=='c_call':
            if str(getattr(arg,'__module__','')).startswith(('numpy.random','_random')):raise RuntimeError('RNG')
    def invoke(name,fn,*args):
        if not global_profile:calls[name]+=1
        value=fn(*args)
        if not global_profile:returns[name]+=1
        return value
    checksum=0;start=time.perf_counter()
    try:
        if global_profile:sys.setprofile(callback)
        for i in range(count):
            if i%128==0:check()
            checksum+=invoke('branch',dummy_branch,i,invoke)
    finally:
        sys.setprofile(before)
    seconds=time.perf_counter()-start;check()
    need(sys.getprofile() is before and calls==returns==Counter(branch=count,leaf=2*count),'exact dummycall ledger/profilerrestored')
    return dict(seconds=seconds,dummy_calls=dict(calls),dummy_returns=dict(returns),checksum=checksum,
        callback_events=callback_events,profiler_restored=True,iterations=count)


def worker(pin,remaining):
    sys.path.insert(0,str(ROOT/'scripts/research'))
    from windows_owned_worker import worker_gate
    owner=worker_gate()
    need(owner['status']=='OWNED_JOB_GATE_PASSED_NOT_SCIENTIFIC_ACCEPTANCE','ownedgate before fabricatedwork')
    need(sha(PLAN)==pin,'exact plan')
    plan=json.loads(PLAN.read_bytes());need(sha(Path(__file__).resolve())==plan['worker_sha256'],'exact source')
    need(sha(PREP/'mastery_observer_microbenchmark_schema01.json')==plan['schema_mapping_sha256'],'source-schema mapping pin')
    need(plan['representation_iterations']==64 and plan['dummy_iterations']==4000,'fixed finite counts, no adaptive tuning')
    need(type(remaining) is float and math.isfinite(remaining) and 0<remaining<5,'worker remainder fromsame5s')
    def check():
        if elapsed()>=remaining:raise TimeoutError('operational worker remainder; noretry')
    def audit(event,args):
        if event=='subprocess.Popen' or event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.spawn'):
            raise RuntimeError('no operational children/network')
        if event=='import' and str(args[0]).split('.')[0] in {'numpy','pandas','torch','knowledge_tracing','scipy','sklearn','random'}:
            raise RuntimeError('stdlib-only no native/model/RNG')
        if event=='open' and args and isinstance(args[0],(str,bytes)):
            name=str(args[0]).replace('\\','/').lower()
            if any(x in name for x in ('/dataset/','/paper2/','/research_tracking/runs/','/artifacts/simulator/','/experiments/','/oracle/')):
                raise RuntimeError('no dataset/sourceartifact/cache/oracle/model reads')
    sys.addaudithook(audit)
    need(not any(n in sys.modules for n in ('numpy','pandas','torch','knowledge_tracing')),'fresh stdlibonly')
    error=None;results={};initial_profile=sys.getprofile()
    try:
        need(initial_profile is None,'no preexisting profiler')
        check();original,clone,proof=fixtures(check)
        # Fixed order/iterations frozen in plan before observing any timing.
        old=representation_trial(original,clone,legacy_fingerprint,plan['representation_iterations'],check)
        new=representation_trial(original,clone,immutable_view,plan['representation_iterations'],check)
        global_trial=ledger_trial(plan['dummy_iterations'],True,check)
        direct_trial=ledger_trial(plan['dummy_iterations'],False,check)
        need(global_trial['checksum']==direct_trial['checksum'] and global_trial['dummy_calls']==direct_trial['dummy_calls'], 'equal dummyoutputs/counters')
        need(new['seconds']>0 and direct_trial['seconds']>0,'positive measured denominators')
        results=dict(fixtures=proof,original_4jsonsha=old,immutable_4views=new,
            original_over_view_seconds_ratio=old['seconds']/new['seconds'],global_profile=global_trial,direct_ledger=direct_trial,
            global_over_direct_seconds_ratio=global_trial['seconds']/direct_trial['seconds'],
            ratio_scope='THIS_FIXED_MANUFACTURED_OBSERVER_WORKLOAD_ONLY_NOT_NATIVE_RUNTIME_OR_COVERAGE')
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
        with (OUT/'worker_failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
    finally:
        if initial_profile is None:sys.setprofile(None)
    if elapsed()>=remaining:error=error or dict(type='PostBudget')
    result=dict(status='OPERATIONAL_MANUFACTURED_BENCHMARK_PENDING_ROOT_POSTWRITE' if error is None else 'REJECTED_NO_RETRY',
        error=error,worker_elapsed_before_receipt_seconds=elapsed(),worker_allowance_seconds=remaining,
        source_sha256=plan['worker_sha256'],plan_sha256=pin,results=results,owned_gate=owner,
        profiler_restored=sys.getprofile() is initial_profile,shape=[28,38],memory_dtype='float32',memory_bytes_per_concept=152,
        model_calls=0,teacher_calls=0,rng_calls=0,actual_data_reads=0,new_independent_N=0,
        prior_native60_allocation_reopened=False,native_schema_coverage_claimed=False,
        rng_scope='Manufactured workload only; ownedlaunch nonce entropy outside workload is not a scientific draw',
        unmeasured_native_costs=['NumPy tobytes allocation','Pandas timestamp conversion','actualnative schema/type verification'])
    write(OUT/'worker_result.json',result)
    if elapsed()>=remaining:
        write(OUT/'worker_postwrite_rejection.json',dict(status='REJECTED_POSTWRITE',seconds=elapsed()))
        error=error or dict(type='PostwriteBudget')
    print(json.dumps(dict(status=result['status'] if error is None else 'REJECTED_NO_RETRY',seconds=elapsed())))
    raise SystemExit(0 if error is None else 1)


def main(args):
    need(args.approval_reference and args.approval_reference.strip() and sha(PLAN)==args.plan_sha256,'ROOT approval/plan')
    plan=json.loads(PLAN.read_bytes())
    need(plan['whole_seconds']==5 and plan['prior_native_60_charged_seconds']==56.3709122
         and plan['native_retry_authorized'] is False,'separate allocation, old60closed')
    need(sha(Path(__file__).resolve())==plan['worker_sha256'] and sha(HELPER)==plan['owned_helper_sha256'],'source/helperpins')
    need(sha(PREP/'mastery_observer_microbenchmark_schema01.json')==plan['schema_mapping_sha256'],'reviewed schema map pin')
    need(Path(sys.prefix).resolve()==ROOT/'.venv' and not OUT.exists(),'fresh .venv attempt, nooverwrite/retry')
    OUT.mkdir();error=None;owned=None;result=None
    try:
        sys.path.insert(0,str(ROOT/'scripts/research'))
        from windows_owned_worker import run_owned
        helper_allowance=5-elapsed()-.5;worker_allowance=helper_allowance-1.1
        need(worker_allowance>0,'samewhole5 includes startup/cleanup1/finalization.5')
        write(OUT/'dispatch.json',dict(status='ONE_OPERATIONAL_ALLOCATION_NOT_REOPEN_NATIVE',approval_reference=args.approval_reference,
            plan_sha256=args.plan_sha256,helper_allowance_seconds=helper_allowance,worker_allowance_seconds=worker_allowance,
            prior_native_charged_seconds=56.3709122,native_retry_authorized=False))
        owned=run_owned(Path(__file__).resolve(),['--worker','--plan-sha256',args.plan_sha256,'--remaining-seconds',str(worker_allowance)],
            OUT/'owned',expected_worker_sha256=plan['worker_sha256'],approval_reference=args.approval_reference,
            max_seconds=helper_allowance,cleanup_reserve_seconds=1.,max_output_bytes=16384)
        write(OUT/'owned/receipt.json',owned)
        need(owned['accepted'] is True and owned['cleanup_accepted'] is True and owned['job_active_after_cleanup']==0
             and owned['actual_worker_in_job_before_GO'] is True and owned['popen_handle_closed'] is True,'owned cleanup/job0')
        need(not (OUT/'worker_postwrite_rejection.json').exists() and not (OUT/'worker_failure.log').exists(),'no late/worker rejection')
        result=json.loads((OUT/'worker_result.json').read_bytes())
        need(result['status']=='OPERATIONAL_MANUFACTURED_BENCHMARK_PENDING_ROOT_POSTWRITE' and result['error'] is None
             and result['profiler_restored'] is True and result['native_schema_coverage_claimed'] is False,'operational result only')
        need(result['plan_sha256']==args.plan_sha256 and result['source_sha256']==plan['worker_sha256']
             and result['results']['fixtures']['mutation_count']==19,'source-bound mutationfixtures')
        need(all(result[k]==0 for k in ('model_calls','teacher_calls','rng_calls','actual_data_reads','new_independent_N')),'zero science/native')
        need(sha(Path(__file__).resolve())==plan['worker_sha256'] and sha(PLAN)==args.plan_sha256
             and sha(HELPER)==plan['owned_helper_sha256']
             and sha(PREP/'mastery_observer_microbenchmark_schema01.json')==plan['schema_mapping_sha256'],'posthash stable')
        need(elapsed()<5,'wholepostelapsed5')
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
        with (OUT/'outer_failure.log').open('x',encoding='utf-8') as f:traceback.print_exc(file=f)
    files=[p for p in OUT.rglob('*') if p.is_file()]
    need(len(files)<=16 and sum(p.stat().st_size for p in files)<=131072,'small bounded operationaloutputs')
    final=dict(status='ACCEPTED_MANUFACTURED_OBSERVER_COST_ONLY' if error is None else 'REJECTED_KEEP_NO_RETRY',error=error,
        elapsed_before_receipt_seconds=elapsed(),cap_seconds=5,prior_native_charged_seconds=56.3709122,
        prior_native_allocation_reopened=False,plan_sha256=args.plan_sha256,source_sha256=plan['worker_sha256'],
        owned_receipt_sha256=sha(OUT/'owned/receipt.json') if owned else None,
        result_sha256=sha(OUT/'worker_result.json') if result else None,
        artifacts_sha256={p.relative_to(OUT).as_posix():sha(p) for p in files},
        limits='ratios only fabricated state/calls; no native forecast or replacement schema proof')
    write(OUT/'final.json',final)
    if elapsed()>=5:
        write(OUT/'postwrite_rejection.json',dict(status='REJECTED_WHOLE5',elapsed_seconds=elapsed()))
        error=error or dict(type='PostwriteBudget')
    print(json.dumps(dict(status=final['status'] if error is None else 'REJECTED_KEEP_NO_RETRY',seconds=elapsed(),error=error)))
    raise SystemExit(0 if error is None else 1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan-sha256',required=True);p.add_argument('--approval-reference')
    p.add_argument('--worker',action='store_true');p.add_argument('--remaining-seconds',type=float)
    args=p.parse_args()
    if args.worker:worker(args.plan_sha256,args.remaining_seconds)
    else:main(args)


