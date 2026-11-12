"""Lấy VRAM/GPU/CPU/RAM từ đúng container của lượt đang chạy."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/akt/results/modal-junyi-batch-utilization-t4-20261112-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
dispatch = json.loads((NATIVE/'dispatch.json').read_text())
started = time.monotonic()
with (BUNDLE/'live-resource-observer-wait.jsonl').open('x') as log:
    while time.monotonic()-started < 180:
        guard = json.loads((NATIVE/'app-budget-guard.json').read_text())
        if guard.get('stop_acknowledged'):
            print('Previous App stopped before resource observation.', flush=True)
            break
        result = subprocess.run([sys.executable, '-B', '-m', 'modal', 'container', 'list', '--json'],
                                capture_output=True, text=True, check=True, timeout=20)
        owned = [row for row in json.loads(result.stdout) if row['app_id'] == dispatch['app_id']]
        log.write(json.dumps(dict(elapsed=time.monotonic()-started, containers=owned))+'\n')
        log.flush()
        if owned:
            assert len(owned) == 1
            (BUNDLE/'live-resource-binding.json').write_text(json.dumps(owned[0], indent=2)+'\n')
            source = (BUNDLE/'collect_live_resources.py').read_text(encoding='utf-8')
            with (BUNDLE/'live-resources.jsonl').open('xb') as output:
                result = subprocess.run([sys.executable, '-B', '-m', 'modal', 'container', 'exec',
                    '--no-pty', owned[0]['container_id'], '--', '/opt/kltn/.venv/bin/python',
                    '-B', '-c', source, NATIVE.name], stdout=output, stderr=subprocess.STDOUT, timeout=150)
            assert result.returncode == 0, 'Keep diagnostic log, resource observation incomplete'
            print('Completed live resource sample.', flush=True)
            break
        time.sleep(5)
    else:
        print('No container assigned during bounded observation.', flush=True)
