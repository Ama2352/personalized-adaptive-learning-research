"""Shared60s controller: portable mock unit vs separate actual stored-checkpoint integration."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path.cwd().resolve(); PREP = Path(__file__).resolve().parent
assert sys.argv[1:] in (['unit01'], ['integration01'])
label = sys.argv[1]; budget_path = PREP / 'budget.json'
budget = json.loads(budget_path.read_bytes())
remaining = math.floor(60 - budget['reserved_pretest_static_seconds'] - budget['actual_controller_seconds'])
assert remaining > 0
directory = PREP.parent / ('parallel-gkt-adapter-20261108-' + label)
directory.mkdir(exist_ok=False)
names = ['src/knowledge_tracing/gkt/' + n for n in ('adapter.py', 'training_checkpoint.py', 'training.py',
    'recurrent.py', 'core.py', 'config.py', '__init__.py')]
names += ['src/knowledge_tracing/shared_kt.py', 'src/knowledge_tracing/simulator_bridge.py', 'tests/gkt/test_adapter.py']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {n: sha(ROOT / n) for n in names}
for n in names:
    shutil.copyfile(ROOT / n, directory / (n.replace('/', '__') + '.before'))
if label == 'unit01':
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B', '-m', 'pytest', 'tests/gkt/test_adapter.py', '-q',
        '-p', 'no:cacheprovider', '--basetemp', str(directory / 'tmp'), '--junitxml', str(directory / 'pytest.xml')]
else:
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B', str(PREP / 'actual_stored_integration.py'),
               '--output', str(directory / 'result.json')]
env = os.environ.copy()
env.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
           PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'))
start = time.perf_counter(); wall = time.time(); timeout = False
with (directory / 'stdout.log').open('xb') as stdout, (directory / 'stderr.log').open('xb') as stderr:
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=remaining)
        rc = result.returncode
    except subprocess.TimeoutExpired:
        timeout = True; rc = None
elapsed = time.perf_counter() - start; wall_elapsed = time.time() - wall
after = {n: sha(ROOT / n) for n in names}
for n in names:
    shutil.copyfile(ROOT / n, directory / (n.replace('/', '__') + '.after'))
counts = None
if (directory / 'pytest.xml').exists():
    suites = list(ET.parse(directory / 'pytest.xml').iter('testsuite'))
    counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
row = dict(label=label, command=command, returncode=rc, timeout=timeout, timeout_seconds=remaining,
    controller_elapsed_seconds=elapsed, controller_wall_seconds=wall_elapsed, optimizer_steps=0,
    evidence_kind='mocked_unverified_portable_unit' if label == 'unit01' else 'actual_stored_trained_checkpoint_integration',
    source_before=before, source_after=after, sources_unchanged=before == after, counts=counts)
budget['actual_controller_seconds'] += max(elapsed, wall_elapsed)
budget['attempts'].append(dict(label=label, elapsed_seconds=elapsed, returncode=rc))
row['cumulative_conservative_seconds'] = budget['actual_controller_seconds'] + budget['reserved_pretest_static_seconds']
row['resource_accepted'] = not timeout and max(elapsed, wall_elapsed) <= remaining and row['cumulative_conservative_seconds'] <= 60
with (directory / 'run.json').open('x', encoding='utf-8') as stream:
    json.dump(row, stream, indent=2); stream.write('\n')
with budget_path.open('w', encoding='utf-8') as stream:
    json.dump(budget, stream, indent=2); stream.write('\n')
print(json.dumps(row))
print('\n'.join((directory / 'stdout.log').read_text().splitlines()[-14:]))
print('\n'.join((directory / 'stderr.log').read_text().splitlines()[-14:]))
