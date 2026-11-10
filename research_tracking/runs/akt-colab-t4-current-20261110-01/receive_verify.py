"""Nhận log T4, kiểm nội dung mà không import Torch hoặc chạy mô hình local."""
import base64
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import runpy
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SESSION = ROOT/'artifacts/akt/private/colab-bridge/session-fa618f21c2674be6a1831af6344c72d7'
metadata = json.loads((HERE/'export-metadata.json').read_bytes())


def preserve_file(path, data):
    if path.exists():
        assert path.is_file() and not path.is_symlink() and path.read_bytes() == data
    else:
        with path.open('xb') as stream:
            stream.write(data)


parts = {}
launch = None
for file in SESSION.glob('result*.json'):
    for output in (json.loads(file.read_bytes()).get('data') or {}).get('outputs', []):
        if output.get('output_type') != 'stream':
            continue
        try:
            value = json.loads(''.join(output.get('text', [])))
        except ValueError:
            continue
        if not isinstance(value, dict):
            continue
        if value.get('status') == 'T4_SMOKE_STARTED':
            launch = value
        if value.get('export_sha256') == metadata['sha256']:
            index = value['current_t4_part']
            data = base64.b64decode(value['data'], validate=True)
            assert index not in parts or parts[index] == data
            parts[index] = data
assert set(parts) == set(range(metadata['parts']))
raw = b''.join(parts[index] for index in range(metadata['parts']))
assert len(raw) == metadata['bytes'] and hashlib.sha256(raw).hexdigest() == metadata['sha256']
archive = zipfile.ZipFile(io.BytesIO(raw))
assert archive.testzip() is None
inventory = json.loads(archive.read('SHA256.json'))
assert len(archive.namelist()) == len(set(archive.namelist())) == len(inventory)+1
assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
for name, digest in inventory.items():
    path = PurePosixPath(name)
    assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
    assert hashlib.sha256(archive.read(name)).hexdigest() == digest

prefix = 'artifacts/akt/runtime/isolated-install02/'
installed = json.loads(archive.read(prefix+'result.json'))
assert installed['status'] == 'ISOLATED_ENV_READY_GPU_UNTESTED'
assert installed['installed_packages'] == 44 and installed['base_pip_unchanged'] is True
assert installed['elapsed_seconds'] <= 600 and installed['peak_workspace_bytes'] <= 20*1024**3
assert archive.read(prefix+'base-pip-before.stdout') == archive.read(prefix+'base-pip-after.stdout')
audit = installed['installed_origins']
assert audit['python'] == '3.13.16' and audit['package_count'] == 44
assert audit['external_distribution_origins'] == 0 and audit['cuda_initialized'] is False
report = json.loads(archive.read(prefix+'pip-install-report.json'))
expected = json.loads((HERE.parent/'akt-colab-isolated-cpu-20261110-01/expected44.json').read_bytes())
actual = {item['metadata']['name'].lower().replace('_', '-').replace('.', '-'): dict(
    version=item['metadata']['version'], url=item['download_info']['url'],
    sha256=item['download_info']['archive_info']['hashes']['sha256']) for item in report['install']}
assert len(report['install']) == 44 and actual == expected
prior = json.loads(archive.read('artifacts/akt/runtime/isolated-install01/result.json'))
assert prior['error'] == 'empty-venv failed; retain stdout/stderr'
assert 'artifacts/akt/runtime/isolated-install01/pip-install.stdout' not in inventory

