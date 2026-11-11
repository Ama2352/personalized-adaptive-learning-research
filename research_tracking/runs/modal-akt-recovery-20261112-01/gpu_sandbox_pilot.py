"""Pilot09 trực tiếp một T4, chờ cấp phát180giây, runtime tối đa600giây."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent.parent
os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE'] = 'kltn'
import modal

RUN = 'modal-checkpoint-pilot-20261112-09'


async def main():
    native = ROOT / 'experiments/akt/results' / RUN
    native.mkdir(parents=True, exist_ok=True)
    assert not (native / 'receipt.json').exists()
    app = modal.App('kltn-akt-' + RUN)
    volume = modal.Volume.from_name('kltn-akt-' + RUN, create_if_missing=True, version=1)
    worker = Path(__file__).parent / 'gpu_sandbox_worker.py'
    image = modal.Image.from_id('im-PcG3UeRJq1Qu86G1dHDXz8').add_local_file(
        worker, '/opt/gpu_sandbox_worker.py', copy=True)
    sandbox = None
    with modal.enable_output():
        async with app.run.aio(environment_name='main'):
            try:
                sandbox = await asyncio.wait_for(modal.Sandbox.create.aio(
                    '/opt/kltn/.venv/bin/python', '-B', '/opt/gpu_sandbox_worker.py',
                    app=app, image=image, runtime='gvisor', gpu='T4', cpu=(0.25, 2), memory=(4096, 8192),
                    timeout=600, name=RUN, volumes={'/opt/kltn/experiments/akt/results': volume}), 180)
                (native / 'sandbox.json').write_text(json.dumps(dict(
                    sandbox_id=sandbox.object_id, runtime='gvisor', gpu='T4')) + '\n')
                await asyncio.wait_for(sandbox.wait.aio(), 660)
                (native / 'stdout.log').write_text(await sandbox.stdout.read.aio())
                (native / 'stderr.log').write_text(await sandbox.stderr.read.aio())
                archive = native / 'artifacts.zip'
                with archive.open('xb') as stream:
                    async for block in volume.read_file.aio(RUN + '/artifacts.zip'):
                        stream.write(block)
                with zipfile.ZipFile(archive) as saved:
                    assert saved.testzip() is None
                    inventory = json.loads(saved.read('SHA256.json'))
                    for name, expected in inventory.items():
                        raw = saved.read(name)
                        assert len(raw) == expected['bytes']
                        assert hashlib.sha256(raw).hexdigest() == expected['sha256']
                    result = json.loads(saved.read(RUN + '/summary.json'))
                result.update(download_inventory_verified=True, runtime='gvisor', archive_bytes=archive.stat().st_size,
                              archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
                (native / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps(result), flush=True)
                assert result['status'] == 'CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED'
            finally:
                if sandbox is None:
                    try:
                        sandbox = await modal.Sandbox.from_name.aio('kltn-akt-' + RUN, RUN, environment_name='main')
                    except modal.exception.NotFoundError:
                        pass
                if sandbox is not None:
                    await sandbox.terminate.aio()


if __name__ == '__main__':
    asyncio.run(main())
