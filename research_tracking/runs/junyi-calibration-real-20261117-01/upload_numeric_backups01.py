"""Stream hai snapshot số sang Drive, chỉ CPU local và API, không binary trên đĩa."""
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback
import warnings

ROOT = Path.cwd()
B = ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'
PRIVATE = ROOT/'artifacts/akt/private/drive-upload/numeric-backups-20261117-01'
os.environ['MODAL_CONFIG_PATH'] = str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE'] = 'kltn2016'
warnings.filterwarnings('ignore', message=r'Your Modal token .*')
sys.path[:0] = [str(ROOT/'scripts/akt'), str(B)]
import modal
import psutil
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from drive_stream_upload import upload_stream
from modal_volume_archive import iter_zip_bytes, validate_plan, zip_size
from fetch_calibration_metadata01 import API, ACCOUNT, PARENT, RUN, FOLDER, MetadataDrive


def save_once(path, value):
    if path.exists():
        assert json.loads(path.read_text()) == value
        return
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def archive_folder(session):
    drive = MetadataDrive(session)
    about = drive.get('/about', params={'fields': 'user(emailAddress)'}).json()
    assert about['user']['emailAddress'] == ACCOUNT
    run_folder = drive.folder(PARENT, RUN)
    assert run_folder is not None
    name = 'numeric-backups-local-stream-20261117-01'
    folder = drive.folder(run_folder, name)
    if folder is None:
        response = session.post(API+'/files', json=dict(name=name, mimeType=FOLDER, parents=[run_folder]),
            params={'fields': 'id'}, timeout=30, allow_redirects=False)
        response.raise_for_status()
        folder = response.json()['id']
    metadata = drive.get('/files/'+folder,
        params={'fields': 'id,parents,owners(emailAddress),trashed'}).json()
    assert metadata['parents'] == [run_folder] and not metadata['trashed']
    assert any(owner.get('emailAddress') == ACCOUNT for owner in metadata['owners'])
    return folder


def telemetry(stop):
    process = psutil.Process()
    path = B/'NUMERIC_STREAM_RESOURCE01.jsonl'
    with path.open('a', encoding='utf-8') as stream:
        while not stop.is_set():
            offsets = {}
            for variant in ('A2', 'A3'):
                state = PRIVATE/f'{variant}.json'
                if state.exists():
                    try:
                        payload = json.loads(state.read_text())
                        offsets[variant] = payload.get('offset', 0)
                    except (OSError, ValueError):
                        pass
            row = dict(at=time.time(), rss_bytes=process.memory_info().rss, offsets=offsets)
            stream.write(json.dumps(row)+'\n')
            stream.flush()
            stop.wait(2)


def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    credentials = Credentials.from_authorized_user_file(
        str(ROOT/'artifacts/akt/private/drive-upload/token.json'), ['https://www.googleapis.com/auth/drive'])
    stop = threading.Event()
    monitor = threading.Thread(target=telemetry, args=(stop,), daemon=True)
    monitor.start()
    try:
        with AuthorizedSession(credentials) as session:
            folder = archive_folder(session)
            save_once(B/'NUMERIC_BACKUP_FOLDER01.json', dict(account=ACCOUNT, parent_id=PARENT,
                folder_id=folder, url='https://drive.google.com/drive/folders/'+folder,
                mode='LOCAL_STREAM_NO_MODAL_COMPUTE_NO_LOCAL_BINARY'))
            for variant in ('A2', 'A3'):
                source = json.loads((B/f'{variant}_NUMERIC_BACKUP_PLAN01.json').read_text())
                validate_plan(source)
                plan = dict(folder_id=folder, name=variant+'_NUMERIC_COMPLETE.zip',
                    total_bytes=zip_size(source), source_plan_sha256=source['source_plan_sha256'])
                print(variant, 'LOCAL_STREAM_START', plan['total_bytes'], flush=True)
                # Volume mới cho mỗi lần tái tạo stream, tránh giữ reader đã đóng.
                def factory():
                    volume = modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1', environment_name='main')
                    return iter_zip_bytes(volume, source)
                receipt = upload_stream(session, plan, factory, PRIVATE/f'{variant}.json')
                assert receipt['status'] == 'REMOTE_STREAM_SHA256_VERIFIED'
                metadata = MetadataDrive(session).get('/files/'+receipt['file_id'],
                    params={'fields': 'id,size,sha256Checksum,owners(emailAddress),parents'}).json()
                assert metadata['sha256Checksum'] == receipt['sha256']
                assert int(metadata['size']) == receipt['bytes'] and metadata['parents'] == [folder]
                assert any(owner.get('emailAddress') == ACCOUNT for owner in metadata['owners'])
                receipt['account'] = ACCOUNT
                receipt['source_members'] = len(source['entries'])
                receipt['url'] = 'https://drive.google.com/file/d/'+receipt['file_id']+'/view'
                save_once(B/f'{variant}_NUMERIC_DRIVE_BACKUP01.json', receipt)
                print(variant, 'DRIVE_ARCHIVE_SHA256_VERIFIED', receipt['bytes'], flush=True)
    finally:
        stop.set()
        monitor.join(timeout=5)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        PRIVATE.mkdir(parents=True, exist_ok=True)
        (PRIVATE/'last-error.txt').write_text(traceback.format_exc(), encoding='utf-8')
        print('LOCAL_STREAM_STOPPED_STATE_RETAINED', type(error).__name__, flush=True)
        raise SystemExit(1) from None
