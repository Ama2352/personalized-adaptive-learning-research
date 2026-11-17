"""Kiểm image CPU thật sau thêm wrapper audit, chưa đọc dataset/model."""
import hashlib
import json
import os
from pathlib import Path
import sys
import warnings

ROOT = Path.cwd()
B = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
sys.path[:0] = [str(ROOT/'scripts/akt'), str(ROOT/'src')]
import modal
from modal_junyi_calibration import create_app

app, functions = create_app()
with modal.enable_output(), app.run(environment_name='main'):
    result = functions['preflight'].remote()
assert result['source_identity'] == json.loads((B/'REQUEST_A0_GPU01.json').read_text())['source_identity']
for name, pin in result['worker_sources'].items():
    assert hashlib.sha256((ROOT/'scripts/akt'/name).read_bytes()).hexdigest() == pin, name
with (B/'PREFLIGHT07.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print('PREFLIGHT_TRANSACTION_WRAPPER_SOURCE_FROZEN_KT_PASS', flush=True)
