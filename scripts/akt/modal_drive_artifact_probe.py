"""Kiểm CPU cloud lưu artifact Drive, ngắt và tiếp tục không tải binary về máy."""
import json
import os
from pathlib import Path
import warnings

ROOT = Path(__file__).resolve().parents[2] if os.name == 'nt' else Path('/opt/kltn')
if os.name == 'nt':
    os.environ['MODAL_CONFIG_PATH'] = str(ROOT / 'artifacts/akt/private/modal2016.toml')
    os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
import modal

RUN_ID = 'drive-cloud-artifacts-20261117-01'
TRANCHE = 'cpu-resume-probe01'
volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',
                                environment_name='main', create_if_missing=True, version=2)
image = (modal.Image.debian_slim(python_version='3.13')
         .pip_install('requests==2.34.2', 'google-auth==2.62.1')
         .add_local_file(str(ROOT / 'scripts/akt/drive_artifact_sink.py'), '/opt/kltn/scripts/akt/drive_artifact_sink.py')
         .add_local_file(str(ROOT / 'scripts/akt/drive_resumable_upload.py'), '/opt/kltn/scripts/akt/drive_resumable_upload.py'))
app = modal.App('kltn-drive-cpu-resume-probe')


@app.function(image=image, cpu=1, memory=1024, timeout=180, startup_timeout=180,
              max_containers=1, scaledown_window=2, retries=0,
              single_use_containers=True, volumes={'/artifacts': volume},
              secrets=[modal.Secret.from_name('kltn-drive-artifacts-sang2005-20261117',
                        environment_name='main', required_keys=['KLTN_DRIVE_OAUTH_JSON'])])
def probe(interrupt):
    import hashlib
    import sys
    import time
    sys.path.insert(0, '/opt/kltn/scripts/akt')
    import drive_artifact_sink as sink

    started = time.monotonic()
    volume.reload()
    # Mount Modal có thể là symlink do runtime quản lý. Pin physical root
    # một lần tại worker, giữ kiểm chống alias cho mọi payload bên dưới.
    sink.CLOUD_ROOT = Path('/artifacts').resolve(strict=True)
    batch = sink.CLOUD_ROOT / RUN_ID / TRANCHE
    payloads = batch / 'payloads'
    payloads.mkdir(parents=True, exist_ok=True)
    binary = payloads / 'probe.bin'
    if not binary.exists():
        binary.write_bytes(bytes(range(256)) * 4096)
    config = payloads / 'config.json'
    if not config.exists():
        config.write_text(json.dumps(dict(purpose='Kiểm kỹ thuật lưu Drive và tiếp tục phiên upload',
            synthetic=True, bytes=1048576, gpu=False, drive_account=sink.DRIVE_ACCOUNT),
            ensure_ascii=False, indent=2), encoding='utf-8')
    volume.commit()
    state_path = batch / '.drive-state/state.json'

    def offset():
        if not state_path.exists():
            return 0
        state = json.loads(state_path.read_text())
        return state.get('files', {}).get('probe.bin', {}).get('offset', 0) or 0

    initial_offset = offset()
    deliberately_interrupted = False

    def commit():
        nonlocal deliberately_interrupted
        volume.commit()
        acknowledged = offset()
        if interrupt and 262144 <= acknowledged < 1048576:
            deliberately_interrupted = True
            raise RuntimeError('CONTROLLED_INTERRUPT_AFTER_DURABLE_DRIVE_ACK')

    try:
        receipt = sink.publish_from_environment(source_root=payloads,
            files=['config.json', 'probe.bin'], run_id=RUN_ID, tranche_id=TRANCHE,
            volume_commit=commit, max_total_bytes=1100000, chunk_bytes=262144, retries=2)
    except sink.ArtifactSinkError:
        if not deliberately_interrupted:
            raise
        return dict(status='CONTROLLED_INTERRUPT_PERSISTED', acknowledged_bytes=offset(),
                    initial_offset=initial_offset, gpu=False, seconds=time.monotonic()-started)
    if interrupt:
        raise RuntimeError('Probe không đi qua ngắt giữa file, cần rà evidence.')
    if not 262144 <= initial_offset < 1048576:
        raise RuntimeError('Không tìm thấy offset bền vững của lượt ngắt.')
    return dict(status='PASS_CLOUD_DRIVE_RESUME_SHA256', initial_offset=initial_offset,
                receipt=receipt, gpu=False, seconds=time.monotonic()-started,
                payload_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())


if __name__ == '__main__':
    destination = ROOT / 'research_tracking/runs' / RUN_ID / 'CLOUD_PROBE01.json'
    if destination.exists():
        raise SystemExit('Đã có receipt; đọc trạng thái trước khi chạy lại.')
    results = []
    with modal.enable_output(), app.run(environment_name='main'):
        first = probe.remote(True)
        results.append(first)
        if first['status'] != 'CONTROLLED_INTERRUPT_PERSISTED':
            raise RuntimeError('Lượt đầu chưa đạt điều kiện ngắt.')
        results.append(probe.remote(False))
    destination.write_text(json.dumps(dict(results=results, budget_reservation_usd=0.05,
        gpu_called=False, large_outputs_downloaded=False), ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False))
