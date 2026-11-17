"""Drive giả và ZIP tổng hợp nhỏ, không gọi Modal/Drive thật."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import zipfile

import pytest
import requests

SPEC = importlib.util.spec_from_file_location('input_stage',
    Path(__file__).resolve().parents[2]/'scripts/akt/modal_calibration_input_stage.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def sha(value):
    return hashlib.sha256(value).hexdigest()


class Response:
    def __init__(self, data=None, content=b'', status=200, headers=None, crash=False):
        self.data, self.content, self.status_code, self.headers = data, content, status, headers or {}
        self.crash = crash
    def json(self):
        return self.data
    def close(self):
        pass
    def iter_content(self, chunk_size):
        yield self.content[:128]
        if self.crash:
            raise requests.ConnectionError('synthetic interrupted network')
        yield self.content[128:]


class Drive:
    def __init__(self, payload):
        self.payload = payload
        self.account = module.ACCOUNT
        self.crash = True
        self.ranges = []
        self.wrong_range = False
        self.wrong_folder_parent = False
        self.metadata_calls = 0
    def request(self, method, url, **kwargs):
        assert method == 'GET' and kwargs['allow_redirects'] is False
        if url.endswith('/about'):
            self.metadata_calls += 1
            return Response(dict(user=dict(emailAddress=self.account)))
        if url.endswith('/files/'+module.FILE_PARENT):
            self.metadata_calls += 1
            return Response(dict(id=module.FILE_PARENT, parents=['wrong' if self.wrong_folder_parent else module.PARENT],
                mimeType='application/vnd.google-apps.folder'))
        if kwargs['params'].get('alt') != 'media':
            self.metadata_calls += 1
            return Response(dict(id='fixture', size=len(self.payload), sha256Checksum=sha(self.payload), parents=[module.FILE_PARENT]))
        offset = int(kwargs['headers']['Range'][6:-1])
        self.ranges.append(offset)
        crash, self.crash = self.crash, False
        header = dict({'Content-Range':f'bytes {offset}-{len(self.payload)-1}/{len(self.payload)}'})
        if self.wrong_range:
            header['Content-Range'] = 'bytes 0-1/2'
        return Response(content=self.payload[offset:], status=206 if offset else 200, headers=header, crash=crash)


def test_download_resumes_committed_http_range(tmp_path):
    drive = Drive(bytes(range(256))*4)
    commits = []
    result = module.download_pinned_input(drive, tmp_path, volume_commit=lambda: commits.append(True),
        file_id='fixture', expected_sha=sha(drive.payload), expected_bytes=len(drive.payload), sleep=lambda _:None)
    assert drive.ranges == [0, 128]
    assert drive.metadata_calls == 3
    assert result.read_bytes() == drive.payload and commits
    assert not (tmp_path/'INPUT.zip.part').exists()


def test_wrong_account_stops_before_media(tmp_path):
    drive = Drive(b'fixture')
    drive.account = 'other@example.com'
    with pytest.raises(ValueError, match='account'):
        module.download_pinned_input(drive, tmp_path, volume_commit=lambda:None,
            file_id='fixture', expected_sha=sha(drive.payload), expected_bytes=len(drive.payload))
    assert not drive.ranges


def test_wrong_range_stops_without_overwriting_partial(tmp_path):
    drive = Drive(b'x'*256)
    drive.crash = False
    drive.wrong_range = True
    (tmp_path/'INPUT.zip.part').write_bytes(b'x'*128)
    with pytest.raises(ValueError, match='Range'):
        module.download_pinned_input(drive, tmp_path, volume_commit=lambda:None,
            file_id='fixture', expected_sha=sha(drive.payload), expected_bytes=len(drive.payload))
    assert (tmp_path/'INPUT.zip.part').stat().st_size == 128


def test_wrong_folder_lineage_stops_before_media(tmp_path):
    drive = Drive(b'fixture')
    drive.wrong_folder_parent = True
    with pytest.raises(ValueError, match='lineage'):
        module.download_pinned_input(drive, tmp_path, volume_commit=lambda:None,
            file_id='fixture', expected_sha=sha(drive.payload), expected_bytes=len(drive.payload))
    assert drive.metadata_calls == 3 and not drive.ranges


def archive(tmp_path, *, member='src/config.py', incorrect_sha=False, extra=False, symlink=False):
    payload = b'# fixture\n'
    plan = dict(schema='junyi-calibration-cloud-inputs-v1', bytes=len(payload),
        files=[dict(path=member, bytes=len(payload), sha256='0'*64 if incorrect_sha else sha(payload))])
    raw = json.dumps(plan).encode()
    path = tmp_path/'input.zip'
    with zipfile.ZipFile(path, 'w') as output:
        info = zipfile.ZipInfo(member)
        if symlink:
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK|0o777)<<16
        output.writestr(info, payload)
        output.writestr('CLOUD_INPUT_PLAN.json', raw)
        if extra:
            output.writestr('unlisted.json', b'{}')
    return path, dict(expected_zip_sha=module.sha256(path), expected_plan_sha=sha(raw))


def test_exact_archive_verified_then_idempotent(tmp_path):
    path, pins = archive(tmp_path)
    target = tmp_path/'source'
    plan = module.extract_verified_input(path, target, **pins)
    assert (target/'src/config.py').read_bytes() == b'# fixture\n'
    assert module.extract_verified_input(path, target, **pins) == plan


@pytest.mark.parametrize('kwargs', [dict(member='../escape'), dict(member='C:/escape'),
    dict(member='private/token.json'), dict(incorrect_sha=True), dict(extra=True), dict(symlink=True)])
def test_bad_archive_never_publishes_source(tmp_path, kwargs):
    path, pins = archive(tmp_path, **kwargs)
    with pytest.raises(ValueError):
        module.extract_verified_input(path, tmp_path/'source', **pins)
    assert not (tmp_path/'source').exists()


def test_plan_or_zip_pin_mismatch_rejected(tmp_path):
    path, pins = archive(tmp_path)
    for field in ('expected_zip_sha', 'expected_plan_sha'):
        bad = dict(pins, **{field:'0'*64})
        with pytest.raises(ValueError, match='pin'):
            module.extract_verified_input(path, tmp_path/'source', **bad)


def test_existing_staged_extra_file_rejected(tmp_path):
    path, pins = archive(tmp_path)
    target = tmp_path/'source'
    module.extract_verified_input(path, target, **pins)
    (target/'unlisted.py').write_text('# extra')
    with pytest.raises(ValueError, match='coverage'):
        module.extract_verified_input(path, target, **pins)


def test_duplicate_zip_members_rejected(tmp_path):
    path, pins = archive(tmp_path)
    with pytest.warns(UserWarning, match='Duplicate'):
        with zipfile.ZipFile(path, 'a') as output:
            output.writestr('src/config.py', b'# duplicate')
    pins['expected_zip_sha'] = module.sha256(path)
    with pytest.raises(ValueError, match='limits'):
        module.extract_verified_input(path, tmp_path/'source', **pins)


def test_uncompressed_member_cap_enforced(tmp_path, monkeypatch):
    path, pins = archive(tmp_path)
    monkeypatch.setattr(module, 'MAX_FILE', 4)
    with pytest.raises(ValueError, match='limits'):
        module.extract_verified_input(path, tmp_path/'source', **pins)


def test_safe_failure_records_phase_owned_message_and_byte_counts(tmp_path, capsys):
    (tmp_path/'INPUT.zip.part').write_bytes(b'x'*128)
    commits = []
    result = module.record_safe_failure(ValueError('Drive input metadata pin mismatch'),
        'DOWNLOAD', tmp_path, lambda:commits.append(True))
    assert result['phase'] == 'DOWNLOAD' and result['part_bytes'] == 128
    assert result['message'] == 'Drive input metadata pin mismatch'
    assert commits and len(list(tmp_path.glob('FAILED-*.json'))) == 1
    assert json.loads(capsys.readouterr().out)['error_type'] == 'ValueError'


def test_safe_failure_redacts_unknown_error_uri_and_secret(tmp_path, capsys):
    secret = 'refresh_token=PRIVATE https://www.googleapis.com/upload?upload_id=PRIVATE'
    result = module.record_safe_failure(ValueError(secret), 'AUTH', tmp_path, lambda:None)
    public = capsys.readouterr().out
    saved = ''.join(p.read_text() for p in tmp_path.glob('FAILED-*.json'))
    assert result['message'] is None and 'PRIVATE' not in public+saved


def test_failure_diagnostic_commit_error_keeps_original_safe_context(tmp_path, capsys):
    def fail():
        raise ValueError('PRIVATE_OAUTH_ERROR')
    result = module.record_safe_failure(ValueError('Input ZIP pin mismatch'), 'EXTRACT', tmp_path, fail)
    public = capsys.readouterr().out
    assert result['phase'] == 'EXTRACT'
    assert 'DIAGNOSTIC_PERSIST_FAILED' in public and 'PRIVATE_OAUTH_ERROR' not in public


def test_lf_embedded_plan_requires_own_raw_pin_despite_equal_crlf_json(tmp_path):
    payload = b'# fixture\n'
    plan = dict(schema='junyi-calibration-cloud-inputs-v1', bytes=len(payload),
        files=[dict(path='src/config.py', bytes=len(payload), sha256=sha(payload))])
    embedded_lf = (json.dumps(plan, indent=2)+'\n').encode()
    local_crlf = embedded_lf.replace(b'\n', b'\r\n')
    assert json.loads(embedded_lf) == json.loads(local_crlf)
    assert sha(embedded_lf) != sha(local_crlf)
    path = tmp_path/'input.zip'
    with zipfile.ZipFile(path, 'w') as output:
        output.writestr('src/config.py', payload)
        output.writestr('CLOUD_INPUT_PLAN.json', embedded_lf)
    with pytest.raises(ValueError, match='Embedded input plan pin'):
        module.extract_verified_input(path, tmp_path/'source', expected_zip_sha=module.sha256(path),
            expected_plan_sha=sha(local_crlf))
    assert not (tmp_path/'source').exists()
    assert module.extract_verified_input(path, tmp_path/'source', expected_zip_sha=module.sha256(path),
        expected_plan_sha=sha(embedded_lf)) == plan
