"""Checkpoint CUDA qua Sandbox trực tiếp, giữ recipe và tối đa16updates."""
import hashlib,json,os,zipfile
from pathlib import Path,PurePosixPath
def sha_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def remote_pilot(expected_zip_sha, run_id, expected_gpu, volume_name):
    import subprocess
    import time
    import traceback
    remote = Path('/opt/kltn')
    results = remote/'experiments/akt/results'
    out = results/run_id
    out.mkdir(exist_ok=False)
    print(json.dumps(dict(event='pilot_started', run_id=run_id)), flush=True)
    began = time.monotonic()
    summary = dict(status='FAILED', run_id=run_id, gpu_requested=expected_gpu,
        main_training=False, source_zip_sha256=expected_zip_sha)
    try:
        assert sha_file(Path('/opt/kltn-input.zip')) == expected_zip_sha
        with zipfile.ZipFile('/opt/kltn-input.zip') as source:
            pins = json.loads(source.read('MANIFEST.json'))
            assert source.testzip() is None
            assert len(source.namelist()) == len(set(source.namelist())) == len(pins['files'])+1
            for name, expected_sha in pins['files'].items():
                path = PurePosixPath(name)
                assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
                assert hashlib.sha256(source.read(name)).hexdigest() == expected_sha
            source.extractall(remote)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', EXPECTED_PILOT_GPU=expected_gpu)
        runtime_command = [str(remote/'.venv/bin/python'), '-I', '-B',
            str(remote/'scripts/akt/check_runtime.py'), '--upstream',
            str(remote/'artifacts/akt/dependencies/upstream'), '--device', 'cuda',
            '--lock-file', '/opt/locked-cu126.txt', '--output',
            str(remote/'artifacts/akt/runtime/modal-runtime.json')]
        with (out/'runtime.log').open('xb') as log:
            subprocess.run(runtime_command, cwd=remote, env=env, stdout=log,
                stderr=subprocess.STDOUT, timeout=40, check=True)
        runtime = json.loads((remote/'artifacts/akt/runtime/modal-runtime.json').read_text())
        assert runtime['lock_sha256'] == pins['lock_sha256']
        (out/'runtime.json').write_text(json.dumps(runtime, indent=2)+'\n')
        command = [str(remote/'.venv/bin/python'), '-I', '-B',
            str(remote/'artifacts/akt/runtime/t4_checkpoint_controller.py')]
        with (out/'controller.log').open('xb') as log:
            process = subprocess.run(command, cwd=remote, env=env, stdout=log,
                stderr=subprocess.STDOUT, timeout=390)
        summary['controller_returncode'] = process.returncode
        actual = json.loads((results/'t4-checkpoint-recovery-20261110-01/result.json').read_text())
        summary.update(controller_result=actual, status=actual['status'])
    except BaseException as error:
        summary.update(error_type=type(error).__name__, error=str(error))
        (out/'failure.log').write_text(traceback.format_exc())
    finally:
        summary['elapsed_seconds'] = time.monotonic()-began
        (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        files = list(out.glob('*.json'))+list(out.glob('*.log'))
        checkpoint_root = results/'t4-checkpoint-recovery-20261110-01'
        if checkpoint_root.exists():
            files += [path for path in checkpoint_root.rglob('*') if path.is_file()]
        inventory = {path.relative_to(results).as_posix(): dict(
            sha256=sha_file(path), bytes=path.stat().st_size) for path in files}
        with zipfile.ZipFile(out/'artifacts.zip', 'x', compression=zipfile.ZIP_DEFLATED) as saved:
            for path in files:
                saved.write(path, path.relative_to(results).as_posix())
            saved.writestr('SHA256.json', json.dumps(inventory, indent=2)+'\n')
        summary.update(archive_sha256=sha_file(out/'artifacts.zip'),
            archive_bytes=(out/'artifacts.zip').stat().st_size)
        (out/'receipt.json').write_text(json.dumps(summary, indent=2)+'\n')
        pass  # Volume đồng bộ khi Sandbox kết thúc.
    return summary

result=remote_pilot('93bdf7902d5b4f48e186daca2b10adc9c1a6fb37122bb788def56dbcd590e0f8','modal-checkpoint-pilot-20261112-09','T4','kltn-akt-checkpoint-pilot-20261112-09')
print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED' else 1)
