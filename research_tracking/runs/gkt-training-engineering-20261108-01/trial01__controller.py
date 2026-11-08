import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

root = Path.cwd()
out = Path(__file__).resolve().parent
files = ['src/knowledge_tracing/gkt/training.py', 'tests/gkt/test_training.py',
         'src/knowledge_tracing/gkt/recurrent.py', 'src/knowledge_tracing/gkt/core.py',
         'src/knowledge_tracing/gkt/config.py']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {n: sha(root / n) for n in files}
for n in files:
    shutil.copyfile(root / n, out / (n.replace('/', '__') + '.before'))
command = [str(root / '.venv/Scripts/python.exe'), '-B', '-m', 'pytest', 'tests/gkt/test_training.py',
           '-q', '-p', 'no:cacheprovider', '--basetemp', str(out / 'tmp'), '--junitxml', str(out / 'pytest.xml')]
env = os.environ.copy()
env.update(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
           PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(root / 'src'),
           GKT_TRAINING_UPDATE_LEDGER=str(out / 'optimizer-updates.jsonl'))
start = time.perf_counter(); wall = time.time(); timed_out = False
with (out / 'stdout.log').open('xb') as stdout, (out / 'stderr.log').open('xb') as stderr:
    try:
        proc = subprocess.run(command, cwd=root, env=env, stdout=stdout, stderr=stderr, timeout=59)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = None; timed_out = True
elapsed = time.perf_counter() - start; wall_elapsed = time.time() - wall
after = {n: sha(root / n) for n in files}
for n in files:
    shutil.copyfile(root / n, out / (n.replace('/', '__') + '.after'))
ledger = out / 'optimizer-updates.jsonl'
updates = len(ledger.read_text().splitlines()) if ledger.exists() else 0
row = dict(command=command, exit_code=rc, timed_out=timed_out,
    controller_elapsed_seconds=elapsed, controller_wall_seconds=wall_elapsed, cap_seconds=59,
    cumulative_total_cap_seconds=60, reserved_prior_controller_compile_diagnostic_seconds=1,
    resource_accepted=not timed_out and elapsed <= 59 and wall_elapsed <= 59,
    optimizer_updates=updates, optimizer_cap=8, source_before=before, source_after=after,
    sources_unchanged=before == after,
    log_sha256={p.name: sha(p) for p in out.iterdir() if p.is_file() and p.suffix in ('.log', '.xml', '.jsonl')},
    scope='tiny synthetic CPU train-batch engineering, no corpus/GPU/checkpoint/resume')
with (out / 'run.json').open('x', encoding='utf-8') as f:
    json.dump(row, f, indent=2); f.write('\n')
print(json.dumps(row))
print((out / 'stdout.log').read_text())
print((out / 'stderr.log').read_text())
