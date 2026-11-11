"""Kiểm Gate CPU trên image Modal đã cài, trong grant pilot tổng0,50USD."""
import hashlib
import json
import os
from pathlib import Path
import zipfile

if __name__ == '__main__':
    ROOT = Path(__file__).resolve().parent.parent.parent.parent
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'

import modal

RUN = 'modal-cpu-preflight-20261112-01'
VOLUME = 'kltn-akt-' + RUN
app = modal.App('kltn-akt-' + RUN)
volume = modal.Volume.from_name(VOLUME, create_if_missing=True, version=1)


@app.function(image=modal.Image.from_id('im-PcG3UeRJq1Qu86G1dHDXz8'),
              cpu=(1, 2), memory=(2048, 8192), timeout=600, startup_timeout=60,
              retries=0, max_containers=1, volumes={'/cpu-evidence': volume})
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
        volume.commit()
    return result


if __name__ == '__main__':
    native = ROOT / 'experiments/akt/results' / RUN
    native.mkdir(parents=True, exist_ok=True)
    assert not (native / 'receipt.json').exists()
    with modal.enable_output(), app.run(environment_name='main'):
        result = preflight.spawn().get(timeout=720)
        archive = native / 'artifacts.zip'
        with archive.open('xb') as stream:
            for block in volume.read_file(RUN + '/artifacts.zip'):
                stream.write(block)
        with archive.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == result['archive_sha256']
        assert archive.stat().st_size == result['archive_bytes']
        with zipfile.ZipFile(archive) as saved:
            assert saved.testzip() is None
            for name, expected in json.loads(saved.read('SHA256.json')).items():
                raw = saved.read(name)
                assert hashlib.sha256(raw).hexdigest() == expected['sha256']
        result['download_inventory_verified'] = True
        (native / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        assert result['status'] == 'MODAL_CPU_GATE_VERIFIED'
