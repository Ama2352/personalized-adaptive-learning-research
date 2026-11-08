"""ROOT worker: tám fixtures và join hai bộ snapshot có sẵn; không model."""
import time
START = time.perf_counter()
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
import os
import unittest

ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts/research'))
from windows_owned_worker import worker_gate
owner = worker_gate()
OUT = P/'rq1-query-overlap01'
OUT.mkdir(exist_ok=False)
PLAN = P/'rq1_query_overlap_plan01.json'
assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == sys.argv[1]
plan = json.loads(PLAN.read_bytes())
timer = threading.Timer(6, lambda: os._exit(124)); timer.daemon = True; timer.start()

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name, value):
    with (OUT/name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False); stream.write('\n')
def audit(event, args):
    if event == 'subprocess.Popen': raise RuntimeError('Không subprocess trong worker phân tích')
    if event == 'import' and args[0].split('.')[0] in ('torch','numpy','pandas','modal','requests'):
        raise RuntimeError('Không framework/cloud/network trong cached join')
sys.addaudithook(audit)
before = {name: sha(ROOT/name) for name in plan['sources_sha256']}
assert before == plan['sources_sha256']
write('before.json', dict(sources_sha256=before, owner=owner, scope='Cached join, không research N mới'))
spec = importlib.util.spec_from_file_location('overlap_tests', ROOT/'tests/shared_kt/test_rq1_query_decision_overlap.py')
tests = importlib.util.module_from_spec(spec); spec.loader.exec_module(tests)
with (OUT/'unittest.log').open('x', encoding='utf-8') as log:
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
assert result.wasSuccessful() and result.testsRun == 8 and not result.skipped
dirs = [ROOT/x for x in plan['input_bundles']]
for directory in dirs:
    manifest = json.loads((directory/'manifest.json').read_bytes())
    for name in ('event_flags.json', 'summary.json'):
        assert sha(directory/name) == manifest['outputs_sha256'][name]
left, right = [json.loads((d/'event_flags.json').read_bytes()) for d in dirs]
nodes = json.loads((dirs[0]/'summary.json').read_bytes())['node_order']
summary = tests.module.analyze(left, right, nodes)
assert len(left) == len(right) == summary['groups']['pooled']['paired_snapshots'] == 1080
assert len(summary['groups']) == 16
for k, group in summary['groups'].items():
    if k.startswith('trajectory:'): assert group['paired_snapshots'] == 120
write('summary.json', summary)
after = {name: sha(ROOT/name) for name in plan['sources_sha256']}
assert after == before
write('validation.json', dict(status='ACCEPTED_CACHED_OVERLAP_NOT_CAUSAL', tests=8, failures=0, errors=0,
    skipped=0, pairs=1080, groups=16, model_calls=0, new_independent_N=0, source_before=before,
    source_after=after, seconds=time.perf_counter()-START,
    scientific_modules_loaded=sorted(set(sys.modules)&{'torch','numpy','pandas','modal','requests'})))
timer.cancel()
print(json.dumps(dict(status='ACCEPTED_CACHED_OVERLAP_NOT_CAUSAL', pairs=1080, tests=8, seconds=time.perf_counter()-START)))
