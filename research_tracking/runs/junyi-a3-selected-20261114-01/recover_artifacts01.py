"""Thu artifact A3 đã hoàn tất trên server sau lỗi mạng local; không gọi GPU."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import collect_outputs, sha, write_new


def main():
    os.environ.update(MODAL_CONFIG_PATH=str(ROOT / 'artifacts/akt/private/modal.toml'), MODAL_PROFILE='kltn')
    import modal
    run = ROOT / 'experiments/akt/results/modal-junyi-a3-staged-h100-20261114-01'
    dispatch = json.loads((run / 'dispatch.json').read_text())
    assert dispatch['app_id'] == 'ap-T7LjfYYBIS79yKxCOfnwxR'
    assert json.loads((HERE / 'containers-recovery01.json').read_text()) == []
    log = (HERE / 'recovery-stop01.log').read_text(encoding='utf-8')
    assert 'App is already stopped' in log
    acknowledgment = dict(status='SERVER_APP_ALREADY_STOPPED_CONFIRMED', app_id=dispatch['app_id'],
        stopped_at_server='2026-11-14T17:48:41+07:00', containers_empty=True,
        original_guard_sha256=sha(run / 'app-budget-guard.json'),
        cli_stop_log_sha256=sha(HERE / 'recovery-stop01.log'),
        note_vi='Client mất DNS/khoảng ngắt local làm watchdog local ghi muộn. '
        'App đã kết thúc trên server trước lệnh kiểm lại. Giữ nguyên guard lỗi; thu artifact sau xác nhận server.')
    write_new(HERE / 'recovery-stop-acknowledged01.json', acknowledgment)
    volume = modal.Volume.from_name(dispatch['volume_name'], version=2)
    name = 'outputs/' + run.name + '-operation/remote-inventory.json'
    receipt = json.loads(b''.join(volume.read_file(name)))
    assert receipt['status'] == 'PARTIAL_SELECTED_ONLY_NOT_FINAL'
    result = collect_outputs(receipt, run, volume.read_file, stop_acknowledged=True)
    result['worker_status'] = receipt['status']
    result['stop_recovery_evidence'] = (HERE / 'recovery-stop-acknowledged01.json').relative_to(ROOT).as_posix()
    write_new(run / 'stage-result.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
