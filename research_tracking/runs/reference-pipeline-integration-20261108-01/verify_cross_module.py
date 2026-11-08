"""Một lượt kiểm tích hợp local hữu hạn, không model hoặc environment training."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

root = Path.cwd()
target = root / 'artifacts/akt/local-tests/reference-controller-v1-20261108-01/cross-module01'
target.mkdir(exist_ok=False)
names = ['simulator_research_data', 'simulator_data', 'response_calibration',
         'reference_controller', 'simulator_bridge']
sources = [root / f'src/knowledge_tracing/{name}.py' for name in names]
tests = [root / f'tests/shared_kt/test_{name}.py' for name in names]
sources += tests + [root / 'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md']
def inventory():
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
before = inventory()
(target / 'sources_before.json').write_text(json.dumps(before, indent=2) + '\n', encoding='utf-8')
argv = [str(root / '.venv/Scripts/python.exe'), '-B', '-m', 'pytest']
argv += [str(path.relative_to(root)) for path in tests]
argv += ['-q', '-p', 'no:cacheprovider', '--basetemp', str(target / 'temp'), '--junitxml', str(target / 'pytest.xml')]
env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=str(root / 'src'),
           CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
started = time.monotonic()
error = None
try:
    with (target / 'stdout.log').open('wb') as stream:
        result = subprocess.run(argv, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=30)
    returncode = result.returncode
except subprocess.TimeoutExpired:
    error, returncode = 'TIMEOUT_NO_RETRY', None
elapsed = time.monotonic() - started
after = inventory()
counts = {}
if (target / 'pytest.xml').exists():
    suite = ET.parse(target / 'pytest.xml').getroot().find('testsuite')
    counts = {key: int(suite.attrib[key]) for key in ('tests', 'errors', 'failures', 'skipped')}
accepted = (returncode == 0 and error is None and elapsed <= 30 and before == after
            and counts.get('tests', 0) > 0 and all(counts.get(key) == 0 for key in ('errors', 'failures', 'skipped')))
receipt = dict(status='PASS' if accepted else 'STOP', command=argv, counts=counts,
               elapsed_seconds=elapsed, cap_seconds=30, returncode=returncode, error=error,
               source_before=before, source_after=after, source_unchanged=before == after,
               scope='synthetic contracts and calibration/controller integration; no research efficacy',
               neural_optimizer_steps=0, remote_or_cloud_spending=False)
(target / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: receipt[k] for k in ('status', 'counts', 'elapsed_seconds', 'source_unchanged')}))
raise SystemExit(0 if accepted else 1)
