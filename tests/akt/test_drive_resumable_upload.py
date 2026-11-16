"""Kiểm uploader bằng Drive giả lập, hoàn toàn offline và dữ liệu tổng hợp."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import requests

MODULE = Path(__file__).resolve().parents[2] / 'scripts/akt/drive_resumable_upload.py'
spec = importlib.util.spec_from_file_location('drive_upload', MODULE)
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


def response(status, body=None, **headers):
    result = requests.Response()
    result.status_code = status
    result.headers.update(headers)
    result._content = json.dumps(body or {}).encode()
    return result


class Drive:
    def __init__(self, content, name='example.zip'):
        self.content = content
        self.name = name
        self.received = bytearray()
        self.sessions = 0
        self.calls = []
        self.fail_after_commit = False
        self.crash_after_commit = False
        self.always_fail = False
        self.expire_once = False
        self.bad_checksum = False

    def meta(self):
        return dict(id='file1', name=self.name, size=str(len(self.content)), parents=['parent'],
                    md5Checksum='bad' if self.bad_checksum else upload.hashlib.md5(self.content).hexdigest(),
                    sha256Checksum=upload.hashlib.sha256(self.content).hexdigest())

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if url == upload.API + '/files/generateIds':
            return response(200, {'ids': ['file1']})
        if url == upload.API + '/files':
            return response(200, {'files': []})
        if method == 'GET' and url == upload.API + '/files/file1':
            return response(200, self.meta()) if self.received == self.content else response(404)
        if method == 'POST' and url == upload.UPLOAD:
            self.sessions += 1
            return response(200, Location=upload.UPLOAD + '?upload_id=test')
        assert method == 'PUT'
        if self.expire_once:
            self.expire_once = False
            self.received.clear()
            return response(404)
        data = kwargs['data']
        if data:
            start = int(kwargs['headers']['Content-Range'].split()[1].split('-')[0])
            assert start == len(self.received)
            if self.always_fail:
                raise requests.ConnectionError('fake offline')
            self.received.extend(data)
            if self.crash_after_commit:
                self.crash_after_commit = False
                raise KeyboardInterrupt
            if self.fail_after_commit:
                self.fail_after_commit = False
                raise requests.ConnectionError('response lost after server commit')
        if self.received == self.content:
            return response(200, self.meta())
        return response(308, **({'Range': f'bytes=0-{len(self.received)-1}'} if self.received else {}))


@pytest.fixture
def case(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    content = bytes(range(256)) * 2305
    path = source / 'example.zip'
    path.write_bytes(content)
    row = dict(path=path.name, **upload.hashes(path))
    plan = dict(source=str(source), files=[row])
    drive = Drive(content)

    def make():
        return upload.Uploader(drive, plan, tmp_path / 'private/state.json', tmp_path / 'evidence',
                               chunk_bytes=256*1024, retries=2, sleep=lambda _: None)
    return dict(path=path, row=row, drive=drive, make=make, root=tmp_path)


def test_full_upload_and_remote_receipt(case):
    worker = case['make']()
    worker.send_file(case['row'], 'parent')
    assert case['drive'].received == case['drive'].content
    state = upload.read_json(worker.state_path)
    assert state['files']['example.zip']['complete']
    assert 'session_url' not in state['files']['example.zip']
    receipts = upload.read_json(worker.evidence / 'RECEIPTS.json')
    assert receipts[0]['local_sha256'] == case['row']['sha256']
    assert all(not call[2].get('allow_redirects', False) for call in case['drive'].calls)


def test_recover_network_loss_after_server_received_chunk(case):
    case['drive'].fail_after_commit = True
    case['make']().send_file(case['row'], 'parent')
    chunks = [c for c in case['drive'].calls if c[0] == 'PUT' and c[2]['data']]
    assert len(chunks) == 3
    assert chunks[1][2]['headers']['Content-Range'].startswith('bytes 262144-')


def test_process_restart_recovers_server_offset_not_stale_local_offset(case):
    case['drive'].crash_after_commit = True
    first = case['make']()
    with pytest.raises(KeyboardInterrupt):
        first.send_file(case['row'], 'parent')
    state = upload.read_json(first.state_path)
    assert 'session_url' in state['files']['example.zip']
    assert len(case['drive'].received) == 262144
    case['make']().send_file(case['row'], 'parent')
    assert case['drive'].sessions == 1
    assert case['drive'].received == case['drive'].content


def test_restart_skips_completed_remote_file(case):
    case['make']().send_file(case['row'], 'parent')
    before = len([c for c in case['drive'].calls if c[0] in ('POST', 'PUT')])
    case['make']().send_file(case['row'], 'parent')
    assert len([c for c in case['drive'].calls if c[0] in ('POST', 'PUT')]) == before


def test_browser_completed_file_reused_after_checksum_match(case):
    drive = case['drive']
    drive.received.extend(drive.content)
    original = drive.request

    def request(method, url, **kwargs):
        if url == upload.API + '/files':
            return response(200, {'files': [drive.meta()]})
        return original(method, url, **kwargs)
    drive.request = request
    case['make']().send_file(case['row'], 'parent')
    assert drive.sessions == 0


def test_expired_session_restarts_same_file_id(case):
    worker = case['make']()
    worker.state['files']['example.zip'] = dict(remote_id='file1', session_url=upload.UPLOAD+'?upload_id=expired')
    worker.save()
    case['drive'].expire_once = True
    case['make']().send_file(case['row'], 'parent')
    assert case['drive'].sessions == 1
    assert case['drive'].received == case['drive'].content


def test_bad_remote_checksum_never_marks_complete(case):
    case['drive'].bad_checksum = True
    worker = case['make']()
    with pytest.raises(RuntimeError, match='Checksum'):
        worker.send_file(case['row'], 'parent')
    assert not worker.state['files']['example.zip'].get('complete')


def test_changed_source_rejected_before_network(case):
    case['path'].write_bytes(b'changed')
    with pytest.raises(RuntimeError, match='Nguồn'):
        case['make']().send_file(case['row'], 'parent')
    assert not case['drive'].calls


def test_source_hash_mismatch_rejected_before_network(case):
    case['row']['sha256'] = '0' * 64
    with pytest.raises(RuntimeError, match='SHA nguồn'):
        case['make']().send_file(case['row'], 'parent')
    assert not case['drive'].calls


def test_account_mismatch_stops_before_creating_remote_files(case):
    worker = case['make']()
    worker.plan['account'] = 'expected@example.com'
    worker.api = lambda *a, **k: response(200, {'user': {'emailAddress': 'other@example.com'}})
    with pytest.raises(RuntimeError, match='Tài khoản'):
        worker.run()
    assert not case['drive'].calls


def test_login_only_checks_identity_and_parent_without_upload(case):
    worker = case['make']()
    worker.plan.update(account='expected@example.com', parent_id='parent')
    worker.api = lambda *a, **k: response(200, {'user': {'emailAddress': 'expected@example.com'}})
    worker.metadata = lambda _: dict(id='parent', mimeType=upload.FOLDER)
    worker.run(login_only=True)
    assert not case['drive'].calls
    assert not worker.state_path.exists()


def test_api_permission_error_stops_with_status_only(case):
    case['drive'].request = lambda *a, **k: response(403)
    with pytest.raises(RuntimeError, match='HTTP 403'):
        case['make']().api('GET', '/about')


def test_api_retries_rate_limit_without_failing_state(case):
    calls = []
    def request(*args, **kwargs):
        calls.append(args)
        return response(429 if len(calls) == 1 else 200)
    case['drive'].request = request
    assert case['make']().api('GET', '/about').status_code == 200
    assert len(calls) == 2


def test_lost_final_response_recovers_complete_file(case):
    case['drive'].received.extend(case['drive'].content[:524288])
    worker = case['make']()
    worker.state['files']['example.zip'] = dict(remote_id='file1', session_url=upload.UPLOAD+'?upload_id=test')
    worker.save()
    case['drive'].fail_after_commit = True
    case['make']().send_file(case['row'], 'parent')
    assert upload.read_json(worker.state_path)['files']['example.zip']['complete']


def test_changed_plan_rejected(case):
    worker = case['make']()
    worker.save()
    worker.plan['source'] += '-changed'
    with pytest.raises(RuntimeError, match='inventory'):
        upload.Uploader(case['drive'], worker.plan, worker.state_path, worker.evidence)


def test_bounded_retry_preserves_private_session(case):
    case['drive'].always_fail = True
    worker = case['make']()
    with pytest.raises(RuntimeError, match='Hết số lần'):
        worker.send_file(case['row'], 'parent')
    assert 'session_url' in upload.read_json(worker.state_path)['files']['example.zip']
    assert not (worker.evidence / 'RECEIPTS.json').exists()


@pytest.mark.parametrize('status,header,total,expected', [
    (308, None, 100, 0), (308, 'bytes=0-41', 100, 42),
    (308, 'bytes=0-34359738367', 34359738369, 34359738368), (200, None, 100, 100),
])
def test_server_offsets_including_files_over_32gb(status, header, total, expected):
    headers = {'Range': header} if header else {}
    assert upload.checked_offset(response(status, **headers), total) == expected


@pytest.mark.parametrize('header', ['bytes=1-9', 'bytes=0-101', 'bad'])
def test_invalid_range_rejected(header):
    with pytest.raises(RuntimeError):
        upload.checked_offset(response(308, Range=header), 100)


@pytest.mark.parametrize('url', ['http://www.googleapis.com/upload/drive/v3/files',
    'https://attacker.invalid/upload/drive/v3/files', 'https://www.googleapis.com.evil/upload/drive/v3/files'])
def test_private_session_url_restricted_to_google(url):
    with pytest.raises(RuntimeError):
        upload.safe_session_url(url)


def test_single_writer_prevents_parallel_state_updates(tmp_path):
    with upload.single_writer(tmp_path / 'lock'):
        with pytest.raises(RuntimeError, match='uploader khác'):
            with upload.single_writer(tmp_path / 'lock'):
                pytest.fail('Must reject another writer')


def test_empty_source_rejected(tmp_path):
    (tmp_path / 'MANIFEST.json').write_text('{"files": []}')
    (tmp_path / 'empty').touch()
    with pytest.raises(RuntimeError, match='File rỗng'):
        upload.build_plan(tmp_path, 'parent', 'example@example.com')


def test_prepare_only_keeps_historical_manifest_unmodified(tmp_path):
    (tmp_path / 'archive.zip').write_bytes(b'archive')
    row = dict(upload_path='archive.zip', bytes=7, sha256=upload.hashes(tmp_path/'archive.zip')['sha256'])
    manifest = json.dumps(dict(files=[row])).encode()
    (tmp_path / 'MANIFEST.json').write_bytes(manifest)
    plan = upload.build_plan(tmp_path, 'parent', 'example@example.com')
    assert len(plan['files']) == 2
    assert (tmp_path / 'MANIFEST.json').read_bytes() == manifest


def test_login_only_uses_saved_plan_after_archives_removed(tmp_path, monkeypatch):
    evidence = tmp_path / 'evidence'
    source = tmp_path / 'archived-source'
    plan = dict(source=str(source.resolve()), parent_id='parent', account='sang@example.com',
                files=[dict(path='removed.zip')], bytes=1024)
    upload.atomic_json(evidence / 'UPLOAD_PLAN.json', plan)
    before = (evidence / 'UPLOAD_PLAN.json').read_bytes()
    monkeypatch.setattr(upload, 'EVIDENCE', evidence)
    monkeypatch.setattr(upload, 'PRIVATE', tmp_path / 'private')
    monkeypatch.setattr(upload, 'build_plan', lambda *a: pytest.fail('Must reuse saved plan for login'))
    monkeypatch.setattr(sys, 'argv', ['uploader', '--login-only', '--source', str(source),
                                     '--parent-id', 'parent', '--account', 'sang@example.com'])
    with pytest.raises(RuntimeError, match='OAuth Desktop client'):
        upload.main()
    assert (evidence / 'UPLOAD_PLAN.json').read_bytes() == before
