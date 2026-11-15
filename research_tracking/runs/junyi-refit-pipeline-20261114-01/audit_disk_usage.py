"""Thống kê metadata dung lượng, không sửa/xóa file và không đi qua junction."""
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    started = time.monotonic()
    groups = defaultdict(lambda: dict(bytes=0, files=0))
    extensions = defaultdict(lambda: dict(bytes=0, files=0))
    seen = set()
    logical = 0
    unique = 0
    large = []
    recent = defaultdict(lambda: dict(bytes=0, files=0))
    errors = []
    skipped = []
    stack = [ROOT]
    count = 0
    now = time.time()
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink() or os.path.isjunction(entry.path):
                            skipped.append(str(Path(entry.path).relative_to(ROOT)))
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        stat = entry.stat(follow_symlinks=False)
                        path = Path(entry.path).relative_to(ROOT)
                        count += 1
                        logical += stat.st_size
                        key = (stat.st_dev, stat.st_ino) if stat.st_ino else str(path)
                        if key not in seen:
                            seen.add(key)
                            unique += stat.st_size
                        for depth in (1, 2, 3):
                            group = '/'.join(path.parts[:depth])
                            groups[group]['bytes'] += stat.st_size
                            groups[group]['files'] += 1
                        extension = path.suffix.lower() or '[không đuôi]'
                        extensions[extension]['bytes'] += stat.st_size
                        extensions[extension]['files'] += 1
                        if stat.st_size >= 100 * 1024**2:
                            large.append(dict(path=path.as_posix(), bytes=stat.st_size,
                                modified_at_utc=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()))
                        if now - stat.st_mtime < 24 * 3600:
                            recent[path.parts[0]]['bytes'] += stat.st_size
                            recent[path.parts[0]]['files'] += 1
                    except OSError as error:
                        errors.append(dict(path=entry.path, error=str(error)))
        except OSError as error:
            errors.append(dict(path=str(directory), error=str(error)))
    report = dict(status='READ_ONLY_DISK_METADATA_INVENTORY', root=str(ROOT), files=count,
                  logical_bytes=logical, unique_file_id_logical_bytes=unique,
                  wall_seconds=time.monotonic() - started,
                  observed_at_utc=datetime.now(timezone.utc).isoformat(),
                  groups=dict(sorted(groups.items(), key=lambda item: item[1]['bytes'], reverse=True)),
                  extensions=dict(sorted(extensions.items(), key=lambda item: item[1]['bytes'], reverse=True)),
                  large_files=sorted(large, key=lambda item: item['bytes'], reverse=True),
                  modified_last_24h_by_root=dict(recent), errors=errors, skipped_links=skipped,
                  limits_vi='Dung lượng logic theo metadata, không tương đương hoàn toàn dung lượng cấp phát nếu sparse/compressed. File hardlink có thể lặp ở bảng thư mục; tổngunique tách theo fileID. mtime không chứng minh thời điểm download.')
    output = HERE / 'disk-usage-20261115-01.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ('files', 'logical_bytes', 'unique_file_id_logical_bytes', 'wall_seconds')}))
    print(json.dumps({key: value for key, value in report['groups'].items() if '/' not in key}, ensure_ascii=False))
    print(json.dumps(report['large_files'][:12], ensure_ascii=False))


if __name__ == '__main__':
    main()
