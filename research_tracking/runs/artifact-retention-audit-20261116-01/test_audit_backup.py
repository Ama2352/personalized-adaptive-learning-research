"""Kiểm gói tổng hợp nhỏ và phục hồi an toàn, không đọc model nghiên cứu."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def backup(tmp_path):
    spec = importlib.util.spec_from_file_location('audit_backup_fixture', Path(__file__).with_name('audit_backup.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    package = tmp_path / 'package'
    (package / 'CONTENT').mkdir(parents=True)
    data = b'noi dung tong hop nho\n'
    sha = hashlib.sha256(data).hexdigest()
    content = 'CONTENT/' + sha + '.bin'
    (package / content).write_bytes(data)
    pin = {'bytes': len(data), 'sha256': sha}
    manifest = {'schema': 'kltn-deduplicated-audit-v1',
                'content_files': [dict(pin, path=content, keeper='retained.bin')],
                'original_paths': [dict(pin, path=name, content=content, keeper='retained.bin',
                                        modified_ns=1700000000000000000)
                                   for name in ['snapshot/a.bin', 'snapshot/b.bin']]}
    (package / 'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
    return helper, package, manifest, data


def test_verify_hashes_unique_content_once(backup, monkeypatch):
    helper, package, _, _ = backup
    original = helper.digest
    calls = []
    def counted(path):
        calls.append(path)
        return original(path)
    monkeypatch.setattr(helper, 'digest', counted)
    result = helper.run(package)
    assert result == {'content_files_verified': 1, 'original_paths': 2, 'files_restored': 0, 'files_deleted': 0}
    assert len(calls) == 1


def test_changed_blob_rejected(backup):
    helper, package, manifest, data = backup
    (package / manifest['content_files'][0]['path']).write_bytes(b'x' * len(data))
    with pytest.raises(ValueError, match='khác pin'):
        helper.run(package)


def test_restore_preserves_content_mtime_and_retry(backup, tmp_path):
    helper, package, manifest, data = backup
    target = tmp_path / 'restored'
    assert helper.run(package, target)['files_restored'] == 2
    for row in manifest['original_paths']:
        path = target / row['path']
        assert path.read_bytes() == data
        assert path.stat().st_mtime_ns == row['modified_ns']
    assert helper.run(package, target)['files_restored'] == 0
    assert not list(target.rglob('.audit-restore-*'))


def test_mismatching_target_preserved_before_any_write(backup, tmp_path):
    helper, package, _, _ = backup
    target = tmp_path / 'restored'
    (target / 'snapshot').mkdir(parents=True)
    (target / 'snapshot/b.bin').write_bytes(b'existing different data')
    with pytest.raises(ValueError, match='khác pin'):
        helper.run(package, target)
    assert (target / 'snapshot/b.bin').read_bytes() == b'existing different data'
    assert not (target / 'snapshot/a.bin').exists()


def test_target_created_during_publish_is_preserved(backup, tmp_path, monkeypatch):
    helper, package, _, _ = backup
    target_root = tmp_path / 'restored'
    operation = 'rename' if helper.os.name == 'nt' else 'link'
    publish = getattr(helper.os, operation)
    def concurrent_publish(source, target):
        target.write_bytes(b'created concurrently')
        return publish(source, target)
    monkeypatch.setattr(helper.os, operation, concurrent_publish)
    with pytest.raises(FileExistsError):
        helper.run(package, target_root)
    assert (target_root / 'snapshot/a.bin').read_bytes() == b'created concurrently'
    assert not list(target_root.rglob('.audit-restore-*'))


@pytest.mark.parametrize('field,value', [('path', '../outside.bin'), ('path', 'C:/outside.bin'),
                                        ('path', '/outside.bin'), ('content', '../outside.bin')])
def test_path_traversal_rejected(backup, tmp_path, field, value):
    helper, package, manifest, _ = backup
    if field == 'content':
        manifest['content_files'][0]['path'] = value
    else:
        manifest['original_paths'][0][field] = value
    (package / 'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(ValueError):
        helper.run(package, tmp_path / 'restored')
    assert not (tmp_path / 'restored').exists()
