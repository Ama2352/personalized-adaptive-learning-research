"""Pilot A0 selected-only trên GPU, dùng cohort engineering10x84 đã có."""
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent
RUN = 'modal-a0-gpu-lifecycle-engineering10x84-20261112-01'
if __name__ == '__main__':
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'

import modal

app = modal.App('kltn-akt-'+RUN)
volume = modal.Volume.from_name('kltn-akt-'+RUN, create_if_missing=True, version=2)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def remote_train(expected_inputs):
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
    process = None
    started = time.monotonic()
    summary = dict(status='FAILED', main60_training=False, cohort='engineering10x84',
                   device='cuda', inputs=expected_inputs, checkpoint_transfers={})
    try:
        for name, digest in expected_inputs.items():
            assert sha(Path(name)) == digest
        copier = runpy.run_path('/opt/checkpoint_sync.py')['copy_complete_checkpoint']
        command = [str(root/'.venv/bin/python'), '-B', '/opt/gpu_a0_lifecycle_worker.py']
        with (driver/'worker.log').open('xb') as log:
            process = subprocess.Popen(command, cwd=root, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            while True:
                assert time.monotonic()-started < 380, 'bounded lifecycle driver timeout'
                finished = process.poll() is not None
                for marker in sorted((results/RUN/'checkpoints').glob('epoch-*/COMPLETE.json')):
                    name = marker.parent.name
                    if name not in summary['checkpoint_transfers']:
                        transfer = copier(marker.parent, durable/'checkpoints'/name)
                        volume.commit()
                        summary['checkpoint_transfers'][name] = transfer
                if finished:
                    break
                time.sleep(0.5)
        summary['returncode'] = process.returncode
        actual = json.loads((results/(RUN+'-operation')/'result.json').read_text())
        summary['worker_result'] = actual
        assert process.returncode == 0 and actual['status'] == 'ACTUAL_A0_CUDA_SELECTED_ENGINEERING_COMPLETE'
        terminal = json.loads((results/RUN/'selected-terminal.json').read_text())
        complete = json.loads((results/RUN/'COMPLETE.json').read_text())
        assert terminal['fresh_best_reload'] is True
        assert complete['status'] == 'COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE'
        summary.update(status='CUDA_A0_SELECTED_ENGINEERING_COMPLETE', terminal=terminal)
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
        files = [p for p in results.rglob('*') if p.is_file()]
        files += list((root/'artifacts/akt/runtime').glob(RUN+'*.json'))
        files += list((root/'artifacts/akt/preflight').glob(RUN+'*.json'))
        archive = root/'artifacts/akt/runtime'/(RUN+'-delivery.zip')
        inventory = {}
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as saved:
            for path in files:
                name = path.relative_to(root).as_posix()
                inventory[name] = dict(bytes=path.stat().st_size, sha256=sha(path))
                saved.write(path, name)
            saved.writestr('SHA256.json', json.dumps(inventory, indent=2)+'\n')
        import shutil
        shutil.copyfile(archive, durable/'artifacts.zip')
        assert sha(durable/'artifacts.zip') == sha(archive)
        summary.update(archive_sha256=sha(archive), archive_bytes=archive.stat().st_size)
        (durable/'receipt.json').write_text(json.dumps(summary, indent=2)+'\n')
        volume.commit()
    return summary


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    bundle = ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01'
    inputs = {
        '/opt/gpu_a0_lifecycle_worker.py': bundle/'gpu_a0_lifecycle_worker.py',
        '/opt/checkpoint_sync.py': ROOT/'experiments/akt/modal_artifact_sync.py',
        '/opt/cpu-gate.zip': ROOT/'experiments/akt/results/modal-cpu-preflight-20261112-04/artifacts.zip',
        '/opt/public-corpus.zip': ROOT/'artifacts/akt/modal/modal-a0-lifecycle-engineering10x84-20261112-01/public-corpus.zip',
    }
    pins = {name: sha(path) for name, path in inputs.items()}
    native = ROOT/'experiments/akt/results'/RUN
    assert not native.exists() or {p.name for p in native.iterdir()} <= {'execution.log'}, 'fresh operation only'
    print(json.dumps(dict(run_id=RUN, cohort='engineering10x84', device='cuda',
        max_optimizer_steps=40, max_optimized_targets=13440, max_containers=1,
        function_timeout_seconds=420, client_wait_seconds=1800, inputs=pins)), flush=True)
    if not args.run:
        raise SystemExit(0)
    recovery = json.loads((ROOT/'experiments/akt/results/modal-checkpoint-pilot-20261112-12/receipt.json').read_text())
    assert recovery['status'] == 'CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED'
    independent = json.loads((bundle/'checkpoint12-verification.json').read_text())
    assert independent['status'] == 'VERIFIED_DOWNLOADED_CUDA_EPOCH_RECOVERY'
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name, path in inputs.items():
        image = image.add_local_file(path, name, copy=True)
    function = app.function(image=image, gpu=['L4', 'T4', 'A10'], cpu=(0.25, 2), memory=(4096, 8192),
        timeout=420, startup_timeout=120, retries=0, max_containers=1,
        volumes={'/durable': volume})(remote_train)
    native.mkdir(exist_ok=True)
    with modal.enable_output(), app.run(environment_name='main'):
        call = function.spawn(pins)
        (native/'dispatch.json').write_text(json.dumps(dict(call_id=call.object_id))+'\n')
        receipt = call.get(timeout=1800)
        archive = native/'artifacts.zip'
        with archive.open('xb') as stream:
            for block in volume.read_file(RUN+'/artifacts.zip'):
                stream.write(block)
        assert archive.stat().st_size == receipt['archive_bytes']
        assert sha(archive) == receipt['archive_sha256']
        with zipfile.ZipFile(archive) as saved:
            assert saved.testzip() is None
            inventory = json.loads(saved.read('SHA256.json'))
            assert set(saved.namelist()) == set(inventory) | {'SHA256.json'}
            for name, expected in inventory.items():
                with saved.open(name) as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected['sha256']
        receipt['download_inventory_verified'] = True
        (native/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print(json.dumps(receipt), flush=True)
        assert receipt['status'] == 'CUDA_A0_SELECTED_ENGINEERING_COMPLETE'
