"""ROOT: kiểm metadata condition bằng pytest; không model/dataset/solver."""
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
OUT = Path(__file__).resolve().parent/'graph-condition-pure01'
PINS = {'src/knowledge_tracing/akt/research_graph_condition.py':'6678f04c3c0b3655aa797edd3e491877d17ac3f0fa12f7dfc9971f637d875cf0',
        'tests/akt/test_research_graph_condition.py':'adcca5792f9f35fb2798ad2157d38835e50d01f5e35eebc74427002bd5c4b0e3'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert Path(sys.prefix).resolve() == ROOT/'.venv'
assert all(sha(ROOT/n) == h for n,h in PINS.items())
assert not OUT.exists()
OUT.mkdir()
sys.path.insert(0, str(ROOT/'src'))
from knowledge_tracing.akt.research_graph_condition import source_inventory
sources = dict(source_inventory()); sources.update(PINS)
assert not set(('numpy','torch','pandas','scipy','sklearn')).intersection(sys.modules)
env = dict(os.environ, PYTHONPATH=str(ROOT/'src'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='')
command = [sys.executable,'-B','-m','pytest','tests/akt/test_research_graph_condition.py','-q','--noconftest',
           '-p','no:cacheprovider','--basetemp',str(OUT/'tmp'),'--junitxml',str(OUT/'junit.xml')]
error = None
code = None
try:
    with (OUT/'pytest.log').open('xb') as stream:
        child = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=20)
    code = child.returncode
except subprocess.TimeoutExpired:
    error = 'PYTEST_20S_TIMEOUT_CHILD_KILLED_AND_REAPED'
counts = None
if (OUT/'junit.xml').is_file():
    tree = ET.parse(OUT/'junit.xml').getroot()
    counts = {k:sum(int(s.get(k,'0')) for s in tree.iter('testsuite')) for k in ('tests','failures','errors','skipped')}
    assert len(list(tree.iter('testcase'))) == counts['tests']
after = {n:sha(ROOT/n) for n in sources}
accepted = error is None and code == 0 and after == sources and counts == dict(tests=66,failures=0,errors=0,skipped=0) and time.perf_counter()-START < 30
result = dict(status='ACCEPTED_66_METADATA_CONDITION_CASES_NOT_MODEL' if accepted else 'REJECTED_KEEP_ALL',
              counts=counts,returncode=code,error=error,source_before=sources,source_after=after,
              command=command,seconds=time.perf_counter()-START,cap_seconds=30,child_cap_seconds=20,
              actual_model_calls=0,actual_optimizer_calls=0,actual_solver_calls=0,
              actual_artifact_or_corpus_parsed=False,scope_vi='Handmade typed UNVERIFIED metadata only; no producer or neural fit proof. Plain subprocess reaped; no descendants launched by reviewed test source; no OS RAM quota claim.')
with (OUT/'result.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps(dict(status=result['status'],counts=counts,seconds=time.perf_counter()-START)))
raise SystemExit(0 if accepted else 1)
