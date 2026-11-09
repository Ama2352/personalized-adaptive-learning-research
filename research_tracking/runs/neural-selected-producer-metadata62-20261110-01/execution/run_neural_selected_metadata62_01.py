"""Kiểm35SAKT và27GKT trong một cold process, không native fit."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUT = PREP / 'neural-selected-metadata62-01'
SOURCES = ('src/knowledge_tracing/sakt/research_execution.py',
    'src/knowledge_tracing/sakt/research_runner.py', 'tests/sakt/test_research_selected_runner.py',
    'src/knowledge_tracing/gkt/research_execution.py', 'src/knowledge_tracing/gkt/research_runner.py',
    'tests/gkt/test_research_selected.py')
EXPECTED = {'tests/sakt/test_research_selected_runner.py': 35, 'tests/gkt/test_research_selected.py': 27}
FILES = ['cases.json', 'junit.xml', 'pytest.log', 'pytest-file.log', 'stdout.log', 'stderr.log']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


started = time.perf_counter()
assert sys.dont_write_bytecode and Path(sys.prefix).resolve() == ROOT / '.venv'
OUT.mkdir()
before = {name: sha(ROOT / name) for name in SOURCES}
write('reservation.json', dict(source_before=before, expected_per_module=EXPECTED,
    whole_cap_seconds=40, child_timeout_seconds=35, actual_native_fit_permitted=False))
child = r'''
import sys,json,os
from pathlib import Path
from collections import Counter
root=Path.cwd();out=root/'artifacts/akt/local-tests/akt-research-runner-20261108-01/neural-selected-metadata62-01'
sys.path.insert(0,str(root/'src'));sys.pycache_prefix=str(out/'fresh-bytecode')
blocked={'torch','numpy','pandas','scipy','sklearn','modal','boto3','pyBKT'}
assert not blocked.intersection(sys.modules)
def audit(event,args):
    if event=='import' and str(args[0]).split('.')[0] in blocked:raise RuntimeError('No scientific import in metadata tests')
sys.addaudithook(audit)
import pytest
class Recorder:
    def __init__(self):self.ids=[];self.reports=[]
    def pytest_collection_modifyitems(self,items):self.ids=[item.nodeid for item in items]
    def pytest_runtest_logreport(self,report):self.reports.append({'nodeid':report.nodeid,'when':report.when,'outcome':report.outcome})
plugin=Recorder()
args=['-q','--import-mode=importlib','-o','addopts=','-o','log_cli=false','-o','log_file='+str(out/'pytest-file.log'),
      '--basetemp='+str(out/'pytest-temp'),'--junitxml='+str(out/'junit.xml'),
      'tests/sakt/test_research_selected_runner.py','tests/gkt/test_research_selected.py']
with (out/'pytest.log').open('x',encoding='utf-8') as stream:
    from contextlib import redirect_stdout,redirect_stderr
    with redirect_stdout(stream),redirect_stderr(stream):rc=pytest.main(args,plugins=[plugin])
heavy=sorted(blocked.intersection(sys.modules))
with (out/'cases.json').open('x') as stream:json.dump({'pytest_returncode':int(rc),'collected_ids':plugin.ids,'reports':plugin.reports,
    'per_module':dict(Counter(n.split('::')[0] for n in plugin.ids)),'heavy_imports':heavy},stream,indent=2)
raise SystemExit(int(rc) if not heavy else 1)
'''
environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
error = None
returncode = None
stdout = stderr = b''
try:
    result = subprocess.run([sys.executable, '-B', '-c', child], cwd=ROOT, env=environment,
        capture_output=True, timeout=35)
    returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
except subprocess.TimeoutExpired as caught:
    error = 'TIMEOUT_KEEP_ALL_NO_AUTOMATIC_RETRY'
    stdout, stderr = caught.stdout or b'', caught.stderr or b''
for name, raw in [('stdout.log', stdout), ('stderr.log', stderr)]:
    assert len(raw) <= 256 * 1024
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
after = {name: sha(ROOT / name) for name in SOURCES}
counts = cases = None
try:
    cases = json.loads((OUT / 'cases.json').read_bytes())
    tests = list(ET.parse(OUT / 'junit.xml').getroot().iter('testcase'))
    counts = dict(tests=len(tests), failures=sum(len(t.findall('failure')) for t in tests),
        errors=sum(len(t.findall('error')) for t in tests), skipped=sum(len(t.findall('skipped')) for t in tests))
except (OSError, ValueError, ET.ParseError) as caught:
    error = error or str(caught)
calls = [] if cases is None else [r for r in cases['reports'] if r['when'] == 'call']
accepted = (error is None and returncode == 0 and before == after
    and counts == dict(tests=62, failures=0, errors=0, skipped=0)
    and cases['per_module'] == EXPECTED and cases['heavy_imports'] == []
    and len(cases['collected_ids']) == len(set(cases['collected_ids'])) == len(calls) == 62
    and all(report['outcome'] == 'passed' for report in calls)
    and set(report['nodeid'] for report in calls) == set(cases['collected_ids'])
    and time.perf_counter() - started < 40)
outputs = {name: sha(OUT / name) for name in FILES if (OUT / name).is_file()}
write('result.json', dict(status='ACCEPTED_COLD_METADATA62_SAKT35_GKT27' if accepted else 'REJECTED_METADATA_KEEP_ALL',
    accepted=accepted, returncode=returncode, error=error, counts=counts,
    per_module=None if cases is None else cases['per_module'],
    heavy_imports=None if cases is None else cases['heavy_imports'], source_before=before,
    source_after=after, outputs_sha256=outputs, elapsed_seconds=time.perf_counter()-started,
    scope_vi='35SAKT và27GKT là hai phần của62ca, không cộng thêm62lần nữa. Không model/NN/corpusfit hoặc execution grant.'))
print(json.dumps(dict(accepted=accepted, counts=counts, error=error)))
raise SystemExit(0 if accepted else 1)
