"""A0 selected lifecycle engineering10x84 trên VM CPU đã nghiệm thu Gate."""
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

RUN = 'modal-a0-lifecycle-engineering10x84-20261112-02'


async def main():
    native = ROOT / 'experiments/akt/results' / RUN
    native.mkdir(parents=True, exist_ok=True)
    assert not (native / 'receipt.json').exists()
    app = modal.App('kltn-akt-' + RUN)
    volume = modal.Volume.from_name('kltn-akt-' + RUN, create_if_missing=True, version=1)
    worker = Path(__file__).parent / 'a0_lifecycle_worker.py'
    image = modal.Image.from_id('im-PcG3UeRJq1Qu86G1dHDXz8').add_local_file(
        worker, '/opt/a0_lifecycle_worker.py', copy=True)
    gate = ROOT / 'experiments/akt/results/modal-cpu-preflight-20261112-04/artifacts.zip'
    corpus = ROOT / 'artifacts/akt/modal/modal-a0-lifecycle-engineering10x84-20261112-01/public-corpus.zip'
    gate_receipt = json.loads((gate.parent / 'receipt.json').read_text())
    assert gate_receipt['status'] == 'MODAL_CPU_GATE_VERIFIED'
    assert gate_receipt['test_result'] == dict(passed=1994, failed=0, errors=0, skipped=0)
    assert hashlib.sha256(gate.read_bytes()).hexdigest() == gate_receipt['archive_sha256']
    corpus_plan = json.loads((Path(__file__).parent / 'next-lifecycle-plan.json').read_text())
    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == corpus_plan['archive_sha256']
    image = image.add_local_file(gate, '/opt/cpu-gate.zip', copy=True).add_local_file(
        corpus, '/opt/public-corpus.zip', copy=True)
    image = image.add_local_file(ROOT / 'artifacts/akt/modal/modal-checkpoint-pilot-20261112-10/source.zip', '/opt/kltn-input.zip', copy=True)

    sandbox = None
    with modal.enable_output():
        async with app.run.aio(environment_name='main'):
            try:
                sandbox = await modal.Sandbox.create.aio(
                    '/opt/kltn/.venv/bin/python', '-B', '/opt/a0_lifecycle_worker.py',
                    app=app, image=image, runtime='vm', cpu=(1, 2), memory=8192,
                    timeout=420, volumes={'/opt/kltn/experiments/akt/results': volume})
                (native / 'sandbox.json').write_text(json.dumps(dict(
                    sandbox_id=sandbox.object_id, runtime='vm', gpu=None)) + '\n')
                await asyncio.wait_for(sandbox.wait.aio(), 480)
                (native / 'stdout.log').write_text(await sandbox.stdout.read.aio())
                (native / 'stderr.log').write_text(await sandbox.stderr.read.aio())
                archive = native / 'artifacts.zip'
                with archive.open('xb') as stream:
                    async for block in volume.read_file.aio(RUN + '-operation/artifacts.zip'):
                        stream.write(block)
                with zipfile.ZipFile(archive) as saved:
                    assert saved.testzip() is None
                    inventory = json.loads(saved.read('SHA256.json'))
                    for name, expected in inventory.items():
                        raw = saved.read(name)
                        assert len(raw) == expected['bytes']
                        assert hashlib.sha256(raw).hexdigest() == expected['sha256']
                    result = json.loads(saved.read('experiments/akt/results/' + RUN + '-operation/result.json'))
                result.update(download_inventory_verified=True, runtime='vm',
                              archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
                (native / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
                print(json.dumps(result), flush=True)
                assert result['status'] == 'ACTUAL_A0_LINUX_SELECTED_ENGINEERING_COMPLETE'
            finally:
                if sandbox is not None:
                    await sandbox.terminate.aio()


if __name__ == '__main__':
    raise SystemExit('Launcher CPU đã lưu làm lịch sử. Lượt training hiện hành dùng experiments/akt/modal_a0_gpu_pilot.py trên GPU theo yêu cầu người dùng.')
