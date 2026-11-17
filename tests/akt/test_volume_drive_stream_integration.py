"""Nối ZIP trong RAM với resumable Drive giả, không network hoặc Modal compute."""
import hashlib
import io
import json
import zipfile

import pytest

from test_drive_stream_upload import Drive, upload
from test_modal_volume_archive import Volume
from scripts.akt.modal_volume_archive import iter_zip_bytes, make_plan, zip_size


def source_case():
    prefix = 'junyi-calibration-real-20261117-01/a2-numeric/payloads/'
    content = {prefix+'RECEIPT.json': b'{"synthetic":true}',
               prefix+'shard-000000.npz': b'synthetic-probability'*32768}
    plan = make_plan([dict(archive_name=path, volume_path=path, bytes=len(data),
                           sha256=hashlib.sha256(data).hexdigest()) for path, data in content.items()])
    return content, plan


@pytest.mark.parametrize('mode', ['partial', 'disconnect'])
def test_archive_to_drive_resumes_and_matches_zip_members(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(upload, 'PRIVATE', tmp_path)
    content, source = source_case()
    drive = Drive()
    drive.mode = mode
    path = tmp_path/'private/state.json'
    plan = dict(folder_id='folder', name='A2_NUMERIC_COMPLETE.zip', total_bytes=zip_size(source),
                source_plan_sha256=source['source_plan_sha256'])
    receipt = upload.upload_stream(drive, plan, lambda: iter_zip_bytes(Volume(content), source),
                                   path, chunk_bytes=256*1024, sleep=lambda _: None)
    assert receipt['status'] == 'REMOTE_STREAM_SHA256_VERIFIED'
    assert receipt['sha256'] == hashlib.sha256(drive.data).hexdigest()
    assert len(drive.data) == zip_size(source)
    with zipfile.ZipFile(io.BytesIO(drive.data)) as archive:
        assert {name: archive.read(name) for name in archive.namelist()} == content
    assert json.loads(path.read_text())['complete'] == receipt
    upload.upload_stream(drive, plan, lambda: pytest.fail('Completed upload must not read Volume again'),
                         path, chunk_bytes=256*1024, sleep=lambda _: None)


def test_source_hash_error_never_marks_archive_verified(tmp_path, monkeypatch):
    monkeypatch.setattr(upload, 'PRIVATE', tmp_path)
    content, source = source_case()
    payload = next(path for path in content if path.endswith('.npz'))
    content[payload] = b'x'+content[payload][1:]
    path = tmp_path/'private/state.json'
    plan = dict(folder_id='folder', name='A2_NUMERIC_COMPLETE.zip', total_bytes=zip_size(source),
                source_plan_sha256=source['source_plan_sha256'])
    with pytest.raises(ValueError, match='SHA/bytes'):
        upload.upload_stream(Drive(), plan, lambda: iter_zip_bytes(Volume(content), source),
                             path, chunk_bytes=256*1024, sleep=lambda _: None)
    assert 'complete' not in json.loads(path.read_text())
