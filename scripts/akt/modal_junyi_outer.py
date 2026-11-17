"""Factory H100-onlyouter. Root cấp image/Volume đã stage và allocation riêng.

Import hoặc chạy file này không cấp container. Không có CPUcloudfunction,
OAuthsecret, transferdata hoặc tự retry. Numeric/logs giữVolume đểCPUlocal
streamDrive sau khi GPU đã trả.
"""
import json
import os
from pathlib import Path
import sys

IMAGE_ID = 'im-FLsPV1Te1DGul7RBdUy5HH'
SOURCE_IDENTITY = '7c72414eedf9507d514430aed4734f0a192ab14914a4984b17fdfcbfebd39123'


def create_outer_gpu_app(image, volume):
    """Dùng image đã đóngSOURCE7c, không dựng/launchimage hoặc upload tại đây."""
    import modal
    app = modal.App('kltn-junyi-outer-h100')
    @app.function(image=image,volumes={'/artifacts':volume},gpu='H100!',cpu=2,memory=8192,
        timeout=300,max_containers=1,scaledown_window=2,retries=0,single_use_containers=True,
        startup_timeout=180,serialized=True,routing_region='ap-south')
    def predict(request_entry, worker_sha256, authorization, attempt_id):
        sys.path.insert(0,'/opt/kltn/scripts/akt')
        from calibration_cloud_worker import pinned, sha
        from modal_junyi_calibration import validate_authorization, request_pin, run_gpu_monitored
        from outer_gpu_worker import validate_outer_request
        validate_authorization(authorization,request_entry,'gpu')
        if type(attempt_id) is not str or not attempt_id.isalnum() or len(attempt_id)>32:
            raise ValueError('Explicit bounded alphanumeric attempt required')
        volume.reload()
        root = Path('/artifacts').resolve(strict=True)
        entry = request_pin(request_entry)
        request_path = pinned(entry,root)
        request = json.loads(request_path.read_text())
        validate_outer_request(request)
        if request['max_cost_usd'] > authorization['reserved_usd']:
            raise PermissionError('Request exceeds externally reserved allocation')
        worker = Path('/opt/kltn/scripts/akt/outer_gpu_worker.py')
        if sha(worker) != worker_sha256:
            raise ValueError('GPUworker source pin mismatch')
        operation = root/request['run_id']/(request['variant'].lower()+'-outer-operation-'+attempt_id)
        if operation.resolve()!=operation:
            raise ValueError('Physical new operation path required')
        operation.mkdir(parents=True,exist_ok=False)
        result_path = operation/'result.json'
        config = dict(request_pin=entry,worker_sha256=worker_sha256,authorization=authorization,
            device='H100',function_timeout_seconds=300,child_timeout_seconds=270)
        with (operation/'config.json').open('x',encoding='utf-8') as stream:
            json.dump(config,stream,sort_keys=True)
        environment = dict(os.environ)
        environment.update(PYTHONPATH='/opt/kltn/src:/opt/kltn/scripts/akt',
            OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        command = ['/opt/kltn/.venv/bin/python','-B',str(worker),'--request',str(request_path),
            '--request-sha256',entry['sha256'],'--result',str(result_path)]
        try:
            with (operation/'worker.log').open('x') as log, (operation/'gpu-utilization.jsonl').open('x') as telemetry:
                run_gpu_monitored(command,log,telemetry,timeout=270,environment=environment)
            result = json.loads(result_path.read_text())
            if result['status'] != 'OUTER_NUMERIC_COMMITTED_RELEASE_H100':
                raise ValueError('GPU result is not numerically complete/committed')
            with (operation/'COMPLETE.json').open('x') as stream:
                json.dump(dict(status='OUTER_GPU_OPERATION_COMPLETE',result_sha256=sha(result_path)),stream)
            return dict(status='OUTER_GPU_OPERATION_COMPLETE',result=result,
                result_path=str(result_path),result_sha256=sha(result_path),operation_path=str(operation))
        except BaseException as error:
            with (operation/'FAILED.json').open('x') as stream:
                json.dump(dict(status='OUTER_GPU_STOPPED_NO_RETRY',error_type=type(error).__name__),stream)
            raise
        finally:
            volume.commit()
    return app,predict
