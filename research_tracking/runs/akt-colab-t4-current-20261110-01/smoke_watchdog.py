import json,os,signal,subprocess,time
from pathlib import Path
r=Path('/content/kltn-current-t4-20261110-01')
out=r/'artifacts/akt/runtime/t4-smoke01';out.mkdir(exist_ok=False)
env=dict(os.environ,CUBLAS_WORKSPACE_CONFIG=':4096:8',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[str(r/'.venv/bin/python'),'-I','-B',str(r/'artifacts/akt/runtime/t4_cuda_smoke.py')]
started=time.monotonic();result=dict(status='FAILED',scope='Bounded free T4 CUDA fixture smoke',timeout_seconds=180)
with (out/'worker.log').open('xb') as log:
    p=subprocess.Popen(command,cwd=r,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    result['pid']=p.pid
    try:
        result['returncode']=p.wait(timeout=180)
        result['status']='PROCESS_EXITED_CHECK_ARTIFACTS' if p.returncode==0 else 'FAILED'
    except subprocess.TimeoutExpired:
        result['error']='180 second smoke timeout'
        assert p.pid>1 and p.pid!=os.getpgrp()
        for sig in (signal.SIGTERM,signal.SIGKILL):
            try:os.killpg(p.pid,sig)
            except ProcessLookupError:pass
        p.wait(timeout=10)
result['elapsed_seconds']=time.monotonic()-started
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
