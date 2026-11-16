"""Kiểm nội dung gói audit và phục hồi đường dẫn theo manifest, không xóa nguồn."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('Đường dẫn manifest không hợp lệ')
    parts = relative.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10)}
    if any(part in ('', '.', '..') or part.endswith((' ', '.')) or
           part.split('.')[0].upper() in reserved or any(ord(char) < 32 for char in part)
           for part in parts):
        raise ValueError('Đường dẫn manifest không hợp lệ: ' + relative)
    root = root.resolve()
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root):
        raise ValueError('Đường dẫn vượt thư mục đích: ' + relative)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError('Đường dẫn chứa liên kết: ' + relative)
    return target


def validate_pin(row):
    if type(row['bytes']) is not int or row['bytes'] < 0 or not re.fullmatch('[0-9a-f]{64}', row['sha256']):
        raise ValueError('Pin kích thước/SHA không hợp lệ')


def check_file(path, row):
    before = path.stat()
    if not path.is_file() or before.st_size != row['bytes'] or digest(path) != row['sha256']:
        raise ValueError('Nội dung khác pin: ' + str(path))
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino, before.st_dev) != (after.st_size, after.st_mtime_ns, after.st_ino, after.st_dev):
        raise ValueError('File thay đổi trong lúc kiểm: ' + str(path))


def restore_file(source, target, row):
    if target.exists():
        check_file(target, row)
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=target.parent, prefix='.audit-restore-', delete=False) as output:
            temporary = Path(output.name)
            combined = hashlib.sha256()
            total = 0
            with source.open('rb') as stream:
                for block in iter(lambda: stream.read(1024**2), b''):
                    output.write(block)
                    combined.update(block)
                    total += len(block)
            output.flush()
            os.fsync(output.fileno())
        if total != row['bytes'] or combined.hexdigest() != row['sha256']:
            raise ValueError('Nội dung thay đổi trong lúc phục hồi: ' + str(source))
        os.utime(temporary, ns=(temporary.stat().st_atime_ns, row['modified_ns']))
        # Công bố file hoàn chỉnh, từ chối ghi đè kể cả khi đích vừa được tạo.
        if os.name == 'nt':
            os.rename(temporary, target)
        else:
            os.link(temporary, target)
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def run(directory, restore_root=None):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / 'MANIFEST.json').read_text(encoding='utf-8-sig'))
    if manifest['schema'] != 'kltn-deduplicated-audit-v1':
        raise ValueError('Schema manifest không được hỗ trợ')
    contents = {}
    for row in manifest['content_files']:
        validate_pin(row)
        path = safe_path(directory, row['path'])
        if not row['path'].startswith('CONTENT/') or row['path'] in contents:
            raise ValueError('Đường dẫn CONTENT trùng hoặc không hợp lệ')
        contents[row['path']] = (path, row)
    targets = []
    seen = set()
    target_root = Path(restore_root).resolve() if restore_root is not None else directory
    for row in manifest['original_paths']:
        validate_pin(row)
        target = safe_path(target_root, row['path'])
        normalized = os.path.normcase(str(target))
        if normalized in seen:
            raise ValueError('Đường dẫn phục hồi trùng: ' + row['path'])
        seen.add(normalized)
        source, pin = contents[row['content']]
        if (row['bytes'], row['sha256']) != (pin['bytes'], pin['sha256']):
            raise ValueError('Ánh xạ nội dung khác pin: ' + row['path'])
        if type(row['modified_ns']) is not int or row['modified_ns'] < 0:
            raise ValueError('mtime không hợp lệ')
        targets.append((source, target, row))
    for path, row in contents.values():
        check_file(path, row)
    if 'metadata_zip' in manifest:
        metadata = manifest['metadata_zip']
        path = safe_path(directory, metadata['path'])
        if digest(path) != metadata['sha256']:
            raise ValueError('ZIP metadata khác SHA')
    restored = 0
    if restore_root is not None:
        # Kiểm mọi đích hiện hữu trước khi bắt đầu ghi file mới.
        for _, target, row in targets:
            if target.exists():
                check_file(target, row)
        for source, target, row in targets:
            safe_path(target_root, row['path'])
            restored += restore_file(source, target, row)
    return {'content_files_verified': len(contents), 'original_paths': len(targets),
            'files_restored': restored, 'files_deleted': 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent,
                        help='Thư mục chứa MANIFEST.json và CONTENT')
    parser.add_argument('--restore-root', type=Path, help='Thư mục nhận đường dẫn gốc cần phục hồi')
    args = parser.parse_args(argv)
    result = run(args.directory, args.restore_root)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
