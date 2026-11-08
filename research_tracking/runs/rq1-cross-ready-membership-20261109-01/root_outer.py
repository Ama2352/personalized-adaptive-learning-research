"""ROOT: một hậu kiểm cache, toàn operation10s, không chạy lại mô hình."""
from pathlib import Path
import hashlib,json,sys,time
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
started=time.perf_counter();wall=time.time()
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
worker=R/'scripts/research/analyze_rq1_cross_ready.py'
worker_sha='423968f864c84c8fc66a6678bf9351b195cc3ce47d38eb8696ddbab0ee830398'
plan=P/'rq1_cross_ready_plan01.json';plan_sha='f54f99fa4cf098ae28bc4488bd827b9bca1b05663472189364618228e4b43fc8'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(worker)==worker_sha and sha(plan)==plan_sha
pure=json.loads((P/'edge-artifact-cross-ready02-owned/final.json').read_bytes())
assert pure['status']=='ACCEPTED_60_DATA_ONLY_FIXTURES' and pure['counts']==dict(tests=60,failures=0,errors=0,skipped=0)
config=json.loads(plan.read_bytes())
before={n:sha(R/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01'/n) for n in config['inputs_sha256']}
assert before==config['inputs_sha256']
out=P/'rq1-cross-ready01-owned'
args=['--plan',plan.relative_to(R).as_posix(),'--plan-sha256',plan_sha,'--source-sha256',worker_sha,
      '--output-name','rq1-cross-ready-attempt01']
allowance=10-max(time.perf_counter()-started,time.time()-wall)-.5
assert allowance>2
receipt=run_owned(worker,args,out,expected_worker_sha256=worker_sha,
    approval_reference='ROOT_USER_LOCAL_CACHED_RQ1_1080PAIRS_CROSS_READY_10S_0NEW_N_0MODELS',
    max_seconds=allowance,cleanup_reserve_seconds=2,max_output_bytes=16384)
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
directory=P/'rq1-cross-ready-attempt01';errors=[];inputs_after={};result=validation=None;artifacts={}
try:
    assert receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0 and receipt['popen_handle_closed']
    assert {q.name for q in directory.iterdir()}=={'summary.json','event_flags.json','validation.json','result.json'}
    result=json.loads((directory/'result.json').read_bytes());validation=json.loads((directory/'validation.json').read_bytes())
    assert result['status']=='INNER_COMPLETE_PENDING_OWNED_OUTER_ACCEPTANCE' and result['worker_seconds']<7
    assert validation['rows']==1080 and validation['groups']==16 and validation['joint_cells']==128 and validation['membership_cells']==256
    assert validation['exact_query_label_key_join'] and validation['old_per_event_flags_exact'] and validation['old_marginals_exact'] and validation['no_dropped_rows']
    assert validation['new_independent_N']==validation['actual_model_calls']==0
    for q in directory.iterdir():
        assert q.stat().st_size<=4*1024**2
        artifacts[q.name]={'sha256':sha(q),'bytes':q.stat().st_size}
    assert sum(x['bytes'] for x in artifacts.values())<=8*1024**2
    assert result['outputs_sha256']=={n:v['sha256'] for n,v in artifacts.items() if n!='result.json'}
    inputs_after={n:sha(R/'research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01'/n) for n in before}
    assert before==inputs_after and sha(worker)==worker_sha and sha(plan)==plan_sha
except BaseException as e:errors.append({'type':type(e).__name__,'message':str(e)})
elapsed=max(time.perf_counter()-started,time.time()-wall)
accepted=not errors and elapsed<10
final=dict(status='ACCEPTED_CACHED_CROSS_READY_DIAGNOSTIC' if accepted else 'REJECTED_KEEP_PARTIAL',
    elapsed_seconds=elapsed,cap_seconds=10,errors=errors,artifacts=artifacts,input_before=before,input_after=inputs_after,
    source_sha256=worker_sha,plan_sha256=plan_sha,new_independent_N=0,model_calls=0,solver_fits=0,
    scope_vi='Recordedready membership, không actualC/B/score-only/causalmediation; no rerun simulation.')
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2)
if max(time.perf_counter()-started,time.time()-wall)>=10:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False
print(json.dumps({'status':final['status'] if accepted else 'REJECTED_KEEP_PARTIAL','elapsed_seconds':max(time.perf_counter()-started,time.time()-wall),'cap_seconds':10}))
raise SystemExit(0 if accepted else 1)
