"""Rà lại giá trị audit của UNUSED, giữ nguyên danh mục và gói cũ."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'experiments/akt/results/artifact-offload-20261116-01'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def disposition(row):
    if row['category'] == 'UNUSED_RESUME_FINISHED_RUN':
        return 'KEEP_UNIQUE_AUDIT_CHECKPOINT'
    if row['category'] == 'UNUSED_VERIFIED_TRANSFER_PART':
        return 'CONDITIONAL_RECONSTRUCTIBLE_TRANSFER'
    return 'CONDITIONAL_DEDUP_RETAIN_CONTENT_AND_LINEAGE'


def scan_metadata(inventory, target_hashes):
    references = defaultdict(list)
    sources = []
    total = 0
    for item in inventory:
        relative = item['path']
        path = ROOT / relative
        parts = relative.lower().split('/')
        if any(part in ('private', 'holdout', 'test') for part in parts):
            continue
        if relative.startswith('research_tracking/runs/artifact-retention-audit-'):
            continue
        staged_index = relative.startswith('artifacts/akt/staged/') and path.name == 'INPUTS.json' and '/project/' not in relative
        relevant = relative.startswith(('research_tracking/', 'docs/', 'experiments/akt/results/')) or staged_index
        if not relevant or path.suffix != '.json' or item['bytes'] > 8 * 1024**2:
            continue
        if not path.is_file():
            continue
        content = path.read_bytes()
        sources.append(dict(path=relative, sha256=hashlib.sha256(content).hexdigest(), bytes=len(content)))
        total += len(content)
        text = content.decode('utf-8', errors='replace')
        for line_number, line in enumerate(text.splitlines(), 1):
            for digest in set(re.findall(r'(?<![a-fA-F0-9])[a-fA-F0-9]{64}(?![a-fA-F0-9])', line)) & target_hashes:
                if len(references[digest]) < 8:
                    references[digest].append(f'{relative}:{line_number}')
    return references, sources, total


def main():
    with (OUT / 'UNUSED.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    inventory = [json.loads(line) for line in (OUT / 'INVENTORY.jsonl').read_text(encoding='utf-8').splitlines()]
    by_path = {item['path']: item for item in inventory}
    original_pin = sha(OUT / 'UNUSED.csv')
    keepers = {row['keeper']: row['keeper_sha256'] for row in rows if row['keeper']}
    with ThreadPoolExecutor(max_workers=2) as pool:
        digests = dict(zip(keepers, pool.map(lambda relative: sha(ROOT / relative), keepers)))
    assert all(digests[path] == pin for path, pin in keepers.items())
    print(json.dumps(dict(event='KEEPERS_REHASHED', files=len(keepers), bytes=sum((ROOT / p).stat().st_size for p in keepers))), flush=True)
    references, sources, scanned_bytes = scan_metadata(inventory, {row['sha256'] for row in rows})
    counts = Counter()
    sizes = Counter()
    linked = 0
    staged_pinned = 0
    for row in rows:
        stat = (ROOT / row['path']).stat()
        assert (stat.st_size, stat.st_mtime_ns) == (int(row['bytes']), int(row['modified_ns']))
        status = disposition(row)
        row['review_status'] = status
        row['audit_value_vi'] = 'Nội dung và vị trí thuộc lịch sử run vẫn có giá trị audit.'
        row['deletion_authorized'] = 'false'
        refs = references.get(row['sha256'], [])
        row['metadata_sha_references'] = ' | '.join(refs)
        linked += bool(refs)
        if row['keeper']:
            assert not by_path[row['keeper']]['category'].startswith('UNUSED_')
            row['keeper_current_sha256'] = digests[row['keeper']]
        else:
            assert sha(ROOT / row['path']) == row['sha256']
            row['keeper_current_sha256'] = ''
        row['snapshot_manifest'] = ''
        if row['path'].startswith('artifacts/akt/staged/') and '/project/' in row['path']:
            prefix, logical = row['path'].split('/project/', 1)
            manifest_path = ROOT / prefix / 'INPUTS.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            pin = manifest.get('files', {}).get(logical)
            if pin:
                assert pin['sha256'] == row['sha256'] and pin['bytes'] == int(row['bytes'])
                row['snapshot_manifest'] = manifest_path.relative_to(ROOT).as_posix()
                staged_pinned += 1
        if status == 'KEEP_UNIQUE_AUDIT_CHECKPOINT':
            row['required_before_cleanup_vi'] = 'Giữ checkpoint và metadata. Model cuối không tái tạo được optimizer/RNG tại bước trung gian này.'
        elif status == 'CONDITIONAL_RECONSTRUCTIBLE_TRANSFER':
            row['required_before_cleanup_vi'] = 'Giữ ZIP đầy đủ, DRIVE_PARTS và recipe chia phần. Chỉ bỏ phần sau backup và kiểm phục hồi đúng SHA.'
        else:
            row['required_before_cleanup_vi'] = 'Giữ một bản nội dung, metadata nguồn và ánh xạ đường dẫn/SHA. Kiểm phục hồi snapshot trước khi thu gọn.'
        counts[status] += 1
        sizes[status] += int(row['bytes'])
    proofs = json.loads((OUT / 'TRANSFER_PARTS_VERIFIED.json').read_text())
    part_count = 0
    for proof in proofs:
        index = json.loads((ROOT / proof['index']).read_text())
        with (ROOT / proof['archive']).open('rb') as stream:
            for part in index['parts']:
                count = part['bytes']
                digest = hashlib.sha256()
                while count:
                    chunk = stream.read(min(count, 1024**2))
                    assert chunk
                    count -= len(chunk)
                    digest.update(chunk)
                assert digest.hexdigest() == part['sha256']
                part_count += 1
            assert not stream.read(1)
    catalog = OUT / 'RETENTION_REVIEW02.csv'
    with catalog.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(status='AUDIT_RETENTION_REVIEW_COMPLETE_NO_DELETION', reviewed_files=len(rows),
        reviewed_bytes=sum(int(row['bytes']) for row in rows), dispositions={name: dict(files=counts[name], bytes=sizes[name]) for name in counts},
        keeper_files_rehashed=len(keepers), keeper_bytes_rehashed=sum((ROOT / p).stat().st_size for p in keepers),
        files_with_sha_metadata_reference=linked, staged_files_matched_to_INPUTS=staged_pinned,
        metadata_json_files_scanned=len(sources), metadata_bytes_scanned=scanned_bytes,
        transfer_parts_reproduced_from_full_zip=part_count, original_unused_csv_sha256=original_pin,
        revised_catalog_sha256=sha(catalog), deletion_authorized=False, originals_changed=False,
        limits_vi=['Tham chiếu SHA chỉ là bằng chứng liên kết, không chứng minh đầy đủ mọi phụ thuộc.',
                   'Phạm vi quét metadata JSON từ inventory cũ, tối đa 8 MiB/file. Không đọc Holdout/private.',
                   'Chưa thực hiện thay thế file bằng liên kết hoặc thử dựng lại mọi snapshot trong đường dẫn độc lập.',
                   'Các gói 01–05 không sao lưu toàn bộ 57,18 GB trong danh mục cũ.'])
    write_json(HERE / 'REVIEW02.json', summary)
    write_json(OUT / 'REVIEW02_METADATA_SOURCES.json', dict(files=sources))
    unique = next(row for row in rows if disposition(row) == 'KEEP_UNIQUE_AUDIT_CHECKPOINT')
    checkpoint_dir = (ROOT / unique['path']).parent
    paths = [catalog, HERE / 'REVIEW02.json', OUT / 'REVIEW02_METADATA_SOURCES.json', *checkpoint_dir.iterdir()]
    archive_path = OUT / '06_AUDIT_RETENTION_REVIEW.zip'
    pins = {path.relative_to(ROOT).as_posix(): dict(sha256=sha(path), bytes=path.stat().st_size) for path in paths if path.is_file()}
    with zipfile.ZipFile(archive_path, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for relative in pins:
            archive.write(ROOT / relative, relative)
        archive.writestr('PACKAGE_MANIFEST.json', json.dumps(dict(files=pins, originals_preserved=True), ensure_ascii=False, indent=2))
    with zipfile.ZipFile(archive_path) as archive:
        for relative, pin in pins.items():
            with archive.open(relative) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
            assert sha(ROOT / relative) == pin['sha256']
    assert sha(OUT / 'UNUSED.csv') == original_pin
    write_json(HERE / 'REVIEW02_PACKAGE.json', dict(path=archive_path.relative_to(ROOT).as_posix(), bytes=archive_path.stat().st_size,
        sha256=sha(archive_path), members_verified=len(pins), uploaded=False))
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
