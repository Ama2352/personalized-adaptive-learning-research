"""Ghép các phần đã tải từ Drive và kiểm SHA trước khi xuất ZIP gốc."""
import hashlib
import json
import os
from pathlib import Path


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def local_file(directory, name):
    if Path(name).name != name or '/' in name or '\\' in name or name in ('.', '..'):
        raise ValueError('Tên file trong manifest phải nằm trong thư mục hiện hành')
    return directory / name


def main():
    directory = Path(__file__).resolve().parent
    manifest = json.loads((directory / 'DRIVE_PARTS_MANIFEST.json').read_text(encoding='utf-8'))
    for archive in manifest['archives']:
        target = local_file(directory, archive['name'])
        if target.exists():
            if target.stat().st_size != archive['bytes'] or digest(target) != archive['sha256']:
                raise ValueError('ZIP đã tồn tại nhưng khác pin: ' + target.name)
            print('Đã có ZIP đúng SHA: ' + target.name)
            continue
        for part in archive['parts']:
            path = local_file(directory, part['name'])
            if path.stat().st_size != part['bytes'] or digest(path) != part['sha256']:
                raise ValueError('Phần tải về thiếu hoặc khác SHA: ' + path.name)
        temporary = target.with_suffix(target.suffix + '.rebuilding')
        total = 0
        combined = hashlib.sha256()
        with temporary.open('xb') as output:
            for part in archive['parts']:
                with local_file(directory, part['name']).open('rb') as source:
                    for block in iter(lambda: source.read(1024**2), b''):
                        output.write(block)
                        combined.update(block)
                        total += len(block)
        if total != archive['bytes'] or combined.hexdigest() != archive['sha256']:
            raise ValueError('ZIP ghép lại khác pin, giữ file rebuilding để kiểm tra')
        os.link(temporary, target)
        temporary.unlink()
        print('Đã ghép ZIP đúng SHA: ' + target.name)


if __name__ == '__main__':
    main()
