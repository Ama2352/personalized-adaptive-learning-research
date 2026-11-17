"""Chuyển stream xác định sang Drive, không tạo bản binary trên đĩa local."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import time

import requests
from google.auth.exceptions import TransportError

try:
    from .drive_resumable_upload import (
        API, FIELDS, FOLDER, UPLOAD, atomic_json, checked_offset, now,
        read_json, safe_session_url, single_writer,
    )
except ImportError:
    from drive_resumable_upload import (
        API, FIELDS, FOLDER, UPLOAD, atomic_json, checked_offset, now,
        read_json, safe_session_url, single_writer,
    )

ACCOUNT = 'honguyenminhsang2005@gmail.com'
MAX_BYTES = 256 * 1024**2
MAX_BLOCK = 8 * 1024**2
RETRIES = 2
PRIVATE = Path(__file__).resolve().parents[2] / 'artifacts/akt/private'


def _plan(plan, maximum):
    if set(plan) != {'folder_id', 'name', 'total_bytes', 'source_plan_sha256'}:
        raise ValueError('Plan stream phải có đúng bốn trường đã chốt.')
    if (type(maximum) is not int or not 0 < maximum <= MAX_BYTES
            or type(plan['total_bytes']) is not int
            or not 0 < plan['total_bytes'] <= maximum):
        raise ValueError('Stream vượt giới hạn byte được duyệt.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', plan['folder_id']):
        raise ValueError('Folder Drive không hợp lệ.')
    if (not isinstance(plan['name'], str) or not plan['name']
            or len(plan['name']) > 200
            or any(char in plan['name'] for char in '/\\\r\n\0')):
        raise ValueError('Tên archive không hợp lệ.')
    if not re.fullmatch(r'[0-9a-f]{64}', plan['source_plan_sha256']):
        raise ValueError('Thiếu SHA kế hoạch nguồn.')


class _Upload:
    def __init__(self, session, plan, factory, path, chunk_bytes, sleep):
        self.session, self.plan, self.factory = session, plan, factory
        self.path, self.chunk_bytes, self.sleep = path, chunk_bytes, sleep
        self.failures = 0
        self.state = read_json(path) if path.exists() else {
            'kind': 'DRIVE_STREAM_UPLOAD_V1', 'plan': plan, 'new_sessions': 0,
        }
        if self.state.get('kind') != 'DRIVE_STREAM_UPLOAD_V1' or self.state.get('plan') != plan:
            raise ValueError('State khác kế hoạch nguồn, không tiếp tục phiên cũ.')

    def save(self):
        atomic_json(self.path, self.state)

    def retry(self):
        self.failures += 1
        if self.failures > RETRIES:
            raise RuntimeError('Hết hai lần thử lại; state riêng đã giữ để tiếp tục.') from None
        self.sleep(self.failures)

    def request(self, method, url, **kwargs):
        while True:
            try:
                response = self.session.request(
                    method, url, timeout=(20, 180), allow_redirects=False, **kwargs,
                )
            except (requests.RequestException, TransportError):
                self.retry()
                continue
            if response.status_code == 429 or response.status_code >= 500:
                self.retry()
                continue
            return response

    def metadata(self):
        response = self.request('GET', API+'/files/'+self.state['file_id'], params={'fields': FIELDS})
        if response.status_code != 200:
            raise RuntimeError('Chưa đọc được metadata file Drive.')
        return response.json()

    def verify(self, metadata, digest):
        plan = self.plan
        if (metadata.get('id') != self.state['file_id']
                or metadata.get('name') != plan['name']
                or metadata.get('trashed') is not False
                or metadata.get('parents') != [plan['folder_id']]
                or metadata.get('size') != str(plan['total_bytes'])
                or metadata.get('sha256Checksum') != digest):
            raise RuntimeError('Metadata/SHA Drive không khớp toàn bộ stream.')
        receipt = dict(
            status='REMOTE_STREAM_SHA256_VERIFIED', file_id=metadata['id'],
            name=plan['name'], folder_id=plan['folder_id'],
            bytes=plan['total_bytes'], sha256=digest,
            source_plan_sha256=plan['source_plan_sha256'], verified_at=now(),
        )
        self.state.update(complete=receipt)
        self.save()
        return receipt

    def new_session(self):
        if self.state['new_sessions'] >= 2:
            raise RuntimeError('Đã dùng hết một phiên upload thay thế.')
        # Cố định file ID để tạo lại phiên không tạo bản file trùng.
        if 'file_id' not in self.state:
            response = self.request('GET', API+'/files/generateIds', params={'count': 1, 'space': 'drive'})
            if response.status_code != 200:
                raise RuntimeError('Không cấp được file ID Drive.')
            self.state['file_id'] = response.json()['ids'][0]
            self.save()
        response = self.request(
            'POST', UPLOAD, params={'uploadType': 'resumable', 'fields': FIELDS},
            headers={'X-Upload-Content-Type': 'application/zip',
                     'X-Upload-Content-Length': str(self.plan['total_bytes'])},
            json={'id': self.state['file_id'], 'name': self.plan['name'],
                  'parents': [self.plan['folder_id']]},
        )
        if response.status_code not in (200, 201):
            raise RuntimeError('Không mở được phiên upload Drive.')
        self.state.update(session_uri=safe_session_url(response.headers['Location']), offset=0,
                          new_sessions=self.state['new_sessions']+1)
        self.save()

    def offset(self):
        response = self.request(
            'PUT', safe_session_url(self.state['session_uri']), data=b'',
            headers={'Content-Length': '0', 'Content-Range': f"bytes */{self.plan['total_bytes']}"},
        )
        if response.status_code in (404, 410):
            # Mất phản hồi cuối rồi phiên hết hạn vẫn có thể đã tạo file hoàn chỉnh.
            metadata = self.request('GET', API+'/files/'+self.state['file_id'], params={'fields': FIELDS})
            if metadata.status_code == 200:
                if metadata.json().get('size') == str(self.plan['total_bytes']):
                    return self.plan['total_bytes']
                raise RuntimeError('File ID đã tồn tại nhưng chưa khớp kích thước nguồn.')
            if metadata.status_code != 404:
                raise RuntimeError('Chưa kiểm được file sau khi phiên Drive hết hạn.')
            self.new_session()
            return 0
        return checked_offset(response, self.plan['total_bytes'])

    def transfer(self, committed):
        total = self.plan['total_bytes']
        digest, consumed, pending = hashlib.sha256(), 0, bytearray()
        iterator = iter(self.factory())
        try:
            for block in iterator:
                if not isinstance(block, bytes) or not 0 < len(block) <= MAX_BLOCK:
                    raise ValueError('Factory phải trả block bytes không rỗng tối đa 8 MiB.')
                start = consumed
                consumed += len(block)
                if consumed > total:
                    raise ValueError('Factory sinh nhiều byte hơn kế hoạch.')
                digest.update(block)
                if consumed > committed:
                    pending.extend(block[max(0, committed-start):])
                while len(pending) >= self.chunk_bytes or (consumed == total and pending):
                    chunk = bytes(pending[:self.chunk_bytes])
                    end = committed+len(chunk)
                    try:
                        response = self.session.request(
                            'PUT', safe_session_url(self.state['session_uri']), data=chunk,
                            headers={'Content-Length': str(len(chunk)),
                                     'Content-Range': f'bytes {committed}-{end-1}/{total}'},
                            timeout=(20, 180), allow_redirects=False,
                        )
                    except (requests.RequestException, TransportError):
                        self.retry()
                        return None
                    if response.status_code == 429 or response.status_code >= 500:
                        self.retry()
                        return None
                    if response.status_code in (404, 410):
                        self.new_session()
                        return None
                    received = checked_offset(response, total)
                    if not committed <= received <= end:
                        raise RuntimeError('Drive trả offset ngoài chunk đã gửi.')
                    self.state['offset'] = received
                    self.save()
                    if received != end:
                        self.retry()
                        return None
                    del pending[:len(chunk)]
                    committed = received
            if consumed != total or pending or committed != total:
                raise ValueError('Factory kết thúc thiếu byte so với kế hoạch.')
            return digest.hexdigest()
        finally:
            close = getattr(iterator, 'close', None)
            if close:
                close()

    def run(self):
        about = self.request('GET', API+'/about', params={'fields': 'user(emailAddress)'})
        if about.status_code != 200 or about.json().get('user', {}).get('emailAddress', '').lower() != ACCOUNT:
            raise RuntimeError('Cần đúng tài khoản Drive cá nhân Sang đã duyệt.')
        folder = self.request('GET', API+'/files/'+self.plan['folder_id'],
                              params={'fields': 'id,mimeType,trashed,capabilities(canAddChildren)'})
        metadata = folder.json()
        if (folder.status_code != 200 or metadata.get('mimeType') != FOLDER
                or metadata.get('trashed') is not False
                or metadata.get('capabilities', {}).get('canAddChildren') is not True):
            raise RuntimeError('Chưa có quyền ghi vào đúng thư mục Drive.')
        if 'complete' in self.state:
            return self.verify(self.metadata(), self.state['complete']['sha256'])
        if 'session_uri' not in self.state:
            self.new_session()
        while True:
            committed = self.offset()
            digest = self.transfer(committed)
            if digest is not None:
                return self.verify(self.metadata(), digest)


def upload_stream(session, plan, factory, private_state: Path, *,
                  chunk_bytes=8 * 1024**2, max_total_bytes=MAX_BYTES, sleep=time.sleep):
    """Upload stream tái tạo được; state chứa URI nhạy cảm chỉ giữ vùng private."""
    _plan(plan, max_total_bytes)
    if type(chunk_bytes) is not int or not 0 < chunk_bytes <= 8 * 1024**2 or chunk_bytes % (256 * 1024):
        raise ValueError('Chunk phải là bội 256 KiB, tối đa 8 MiB.')
    private_state = Path(private_state)
    if not private_state.resolve().is_relative_to(PRIVATE.resolve()):
        raise ValueError('State upload phải nằm trong artifacts/akt/private.')
    with single_writer(private_state.with_suffix(private_state.suffix+'.lock')):
        return _Upload(session, dict(plan), factory, private_state, chunk_bytes, sleep).run()
