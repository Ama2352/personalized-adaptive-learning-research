"""Một readonly regression, cùng cumulative60s actual-stage;0updates mới."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
r=Path.cwd();p=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==r/'.venv'
spent=sum(json.loads(f.read_text())['controller_seconds'] for f in p.glob('actual[0-9][0-9]/receipt.json'))
out=p/'inventory-correction01';out.mkdir(exist_ok=False)
files=[r/'tests/akt/test_simulator_engineering.py',p/'inventory_correction_child.py']
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
before={str(f.relative_to(r)):h(f) for f in files}
for f in files:(out/f.name).write_bytes(f.read_bytes())
env=dict(os.environ,PYTHONPATH=str(r/'src'),CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
start=time.perf_counter()
with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
    result=subprocess.run([sys.executable,str(p/'inventory_correction_child.py')],cwd=r,env=env,stdout=stdout,stderr=stderr,timeout=60-spent-2)
elapsed=time.perf_counter()-start
after={str(f.relative_to(r)):h(f) for f in files}
receipt=dict(status='PASS_READONLY_CORRECTED_INVENTORY_TEST' if result.returncode==0 and before==after and spent+elapsed<=60 else 'FAILED',returncode=result.returncode,controller_seconds=elapsed,previous_actual_seconds=spent,cumulative_seconds=spent+elapsed,cap_seconds=60,source_before=before,source_after=after,new_optimizer_updates=0,scope='One direct test-function call with stored fixture; not a whole46suite rerun or new fit')
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
raise SystemExit(result.returncode)
