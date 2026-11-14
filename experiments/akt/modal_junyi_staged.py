"""CPU local chuẩn bị/thu artifact, một function GPU chỉ chạy numerical worker.

Mặc định chỉ đọc snapshot. --run mới upload hoặc tạo tài nguyên Modal.
Tái dùng budget guard toàn KLTN; GPU phải dừng trước download/nén local.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent.parent


def cpu_mount_preflight(execution_id):
    """Kiểm mount và byte thực tế trên CPU provider trước khi gọi GPU."""
    import hashlib
    import json
    import os
    from pathlib import Path
    import subprocess
    import time
    started=time.monotonic()
    root=Path('/opt/kltn')
    inventory=json.loads((root/'staged-input-inventory.json').read_text())
    for index,(name,pin) in enumerate(inventory['files'].items(),1):
        path=root/name
        with path.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        if path.stat().st_size!=pin['bytes'] or digest!=pin['sha256']:
            raise ValueError('Input provider khác snapshot local: '+name)
        if index%250==0:
            print(json.dumps(dict(checked_files=index,seconds=time.monotonic()-started)),flush=True)
    hashing_seconds=time.monotonic()-started
    environment=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_COUNT='3',
        GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=str(root/'artifacts/akt/dependencies/upstream'),
        GIT_CONFIG_KEY_2='core.autocrlf',GIT_CONFIG_VALUE_2='false')
    operation=root/'experiments/akt/results'/(execution_id+'-cpu-preflight')
    operation.mkdir(parents=True)
    script=('import sys;sys.path.insert(0,"/opt/kltn/scripts/akt");'
        'from pathlib import Path;from run_junyi_gpu_stage import prepare_runtime_report;'
        'prepare_runtime_report(Path("/opt/kltn"),Path(sys.argv[1]),'
        'Path("/opt/kltn/artifacts/akt/dependencies/upstream"),Path("/opt/locked-cu126.txt"),"cpu")')
    worker=json.loads((root/'gpu-stage-request.json').read_text())
    if worker.get('purpose')=='refit90':
        script+=(';import json;from run_junyi_refit import pinned,prepare_inputs;'
            'w=json.loads(Path("/opt/kltn/gpu-stage-request.json").read_text());'
            'c=prepare_inputs(json.loads(pinned(w["refit_request"]).read_text()));'
            'Path(sys.argv[1],"refit-inputs.json").write_text(json.dumps(dict('
            'status="PASS_REFIT90_PROVIDER_INPUTS",variant=w["variant"],'
            'targets=c["inputs"].targets,encoding=c["encoding"].identity,plan=c["plan"]["identity"])))')
    try:
        subprocess.run([str(root/'.venv/bin/python'),'-B','-c',script,str(operation)],
            env=environment,capture_output=True,text=True,check=True,timeout=120)
    except subprocess.CalledProcessError as error:
        print(error.stderr,flush=True)
        raise
    runtime=json.loads((operation/'runtime.json').read_text())
    return dict(status='PASS_STAGED_PROVIDER_INPUTS',files=len(inventory['files']),torch=runtime['torch_version'],
                runtime=runtime,
                refit_inputs=(json.loads((operation/'refit-inputs.json').read_text())
                              if worker.get('purpose')=='refit90' else None),
                hashing_seconds=hashing_seconds,total_seconds=time.monotonic()-started)


def gpu_compute(execution, volume_name):
    """Không giải nén input và không nén output trong container GPU."""
    import csv
    import modal
    import signal
    import traceback
    root = Path('/opt/kltn')
    results = root/'experiments/akt/results'
    operation = results/(execution['execution_id']+'-operation')
    volume = modal.Volume.from_name(volume_name, version=2)
    if operation.exists():
        previous = json.loads((operation/'execution.json').read_text())
        if previous != execution:
            raise ValueError('Execution ID cũ có cấu hình khác')
        receipt = operation/'remote-inventory.json'
        if receipt.exists():
            return json.loads(receipt.read_text())
        raise RuntimeError('Lượt cũ bị gián đoạn; dùng execution ID mới và checkpoint đã kiểm')
    operation.mkdir(parents=True)
    (operation/'execution.json').write_text(json.dumps(execution,indent=2))
    worker_request = root/'gpu-stage-request.json'
    if hashlib.sha256(worker_request.read_bytes()).hexdigest()!=execution['worker_request_sha256']:
        raise ValueError('Worker request thay đổi')
    request = json.loads(worker_request.read_text())
    entrypoint = execution.get('worker_entrypoint', 'run_junyi_gpu_stage.py')
    if entrypoint not in ('run_junyi_gpu_stage.py', 'run_junyi_refit_gpu_stage.py'):
        raise ValueError('Numerical worker entrypoint ngoài allowlist')
    process = None
    started = time.monotonic()
    checkpoint_markers = set()
    try:
        with (operation/'worker.log').open('xb') as log, (operation/'gpu-telemetry.jsonl').open('x') as telemetry:
            process = subprocess.Popen([str(root/'.venv/bin/python'),'-B',
                str(root/'scripts/akt'/entrypoint),'--request',str(worker_request),
                '--execution',str(operation/'execution.json')], cwd=root,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            while True:
                if time.monotonic()-started>execution['child_timeout_seconds']:
                    raise TimeoutError('Numerical worker vượt thời gian đã duyệt')
                current = {path.parent.name for path in (results/request['logical_run_id']/'checkpoints').glob('*/COMPLETE.json')}
                if current!=checkpoint_markers:
                    # File COMPLETE chỉ được producer ghi sau state+metadata.
                    checkpoint_files={}
                    for marker in sorted((results/request['logical_run_id']/'checkpoints').glob('*/COMPLETE.json')):
                        metadata=json.loads((marker.parent/'metadata.json').read_text())
                        complete=json.loads(marker.read_text())
                        raw_metadata=(marker.parent/'metadata.json').read_bytes()
                        if hashlib.sha256(raw_metadata).hexdigest()!=complete['metadata_sha256']:
                            raise ValueError('Checkpoint metadata chưa hoàn tất')
                        for filename in ('state.pt','metadata.json','COMPLETE.json'):
                            path=marker.parent/filename
                            if filename=='state.pt':
                                digest=complete['checkpoint_sha256']
                                if path.stat().st_size!=metadata['checkpoint_bytes']:
                                    raise ValueError('Checkpoint state sai kích thước')
                            else:
                                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                            checkpoint_files['outputs/'+path.relative_to(results).as_posix()]=dict(
                                bytes=path.stat().st_size,sha256=digest)
                    index=operation/'checkpoint-index.json'
                    temporary=operation/'checkpoint-index.writing.json'
                    temporary.write_text(json.dumps(dict(status='CHECKPOINT_RECOVERY_INDEX',files=checkpoint_files)))
                    temporary.replace(index)
                    volume.commit()
                    checkpoint_markers=current
                query=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total,power.draw',
                    '--format=csv,noheader,nounits'],check=True,capture_output=True,text=True,timeout=5)
                values=next(csv.reader(query.stdout.splitlines()))
                telemetry.write(json.dumps(dict(seconds=time.monotonic()-started,
                    gpu_utilization=float(values[0]),vram_used_mib=float(values[1]),
                    vram_total_mib=float(values[2]),power_w=float(values[3])))+'\n')
                telemetry.flush()
                if process.poll() is not None:
                    break
                time.sleep(2)
    except BaseException:
        (operation/'controller-failure.log').write_text(traceback.format_exc())
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid,signal.SIGTERM)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait(timeout=8)
        volume.commit()
    actual_path=operation/'result.json'
    actual=json.loads(actual_path.read_text()) if actual_path.exists() else dict(status='FAILED')
    if process is None or process.returncode!=0 or (operation/'controller-failure.log').exists():
        actual=dict(actual,status='FAILED',numerical_status=actual.get('status'))
    inventory={}
    for folder in (operation,results/request['logical_run_id']):
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            if path.is_symlink():
                raise ValueError('Output symlink không được chuyển')
            with path.open('rb') as stream:
                digest=hashlib.file_digest(stream,'sha256').hexdigest()
            inventory['outputs/'+path.relative_to(results).as_posix()]=dict(bytes=path.stat().st_size,sha256=digest)
    receipt=dict(status=actual['status'],worker_result=actual,files=inventory,
                 checkpoints=sorted(checkpoint_markers),gpu_worker_seconds=time.monotonic()-started)
    (operation/'remote-inventory.json').write_text(json.dumps(receipt,indent=2))
    volume.commit()
    return receipt


def validate_execution(request, worker):
    """Ràng buộc tài nguyên và workload trước bất kỳ upload/cấp GPU nào."""
    if request.get('status')!='USER_APPROVED' or not request.get('approval_reference'):
        raise PermissionError('Thiếu quyền thực thi lượt chạy')
    if worker['variant'] not in ('A2','A3') or worker['config']['batch_size']!=128:
        raise ValueError('A2/A3 batch128 đã chốt mới được dùng entry này')
    sys.path.insert(0,str(ROOT/'src'))
    from knowledge_tracing.akt.research_junyi_prepared import prepared_cache_options
    prepared_cache_options(worker,lambda value:value)
    if worker['validation_batch_size']!=128 or worker['config']['seed']!=42:
        raise ValueError('Batch validation/seed khác hợp đồng A0/A1')
    return validate_resource_budget(request, worker)


def validate_resource_budget(request, worker):
    """Dùng chung deadline, tài nguyên và cận chi phí cho selected/refit."""
    if request.get('status')!='USER_APPROVED' or not request.get('approval_reference'):
        raise PermissionError('Thiếu quyền thực thi lượt chạy')
    if worker['logical_run_id']!=worker['config']['run_id']:
        raise ValueError('Logical run khác config')
    for name in (request['execution_id'],worker['logical_run_id']):
        if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}',name) is None:
            raise ValueError('Run ID không hợp lệ')
    if request['gpu'] not in ('T4','L4','H100'):
        raise ValueError('GPU ngoài danh sách đã dự toán')
    if request['gpu']=='T4' and worker['profile']['max_vram_bytes']>12*1024**3:
        raise ValueError('Profile T4 cần trần VRAM phù hợp dung lượng thực')
    child=request['child_timeout_seconds']
    function=request['function_timeout_seconds']
    watchdog=request['watchdog_seconds']
    if (any(type(value) is not int for value in (child,function,watchdog))
            or not 30<=child<function<watchdog<=2100):
        raise ValueError('Thứ tự thời hạn child/function/watchdog không hợp lệ')
    gpu_rate={'T4':.000164,'L4':.000222,'H100':.001097}[request['gpu']]
    # Cận CPU/RAM 3x giá list để giữ cùng quy tắc bảo thủ của ledger hiện có.
    rate=gpu_rate+4*.00003942+12*.00000667
    upper=(watchdog+60)*rate
    if upper>request['reserved_usd_per_run']:
        raise PermissionError('Cap tiền thấp hơn cận thời gian/tài nguyên')
    if (worker['config']['max_wall_seconds']+120>child
            or worker['config']['max_seconds']>worker['config']['max_wall_seconds']):
        raise ValueError('Cần chừa thời gian runtime, handoff và checkpoint trong cap GPU')
    return dict(upper_usd=upper,rate_upper_usd_per_second=rate)


def run(snapshot, request, *, worker_entrypoint='run_junyi_gpu_stage.py', execution_validator=None):
    if worker_entrypoint not in ('run_junyi_gpu_stage.py', 'run_junyi_refit_gpu_stage.py'):
        raise ValueError('Numerical worker entrypoint ngoài allowlist')
    sys.path.insert(0,str(ROOT/'experiments/akt'))
    from junyi_staged_io import verify_project, collect_outputs, sha, write_new
    from modal_budget_guard import ModalRunDeadline, ModalAppBudgetGuard, PendingOwnedModalApp, stop_owned_app_cli
    from modal_junyi_main_selected import validate_project_budget
    from modal_graph_selected import read_billing
    import modal
    snapshot=Path(snapshot).resolve()
    if not snapshot.is_relative_to(ROOT/'artifacts/akt'):
        raise ValueError('Snapshot phải thuộc artifacts/akt')
    prepared=verify_project(snapshot)
    worker=json.loads((snapshot/'project/gpu-stage-request.json').read_text())
    validator = validate_execution if execution_validator is None else execution_validator
    resource=validator(request,worker)
    # CPU preparation validator tạo receipt riêng, source/request đều phải khớp.
    cpu=json.loads((snapshot/'CPU_CHECK.json').read_text())
    if (cpu['status']!='PASS_LOCAL_STAGE_INPUTS' or cpu['inputs_sha256']!=sha(snapshot/'INPUTS.json')
            or cpu['worker_request_sha256']!=sha(snapshot/'project/gpu-stage-request.json')):
        raise PermissionError('Thiếu nghiệm thu CPU trên snapshot chính xác')
    ledger_path=ROOT/'research_tracking/COMPUTE_BUDGET.json'
    ledger=json.loads(ledger_path.read_text())
    billing=asyncio.run(read_billing())
    admission=validate_project_budget(ledger,request,float(billing['billing']['metered_cost']))
    output=ROOT/'experiments/akt/results'/request['execution_id']
    output.mkdir(parents=True,exist_ok=False)
    write_new(output/'budget-admission.json',dict(project=admission,resource=resource,billing=billing))
    if request.get('resume_checkpoint') is not None:
        from junyi_staged_io import owned_input
        previous=json.loads(owned_input(ROOT,request['resume_inventory']).read_text())
        prefix='experiments/akt/results/'
        resume=request['resume_checkpoint']
        if not resume.startswith(prefix+worker['logical_run_id']+'/checkpoints/'):
            raise ValueError('Resume khác logical run')
        key='outputs/'+resume[len(prefix):]
        marker=key.rsplit('/',1)[0]+'/COMPLETE.json'
        if previous['files'][key]['sha256']!=request['resume_sha256'] or marker not in previous['files']:
            raise ValueError('Checkpoint chưa có bằng chứng tải/inventory COMPLETE')
    # Một allocation dành cho một tranche, giữ reservation kể cả upload lỗi.
    reservation_dir=ROOT/'artifacts/akt/modal/allocations'
    reservation_dir.mkdir(parents=True,exist_ok=True)
    allocation_key=hashlib.sha256(request['allocation_id'].encode()).hexdigest()
    write_new(reservation_dir/(allocation_key+'.json'),dict(execution_id=request['execution_id'],
        allocation_id=request['allocation_id'],reserved_usd=request['reserved_usd_per_run'],
        ledger_sha256=sha(ledger_path)))
    volume_name='kltn-staged-'+worker['logical_run_id']
    # Input upload/dựng image hoàn tất trước CPU preflight và function GPU.
    output_volume_name=volume_name+'-outputs'
    volume=modal.Volume.from_name(output_volume_name,create_if_missing=True,version=2)
    app=modal.App('kltn-akt-'+request['execution_id'])
    # Chỉ dọn hai mount đích trong layer image mới. Image gốc bất biến.
    image=modal.Image.from_id(request['image_id']).run_commands(
        'rm -rf /opt/kltn/artifacts /opt/kltn/experiments/akt/results',
        'mkdir -p /opt/kltn/artifacts /opt/kltn/experiments/akt/results')
    # Image được dựng trên CPU. Cache lớn trở thành file local của GPU container.
    image=image.add_local_dir(snapshot/'project','/opt/kltn',copy=True)
    image=image.add_local_file(snapshot/'INPUTS.json','/opt/kltn/staged-input-inventory.json',copy=True)
    directories={name.split('/')[0] for name in prepared['files'] if '/' in name}
    if '.venv' in directories or 'dataset' in directories:
        raise ValueError('Snapshot có vùng không được phép mount')
    # Một Volume output duy nhất, input đã ghim trong image.
    if (snapshot/'project/experiments/akt/results').exists():
        raise ValueError('Snapshot source không được chứa output cũ')
    mounts={}
    mounts['/opt/kltn/experiments/akt/results']=volume.with_mount_options(sub_path='/outputs')
    gpu_specification='H100!' if request['gpu']=='H100' else request['gpu']
    # Hai luồng Torch cần CPU được bảo đảm để tránh host bận làm GPU chờ.
    function=app.function(image=image,gpu=gpu_specification,cpu=(2,4),memory=(4096,12288),
        timeout=request['function_timeout_seconds'],startup_timeout=60,max_containers=1,retries=0,
        scaledown_window=2,volumes=mounts)(gpu_compute)
    cpu_check=app.function(image=image,cpu=2,memory=4096,timeout=180,
        startup_timeout=60,max_containers=1,retries=0,scaledown_window=2,volumes=mounts)(cpu_mount_preflight)
    execution=dict(execution_id=request['execution_id'],approval_reference=request['approval_reference'],
        gpu=request['gpu'],
        child_timeout_seconds=request['child_timeout_seconds'],
        worker_request_sha256=sha(snapshot/'project/gpu-stage-request.json'))
    if worker_entrypoint != 'run_junyi_gpu_stage.py':
        execution['worker_entrypoint'] = worker_entrypoint
    if request.get('resume_checkpoint') is not None:
        execution.update(resume_checkpoint=request['resume_checkpoint'],resume_sha256=request['resume_sha256'])
    deadline=ModalRunDeadline(request['watchdog_seconds'])
    reservation=json.loads((reservation_dir/(allocation_key+'.json')).read_text())
    if sha(ledger_path)!=reservation['ledger_sha256']:
        raise PermissionError('Ledger thay đổi sau reservation, cần kiểm lại trước cấp GPU')
    binding=PendingOwnedModalApp(request['execution_id'],app.name,lambda:app.app_id)
    try:
        with ModalAppBudgetGuard(binding,deadline,stop_app=stop_owned_app_cli,
                                 diagnostic_path=output/'app-budget-guard.json'):
            with modal.enable_output(),app.run(environment_name='main'):
                provider=cpu_check.spawn(request['execution_id']).get(timeout=min(240,deadline.remaining()))
                if provider.get('status')!='PASS_STAGED_PROVIDER_INPUTS':
                    raise ValueError('CPU provider chưa nghiệm thu input')
                write_new(output/'provider-cpu-preflight.json',provider)
                call=function.spawn(execution,output_volume_name)
                write_new(output/'dispatch.json',dict(app_id=app.app_id,call_id=call.object_id,
                    volume_name=output_volume_name,input_snapshot_sha256=sha(snapshot/'INPUTS.json')))
                receipt=call.get(timeout=deadline.remaining())
    except BaseException as error:
        write_new(output/'local-failure.json',dict(error_type=type(error).__name__,error=str(error)))
        guard_path=output/'app-budget-guard.json'
        stopped=guard_path.exists() and json.loads(guard_path.read_text()).get('stop_acknowledged') is True
        if stopped:
            try:
                raw=b''.join(volume.read_file('outputs/'+request['execution_id']+'-operation/checkpoint-index.json'))
                recovery=json.loads(raw)
                if recovery['files']:
                    collect_outputs(recovery,output/'recovery',volume.read_file,stop_acknowledged=True)
            except Exception as recovery_error:
                write_new(output/'recovery-failure.json',dict(error_type=type(recovery_error).__name__,error=str(recovery_error)))
        raise
    # Context guard chỉ trả về sau stop acknowledged. CPU download/zip bắt đầu ở đây.
    guard=json.loads((output/'app-budget-guard.json').read_text())
    previous_output=None
    if request.get('resume_inventory') is not None:
        previous_output=(ROOT/request['resume_inventory']).parent
    result=collect_outputs(receipt,output,volume.read_file,stop_acknowledged=guard['stop_acknowledged'],
                           reuse_from=previous_output)
    result['worker_status']=receipt['status']
    write_new(output/'stage-result.json',result)
    if receipt['status']=='FAILED':
        raise RuntimeError('GPU worker lỗi; artifact đã tải/kiểm local, xem stage-result.json')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run:
        print(json.dumps(dict(status='NO_CLOUD_ACTION',snapshot=str(args.snapshot))))
        return
    temp=ROOT/'artifacts/akt/runtime/modal-client-temp'
    temp.mkdir(parents=True,exist_ok=True)
    for key in ('TEMP','TMP','TMPDIR'):
        os.environ[key]=str(temp)
    import tempfile
    tempfile.tempdir=str(temp)
    os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE']='kltn'
    print(json.dumps(run(args.snapshot,json.loads(args.request.read_text())),ensure_ascii=False))


if __name__=='__main__':
    main()
