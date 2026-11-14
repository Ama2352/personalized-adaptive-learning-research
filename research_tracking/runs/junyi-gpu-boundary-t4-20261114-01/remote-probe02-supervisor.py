from pathlib import Path
import json,subprocess,os,sys,time,signal,traceback
root=Path('/content/kltn-gpu-boundary-20261114-01');started=time.monotonic();process=None;status={'status':'FAILED'}
try:
 assert json.loads((root/'runtime/setup-result.json').read_text())['status']=='PROJECT_VENV_READY'
 assert json.loads((root/'runtime/materialization-result.json').read_text())['status']=='SOURCE_AND_OFFLINE_CACHES_MATERIALIZED'
 output=root/'experiments/akt/results/gpu-boundary-t4-20261114-02';assert not output.exists()
 command=[str(root/'.venv/bin/python'),'-u','-B',str(root/'scripts/akt/probe_junyi_gpu_boundary.py'),'--root',str(root),'--output',str(output),'--prepared-receipts',str(root/'benchmark-prepared'),'--cache-id','gpu-boundary-t4-20261114-01']
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
 with (root/'runtime/probe02.log').open('xb') as log:
  process=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  status['pid']=process.pid
  process.wait(timeout=480)
 status.update(status='PROBE_PROCESS_EXITED',returncode=process.returncode)
except BaseException as error:
 status.update(error_type=type(error).__name__,error=str(error));traceback.print_exc()
finally:
 if process is not None and process.poll() is None:
  os.killpg(process.pid,signal.SIGTERM)
  try:process.wait(timeout=8)
  except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=8)
 status['seconds']=time.monotonic()-started;(root/'runtime/probe02-supervisor-result.json').write_text(json.dumps(status))
