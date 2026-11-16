"""Đối chiếu 35 archive, mọi hardlink và Drive; chỉ lập allowlist, chưa xóa."""
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
HISTORY = ROOT / 'experiments/akt/results/drive-offload-history-20261116-01'
UPLOAD = ROOT / 'research_tracking/runs/drive-history-upload-20261116-01'
PRIVATE = ROOT / 'artifacts/akt/private/drive-upload'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def checked_path(relative):
    path = ROOT / relative
    assert path.is_file() and path.resolve().is_relative_to(ROOT.resolve())
    for node in (path, *path.parents):
        assert not node.is_symlink() and not node.is_junction(), str(node)
        if node == ROOT:
            break
    return path


def hardlinks(path):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    first = kernel.FindFirstFileNameW
    first.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                      ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR]
    first.restype = wintypes.HANDLE
    following = kernel.FindNextFileNameW
    following.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR]
    following.restype = wintypes.BOOL
    kernel.FindClose.argtypes = [wintypes.HANDLE]
    buffer = ctypes.create_unicode_buffer(32768)
    size = wintypes.DWORD(len(buffer))
    handle = first(str(path), 0, ctypes.byref(size), buffer)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    result = []
    try:
        result.append(Path(path.drive + buffer.value))
        while True:
            size.value = len(buffer)
            if not following(handle, ctypes.byref(size), buffer):
                code = ctypes.get_last_error()
                if code != 38:  # ERROR_HANDLE_EOF
                    raise ctypes.WinError(code)
                break
            result.append(Path(path.drive + buffer.value))
    finally:
        kernel.FindClose(handle)
    return result


