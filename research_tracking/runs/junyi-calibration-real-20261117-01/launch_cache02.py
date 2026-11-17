"""Tiếp tục CPU cache trên image đã preflight, chuẩn hóa entry path/SHA."""
import json,os,sys,warnings
from pathlib import Path
ROOT=Path.cwd()
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
import modal
B=ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')
app=modal.App('kltn-calibration-cache-continue-cpu')
@app.function(image=modal.Image.from_id('im-HYtUuyWH9hslrwqviVh9Br'),cpu=1,memory=16384,
 timeout=3600,startup_timeout=180,max_containers=1,scaledown_window=2,retries=0,
 single_use_containers=True,serialized=True,routing_region='ap-south',volumes={'/artifacts':volume})
def prepare(entry,worker_sha,authorization):
 import sys
 sys.path.insert(0,'/opt/kltn/scripts/akt')
 import modal_junyi_calibration as controller
 volume.reload()
 return controller._run('cpu-cache',entry,worker_sha,authorization)
if __name__=='__main__':
 receipt=json.loads((B/'CPU_CACHE_REQUEST_ENTRY01.json').read_text())
 entry={key:receipt[key] for key in ('path','sha256')}
 authorization=json.loads((B/'CPU_CACHE_AUTHORIZATION01.json').read_text())
 pre=json.loads((B/'PREFLIGHT03.json').read_text())
 (B/'CPU_CACHE_ENTRY_NORMALIZED02.json').write_text(json.dumps(entry,indent=2),encoding='utf-8')
 with modal.enable_output(),app.run(environment_name='main'):
  result=prepare.remote(entry,pre['worker_sources']['calibration_cloud_worker.py'],authorization)
 (B/'CPU_CACHE_RESULT02.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False),flush=True)
