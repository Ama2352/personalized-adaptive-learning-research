"""Chuẩn bị/chạy CPU03 bằng ba packet pinned, trần0,15USD và600giây VM."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUNDLE = Path(__file__).parent
RUN = 'modal-junyi-numerical-cpu-20261112-03'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source','data','checkpoint'):
        parser.add_argument('--'+name+'-zip',type=Path,required=True)
        parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--allocation-id',default='numerical-cpu03-20261112-01')
    parser.add_argument('--project-budget-file',type=Path,default=ROOT/'research_tracking/COMPUTE_BUDGET.json')
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    for name in ('source','data','checkpoint'):
        if sha(getattr(args,name+'_zip'))!=getattr(args,name+'_sha256'):
            raise ValueError(name+' archive pin mismatch')
    return args


async def main(args):
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
    sys.path.insert(0,str(ROOT/'experiments/akt'))
    import modal
    from modal_budget_guard import ModalRunDeadline,ModalAppBudgetGuard,PendingOwnedModalApp,stop_owned_app_cli
    from modal_graph_selected import read_billing
    from modal_junyi_numerical_probe import validate_project_budget
    request = dict(run_id=RUN,reserved_usd=.15,gpu=None,max_vm_seconds=600,
        allocation_id=args.allocation_id,authorized_batch_usd=.15,reserved_usd_per_run=.15,
        worker_sha256=sha(BUNDLE/'cpu03_worker.py'),diagnostic_sha256=sha(BUNDLE/'cpu_diagnostic.py'),
        archives={name:dict(sha256=getattr(args,name+'_sha256'),bytes=getattr(args,name+'_zip').stat().st_size)
                  for name in ('source','data','checkpoint')})
    print(json.dumps(dict(request=request,paid_execution_requested=args.run)),flush=True)
    if not args.run:
        return
    # Cận compute VM dùng2core/8GiB, giáSandbox3×, cộngdựphòng trong0,15USD.
    maximum_compute_usd = 600*(2*.00003942+8*.00000667)
    assert maximum_compute_usd<request['reserved_usd']<=.15
    billing = await read_billing()
    ledger_path = args.project_budget_file.resolve()
    if not ledger_path.is_relative_to((ROOT/'research_tracking').resolve()):
        raise ValueError('Owned project budget ledger required')
    ledger_sha256 = sha(ledger_path)
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    budget = validate_project_budget(ledger,request,float(billing['billing']['metered_cost']))
    if budget['per_run_reserved_usd']!=.15:
        raise PermissionError('CPU03 requires its explicit0.15USD reservation')
    request['project_budget_sha256'] = ledger_sha256
    ledger_path = ROOT/'research_tracking/COMPUTE_BUDGET.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    allocations = ledger['new_allocations']
    assert len({entry['id'] for entry in allocations})==len(allocations)
    assert any(entry['id']=='numerical-cpu03-20261112-01' and entry['cap_usd']==.15 for entry in allocations)
    envelope = max(ledger['historical_usage_reserved_upper_usd'],float(billing['billing']['metered_cost']))+ledger['safety_and_final_inference_reserve_usd']+sum(entry['cap_usd'] for entry in allocations)
    assert envelope<=ledger['total_project_credit_ceiling_usd']<=30
    request['project_budget_admission'] = dict(ledger_sha256=sha(ledger_path),conservative_envelope_usd=envelope)
    native = ROOT/'experiments/akt/results'/RUN
    native.mkdir(exist_ok=False)
    request_path = native/'request.json'
    request_path.write_text(json.dumps(request,indent=2)+'\n')
    (native/'billing-before.json').write_text(json.dumps(billing,indent=2)+'\n')
    (native/'reservation.json').write_text(json.dumps(dict(run_id=RUN,reserved_usd=.15,
        vm_maximum_compute_usd=maximum_compute_usd,automatic_retry=False,
        project_budget_sha256=ledger_sha256,decision=budget),indent=2)+'\n')
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name in ('source','data','checkpoint'):
        image = image.add_local_file(getattr(args,name+'_zip'),'/opt/junyi-'+name+'03.zip',copy=True)
    image = image.add_local_file(request_path,'/opt/junyi-cpu03-request.json',copy=True)
    image = image.add_local_file(BUNDLE/'cpu03_worker.py','/opt/junyi_cpu03_worker.py',copy=True)
    image = image.add_local_file(BUNDLE/'cpu_diagnostic.py','/opt/junyi_cpu_diagnostic.py',copy=True)
    app = modal.App('kltn-akt-'+RUN)
    volume = modal.Volume.from_name('kltn-akt-'+RUN,create_if_missing=True,version=1)
    sandbox = None
    deadline = ModalRunDeadline(580)
    if sha(ledger_path)!=ledger_sha256:
        raise ValueError('Project budget changed before CPU03 dispatch')
    try:
        with ModalAppBudgetGuard(PendingOwnedModalApp(RUN,app.name,lambda:app.app_id),deadline,
                stop_app=stop_owned_app_cli,diagnostic_path=native/'app-budget-guard.json') as guard:
            with modal.enable_output():
                async with app.run.aio(environment_name='main'):
                    sandbox = await modal.Sandbox.create.aio('/opt/kltn/.venv/bin/python','-B',
                        '/opt/junyi_cpu03_worker.py',app=app,image=image,runtime='vm',cpu=(1,2),
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
    assert result['status']=='CPU03_DIAGNOSTICS_COMPLETE_UNADMITTED'


if __name__=='__main__':
    asyncio.run(main(parse_args()))
