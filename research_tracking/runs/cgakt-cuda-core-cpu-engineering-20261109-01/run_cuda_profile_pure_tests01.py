"""Root kiểm metadata recipe CUDA bằng unittest, không import Torch."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP / 'cuda-profile-pure-tests01'
PINS = {
    'src/knowledge_tracing/akt/config.py': '472b1b08d5270a1f2f07b214d5bf2658443265400828f6d66d1a802c1f92083d',
    'tests/akt/test_research_cuda_profile.py': '65de544c73cbe56431e7c6fcc457c19021b323209ac32913a363f8dfcdf31c57',
}


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PINS}


if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT / '.venv' or hashes() != PINS:
        raise ValueError('Cần đúng .venv và source đã review')
    OUTPUT.mkdir(exist_ok=False)
    program = (
        'import sys, unittest; '
        "suite=unittest.TestLoader().discover('tests/akt', pattern='test_research_cuda_profile.py'); "
        'result=unittest.TextTestRunner(verbosity=2).run(suite); '
        "cold=not any(name in sys.modules for name in ('torch','numpy','pandas')); "
        "print({'scientific_modules_absent':cold,'physical_tests':result.testsRun}); "
        'raise SystemExit(0 if result.wasSuccessful() and result.testsRun==13 and cold else 1)'
    )
    command = [sys.executable, '-B', '-c', program]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'), CUDA_VISIBLE_DEVICES='')
    start = time.perf_counter()
    timeout = False
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=10)
        stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, returncode = error.stdout or b'', error.stderr or b'', None
        timeout = True
    elapsed = time.perf_counter() - start
    (OUTPUT / 'stdout.log').write_bytes(stdout)
    (OUTPUT / 'stderr.log').write_bytes(stderr)
    match = re.search(rb'Ran (\d+) tests?', stderr)
    count = int(match.group(1)) if match else 0
    after = hashes()
    accepted = (returncode == 0 and not timeout and elapsed < 10 and count == 13
                and b'\nOK\n' in stderr.replace(b'\r\n', b'\n') and after == PINS)
    result = dict(status='ACCEPTED_13_PURE_CUDA_PROFILE_TESTS' if accepted else 'REJECTED', tests=count,
                  command=command, returncode=returncode, timeout=timeout, elapsed_seconds=elapsed,
                  cap_seconds=10, source_before=PINS, source_after=after,
                  scope_vi='Metadata/config trên CPU host. Chưa kiểm actual CUDA hoặc mô hình.')
    (OUTPUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
