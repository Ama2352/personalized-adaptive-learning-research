"""Rà độc lập danh mục: giữ baseline/pending replay và một bản chứng mỗi nhóm."""
import json
from pathlib import Path
import shutil

import audit_retention as audit


def main():
    summary_path = audit.HERE / 'SUMMARY.json'
    first = json.loads(summary_path.read_text())
    preserved = audit.HERE / 'SUMMARY_PASS01.json'
    assert not preserved.exists()
    shutil.copyfile(summary_path, preserved)
    rows = [json.loads(line) for line in (audit.OUTPUT / 'INVENTORY.jsonl').read_text(encoding='utf-8').splitlines()]
    for row in rows:
        category, reason = audit.classify(row['path'])
        row.update(category=category, source_category=category, reason=reason, keeper='', keeper_sha256='',
                   action='Giữ nguyên trong lần kiểm này')
        if row['sha256']:
            stat = (audit.ROOT / row['path']).stat()
            assert (stat.st_size, stat.st_mtime_ns) == (row['bytes'], row['modified_ns'])
    duplicates = audit.flag_duplicates(rows)
    parts = audit.verify_transfer_parts(rows)
    by_path = {row['path']: row for row in rows}
    for row in rows:
        if row['category'] == 'UNUSED_VERIFIED_DUPLICATE':
            keeper = by_path[row['keeper']]
            assert not keeper['category'].startswith('UNUSED_')
            assert row['sha256'] == keeper['sha256'] == row['keeper_sha256']
            assert row['bytes'] == keeper['bytes']
    audit.write_catalogs(rows, duplicates, parts, first['skipped_scopes'], first['errors'])
    result = dict(status='PASS_CLASSIFICATION_ADVERSARIAL_REVIEW',
                  corrections_vi=['Giữ baseline GAM lịch sử ở KEEP_ACTIVE.',
                                  'Giữ metadata checkpoint phục hồi và giữ một bản chứng audit của mọi nhóm trùng.',
                                  'Mỗi file trùng có bản giữ ngoài danh mục UNUSED.'],
                  verified_duplicate_keeper_links=sum(row['category'] == 'UNUSED_VERIFIED_DUPLICATE' for row in rows),
                  source_files_changed=False)
    with (audit.HERE / 'CLASSIFICATION_REVIEW.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
