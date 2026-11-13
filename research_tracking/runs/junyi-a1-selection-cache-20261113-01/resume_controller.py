"""Phục hồi A0 Junyi selected trong container T4 mới, giữ logical identity."""
import argparse
import asyncio
from decimal import Decimal
import hashlib
import json
import math
import os
import time
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent.parent
import sys
sys.path.insert(0,str(ROOT/'experiments/akt'))
BUNDLE = Path(__file__).resolve().parent
if __name__ == '__main__':
    import tempfile
    client_temp = ROOT/'artifacts/akt/runtime/modal-client-temp'
    client_temp.mkdir(parents=True,exist_ok=True)
    for variable in ('TEMP','TMP','TMPDIR'):
        os.environ[variable] = str(client_temp)
    tempfile.tempdir = str(client_temp)
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
import modal


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def validate_project_budget(ledger, request, metered_usd):
    """Kiểm trần toàn KLTN, cap lượt chạy độc lập các billing delta cũ."""
    def amount(value):
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:
            raise ValueError('Finite nonnegative credit reservation required')
        return Decimal(str(value))
    if (ledger.get('status')!='USER_PREAPPROVED_BOUNDED_TRANCHES_TOTAL_PROJECT_CAP'
            or ledger.get('extra_payment_allowed') is not False
            or ledger.get('automatic_monthly_budget_reset') is not False):
        raise PermissionError('Explicit total-project free-credit policy required')
    ceiling = amount(ledger['total_project_credit_ceiling_usd'])
    if not 0<ceiling<=30:
        raise ValueError('Project credit ceiling must stay within30USD')
    allocations = ledger['new_allocations']
    identifiers = [entry['id'] for entry in allocations]
    if len(identifiers)!=len(set(identifiers)) or request['allocation_id'] not in identifiers:
        raise ValueError('Unique declared project allocation required')
    caps = {entry['id']:amount(entry['cap_usd']) for entry in allocations}
    authorized = amount(request['authorized_batch_usd'])
    reserve = amount(request['reserved_usd_per_run'])
    run_cap = Decimal('3') if request.get('gpu')=='H100' else Decimal('.85')
    if not 0<reserve<=authorized<=caps[request['allocation_id']]<=run_cap:
        raise PermissionError('Main selected exceeds its declared GPU allocation')
    historical = amount(ledger['historical_usage_reserved_upper_usd'])
    metered = amount(metered_usd)
    safety = amount(ledger['safety_and_final_inference_reserve_usd'])
    allocated = sum(caps.values(),Decimal(0))
    conservative = max(historical,metered)+safety+allocated
    if conservative>ceiling:
        raise PermissionError('Total KLTN credit envelope exhausted')
    return dict(allocation_id=request['allocation_id'],per_run_reserved_usd=float(reserve),
        historical_reserved_upper_usd=float(historical),provider_metered_usd=float(metered),
        safety_reserve_usd=float(safety),all_new_allocation_caps_usd=float(allocated),
        conservative_project_envelope_usd=float(conservative),project_ceiling_usd=float(ceiling))


