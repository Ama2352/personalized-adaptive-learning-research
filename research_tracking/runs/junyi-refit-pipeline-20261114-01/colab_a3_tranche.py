"""Một lượt tiếp tục A3 có hạn giờ trên T4 miễn phí, dùng worker đã đóng."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path('/opt/kltn')
TRANSFER = Path('/content/kltn-a3-transfer')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(attempt, checkpoint, checkpoint_sha, backup_root=None):
    assert json.loads((TRANSFER / 'runtime-verified.json').read_text())['status'] == 'PASS_ISOLATED_CUDA_RUNTIME'
    if backup_root is not None:
        backup_root = Path(backup_root)
        assert backup_root.resolve().is_relative_to(Path('/content/drive/MyDrive').resolve())
        assert backup_root.is_dir(), 'Drive chưa sẵn sàng để lưu checkpoint'
    worker = ROOT / 'gpu-stage-request.json'
    frozen = json.loads(worker.read_text())
    assert frozen['variant'] == 'a3' and frozen['frozen_epochs'] == 9
    logical = ROOT / 'experiments/akt/results' / frozen['logical_run_id']
    resume = (ROOT / checkpoint).resolve()
    assert resume.is_relative_to((logical / 'checkpoints').resolve())
    assert sha(resume) == checkpoint_sha
    assert not (logical / 'COMPLETE.json').exists(), 'Refit đã hoàn tất, không chạy thêm'
    execution_id = f'colab-junyi-a3-refit-20261115-{attempt:03}'
    operation = ROOT / 'experiments/akt/results' / (execution_id + '-operation')
    operation.mkdir(exist_ok=False)
    request = dict(execution_id=execution_id, gpu='T4', worker_request_sha256=sha(worker),
                   approval_reference='Người dùng15/11 duyệt tiếp tục A3 bằng T4 Colab miễn phí và chuyển gói683MB.',
                   resume_checkpoint=checkpoint, resume_sha256=checkpoint_sha)
    execution = operation / 'execution.json'
    execution.write_text(json.dumps(request, ensure_ascii=False, indent=2))
    lock = TRANSFER / 'training.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with lock.open('x') as stream:
        json.dump(dict(pid=os.getpid(), execution_id=execution_id), stream)
    result = dict(status='FAILED', execution_id=execution_id, checkpoint_input_sha256=checkpoint_sha)
    process = None
    try:
        with (operation / 'console.log').open('x') as output:
            process = subprocess.Popen([str(ROOT / '.venv/bin/python'), '-u', '-B',
                str(ROOT / 'scripts/akt/run_junyi_refit_gpu_stage.py'), '--request', str(worker),
                '--execution', str(execution)], cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            (operation / 'child.json').write_text(json.dumps(dict(pid=process.pid)))
            try:
                code = process.wait(timeout=600)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=10)
                raise TimeoutError('Dừng lượt600giây; giữ checkpoint gần nhất, cần kiểm trước tiếp tục')
        result.update(exit_code=code)
        assert code == 0, 'Worker lỗi, đọc console/failure trước khi tiếp tục'
        native = json.loads((operation / 'result.json').read_text())
        assert native['status'] in {'PARTIAL_JUNYI_REFIT90', 'JUNYI_REFIT90_COMPLETE'}, native['status']
        result.update(status='PASS_BOUNDED_NATIVE_WORKER', native_status=native['status'])
        if backup_root is not None:
            from colab_a3_backup import backup
            result['drive_backup'] = str(backup(ROOT,operation,backup_root))
    except BaseException:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        raise
    finally:
        result['wall_seconds'] = time.monotonic() - started
        result['child_running'] = process is not None and process.poll() is None
        (operation / 'controller-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
        if not result['child_running']:
            lock.unlink()
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--backup-root', type=Path)
    args = parser.parse_args()
    assert args.attempt > 0
    run(args.attempt, args.checkpoint, args.sha256, args.backup_root)
