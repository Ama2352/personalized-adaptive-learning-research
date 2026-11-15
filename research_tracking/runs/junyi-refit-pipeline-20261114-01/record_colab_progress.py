"""Lưu tiến độ đọc từ MCP, tách checkpoint Drive khỏi model đã nghiệm thu trên D."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bridge-directory', type=Path, required=True)
    args = parser.parse_args()
    latest = max(args.bridge_directory.glob('result-*.json'), key=lambda path: path.stat().st_mtime)
    result = json.loads(latest.read_text())
    assert not result.get('is_error'), 'MCP trả lỗi'
    outputs = result['structured_content']['outputs']
    assert not any(item.get('output_type') == 'error' for item in outputs), 'Cell kiểm tiến độ lỗi'
    monitor = json.loads(''.join(''.join(item.get('text', [])) for item in outputs
                                 if item.get('output_type') == 'stream'))
    assert monitor['status'] == 'A3_T4_MONITOR'
    backup = monitor['drive_backup']
    assert backup['status'] == 'PASS_DRIVE_CHECKPOINT_BACKUP'
    assert 3 <= backup['complete_epochs'] <= 9
    now = datetime.now(timezone.utc).isoformat()
    with (HERE / 'a3-colab-monitor.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(observed_at_utc=now, monitor=monitor), ensure_ascii=False) + '\n')
    progress_path = HERE / 'refit-loop-progress.json'
    progress = json.loads(progress_path.read_text())
    previous_epochs = progress['models']['a3']['complete_epochs']
    assert backup['complete_epochs'] >= previous_epochs, 'Không chấp nhận tiến độ lùi'
    status = 'COLAB_A3_SEQUENCE_RUNNING'
    if monitor.get('sequence'):
        status = 'COLAB_A3_SEQUENCE_STOPPED_REQUIRES_ACCEPTANCE'
    for path in (HERE / 'STATE.json', progress_path):
        state = json.loads(path.read_text())
        state.update(status=status, updated_at_utc=now,
                     active_execution=monitor['operation'], colab_latest_drive_progress=backup,
                     colab_latest_monitor_log='a3-colab-monitor.jsonl')
        if path == progress_path:
            state['models']['a3'].update(complete_epochs=backup['complete_epochs'],
                                      partial_epoch=backup['partial_epoch'],
                                      partial_optimizer_step=backup['partial_optimizer_step'],
                                      checkpoint_evidence='a3-colab-monitor.jsonl')
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if previous_epochs != backup['complete_epochs']:
        subprocess.run([sys.executable, '-B', str(HERE / 'report_refit_progress.py')],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    print(json.dumps(dict(status=status, complete_epochs=backup['complete_epochs'],
                          partial_epoch=backup['partial_epoch'],
                          partial_optimizer_step=backup['partial_optimizer_step'],
                          epoch_advanced=previous_epochs != backup['complete_epochs'],
                          sequence=monitor.get('sequence')), ensure_ascii=False))


if __name__ == '__main__':
    main()
