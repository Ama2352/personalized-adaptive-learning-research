"""Gom nội dung duy nhất bằng hardlink, giữ ánh xạ audit và mọi bản nguồn."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CATALOG = ROOT / 'experiments/akt/results/artifact-offload-20261116-01/RETENTION_REVIEW02.csv'
OUTPUT = ROOT / 'experiments/akt/results/drive-offload-duplicates-20261116-01'
PROTECTED = ('dataset/', 'artifacts/bkt_baseline/', 'venv/', '.venv/', '.wsl/', '.git/')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe_path(relative):
    if '\\' in relative or ':' in relative or '..' in relative.split('/') or relative.startswith('/'):
        raise ValueError('Đường dẫn nguồn không hợp lệ')
    path = ROOT / relative
    if not path.resolve().is_relative_to(ROOT.resolve()) or path.is_symlink():
        raise ValueError('Nguồn ra ngoài repository hoặc là symlink')
    return path


def main():
    assert digest(CATALOG) == 'b025fc11627455937e63995fce9b919938d1263afcb262be1d18965623403ad7'
    with CATALOG.open(encoding='utf-8-sig', newline='') as stream:
        candidates = [row for row in csv.DictReader(stream) if row['category'] == 'UNUSED_VERIFIED_DUPLICATE']
    by_hash = defaultdict(list)
    for row in candidates:
        assert not row['path'].lower().startswith(PROTECTED)
        assert row['sha256'] == row['keeper_sha256'] == row['keeper_current_sha256']
        by_hash[row['sha256']].append(row)
    assert len(candidates) == 21604 and len(by_hash) == 2219
    OUTPUT.mkdir(exist_ok=False)
    (OUTPUT / 'CONTENT').mkdir()
    before_free = shutil.disk_usage(ROOT).free
    originals = []
    contents = []
    for sha, group in by_hash.items():
        row = group[0]
        source = safe_path(row['keeper'])
        stat = source.stat()
        assert stat.st_size == int(row['bytes']) and source.is_file()
        name = sha + source.suffix.lower()
        destination = OUTPUT / 'CONTENT' / name
        os.link(source, destination)
        linked = destination.stat()
        assert os.path.samefile(source, destination) and (stat.st_ino, stat.st_dev, stat.st_size, stat.st_mtime_ns) == (linked.st_ino, linked.st_dev, linked.st_size, linked.st_mtime_ns)
        contents.append(dict(path='CONTENT/' + name, bytes=stat.st_size, sha256=sha, keeper=row['keeper'],
                             file_id=stat.st_ino, volume_id=stat.st_dev, keeper_links_before=stat.st_nlink))
        for item in group:
            path = safe_path(item['path'])
            current = path.stat()
            assert (current.st_size, current.st_mtime_ns) == (int(item['bytes']), int(item['modified_ns']))
            originals.append(dict(path=item['path'], bytes=current.st_size, modified_ns=current.st_mtime_ns,
                sha256=sha, content='CONTENT/' + name, keeper=item['keeper'], file_id=current.st_ino,
                volume_id=current.st_dev, links=current.st_nlink, snapshot_manifest=item['snapshot_manifest']))
    def verify(content):
        assert digest(OUTPUT / content['path']) == content['sha256']
        assert digest(safe_path(content['keeper'])) == content['sha256']
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(verify, contents))
    print(json.dumps(dict(event='CONTENT_VERIFIED', files=len(contents), bytes=sum(x['bytes'] for x in contents))), flush=True)
    manifests = {}
    for row in originals:
        if not row['snapshot_manifest']:
            continue
        relative = row['snapshot_manifest']
        if relative not in manifests:
            manifests[relative] = json.loads(safe_path(relative).read_text(encoding='utf-8'))
        logical = row['path'].split('/project/', 1)[1]
        pin = manifests[relative]['files'][logical]
        assert (pin['sha256'], pin['bytes']) == (row['sha256'], row['bytes'])
    metadata = {safe_path(path) for path in manifests}
    for row in originals:
        path = safe_path(row['path'])
        if path.suffix.lower() == '.pt':
            for sibling in path.parent.glob('*.json'):
                if sibling.stat().st_size <= 8 * 1024**2:
                    metadata.add(sibling)
    metadata_manifest = {}
    with zipfile.ZipFile(OUTPUT / 'AUDIT_METADATA.zip', 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for path in sorted(metadata):
            relative = path.relative_to(ROOT).as_posix()
            assert not any(part.lower() in ('private', 'holdout', 'test') for part in path.relative_to(ROOT).parts)
            data = path.read_bytes()
            pin = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            archive.writestr(relative, data)
            metadata_manifest[relative] = pin
        archive.writestr('METADATA_MANIFEST.json', json.dumps(metadata_manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(OUTPUT / 'AUDIT_METADATA.zip') as archive:
        for relative, pin in metadata_manifest.items():
            with archive.open(relative) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
    manifest = dict(schema='kltn-deduplicated-audit-v1', created_at_utc=datetime.now(timezone.utc).isoformat(),
        source_catalog_sha256=digest(CATALOG), content_files=contents, original_paths=originals,
        content_bytes=sum(item['bytes'] for item in contents), duplicate_path_bytes=sum(item['bytes'] for item in originals),
        metadata_zip=dict(path='AUDIT_METADATA.zip', sha256=digest(OUTPUT / 'AUDIT_METADATA.zip')),
        source_contents_preserved=True, original_duplicate_paths_removed=0,
        method_vi='Hardlink NTFS cùng volume để gom upload. Tên CONTENT là địa chỉ SHA. Nội dung nguồn/đường dẫn giữ nguyên, số liên kết filesystem tăng.',
        limits_vi='Gói lưu nội dung và ánh xạ của các binary trùng. Các log/source/dataset khác của KLTN vẫn cần giữ ở repository. Chưa nghiệm thu upload hoặc cho xóa file gốc.')
    write_json(OUTPUT / 'MANIFEST.json', manifest)
    assert all(os.path.samefile(OUTPUT / item['path'], safe_path(item['keeper'])) for item in contents)
    identities = defaultdict(list)
    for row in originals:
        identities[(row['volume_id'], row['file_id'])].append(row)
    eligible_bytes = sum(group[0]['bytes'] for group in identities.values() if len(group) == group[0]['links'])
    state = dict(status='PREPARED_AWAITING_MANUAL_UPLOAD', folder=OUTPUT.relative_to(ROOT).as_posix(),
        manifest_sha256=digest(OUTPUT / 'MANIFEST.json'), content_files=len(contents), content_bytes=manifest['content_bytes'],
        duplicate_paths=len(originals), duplicate_path_bytes=manifest['duplicate_path_bytes'],
        metadata_files=len(metadata_manifest), snapshot_manifests_verified=len(manifests),
        unique_candidate_file_identities=len(identities), candidate_last_link_logical_bytes=eligible_bytes,
        free_bytes_before=before_free, free_bytes_after=shutil.disk_usage(ROOT).free,
        files_deleted=0, uploaded=False, deletion_after_upload_requires_verification=True,
        note_vi='Dung lượng logical không bằng dung lượng thực giải phóng. Đo free bytes sau khi dọn mới có kết quả thực.')
    write_json(HERE / 'MANUAL_OFFLOAD_STATE.json', state)
    print(json.dumps(state, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
