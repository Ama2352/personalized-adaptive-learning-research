"""CPU Gate nguồn A1 hiện hành, trần0,15USD với ledger toàn dự án."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = Path(__file__).parent
RUN = 'modal-junyi-refit-source-cpu-20261114-04'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-zip',type=Path,required=True)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--allocation-id',default='junyi-refit-source-cpu-20261114-04')
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    if sha(args.source_zip)!=args.source_sha256:
        raise ValueError('Source selection cache pin mismatch')
    return args


async def main(args):
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
    sys.path.insert(0,str(ROOT/'experiments/akt'))
    import modal
    from modal_budget_guard import ModalRunDeadline,ModalAppBudgetGuard,PendingOwnedModalApp,stop_owned_app_cli
    from modal_graph_selected import read_billing
    from modal_junyi_numerical_probe import validate_project_budget
    preparation = json.loads((BUNDLE/'source-gate-preparation.json').read_text(encoding='utf-8'))
    if preparation['source_sha256'] != args.source_sha256:
        raise ValueError('Prepared source freeze mismatch')
    if preparation['worker_sha256'] != sha(BUNDLE/'cpu_worker.py'):
        raise ValueError('Prepared worker changed')
    request = dict(run_id=RUN,reserved_usd=.15,authorized_batch_usd=.15,reserved_usd_per_run=.15,
        allocation_id=args.allocation_id,source_sha256=args.source_sha256,
        expected_source_build_sha256=preparation['source_build_sha256'],
        source_bytes=args.source_zip.stat().st_size,worker_sha256=sha(BUNDLE/'cpu_worker.py'),
        gpu=None,max_vm_seconds=600,numerical_diagnostic_repeated=False)
    print(json.dumps(dict(request=request,paid_execution_requested=args.run)),flush=True)
    if not args.run:
        return
    maximum_compute_usd = 600*(2*.00003942+8*.00000667)
    assert maximum_compute_usd<.15
    billing = await read_billing()
    ledger_path = ROOT/'research_tracking/COMPUTE_BUDGET.json'
    ledger_sha256 = sha(ledger_path)
    budget = validate_project_budget(json.loads(ledger_path.read_text()),request,
                                    float(billing['billing']['metered_cost']))
    request['project_budget_sha256'] = ledger_sha256
    native = ROOT/'experiments/akt/results'/RUN
    native.mkdir(exist_ok=False)
    request_path = native/'request.json'
    request_path.write_text(json.dumps(request,indent=2)+'\n')
    (native/'billing-before.json').write_text(json.dumps(billing,indent=2)+'\n')
    (native/'reservation.json').write_text(json.dumps(dict(run_id=RUN,reserved_usd=.15,
        maximum_compute_usd=maximum_compute_usd,automatic_retry=False,
        project_budget_sha256=ledger_sha256,budget_decision=budget),indent=2)+'\n')
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    image = image.add_local_file(args.source_zip,'/opt/junyi-a1-source.zip',copy=True)
    image = image.add_local_file(BUNDLE/'cpu_worker.py','/opt/junyi_cpu_worker.py',copy=True)
    image = image.add_local_file(request_path,'/opt/junyi-selection-cpu-request.json',copy=True)
    app = modal.App('kltn-akt-'+RUN)
    volume = modal.Volume.from_name('kltn-akt-'+RUN,create_if_missing=True,version=1)
    sandbox = None
    deadline = ModalRunDeadline(580)
    if sha(ledger_path)!=ledger_sha256:
        raise ValueError('Project budget changed before CPU selection cache dispatch')
    try:
        with ModalAppBudgetGuard(PendingOwnedModalApp(RUN,app.name,lambda:app.app_id),deadline,
                stop_app=stop_owned_app_cli,diagnostic_path=native/'app-budget-guard.json') as guard:
            with modal.enable_output():
                async with app.run.aio(environment_name='main'):
                    sandbox = await modal.Sandbox.create.aio('/opt/kltn/.venv/bin/python','-B',
                        '/opt/junyi_cpu_worker.py',app=app,image=image,runtime='vm',cpu=(1,2),
                        memory=8192,timeout=600,volumes={'/cpu-evidence':volume})
                    (native/'sandbox.json').write_text(json.dumps(dict(sandbox_id=sandbox.object_id,
                        runtime='vm',gpu=None))+'\n')
                    await asyncio.wait_for(sandbox.wait.aio(),guard.remaining())
                    (native/'stdout.log').write_text(await sandbox.stdout.read.aio())
                    (native/'stderr.log').write_text(await sandbox.stderr.read.aio())
    finally:
        if sandbox is not None:
            await sandbox.terminate.aio()
    archive = native/'artifacts.zip'
    with archive.open('xb') as stream:
        async for block in volume.read_file.aio(RUN+'/artifacts.zip'):
            stream.write(block)
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        inventory = json.loads(saved.read('SHA256.json'))
        assert set(saved.namelist())==set(inventory)|{'SHA256.json'}
        for name,entry in inventory.items():
            raw = saved.read(name)
            assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
        result = json.loads(saved.read('result.json'))
    result.update(download_inventory_verified=True,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size)
    (native/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    assert result['status']=='MODAL_CPU_GATE_VERIFIED'


if __name__=='__main__':
    asyncio.run(main(arguments()))
