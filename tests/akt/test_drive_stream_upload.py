"""Transport Drive stream với session giả lập, không kết nối mạng."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import requests

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts/akt'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('stream_upload_test', SCRIPTS/'drive_stream_upload.py')
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


def response(status, body=None, **headers):
    result = requests.Response()
    result.status_code = status
    result.headers.update(headers)
    result._content = json.dumps(body or {}).encode()
    return result


class Drive:
    def __init__(self):
        self.data = bytearray()
        self.sessions = 0
        self.mode = None
        self.failed = False
        self.account = upload.ACCOUNT
        self.bad_sha = False
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if url.endswith('/about'):
            return response(200, {'user': {'emailAddress': self.account}})
        if url.endswith('/files/folder'):
            return response(200, {'id': 'folder', 'mimeType': upload.FOLDER,
                                 'trashed': False, 'capabilities': {'canAddChildren': True}})
        if url.endswith('/generateIds'):
            return response(200, {'ids': ['file']})
        if method == 'POST':
            self.sessions += 1
            self.name = kwargs['json']['name']
            self.total = int(kwargs['headers']['X-Upload-Content-Length'])
            self.data.clear()
            return response(200, Location=upload.UPLOAD+'?upload_id=PRIVATE'+str(self.sessions))
        if method == 'GET':
            digest = hashlib.sha256(self.data).hexdigest()
            return response(200, {'id': 'file', 'name': self.name,
                                 'size': str(len(self.data)), 'sha256Checksum': '0'*64 if self.bad_sha else digest,
                                 'parents': ['folder'], 'trashed': False})
        content_range = kwargs['headers']['Content-Range']
        if content_range.startswith('bytes */'):
            return self.progress()
        start = int(content_range.split()[1].split('-')[0])
        assert start == len(self.data)
        chunk = kwargs['data']
        if not self.failed and self.mode in ('partial', 'disconnect', 'crash', 'expire'):
            self.failed = True
            if self.mode == 'expire':
                return response(410)
            amount = len(chunk)//2 if self.mode == 'partial' else len(chunk)
            self.data.extend(chunk[:amount])
            if self.mode == 'partial':
                return self.progress()
            if self.mode == 'crash':
                raise KeyboardInterrupt()
            raise requests.ConnectionError('secret URI must not appear in raised error')
        self.data.extend(chunk)
        return self.progress()

    def progress(self):
        if len(self.data) == self.total:
            return response(200)
        return response(308, **({'Range': f'bytes=0-{len(self.data)-1}'} if self.data else {}))


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(upload, 'PRIVATE', tmp_path)
    content = b'example-stream-' * 40000
    plan = dict(folder_id='folder', name='NUMERIC.zip', total_bytes=len(content), source_plan_sha256='a'*64)
    state = tmp_path/'private/state.json'
    factory_calls, closed = [], []

    def factory():
        factory_calls.append(True)
        try:
            for offset in range(0, len(content), 70001):
                yield content[offset:offset+70001]
        finally:
            closed.append(True)

    def run(drive, **kwargs):
        return upload.upload_stream(drive, plan, factory, state, chunk_bytes=256*1024,
                                    sleep=lambda _: None, **kwargs)
    return content, plan, state, factory_calls, closed, run


@pytest.mark.parametrize('mode', [None, 'partial', 'disconnect', 'expire'])
def test_stream_resume_checksum_and_no_binary_copy(setup, mode):
    content, plan, state, calls, closed, run = setup
    drive = Drive()
    drive.mode = mode
    receipt = run(drive)
    assert receipt['sha256'] == hashlib.sha256(content).hexdigest()
    assert receipt['bytes'] == len(content) and bytes(drive.data) == content
    assert len(calls) == len(closed)
    assert len(calls) == (1 if mode is None else 2)
    assert 'PRIVATE' not in json.dumps(receipt)
    assert {path.suffix for path in state.parent.iterdir()} == {'.json', '.lock'}
    before = len(calls)
    assert run(drive)['sha256'] == receipt['sha256']
    assert len(calls) == before  # completed state verifies metadata without regeneration


def test_process_restart_regenerates_prefix_and_hashes_whole_stream(setup):
    content, plan, state, calls, closed, run = setup
    drive = Drive()
    drive.mode = 'crash'
    with pytest.raises(KeyboardInterrupt):
        run(drive)
    assert len(drive.data) == 256*1024
    result = run(drive)
    assert result['sha256'] == hashlib.sha256(content).hexdigest()
    assert len(calls) == len(closed) == 2
    assert drive.sessions == 1


def test_source_plan_change_rejected_before_network(setup):
    _, plan, state, _, _, run = setup
    drive = Drive()
    run(drive)
    plan['source_plan_sha256'] = 'b'*64
    before = len(drive.calls)
    with pytest.raises(ValueError, match='State khác'):
        run(drive)
    assert len(drive.calls) == before


@pytest.mark.parametrize('change', ['account', 'sha'])
def test_wrong_account_or_final_sha_rejected(setup, change):
    *_, run = setup
    drive = Drive()
    if change == 'account':
        drive.account = 'someone@example.com'
    else:
        drive.bad_sha = True
    with pytest.raises(RuntimeError):
        run(drive)


def test_size_cap_rejected_before_factory_and_network(setup):
    _, plan, _, calls, _, run = setup
    plan['total_bytes'] = upload.MAX_BYTES+1
    drive = Drive()
    with pytest.raises(ValueError, match='giới hạn'):
        run(drive)
    assert not calls and not drive.calls


@pytest.mark.parametrize('delta', [-1, 1])
def test_factory_exact_size_required(setup, delta):
    _, plan, _, _, _, run = setup
    plan['total_bytes'] += delta
    with pytest.raises(ValueError, match='byte'):
        run(Drive())


def test_uri_only_in_private_state(setup, tmp_path):
    _, plan, _, _, _, _ = setup
    with pytest.raises(ValueError, match='private'):
        upload.upload_stream(Drive(), plan, lambda: iter(()), tmp_path.parent/'public.json')


def test_retry_cap_and_stream_closed(setup):
    _, _, state, calls, closed, run = setup
    drive = Drive()
    original = drive.request
    failures = []

    def failing_chunk(method, url, **kwargs):
        if method == 'PUT' and kwargs['data']:
            failures.append(True)
            raise requests.ConnectionError('PRIVATE_SESSION_URI')
        return original(method, url, **kwargs)

    drive.request = failing_chunk
    with pytest.raises(RuntimeError, match='hai lần') as caught:
        run(drive)
    assert len(failures) == len(calls) == len(closed) == 3
    assert caught.value.__suppress_context__
    assert 'complete' not in json.loads(state.read_text())


def test_complete_server_on_restart_still_hashes_all_source(setup):
    content, _, _, calls, closed, run = setup
    drive = Drive()
    drive.mode = 'crash'
    # Commit the final chunk before the client receives its completion response.
    original = drive.request

    def last_chunk_crash(method, url, **kwargs):
        if method == 'PUT' and kwargs['data'] and len(drive.data)+len(kwargs['data']) == len(content):
            drive.mode = 'crash'
            drive.failed = False
        else:
            drive.mode = None
        return original(method, url, **kwargs)

    drive.request = last_chunk_crash
    with pytest.raises(KeyboardInterrupt):
        run(drive)
    assert bytes(drive.data) == content
    assert run(drive)['sha256'] == hashlib.sha256(content).hexdigest()
    assert len(calls) == len(closed) == 2


def test_expired_session_after_completed_commit_reuses_existing_file(setup):
    content, _, _, calls, closed, run = setup
    drive = Drive()
    drive.mode = 'crash'
    with pytest.raises(KeyboardInterrupt):
        run(drive)
    drive.data[:] = content
    original = drive.request

    def expired_query(method, url, **kwargs):
        if method == 'PUT' and not kwargs['data']:
            return response(410)
        return original(method, url, **kwargs)

    drive.request = expired_query
    assert run(drive)['sha256'] == hashlib.sha256(content).hexdigest()
    assert drive.sessions == 1 and len(calls) == len(closed) == 2
