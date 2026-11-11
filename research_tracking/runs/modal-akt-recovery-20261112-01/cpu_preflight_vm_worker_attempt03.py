"""Gate CPU trên VM Linux, giữ nguyên nguồn và giới hạn test."""
import hashlib,json,os
from pathlib import Path
import zipfile
RUN='modal-cpu-preflight-20261112-03'
def preflight():
    import shutil
    import subprocess
    import time
    import traceback
    root = Path('/opt/kltn')
    out = Path('/cpu-evidence') / RUN
    out.mkdir(exist_ok=False)
    result = dict(status='FAILED', gpu_requested=False, main_training=False)
    started = time.monotonic()
    try:
        with zipfile.ZipFile('/opt/kltn-input.zip') as saved:
            pins = json.loads(saved.read('MANIFEST.json'))
            for name, expected in pins['files'].items():
                assert hashlib.sha256(saved.read(name)).hexdigest() == expected
            saved.extractall(root)
        lock = root / 'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
        shutil.copyfile('/opt/locked-cu126.txt', lock)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
                   OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2',
                   PYTHONDONTWRITEBYTECODE='1')
        command = [str(root / '.venv/bin/python'), '-B',
                   str(root / 'scripts/akt/refresh_gate2.py'), '--run-id', RUN,
                   '--publish-current', '--timeout-seconds', '540', '--lock-file', str(lock)]
        with (out / 'gate-controller.log').open('xb') as log:
            completed = subprocess.run(command, cwd=root, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, timeout=565)
        result['returncode'] = completed.returncode
        report = root / ('artifacts/akt/preflight/gate2-evidence-' + RUN + '.json')
        if report.exists():
            actual = json.loads(report.read_text())
            result.update(gate_status=actual['status'], test_result=actual.get('test_result'))
        if completed.returncode == 0:
            assert result['gate_status'] == 'PASS'
            result['status'] = 'MODAL_CPU_GATE_VERIFIED'
    except BaseException as error:
        result.update(error_type=type(error).__name__, error=str(error))
        (out / 'failure.log').write_text(traceback.format_exc())
    finally:
        result['elapsed_seconds'] = time.monotonic() - started
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        files = list(out.glob('*.json')) + list(out.glob('*.log'))
        files += list((root / 'artifacts/akt/preflight').glob('*'))
        inventory = {}
        with zipfile.ZipFile(out / 'artifacts.zip', 'x', zipfile.ZIP_DEFLATED) as saved:
            for path in files:
                if path.is_file():
                    name = path.name
                    raw = path.read_bytes()
                    assert name not in inventory
                    inventory[name] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
                    saved.writestr(name, raw)
            saved.writestr('SHA256.json', json.dumps(inventory, indent=2) + '\n')
        with (out / 'artifacts.zip').open('rb') as stream:
            result['archive_sha256'] = hashlib.file_digest(stream, 'sha256').hexdigest()
        result['archive_bytes'] = (out / 'artifacts.zip').stat().st_size
        pass  # Volume đồng bộ khi Sandbox kết thúc.
    return result

result=preflight()
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='MODAL_CPU_GATE_VERIFIED' else 1)
