"""Modal Junyi A0 một epoch trong allocation0,50USD đã được duyệt."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT/'research_tracking/runs/junyi-akt-cuda-engineering-20261112-01'
RUN = 'modal-junyi-a0-epoch-20261112-02'
if __name__ == '__main__':
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
import modal


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def remote_epoch(pins):
    import runpy
    import signal
    import subprocess
    import time
    import traceback
    root = Path('/opt/kltn')
    results = root/'experiments/akt/results'
    results.mkdir(parents=True, exist_ok=True)
    driver = results/(RUN+'-driver')
    driver.mkdir(exist_ok=False)
    durable = Path('/durable')/RUN
    durable.mkdir(exist_ok=False)
    volume = modal.Volume.from_name('kltn-akt-'+RUN)
    process = None
    summary = dict(status='FAILED', checkpoint_transfers={})
    started = time.monotonic()
    try:
        for name, digest in pins.items():
            assert sha(Path(name)) == digest
        copy = runpy.run_path('/opt/checkpoint_sync.py')['copy_complete_checkpoint']
        with (driver/'worker.log').open('xb') as log:
            process = subprocess.Popen([str(root/'.venv/bin/python'), '-B', '/opt/junyi-worker.py'],
                cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            while True:
                assert time.monotonic()-started < 800, 'Junyi controller wall budget'
                for marker in (results/RUN/'checkpoints').glob('epoch-*/COMPLETE.json'):
                    name = marker.parent.name
                    if name not in summary['checkpoint_transfers']:
                        try:
                            transfer = copy(marker.parent, durable/'checkpoints'/name)
                        except json.JSONDecodeError:
                            # Worker có thể còn đang đóng marker; lượt poll kế tiếp đọc lại.
                            continue
                        summary['checkpoint_transfers'][name] = transfer
                        volume.commit()
                if process.poll() is not None:
                    for marker in (results/RUN/'checkpoints').glob('epoch-*/COMPLETE.json'):
                        name = marker.parent.name
                        if name not in summary['checkpoint_transfers']:
                            summary['checkpoint_transfers'][name] = copy(marker.parent, durable/'checkpoints'/name)
                            volume.commit()
                    break
                time.sleep(0.5)
        summary['returncode'] = process.returncode
        actual = json.loads((results/(RUN+'-operation')/'result.json').read_text())
        assert process.returncode == 0 and actual['status'] == 'ACTUAL_JUNYI_A0_CUDA_ONE_EPOCH_COMPLETE', actual
        summary.update(status=actual['status'], terminal=actual['terminal'])
    except BaseException as error:
        summary.update(error_type=type(error).__name__, error=str(error))
        (driver/'failure.log').write_text(traceback.format_exc())
    finally:
        if process is not None and process.poll() is None:
            assert process.pid > 1 and process.pid != os.getpgrp()
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(process.pid, sig)
                except ProcessLookupError:
                    pass
            process.wait(timeout=10)
        summary['elapsed_seconds'] = time.monotonic()-started
        (driver/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        archive = durable/'artifacts.zip'
        inventory = {}
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as saved:
            for folder in (driver, results/RUN, results/(RUN+'-operation')):
                for path in folder.rglob('*'):
                    if path.is_file():
                        name = path.relative_to(root).as_posix()
                        inventory[name] = dict(bytes=path.stat().st_size, sha256=sha(path))
                        saved.write(path, name)
            saved.writestr('SHA256.json', json.dumps(inventory, indent=2))
        summary.update(archive_sha256=sha(archive), archive_bytes=archive.stat().st_size)
        (durable/'receipt.json').write_text(json.dumps(summary, indent=2)+'\n')
        volume.commit()
    return summary


def main():
    from modal_graph_selected import read_billing
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    allocation = json.loads((BUNDLE/'allocation.json').read_text())
    assert allocation['status']=='USER_APPROVED' and allocation['authorized_usd']==0.5
    gate_native = ROOT/'experiments/akt/results'/allocation['cpu_run']
    gate = json.loads((gate_native/'receipt.json').read_text())
    assert gate['status']=='MODAL_CPU_GATE_VERIFIED' and gate['download_inventory_verified'] is True
    inputs_root = ROOT/'artifacts/akt/modal/junyi-engineering-20261112-01'
    inputs = {'/opt/kltn-input.zip': inputs_root/'source.zip',
        '/opt/junyi-cohort.zip': inputs_root/'cohort.zip', '/opt/junyi-worker.py': BUNDLE/'gpu_worker.py',
        '/opt/cpu-gate.zip': gate_native/'artifacts.zip', '/opt/junyi-request.json': BUNDLE/'gpu-request.json',
        '/opt/checkpoint_sync.py': ROOT/'experiments/akt/modal_artifact_sync.py'}
    pins = {name:sha(path) for name,path in inputs.items()}
    print(json.dumps(dict(run_id=RUN, inputs=pins, paid_run_requested=args.run)), flush=True)
    if not args.run:
        return
    billing = asyncio.run(read_billing())
    baseline = json.loads((BUNDLE/'billing-before.json').read_text())
    assert float(billing['billing']['metered_cost'])+0.4 < 30
    assert float(billing['billing']['metered_cost'])-float(baseline['billing']['metered_cost'])+0.4 < 0.5
    native = ROOT/'experiments/akt/results'/RUN
    native.mkdir(exist_ok=False)
    (native/'billing-before.json').write_text(json.dumps(billing, indent=2))
    with (BUNDLE/'gpu-reservation02.json').open('x') as stream:
        json.dump(dict(run_id=RUN, reserved_usd=0.4, pins=pins), stream)
    app = modal.App('kltn-akt-'+RUN)
    volume = modal.Volume.from_name('kltn-akt-'+RUN, create_if_missing=True, version=2)
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name,path in inputs.items():
        image = image.add_local_file(path, name, copy=True)
    function = app.function(image=image, gpu=allocation['gpu_options'], cpu=(0.25,2), memory=(4096,8192),
        timeout=840, startup_timeout=60, retries=0, max_containers=1, scaledown_window=60,
        volumes={'/durable':volume})(remote_epoch)
    with modal.enable_output(), app.run(environment_name='main'):
        call = function.spawn(pins)
        (native/'dispatch.json').write_text(json.dumps(dict(call_id=call.object_id)))
        receipt = call.get(timeout=1800)
        (native/'remote-receipt.json').write_text(json.dumps(receipt, indent=2))
    archive = native/'artifacts.zip'
    with archive.open('xb') as stream:
        for block in volume.read_file(RUN+'/artifacts.zip'):
            stream.write(block)
    assert sha(archive)==receipt['archive_sha256'] and archive.stat().st_size==receipt['archive_bytes']
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        inventory = json.loads(saved.read('SHA256.json'))
        assert set(saved.namelist()) == set(inventory)|{'SHA256.json'}
        for name,entry in inventory.items():
            raw = saved.read(name)
            assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
    receipt['download_inventory_verified'] = True
    (native/'receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    assert receipt['status']=='ACTUAL_JUNYI_A0_CUDA_ONE_EPOCH_COMPLETE'


if __name__ == '__main__':
    main()
