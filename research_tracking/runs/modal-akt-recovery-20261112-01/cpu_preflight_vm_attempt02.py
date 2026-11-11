"""Lượt Gate CPU thứ02 dùng VM, không GPU hoặc thay code/test của AKT."""
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

RUN = 'modal-cpu-preflight-20261112-02'


async def main():
    native = ROOT / 'experiments/akt/results' / RUN
    native.mkdir(parents=True, exist_ok=True)
    assert not (native / 'receipt.json').exists()
    app = modal.App('kltn-akt-' + RUN)
    volume = modal.Volume.from_name('kltn-akt-' + RUN, create_if_missing=True, version=1)
    worker = Path(__file__).parent / 'cpu_preflight_vm_worker.py'
    image = modal.Image.from_id('im-PcG3UeRJq1Qu86G1dHDXz8').add_local_file(
        worker, '/opt/cpu_preflight_vm_worker.py', copy=True)
    sandbox = None
    with modal.enable_output():
        async with app.run.aio(environment_name='main'):
            try:
                sandbox = await modal.Sandbox.create.aio(
                    '/opt/kltn/.venv/bin/python', '-B', '/opt/cpu_preflight_vm_worker.py',
                    app=app, image=image, runtime='vm', cpu=(1, 2), memory=(2048, 8192),
                    timeout=600, volumes={'/cpu-evidence': volume})
                (native / 'sandbox.json').write_text(json.dumps(dict(
                    sandbox_id=sandbox.object_id, runtime='vm', gpu=None)) + '\n')
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
                    result = json.loads(saved.read('result.json'))
                result.update(download_inventory_verified=True, runtime='vm',
                              archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
                (native / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps(result), flush=True)
                assert result['status'] == 'MODAL_CPU_GATE_VERIFIED'
            finally:
                if sandbox is not None:
                    await sandbox.terminate.aio()


if __name__ == '__main__':
    asyncio.run(main())
