"""Inventory SHA-256 các fixture pytest cũ trước khi đề xuất dọn cache."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    base = (ROOT / 'artifacts/akt/test-temp').resolve()
    assert base.is_relative_to(ROOT.resolve())
    output = ROOT / 'artifacts/akt/runtime/disk-cleanup-test-cache-20261115-01.jsonl'
    groups = defaultdict(lambda: dict(files=0, bytes=0, newest_mtime=0))
    skipped = []
    inventory_sha = hashlib.sha256()
    with output.open('xb') as stream:
        for directory, directories, files in os.walk(base, followlinks=False):
            directories[:] = [name for name in directories if not os.path.isjunction(Path(directory) / name)
                              and not (Path(directory) / name).is_symlink()]
            for name in sorted(files):
                path = Path(directory) / name
                if path.is_symlink():
                    skipped.append(path.relative_to(ROOT).as_posix())
                    continue
                resolved = path.resolve()
                assert resolved.is_relative_to(base)
                stat = path.stat()
                with path.open('rb') as source:
                    sha = hashlib.file_digest(source, 'sha256').hexdigest()
                after = path.stat()
                assert (stat.st_size, stat.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
                record = dict(path=path.relative_to(ROOT).as_posix(), bytes=stat.st_size,
                              sha256=sha, modified_ns=stat.st_mtime_ns)
                raw = (json.dumps(record, ensure_ascii=False) + '\n').encode('utf-8')
                stream.write(raw)
                inventory_sha.update(raw)
                group = groups[path.relative_to(base).parts[0]]
                group['files'] += 1
                group['bytes'] += stat.st_size
                group['newest_mtime'] = max(group['newest_mtime'], stat.st_mtime)
    summary = dict(status='INVENTORY_ONLY_NO_DELETION', base=str(base), inventory=output.relative_to(ROOT).as_posix(),
                   inventory_sha256=inventory_sha.hexdigest(), groups=dict(groups), skipped_links=skipped,
                   observed_at_utc=datetime.now(timezone.utc).isoformat())
    with (HERE / 'disk-cleanup-test-cache-plan01.json').open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
