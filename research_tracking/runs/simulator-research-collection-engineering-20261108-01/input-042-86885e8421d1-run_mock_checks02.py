"""Bounded mock-only collector checks; source hashing never loads native equations."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
START=time.perf_counter();sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.simulator_research_collection import source_inventory
PREP=Path(__file__).resolve().parent;OUT=PREP/'mock02';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PRIOR=json.loads((PREP/'mock01/run.json').read_bytes())['cumulative_all_attempts_seconds']
before=source_inventory()
for p in ('tests/shared_kt/test_simulator_research_collection.py',
          'artifacts/akt/local-tests/simulator-research-collection-20261108-01/run_mock_checks02.py'):
 before[p]=sha(ROOT/p)
for p in before:
 # Source-only files; no generated learner or model data.
 with (OUT/('before__'+p.replace('/','__'))).open('xb') as f:f.write((ROOT/p).read_bytes())
 assert sha(OUT/('before__'+p.replace('/','__')))==before[p]
cmd=[sys.executable,'-B','-m','pytest','tests/shared_kt/test_simulator_research_collection.py',
 '-q','-p','no:cacheprovider','--basetemp',str(OUT/'t'),'--junitxml',str(OUT/'pytest.xml')]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src'),
 PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
 OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
code=None;error=None
try:
 with (OUT/'pytest.log').open('xb') as log:
  code=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
    timeout=max(.1,60-PRIOR-(time.perf_counter()-START)-.1)).returncode
except BaseException as exc:error=repr(exc)
after={p:sha(ROOT/p) for p in before}
for p in after:
 with (OUT/('after__'+p.replace('/','__'))).open('xb') as f:f.write((ROOT/p).read_bytes())
elapsed=time.perf_counter()-START;counts=None
if (OUT/'pytest.xml').exists():
 suite=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
 counts={k:int(suite.attrib[k]) for k in ('tests','failures','errors','skipped')}
ok=code==0 and not error and counts and not any(counts[k] for k in ('failures','errors','skipped')) and before==after and PRIOR+elapsed<=60
receipt={'status':'PASS_MOCK_ONLY_RESEARCH_COLLECTOR' if ok else 'REJECTED_RETAIN_NO_AUTO_RETRY',
 'command':cmd,'returncode':code,'error':error,'counts':counts,'controller_seconds':elapsed,
 'prior_actual_seconds':PRIOR,'cumulative_all_attempts_seconds':PRIOR+elapsed,'cap_seconds':60,'source_sha256_before':before,
 'source_sha256_after':after,'actual_Paper2_environment_calls':0,'models_optimizer_real_data_remote_calls':0,
 'research_corpus_generated':False,'mock_scope':'Autouse test guard prohibits actual reference loader; mocked environment only',
 'source_snapshot_scope':'fixed source notebook/CSV and code bytes only, not learner events'}
with (OUT/'run.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(receipt,ensure_ascii=False,indent=2));sys.exit(0 if ok else 1)