smoke_path = 'experiments/akt/results/current-t4-four-variant-smoke-20261110-01/result.json'
smoke = json.loads(archive.read(smoke_path))
assert smoke['status'] == 'CUDA_FOUR_VARIANT_SMOKE_PASS'
assert smoke['gpu_name'] == 'Tesla T4' and smoke['torch_version'] == '2.7.1+cu126'
assert smoke['total_optimizer_updates'] == 8 and smoke['total_optimized_targets'] == 192
assert smoke['total_predictions'] == 24 and smoke['same_initial_backbone'] is True
assert smoke['source_unchanged'] is True and smoke['elapsed_seconds'] <= 180
assert smoke['model_checkpoint_generated'] is False and smoke['main_training'] is False
assert [row['variant'] for row in smoke['variants']] == ['A0', 'A1', 'A2', 'A3']
assert len({row['initial_backbone_sha256'] for row in smoke['variants']}) == 1
for row in smoke['variants']:
    assert row['optimized_targets'] == 48 and row['prediction_count'] == 6 and len(row['updates']) == 2
    assert row['initial_backbone_sha256'] != row['final_backbone_sha256']
    assert row['peak_vram_allocated_bytes'] <= 2*1024**3
    assert all(math.isfinite(p) and 0 <= p <= 1 for sequence in row['predictions'] for p in sequence)
    assert all(update['stepped'] and update['parameter_updated'] and update['valid_targets'] == 24
        and math.isfinite(update['mean_loss']) for update in row['updates'])
watchdog = json.loads(archive.read('artifacts/akt/runtime/t4-smoke01/result.json'))
assert watchdog['returncode'] == 0 and watchdog['elapsed_seconds'] <= 190
assert launch and launch['worker_sha256'] == hashlib.sha256((HERE/'cuda_smoke.py').read_bytes()).hexdigest()
manifest = json.loads(archive.read('BUNDLE_MANIFEST.json'))
contents, _ = runpy.run_path(str(ROOT/'scripts/akt/build_colab_bundle.py'))['bundle_contents']()
assert manifest['source_files'] == {name:hashlib.sha256(data).hexdigest() for name, data in contents.items()}

native = ROOT/'experiments/akt/results/colab-t4-current-20261110-01'
native.mkdir(exist_ok=True)
assert not native.is_symlink()
preserve_file(native/'logs.zip', raw)
remote = HERE/'remote'
remote.mkdir(exist_ok=True)
assert not remote.is_symlink()
selected = {prefix+'result.json':'install02-result.json', prefix+'installed-origins-cpu.stdout':'origins.stdout',
    'artifacts/akt/runtime/isolated-install01/result.json':'install01-result.json',
    'artifacts/akt/runtime/isolated-install01/empty-venv.stderr':'install01-error.log',
    smoke_path:'smoke-result.json', 'artifacts/akt/runtime/t4-smoke01/worker.log':'smoke-worker.log',
    'artifacts/akt/runtime/t4-smoke01/result.json':'watchdog-result.json'}
for source, name in selected.items():
    preserve_file(remote/name, archive.read(source))
preserve_file(HERE/'archive-inventory.json', (json.dumps(inventory, indent=2)+'\n').replace('\n', '\r\n').encode())
preserve_file(HERE/'smoke-launch-receipt.json', (json.dumps(launch, indent=2)+'\n').replace('\n', '\r\n').encode())
proof = dict(status='CURRENT_T4_FOUR_VARIANT_SMOKE_VERIFIED', variants=['A0','A1','A2','A3'],
    optimizer_updates=8, synthetic_targets=192, predictions=24, source_files_in_bundle=len(contents),
    packages_verified=44, same_initial_backbone=True, source_matches_local=True,
    elapsed_seconds=smoke['elapsed_seconds'], max_peak_vram_allocated_bytes=max(
        row['peak_vram_allocated_bytes'] for row in smoke['variants']),
    archive_sha256=metadata['sha256'], archive_bytes=len(raw),
    actual_research_checkpoint_recovery_verified=False, representative_throughput_measured=False,
    main_training_completed=False, model_checkpoint_generated=False, modal_spend_usd=0)
proof_bytes = (json.dumps(proof, indent=2)+'\n').replace('\n', '\r\n').encode()
preserve_file(HERE/'verification.json', proof_bytes)
preserve_file(native/'receipt.json', proof_bytes)
print(json.dumps(proof))
