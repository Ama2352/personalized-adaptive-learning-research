"""ROOT: cold imports và condition/context fixtures; không neural model hoặc corpus."""
import time
START = time.perf_counter()
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent/'graph-context-pure03'
PINS = {'src/knowledge_tracing/akt/research_graph_condition.py':'6678f04c3c0b3655aa797edd3e491877d17ac3f0fa12f7dfc9971f637d875cf0',
        'src/knowledge_tracing/akt/research_graph_context.py':'5a5ada91a78a5d7de2b4d5021dc3cf34e6c97de2e46931509b8f6faf5c56c4d5',
        'tests/akt/test_research_graph_condition.py':'2fdd512ca905973306a27b2d0059d0110cff1e8f4b01b7db715aa23ec5d758e1',
        'tests/akt/test_research_graph_context.py':'ac6bff7187ef37aa9b4455706992763681ccd9f433fd93965cf93d7ce7c9dd52'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert Path(sys.prefix).resolve() == ROOT/'.venv'
assert all(sha(ROOT/n) == h for n,h in PINS.items())
assert not OUT.exists()
OUT.mkdir()
env = dict(os.environ, PYTHONPATH=str(ROOT/'src'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2')
canaries = []
for name, block_numpy in [('research_graph_condition',True),('research_graph_context',False)]:
    code = """import importlib,json,sys
blocked={'torch','pandas','scipy','sklearn','joblib'}
if sys.argv[2]=='1': blocked.add('numpy')
assert not blocked.intersection(sys.modules)
def guard(event,args):
 if event=='import' and str(args[0]).split('.')[0] in blocked: raise RuntimeError('cold import forbidden: '+str(args[0]))
sys.addaudithook(guard)
m=importlib.import_module('knowledge_tracing.akt.'+sys.argv[1])
assert not blocked.intersection(sys.modules)
print(json.dumps({'module':m.__name__,'numpy_loaded':'numpy' in sys.modules,'torch_loaded':'torch' in sys.modules,'accepted':True}))
"""
    child = subprocess.run([sys.executable,'-B','-c',code,name,str(int(block_numpy))],cwd=ROOT,env=env,capture_output=True,timeout=5)
    (OUT/(name+'-cold.stdout.log')).write_bytes(child.stdout)
    (OUT/(name+'-cold.stderr.log')).write_bytes(child.stderr)
    assert child.returncode == 0, child.stderr
    canaries.append(json.loads(child.stdout))
sys.path.insert(0,str(ROOT/'src'))
from knowledge_tracing.akt.research_graph_context import source_inventory
sources = dict(source_inventory()); sources.update(PINS)
assert 'torch' not in sys.modules
command = [sys.executable,'-B','-m','pytest','tests/akt/test_research_graph_condition.py','tests/akt/test_research_graph_context.py','-q','--noconftest','-p','no:cacheprovider','--basetemp',str(OUT/'tmp'),'--junitxml',str(OUT/'junit.xml')]
error = None; code = None
try:
    with (OUT/'pytest.log').open('xb') as stream:
        code = subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=min(75,90-(time.perf_counter()-START)-2)).returncode
except subprocess.TimeoutExpired:
    error = 'PYTEST_TIMEOUT_CHILD_KILLED_AND_REAPED'
counts = None
if (OUT/'junit.xml').is_file():
    tree = ET.parse(OUT/'junit.xml').getroot()
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    assert len(list(tree.iter('testcase'))) == counts['tests']
after = {n:sha(ROOT/n) for n in sources}
accepted = error is None and code == 0 and after == sources and counts == dict(tests=109,failures=0,errors=0,skipped=0) and time.perf_counter()-START < 90
result = dict(status='ACCEPTED_109_CONDITION_CONTEXT_CASES_NOT_MODEL' if accepted else 'REJECTED_KEEP_ALL',
              counts=counts,returncode=code,error=error,cold_import_canaries=canaries,source_before=sources,source_after=after,
              command=command,seconds=time.perf_counter()-START,cap_seconds=90,child_cap_seconds=75,
              actual_neural_model_calls=0,actual_optimizer_calls=0,actual_teacher_calls=0,actual_artifact_or_corpus_parsed=False,
              scope_vi='Handmade typed observable phases, NumPy allowed; no neural/solver/realcorpus. Reviewed tests launch no descendants; ordinary subprocess reaped, not hard OS RAM quota.')
with (OUT/'result.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status=result['status'],counts=counts,seconds=time.perf_counter()-START)))
raise SystemExit(0 if accepted else 1)
