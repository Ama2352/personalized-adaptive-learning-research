"""Dựng image CPU từ lock cũ trong workspace mới, không gắn GPU."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(os.environ.get('KLTN_WORKSPACE_ROOT', 'D:/Dev/KLTN'))
HERE = ROOT / 'research_tracking/runs/junyi-refit-pipeline-20261114-01'


def probe():
    import json
    import subprocess
    result = subprocess.run(['/opt/kltn/.venv/bin/python', '-c',
        'import json,sys,torch;print(json.dumps(dict(python=sys.version,torch=torch.__version__,cuda_build=torch.version.cuda,cuda_available=torch.cuda.is_available())))'],
        capture_output=True, text=True, timeout=60, check=True)
    return json.loads(result.stdout)


def main():
    assert os.environ['MODAL_PROFILE'] == 'kltn2016'
    temporary = ROOT / 'artifacts/akt/runtime/modal-client-temp'
    temporary.mkdir(parents=True, exist_ok=True)
    for variable in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[variable] = str(temporary)
    import tempfile
    tempfile.tempdir = str(temporary)
    sys.path.insert(0, str(ROOT / 'experiments/akt'))
    from modal_budget_guard import ModalRunDeadline, ModalAppBudgetGuard, PendingOwnedModalApp, stop_owned_app_cli
    import modal
    lock = ROOT / 'artifacts/akt/runtime/modal-linux-cuda.lock.txt'
    assert hashlib.sha256(lock.read_bytes()).hexdigest() == '60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a'
    image = (modal.Image.debian_slim(python_version='3.13').apt_install('git')
        .add_local_file(lock, '/opt/locked-cu126.txt', copy=True)
        .run_commands('python -m venv --without-pip /opt/kltn/.venv',
            'timeout 480 python -m pip --python /opt/kltn/.venv/bin/python install '
            '--require-hashes --no-deps --only-binary=:all: --no-cache-dir --retries 0 '
            '--timeout 20 -r /opt/locked-cu126.txt'))
    identifier = 'workspace2016-runtime-cpu-20261115-02'
    app = modal.App('kltn-akt-' + identifier)
    function = app.function(image=image, cpu=1, memory=4096, timeout=90,
        retries=0, max_containers=1, scaledown_window=2)(probe)
    guard_path = HERE / 'workspace2016-runtime-stop02.json'
    binding = PendingOwnedModalApp(identifier, app.name, lambda: app.app_id)
    with ModalAppBudgetGuard(binding, ModalRunDeadline(900), stop_app=stop_owned_app_cli,
                             diagnostic_path=guard_path):
        with modal.enable_output(), app.run(environment_name='main'):
            result = function.remote()
            image_id = image.object_id
    assert result['torch'] == '2.7.1+cu126' and result['cuda_build'] == '12.6'
    assert result['cuda_available'] is False
    assert json.loads(guard_path.read_text())['stop_acknowledged'] is True
    receipt = dict(status='PASS_CPU_RUNTIME_NEW_WORKSPACE', image_id=image_id,
                   workspace='honguyenminhsang2016', runtime=result, gpu_started=False,
                   lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest())
    with (HERE / 'workspace2016-runtime01.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
