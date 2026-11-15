"""Một lượt tiếp tục A3 có hạn giờ trên T4 miễn phí, dùng worker đã đóng."""
import argparse
from contextlib import contextmanager
import csv
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

ROOT = Path('/opt/kltn')
TRANSFER = Path('/content/kltn-a3-transfer')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@contextmanager
def measure_gpu(operation):
    """NVML qua nvidia-smi, không thay Torch/RNG hoặc trọng số."""
    stop = threading.Event()
    started = time.monotonic()
    def sample():
        with (operation/'gpu-telemetry.jsonl').open('x') as log:
            while not stop.is_set():
                try:
                    query = subprocess.run(['nvidia-smi',
                        '--query-gpu=utilization.gpu,memory.used,memory.total,power.draw',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5)
                    values = next(csv.reader(query.stdout.splitlines()))
                    event = dict(seconds=time.monotonic()-started,gpu_utilization=float(values[0]),
                        vram_used_mib=float(values[1]),vram_total_mib=float(values[2]),power_w=float(values[3]))
                except Exception as error:
                    event = dict(seconds=time.monotonic()-started,error_type=type(error).__name__,error=str(error))
                log.write(json.dumps(event)+'\n')
                log.flush()
                if stop.wait(5):
                    break
    thread = threading.Thread(target=sample,daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=10)
        assert not thread.is_alive(), 'GPU sampler chưa kết thúc'


def run(attempt, checkpoint, checkpoint_sha, backup_root=None):
    assert json.loads((TRANSFER / 'runtime-verified.json').read_text())['status'] == 'PASS_ISOLATED_CUDA_RUNTIME'
    if backup_root is not None:
        backup_root = Path(backup_root)
        assert backup_root.resolve().is_relative_to(Path('/content/drive/MyDrive').resolve())
        assert backup_root.is_dir(), 'Drive chưa sẵn sàng để lưu checkpoint'
    worker = ROOT / 'gpu-stage-request.json'
    frozen = json.loads(worker.read_text())
    assert frozen['variant'] == 'A3' and frozen['frozen_epochs'] == 9
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
        with measure_gpu(operation), (operation / 'console.log').open('x') as output:
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
    return result


def run_sequence(attempt, checkpoint, checkpoint_sha, backup_root, max_tranches, sequence_seconds):
    """Tiếp tục một protocol đã đóng, dừng ở9epoch/lỗi/giới hạn và kiểm backup mỗi lượt."""
    from colab_a3_backup import position
    assert backup_root is not None and 1 <= max_tranches <= 40
    assert 650 <= sequence_seconds <= 10800
    started = time.monotonic()
    backup_root = Path(backup_root)
    previous = position(Path(checkpoint).parent)
    state = dict(status='RUNNING', complete_epochs=previous[0] if previous[2] else previous[0]-1)
    try:
        for offset in range(max_tranches):
            if time.monotonic()-started+620 > sequence_seconds:
                state['status'] = 'TIME_LIMIT_CHECKPOINT_SAVED'
                break
            result = run(attempt+offset,checkpoint,checkpoint_sha,backup_root)
            assert result['status'] == 'PASS_BOUNDED_NATIVE_WORKER' and not result['child_running']
            manifest = Path(result['drive_backup'])
            receipt = json.loads(manifest.read_text())
            assert receipt['status'] == 'PASS_DRIVE_CHECKPOINT_BACKUP' and receipt['frozen_epochs'] == 9
            pointer = json.loads((backup_root/'LATEST.json').read_text())
            assert (backup_root/pointer['manifest']).resolve() == manifest.resolve()
            assert sha(manifest) == pointer['sha256']
            current = position(Path(receipt['checkpoint']).parent)
            assert current > previous, 'Không có checkpoint tiến triển, dừng trước lượt tiếp theo'
            checkpoint, checkpoint_sha = receipt['checkpoint'], receipt['checkpoint_sha256']
            previous = current
            state.update(complete_epochs=receipt['complete_epochs'],partial_epoch=receipt['partial_epoch'],
                partial_optimizer_step=receipt['partial_optimizer_step'],checkpoint=checkpoint,
                checkpoint_sha256=checkpoint_sha,last_attempt=attempt+offset,
                status='COMPLETE_9_EPOCHS_DRIVE_BACKED_UP' if receipt['refit_complete'] else 'RUNNING')
            if receipt['refit_complete']:
                assert receipt['complete_epochs'] == 9
                break
        else:
            state['status'] = 'TRANCHE_LIMIT_CHECKPOINT_SAVED'
    except BaseException as error:
        state.update(status='STOPPED_REQUIRES_REVIEW',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        state['elapsed_seconds'] = time.monotonic()-started
        (TRANSFER/'sequence-status.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
        temporary = backup_root/'SEQUENCE_STATUS.writing.json'
        temporary.write_text(json.dumps(state,ensure_ascii=False,indent=2))
        temporary.replace(backup_root/'SEQUENCE_STATUS.json')
        print(json.dumps(state,ensure_ascii=False),flush=True)
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--backup-root', type=Path)
    parser.add_argument('--max-tranches', type=int, default=1)
    parser.add_argument('--sequence-seconds', type=int, default=10800)
    args = parser.parse_args()
    assert args.attempt > 0
    if args.max_tranches == 1:
        run(args.attempt, args.checkpoint, args.sha256, args.backup_root)
    else:
        run_sequence(args.attempt,args.checkpoint,args.sha256,args.backup_root,
                     args.max_tranches,args.sequence_seconds)
