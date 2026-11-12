"""Gate Linux8GiB trước probe, cùng allocation0,50USD đã được duyệt."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).parent
RUN='modal-junyi-optimization-cpu-20261112-01'
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
os.environ['MODAL_PROFILE']='kltn'
sys.path.insert(0,str(ROOT/'experiments/akt'))
import modal
from modal_budget_guard import ModalRunDeadline,ModalAppBudgetGuard,PendingOwnedModalApp,stop_owned_app_cli
from modal_graph_selected import read_billing


async def main():
    allocation=json.loads((BUNDLE/'allocation.json').read_text())
    assert allocation['status']=='USER_APPROVED' and allocation['authorized_batch_usd']==.5
    billing=await read_billing()
    assert float(billing['billing']['metered_cost'])+.5<30
    with (BUNDLE/'billing-before.json').open('x') as stream:
        json.dump(billing,stream,indent=2)
    native=ROOT/'experiments/akt/results'/RUN
    native.mkdir(exist_ok=False)
    app=modal.App('kltn-akt-'+RUN)
    volume=modal.Volume.from_name('kltn-akt-'+RUN,create_if_missing=True,version=1)
    image=modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    image=image.add_local_file(BUNDLE/'cpu_worker.py','/opt/cpu_preflight_vm_worker.py',copy=True)
    image=image.add_local_file(ROOT/'artifacts/akt/modal/junyi-optimization-20261112-01/source.zip',
                               '/opt/kltn-input.zip',copy=True)
    sandbox=None
    deadline=ModalRunDeadline(580)
    try:
        with ModalAppBudgetGuard(PendingOwnedModalApp(RUN,app.name,lambda:app.app_id),deadline,
                stop_app=stop_owned_app_cli,diagnostic_path=native/'app-budget-guard.json') as guard:
            with modal.enable_output():
                async with app.run.aio(environment_name='main'):
                    sandbox=await modal.Sandbox.create.aio('/opt/kltn/.venv/bin/python','-B',
                        '/opt/cpu_preflight_vm_worker.py',app=app,image=image,runtime='vm',cpu=(1,2),
                        memory=8192,timeout=600,volumes={'/cpu-evidence':volume})
                    (native/'sandbox.json').write_text(json.dumps(dict(sandbox_id=sandbox.object_id)))
                    await asyncio.wait_for(sandbox.wait.aio(),guard.remaining())
                    (native/'stdout.log').write_text(await sandbox.stdout.read.aio())
                    (native/'stderr.log').write_text(await sandbox.stderr.read.aio())
    finally:
        if sandbox is not None:
            await sandbox.terminate.aio()
    archive=native/'artifacts.zip'
    with archive.open('xb') as stream:
        async for block in volume.read_file.aio(RUN+'/artifacts.zip'):
            stream.write(block)
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        for name,entry in json.loads(saved.read('SHA256.json')).items():
            raw=saved.read(name)
            assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
        result=json.loads(saved.read('result.json'))
    result.update(download_inventory_verified=True,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
    (native/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    assert result['status']=='MODAL_CPU_GATE_VERIFIED'


if __name__=='__main__':
    asyncio.run(main())
