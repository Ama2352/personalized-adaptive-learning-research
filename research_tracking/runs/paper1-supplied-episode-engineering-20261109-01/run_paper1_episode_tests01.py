"""Root chạy bộ kiểm Paper1 gồm episode mới, giới hạn 30 giây trên .venv."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP / 'paper1-episode-tests01'
PINS = {
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'src/knowledge_tracing/paper1_pdf/domain.py': 'c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18',
    'src/knowledge_tracing/paper1_pdf/episode.py': 'e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471',
    'tests/paper1_pdf/test_simulator.py': '0810c04847a0461bcb2ed8ddf5cb17fda13ab90dca1709adc7bc16ee847c8a03',
    'tests/paper1_pdf/test_domain.py': '5443ff36d437c4ed9a758089a0114e6a5b4da1396a137ec5b7ec5e4b16e9afdb',
    'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
    'tests/paper1_pdf/test_episode.py': 'd0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0',
}


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PINS}


if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT / '.venv' or hashes() != PINS:
        raise ValueError('Cần đúng .venv và source đã review')
    OUTPUT.mkdir(exist_ok=False)
    temporary = OUTPUT / 'temporary'
    temporary.mkdir()
    if temporary.resolve() != temporary or not temporary.is_relative_to(ROOT):
        raise ValueError('Temporary phải nằm trong workspace')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests/paper1_pdf', '-p', 'test_*.py', '-v']
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'),
                       TEMP=str(temporary), TMP=str(temporary), CUDA_VISIBLE_DEVICES='',
                       OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    start = time.perf_counter()
    timeout = False
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=30)
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
    accepted = (returncode == 0 and not timeout and elapsed < 30 and count == 72
                and b'\nOK\n' in stderr.replace(b'\r\n', b'\n') and after == PINS)
    result = dict(status='ACCEPTED_72_PAPER1_TESTS_WITH_18_EPISODE_CASES' if accepted else 'REJECTED',
                  command=command, returncode=returncode, timeout=timeout, tests=count, new_episode_cases=18,
                  elapsed_seconds=elapsed, cap_seconds=30, source_before=PINS, source_after=after,
                  scope_vi='Kiểm profile và episode supplied cùng regression Paper1. Dữ liệu dựng tay, chưa chạy matrix hoặc người học nghiên cứu.')
    (OUTPUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
