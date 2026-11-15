"""Modal refit dùng lại image CPU, budget guard, stop barrier và artifact IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

from modal_junyi_staged import ROOT, run, validate_resource_budget


def verify_final_epoch_timebox(request, worker):
    """Chỉ cho timebox ngắn ở phần cuối của refit đã có checkpoint kiểm đủ.

    Cấu hình và identity mô hình giữ nguyên. Deadline của controller được rút
    ngắn để giới hạn tiền lượt cuối. Nếu quá hạn, controller dừng process và
    giữ checkpoint phục hồi, không được tự tính hoàn tất hay tự chạy lại.
    """
    from junyi_staged_io import owned_input, sha

    if (request.get('final_epoch_timebox') is not True
            or not 300 <= request['child_timeout_seconds'] <= 600):
        raise ValueError('Timebox cuối cần phê chuẩn và deadline rõ ràng')
    previous_path = owned_input(ROOT, request['resume_inventory'])
    local_complete = json.loads((previous_path.parent / 'COMPLETE.json').read_text())
    stopped = json.loads((previous_path.parent / 'app-budget-guard.json').read_text())
    if (local_complete.get('status') != 'LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
            or stopped.get('stop_acknowledged') is not True):
        raise ValueError('Đợt trước phải dừng GPU và nghiệm thu artifact trên D')
    previous = json.loads(previous_path.read_text())
    terminal = previous.get('worker_result', {}).get('terminal', {})
    epochs = worker['frozen_epochs']
    if (previous.get('status') != 'PARTIAL_JUNYI_REFIT90'
            or terminal.get('complete_epochs') not in (epochs - 1, epochs - 2)
            or terminal.get('frozen_epochs') != epochs):
        raise ValueError('Chỉ cho timebox ngắn ở epoch refit cuối đã xác nhận')
    remote_checkpoint = owned_input(ROOT, request['resume_checkpoint'])
    relative = remote_checkpoint.relative_to(ROOT / 'experiments/akt/results').as_posix()
    prefix = worker['logical_run_id'] + '/checkpoints/'
    if not relative.startswith(prefix):
        raise ValueError('Checkpoint cuối khác logical run')
    name = remote_checkpoint.parent.name
    match = re.fullmatch(r'refit-batch-epoch-(\d+)-step-(\d+)-[a-f0-9]+', name)
    if match is None:
        raise ValueError('Checkpoint không thuộc epoch cuối')
    epoch, step = int(match[1]), int(match[2])
    if epoch != terminal['complete_epochs'] + 1:
        raise ValueError('Checkpoint khác số epoch đã nghiệm thu')
    if epoch != epochs:
        # TRAIN90 thật có 2.040 batch/epoch. Chỉ cho phần đuôi epoch 8
        # khi còn tối đa 40 batch rồi đến epoch 9, giữ nguyên mọi target.
        history = terminal.get('history', [])
        if (epoch != epochs - 1 or not 2000 <= step <= 2040 or not history
                or history[-1].get('optimizer_steps') != 2040
                or history[-1].get('valid_targets') != 14947674):
            raise ValueError('Phần refit còn lại vượt phạm vi đợt cuối')
    key = 'outputs/' + relative
    checkpoint = owned_input(ROOT, (previous_path.parent / 'files' / key).relative_to(ROOT).as_posix())
    marker_key = key.rsplit('/', 1)[0] + '/COMPLETE.json'
    metadata_key = key.rsplit('/', 1)[0] + '/metadata.json'
    files = previous['files']
    if (files[key]['sha256'] != request['resume_sha256']
            or checkpoint.stat().st_size != files[key]['bytes']
            or sha(checkpoint) != request['resume_sha256']):
        raise ValueError('Checkpoint cuối khác inventory đã tải')
    marker = checkpoint.parent / 'COMPLETE.json'
    metadata = checkpoint.parent / 'metadata.json'
    if sha(marker) != files[marker_key]['sha256'] or sha(metadata) != files[metadata_key]['sha256']:
        raise ValueError('Marker checkpoint cuối khác inventory')
    complete = json.loads(marker.read_text())
    if (complete['checkpoint_sha256'] != request['resume_sha256']
            or complete['metadata_sha256'] != hashlib.sha256(metadata.read_bytes()).hexdigest()):
        raise ValueError('Checkpoint cuối chưa đóng đầy đủ')


def validate_refit_execution(request, worker):
    if (worker.get('purpose') != 'refit90' or worker.get('variant') not in ('A0', 'A1', 'A2', 'A3')
            or worker['config']['phase'] != 'junyi-research' or worker['config']['batch_size'] != 128
            or worker['config']['seed'] != 42 or type(worker.get('frozen_epochs')) is not int
            or not 1 <= worker['frozen_epochs'] <= 20
            or not isinstance(worker.get('refit_request'), dict)):
        raise ValueError('Pinned A0–A3 refit90 worker and frozen epoch budget required')
    short_final = request.get('final_epoch_timebox', False)
    if short_final:
        verify_final_epoch_timebox(request, worker)
    return validate_resource_budget(request, worker, allow_short_final_epoch=short_final)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps(dict(status='NO_CLOUD_ACTION', snapshot=str(args.snapshot))))
        return
    temporary = ROOT / 'artifacts/akt/runtime/modal-client-temp'
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))
    os.environ.setdefault('MODAL_CONFIG_PATH', str(ROOT / 'artifacts/akt/private/modal.toml'))
    os.environ.setdefault('MODAL_PROFILE', 'kltn')
    import tempfile
    tempfile.tempdir = str(temporary)
    print(json.dumps(run(args.snapshot, json.loads(args.request.read_text()),
        worker_entrypoint='run_junyi_refit_gpu_stage.py', execution_validator=validate_refit_execution)))


if __name__ == '__main__':
    main()
