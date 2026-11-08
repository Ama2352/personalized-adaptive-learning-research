"""Shared60s/4reserved-update controller; model phase requires parent approval first."""
import argparse
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
parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=('pure01', 'model01'))
parser.add_argument('--parent-approval-reference')
args = parser.parse_args()
contract = json.loads((PREP / 'pre_update_contract.json').read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(ROOT / n) == h for n, h in contract['sources_sha256'].items())
budget_path = PREP / 'budget.json'; budget = json.loads(budget_path.read_bytes())
remaining = math.floor(60 - budget['reserved_static_seconds'] - budget['actual_controller_seconds'])
assert remaining > 0
if args.phase == 'model01':
    assert args.parent_approval_reference and args.parent_approval_reference.strip()
    assert 4 - budget['optimizer_updates'] >= 2
directory = PREP.parent / ('parallel-gkt-pipeline-20261108-' + args.phase); directory.mkdir(exist_ok=False)
names = ['src/knowledge_tracing/gkt/' + n for n in ('training_data.py', 'pipeline.py', 'adapter.py',
    'training_checkpoint.py', 'training.py', 'recurrent.py', 'core.py', 'config.py', '__init__.py')]
names += ['src/knowledge_tracing/shared_kt.py', 'src/knowledge_tracing/simulator_bridge.py',
          'src/knowledge_tracing/simulator_data.py', 'tests/gkt/test_pipeline.py']
before = {n: sha(ROOT / n) for n in names}
for n in names:
    shutil.copyfile(ROOT / n, directory / (n.replace('/', '__') + '.before'))
if args.phase == 'pure01':
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B', '-m', 'pytest', 'tests/gkt/test_pipeline.py',
        '-q', '-p', 'no:cacheprovider', '--basetemp', str(directory / 'tmp'), '--junitxml', str(directory / 'pytest.xml')]
else:
    command = [str(ROOT / '.venv/Scripts/python.exe'), '-B', str(PREP / 'model_phase.py'),
        '--output', str(directory / 'output'), '--remaining-seconds', str(max(1, remaining - 2)),
        '--parent-approval-reference', args.parent_approval_reference]
env = os.environ.copy(); env.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2',
    OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'))
start = time.perf_counter(); wall = time.time(); timed_out = False
with (directory / 'stdout.log').open('xb') as stdout, (directory / 'stderr.log').open('xb') as stderr:
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=remaining)
        rc = result.returncode
    except subprocess.TimeoutExpired:
        rc = None; timed_out = True
elapsed = time.perf_counter() - start; wall_elapsed = time.time() - wall
after = {n: sha(ROOT / n) for n in names}
for n in names:
    shutil.copyfile(ROOT / n, directory / (n.replace('/', '__') + '.after'))
counts = None
if (directory / 'pytest.xml').exists():
    suites = list(ET.parse(directory / 'pytest.xml').iter('testsuite'))
    counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
event_path = directory / 'output/optimizer_events.jsonl'
events = [json.loads(line) for line in event_path.read_text().splitlines()] if event_path.exists() else []
reserved = sum(x['event'] == 'step_started' for x in events)
returned = sum(x['event'] == 'step_returned' for x in events)
budget['actual_controller_seconds'] += max(elapsed, wall_elapsed)
budget['optimizer_updates'] += reserved
budget['attempts'].append(dict(phase=args.phase, elapsed_seconds=elapsed, returncode=rc, reserved_updates=reserved, returned_updates=returned))
row = dict(phase=args.phase, command=command, returncode=rc, timeout=timed_out, timeout_seconds=remaining,
    controller_elapsed_seconds=elapsed, controller_wall_seconds=wall_elapsed, counts=counts,
    source_before=before, source_after=after, sources_unchanged=before == after,
    reserved_updates=reserved, returned_updates=returned, cumulative_reserved_updates=budget['optimizer_updates'],
    cumulative_conservative_seconds=budget['actual_controller_seconds'] + budget['reserved_static_seconds'])
row['resource_accepted'] = (not timed_out and max(elapsed, wall_elapsed) <= remaining
    and row['cumulative_conservative_seconds'] <= 60 and row['cumulative_reserved_updates'] <= 4)
with (directory / 'run.json').open('x', encoding='utf-8') as stream:
    json.dump(row, stream, indent=2); stream.write('\n')
with budget_path.open('w', encoding='utf-8') as stream:
    json.dump(budget, stream, indent=2); stream.write('\n')
print(json.dumps(row))
for name in ('stdout.log', 'stderr.log'):
    print('\n'.join((directory / name).read_text().splitlines()[-20:]))
