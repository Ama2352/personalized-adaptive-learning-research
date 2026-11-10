"""Một child unittest stdlib, timeout10s, giữ output thật và scope fixture."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'main-selection-file-primitives-tests01'
out.mkdir(exist_ok=False)
pins = {'main_selection_file_primitives_candidate01.py': '2b7016f7d9a8b4b295d44d95e8eb1f39c1d4054dcb46bac25f8d875d62d8b335',
        'test_main_selection_file_primitives_candidate01.py': 'e2b2de67a468a076aef2a340c5eeaec291e60cdab0131e99bcaac52ea5dd40e9'}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert Path(sys.prefix).resolve() == root / '.venv'
assert all(sha(prep / name) == pin for name, pin in pins.items())
code = """import sys, unittest, json
sys.path[:0]=['src','artifacts/akt/local-tests/akt-research-runner-20261108-01']
import test_main_selection_file_primitives_candidate01 as tests
suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
assert suite.countTestCases()==9
result=unittest.TextTestRunner(verbosity=2).run(suite)
heavy=sorted(set(sys.modules)&{'torch','numpy','pandas','scipy','sklearn','modal','boto3'})
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'heavy_imports':heavy}))
raise SystemExit(0 if result.wasSuccessful() and not result.skipped and not heavy else 1)
"""
start = time.perf_counter()
workspace = out / 'workspace'
workspace.mkdir()
environment = dict(os.environ, TEMP=str(workspace), TMP=str(workspace), TMPDIR=str(workspace))
result = subprocess.run([sys.executable, '-B', '-c', code], cwd=root, env=environment, capture_output=True, timeout=20)
(out / 'stdout.log').write_bytes(result.stdout)
(out / 'stderr.log').write_bytes(result.stderr)
after = {name: sha(prep / name) for name in pins}
record = {'returncode': result.returncode, 'elapsed_seconds': time.perf_counter() - start,
          'timeout_seconds': 20, 'source_before': pins, 'source_after': after,
          'source_unchanged': after == pins,
          'scope_vi': 'Sáu unittest manufactured fixtures, không đọc corpus/model hoặc nghiệm thu freeze/refit.'}
(out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
print(result.stdout.decode('utf-8', errors='replace'))
raise SystemExit(0 if result.returncode == 0 and after == pins else 1)
