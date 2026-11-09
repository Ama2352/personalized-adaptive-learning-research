"""Root chạy synthetic unittest PDF primitives, giới hạn30giây, không training."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
WORK = Path(__file__).resolve().parent
OUTPUT = WORK / 'reference-mixture-pure01'
FILES = ('artifacts/akt/local-tests/akt-research-runner-20261108-01/analyze_rq1_reference_mixture01.py',
         'artifacts/akt/local-tests/akt-research-runner-20261108-01/test_rq1_reference_mixture01.py',
         'artifacts/akt/local-tests/akt-research-runner-20261108-01/rq1_reference_mixture_contract01.json')

def pins():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}

if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT/'.venv':
        raise ValueError('Chỉ dùng .venv repository')
    before = pins()
    OUTPUT.mkdir(exist_ok=False)
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(WORK), '-p', 'test_rq1_reference_mixture01.py', '-v']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT/'src'))
    start = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=10)
        stdout, stderr = completed.stdout, completed.stderr
        returncode = completed.returncode
        timeout = False
    except subprocess.TimeoutExpired as error:
        stdout, stderr = error.stdout or b'', error.stderr or b''
        returncode = None
        timeout = True
    (OUTPUT/'stdout.log').write_bytes(stdout)
    (OUTPUT/'stderr.log').write_bytes(stderr)
    elapsed = time.perf_counter()-start
    after = pins()
    match = re.search(rb'Ran (\d+) tests?', stderr)
    tests = int(match.group(1)) if match else 0
    accepted = returncode == 0 and not timeout and tests > 0 and b'\nOK\n' in stderr.replace(b'\r\n', b'\n') and before == after
    result = dict(status='ACCEPTED_REFERENCE_MIXTURE_PURE' if accepted else 'REJECTED',
                  command=command, returncode=returncode, timeout=timeout, cap_seconds=10,
                  elapsed_seconds=elapsed, tests=tests, source_before=before, source_after=after,
                  scope_vi='Kiểm manufactured fixtures. Chưa phân tích cache hoặc chứng minh RQ.')
    (OUTPUT/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
