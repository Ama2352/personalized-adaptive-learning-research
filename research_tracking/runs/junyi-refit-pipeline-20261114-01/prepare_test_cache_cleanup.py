"""Giữ log/config fixture và kiểm SHA lần hai cho các cache pytest cũ."""
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    plan = json.loads((HERE / 'disk-cleanup-test-cache-plan01.json').read_text())
    inventory = ROOT / plan['inventory']
    assert file_sha(inventory) == plan['inventory_sha256']
    base = (ROOT / 'artifacts/akt/test-temp').resolve()
    records = defaultdict(dict)
    for line in inventory.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        relative = Path(record['path']).relative_to('artifacts/akt/test-temp')
        if len(relative.parts) > 1:
            records[relative.parts[0]][record['path']] = record
    archive_path = ROOT / 'artifacts/akt/runtime/pytest-cache-logs-before-cleanup-20261116-01.zip'
    preserved = {}
    targets = []
    text_extensions = {'.py', '.json', '.jsonl', '.txt', '.md', '.csv', '.xml', '.log', '.toml', '.yaml', '.yml', '.ini', '.cfg', '.sha256'}
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, expected in records.items():
            directory = (base / name).resolve()
            assert directory.is_relative_to(base) and directory.parent == base
            assert not directory.is_symlink() and not os.path.isjunction(directory)
            assert plan['groups'][name]['newest_mtime'] < time.time() - 24 * 3600
            current = {}
            for parent, dirs, names in os.walk(directory, followlinks=False):
                for child in dirs:
                    path = Path(parent) / child
                    assert not path.is_symlink() and not os.path.isjunction(path)
                for child in names:
                    path = Path(parent) / child
                    assert not path.is_symlink()
                    current[path.relative_to(ROOT).as_posix()] = path
            assert set(current) == set(expected), 'Cache thay đổi sau inventory'
            for relative, path in current.items():
                pin = expected[relative]
                assert path.stat().st_size == pin['bytes'] and file_sha(path) == pin['sha256']
                if path.suffix.lower() in text_extensions or (not path.suffix and pin['bytes'] < 1024**2):
                    archive.write(path, relative)
                    preserved[relative] = pin['sha256']
            targets.append(dict(path=str(directory), files=len(current), bytes=sum(pin['bytes'] for pin in expected.values())))
    with zipfile.ZipFile(archive_path) as archive:
        assert all(hashlib.sha256(archive.read(name)).hexdigest() == sha for name, sha in preserved.items())
    ready = dict(status='CACHE_CLEANUP_VERIFIED_READY', targets=targets,
                 input_inventory=plan['inventory'], input_inventory_sha256=plan['inventory_sha256'],
                 preserved_archive=archive_path.relative_to(ROOT).as_posix(), preserved_archive_sha256=file_sha(archive_path),
                 preserved_files=len(preserved), bytes_to_remove=sum(item['bytes'] for item in targets),
                 limits_vi='Chỉ các thư mục fixture pytest13–14/11 đã kiểm hai lần. File log ở root test-temp giữ nguyên; các cache mới16/11 nằm ngoài danh sách.')
    with (HERE / 'disk-cleanup-ready-20261116-01.json').open('x', encoding='utf-8') as stream:
        json.dump(ready, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: ready[key] for key in ('status', 'preserved_files', 'bytes_to_remove', 'preserved_archive')}))


if __name__ == '__main__':
    main()
