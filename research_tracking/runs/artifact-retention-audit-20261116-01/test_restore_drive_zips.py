"""Kiểm phục hồi bằng ZIP tổng hợp nhỏ, không đọc ZIP/model nghiên cứu."""
import hashlib
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def prepared_run(tmp_path):
    source = Path(__file__).with_name('restore_drive_zips.py')
    helper_path = tmp_path / source.name
    helper_path.write_bytes(source.read_bytes())
    specification = importlib.util.spec_from_file_location('drive_restore_fixture', helper_path)
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, 'w', compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('note.txt', 'Kiểm phục hồi tổng hợp\n')
        archive.writestr('tiny.bin', bytes(range(64)))
    archive_bytes = archive_buffer.getvalue()
    boundary = len(archive_bytes) // 3
    part_bytes = [archive_bytes[:boundary], archive_bytes[boundary:]]
    parts = []
    for index, contents in enumerate(part_bytes, start=1):
        name = f'synthetic.zip.part{index:02d}'
        (tmp_path / name).write_bytes(contents)
        parts.append({
            'name': name,
            'bytes': len(contents),
            'sha256': hashlib.sha256(contents).hexdigest(),
        })
    manifest = {
        'schema': 'kltn-drive-split-v1',
        'archives': [{
            'name': 'synthetic.zip',
            'bytes': len(archive_bytes),
            'sha256': hashlib.sha256(archive_bytes).hexdigest(),
            'parts': parts,
        }],
    }
    manifest_path = tmp_path / 'DRIVE_PARTS_MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    return helper, manifest, archive_bytes


def test_valid_ordered_reassembly(prepared_run, tmp_path):
    helper, manifest, archive_bytes = prepared_run
    helper.main()
    target = tmp_path / 'synthetic.zip'
    assert target.read_bytes() == archive_bytes
    assert not (tmp_path / 'synthetic.zip.rebuilding').exists()
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert archive.read('tiny.bin') == bytes(range(64))
    for part in manifest['archives'][0]['parts']:
        assert helper.digest(tmp_path / part['name']) == part['sha256']


def test_corrupt_part_is_rejected(prepared_run, tmp_path):
    helper, manifest, _ = prepared_run
    part_path = tmp_path / manifest['archives'][0]['parts'][0]['name']
    damaged = bytearray(part_path.read_bytes())
    damaged[0] ^= 1
    part_path.write_bytes(damaged)
    with pytest.raises(ValueError, match='Phần tải về thiếu hoặc khác SHA'):
        helper.main()
    assert not (tmp_path / 'synthetic.zip').exists()
    assert not (tmp_path / 'synthetic.zip.rebuilding').exists()


def test_existing_wrong_target_is_preserved(prepared_run, tmp_path):
    helper, _, archive_bytes = prepared_run
    target = tmp_path / 'synthetic.zip'
    existing_bytes = b'x' * len(archive_bytes)
    target.write_bytes(existing_bytes)
    with pytest.raises(ValueError, match='ZIP đã tồn tại nhưng khác pin'):
        helper.main()
    assert target.read_bytes() == existing_bytes
    assert not (tmp_path / 'synthetic.zip.rebuilding').exists()


def test_reordered_parts_fail_complete_archive_pin(prepared_run, tmp_path):
    helper, manifest, _ = prepared_run
    manifest['archives'][0]['parts'].reverse()
    (tmp_path / 'DRIVE_PARTS_MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError, match='ZIP ghép lại khác pin'):
        helper.main()
    assert not (tmp_path / 'synthetic.zip').exists()
    assert (tmp_path / 'synthetic.zip.rebuilding').exists()


def test_target_created_during_publication_is_preserved(prepared_run, tmp_path, monkeypatch):
    helper, _, archive_bytes = prepared_run
    original_link = helper.os.link
    concurrent_bytes = 'Giữ file được tạo trong lúc phục hồi'.encode('utf-8')

    def create_target_then_link(source, target):
        target.write_bytes(concurrent_bytes)
        original_link(source, target)

    monkeypatch.setattr(helper.os, 'link', create_target_then_link)
    with pytest.raises(FileExistsError):
        helper.main()
    assert (tmp_path / 'synthetic.zip').read_bytes() == concurrent_bytes
    assert (tmp_path / 'synthetic.zip.rebuilding').read_bytes() == archive_bytes


@pytest.mark.parametrize('name', ['.', '..', '../escape.zip', 'nested/file.zip', 'nested\\file.zip'])
def test_non_basename_is_rejected(prepared_run, tmp_path, name):
    helper, _, _ = prepared_run
    with pytest.raises(ValueError, match='Tên file trong manifest'):
        helper.local_file(tmp_path, name)


def test_absolute_path_is_rejected(prepared_run, tmp_path):
    helper, _, _ = prepared_run
    with pytest.raises(ValueError, match='Tên file trong manifest'):
        helper.local_file(tmp_path, str(tmp_path / 'escape.zip'))


def test_plain_basename_is_accepted(prepared_run, tmp_path):
    helper, _, _ = prepared_run
    assert helper.local_file(tmp_path, 'synthetic.zip.part01') == tmp_path / 'synthetic.zip.part01'
