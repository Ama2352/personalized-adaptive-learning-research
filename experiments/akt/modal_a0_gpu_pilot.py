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

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def remote_train(expected_inputs, run_id, research_main, candidate_id='A0'):
    import runpy
    import signal
    import subprocess
    import time
    import traceback
    RUN = run_id
    volume = modal.Volume.from_name('kltn-akt-'+RUN)
    root = Path('/opt/kltn')
    results = root/'experiments/akt/results'
    results.mkdir(parents=True, exist_ok=True)
    driver = results/(RUN+'-driver')
    driver.mkdir(exist_ok=False)
    durable = Path('/durable')/RUN
    durable.mkdir(exist_ok=False)
    process = None
    started = time.monotonic()
    assert candidate_id in ('A0', 'A1_EXPERT', 'A1_LEARNED', 'A2_EXPERT', 'A2_LEARNED', 'A3_EXPERT', 'A3_LEARNED')
    graph_candidate = candidate_id != 'A0'
    summary = dict(status='FAILED', candidate_id=candidate_id, main60_training=research_main,
                   cohort='Main60x210' if research_main else 'engineering10x84',
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
                assert time.monotonic()-started < (800 if research_main else 380), 'bounded lifecycle driver timeout'
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
        expected_worker = ('ACTUAL_A0_CUDA_SELECTED_MAIN60_COMPLETE' if research_main
                           else 'ACTUAL_A0_CUDA_SELECTED_ENGINEERING_COMPLETE')
        if graph_candidate:
            expected_worker = 'ACTUAL_GRAPH_CUDA_SELECTED_MAIN60_COMPLETE'
        assert process.returncode == 0 and actual['status'] == expected_worker
        terminal = json.loads((results/RUN/'selected-terminal.json').read_text())
        complete = json.loads((results/RUN/'COMPLETE.json').read_text())
        assert terminal['fresh_best_reload'] is True
        assert complete['status'] == 'COMPLETE_MAIN_SELECTED_ONLY_CANDIDATE'
        summary.update(status='CUDA_A0_SELECTED_MAIN60_COMPLETE' if research_main
                       else 'CUDA_A0_SELECTED_ENGINEERING_COMPLETE', terminal=terminal)
        if graph_candidate:
            summary['status'] = 'CUDA_GRAPH_SELECTED_MAIN60_COMPLETE'
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
    from modal_budget_guard import (ModalAppBudgetGuard, ModalRunDeadline,
                                    PendingOwnedModalApp, stop_owned_app_cli)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--main60', action='store_true', help='A0 selected-only trên corpus48/6/6, giữ recipe frozen')
    args = parser.parse_args()
    bundle = ROOT/'research_tracking/runs/modal-akt-recovery-20261112-01'
    if args.main60:
        RUN = 'modal-main60-a0-selected-20261112-01'
        allocation = json.loads((bundle/'main60-a0-allocation.json').read_text())
        assert allocation['aggregate_compute_envelope_usd'] <= allocation['authorized_total_pilot_usd']
    deadline = ModalRunDeadline(800 if args.main60 else 380)
    app = modal.App('kltn-akt-'+RUN)
    volume = modal.Volume.from_name('kltn-akt-'+RUN, create_if_missing=True, version=2)
    inputs = {
        '/opt/gpu_a0_lifecycle_worker.py': bundle/('gpu_main60_a0_worker.py' if args.main60 else 'gpu_a0_lifecycle_worker.py'),
        '/opt/checkpoint_sync.py': ROOT/'experiments/akt/modal_artifact_sync.py',
        '/opt/cpu-gate.zip': ROOT/'experiments/akt/results/modal-cpu-preflight-20261112-04/artifacts.zip',
        '/opt/public-corpus.zip': ROOT/('artifacts/akt/modal/main60-akt-inputs-20261112-01/public-corpus.zip'
                                      if args.main60 else 'artifacts/akt/modal/modal-a0-lifecycle-engineering10x84-20261112-01/public-corpus.zip'),
    }
    pins = {name: sha(path) for name, path in inputs.items()}
    native = ROOT/'experiments/akt/results'/RUN
    assert not native.exists() or {p.name for p in native.iterdir()} <= {'execution.log'}, 'fresh operation only'
    print(json.dumps(dict(run_id=RUN, cohort='Main60x210' if args.main60 else 'engineering10x84', device='cuda',
        max_optimizer_steps=720 if args.main60 else 40,
        max_optimized_targets=201600 if args.main60 else 13440, max_containers=1,
        function_timeout_seconds=840 if args.main60 else 420,
        client_wait_seconds=800 if args.main60 else 380, inputs=pins)), flush=True)
    if not args.run:
        raise SystemExit(0)
    recovery = json.loads((ROOT/'experiments/akt/results/modal-checkpoint-pilot-20261112-12/receipt.json').read_text())
    assert recovery['status'] == 'CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED'
    independent = json.loads((bundle/'checkpoint12-verification.json').read_text())
    assert independent['status'] == 'VERIFIED_DOWNLOADED_CUDA_EPOCH_RECOVERY'
    if args.main60:
        lifecycle = json.loads((bundle/'a0-gpu-lifecycle-verification.json').read_text())
        assert lifecycle['status'] == 'VERIFIED_A0_CUDA_SELECTED_ENGINEERING_LIFECYCLE'
        assert pins['/opt/gpu_a0_lifecycle_worker.py'] == allocation['worker_sha256']
        assert pins['/opt/public-corpus.zip'] == allocation['archive_sha256']
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name, path in inputs.items():
        image = image.add_local_file(path, name, copy=True)
    function = app.function(image=image, gpu=['L4', 'T4', 'A10'], cpu=(0.25, 2), memory=(4096, 8192),
        timeout=840 if args.main60 else 420, startup_timeout=60 if args.main60 else 120,
        retries=0, max_containers=1,
        volumes={'/durable': volume})(remote_train)
    native.mkdir(exist_ok=True)
    binding = PendingOwnedModalApp(RUN, app.name, lambda: app.app_id)
    with ModalAppBudgetGuard(binding, deadline, stop_app=stop_owned_app_cli,
                             diagnostic_path=native/'app-budget-guard.json') as guard:
        with modal.enable_output(), app.run(environment_name='main'):
            guard.remaining()
            call = function.spawn(pins, RUN, args.main60)
            (native/'dispatch.json').write_text(json.dumps(dict(call_id=call.object_id))+'\n')
            receipt = call.get(timeout=guard.remaining())
            (native/'remote-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    # GPU đã dừng trước download/CRC/SHA trên máy người dùng.
    volume = modal.Volume.from_name('kltn-akt-'+RUN)
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
    terminal = receipt.get('terminal', {})
    print(json.dumps(dict(status=receipt['status'], epochs=terminal.get('complete_fit_epochs'),
        selected_epoch=terminal.get('selected_epoch'), counters=terminal.get('counters'),
        archive_bytes=receipt['archive_bytes'], downloaded_verified=True)), flush=True)
    expected = 'CUDA_A0_SELECTED_MAIN60_COMPLETE' if args.main60 else 'CUDA_A0_SELECTED_ENGINEERING_COMPLETE'
    assert receipt['status'] == expected
