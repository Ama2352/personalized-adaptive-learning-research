"""Bộ điều khiển local: tổng thời gian các lượt kiểm thử không quá30giây."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
FILES = (
    'src/knowledge_tracing/response_calibration.py',
    'tests/shared_kt/test_response_calibration.py',
    'src/knowledge_tracing/reference_controller.py',
    'tests/shared_kt/test_reference_controller.py',
    'src/knowledge_tracing/simulator_bridge.py',
    'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md',
)


def dump(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def snapshot(folder):
    folder.mkdir()
    result = {}
    for name in FILES:
        payload = (ROOT / name).read_bytes()
        destination = folder / name.replace('/', '__')
        destination.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        assert hashlib.sha256(destination.read_bytes()).hexdigest() == digest
        result[name] = dict(sha256=digest, bytes=len(payload))
    dump(folder / 'inventory.json', result)
    return result


if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        snapshot(PREP / 'before')
    else:
        started = time.perf_counter()
        ledger_path = PREP / 'budget.json'
        previous = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
        spent = sum(row['controller_seconds'] for row in previous)
        remaining = 30.0 - spent
        if remaining <= .5:
            raise RuntimeError('cumulative30s exhausted')
        trial = PREP / sys.argv[1]
        trial.mkdir()
        before = snapshot(trial / 'source-before')
        command = [str(ROOT / '.venv/Scripts/python.exe'), '-m', 'pytest',
                   *sys.argv[2:], '-q', '-o', 'addopts=',
                   '--basetemp=' + str(trial / 'tmp'),
                   '--junitxml=' + str(trial / 'pytest.xml')]
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                   PYTEST_ADDOPTS='', CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='none',
                   OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
        timed_out = False
        with (trial / 'pytest.log').open('wb') as log:
            try:
                completed = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                           stderr=subprocess.STDOUT, timeout=remaining-.5)
                rc = completed.returncode
            except subprocess.TimeoutExpired:
                rc = None
                timed_out = True
        after = {name: dict(sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),
                            bytes=(ROOT/name).stat().st_size) for name in FILES}
        elapsed = time.perf_counter() - started
        result = dict(command=command, returncode=rc, timed_out=timed_out,
                      controller_seconds=elapsed, cumulative_seconds=spent+elapsed,
                      budget_seconds=30, source_before=before, source_after=after,
                      sources_unchanged=before == after, neural_network_calls=0,
                      optimizer_steps=0, remote_calls=0)
        dump(trial / 'run.json', result)
        previous.append(dict(trial=sys.argv[1], controller_seconds=elapsed, returncode=rc))
        ledger_path.write_text(json.dumps(previous, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k not in ('source_before','source_after','command')}))
        if elapsed+spent > 30 or before != after:
            raise RuntimeError('budget/source guard failed')
