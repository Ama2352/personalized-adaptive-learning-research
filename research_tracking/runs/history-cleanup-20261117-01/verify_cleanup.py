"""Kiểm sau dọn: 70 link mất, 44 file giữ đúng SHA và 35 ZIP Drive còn đúng."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIVATE = ROOT / 'artifacts/akt/private/drive-upload'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan = load(HERE / 'DELETE_PLAN.json')
    result = load(HERE / 'DELETE_RESULT.json')
    assert result['status'] == 'COMPLETE' and result['deleted_paths'] == 70
    assert result['deleted_archive_groups'] == 35
    assert all(not (ROOT / path).exists() for group in plan['groups'] for path in group['paths'])
    rows = [json.loads(line) for line in (HERE / 'DELETE_JOURNAL.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    assert len(rows) == 140 and sum(row['action'] == 'DELETED' for row in rows) == 70
    protected = load(HERE / 'PROTECTED_FILES.json')
    for row in protected:
        path = ROOT / row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], row['path']
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    credentials = Credentials.from_authorized_user_file(str(PRIVATE / 'token.json'))
    remote = []
    try:
        with AuthorizedSession(credentials) as session:
            for group in plan['groups']:
                response = session.get('https://www.googleapis.com/drive/v3/files/' + group['remote_id'],
                    params={'fields': 'id,size,sha256Checksum,trashed'}, timeout=60)
                assert response.status_code == 200
                meta = response.json()
                assert (not meta.get('trashed') and int(meta['size']) == group['bytes']
                        and meta['sha256Checksum'] == group['sha256'])
                remote.append(meta)
    finally:
        temporary = PRIVATE / 'token.json.tmp'
        with temporary.open('w', encoding='utf-8') as stream:
            stream.write(credentials.to_json())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, PRIVATE / 'token.json')
    acceptance = dict(status='PASS_LOCAL_REMOVAL_PROTECTED_FILES_REMOTE_SHA256',
                      checked_at=datetime.now(timezone.utc).isoformat(), deleted_local_paths=70,
                      archived_unique_files=35, archived_bytes=35154218914,
                      protected_files_sha256_verified=len(protected),
                      remote_after_delete_sha256_verified=len(remote),
                      free_before=result['free_before'], free_after=result['free_after'],
                      observed_free_increase=result['free_after'] - result['free_before'],
                      relocation='RELOCATION_MANIFEST.json',
                      limits_vi='Free-space delta có thể chịu hoạt động khác. Kiểm Drive bằng SHA server, không tải lại 35GB.',
                      remote=remote)
    (HERE / 'ACCEPTANCE.json').write_text(json.dumps(acceptance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in acceptance.items() if k != 'remote'}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Kiểm sau dọn chưa đạt, cần giữ hồ sơ. Loại lỗi:', type(error).__name__)
        raise SystemExit(1)
