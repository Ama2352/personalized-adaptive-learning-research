"""Chờ checkpoint mới rồi đọc GPU của đúng App06, không tạo cloud job."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
RUN = 'modal-junyi-main-selected-t4-20261112-06'
NATIVE = ROOT / 'experiments/akt/results' / RUN
os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
import modal

volume = modal.Volume.from_name('kltn-akt-modal-junyi-main-selected-t4-20261112-01')
started = time.monotonic()
ready = False
with (BUNDLE / 'gpu-telemetry06-wait.jsonl').open('x', encoding='utf-8') as log:
    while time.monotonic() - started < 900:
        if (NATIVE / 'receipt.json').exists() or (NATIVE / 'preemption-receipt.json').exists():
            raise RuntimeError('Execution ended before stable training observation')
        try:
            raw = b''.join(volume.read_file(RUN + '/checkpoint-index.json'))
            index = json.loads(raw)
            checkpoints = [tuple(map(int, match.groups())) for name in index
                           if (match := re.search(r'batch-epoch-(\d+)-step-(\d+)-', name))]
            latest = max(checkpoints, default=(0, 0))
            ready = latest[0] == 5 and latest[1] >= 41000
            event = dict(status='READY' if ready else 'WAITING', latest_epoch_step=latest,
                         elapsed_seconds=time.monotonic() - started)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            event = dict(status='WAITING', error_type=type(error).__name__,
                         elapsed_seconds=time.monotonic() - started)
        log.write(json.dumps(event) + '\n')
        log.flush()
        if ready:
            break
        time.sleep(15)
if not ready:
    raise TimeoutError('Stable observation wait exhausted')
dispatch = json.loads((NATIVE / 'dispatch.json').read_text())
listed = subprocess.run([sys.executable, '-B', '-m', 'modal', 'container', 'list', '--json'],
                        capture_output=True, text=True, check=True, timeout=30)
containers = [row for row in json.loads(listed.stdout) if row['app_id'] == dispatch['app_id']]
if len(containers) != 1:
    raise RuntimeError('Exactly one owned running container required')
source_path = BUNDLE / 'collect_gpu_telemetry06.py'
source = source_path.read_text(encoding='utf-8')
binding = dict(status='OWNED_RUNNING_CONTAINER_BOUND', run=RUN, container=containers[0],
               source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
               checkpoint_before_observation=latest)
(BUNDLE / 'gpu-telemetry06-binding.json').write_text(
    json.dumps(binding, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (BUNDLE / 'gpu-telemetry06.log').open('xb') as log:
    subprocess.run([sys.executable, '-B', '-m', 'modal', 'container', 'exec', '--no-pty',
                    containers[0]['container_id'], '--', '/opt/kltn/.venv/bin/python',
                    '-B', '-c', source, RUN], stdout=log, stderr=subprocess.STDOUT,
                   check=True, timeout=100)
print(json.dumps(binding), flush=True)
