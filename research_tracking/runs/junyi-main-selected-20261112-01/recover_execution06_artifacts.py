"""Xác nhận dừng độc lập rồi tải archive đã tạo, không cấp GPU."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT/'experiments/akt/results/modal-junyi-main-selected-t4-20261112-06'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
import modal

receipt = json.loads((NATIVE/'remote-receipt.json').read_text())
dispatch = json.loads((NATIVE/'dispatch.json').read_text())
def query(surface):
    result = subprocess.run([sys.executable, '-B', '-m', 'modal', surface, 'list', '--json'],
                            capture_output=True, text=True, check=True, timeout=30)
    return json.loads(result.stdout)
matches = [row for row in query('app') if row['app_id'] == dispatch['app_id']]
assert len(matches) == 1 and matches[0]['state'] == 'stopped' and matches[0]['tasks'] in (0, '0')
containers = query('container')
assert not any(row['app_id'] == dispatch['app_id'] for row in containers)
confirmation = dict(stop_acknowledged=True, app=matches[0], containers=containers,
                    observed_at_utc=datetime.now(timezone.utc).isoformat(),
                    original_guard_preserved=True, confirmation='independent_server_state_after_guard_failure')
(NATIVE/'independent-stop-confirmation.json').write_text(json.dumps(confirmation, indent=2)+'\n')
archive = NATIVE/'artifacts.zip'
volume = modal.Volume.from_name('kltn-akt-modal-junyi-main-selected-t4-20261112-01')
with archive.open('xb') as stream:
    for block in volume.read_file(NATIVE.name+'/artifacts.zip'):
        stream.write(block)
assert archive.stat().st_size == receipt['archive_bytes']
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['archive_sha256']
with zipfile.ZipFile(archive) as saved:
    assert saved.testzip() is None
    inventory = json.loads(saved.read('SHA256.json'))
    assert set(saved.namelist()) == set(inventory) | {'SHA256.json'}
    for name, entry in inventory.items():
        with saved.open(name) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
receipt.update(download_inventory_verified=True, independent_stop_confirmation=confirmation,
               recovery='download_only_after_guard_stop_confirmation_failure')
(NATIVE/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'], archive_bytes=archive.stat().st_size,
                      download_inventory_verified=True, independent_stop_acknowledged=True)), flush=True)
