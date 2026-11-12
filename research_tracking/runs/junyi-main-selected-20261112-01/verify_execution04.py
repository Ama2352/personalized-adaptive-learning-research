"""Nghiệm thu execution04 từ archive, không nạp Torch hoặc chạy mô hình."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT / 'experiments/akt/results/modal-junyi-main-selected-t4-20261112-04'
receipt = json.loads((NATIVE / 'receipt.json').read_text())
assert receipt['download_inventory_verified'] is True
assert receipt['status'] == 'PARTIAL_SELECTED_ONLY_NOT_FINAL'
assert json.loads((NATIVE / 'app-budget-guard.json').read_text())['stop_acknowledged'] is True
archive = NATIVE / 'artifacts.zip'
with archive.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest == receipt['archive_sha256'] and archive.stat().st_size == receipt['archive_bytes']
terminal = receipt['worker_result']['terminal']
previous = json.loads((ROOT / 'experiments/akt/results/modal-junyi-main-selected-t4-20261112-03/receipt.json').read_text())
history = terminal['history']
assert history[:3] == previous['worker_result']['terminal']['history']
assert [row['epoch'] for row in history] == [1, 2, 3, 4]
assert all(row['validation']['targets'] == row['validation']['supported'] == 1600343
           and row['validation']['oov'] == 0 for row in history)
assert len({row['validation']['population_sha256'] for row in history}) == 1
assert terminal['selected_epoch'] is None and terminal['external_freeze'] is False
assert receipt['worker_result']['refit_completed'] is False
epochs = []
with zipfile.ZipFile(archive) as saved:
    inventory = json.loads(saved.read('SHA256.json'))
    for name in saved.namelist():
        if name.endswith('-training.json'):
            raw = saved.read(name)
            assert hashlib.sha256(raw).hexdigest() == inventory[name]['sha256']
            stats = json.loads(raw)
            number = int(Path(name).name.split('-')[1])
            epochs.append(dict(epoch=number, complete=stats['complete'],
                targets=stats['valid_targets'], optimizer_steps=stats['optimizer_steps'],
                train_seconds=stats['resource']['wall_seconds'], archive_member=name))
epochs.sort(key=lambda row: row['epoch'])
assert [row['epoch'] for row in epochs] == [4, 5]
assert epochs[0]['complete'] is True and epochs[0]['targets'] == 13347331
assert epochs[0]['optimizer_steps'] == 58166
assert epochs[1]['complete'] is False and epochs[1]['optimizer_steps'] == 39488
assert terminal['optimizer_steps'] == 4 * 58166 + epochs[1]['optimizer_steps']
assert terminal['trained_targets'] == 4 * 13347331 + epochs[1]['targets']
assert 'epoch-004' in receipt['checkpoint_transfers']
assert any(name.startswith('inner-batch-epoch-5-step-39488-') for name in receipt['checkpoint_transfers'])
result = dict(status='VERIFIED_FOUR_VALIDATED_EPOCHS_PARTIAL_FIFTH',
    archive_sha256=digest, archive_bytes=archive.stat().st_size,
    app_stop_acknowledged=True, preserved_previous_validation_history=True,
    epochs_in_execution=epochs, validation_history=history,
    optimizer_steps=terminal['optimizer_steps'], trained_target_exposures=terminal['trained_targets'],
    selected_epoch_final=None, refit_complete=False, calibration_complete=False,
    limits_vi='Log Loss selection phục vụ chọn epoch, chưa đánh giá độc lập. '
              'Giữ provenance metadata khởi tạo đã tái dựng từ execution01.')
target = BUNDLE / 'execution04-verification.json'
raw = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
if target.exists():
    assert target.read_text(encoding='utf-8') == raw
else:
    target.write_text(raw, encoding='utf-8')
print(json.dumps(dict(status=result['status'], epochs=epochs,
                      validation4=history[3]['validation']['native_bce']), ensure_ascii=False))
