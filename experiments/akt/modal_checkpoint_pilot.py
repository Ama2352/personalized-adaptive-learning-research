"""Pilot Modal đã được user duyệt tối đa 0,50 USD free credits, một GPU T4/L4/A10, tối đa 600 giây mỗi lượt."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import runpy
import zipfile

ROOT = Path(__file__).resolve().parent.parent.parent
REMOTE = '/opt/kltn'
RUN_ID = 'modal-checkpoint-pilot-20261111-01'
INPUTS = ROOT/'artifacts/akt/modal'/RUN_ID
NATIVE = ROOT/'experiments/akt/results'/RUN_ID
VOLUME_NAME = 'kltn-akt-checkpoint-pilot-20261111-01'
GPU = 'T4'
WAIT_SECONDS = 600
LOCK = ROOT/'artifacts/akt/colab/gpu08-linux-20261108-01/received/resolution-attempt01/candidate-linux-cuda.lock.txt'
LOCK_SHA = '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
EXPECTED = 'CUDA_CHECKPOINT_FRESH_PROCESS_RESTORE_VERIFIED'


def sha_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare():
    assert sha_file(LOCK) == LOCK_SHA
    contents, transforms = runpy.run_path(str(ROOT/'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
    source_hashes = {name:hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    parent = ROOT/'research_tracking/runs/akt-t4-checkpoint-recovery-20261110-01'
    for source, target in [('checkpoint_worker.py', 't4_checkpoint_worker.py'),
            ('checkpoint_controller.py', 't4_checkpoint_controller.py')]:
        code = (parent/source).read_text().replace('/content/kltn-current-t4-20261110-01', REMOTE)
        code = code.replace("ROOT/'experiments/akt/results/current-t4-four-variant-smoke-20261110-01/result.json'",
            "ROOT/'artifacts/akt/runtime/accepted-colab-smoke.json'")
        code = code.replace("assert torch.cuda.get_device_name(0) == 'Tesla T4'",
            "assert any(g in torch.cuda.get_device_name(0) for g in os.environ['EXPECTED_PILOT_GPU'].split(','))")
        code = code.replace('isolated-install02/result.json', 'modal-runtime.json')
        code = code.replace("assert installed['status'] == 'ISOLATED_ENV_READY_GPU_UNTESTED'",
            "assert installed['runtime_schema_version'] == 2 and installed['device'] == 'cuda' and installed['cuda_available'] is True")
        code = code.replace('modal_spend_usd=0', 'modal_spend_usd=None')
        code = code.replace("run_id='t4-checkpoint-'+args.variant.lower()+'-'+args.phase, output_dir=OUT",
            'run_id=BASE.name, output_dir=BASE')
        code = code.replace("device='cuda', max_steps=4,", "device='cuda', max_steps=4, max_rss_bytes=6*1024**3,")
        code = code.replace('max_rss_bytes=2*1024**3,', 'max_rss_bytes=6*1024**3,')
        if source == 'checkpoint_controller.py':
            code = code.replace("            assert entry['returncode'] == 0, entry", """            durable_phase = Path(os.environ['PILOT_DURABLE_ROOT'])/variant/phase
            durable_phase.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(BASE/variant/phase, durable_phase)
            copied = {}
            for native_file in sorted((BASE/variant/phase).rglob('*')):
                if native_file.is_file():
                    relative = native_file.relative_to(BASE/variant/phase)
                    with native_file.open('rb') as stream:
                        native_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
                    with (durable_phase/relative).open('rb') as stream:
                        assert hashlib.file_digest(stream, 'sha256').hexdigest() == native_sha
                    copied[relative.as_posix()] = native_sha
            (durable_phase/'TRANSFER_SHA256.json').write_text(json.dumps(copied, indent=2)+'\\n')
            subprocess.run(['sync', '/durable'], timeout=20, check=True)
            assert entry['returncode'] == 0, entry""")
        contents['artifacts/akt/runtime/'+target] = code.encode()
    accepted = ROOT/'research_tracking/runs/akt-colab-t4-current-20261110-01/remote/smoke-result.json'
    contents['artifacts/akt/runtime/accepted-colab-smoke.json'] = accepted.read_bytes()
    manifest = dict(schema_version=1, run_id=RUN_ID, source_files=source_hashes,
        files={name:hashlib.sha256(data).hexdigest() for name, data in contents.items()},
        notebook_copy_transforms=transforms, lock_sha256=LOCK_SHA,
        authorization='User approved first pilot up to USD0.50 free credits, one T4 at most ten minutes')
    INPUTS.mkdir(parents=True, exist_ok=True)
    archive = INPUTS/'source.zip'
    if archive.exists():
        with zipfile.ZipFile(archive) as saved:
            assert json.loads(saved.read('MANIFEST.json')) == manifest, 'existing input changed'
    else:
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as saved:
            for name, data in contents.items():
                saved.writestr(name, data)
            saved.writestr('MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
    plan = dict(run_id=RUN_ID, gpu=['L4', 'T4', 'A10'] if GPU == 'auto' else GPU, max_containers=1, retries=0,
        timeout_seconds=420, startup_timeout_seconds=120, max_gpu_startup_and_run_seconds=600,
        client_wait_seconds=WAIT_SECONDS,
        cpu_request=0.25, cpu_limit=2,
        memory_request_mib=4096, memory_limit_mib=8192, pilot_budget_usd=0.50,
        worker_max_rss_bytes=6*1024**3,
        volume_version=2, native_checkpoint_filesystem='container-local',
        durable_checkpoint_boundary='after each fresh-process phase, SHA256 plus sync',
        max_optimizer_updates=16, max_synthetic_targets=384, main_training=False,
        source_zip_sha256=sha_file(archive), source_files=len(source_hashes), lock_sha256=LOCK_SHA,
        volume_name=VOLUME_NAME, image_build_dependency_timeout_seconds=480)
    (INPUTS/'plan.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    return archive, plan


def remote_pilot(expected_zip_sha, run_id, expected_gpu, volume_name):
    import modal
    volume = modal.Volume.from_name(volume_name)
    import subprocess
    import time
    import traceback
    remote = Path('/opt/kltn')
    results = remote/'experiments/akt/results'
    results.mkdir(parents=True, exist_ok=True)
    out = results/run_id
    out.mkdir(exist_ok=False)
    durable = Path('/durable')/run_id
    durable.mkdir(exist_ok=False)
    print(json.dumps(dict(event='pilot_started', run_id=run_id)), flush=True)
    began = time.monotonic()
    summary = dict(status='FAILED', run_id=run_id, gpu_requested=expected_gpu,
        main_training=False, source_zip_sha256=expected_zip_sha)
    try:
        assert sha_file(Path('/opt/kltn-input.zip')) == expected_zip_sha
        with zipfile.ZipFile('/opt/kltn-input.zip') as source:
            pins = json.loads(source.read('MANIFEST.json'))
            assert source.testzip() is None
            assert len(source.namelist()) == len(set(source.namelist())) == len(pins['files'])+1
            for name, expected_sha in pins['files'].items():
                path = PurePosixPath(name)
                assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
                assert hashlib.sha256(source.read(name)).hexdigest() == expected_sha
            source.extractall(remote)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', EXPECTED_PILOT_GPU=expected_gpu,
                   PILOT_DURABLE_ROOT=str(durable/'phase-checkpoints'))
        runtime_command = [str(remote/'.venv/bin/python'), '-I', '-B',
            str(remote/'scripts/akt/check_runtime.py'), '--upstream',
            str(remote/'artifacts/akt/dependencies/upstream'), '--device', 'cuda',
            '--lock-file', '/opt/locked-cu126.txt', '--output',
            str(remote/'artifacts/akt/runtime/modal-runtime.json')]
        with (out/'runtime.log').open('xb') as log:
            subprocess.run(runtime_command, cwd=remote, env=env, stdout=log,
                stderr=subprocess.STDOUT, timeout=40, check=True)
        runtime = json.loads((remote/'artifacts/akt/runtime/modal-runtime.json').read_text())
        assert runtime['lock_sha256'] == pins['lock_sha256']
        (out/'runtime.json').write_text(json.dumps(runtime, indent=2)+'\n')
        command = [str(remote/'.venv/bin/python'), '-I', '-B',
            str(remote/'artifacts/akt/runtime/t4_checkpoint_controller.py')]
        with (out/'controller.log').open('xb') as log:
            process = subprocess.run(command, cwd=remote, env=env, stdout=log,
                stderr=subprocess.STDOUT, timeout=390)
        summary['controller_returncode'] = process.returncode
        actual = json.loads((results/'t4-checkpoint-recovery-20261110-01/result.json').read_text())
        summary.update(controller_result=actual, status=actual['status'])
    except BaseException as error:
        summary.update(error_type=type(error).__name__, error=str(error))
        (out/'failure.log').write_text(traceback.format_exc())
    finally:
        summary['elapsed_seconds'] = time.monotonic()-began
        (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        files = list(out.glob('*.json'))+list(out.glob('*.log'))
        checkpoint_root = results/'t4-checkpoint-recovery-20261110-01'
        if checkpoint_root.exists():
            files += [path for path in checkpoint_root.rglob('*') if path.is_file()]
        inventory = {path.relative_to(results).as_posix(): dict(
            sha256=sha_file(path), bytes=path.stat().st_size) for path in files}
        with zipfile.ZipFile(out/'artifacts.zip', 'x', compression=zipfile.ZIP_DEFLATED) as saved:
            for path in files:
                saved.write(path, path.relative_to(results).as_posix())
            saved.writestr('SHA256.json', json.dumps(inventory, indent=2)+'\n')
        summary.update(archive_sha256=sha_file(out/'artifacts.zip'),
            archive_bytes=(out/'artifacts.zip').stat().st_size)
        (out/'receipt.json').write_text(json.dumps(summary, indent=2)+'\n')
        import shutil
        shutil.copyfile(out/'artifacts.zip', durable/'artifacts.zip')
        assert sha_file(durable/'artifacts.zip') == summary['archive_sha256']
        shutil.copyfile(out/'receipt.json', durable/'receipt.json')
        volume.commit()
    return summary


def execute(archive, plan, *, define_only=False):
    for name in ('MODAL_TOKEN_ID', 'MODAL_TOKEN_SECRET'):
        os.environ.pop(name, None)
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal.toml')
    os.environ['MODAL_PROFILE'] = 'kltn'
    import modal
    from modal.client import _Client
    from modal_proto import api_pb2
    import asyncio

    async def check_workspace():
        client = await _Client.from_env()
        try:
            info = await asyncio.wait_for(client._stub.TokenInfoGet(api_pb2.TokenInfoGetRequest()), 15)
            assert info.workspace_name == 'honguyenminhsang2005'
        finally:
            await client._close()
    asyncio.run(check_workspace())
    assert not (NATIVE/'receipt.json').exists(), 'pilot already downloaded, inspect existing output'
    volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True, version=2)
    image = (modal.Image.debian_slim(python_version='3.13').apt_install('git')
        .add_local_file(LOCK, '/opt/locked-cu126.txt', copy=True)
        .run_commands('python -m venv --without-pip /opt/kltn/.venv',
            'timeout 480 python -m pip --python /opt/kltn/.venv/bin/python install '
            '--require-hashes --no-deps --only-binary=:all: --no-cache-dir --retries 0 '
            '--timeout 20 -r /opt/locked-cu126.txt',
            'mkdir -p /opt/kltn/artifacts/akt/dependencies && '
            'timeout 90 git clone --no-checkout https://github.com/arghosh/AKT.git '
            '/opt/kltn/artifacts/akt/dependencies/upstream && '
            'git -C /opt/kltn/artifacts/akt/dependencies/upstream checkout --detach '
            '01b7e8d7d7c862cabc9467108e3e7f2555653a88')
        .add_local_file(archive, '/opt/kltn-input.zip', copy=True))
    app = modal.App('kltn-akt-'+RUN_ID)

    pilot = app.function(image=image, gpu=plan['gpu'], cpu=(0.25, 2), memory=(4096, 8192),
        timeout=420, startup_timeout=120, retries=0, max_containers=1,
        volumes={'/durable': volume})(remote_pilot)

    if define_only:
        print('LOCAL_MODAL_DEFINITION_VERIFIED; no remote App run', flush=True)
        return
    NATIVE.mkdir(parents=True, exist_ok=True)
    with modal.enable_output():
        with app.run(environment_name='main'):
            call = pilot.spawn(plan['source_zip_sha256'], RUN_ID, 'L4,A10,T4' if GPU == 'auto' else GPU, VOLUME_NAME)
            (NATIVE/'dispatch.json').write_text(json.dumps(dict(
                call_id=call.object_id, client_wait_seconds=plan['client_wait_seconds']))+'\n')
            receipt = call.get(timeout=plan['client_wait_seconds'])
            (NATIVE/'remote-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
            partial = NATIVE/'artifacts.zip.partial'
            with partial.open('xb') as output:
                for block in volume.read_file(RUN_ID+'/artifacts.zip'):
                    output.write(block)
            assert partial.stat().st_size == receipt['archive_bytes']
            assert sha_file(partial) == receipt['archive_sha256']
            target = NATIVE/'artifacts.zip'
            assert not target.exists()
            partial.rename(target)
            with zipfile.ZipFile(target) as saved:
                assert saved.testzip() is None
                inventory = json.loads(saved.read('SHA256.json'))
                assert set(saved.namelist()) == set(inventory) | {'SHA256.json'}
                for name, expected in inventory.items():
                    digest = hashlib.sha256()
                    with saved.open(name) as stream:
                        for block in iter(lambda: stream.read(1024*1024), b''):
                            digest.update(block)
                    assert digest.hexdigest() == expected['sha256'], name
            receipt['download_inventory_verified'] = True
            (NATIVE/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
            print(json.dumps(dict(status=receipt['status'], archive_bytes=receipt['archive_bytes'],
                downloaded_verified=True, volume_name=VOLUME_NAME)), flush=True)
            assert receipt['status'] == EXPECTED, 'inspect downloaded failure artifacts'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Dùng grant pilot 0,50 USD đã được user duyệt')
    parser.add_argument('--define-only', action='store_true', help='Kiểm SDK và cấu hình, chưa build image hoặc chạy App')
    parser.add_argument('--gpu', choices=('T4', 'L4', 'auto'), default='T4')
    parser.add_argument('--run-id', default=RUN_ID)
    parser.add_argument('--wait-seconds', type=int, default=600,
                        help='Chờ cấp phát và kết quả 600–1800 giây; runtime GPU vẫn giữ cap600giây')
    arguments = parser.parse_args()
    assert re.fullmatch(r'modal-checkpoint-pilot-[0-9-]{11,24}', arguments.run_id)
    RUN_ID = arguments.run_id
    GPU = arguments.gpu
    assert 600 <= arguments.wait_seconds <= 1800
    WAIT_SECONDS = arguments.wait_seconds
    INPUTS = ROOT/'artifacts/akt/modal'/RUN_ID
    NATIVE = ROOT/'experiments/akt/results'/RUN_ID
    VOLUME_NAME = RUN_ID.replace('modal-', 'kltn-akt-', 1)
    source, plan = prepare()
    print(json.dumps(plan), flush=True)
    if arguments.run or arguments.define_only:
        execute(source, plan, define_only=arguments.define_only and not arguments.run)
