"""One bounded pure-synthetic input-contract suite; no generation/model/remote."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
ROOT=Path.cwd().resolve();assert Path(sys.prefix).resolve()==ROOT/'.venv'
PREP=Path(__file__).resolve().parent;OUT=PREP/'trial01';OUT.mkdir(exist_ok=False)
started=time.perf_counter();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=['src/knowledge_tracing/simulator_research_data.py','tests/shared_kt/test_simulator_research_data.py',
 'src/knowledge_tracing/simulator_data.py','src/knowledge_tracing/simulator_collection.py',
 'src/knowledge_tracing/simulator_bridge.py','tests/shared_kt/test_simulator_data.py',
 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
 'artifacts/akt/local-tests/simulator-research-data-20261108-01/run_checks01.py']
before={p:sha(ROOT/p) for p in paths}
for p in paths:
 with (OUT/('before__'+p.replace('/','__'))).open('xb') as f:f.write((ROOT/p).read_bytes())
assert all(sha(OUT/('before__'+p.replace('/','__')))==s for p,s in before.items())
cmd=[sys.executable,'-B','-m','pytest','tests/shared_kt/test_simulator_research_data.py',
 'tests/shared_kt/test_simulator_data.py','-q','-p','no:cacheprovider','--basetemp',str(OUT/'t'),
 '--junitxml',str(OUT/'pytest.xml')]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'src'),
 PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',
 OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
returncode=None;failure=None
try:
 with (OUT/'pytest.log').open('xb') as log:
  child=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
    timeout=max(.1,60-(time.perf_counter()-started)-.1))
 returncode=child.returncode
except BaseException as e:failure=repr(e)
after={p:sha(ROOT/p) for p in paths}
for p in paths:
 with (OUT/('after__'+p.replace('/','__'))).open('xb') as f:f.write((ROOT/p).read_bytes())
elapsed=time.perf_counter()-started
counts=None
if (OUT/'pytest.xml').exists():
 suite=ET.parse(OUT/'pytest.xml').getroot().find('testsuite')
 counts={k:int(suite.attrib[k]) for k in ('tests','failures','errors','skipped')}
ok=returncode==0 and not failure and counts and not any(counts[k] for k in ('failures','errors','skipped')) and before==after and elapsed<=60
receipt={'status':'PASS_PURE_SYNTHETIC_RESEARCH_DATA_CONTRACT' if ok else 'REJECTED_RETAIN_NO_AUTO_RETRY',
 'command':cmd,'returncode':returncode,'failure':failure,'counts':counts,'controller_seconds':elapsed,
 'cumulative_all_attempts_seconds':elapsed,'cap_seconds':60,'source_sha256_before':before,
 'source_sha256_after':after,'model_optimizer_environment_generation_calls':0,
 'research_corpus_generated':False,'fixture_events':'hand-constructed observable binary outcomes only; no environment calls',
 'scope':'split/provenance/coverage/refit-input software checks; not research fit, corpus diversity or independence proof'}
with (OUT/'run.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
sys.exit(0 if ok else 1)
