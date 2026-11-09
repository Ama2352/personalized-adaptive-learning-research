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
OUTPUT = WORK / 'paper1-pdf-domain-test01'
FILES = ('src/knowledge_tracing/paper1_pdf/__init__.py',
         'src/knowledge_tracing/paper1_pdf/simulator.py',
         'src/knowledge_tracing/paper1_pdf/domain.py',
         'tests/paper1_pdf/test_domain.py')

def pins():
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}

if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT/'.venv':
        raise ValueError('Chỉ dùng .venv repository')
    before = pins()
    OUTPUT.mkdir(exist_ok=False)
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests/paper1_pdf', '-p', 'test_domain.py', '-v']
    temporary_root = WORK/'paper1-domain-fixture-temp'
    temporary_root.mkdir(exist_ok=True)
    if not temporary_root.resolve().is_relative_to(ROOT) or temporary_root.is_symlink():
        raise ValueError('Owned temporary root must stay inside workspace')
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT/'src'),
                       TEMP=str(temporary_root), TMP=str(temporary_root))
    start = time.perf_counter()
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=30)
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
    result = dict(status='ACCEPTED_SYNTHETIC_PRIMITIVES' if accepted else 'REJECTED',
                  command=command, returncode=returncode, timeout=timeout, cap_seconds=30,
                  elapsed_seconds=elapsed, tests=tests, source_before=before, source_after=after,
                  scope_vi='Kiểm quy tắc primitives trên fixture. Chưa tái lập matrix hoặc chứng minh RQ.')
    (OUTPUT/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
