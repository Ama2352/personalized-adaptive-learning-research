"""Đọc lại metadata Drive của đủ lịch sử, đối chiếu pin nguồn và thư mục."""
from datetime import datetime, timezone, timedelta
import importlib.util
import json
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIVATE = ROOT / 'artifacts/akt/private/drive-upload'
spec = importlib.util.spec_from_file_location('drive_upload', ROOT / 'scripts/akt/drive_resumable_upload.py')
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


def main():
    plan = upload.read_json(HERE / 'UPLOAD_PLAN.json')
    credentials = Credentials.from_authorized_user_file(str(PRIVATE / 'token.json'), [upload.SCOPE])
    files = []
    folders = []
    with upload.single_writer(PRIVATE / 'upload.lock'):
        try:
            with AuthorizedSession(credentials) as session:
                worker = upload.Uploader(session, plan, PRIVATE / 'state.json', HERE, retries=3)
                for relative, file_id in worker.state['folders'].items():
                    meta = worker.api('GET', f'/files/{file_id}',
                                      params={'fields': upload.FIELDS + ',webViewLink'}).json()
                    if relative == '.':
                        name = plan['folder_name']
                        parent = plan['parent_id']
                    else:
                        name = Path(relative).name
                        parent_key = Path(relative).parent.as_posix()
                        parent = worker.state['folders'][parent_key]
                    if (meta.get('trashed') or meta['mimeType'] != upload.FOLDER
                            or meta['name'] != name or parent not in meta['parents']):
                        raise RuntimeError('Thư mục Drive không khớp kế hoạch.')
                    folders.append(dict(path=relative, id=file_id, url=meta.get('webViewLink')))
                for row in plan['files']:
                    path = Path(plan['source']) / row['path']
                    if upload.fingerprint(path) != {k: row[k] for k in ('bytes', 'mtime_ns')}:
                        raise RuntimeError(f'Nguồn đã đổi sau upload: {row["path"]}')
                    entry = worker.state['files'][row['path']]
                    if not entry.get('complete') or entry['local']['sha256'] != row['sha256']:
                        raise RuntimeError('Biên nhận file chưa đủ hoặc SHA nguồn không khớp plan.')
                    parent_key = Path(row['path']).parent.as_posix()
                    parent = worker.state['folders'][parent_key]
                    meta = worker.api('GET', f'/files/{entry["remote_id"]}',
                                      params={'fields': upload.FIELDS + ',webViewLink'}).json()
                    check = dict(row, md5=entry['local']['md5'])
                    if not worker.matches(meta, check, parent):
                        raise RuntimeError(f'Checksum Drive đọc lại không khớp: {row["path"]}')
                    files.append(dict(path=row['path'], bytes=row['bytes'], id=meta['id'],
                                      local_sha256=row['sha256'], remote_md5=meta['md5Checksum'],
                                      remote_sha256=meta.get('sha256Checksum'), url=meta.get('webViewLink')))
        finally:
            upload.atomic_json(PRIVATE / 'token.json', json.loads(credentials.to_json()))
    assert len(files) == 37 and sum(row['bytes'] for row in files) == 35154236922
    root_folder = next(row for row in folders if row['path'] == '.')
    result = dict(status='REMOTE_METADATA_CHECKSUM_READBACK_VERIFIED', verified_files=len(files),
                  zip_files=35, support_files=2, bytes=sum(row['bytes'] for row in files),
                  server_sha256_verified=sum(bool(row['remote_sha256']) for row in files),
                  source_size_mtime_unchanged=37, folder_url=root_folder['url'],
                  completed_local=datetime.now(timezone(timedelta(hours=7))).isoformat(),
                  local_files_deleted=0,
                  limit_vi='Kiểm bằng checksum server và pin hash local trước upload, không tải lại 35 GB.',
                  folders=folders, files=files)
    upload.atomic_json(HERE / 'READBACK_ACCEPTANCE.json', result)
    execution = upload.read_json(HERE / 'EXECUTION_STATE.json')
    execution.update(status='COMPLETE_READBACK_VERIFIED', completed_local=result['completed_local'],
                     verified_files=len(files), verified_bytes=result['bytes'],
                     acceptance='READBACK_ACCEPTANCE.json', folder_url=root_folder['url'])
    upload.atomic_json(HERE / 'EXECUTION_STATE.json', execution)
    print(json.dumps({k: v for k, v in result.items() if k not in ('folders', 'files')}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        print(str(error))
        raise SystemExit(1)
    except Exception as error:
        print(f'Đọc lại dừng do {type(error).__name__}; giữ hồ sơ để kiểm.')
        raise SystemExit(1)