def main():
    HERE.mkdir(exist_ok=True)
    plan_path = HERE / 'DELETE_PLAN.json'
    assert not plan_path.exists(), 'Lượt đã có plan, phải rà trạng thái trước khi chạy lại.'
    source_manifest = load(HISTORY / 'MANIFEST.json')
    receipt = load(UPLOAD / 'READBACK_ACCEPTANCE.json')
    completion = load(UPLOAD / 'COMPLETION.json')
    receipt_pin = next(h for p, h in completion['sha256'].items()
                       if p.replace('\\', '/').endswith('/READBACK_ACCEPTANCE.json'))
    assert sha(UPLOAD / 'READBACK_ACCEPTANCE.json') == receipt_pin
    assert receipt['status'] == 'REMOTE_METADATA_CHECKSUM_READBACK_VERIFIED'
    rows = source_manifest['files']
    assert len(rows) == 35 and sum(row['bytes'] for row in rows) == 35154218914
    remote = {row['path']: row for row in receipt['files']}
    compact = [ROOT / 'experiments/akt/results/model-export-20261112-01']
    for variant, date in (('a0', '20261112'), ('a1', '20261113'),
                          ('a2', '20261114'), ('a3', '20261114')):
        compact.append(ROOT / f'experiments/akt/results/model-export-{variant}-batch128-{date}-01')
        compact.append(ROOT / f'experiments/akt/results/model-export-{variant}-refit-20261114-01')
    protected = []
    for directory in compact:
        assert directory.is_dir(), str(directory)
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                stat = path.stat()
                protected.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=stat.st_size,
                                      sha256=sha(path), volume_id=stat.st_dev, file_id=stat.st_ino))
    audit_zip = ROOT / 'experiments/akt/results/modal-junyi-a0-b128-h100-20261112-03/artifacts.zip'
    assert audit_zip.is_file()
    stat = audit_zip.stat()
    protected.append(dict(path=audit_zip.relative_to(ROOT).as_posix(), bytes=stat.st_size,
                          sha256=sha(audit_zip), volume_id=stat.st_dev, file_id=stat.st_ino))
    protected_ids = {(row['volume_id'], row['file_id']) for row in protected}

    def inspect(row):
        source = checked_path(row['source'])
        alias = checked_path((HISTORY / row['upload_path']).relative_to(ROOT))
        before = source.stat()
        other = alias.stat()
        identity = (before.st_dev, before.st_ino)
        assert identity == (other.st_dev, other.st_ino) and identity not in protected_ids
        assert before.st_size == other.st_size == row['bytes']
        links = hardlinks(source)
        expected = {os.path.normcase(str(source)), os.path.normcase(str(alias))}
        assert {os.path.normcase(str(path)) for path in links} == expected
        assert before.st_nlink == other.st_nlink == len(links) == 2
        digest = sha(source)
        after = source.stat()
        assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
        saved = remote[row['upload_path']]
        assert digest == row['sha256'] == saved['local_sha256'] == saved['remote_sha256']
        assert saved['bytes'] == row['bytes']
        return dict(paths=[row['source'], alias.relative_to(ROOT).as_posix()], bytes=row['bytes'],
                    sha256=digest, modified_ns=after.st_mtime_ns, volume_id=after.st_dev,
                    file_id=after.st_ino, links=2, remote_id=saved['id'], remote_url=saved['url'],
                    remote_path=row['upload_path'])

    print('Đang hash 35 archive và đối chiếu toàn bộ hardlink.', flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        groups = list(pool.map(inspect, rows))
    assert len({(r['volume_id'], r['file_id']) for r in groups}) == 35
    # Chỉ đọc Drive, lưu refresh token riêng, không sửa file hoặc quyền remote.
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    credentials = Credentials.from_authorized_user_file(str(PRIVATE / 'token.json'))
    live = []
    try:
        with AuthorizedSession(credentials) as session:
            response = session.get('https://www.googleapis.com/drive/v3/about',
                                   params={'fields': 'user(emailAddress)'}, timeout=60)
            assert response.status_code == 200
            assert response.json()['user']['emailAddress'] == 'honguyenminhsang2005@gmail.com'
            folders = {row['path']: row['id'] for row in receipt['folders']}
            for group in groups:
                response = session.get('https://www.googleapis.com/drive/v3/files/' + group['remote_id'],
                    params={'fields': 'id,name,size,sha256Checksum,md5Checksum,parents,trashed'}, timeout=60)
                assert response.status_code == 200
                meta = response.json()
                parent = folders[Path(group['remote_path']).parent.as_posix()]
                assert (not meta.get('trashed') and meta['sha256Checksum'] == group['sha256']
                        and int(meta['size']) == group['bytes'] and parent in meta['parents']
                        and meta['name'] == Path(group['remote_path']).name)
                live.append(meta)
    finally:
        temporary = PRIVATE / 'token.json.tmp'
        with temporary.open('w', encoding='utf-8') as stream:
            stream.write(credentials.to_json())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, PRIVATE / 'token.json')
    save(HERE / 'LIVE_DRIVE_VERIFICATION.json', dict(at=datetime.now(timezone.utc).isoformat(),
         status='PASS_35_REMOTE_SHA256', files=live))
    save(HERE / 'PROTECTED_FILES.json', protected)
    plan = dict(status='READY_FOR_AUTHORIZED_DELETE', at=datetime.now(timezone.utc).isoformat(),
                groups=groups, unique_files=35, delete_paths=70, unique_logical_bytes=35154218914,
                directory_entry_logical_bytes=70308437828, all_groups_have_only_two_approved_links=True,
                protected_files=len(protected), remote_reverified=35,
                authorization_vi='User yêu cầu xóa an toàn 35 GB lịch sử đã sao lưu, giữ model/checkpoint đang cần.',
                metadata_preserved_vi='MANIFEST và hướng dẫn upload cũ giữ nguyên; relocation riêng trỏ Drive.')
    save(plan_path, plan)
    save(HERE / 'PLAN_PIN.json', dict(sha256=sha(plan_path)))
    print(json.dumps({k: v for k, v in plan.items() if k != 'groups'}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Preflight dừng, chưa xóa file. Loại lỗi:', type(error).__name__, flush=True)
        raise SystemExit(1)
