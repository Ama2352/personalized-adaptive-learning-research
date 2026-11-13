"""Tiếp tục các tranche CPU hữu hạn, giữ log và dừng ngay khi lỗi khác timeout spool."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'artifacts/akt/confidence/full-train80-20261114-02'
REQUEST = BUNDLE / 'request.json'


def run(action, seconds, rss):
    log = BUNDLE / (action + '-' + str(time.time_ns()) + '.log')
    args = [sys.executable, '-u', '-B', str(ROOT/'scripts/akt/fit_junyi_confidence.py'),
        '--request', str(REQUEST), '--output', str(OUTPUT), '--action', action,
        '--max-seconds', str(seconds), '--max-rss-mib', str(rss), '--max-rows', '1000000']
    with log.open('xb') as stream:
        result = subprocess.run(args, cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                                stdout=stream, stderr=subprocess.STDOUT)
    print(json.dumps(dict(action=action, code=result.returncode, log=log.name)), flush=True)
    return result.returncode, log.read_text(encoding='utf-8', errors='replace')


def main():
    # Tối đa ba tranche spool, mỗi tranche một giờ, có watchdog RAM/thời gian của CLI.
    for _ in range(3):
        if (OUTPUT/'SPOOL_COMPLETE.json').exists():
            break
        code, log = run('spool', 3600, 448)
        if code and 'Hết tranche CPU spool' not in log and 'Junyi confidence preparation time cap' not in log:
            raise RuntimeError('Lỗi spool khác timeout dự kiến, dừng để kiểm evidence')
    if not (OUTPUT/'SPOOL_COMPLETE.json').exists():
        raise TimeoutError('Chưa đủ spool sau ba tranche, giữ checkpoint')
    code, _ = run('fit-all', 3600, 768)
    if code:
        raise RuntimeError('Fit child gặp lỗi/cap, giữ các child COMPLETE và dừng để chẩn đoán')
    code, _ = run('finalize', 300, 768)
    if code:
        raise RuntimeError('Finalize chưa đạt, không công bố training sẵn sàng')
    print((OUTPUT/'COMPLETE.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
