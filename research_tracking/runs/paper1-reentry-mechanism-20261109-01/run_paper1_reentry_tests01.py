"""Root kiểm bốn tình huống cơ chế hữu hạn, lưu log và nguồn trước/sau."""
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
OUTPUT = PREP / 'paper1-reentry-mechanism-tests01'
PINS = {
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
}


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PINS}


if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT / '.venv' or hashes() != PINS:
        raise ValueError('Cần đúng .venv và source đã review')
    OUTPUT.mkdir(exist_ok=False)
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests/paper1_pdf',
               '-p', 'test_reentry_mechanism.py', '-v']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'),
                       CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    started = time.perf_counter()
    timeout = False
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=30)
        stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, returncode = error.stdout or b'', error.stderr or b'', None
        timeout = True
    elapsed = time.perf_counter() - started
    (OUTPUT / 'stdout.log').write_bytes(stdout)
    (OUTPUT / 'stderr.log').write_bytes(stderr)
    match = re.search(rb'Ran (\d+) tests?', stderr)
    count = int(match.group(1)) if match else 0
    after = hashes()
    accepted = (returncode == 0 and not timeout and elapsed < 30 and count == 4
                and b'\nOK\n' in stderr.replace(b'\r\n', b'\n') and after == PINS)
    result = dict(status='ACCEPTED_FOUR_REENTRY_MECHANISM_FIXTURES' if accepted else 'REJECTED',
                  command=command, returncode=returncode, timeout=timeout, tests=count,
                  elapsed_seconds=elapsed, cap_seconds=30, source_before=PINS, source_after=after,
                  scope_vi='Phản ví dụ và điều kiện đủ trên fixture nhỏ, gắn với chứng minh cấu trúc. Chưa chạy ma trận nghiên cứu.')
    (OUTPUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
