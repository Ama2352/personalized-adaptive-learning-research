"""ROOT: một hậu kiểm cache, tổng10giây; không simulator/model/labels để chọn."""
from pathlib import Path
import hashlib,json,sys,time
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts/research'))
from windows_owned_worker import run_owned
start=time.perf_counter();wall=time.time()
freeze=json.loads((P/'ready_set_exposure_freeze01.json').read_bytes())
worker=R/freeze['worker_relative'];out=R/freeze['owned_attempt_relative']
if hashlib.sha256(worker.read_bytes()).hexdigest()!=freeze['source_sha256']:raise ValueError('source changed')
receipt=run_owned(worker,freeze['worker_args'],out,expected_worker_sha256=freeze['source_sha256'],
                  approval_reference='USER_LOCAL_RQ1_POSTHOC_CACHED_READY_EXPOSURE_3240_0NATIVE',
                  max_seconds=freeze['owned_max_seconds'],cleanup_reserve_seconds=freeze['cleanup_reserve_seconds'],
                  max_output_bytes=freeze['max_output_bytes'])
with (out/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
result_path=P/'ready-exposure-attempt01/result.json';validation_path=result_path.with_name('validation.json')
result=json.loads(result_path.read_bytes()) if result_path.exists() else None
validation=json.loads(validation_path.read_bytes()) if validation_path.exists() else None
valid=bool(result and validation and result['status']=='INNER_COMPLETE_PENDING_OWNED_OUTER_ACCEPTANCE'
           and validation['status']=='ALL3240_SOURCE_READY_SETS_ORDER_EXACT'
           and validation['rows']==validation['ready_order_exact']==validation['served_in_B_subset_C_exact']==3240
           and validation['trajectories']==27 and validation['concept_cells_including_zeros']==4480
           and validation['source_sha256']==freeze['source_sha256'] and validation['plan_sha256']==freeze['plan_sha256'])
if result:
    valid=valid and all(hashlib.sha256(result_path.with_name(name).read_bytes()).hexdigest()==digest
                        for name,digest in result['outputs_sha256'].items())
elapsed=max(time.perf_counter()-start,time.time()-wall)
accepted=bool(valid and receipt['accepted'] and receipt['cleanup_accepted'] and receipt['job_active_after_cleanup']==0
              and receipt['popen_handle_closed'] and elapsed<10 and not result_path.with_name('failure.json').exists()
              and hashlib.sha256(worker.read_bytes()).hexdigest()==freeze['source_sha256']
              and hashlib.sha256((R/freeze['plan_relative']).read_bytes()).hexdigest()==freeze['plan_sha256'])
final=dict(status='ACCEPTED_CACHED_SOURCE_LOCAL_DESCRIPTION' if accepted else 'REJECTED_CACHED_ANALYSIS',
           elapsed_seconds=elapsed,cap_seconds=10,rows=3240 if valid else None,new_independent_N=0,
           actual_model_calls=0,optimizer_steps=0,actual_simulator_calls=0,owned_cleanup=receipt['cleanup_accepted'])
with (out/'final.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2);f.write('\n')
if max(time.perf_counter()-start,time.time()-wall)>=10:
    with (out/'postwrite_rejection.json').open('x',encoding='utf-8') as f:json.dump({'status':'REJECTED_POSTWRITE_BUDGET'},f)
    accepted=False
print(json.dumps(final,ensure_ascii=False));raise SystemExit(0 if accepted else 1)
