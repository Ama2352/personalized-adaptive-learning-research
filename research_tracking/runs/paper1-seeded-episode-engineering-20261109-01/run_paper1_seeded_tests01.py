"""Root kiểm85trường hợp Paper1 bằng stdlib, một lượt tối đa30giây."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
OUTPUT = PREP / 'paper1-seeded-tests01'
PINS = {
    'src/knowledge_tracing/paper1_pdf/__init__.py': '0a9e0faa63680643c3526ce13135de2c033f105d82bf5ea8e7a55afdc2df7df7',
    'src/knowledge_tracing/paper1_pdf/simulator.py': 'b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f',
    'src/knowledge_tracing/paper1_pdf/domain.py': 'c37e32420c90f98289b9e21c2e6ea9197324f77a2452b7faae79f8c60985fb18',
    'src/knowledge_tracing/paper1_pdf/episode.py': 'e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471',
    'src/knowledge_tracing/paper1_pdf/seeded_episode.py': '7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2',
    'tests/paper1_pdf/test_simulator.py': '0810c04847a0461bcb2ed8ddf5cb17fda13ab90dca1709adc7bc16ee847c8a03',
    'tests/paper1_pdf/test_domain.py': '5443ff36d437c4ed9a758089a0114e6a5b4da1396a137ec5b7ec5e4b16e9afdb',
    'tests/paper1_pdf/test_reentry_mechanism.py': '365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074',
    'tests/paper1_pdf/test_episode.py': 'd0bf6e052d9e2618b0b2d3ecf729164da68d99fc49a42e4c6dc0eadf6b4db1c0',
    'tests/paper1_pdf/test_seeded_episode.py': 'f97674bc764988271c091a00560bf31f2afba2f951b72819a150ae64a83b48e2',
}


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in PINS}


if __name__ == '__main__':
    if Path(sys.prefix).resolve() != ROOT / '.venv' or hashes() != PINS:
        raise ValueError('Cần đúng .venv và10nguồn đã review')
    OUTPUT.mkdir(exist_ok=False)
    temporary = OUTPUT / 'temporary'
    temporary.mkdir()
    script = """import json, sys, unittest
suite = unittest.defaultTestLoader.discover('tests/paper1_pdf', pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
cold = not any(name in sys.modules for name in ('torch', 'numpy', 'pandas'))
print(json.dumps(dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
    skipped=len(result.skipped), scientific_modules_absent=cold)))
raise SystemExit(0 if result.wasSuccessful() and not result.skipped and result.testsRun == 85 and cold else 1)
"""
    command = [sys.executable, '-B', '-c', script]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'src'),
                       TEMP=str(temporary), TMP=str(temporary), CUDA_VISIBLE_DEVICES='',
                       OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    start = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, timeout=30)
        stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, returncode = error.stdout or b'', error.stderr or b'', None
        timed_out = True
    elapsed = time.perf_counter() - start
    (OUTPUT / 'stdout.log').write_bytes(stdout)
    (OUTPUT / 'stderr.log').write_bytes(stderr)
    observed = json.loads(stdout.decode().splitlines()[-1]) if stdout else None
    after = hashes()
    expected = dict(tests=85, failures=0, errors=0, skipped=0, scientific_modules_absent=True)
    accepted = returncode == 0 and not timed_out and elapsed < 30 and observed == expected and after == PINS
    result = dict(status='ACCEPTED85_PAPER1_CASES_WITH13_SEEDED_CASES' if accepted else 'REJECTED_KEEP_LOGS',
                  counts=observed, command=command, returncode=returncode, timeout=timed_out,
                  elapsed_seconds=elapsed, cap_seconds=30, new_seeded_cases=13,
                  source_before=PINS, source_after=after,
                  scope_vi='Bank dựng tay và hồi quy. Chưa actual domain pilot hoặc matrix nghiên cứu.')
    (OUTPUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                                      encoding='utf-8', newline='')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if accepted else 1)
