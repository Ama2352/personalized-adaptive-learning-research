"""Upload archive AKT lên Drive, lưu phiên riêng để tiếp tục sau mất mạng."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import time
from urllib.parse import urlparse

import requests
from google.auth.exceptions import TransportError

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/akt/results/drive-offload-history-20261116-01'
PRIVATE = ROOT / 'artifacts/akt/private/drive-upload'
EVIDENCE = ROOT / 'research_tracking/runs/drive-history-upload-20261116-01'
API = 'https://www.googleapis.com/drive/v3'
UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files'
FOLDER = 'application/vnd.google-apps.folder'
FIELDS = 'id,name,size,md5Checksum,sha256Checksum,parents,mimeType,trashed'
SCOPE = 'https://www.googleapis.com/auth/drive'


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def fingerprint(path):
    stat = path.stat()
    return dict(bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)


def hashes(path):
    before = fingerprint(path)
    sha = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            sha.update(block)
            md5.update(block)
    if before != fingerprint(path):
        raise RuntimeError('File nguồn thay đổi trong lúc hash.')
    return dict(**before, sha256=sha.hexdigest(), md5=md5.hexdigest())


def build_plan(source, parent_id, account):
    source = source.resolve()
    archive_manifest = read_json(source / 'MANIFEST.json')
    expected = {row['upload_path']: row for row in archive_manifest['files']}
    files = []
    for path in sorted(source.rglob('*')):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError('Thư mục upload có symlink/junction, cần rà riêng.')
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        stat = fingerprint(path)
        if stat['bytes'] == 0:
            raise RuntimeError(f'File rỗng cần xử lý riêng trước upload: {relative}')
        original = expected.get(relative)
        if original:
            if stat['bytes'] != original['bytes']:
                raise RuntimeError(f'Kích thước archive đã đổi: {relative}')
            digest = original['sha256']
        else:
            digest = hashes(path)['sha256']
        files.append(dict(path=relative, **stat, sha256=digest))
    if set(expected) - {row['path'] for row in files}:
        raise RuntimeError('Thiếu archive trong manifest.')
    return dict(source=str(source), parent_id=parent_id, account=account,
                folder_name=source.name, files=files,
                bytes=sum(row['bytes'] for row in files),
                note_vi='SHA archive lấy từ inventory lịch sử, sẽ hash thực tế từng file trước upload.')


def checked_offset(response, total):
    if response.status_code in (200, 201):
        return total
    if response.status_code != 308:
        raise RuntimeError(f'Phản hồi phiên upload không hợp lệ, HTTP {response.status_code}.')
    received = response.headers.get('Range')
    if not received:
        return 0
    match = re.fullmatch(r'bytes=0-(\d+)', received)
    if not match or not 0 < int(match[1]) + 1 <= total:
        raise RuntimeError('Drive trả vị trí byte không hợp lệ.')
    return int(match[1]) + 1


def safe_session_url(url):
    parsed = urlparse(url)
    if (parsed.scheme != 'https' or parsed.hostname != 'www.googleapis.com'
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or not parsed.path.startswith('/upload/drive/v3/files')):
        raise RuntimeError('Địa chỉ phiên upload không thuộc endpoint Drive được phép.')
    return url


@contextmanager
def single_writer(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError('Một uploader khác đang dùng trạng thái này.') from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class Uploader:
    def __init__(self, session, plan, state_path, evidence, chunk_bytes=32 * 1024**2,
                 retries=20, sleep=time.sleep):
        if chunk_bytes <= 0 or chunk_bytes % (256 * 1024):
            raise ValueError('Chunk phải là bội dương của 256 KiB.')
        self.session = session
        self.plan = plan
        self.state_path = state_path
        self.evidence = evidence
        self.chunk_bytes = chunk_bytes
        self.retries = retries
        self.sleep = sleep
        self.state = dict(plan=plan, files={}, folders={})
        if state_path.exists():
            self.state = read_json(state_path)
            if self.state['plan'] != plan:
                raise RuntimeError('Nguồn/đích hoặc inventory đã đổi. Giữ state cũ để rà trước.')

    def save(self):
        atomic_json(self.state_path, self.state)

    def event(self, action, **fields):
        self.evidence.mkdir(parents=True, exist_ok=True)
        with (self.evidence / 'events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(at=now(), action=action, **fields), ensure_ascii=False) + '\n')

    def wait(self, failures):
        if failures > self.retries:
            raise RuntimeError('Hết số lần thử lại. Chạy cùng lệnh để tiếp tục từ state đã giữ.')
        seconds = min(60, 2 ** min(failures, 6))
        print(f'Đang chờ mạng/Drive, thử lại sau {seconds}s.', flush=True)
        self.sleep(seconds)

    def api(self, method, path, allowed=(200,), **kwargs):
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(method, API + path, timeout=(20, 180),
                                                allow_redirects=False, **kwargs)
            except (requests.RequestException, TransportError):
                self.wait(attempt + 1)
                continue
            if response.status_code in allowed:
                return response
            if response.status_code == 429 or response.status_code >= 500:
                self.wait(attempt + 1)
                continue
            raise RuntimeError(f'Yêu cầu Drive thất bại, HTTP {response.status_code}.')
        raise RuntimeError('Drive chưa phản hồi.')

    def metadata(self, file_id):
        response = self.api('GET', f'/files/{file_id}', allowed=(200, 404), params={'fields': FIELDS})
        return response.json() if response.status_code == 200 else None

    def reserve_id(self):
        return self.api('GET', '/files/generateIds', params={'count': 1, 'space': 'drive'}).json()['ids'][0]

    def children(self, parent, name):
        escaped = name.replace('\\', '\\\\').replace("'", "\\'")
        query = f"'{parent}' in parents and name = '{escaped}' and trashed = false"
        rows = []
        page = None
        while True:
            params = dict(q=query, fields=f'nextPageToken,files({FIELDS})', pageSize=100)
            if page:
                params['pageToken'] = page
            result = self.api('GET', '/files', params=params).json()
            rows.extend(result.get('files', []))
            page = result.get('nextPageToken')
            if not page:
                return rows

    def folder(self, relative, parent, name):
        folders = self.state['folders']
        if relative not in folders:
            existing = [f for f in self.children(parent, name) if f['mimeType'] == FOLDER]
            if len(existing) > 1:
                raise RuntimeError(f'Có nhiều thư mục Drive cùng tên {name}, cần chỉ rõ đích.')
            folders[relative] = existing[0]['id'] if existing else self.reserve_id()
            self.save()
        file_id = folders[relative]
        meta = self.metadata(file_id)
        if meta is None:
            self.api('POST', '/files', allowed=(200, 201, 409),
                     json=dict(id=file_id, name=name, mimeType=FOLDER, parents=[parent]))
            meta = self.metadata(file_id)
        if (not meta or meta.get('trashed') or meta['mimeType'] != FOLDER
                or meta.get('name') != name or parent not in meta.get('parents', [])):
            raise RuntimeError('Thư mục Drive không khớp đích đã chốt.')
        return file_id

    def matches(self, meta, row, parent):
        return (meta and not meta.get('trashed') and int(meta.get('size', -1)) == row['bytes']
                and meta.get('name') == Path(row['path']).name
                and parent in meta.get('parents', []) and meta.get('md5Checksum') == row['md5']
                and (not meta.get('sha256Checksum') or meta['sha256Checksum'] == row['sha256']))

    def complete(self, relative, entry, meta, row, parent):
        if not self.matches(meta, row, parent):
            raise RuntimeError(f'Checksum/kích thước/đích Drive chưa khớp: {relative}')
        entry.update(complete=True, offset=row['bytes'])
        entry.pop('session_url', None)
        entry['receipt'] = dict(path=relative, file_id=meta['id'], bytes=row['bytes'],
                                local_sha256=row['sha256'], remote_md5=meta['md5Checksum'],
                                remote_sha256=meta.get('sha256Checksum'), verified_at=now())
        self.save()
        atomic_json(self.evidence / 'RECEIPTS.json',
                    [f['receipt'] for f in self.state['files'].values() if f.get('complete')])
        self.event('FILE_VERIFIED', **entry['receipt'])
        print(f'Đã kiểm xong {relative}', flush=True)

    def send_file(self, row, parent):
        relative = row['path']
        path = Path(self.plan['source']) / relative
        entry = self.state['files'].setdefault(relative, {})
        current = fingerprint(path)
        if current != {k: row[k] for k in ('bytes', 'mtime_ns')}:
            raise RuntimeError(f'Nguồn đã đổi: {relative}')
        if entry.get('local') is None:
            print(f'Kiểm SHA nguồn {relative}', flush=True)
            entry['local'] = hashes(path)
            if entry['local']['sha256'] != row['sha256']:
                raise RuntimeError(f'SHA nguồn không khớp inventory: {relative}')
            self.save()
        if (entry['local']['sha256'] != row['sha256']
                or {k: entry['local'][k] for k in ('bytes', 'mtime_ns')} != current):
            raise RuntimeError(f'Hash đã lưu không khớp inventory: {relative}')
        row = dict(row, md5=entry['local']['md5'])
        if 'remote_id' not in entry:
            matches = [f for f in self.children(parent, path.name) if self.matches(f, row, parent)]
            entry['remote_id'] = matches[0]['id'] if matches else self.reserve_id()
            self.save()
        meta = self.metadata(entry['remote_id'])
        if meta:
            self.complete(relative, entry, meta, row, parent)
            return
        if entry.get('complete'):
            raise RuntimeError(f'File đã nghiệm thu bị mất trên Drive: {relative}')
        failures = 0
        offset = None
        expired = 0
        last_progress = entry.get('offset') or 0
        while True:
            if fingerprint(path) != current:
                raise RuntimeError(f'Nguồn thay đổi trong lúc upload: {relative}')
            try:
                if 'session_url' not in entry:
                    # ID được lưu trước POST, tránh tạo file trùng khi mất phản hồi cuối.
                    response = self.session.request('POST', UPLOAD, params={'uploadType': 'resumable'},
                        json=dict(id=entry['remote_id'], name=path.name, parents=[parent]),
                        headers={'X-Upload-Content-Length': str(row['bytes']),
                                 'X-Upload-Content-Type': mimetypes.guess_type(path.name)[0] or 'application/octet-stream'},
                        timeout=(20, 180), allow_redirects=False)
                    if response.status_code == 409:
                        self.complete(relative, entry, self.metadata(entry['remote_id']), row, parent)
                        return
                    if response.status_code in (429, 500, 502, 503, 504):
                        raise requests.ConnectionError('Drive tạm bận')
                    if response.status_code not in (200, 201):
                        raise RuntimeError(f'Tạo phiên thất bại, HTTP {response.status_code}.')
                    entry['session_url'] = safe_session_url(response.headers['Location'])
                    self.save()
                    offset = None
                url = safe_session_url(entry['session_url'])
                if offset is None:
                    response = self.session.request('PUT', url, data=b'',
                        headers={'Content-Length': '0', 'Content-Range': f"bytes */{row['bytes']}"},
                        timeout=(20, 180), allow_redirects=False)
                else:
                    with path.open('rb') as stream:
                        stream.seek(offset)
                        block = stream.read(min(self.chunk_bytes, row['bytes'] - offset))
                    end = offset + len(block) - 1
                    response = self.session.request('PUT', url, data=block,
                        headers={'Content-Length': str(len(block)),
                                 'Content-Range': f"bytes {offset}-{end}/{row['bytes']}"},
                        timeout=(20, 180), allow_redirects=False)
                if response.status_code == 404:
                    meta = self.metadata(entry['remote_id'])
                    if meta:
                        self.complete(relative, entry, meta, row, parent)
                        return
                    expired += 1
                    if expired > 2:
                        raise RuntimeError('Phiên liên tục hết hạn. Giữ state để kiểm quyền/Drive.')
                    entry.pop('session_url')
                    self.save()
                    self.event('SESSION_EXPIRED', path=relative)
                    continue
                if response.status_code == 429 or response.status_code >= 500:
                    raise requests.ConnectionError('Drive tạm bận')
                offset = checked_offset(response, row['bytes'])
                if response.status_code in (200, 201):
                    self.complete(relative, entry, self.metadata(entry['remote_id']), row, parent)
                    return
                if offset == row['bytes']:
                    offset = None
                entry['offset'] = offset
                self.save()
                if offset is not None and offset > last_progress:
                    failures = 0
                    last_progress = offset
                shown_offset = row['bytes'] if offset is None else offset
                print(f"{relative}: {shown_offset / row['bytes']:.1%}", flush=True)
            except (requests.RequestException, TransportError):
                offset = None  # Hỏi byte Drive đã nhận trước khi gửi lại sau mất mạng.
                failures += 1
                self.wait(failures)

    def run(self, login_only=False):
        about = self.api('GET', '/about', params={'fields': 'user(emailAddress),storageQuota'}).json()
        account = about['user']['emailAddress']
        if account.lower() != self.plan['account'].lower():
            raise RuntimeError('Tài khoản Drive khác tài khoản đã chốt trong kế hoạch.')
        quota = about.get('storageQuota', {})
        if 'limit' in quota:
            remaining = int(quota['limit']) - int(quota.get('usage', 0))
            print(f'Drive đang còn {remaining / 1e9:.2f} GB trống.', flush=True)
        parent = self.metadata(self.plan['parent_id'])
        if not parent or parent.get('trashed') or parent['mimeType'] != FOLDER:
            raise RuntimeError('Chưa truy cập được thư mục đích Drive.')
        if login_only:
            print('Đã kiểm đúng tài khoản và quyền đọc thư mục đích.', flush=True)
            return
        root_id = self.folder('.', self.plan['parent_id'], self.plan['folder_name'])
        for row in self.plan['files']:
            parent = root_id
            relative_parent = Path(row['path']).parent
            current = Path()
            for part in relative_parent.parts:
                current /= part
                parent = self.folder(current.as_posix(), parent, part)
            self.send_file(row, parent)
        self.event('BATCH_VERIFIED', files=len(self.plan['files']), bytes=self.plan['bytes'])
        atomic_json(self.evidence / 'ACCEPTANCE.json', dict(status='REMOTE_CHECKSUM_VERIFIED',
            files=len(self.plan['files']), bytes=self.plan['bytes'], folder_id=root_id,
            completed_at=now(), local_files_deleted=0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Lập inventory local, chưa kết nối Drive')
    parser.add_argument('--login-only', action='store_true', help='Đăng nhập và kiểm tài khoản/đích')
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--parent-id', default='1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7')
    parser.add_argument('--account', default='honguyenminhsang2005@gmail.com')
    parser.add_argument('--chunk-mib', type=int, default=32)
    args = parser.parse_args()
    if not 1 <= args.chunk_mib <= 64:
        parser.error('chunk-mib từ 1 đến 64.')
    plan = build_plan(args.source, args.parent_id, args.account)
    plan_path = EVIDENCE / 'UPLOAD_PLAN.json'
    if plan_path.exists() and read_json(plan_path) != plan:
        raise RuntimeError('Kế hoạch đã có và khác inventory hiện tại, cần rà thay đổi trước.')
    atomic_json(plan_path, plan)
    print(f"Kế hoạch {len(plan['files'])} file, {plan['bytes']/1e9:.2f} GB.", flush=True)
    if args.prepare:
        return
    client_path = PRIVATE / 'client_secret.json'
    token_path = PRIVATE / 'token.json'
    if not token_path.exists() and not client_path.exists():
        raise RuntimeError(f'Cần OAuth Desktop client tại {client_path}')
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    PRIVATE.mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':
        PRIVATE.chmod(0o700)
    with single_writer(PRIVATE / 'upload.lock'):
        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(token_path), [SCOPE])
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), [SCOPE])
            credentials = flow.run_local_server(port=0, login_hint=args.account,
                access_type='offline', prompt='consent', timeout_seconds=300)
            atomic_json(token_path, json.loads(credentials.to_json()))
        try:
            with AuthorizedSession(credentials) as session:
                Uploader(session, plan, PRIVATE / 'state.json', EVIDENCE,
                         chunk_bytes=args.chunk_mib * 1024**2).run(login_only=args.login_only)
        finally:
            atomic_json(token_path, json.loads(credentials.to_json()))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Đã dừng. Chạy lại cùng lệnh để tiếp tục phiên đã lưu.', flush=True)
        raise SystemExit(130)
    except RuntimeError as error:
        print(str(error), flush=True)
        raise SystemExit(1)
    except Exception as error:
        # Ngoại lệ HTTP/OAuth có thể chứa URL phiên hoặc token, chỉ ghi loại lỗi.
        print(f'Đã dừng do {type(error).__name__}; giữ trạng thái để tiếp tục/kiểm tra.', flush=True)
        raise SystemExit(1)
