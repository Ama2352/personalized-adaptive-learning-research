"""Một child unittest stdlib, timeout10s, giữ output thật và scope fixture."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'a1-resource-wait-guard-canaries02'
out.mkdir(exist_ok=False)
pins = {'check_a1_expert_engineering03.py': 'a6fa2e3838d27e288ad1be8ecb33058ef3f7062c0258b4d8b3fb6c765038cc42',
        'test_a1_resource_wait_guard01.py': '7f7715c74c7bea80abc9d02ca9f61e6c4a0795f12ec764bd0fc9a78f4320311a'}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert Path(sys.prefix).resolve() == root / '.venv'
assert all(sha(prep / name) == pin for name, pin in pins.items())
code = """import sys, unittest, json
sys.path[:0]=['src','artifacts/akt/local-tests/akt-research-runner-20261108-01']
import test_a1_resource_wait_guard01 as tests
suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
assert suite.countTestCases()==9
result=unittest.TextTestRunner(verbosity=2).run(suite)
heavy=sorted(set(sys.modules)&{'torch','numpy','pandas','scipy','sklearn','modal','boto3'})
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'heavy_imports':heavy}))
raise SystemExit(0 if result.wasSuccessful() and not result.skipped and not heavy else 1)
"""
start = time.perf_counter()
result = subprocess.run([sys.executable, '-B', '-c', code], cwd=root, capture_output=True, timeout=5)
(out / 'stdout.log').write_bytes(result.stdout)
(out / 'stderr.log').write_bytes(result.stderr)
after = {name: sha(prep / name) for name in pins}
record = {'returncode': result.returncode, 'elapsed_seconds': time.perf_counter() - start,
          'timeout_seconds': 5, 'source_before': pins, 'source_after': after,
          'source_unchanged': after == pins,
          'scope_vi': 'Chín unittest cho resource guard, chỉ fixture WinAPI, không đọc corpus/model.'}
(out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False))
print(result.stdout.decode('utf-8', errors='replace'))
raise SystemExit(0 if result.returncode == 0 and after == pins else 1)