def remote_probe(pins, run_id, logical_run_id, volume_name):
    import runpy
    import signal
    import subprocess
    import time
    import traceback
    root = Path('/opt/kltn')
    results = root/'experiments/akt/results'
    results.mkdir(parents=True,exist_ok=True)
    driver = results/(run_id+'-driver')
    driver.mkdir(exist_ok=False)
    durable = Path('/durable')/run_id
    volume = modal.Volume.from_name(volume_name)
    if durable.exists():
        pinned_inputs=durable/'input-pins.json'
        if pinned_inputs.exists():
            assert json.loads(pinned_inputs.read_text())==pins,'Repeated execution input changed'
        saved_receipt=durable/'receipt.json'
        if saved_receipt.is_file():
            return json.loads(saved_receipt.read_text())
        index=durable/'checkpoint-index.json'
        return dict(status='PREEMPTED_RECOVERY_REQUIRED',run_id=run_id,
                    checkpoint_transfers=json.loads(index.read_text()) if index.exists() else {},
                    original_work_not_restarted=True)
    durable.mkdir(exist_ok=False)
    (durable/'input-pins.json').write_text(json.dumps(pins,indent=2))
    volume.commit()
    process = None
    started = time.monotonic()
    summary = dict(status='FAILED',run_id=run_id,checkpoint_transfers={})
    controls_done=False

    def sync_controls():
        nonlocal controls_done
        if controls_done:
            return
        names=('run-manifest.json','initial-backbone.json')
        sources=[results/logical_run_id/name for name in names]
        if not all(path.is_file() for path in sources):
            return
        destination=durable/'run-control'
        destination.mkdir(exist_ok=True)
        entries={}
        for path in sources:
            raw=path.read_bytes()
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                return
            (destination/path.name).write_bytes(raw)
            entries[path.name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        (destination/'COMPLETE.json').write_text(json.dumps(dict(files=entries),indent=2))
        volume.commit()
        (results/(run_id+'-operation')/'control-durable-ack.json').write_text(
            json.dumps(dict(status='CONTROLS_DURABLE',files=entries),indent=2))
        summary['durable_control_files']=entries
        controls_done=True

    def sync_checkpoints(*, final=False):
        for marker in sorted((results/logical_run_id/'checkpoints').glob('*/COMPLETE.json')):
            name = marker.parent.name
            if name in summary['checkpoint_transfers']:
                continue
            try:
                transfer = copier(marker.parent,durable/'checkpoints'/name)
            except json.JSONDecodeError:
                if final:
                    raise
                continue
            transfer['files'] = {p.name:dict(bytes=p.stat().st_size,sha256=sha(p))
                                 for p in marker.parent.iterdir()}
            summary['checkpoint_transfers'][name] = transfer
            (durable/'checkpoint-index.json').write_text(json.dumps(summary['checkpoint_transfers'],indent=2))
            volume.commit()
    try:
        for name,digest in pins.items():
            assert sha(Path(name))==digest
        copier = runpy.run_path('/opt/checkpoint-sync.py')['copy_complete_checkpoint']
        with (driver/'worker.log').open('xb') as log:
            process = subprocess.Popen([str(root/'.venv/bin/python'),'-B','/opt/junyi-numerical-worker.py'],
                cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            while True:
                assert time.monotonic()-started<1650,'Main selected child deadline'
                sync_controls()
                sync_checkpoints()
                if process.poll() is not None:
                    sync_checkpoints(final=True)
                    break
                time.sleep(.5)
        summary['returncode'] = process.returncode
        actual = json.loads((results/(run_id+'-operation')/'result.json').read_text())
        summary['worker_result'] = actual
        assert process.returncode==0 and actual['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A1_SELECTED_ONLY_COMPLETE'),actual
        assert summary['checkpoint_transfers'],'No durable checkpoint published'
        summary['status'] = actual['status']
    except BaseException as error:
        summary.update(error_type=type(error).__name__,error=str(error))
        (driver/'failure.log').write_text(traceback.format_exc())
    finally:
        if process is not None and process.poll() is None:
            assert process.pid>1 and process.pid!=os.getpgrp()
            for sig in (signal.SIGTERM,signal.SIGKILL):
                try:
                    os.killpg(process.pid,sig)
                except ProcessLookupError:
                    pass
            process.wait(timeout=10)
        summary['elapsed_seconds'] = time.monotonic()-started
        (driver/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        exclusions = {}
        for path in (results/logical_run_id/'batch-recovery').glob('*.pt'):
            envelope = results/logical_run_id/'checkpoints'/path.stem/'state.pt'
            if path.stem in summary['checkpoint_transfers'] and envelope.is_file():
                digest = sha(path)
                assert digest==sha(envelope) and path.stat().st_size==envelope.stat().st_size
                exclusions[path.relative_to(root).as_posix()] = dict(bytes=path.stat().st_size,
                    sha256=digest,identical_archive_member=envelope.relative_to(root).as_posix())
        (driver/'archive-exclusions.json').write_text(json.dumps(dict(
            reason='Raw batch recovery hardlink has identical verified checkpoint envelope in archive and Volume',
            excluded_files=exclusions),indent=2)+'\n')
        archive = durable/'artifacts.zip'
        inventory = {}
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as saved:
            for directory in (driver,results/logical_run_id,results/(run_id+'-operation')):
                for path in directory.rglob('*'):
                    if path.is_file():
                        name = path.relative_to(root).as_posix()
                        if name in exclusions:
                            continue
                        inventory[name] = dict(bytes=path.stat().st_size,sha256=sha(path))
                        saved.write(path,name)
            saved.writestr('SHA256.json',json.dumps(inventory,indent=2))
        summary.update(archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
                       total_remote_seconds=time.monotonic()-started)
        (durable/'receipt.json').write_text(json.dumps(summary,indent=2)+'\n')
        volume.commit()
    return summary


def main():
    from modal_graph_selected import read_billing
    from modal_budget_guard import (ModalAppBudgetGuard,ModalRunDeadline,
                                    PendingOwnedModalApp,stop_owned_app_cli)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--gpu',choices=('T4','H100'),default='T4')
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding='utf-8'))
    assert args.gpu==request.get('gpu','T4')
    h100_batch128 = args.gpu=='H100'
    bundle = BUNDLE
    if h100_batch128:
        bundle = args.request.resolve().parent
        assert bundle==BUNDLE
        assert request['batch_size']==128 and request['benchmark_before_training'] is False
    run_id = request['run_id']
    pattern = r'modal-junyi-a1-b128-h100-[0-9]{8}-[0-9]{2}' if h100_batch128 else r'modal-junyi-main-selected-t4-[0-9]{8}-[0-9]{2}'
    assert re.fullmatch(pattern,run_id)
    print(json.dumps(dict(run_id=run_id,gpu=args.gpu,status=request['status'],execution_requested=args.run)),flush=True)
    if not args.run:
        return
    assert request['status']=='USER_APPROVED' and request['approval_reference'].strip()
    assert request['root_review_status']=='ROOT_REVIEWED_BOUNDED_DISPATCH'
    billing = asyncio.run(read_billing())
    metered = float(billing['billing']['metered_cost'])
    assert request['project_budget_file']=='research_tracking/COMPUTE_BUDGET.json'
    ledger_path = ROOT/request['project_budget_file']
    ledger_sha256 = sha(ledger_path)
    budget = validate_project_budget(json.loads(ledger_path.read_text(encoding='utf-8')),request,metered)
    reserve = budget['per_run_reserved_usd']
    native = ROOT/'experiments/akt/results'/run_id
    native.mkdir(exist_ok=False)
    (native/'billing-before.json').write_text(json.dumps(billing,indent=2))
    (native/'project-budget-admission.json').write_text(json.dumps(dict(
        ledger_sha256=ledger_sha256,decision=budget),indent=2)+'\n')
    worker_request = dict(request,run_id=run_id,gpu=args.gpu,local_deadline_unix=time.time()+1700)
    worker_request_path = native/'worker-request.json'
    worker_request_path.write_text(json.dumps(worker_request,indent=2))
    paths = {'/opt/junyi-numerical-worker.py':bundle/'resume_worker.py',
             '/opt/checkpoint-sync.py':ROOT/'experiments/akt/modal_artifact_sync.py',
             '/opt/probe-request.json':worker_request_path}
    paths['/opt/a0-reused-reference.json']=bundle/'a0-batched-comparison-reference03.json'
    paths['/opt/a0-reused-replay.json']=bundle/'a0-validation-replay03.json'
    for key,target in (('source','/opt/kltn-input.zip'),('cpu_gate','/opt/cpu-gate.zip'),('data','/opt/junyi-data.zip'),('resume_control','/opt/resume-control.zip')):
        relative = Path(request['archives'][key]['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = (ROOT/relative).resolve()
        assert path.is_relative_to(ROOT/'artifacts/akt') or path.is_relative_to(ROOT/'experiments/akt/results')
        assert sha(path)==request['archives'][key]['sha256']
        paths[target] = path
    pins = {name:sha(path) for name,path in paths.items()}
    assert sha(ledger_path)==ledger_sha256,'Project budget changed before reservation'
    with (native/'reservation.json').open('x') as stream:
        json.dump(dict(run_id=run_id,gpu=args.gpu,reserved_usd=reserve,inputs=pins,
            allocation_id=request['allocation_id'],project_budget_sha256=ledger_sha256,
            budget_admission=budget),stream,indent=2)
    deadline = ModalRunDeadline(1700 if h100_batch128 else 3200)
    app = modal.App('kltn-akt-'+run_id)
    volume_name = 'kltn-akt-'+request['logical_run_id']
    volume = modal.Volume.from_name(volume_name,create_if_missing=False,version=2)
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name,path in paths.items():
        image = image.add_local_file(path,name,copy=not h100_batch128)
    cpu_limit = (.25,4) if h100_batch128 else (.25,2)
    memory_limit = (4096,12288) if h100_batch128 else (4096,8192)
    gpu_specification = 'H100!' if h100_batch128 else args.gpu
    function = app.function(image=image,gpu=gpu_specification,cpu=cpu_limit,memory=memory_limit,
        timeout=1800 if h100_batch128 else 3300,startup_timeout=60,retries=0,max_containers=1,scaledown_window=2,
        volumes={'/durable':volume})(remote_probe)
    try:
        binding = PendingOwnedModalApp(run_id,app.name,lambda:app.app_id)
        with ModalAppBudgetGuard(binding,deadline,stop_app=stop_owned_app_cli,
                                 diagnostic_path=native/'app-budget-guard.json') as guard:
            with modal.enable_output(),app.run(environment_name='main'):
                guard.remaining()
                call = function.spawn(pins,run_id,request['logical_run_id'],volume_name)
                (native/'dispatch.json').write_text(json.dumps(dict(call_id=call.object_id,app_id=app.app_id)))
                receipt = call.get(timeout=guard.remaining())
                (native/'remote-receipt.json').write_text(json.dumps(receipt,indent=2))
    except BaseException:
        # Checkpoint đã sync vẫn được giữ ở Volume khi App bị watchdog dừng.
        try:
            with (native/'durable-checkpoint-index.json').open('xb') as stream:
                for block in volume.read_file(run_id+'/checkpoint-index.json'):
                    stream.write(block)
        except Exception as recovery_error:
            (native/'recovery-index-error.txt').write_text(str(recovery_error))
        raise
    if receipt['status']=='PREEMPTED_RECOVERY_REQUIRED':
        (native/'preemption-receipt.json').write_text(json.dumps(receipt,indent=2))
        print(json.dumps(receipt),flush=True)
        return
    archive = native/'artifacts.zip'
    with archive.open('xb') as stream:
        for block in volume.read_file(run_id+'/artifacts.zip'):
            stream.write(block)
    assert sha(archive)==receipt['archive_sha256'] and archive.stat().st_size==receipt['archive_bytes']
    with zipfile.ZipFile(archive) as saved:
        assert saved.testzip() is None
        inventory = json.loads(saved.read('SHA256.json'))
        assert set(saved.namelist())==set(inventory)|{'SHA256.json'}
        for name,entry in inventory.items():
            with saved.open(name) as stream:
                assert hashlib.file_digest(stream,'sha256').hexdigest()==entry['sha256']
    receipt['download_inventory_verified'] = True
    (native/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt),flush=True)
    assert receipt['status'] in ('PARTIAL_SELECTED_ONLY_NOT_FINAL','JUNYI_A1_SELECTED_ONLY_COMPLETE')


if __name__=='__main__':
    main()

