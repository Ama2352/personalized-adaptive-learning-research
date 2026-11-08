"""Same-source localhost demo tests, actual prior cost retained, cap60 all attempts."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,math
import xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve()
assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=ROOT/'artifacts/akt/local-tests/parallel-demo-20261108-01/c14-preparation'
PRIOR=PREP.parent/'c14-t1'
OUT=PREP.parent/'c14-t2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
START=time.perf_counter()
assert sha(PREP/'test_plan01.json')=='7e9066c79caf04427045444f3b169e230a7a47269ccf0e157ad6df79b4082132'
assert sha(PRIOR/'run.json')=='9f83885c1a1abc0c7781bb5a08a2040e7529760def9414ee4a31ecca1973cb17'
plan=json.loads((PREP/'test_plan01.json').read_text());prior=json.loads((PRIOR/'run.json').read_text())
failures=list(ET.parse(PRIOR/'pytest.xml').getroot().iter('failure'))
assert len(failures)==36 and all('WinError 10013' in ''.join(f.itertext()) for f in failures)
assert prior['counts']=={'tests':83,'failures':36,'errors':0,'skipped':0}
assert prior['source_sha256_before']==prior['source_sha256_after']==plan['source_sha256']
BEFORE={f:sha(ROOT/f) for f in plan['source_sha256']};assert BEFORE==plan['source_sha256']
OUT.mkdir(exist_ok=False)
for f in BEFORE:(OUT/(f.replace('/','__')+'.before')).write_bytes((ROOT/f).read_bytes())
command=[sys.executable,'-B','-m','pytest','tests/demo/test_viewer.py','-q','-p','no:cacheprovider','--basetemp',str(OUT/'t'),'--junitxml',str(OUT/'pytest.xml')]
reserve=1.0
remaining=60-prior['controller_seconds']-reserve-(time.perf_counter()-START)
assert math.isfinite(remaining) and remaining>0
rc=None;failure=None
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
try:
 with (OUT/'pytest.log').open('xb') as log:rc=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining).returncode
except BaseException as e:failure=type(e).__name__+': '+str(e)
AFTER={f:sha(ROOT/f) for f in BEFORE}
for f in AFTER:(OUT/(f.replace('/','__')+'.after')).write_bytes((ROOT/f).read_bytes())
counts={}
if (OUT/'pytest.xml').exists():
 suites=list(ET.parse(OUT/'pytest.xml').getroot().iter('testsuite'));counts={k:sum(int(s.get(k,0)) for s in suites) for k in ['tests','failures','errors','skipped']}
elapsed=time.perf_counter()-START;total=prior['controller_seconds']+reserve+elapsed
status='PASS_DEMO_C14_ONLY' if rc==0 and failure is None and BEFORE==AFTER and math.isfinite(total) and total<=60 else 'FAILED_DEMO_C14_RETAIN'
receipt={'status':status,'returncode':rc,'failure':failure,'counts':counts,'controller_seconds':elapsed,'prior_actual_seconds':prior['controller_seconds'],'startup_postcheck_reserve_seconds':reserve,'cumulative_all_attempts_seconds':total,'cap_seconds':60,'command':command,'source_sha256_before':BEFORE,'source_sha256_after':AFTER,'prior_failures_reason':'ALL36HTTPconnectWinError10013;sourceunchanged','execution_scope':'Exact bounded process localhostpermission; no externalnetwork/model/optimizer/researchreplay','model_optimizer_research_replay_calls':0}
(OUT/'run.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2));print((OUT/'pytest.log').read_text(encoding='utf-8')[-8000:])
