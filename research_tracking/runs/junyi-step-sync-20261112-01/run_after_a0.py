"""Một phép đo hữu hạn sau A0, kiểm dừng và tránh hai GPU KLTN đồng thời."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
PREVIOUS = ROOT/'experiments/akt/results/modal-junyi-main-selected-t4-20261112-06'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
started = time.monotonic()
ready = False
with (BUNDLE/'wait-for-a0.jsonl').open('x', encoding='utf-8') as log:
    while time.monotonic() - started < 2100:
        receipt_path = PREVIOUS/'receipt.json'
        guard_path = PREVIOUS/'app-budget-guard.json'
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if receipt['status'] == 'FAILED':
                raise RuntimeError('Review previous run failure before any GPU profile')
            guard = json.loads(guard_path.read_text())
            ready = receipt.get('download_inventory_verified') is True and guard.get('stop_acknowledged') is True
        log.write(json.dumps(dict(ready=ready, elapsed_seconds=time.monotonic()-started))+'\n')
        log.flush()
        if ready:
            break
        time.sleep(30)
if not ready:
    raise TimeoutError('No profile dispatched because A0 stop was not verified')
listed = subprocess.run([sys.executable, '-B', '-m', 'modal', 'container', 'list', '--json'],
                        capture_output=True, text=True, check=True, timeout=30)
containers = json.loads(listed.stdout)
assert not any('kltn' in row['app_name'] for row in containers), 'Owned container still running'
(BUNDLE/'dispatch-preflight.json').write_text(json.dumps(dict(
    status='PREVIOUS_ARTIFACT_VERIFIED_STOP_ACKNOWLEDGED_NO_OWNED_CONTAINER',
    previous_run=PREVIOUS.name, containers=containers), indent=2)+'\n', encoding='utf-8')
with (BUNDLE/'gpu-execution.log').open('xb') as log:
    result = subprocess.run([sys.executable, '-B', 'experiments/akt/modal_junyi_batch_probe.py',
        '--request', str(BUNDLE/'request.json'), '--gpu', 'T4', '--run'],
        cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
assert result.returncode == 0, 'Profile failed, preserve evidence and review before retry'
print('Bounded GPU profile completed. Independent artifact and performance review required.', flush=True)
