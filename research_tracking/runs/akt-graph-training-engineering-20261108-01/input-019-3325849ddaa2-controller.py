"""Callback checks: hard-fail native construction/Adam step, cap30s cumulative."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET

r=Path.cwd();prep=Path(__file__).resolve().parent
assert Path(sys.prefix).resolve()==r/'.venv'
previous=sorted(prep.glob('callback-pure*/receipt.json'))
spent=sum(json.loads(p.read_text())['elapsed_seconds'] for p in previous)
remaining=30-spent
assert remaining>3
out=prep/f'callback-pure{len(previous)+1:02d}';out.mkdir(exist_ok=False)
files=['src/knowledge_tracing/akt/training.py','tests/akt/test_batch_factory.py']
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={f:h(r/f) for f in files}
for f in files:(out/Path(f).name).write_bytes((r/f).read_bytes())
(out/'controller.py').write_bytes(Path(__file__).read_bytes())
env=dict(os.environ,PYTHONPATH=str(r/'src'),CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='',
    OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
code='import torch,pytest,knowledge_tracing.akt.upstream as u;torch.set_num_threads(2);exec("def forbidden(*a,**k):\\n raise AssertionError(\'No native constructor/Adam step in pure suite\')");u.build_native=forbidden;torch.optim.Adam.step=forbidden;raise SystemExit(pytest.main())'
# Real newline in exec source, no shell interpolation.
code=code.replace('\\n','\n')
cmd=[str(r/'.venv/Scripts/python.exe'),'-c',code,'-q',files[1],'-o','cache_dir='+str(out/'cache'),'--junitxml='+str(out/'pytest.xml')]
start=time.perf_counter();p=None;status='FAILED'
try:
    with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
        p=subprocess.Popen(cmd,cwd=r,env=env,stdout=stdout,stderr=stderr)
        try:p.wait(timeout=remaining-2)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=1)
    suites=list(ET.parse(out/'pytest.xml').getroot().iter('testsuite')) if (out/'pytest.xml').exists() else []
    counts={k:sum(int(x.get(k,0)) for x in suites) for k in ('tests','failures','errors','skipped')}
    if p.returncode==0 and counts==dict(tests=8,failures=0,errors=0,skipped=0):status='PASS_PURE_CALLBACK_CONTRACT_NO_MODEL'
finally:
    if p is not None and p.poll() is None:p.kill();p.wait(timeout=1)
    elapsed=time.perf_counter()-start
    after={f:h(r/f) for f in files}
    if before!=after:status='SOURCE_DRIFT'
    if spent+elapsed>30:status='REJECTED_CUMULATIVE_RESOURCE_BOUND'
    receipt=dict(status=status,counts=locals().get('counts'),command=cmd,source_before=before,source_after=after,
        elapsed_seconds=elapsed,previous_seconds=spent,cumulative_seconds=spent+elapsed,cap_seconds=30,
        child_reaped=p is None or p.poll() is not None,native_construction='forbidden by raising spy',optimizer_step='forbidden by raising spy')
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))
raise SystemExit(0 if status.startswith('PASS_') else 1)
