"""Một child kiểm stdlib20s, lưu log và giữ failure nếu có."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'main-selection-population-integration02-dispatch'
out.mkdir(exist_ok=False)
worker = prep / 'check_population_integration02.py'
paths = [worker, root / 'src/knowledge_tracing/research_population.py',
         root / 'tests/shared_kt/test_research_population.py']
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
before = {path.relative_to(root).as_posix(): sha(path) for path in paths}
assert Path(sys.prefix).resolve() == root / '.venv'
start = time.perf_counter()
process = subprocess.run([sys.executable, '-B', str(worker)], cwd=root, capture_output=True, timeout=20)
assert len(process.stdout) + len(process.stderr) <= 262144
(out / 'stdout.log').write_bytes(process.stdout)
(out / 'stderr.log').write_bytes(process.stderr)
after = {path.relative_to(root).as_posix(): sha(path) for path in paths}
result = dict(returncode=process.returncode, elapsed_seconds=time.perf_counter() - start,
    timeout_seconds=20, source_before=before, source_after=after, source_unchanged=before == after)
(out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
print(process.stdout.decode('utf-8', errors='replace'))
if process.returncode:
    print(process.stderr.decode('utf-8', errors='replace'))
raise SystemExit(process.returncode or int(before != after))
