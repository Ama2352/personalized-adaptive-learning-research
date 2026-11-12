"""Đo engineering Junyi trên packet cố định, một GPU có giới hạn."""
import argparse
import asyncio
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT/'research_tracking/runs/junyi-batch-throughput-20261112-01'
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
    if not 0<reserve<=authorized<=caps[request['allocation_id']]<=Decimal('.2'):
        raise PermissionError('Numerical probe must fit its explicit0.20USD allocation')
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


def remote_probe(pins, run_id):
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
    durable.mkdir(exist_ok=False)
    volume = modal.Volume.from_name('kltn-akt-'+run_id)
    process = None
    started = time.monotonic()
    summary = dict(status='FAILED',run_id=run_id,checkpoint_transfers={})
    concurrent_scope = json.loads(Path('/opt/probe-request.json').read_text()).get('scope') == 'engineering_concurrent_gpu_only'

    def sync_checkpoints(*, final=False):
        markers = [(marker.parent.name,marker) for marker in sorted(
            (results/run_id/'checkpoints').glob('*/COMPLETE.json'))]
        if concurrent_scope:
            for label in ('solo-a','solo-b','parallel-a','parallel-b'):
                marker = results/(run_id+'-'+label)/'checkpoints/batch-032/COMPLETE.json'
                if marker.is_file():
                    markers.append((label,marker))
        for name,marker in markers:
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
                assert time.monotonic()-started<380,'Probe remote wall deadline'
                sync_checkpoints()
                if process.poll() is not None:
                    sync_checkpoints(final=True)
                    break
                time.sleep(.5)
        summary['returncode'] = process.returncode
        actual = json.loads((results/(run_id+'-operation')/'result.json').read_text())
        summary['worker_result'] = actual
        assert process.returncode==0 and actual['status'] in ('JUNYI_BATCH_PROFILE_COMPLETE','JUNYI_STEP_SYNC_PROFILE_COMPLETE','JUNYI_BATCH_UTILIZATION_COMPLETE','JUNYI_CONCURRENT_GPU_COMPLETE','PARTIAL_JUNYI_BATCH_PROFILE_OOM'),actual
        if actual['status'] in ('JUNYI_BATCH_PROFILE_COMPLETE','JUNYI_STEP_SYNC_PROFILE_COMPLETE','JUNYI_BATCH_UTILIZATION_COMPLETE','JUNYI_CONCURRENT_GPU_COMPLETE'):
            expected_checkpoints = {'JUNYI_BATCH_PROFILE_COMPLETE':4,
                                    'JUNYI_STEP_SYNC_PROFILE_COMPLETE':6,
                                    'JUNYI_BATCH_UTILIZATION_COMPLETE':1,
                                    'JUNYI_CONCURRENT_GPU_COMPLETE':4}[actual['status']]
            assert len(summary['checkpoint_transfers'])==expected_checkpoints,'Completed case checkpoints required'
        else:
            assert len(summary['checkpoint_transfers'])>=len(actual['cases'])
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
        for path in (results/run_id/'batch-recovery').glob('*.pt'):
            envelope = results/run_id/'checkpoints'/path.stem/'state.pt'
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
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as saved:
            directories = [driver,results/run_id,results/(run_id+'-operation')]
            if concurrent_scope:
                directories.extend(results/(run_id+'-'+label) for label in (
                    'solo-a','solo-b','parallel-a','parallel-b'))
            for directory in directories:
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
    parser.add_argument('--gpu',choices=('T4','L4','SMALL'),default='T4')
    parser.add_argument('--run',action='store_true')
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding='utf-8'))
    profiles = {
        'engineering_step_sync_profile_only':
            ('gpu_worker.py', 'model-candidate.py', None, 'reservation.json'),
        'engineering_attention_transfer_profile_only':
            ('gpu_worker02.py', 'model-attention-candidate.py', 'attention_candidate.py', 'reservation02.json'),
        'engineering_attention_cache_profile_only':
            ('gpu_worker03.py', 'model-attention-cache-candidate.py', 'attention_cache_candidate.py', 'reservation03.json'),
        'engineering_batch32_utilization_only':
            ('gpu_worker.py', None, None, 'reservation.json'),
        'engineering_concurrent_gpu_only':
            ('gpu_worker.py', None, None, 'reservation.json'),
    }
    profile = profiles.get(request.get('scope'))
    step_profile = profile is not None
    worker_name, candidate_name, module_name, reservation_name = profile or (
        'gpu_worker.py', None, None, 'reservation.json')
    bundle = BUNDLE
    batch_utilization = request.get('scope') == 'engineering_batch32_utilization_only'
    concurrent_probe = request.get('scope') == 'engineering_concurrent_gpu_only'
    if step_profile:
        bundle = args.request.resolve().parent
        expected_bundle = 'junyi-batch32-utilization-20261112-01' if batch_utilization else 'junyi-step-sync-20261112-01'
        if concurrent_probe:
            expected_bundle = 'junyi-concurrent-gpu-20261112-01'
        assert bundle == ROOT/'research_tracking/runs'/expected_bundle
    assert args.gpu==request.get('gpu','T4')
    assert args.gpu=='T4' or concurrent_probe
    if concurrent_probe and args.gpu=='L4':
        reservation_name = 'reservation02.json'
    if concurrent_probe and args.gpu=='SMALL':
        reservation_name = 'reservation03.json'
    if concurrent_probe and 'reservation_file' in request:
        assert re.fullmatch(r'reservation[0-9]{2}\.json',request['reservation_file'])
        reservation_name = request['reservation_file']
    run_id = request['run_id']
    prefix = 'step-sync' if step_profile else 'batch-throughput'
    if batch_utilization:
        prefix = 'batch-utilization'
    if concurrent_probe:
        prefix = 'concurrent'
    assert re.fullmatch(r'modal-junyi-'+prefix+'-'+args.gpu.lower()+r'-[0-9]{8}-[0-9]{2}',run_id)
    print(json.dumps(dict(run_id=run_id,gpu=args.gpu,status=request['status'],execution_requested=args.run)),flush=True)
    if not args.run:
        return
    assert request['status']=='USER_APPROVED' and request['approval_reference'].strip()
    if step_profile:
        previous_guard = (ROOT/request['prior_a0_stop_evidence']).resolve()
        assert previous_guard.is_relative_to(ROOT/'experiments/akt/results')
        assert json.loads(previous_guard.read_text())['stop_acknowledged'] is True
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
    worker_request = dict(request,run_id=run_id,gpu=args.gpu)
    worker_request_path = native/'worker-request.json'
    worker_request_path.write_text(json.dumps(worker_request,indent=2))
    paths = {'/opt/junyi-numerical-worker.py':bundle/worker_name,
             '/opt/checkpoint-sync.py':ROOT/'experiments/akt/modal_artifact_sync.py',
             '/opt/probe-request.json':worker_request_path,
             '/opt/packet_reader.py':ROOT/'research_tracking/runs/junyi-throughput-20261112-01/packet_reader.py'}
    if concurrent_probe:
        paths['/opt/concurrent_child.py'] = bundle/'concurrent_child.py'
    if candidate_name is not None:
        paths.update({'/opt/model-candidate.py':bundle/candidate_name,
                      '/opt/model-before.py':bundle/'model-before.py',
                      '/opt/verify_equivalence.py':bundle/'verify_equivalence.py'})
        if module_name is not None:
            paths['/opt/'+module_name] = bundle/module_name
    for key,target in (('source','/opt/kltn-input.zip'),('cpu_gate','/opt/cpu-gate.zip'),('data','/opt/junyi-data.zip')):
        relative = Path(request['archives'][key]['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        path = (ROOT/relative).resolve()
        assert path.is_relative_to(ROOT/'artifacts/akt') or path.is_relative_to(ROOT/'experiments/akt/results')
        assert sha(path)==request['archives'][key]['sha256']
        paths[target] = path
    pins = {name:sha(path) for name,path in paths.items()}
    assert pins['/opt/packet_reader.py']==request['reader_sha256'],'Frozen packet reader changed'
    assert sha(ledger_path)==ledger_sha256,'Project budget changed before reservation'
    with (bundle/reservation_name).open('x') as stream:
        json.dump(dict(run_id=run_id,gpu=args.gpu,reserved_usd=reserve,inputs=pins,
            allocation_id=request['allocation_id'],project_budget_sha256=ledger_sha256,
            budget_admission=budget),stream,indent=2)
    deadline = ModalRunDeadline(340 if args.gpu=='SMALL' else 400)
    app = modal.App('kltn-akt-'+run_id)
    volume = modal.Volume.from_name('kltn-akt-'+run_id,create_if_missing=True,version=2)
    image = modal.Image.from_id('im-ldjZsYO21pzaupmQXGLhnS')
    for name,path in paths.items():
        image = image.add_local_file(path,name,copy=not (batch_utilization or concurrent_probe))
    cpu_limit = (.25,4) if concurrent_probe else (.25,2)
    memory_limit = (4096,12288) if concurrent_probe else (4096,8192)
    gpu_selection = ['T4','L4','A10'] if args.gpu=='SMALL' else args.gpu
    function = app.function(image=image,gpu=gpu_selection,cpu=cpu_limit,memory=memory_limit,
        timeout=360 if args.gpu=='SMALL' else 420,startup_timeout=60,retries=0,max_containers=1,scaledown_window=60,
        volumes={'/durable':volume})(remote_probe)
    try:
        binding = PendingOwnedModalApp(run_id,app.name,lambda:app.app_id)
        with ModalAppBudgetGuard(binding,deadline,stop_app=stop_owned_app_cli,
                                 diagnostic_path=native/'app-budget-guard.json') as guard:
            with modal.enable_output(),app.run(environment_name='main'):
                guard.remaining()
                call = function.spawn(pins,run_id)
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
    assert receipt['status'] in ('JUNYI_BATCH_PROFILE_COMPLETE','JUNYI_STEP_SYNC_PROFILE_COMPLETE','JUNYI_BATCH_UTILIZATION_COMPLETE','JUNYI_CONCURRENT_GPU_COMPLETE','PARTIAL_JUNYI_BATCH_PROFILE_OOM')


if __name__=='__main__':
    main()
