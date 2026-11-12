"""Đối chiếu receipt đã kiểm archive và metadata sáu epoch, không import Torch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/akt/results/modal-junyi-main-selected-t4-20261112-06'
receipt = json.loads((NATIVE/'receipt.json').read_text())
terminal = receipt['worker_result']['terminal']
verification = json.loads((BUNDLE/'execution06-verification.json').read_text())
previous = json.loads((BUNDLE/'execution04-verification.json').read_text())
assert receipt['download_inventory_verified'] is True
assert (NATIVE/'artifacts.zip').stat().st_size == receipt['archive_bytes'] == verification['archive_bytes']
assert receipt['archive_sha256'] == verification['archive_sha256']
assert terminal['history'][:4] == previous['validation_history']
assert [row['epoch'] for row in terminal['history']] == list(range(1, 7))
assert terminal['optimizer_steps'] == verification['optimizer_steps'] == 6*58166
assert terminal['trained_targets'] == verification['target_exposures'] == 6*13347331
assert verification['history'] == [[row['epoch'], row['validation']['native_bce']] for row in terminal['history']]
assert all(row['validation']['targets'] == 1600343 and row['validation']['oov'] == 0
           for row in terminal['history'])
assert terminal['selected_epoch'] is None
stop = json.loads((NATIVE/'independent-stop-confirmation.json').read_text())
assert stop['stop_acknowledged'] and stop['app']['state'] == 'stopped' and stop['app']['tasks'] == '0'
assert stop['app']['app_id'] == json.loads((NATIVE/'dispatch.json').read_text())['app_id']
print('PASS receipt, population counts, preserved history and independent stop. Archive hashes were checked by recovery script.')
