"""CPU join/fit A0 từ numeric đã xong; giữ nguyên request GPU."""
import os,sys,json,warnings,hashlib
from pathlib import Path
ROOT=Path.cwd();B=ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml');os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*');sys.path.insert(0,str(ROOT/'scripts/akt'))
import modal
from modal_junyi_calibration import create_app,operation_tranche
request_entry=json.loads((B/'A0_GPU_REQUEST_ENTRY01.json').read_text())
gpu=json.loads((B/'A0_GPU_RESULT01.json').read_text());gpu_entry=dict(path=gpu['result_path'],sha256=gpu['result_sha256'])
pre=json.loads((B/'PREFLIGHT04.json').read_text())
for name,pin in pre['worker_sources'].items():assert hashlib.sha256((ROOT/'scripts/akt'/name).read_bytes()).hexdigest()==pin,name
auth=dict(workspace='honguyenminhsang2016',stage='cpu-join',allocation_id='calibration-a0-join-20261117-01',reserved_usd=.75,request_sha256=request_entry['sha256'])
(B/'A0_CPU_JOIN_AUTHORIZATION01.json').write_text(json.dumps(auth,indent=2)+'\n',encoding='utf-8')
operation=operation_tranche('A0','cpu-join',auth['allocation_id']);run_id='junyi-calibration-real-20261117-01'
app,functions=create_app()
with modal.enable_output(),app.run(environment_name='main'):
 try:
  print('A0_CPU_JOIN_V1_FIT_DRIVE_START_NO_GPU',flush=True)
  result=functions['join_fit'].remote(request_entry,pre['worker_sources']['calibration_cloud_worker.py'],auth,gpu_entry)
  (B/'A0_CPU_JOIN_RESULT01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print('A0_CPU_CALIBRATION_FIT_COMPLETE',flush=True)
 except Exception as error:
  (B/'A0_CPU_JOIN_FAILURE01.json').write_text(json.dumps(dict(error_type=type(error).__name__,operation=operation),indent=2)+'\n',encoding='utf-8')
  raise
 finally:
  publication=functions['publish_metadata'].remote(run_id,[operation])
  (B/'A0_CPU_JOIN_METADATA_DRIVE01.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('CPU_APP_STOPPED',flush=True)
