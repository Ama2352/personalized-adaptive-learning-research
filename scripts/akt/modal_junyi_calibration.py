"""Các function calibration CPU/GPU độc lập, chỉ root controller gọi sau duyệt.

Chạy file trực tiếp chỉ kiểm request local. Không tự provisioning hoặc upload.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2] if os.name == 'nt' else Path('/opt/kltn')
IMAGE_ID = 'im-FLsPV1Te1DGul7RBdUy5HH'
VOLUME_NAME = 'kltn-junyi-calibration-artifacts-v1'
SECRET_NAME = 'kltn-drive-artifacts-sang2005-20261117'
SOURCE_COMMIT = '01b7e8d7d7c862cabc9467108e3e7f2555653a88'
WORKER_SCRIPTS = ('calibration_cloud_worker.py', 'prepare_junyi_calibration_caches.py',
                  'run_junyi_refit.py', 'drive_artifact_sink.py', 'drive_resumable_upload.py')


def put_request_atomic(request, relative_path, root):
    """Ghi JSON request nhỏ bất biến, retry cùng nội dung trả cùng pin."""
    from pathlib import PurePosixPath
    from calibration_cloud_worker import validate_request, sha
    from knowledge_tracing.akt.filesystem import publish_new_file
    validate_request(request, 'gpu')
    if type(relative_path) is not str or '\\' in relative_path or ':' in relative_path:
        raise ValueError('POSIX request relative path required')
    relative = PurePosixPath(relative_path)
    if (relative.is_absolute() or '..' in relative.parts or len(relative.parts) < 2
            or relative.parts[0] != 'requests' or relative.suffix != '.json'):
        raise ValueError('request must stay under requests/ with JSON suffix')
    encoded = (json.dumps(request, sort_keys=True, allow_nan=False)+'\n').encode()
    if len(encoded) > 2*1024**2:
        raise ValueError('request exceeds 2MiB metadata cap')
    root = Path(root).resolve(strict=True)
    path = root.joinpath(*relative.parts)
    if path.resolve() != path:
        raise ValueError('physical request path required')
    for component in (path, *path.parents):
        if component == root:
            break
        if component.is_symlink() or getattr(component, 'is_junction', lambda: False)():
            raise ValueError('request aliases rejected')
    if path.exists():
        if path.stat().st_size != len(encoded) or path.read_bytes() != encoded:
            raise FileExistsError('immutable request already has different content')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.partial')
        with temporary.open('xb') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        publish_new_file(temporary, path)
    return dict(path=str(path), sha256=sha(path), bytes=len(encoded))


def validate_authorization(authorization, request_entry, stage):
    keys = {'workspace', 'stage', 'allocation_id', 'reserved_usd', 'request_sha256'}
    if (not isinstance(authorization, dict) or set(authorization) != keys
            or authorization['workspace'] != 'honguyenminhsang2016'
            or authorization['stage'] != stage
            or authorization['request_sha256'] != request_entry['sha256']
            or type(authorization['allocation_id']) is not str
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,47}', authorization['allocation_id'])
            or type(authorization['reserved_usd']) not in (int, float)
            or not 0 < authorization['reserved_usd'] <= .75):
        raise PermissionError('externally admitted per-stage budget allocation required')


def request_pin(entry):
    """Producer put_request trả bytes; consumer pinned vẫn giữ schema hai key."""
    if (type(entry) is not dict or set(entry) not in ({'path', 'sha256'}, {'path', 'sha256', 'bytes'})
            or type(entry['path']) is not str or type(entry['sha256']) is not str
            or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])
            or ('bytes' in entry and (type(entry['bytes']) is not int or not 0 < entry['bytes'] <= 2*1024**2))):
        raise ValueError('known request producer entry required')
    return dict(path=entry['path'], sha256=entry['sha256'])


def operation_tranche(variant, stage, attempt_id):
    if (variant not in ('A0', 'A1', 'A2', 'A3') or stage not in ('cpu-cache', 'gpu', 'cpu-join')
            or type(attempt_id) is not str
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,47}', attempt_id)):
        raise ValueError('bounded stage attempt required')
    return variant.lower()+'-'+stage+'-operation-'+attempt_id


def run_gpu_monitored(command, log, telemetry, *, timeout, environment,
                      popen=None, query=None, clock=None, sleep=None):
    """Một child GPU, đo NVML qua nvidia-smi mỗi giây và luôn thu hồi child."""
    popen, query = popen or subprocess.Popen, query or subprocess.run
    clock, sleep = clock or time.monotonic, sleep or time.sleep
    started = clock()
    process = None
    try:
        process = popen(command, stdout=log, stderr=subprocess.STDOUT, cwd='/opt/kltn',
                        env=environment, start_new_session=True)
        while process.poll() is None:
            if clock()-started > timeout:
                raise TimeoutError('GPU worker exceeded bounded runtime')
            sampled = query(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total',
                             '--format=csv,noheader,nounits'], capture_output=True, text=True,
                            check=True, timeout=5)
            rows = list(csv.reader(sampled.stdout.strip().splitlines()))
            if len(rows) != 1 or len(rows[0]) != 3:
                raise ValueError('single-GPU utilization sample required')
            utilization, used, total = (float(value.strip()) for value in rows[0])
            if (not all(math.isfinite(value) for value in (utilization, used, total))
                    or not 0 <= utilization <= 100 or not 0 <= used <= total or total <= 0):
                raise ValueError('invalid GPU utilization sample')
            telemetry.write(json.dumps(dict(seconds=clock()-started, gpu_utilization=utilization,
                vram_used_mib=used, vram_total_mib=total))+'\n')
            telemetry.flush()
            sleep(1)
        returncode = process.wait(timeout=5)
        if returncode != 0:
            raise subprocess.CalledProcessError(returncode, command)
    finally:
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def publish_operation_metadata(root, run_id, operation_names, *, publish, volume_commit):
    """CPU finalizer chỉ đọc allowlist metadata của các operation đã đóng."""
    from calibration_cloud_worker import sha
    if (type(run_id) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,70}', run_id)
            or type(operation_names) is not list or not 1 <= len(operation_names) <= 16
            or len(operation_names) != len(set(operation_names))):
        raise ValueError('bounded metadata finalization request required')
    root = Path(root).resolve(strict=True)
    allowed = ('config.json', 'worker.log', 'result.json', 'COMPLETE.json', 'FAILED.json', 'gpu-utilization.jsonl')
    results = []
    for name in operation_names:
        if (type(name) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,94}', name)
                or '-operation' not in name):
            raise ValueError('explicit operation tranche required')
        source = root/run_id/name/'payloads'
        if source.resolve(strict=True) != source:
            raise ValueError('physical metadata source required')
        for component in (source, *source.parents):
            if component == root:
                break
            if component.is_symlink() or getattr(component, 'is_junction', lambda: False)():
                raise ValueError('metadata aliases rejected')
        if not ((source/'COMPLETE.json').is_file() or (source/'FAILED.json').is_file()):
            raise ValueError('running operation cannot be finalized')
        files, empty, missing, inventory = [], [], [], {}
        for filename in allowed:
            path = source/filename
            if not path.exists():
                missing.append(filename)
            elif not path.is_file() or path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                raise ValueError('regular metadata file required')
            elif path.stat().st_size == 0:
                empty.append(filename)
            else:
                files.append(filename)
                inventory[filename] = dict(bytes=path.stat().st_size, sha256=sha(path))
        if 'config.json' not in files:
            raise ValueError('nonempty operation config required for audit')
        publication = dict(kind='CALIBRATION_OPERATION_METADATA_V1', operation=name, files=inventory,
                           empty_files=empty, missing_files=missing)
        digest = hashlib.sha256(json.dumps(publication, sort_keys=True).encode()).hexdigest()
        tranche = name[:70]+'-meta-'+digest[:16]
        destination = root/run_id/tranche/'payloads'
        if destination.resolve() != destination:
            raise ValueError('physical metadata snapshot required')
        destination.mkdir(parents=True, exist_ok=True)
        for filename in files:
            target = destination/filename
            if target.exists():
                if target.is_symlink() or sha(target) != inventory[filename]['sha256']:
                    raise ValueError('metadata snapshot content changed')
            else:
                shutil.copyfile(source/filename, target)
            if sha(source/filename) != inventory[filename]['sha256'] or sha(target) != inventory[filename]['sha256']:
                raise ValueError('operation metadata changed while copying')
        manifest = destination/'PUBLICATION.json'
        if manifest.exists() and json.loads(manifest.read_text()) != publication:
            raise ValueError('metadata snapshot publication changed')
        if not manifest.exists():
            with manifest.open('x', encoding='utf-8') as stream:
                json.dump(publication, stream, sort_keys=True, allow_nan=False)
        files.append('PUBLICATION.json')
        volume_commit()
        results.append(publish(destination, dict(run_id=run_id, tranche_id=tranche, files=files,
            max_total_bytes=sum((destination/filename).stat().st_size for filename in files))))
    return dict(status='OPERATION_METADATA_PUBLISHED', publications=results)


def _run(stage, request_entry, worker_sha256, authorization, *, gpu_result_entry=None):
    """Worker con giữ log/receipt trên Volume; không tải binary về PC."""
    request_entry = request_pin(request_entry)
    validate_authorization(authorization, request_entry, stage)
    from calibration_cloud_worker import pinned, validate_request, sha
    root = Path('/artifacts').resolve(strict=True)
    request_path = pinned(request_entry, root)
    request = json.loads(request_path.read_text())
    validate_request(request, stage)
    if request['max_cost_usd'] > authorization['reserved_usd']:
        raise PermissionError('request exceeds external budget allocation')
    worker = Path('/opt/kltn/scripts/akt/calibration_cloud_worker.py')
    if sha(worker) != worker_sha256:
        raise ValueError('image worker source pin mismatch')
    attempt_id = authorization['allocation_id']
    operation = root/request['run_id']/operation_tranche(request['variant'], stage, attempt_id)/'payloads'
    operation.mkdir(parents=True, exist_ok=False)
    (operation/'config.json').write_text(json.dumps(dict(request=request, authorization=authorization,
        worker_sha256=worker_sha256, stage=stage), sort_keys=True), encoding='utf-8')
    result = operation/'result.json'
    command = ['/opt/kltn/.venv/bin/python', '-B', str(worker), '--stage', stage,
        '--request', str(request_path), '--request-sha256', request_entry['sha256'], '--result', str(result),
        '--attempt-id', attempt_id]
    if gpu_result_entry is not None:
        command.extend(('--gpu-result', json.dumps(gpu_result_entry)))
    started = time.monotonic()
    import modal
    volume = modal.Volume.from_name(VOLUME_NAME, environment_name='main')
    try:
        with (operation/'worker.log').open('xb') as log:
            environment = dict(os.environ, PYTHONPATH='/opt/kltn/src', PYTHONDONTWRITEBYTECODE='1')
            if stage == 'gpu':
                with (operation/'gpu-utilization.jsonl').open('x', encoding='utf-8') as telemetry:
                    run_gpu_monitored(command, log, telemetry, timeout=270, environment=environment)
            else:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True,
                    cwd='/opt/kltn', timeout=3420, env=environment)
        if not result.is_file():
            raise RuntimeError('worker exited without durable result')
        value = json.loads(result.read_text())
        (operation/'COMPLETE.json').write_text(json.dumps(dict(status='STAGE_COMPLETE',
            stage=stage, worker_seconds=time.monotonic()-started, result_sha256=sha(result))), encoding='utf-8')
        volume.commit()
        if stage == 'cpu-join':
            import drive_artifact_sink as sink
            sink.CLOUD_ROOT = root
            def publish(source, publication):
                return sink.publish_from_environment(source_root=source, **publication,
                    volume_commit=volume.commit, chunk_bytes=32*1024**2, retries=2)
            publish_operation_metadata(root, request['run_id'], [operation.parent.name],
                publish=publish, volume_commit=volume.commit)
        return dict(status='STAGE_COMMITTED', result_path=str(result), result_sha256=sha(result),
                    result=value, operation_tranche=operation.parent.name, worker_seconds=time.monotonic()-started)
    except BaseException as error:
        (operation/'FAILED.json').write_text(json.dumps(dict(stage=stage, error_type=type(error).__name__,
            worker_seconds=time.monotonic()-started)), encoding='utf-8')
        volume.commit()
        raise


def create_app():
    """Định nghĩa resource, không tự gọi remote function hoặc tạo Volume."""
    if os.name == 'nt':
        os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal2016.toml')
        os.environ['MODAL_PROFILE'] = 'kltn2016'
    import warnings
    warnings.filterwarnings('ignore', message=r'Your Modal token .*')
    import modal
    volume = modal.Volume.from_name(VOLUME_NAME, environment_name='main')
    image = modal.Image.from_id(IMAGE_ID).apt_install('git').run_commands(
        # Layer mới của image, không thao tác dữ liệu máy local hoặc Volume.
        'rm -rf /opt/kltn/src /opt/kltn/artifacts /opt/kltn/experiments/akt/results',
        'mkdir -p /opt/kltn/artifacts/akt/dependencies /opt/kltn/experiments/akt/results',
        'git init /opt/kltn/artifacts/akt/dependencies/upstream',
        'git -C /opt/kltn/artifacts/akt/dependencies/upstream remote add origin https://github.com/arghosh/AKT.git',
        'git -C /opt/kltn/artifacts/akt/dependencies/upstream fetch --depth=1 origin '+SOURCE_COMMIT,
        'git -C /opt/kltn/artifacts/akt/dependencies/upstream checkout --detach FETCH_HEAD',
        '/opt/kltn/.venv/bin/python -m ensurepip --upgrade',
        '/opt/kltn/.venv/bin/python -m pip install modal==1.6.3 requests==2.34.2 google-auth==2.62.1')
    image = image.env({'PYTHONPATH': '/opt/kltn/src:/opt/kltn/scripts/akt:/opt/kltn/.venv/lib/python3.13/site-packages'})
    image = image.add_local_dir(str(ROOT/'src'), '/opt/kltn/src', copy=True,
                                ignore=['**/__pycache__/**', '**/*.pyc'])
    for name in ('21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md', '26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md'):
        image = image.add_local_file(str(ROOT/'docs/thesis_recovery'/name), '/opt/kltn/docs/thesis_recovery/'+name, copy=True)
    for name in (*WORKER_SCRIPTS, 'modal_junyi_calibration.py'):
        image = image.add_local_file(str(ROOT/'scripts/akt'/name), '/opt/kltn/scripts/akt/'+name, copy=True)
    app = modal.App('kltn-junyi-calibration-staged')
    common = dict(image=image, volumes={'/artifacts': volume}, max_containers=1,
        scaledown_window=2, retries=0, single_use_containers=True, startup_timeout=180, serialized=True,
        routing_region='ap-south')

    @app.function(**common, cpu=1, memory=4096, timeout=120)
    def preflight():
        import json
        import subprocess
        from knowledge_tracing.akt.research_junyi_cached_numeric import CachedNumericBudget
        import drive_artifact_sink
        import google.auth
        if 'torch' in sys.modules:
            raise ValueError('parent dependency preflight must not import Torch')
        source = ('import sys,json; sys.path.insert(0,"/opt/kltn/src"); '
            'sys.path.insert(0,"/opt/kltn/scripts/akt"); '
            'from calibration_cloud_worker import runtime_preflight; '
            'print(json.dumps(runtime_preflight("/opt/kltn"),sort_keys=True))')
        checked = subprocess.run(['/opt/kltn/.venv/bin/python', '-B', '-c', source],
            capture_output=True, text=True, check=True, timeout=90,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        result = json.loads(checked.stdout)
        result['parent_imports'] = dict(cached_numeric_budget=CachedNumericBudget.__name__,
            drive_sink=str(drive_artifact_sink.__file__), google_auth=str(google.auth.__file__), torch_loaded=False)
        return result

    @app.function(**common, cpu=1, memory=1024, timeout=120)
    def put_request(request_dict, relative_path):
        sys.path.insert(0, '/opt/kltn/scripts/akt')
        import modal_junyi_calibration as controller
        volume.reload()
        result = controller.put_request_atomic(request_dict, relative_path, Path('/artifacts').resolve(strict=True))
        volume.commit()
        return result

    @app.function(**common, cpu=1, memory=1024, timeout=900,
        secrets=[modal.Secret.from_name(SECRET_NAME, environment_name='main', required_keys=['KLTN_DRIVE_OAUTH_JSON'])])
    def publish_metadata(run_id, operation_names):
        sys.path.insert(0, '/opt/kltn/scripts/akt')
        import modal_junyi_calibration as controller
        import drive_artifact_sink as sink
        volume.reload()
        root = Path('/artifacts').resolve(strict=True)
        sink.CLOUD_ROOT = root
        def publish(source, publication):
            return sink.publish_from_environment(source_root=source, **publication,
                volume_commit=volume.commit, chunk_bytes=32*1024**2, retries=2)
        return controller.publish_operation_metadata(root, run_id, operation_names,
            publish=publish, volume_commit=volume.commit)

    @app.function(**common, cpu=1, memory=16384, timeout=3600)
    def prepare(request_entry, worker_sha256, authorization):
        sys.path.insert(0, '/opt/kltn/scripts/akt')
        import modal_junyi_calibration as controller
        volume.reload()
        return controller._run('cpu-cache', request_entry, worker_sha256, authorization)

    @app.function(**common, gpu='H100!', cpu=2, memory=8192, timeout=300)
    def predict(request_entry, worker_sha256, authorization):
        sys.path.insert(0, '/opt/kltn/scripts/akt')
        import modal_junyi_calibration as controller
        volume.reload()
        return controller._run('gpu', request_entry, worker_sha256, authorization)

    @app.function(**common, cpu=1, memory=16384, timeout=3600,
        secrets=[modal.Secret.from_name(SECRET_NAME, environment_name='main', required_keys=['KLTN_DRIVE_OAUTH_JSON'])])
    def join_fit(request_entry, worker_sha256, authorization, gpu_result_entry):
        sys.path.insert(0, '/opt/kltn/scripts/akt')
        import modal_junyi_calibration as controller
        volume.reload()
        return controller._run('cpu-join', request_entry, worker_sha256, authorization, gpu_result_entry=gpu_result_entry)

    return app, dict(preflight=preflight, put_request=put_request, publish_metadata=publish_metadata,
                    prepare=prepare, predict=predict, join_fit=join_fit)


def main():
    parser = argparse.ArgumentParser(description='Kiểm request local, không gọi Modal')
    parser.add_argument('--request', required=True)
    parser.add_argument('--stage', required=True, choices=('cpu-cache', 'gpu', 'cpu-join'))
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT/'scripts/akt'))
    from calibration_cloud_worker import validate_request
    request = validate_request(json.loads(Path(args.request).read_text(encoding='utf-8')), args.stage)
    print(json.dumps(dict(status='LOCAL_REQUEST_SCHEMA_VALID', stage=args.stage,
                         mode=request['mode'], cloud_started=False)))


if __name__ == '__main__':
    main()
