"""Kiểm hồi quy nhỏ với trần RAM/thời gian, chỉ dữ liệu tổng hợp."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
temporary = ROOT/'artifacts/akt/runtime/a1-compact-adapter-tests-20261113-01'
temporary.mkdir(parents=True, exist_ok=True)
environment = dict(os.environ, PYTHONPATH=str(ROOT/'src'),
    PYTHONDONTWRITEBYTECODE='1', TEMP=str(temporary), TMP=str(temporary),
    OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
    GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory',
    GIT_CONFIG_VALUE_0=(ROOT/'artifacts/akt/dependencies/upstream').as_posix())
command = [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
    '--basetemp', str(temporary/'pytest'),
    'tests/akt/test_junyi_compact_context.py', 'tests/akt/test_junyi_graph_model.py',
    'tests/akt/test_a1_vector_residual.py', 'tests/akt/test_research_graph_model.py']
receipt = dict(command=command, max_seconds=240, max_rss_bytes=1024**3,
               peak_rss_bytes=0, status='RUNNING')
started = time.monotonic()
with (HERE/'local-regression.log').open('x', encoding='utf-8') as stream:
    child = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stream,
                             stderr=subprocess.STDOUT)
    process = psutil.Process(child.pid)
    while child.poll() is None:
        try:
            rss = sum(p.memory_info().rss for p in [process]+process.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            rss = 0
        receipt['peak_rss_bytes'] = max(receipt['peak_rss_bytes'], rss)
        if rss > receipt['max_rss_bytes'] or time.monotonic()-started > receipt['max_seconds']:
            receipt['status'] = 'STOPPED_RESOURCE_LIMIT'
            for owned in process.children(recursive=True):
                owned.terminate()
            child.terminate()
            break
        time.sleep(.2)
    receipt['exit_code'] = child.wait(timeout=10)
if receipt['status'] == 'RUNNING':
    receipt['status'] = 'PASS' if receipt['exit_code']==0 else 'FAILED_PRESERVED'
receipt['elapsed_seconds'] = time.monotonic()-started
(HERE/'local-regression.json').write_text(json.dumps(receipt,indent=2)+'\n', encoding='utf-8')
print(json.dumps(receipt))
raise SystemExit(0 if receipt['status']=='PASS' else 1)
