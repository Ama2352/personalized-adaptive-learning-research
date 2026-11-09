"""Một child unittest stdlib, timeout10s, giữ output thật và scope fixture."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'main-selection-population-tests01'
out.mkdir(exist_ok=False)
pins = {'main_selection_population_candidate01.py': '8709f62a4aeed14bb3bfd8581e419205a0e8695d7eb3312832c96d7b64ef1906',
        'test_main_selection_population_candidate01.py': 'ce9c8626193326ab2a43ebc65da81917b49f2139da3066885bf4e11005f66627'}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert Path(sys.prefix).resolve() == root / '.venv'
assert all(sha(prep / name) == pin for name, pin in pins.items())
code = """import sys, unittest, json
sys.path[:0]=['src','artifacts/akt/local-tests/akt-research-runner-20261108-01']
import test_main_selection_population_candidate01 as tests
suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
assert suite.countTestCases()==6
result=unittest.TextTestRunner(verbosity=2).run(suite)
heavy=sorted(set(sys.modules)&{'torch','numpy','pandas','scipy','sklearn','modal','boto3'})
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'heavy_imports':heavy}))
raise SystemExit(0 if result.wasSuccessful() and not result.skipped and not heavy else 1)
"""
start = time.perf_counter()
result = subprocess.run([sys.executable, '-B', '-c', code], cwd=root, capture_output=True, timeout=10)
(out / 'stdout.log').write_bytes(result.stdout)
(out / 'stderr.log').write_bytes(result.stderr)
after = {name: sha(prep / name) for name in pins}
record = {'returncode': result.returncode, 'elapsed_seconds': time.perf_counter() - start,
          'timeout_seconds': 10, 'source_before': pins, 'source_after': after,
          'source_unchanged': after == pins,
          'scope_vi': 'Sáu unittest manufactured fixtures, không đọc corpus/model hoặc nghiệm thu freeze/refit.'}
(out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
print(result.stdout.decode('utf-8', errors='replace'))
raise SystemExit(0 if result.returncode == 0 and after == pins else 1)
