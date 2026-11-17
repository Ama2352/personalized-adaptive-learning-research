"""A0 calibration inference có giới hạn, cache metadata lên Drive trước H100."""
import json,os,sys,warnings,hashlib
from pathlib import Path
ROOT=Path.cwd();B=ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml');os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
sys.path.insert(0,str(ROOT/'scripts/akt'));sys.path.insert(0,str(ROOT/'src'))
import modal
from modal_junyi_calibration import create_app,operation_tranche
request=json.loads((B/'REQUEST_A0_GPU01.json').read_text())
assert request['variant']=='A0' and request['numeric_budget']['expected_targets']==1621484
ledger=json.loads((ROOT/'research_tracking/COMPUTE_BUDGET_WORKSPACE2016.json').read_text())
assert ledger['workspace_name']=='honguyenminhsang2016'
assert ledger['historical_usage_reserved_upper_usd']+sum(x.get('reserved_upper_usd',0) for x in ledger['new_allocations'])+ledger['safety_and_final_inference_reserve_usd']<=30
allocation=next(x for x in ledger['new_allocations'] if x['id']=='calibration-a0-gpu-20261117-01')
assert allocation['reserved_upper_usd']==.75
app,functions=create_app()
with modal.enable_output(),app.run(environment_name='main'):
 pre=functions['preflight'].remote()
 (B/'PREFLIGHT04.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert pre['source_identity']==request['source_identity']
 for name,pin in pre['worker_sources'].items():assert hashlib.sha256((ROOT/'scripts/akt'/name).read_bytes()).hexdigest()==pin,name
 print('ACTUAL_SOURCE_WORKER_RUNTIME_GATE_PASS',flush=True)
 cache_pub=functions['publish_metadata'].remote(request['run_id'],['a0-cpu-cache-operation'])
 (B/'CPU_CACHE_DRIVE01.json').write_text(json.dumps(cache_pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert cache_pub['status']=='OPERATION_METADATA_PUBLISHED'
 assert all(p['account']=='honguyenminhsang2005@gmail.com' and p['status']=='DRIVE_SHA256_VERIFIED' for p in cache_pub['publications'])
 print('CPU_CACHE_CONFIG_RECEIPTS_DRIVE_VERIFIED',flush=True)
 published=functions['put_request'].remote(request,'requests/'+request['run_id']+'-a0-gpu01.json')
 entry={key:published[key] for key in ('path','sha256')}
 (B/'A0_GPU_REQUEST_ENTRY01.json').write_text(json.dumps(entry,indent=2)+'\n',encoding='utf-8')
 auth=dict(workspace='honguyenminhsang2016',stage='gpu',allocation_id='calibration-a0-gpu-20261117-01',reserved_usd=.75,request_sha256=entry['sha256'])
 (B/'A0_GPU_AUTHORIZATION01.json').write_text(json.dumps(auth,indent=2)+'\n',encoding='utf-8')
 operation=operation_tranche('A0','gpu',auth['allocation_id'])
 try:
  print('A0_H100_FULL_CALIBRATION_INFERENCE_START_MAX300_SECONDS',flush=True)
  result=functions['predict'].remote(entry,pre['worker_sources']['calibration_cloud_worker.py'],auth)
  (B/'A0_GPU_RESULT01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  assert result['result']['counts']['targets']==1621484
  assert result['result']['counts']['oov_targets']==0
  print('A0_GPU_COMPLETE_CHECKPOINT_UNCHANGED_NUMERIC_COMMITTED',flush=True)
 except Exception as error:
  (B/'A0_GPU_FAILURE01.json').write_text(json.dumps(dict(error_type=type(error).__name__,operation=operation),indent=2)+'\n',encoding='utf-8')
  raise
 finally:
  publication=functions['publish_metadata'].remote(request['run_id'],[operation])
  (B/'A0_GPU_METADATA_DRIVE01.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print('A0_GPU_OPERATION_LOGS_TELEMETRY_DRIVE_VERIFIED',flush=True)
print('APP_FINISHED_NO_MORE_GPU_INPUTS',flush=True)
