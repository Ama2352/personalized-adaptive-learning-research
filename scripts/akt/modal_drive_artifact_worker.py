"""CPU worker đồng bộ snapshot calibration trên Volume sang Drive Sang."""
import os
from pathlib import Path
import warnings

ROOT = Path(__file__).resolve().parents[2] if os.name == 'nt' else Path('/opt/kltn')
if os.name == 'nt':
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal2016.toml')
    os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
import modal

volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1', environment_name='main')
image = (modal.Image.debian_slim(python_version='3.13')
         .pip_install('requests==2.34.2', 'google-auth==2.62.1')
         .add_local_file(str(ROOT / 'scripts/akt/drive_artifact_sink.py'), '/opt/kltn/scripts/akt/drive_artifact_sink.py')
         .add_local_file(str(ROOT / 'scripts/akt/drive_resumable_upload.py'), '/opt/kltn/scripts/akt/drive_resumable_upload.py'))
app = modal.App('kltn-drive-artifact-cpu')


@app.function(image=image, cpu=1, memory=1024, timeout=900, startup_timeout=180,
              max_containers=1, scaledown_window=2, retries=0,
              single_use_containers=True, volumes={'/artifacts': volume},
              secrets=[modal.Secret.from_name('kltn-drive-artifacts-sang2005-20261117',
                        environment_name='main', required_keys=['KLTN_DRIVE_OAUTH_JSON'])])
def publish(request):
    """Gọi tuần tự sau khi GPU đã trả, snapshot phải đóng và commit trước."""
    import sys
    sys.path.insert(0, '/opt/kltn/scripts/akt')
    import drive_artifact_sink as sink
    expected = {'run_id', 'tranche_id', 'files', 'max_total_bytes'}
    if not isinstance(request, dict) or set(request) != expected:
        raise ValueError('Request cần đúng hợp đồng artifact CPU.')
    run_id = sink._identifier(request['run_id'])
    tranche_id = sink._identifier(request['tranche_id'])
    limit = request['max_total_bytes']
    if type(limit) is not int or not 0 < limit <= 2 * 1024**3:
        raise ValueError('Giới hạn mỗi tranche cần nằm trong 2 GiB.')
    if not isinstance(request['files'], list) or 'config.json' not in request['files']:
        raise ValueError('Snapshot cần lưu config.json cùng artifact.')
    volume.reload()
    sink.CLOUD_ROOT = Path('/artifacts').resolve(strict=True)
    source = sink.CLOUD_ROOT / run_id / tranche_id / 'payloads'
    return sink.publish_from_environment(source_root=source, files=request['files'],
        run_id=run_id, tranche_id=tranche_id, max_total_bytes=limit,
        volume_commit=volume.commit, chunk_bytes=32 * 1024**2, retries=2)
