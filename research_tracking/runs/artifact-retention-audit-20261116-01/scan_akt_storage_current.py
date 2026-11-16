"""Kiểm metadata hai vùng AKT, đếm inode để phân biệt hardlink và dữ liệu."""
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'artifacts/akt/runtime/storage-review-20261116-03'
ROOTS = (ROOT / 'artifacts/akt', ROOT / 'experiments/akt')


def main():
    OUTPUT.mkdir(exist_ok=False)
    groups = defaultdict(lambda: dict(files=0, logical_bytes=0, unique_bytes=0, large_files=[]))
    seen = set()
    errors = []
    skipped = []
    with (OUTPUT / 'files.jsonl').open('x', encoding='utf-8') as log:
        stack = list(ROOTS)
        while stack:
            directory = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        path = Path(entry.path)
                        relative = path.relative_to(ROOT).as_posix()
                        if entry.name.lower() in ('private', 'holdout', 'test') or relative.startswith(OUTPUT.relative_to(ROOT).as_posix()):
                            skipped.append(relative)
                            continue
                        if entry.is_symlink() or os.path.isjunction(entry.path):
                            skipped.append(relative)
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(path)
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        # DirEntry.stat trên Windows có thể trả inode/nlink bằng0.
                        stat = path.stat()
                        if stat.st_ino == 0 or stat.st_nlink == 0:
                            raise ValueError('File identity không hợp lệ: ' + relative)
                        parts = path.relative_to(ROOT).parts
                        group = '/'.join(parts[:3] if parts[0] == 'artifacts' else parts[:4])
                        item = groups[group]
                        item['files'] += 1
                        item['logical_bytes'] += stat.st_size
                        identity = (stat.st_dev, stat.st_ino)
                        if identity not in seen:
                            item['unique_bytes'] += stat.st_size
                            seen.add(identity)
                        row = dict(path=relative, bytes=stat.st_size, modified_ns=stat.st_mtime_ns,
                                   file_id=stat.st_ino, volume_id=stat.st_dev, links=stat.st_nlink, group=group)
                        if stat.st_size >= 100 * 1024**2:
                            item['large_files'].append(dict(path=relative, bytes=stat.st_size))
                        log.write(json.dumps(row, ensure_ascii=False) + '\n')
            except OSError as error:
                errors.append(dict(path=str(directory), error_type=type(error).__name__))
    summary = dict(status='METADATA_SCAN_COMPLETE', checked_at_utc=datetime.now(timezone.utc).isoformat(),
        groups=[dict(path=path, **item) for path, item in sorted(groups.items(), key=lambda x: x[1]['logical_bytes'], reverse=True)],
        total_logical_bytes=sum(item['logical_bytes'] for item in groups.values()),
        total_unique_file_identity_bytes=sum(item['unique_bytes'] for item in groups.values()),
        unique_file_identities=len(seen), free_bytes=shutil.disk_usage(ROOT).free,
        errors=errors, skipped=skipped, files_deleted=0,
        limits_vi='Unique bytes là tổng kích thước theo file identity, chưa phải allocation NTFS. Gán nhóm theo nơi gặp đầu trong scan, không dùng unique_bytes từng nhóm để quyết định xóa. Không đọc nội dung file trong lượt này.')
    (OUTPUT / 'SUMMARY.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    receipt = dict(status=summary['status'], summary=(OUTPUT / 'SUMMARY.json').relative_to(ROOT).as_posix(),
                   inventory=(OUTPUT / 'files.jsonl').relative_to(ROOT).as_posix(),
                   total_logical_bytes=summary['total_logical_bytes'], total_unique_bytes=summary['total_unique_file_identity_bytes'],
                   files_deleted=0, free_bytes=summary['free_bytes'])
    (HERE / 'STORAGE_REVIEW02_STATE.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    print(json.dumps([dict(path=r['path'],files=r['files'],gb=round(r['logical_bytes']/1e9,3)) for r in summary['groups'][:20]], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
