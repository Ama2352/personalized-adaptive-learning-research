import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/research'))
import windows_owned_worker as helper
gate=helper.worker_gate()
attempt=Path(os.environ['KLTN_WINDOWS_LAUNCH_MANIFEST']).parent
mode=sys.argv[1]
result={'mode':mode,'gate':gate,'forbidden': [n for n in helper.FORBIDDEN if n in sys.modules]}
if mode=='descendant':
 child=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(4)'],stdin=subprocess.DEVNULL,
  stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
  creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP)
 api=helper.Kernel();result['descendant']=api.token(int(child._handle))
 job=api.check(api.k.OpenJobObjectW(4,False,gate['job_name']))
 try:result['descendant_in_job']=api.contains(int(child._handle),job)
 finally:api.close(job)
if mode=='timeout':time.sleep(4)
with (attempt/'body.json').open('x',encoding='utf-8') as f:
 json.dump(result,f);f.flush();os.fsync(f.fileno())
print(json.dumps({'mode':mode,'native_model_calls':0}))
