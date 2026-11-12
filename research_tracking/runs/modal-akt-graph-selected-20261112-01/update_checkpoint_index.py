"""Cập nhật chỉ mục checkpoint từ receipt thật, không nạp tensor hoặc gọi cloud."""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
allocation = json.loads((BUNDLE / 'allocation.json').read_text())
runs = [('A0', 'modal-main60-a0-selected-20261112-01')]
for candidate, name in allocation['candidate_requests'].items():
    request = json.loads((BUNDLE / name).read_text())
    runs.append((candidate, request['run_id']))
entries = []
for candidate, run_id in runs:
    native = ROOT / 'experiments/akt/results' / run_id
    receipt_path = native / 'receipt.json'
    entry = dict(candidate_id=candidate, run_id=run_id, environment='grade10_simulator',
                 phase='selected_fit80', status='PREPARED', native_directory=str(native.relative_to(ROOT)).replace('\\', '/'))
    if (native / 'dispatch.json').exists():
        entry['status'] = 'DISPATCHED'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        entry['status'] = receipt['status']
        if receipt.get('download_inventory_verified') and receipt.get('terminal'):
            terminal = receipt['terminal']
            epoch = terminal['selected_epoch']
            state = terminal['checkpoint']
            entry.update(selected_epoch=epoch, completed_epochs=terminal['complete_fit_epochs'],
                archive=entry['native_directory'] + '/artifacts.zip', archive_sha256=receipt['archive_sha256'],
                selected_checkpoint=dict(
                    archive_member_directory=f'experiments/akt/results/{run_id}/checkpoints/epoch-{epoch}',
                    state_sha256=state['checkpoint_sha256'], metadata_sha256=state['metadata_sha256'],
                    complete_sha256=state['complete_sha256'],
                    volume_name='kltn-akt-' + run_id,
                    volume_directory=f'{run_id}/checkpoints/epoch-{epoch}'),
                saved_epochs=list(receipt['checkpoint_transfers']),
                gpu_name=receipt['worker_result'].get('gpu_name', 'Chưa ghi tên GPU trong worker A0'),
                calibration_used_for_selection=False, refit_complete=False)
    entries.append(entry)
index = dict(updated_at_utc=datetime.now(timezone.utc).isoformat(), entries=entries,
    instructions='Checkpoint local đang nằm trong archive. Dùng đúng member_directory để trích ba file state.pt, metadata.json, COMPLETE.json và đối chiếu SHA trước khi nạp. Volume directory là bản dự phòng cloud.',
    limits='Đây là selected checkpoints. Chưa có final refit90/calibration hoặc kết quả Junyi trong chỉ mục này.')
(BUNDLE / 'checkpoint-index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps([(entry['candidate_id'], entry['status']) for entry in entries]))
