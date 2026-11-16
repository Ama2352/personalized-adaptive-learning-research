"""Nghiệm thu gói lưu trữ và liên kết bản giữ, không sửa file nguồn."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'experiments/akt/results/artifact-offload-20261116-01'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    packages = json.loads((HERE / 'PACKAGES.json').read_text())['packages']
    packages.append(json.loads((HERE / 'CATALOG_PACKAGE.json').read_text()))
    for package in packages:
        path = ROOT / package['path']
        assert path.stat().st_size == package['bytes']
        assert sha(path) == package['sha256']
    summary = json.loads((HERE / 'SUMMARY.json').read_text())
    for catalog in summary['catalogs'].values():
        assert sha(ROOT / catalog['path']) == catalog['sha256']
    rows = [json.loads(line) for line in (OUTPUT / 'INVENTORY.jsonl').read_text(encoding='utf-8').splitlines()]
    by_path = {row['path']: row for row in rows}
    duplicate_count = 0
    for row in rows:
        if row['category'] != 'UNUSED_VERIFIED_DUPLICATE':
            continue
        keeper = by_path[row['keeper']]
        assert not keeper['category'].startswith('UNUSED_')
        assert row['sha256'] == keeper['sha256'] == row['keeper_sha256']
        assert row['bytes'] == keeper['bytes']
        for item in (row, keeper):
            stat = (ROOT / item['path']).stat()
            assert (stat.st_size, stat.st_mtime_ns) == (item['bytes'], item['modified_ns'])
        duplicate_count += 1
    pins = {}
    for package in packages[:3]:
        manifest = json.loads((OUTPUT / (Path(package['path']).name + '.manifest.json')).read_text(encoding='utf-8'))
        for relative, pin in manifest['files'].items():
            assert sha(ROOT / relative) == pin['sha256']
            pins[relative] = pin
    for path in HERE.iterdir():
        if path.suffix == '.py' or path.name in ('SUMMARY.json', 'PACKAGES.json', 'CATALOG_PACKAGE.json', 'CLASSIFICATION_REVIEW.json', 'tests03.log'):
            pins[path.relative_to(ROOT).as_posix()] = dict(bytes=path.stat().st_size, sha256=sha(path))
    save(HERE / 'SOURCE_MANIFEST.json', dict(files=pins, note_vi='Pin nguồn model và mã kiểm kê ở thời điểm nghiệm thu.'))
    save(OUTPUT / 'UPLOAD_INDEX.json', dict(packages=packages, total_bytes=sum(p['bytes'] for p in packages),
        existing_archive_index='EXISTING_ARCHIVES_READY.json', unused_catalog='UNUSED.csv', uploaded=False))
    result = dict(status='PASS_OFFLOAD_PREPARATION', checked_at_utc=datetime.now(timezone.utc).isoformat(),
        packages_verified=len(packages), total_package_bytes=sum(p['bytes'] for p in packages),
        duplicate_keeper_links_verified=duplicate_count, catalog_hashes_verified=True,
        source_model_hashes_reverified=True, classifier_tests='8 passed in 0.12s, tests03.log',
        originals_preserved=True, remote_upload_performed=False, deletion_performed=False, gpu_used=False,
        limits_vi=['Chỉ kiểm trùng binary trong phạm vi hash đã mô tả, không phải toàn bộ file.',
                   '.pytest_cache chưa đọc được. REVIEW cần kiểm thêm phụ thuộc.',
                   'ZIP khác SHA có thể chứa member chồng lặp, chưa kiểm hết.',
                   'UNUSED là danh mục đề xuất. Cần giữ lineage khi có quyết định dọn sau này.'])
    save(HERE / 'ACCEPTANCE.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
