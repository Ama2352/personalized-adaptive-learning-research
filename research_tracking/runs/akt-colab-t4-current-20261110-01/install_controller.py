"""Một lượt cài 44 wheel đã ghim vào venv Colab riêng, tối đa 600 giây."""
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import sys
import time
import traceback

ROOT = Path('/content/kltn-current-t4-20261110-01')
INPUT = ROOT/'artifacts/akt/runtime/t4-input01'
OUT = ROOT/'artifacts/akt/runtime/isolated-install01'
TARGET = ROOT/'.venv/bin/python'
LOCK = ROOT/'artifacts/akt/dependencies/linux-cu126/candidate-linux-cuda.lock.txt'
BASE = Path('/usr/bin/python3')

assert not os.environ.get('COLAB_TPU_ADDR')
assert subprocess.check_output(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],text=True,timeout=10).strip() == 'Tesla T4'
assert ROOT.is_dir() and ROOT.resolve() == ROOT and TARGET.is_file()
pins = json.loads((INPUT/'input-manifest.json').read_text())
for name, digest in pins['files'].items():
    assert hashlib.sha256((INPUT/name).read_bytes()).hexdigest() == digest
assert hashlib.sha256(LOCK.read_bytes()).hexdigest() == '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
spec = importlib.util.spec_from_file_location('bounded_install_reuse', INPUT/'bounded_install_reuse.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
OUT.mkdir(exist_ok=False)
for name in ('tmp', 'home', 'cache-home', 'config-home', 'torch-home', 'triton-cache', 'cuda-cache'):
    (OUT/name).mkdir()
source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
stage = helper.Stage(source_sha, 'USER_APPROVED_FREE_T4_CHECK_20261110')
result = dict(status='FAILED_RETAIN_PARTIAL_NO_RETRY', scope='Venv installation on free T4; model GPU steps not started',
    source_sha256=source_sha, target=str(TARGET), lock_sha256=hashlib.sha256(LOCK.read_bytes()).hexdigest(),
    global_install=False, gpu_allocation=False, gpu_model_steps=0, optimizer_steps=0, modal_spend_usd=0)
try:
    probe = stage.python('empty-venv', TARGET, helper.PROBE, 20)
    assert probe['distributions'] == [] and probe['purelib_entries'] == []
    assert probe['torch_spec'] == probe['numpy_spec'] == probe['pip_spec'] == 'None'
    before = stage.python('base-pip-before', BASE, helper.BASE_PIP, 20)
    expected = json.loads((INPUT/'expected44.json').read_text())
    assert len(expected) == 44
    command = [str(BASE), '-I', '-B', '-m', 'pip', '--python', str(TARGET), 'install',
        '--require-hashes', '--no-deps', '--no-index', '--only-binary=:all:', '--no-cache-dir',
        '--no-input', '--disable-pip-version-check', '--progress-bar', 'off', '--retries', '0',
        '--timeout', '20', '--report', str(OUT/'pip-install-report.json'), '-r', str(LOCK)]
    (OUT/'command.json').write_text(json.dumps(command, indent=2))
    stage.run('pip-install', command, 500)
    report = json.loads((OUT/'pip-install-report.json').read_text())
    actual = {helper.normalize(i['metadata']['name']): dict(version=i['metadata']['version'],
        url=i['download_info']['url'], sha256=i['download_info']['archive_info']['hashes']['sha256'])
        for i in report['install']}
    assert len(report['install']) == 44 and actual == expected
    stage.run('pip-check', [str(BASE), '-I', '-B', '-m', 'pip', '--python', str(TARGET), 'check'], 30)
    audit = stage.python('installed-origins-cpu', TARGET, (INPUT/'audit_installed.py').read_text(), 45)
    after = stage.python('base-pip-after', BASE, helper.BASE_PIP, 20)
    assert before == after and audit['package_count'] == 44 and audit['external_distribution_origins'] == 0
    assert audit['torch_build'] == '2.7.1+cu126' and audit['cuda_initialized'] is False
    stage.check()
    result.update(status='ISOLATED_ENV_READY_GPU_UNTESTED', installed_packages=44,
        installed_origins=audit, base_pip_unchanged=True)
except BaseException as error:
    result.update(error_type=type(error).__name__, error=str(error))
    (OUT/'failure.log').write_text(traceback.format_exc())
finally:
    for child in stage.children:
        if not child.get('cleanup_attempted'): stage.kill_owned(child)
    result.update(elapsed_seconds=time.monotonic()-stage.start, peak_workspace_bytes=stage.peak,
        children=stage.children, cleanup=stage.cleanup)
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'installed_origins'}), flush=True)
sys.exit(0 if result['status'] == 'ISOLATED_ENV_READY_GPU_UNTESTED' else 1)
