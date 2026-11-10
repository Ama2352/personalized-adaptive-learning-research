"""Gate CPU production đầy đủ trên venv đã nghiệm thu, không tự chạy CUDA."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

ROOT = Path('/content/kltn-isolated-cpu-20261110-01')
OUT = ROOT/'artifacts/akt/runtime/isolated-gate198-01'
PYTHON = ROOT/'.venv/bin/python'
LOCK = ROOT/'artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt'
RUN_ID = 'colab-isolated198-20261110-01'
installed = json.loads((ROOT/'artifacts/akt/runtime/isolated-install01/result.json').read_text())
assert installed['status'] == 'ISOLATED_LINUX_CPU_READY_NOT_CUDA'
assert installed['installed_packages'] == 44 and installed['base_pip_unchanged'] is True
assert not list(Path('/dev').glob('nvidia[0-9]*'))
OUT.mkdir(exist_ok=False)
env = dict(os.environ, PYTHONPATH=str(ROOT/'src'), PYTHONDONTWRITEBYTECODE='1',
    PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', CUDA_VISIBLE_DEVICES='',
    OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
env.pop('PYTEST_ADDOPTS', None)
env.pop('PYTEST_PLUGINS', None)
started = time.monotonic()
result = dict(status='FAILED', scope='Full isolated CPU software Gate only; no CUDA or training grant')
try:
    command = [str(PYTHON), '-B', str(ROOT/'scripts/akt/check_runtime.py'),
        '--upstream', str(ROOT/'artifacts/akt/dependencies/upstream'), '--device', 'cpu',
        '--lock-file', str(LOCK), '--output', str(OUT/'runtime.json')]
    with (OUT/'runtime.log').open('xb') as log:
        subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            timeout=45, check=True)
    runtime = json.loads((OUT/'runtime.json').read_text())
    assert runtime['available_ram_bytes'] >= 4*1024**3
    command = [str(PYTHON), '-B', str(ROOT/'scripts/akt/refresh_gate2.py'), '--run-id', RUN_ID,
        '--timeout-seconds', '600', '--lock-file', str(LOCK), '--publish-current']
    (OUT/'command.json').write_text(json.dumps(command, indent=2))
    with (OUT/'gate.log').open('xb') as log:
        subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            timeout=630, check=True)
    report = ROOT/'artifacts/akt/preflight'/('gate2-evidence-'+RUN_ID+'.json')
    evidence = json.loads(report.read_text())
    assert evidence['status'] == 'PASS' and all(evidence['test_result'][k] == 0 for k in ('failed','errors','skipped'))
    assert evidence['test_result']['passed'] > 0 and len(evidence['build_hashes']) == 198
    assert sum(len(g['modules']) for g in evidence['process_groups']) == 92
    result.update(status='FULL_ISOLATED_CPU_GATE_VERIFIED', test_result=evidence['test_result'],
        source_count=198, modules=92, report=str(report.relative_to(ROOT)),
        report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (OUT/'failure.log').write_text(traceback.format_exc())
finally:
    result['elapsed_seconds'] = time.monotonic()-started
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
