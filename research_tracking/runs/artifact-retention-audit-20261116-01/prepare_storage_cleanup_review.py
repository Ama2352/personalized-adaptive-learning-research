"""Lập danh sách dọn có bằng chứng và nén hồ sơ nhỏ, chưa xóa file."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / 'experiments/akt/results/artifact-offload-20261116-01'
SCAN = ROOT / 'artifacts/akt/runtime/storage-review-20261116-03'
OUT = ROOT / 'experiments/akt/results/storage-small-evidence-20261116-01'
FIXTURES = (
    'artifacts/akt/runtime/a1-compact-adapter-tests-20261113-01',
    'artifacts/akt/runtime/a1-fastpath-tests-20261113-01',
    'artifacts/akt/runtime/refit-pipeline-tests-20261114-04',
    'artifacts/akt/runtime/refit-pipeline-tests-20261114-03',
)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=False)
    inflight = set()
    for line in (SCAN / 'files.jsonl').open(encoding='utf-8'):
        row = json.loads(line)
        if row['group'].endswith(('drive-offload-duplicates-20261116-01', 'drive-offload-history-20261116-01')):
            inflight.add((row['volume_id'], row['file_id']))
    candidates = []
    rejected = []

    def add(path, group, expected=None):
        relative = path.relative_to(ROOT).as_posix()
        assert path.resolve().is_relative_to(ROOT.resolve()) and path.is_file() and not path.is_symlink()
        before = path.stat()
        if (before.st_dev, before.st_ino) in inflight:
            rejected.append(dict(path=relative, reason_vi='Dùng chung inode với thư mục đang upload, giữ nguyên'))
            return
        digest = sha(path)
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns, after.st_ino)
        if expected:
            assert digest == expected['sha256'] and after.st_size == expected['bytes']
        candidates.append(dict(path=relative, group=group, bytes=after.st_size, sha256=digest,
            modified_ns=after.st_mtime_ns, file_id=after.st_ino, volume_id=after.st_dev, links=after.st_nlink))

    receipt = json.loads((HERE / 'DRIVE_UPLOAD_RECEIPT01.json').read_text(encoding='utf-8'))
    assert receipt['remote_checksum_verified'] and receipt['status'] == 'COMPLETE_REMOTE_SHA256_VERIFIED'
    parts = json.loads((OLD / 'drive-transfer-parts-20261116-01/DRIVE_PARTS_MANIFEST.json').read_text(encoding='utf-8'))
    for archive in parts['archives']:
        source = ROOT / archive['source']
        assert sha(source) == archive['sha256']
        for part in archive['parts']:
            remote = next(r for r in receipt['files'] if r['name'] == part['name'])
            assert remote['remote_sha256_verified'] and remote['sha256'] == part['sha256']
            add(OLD / 'drive-transfer-parts-20261116-01' / part['name'], 'TRANSFER_ALREADY_DRIVE_VERIFIED', part)

    proofs = json.loads((OLD / 'TRANSFER_PARTS_VERIFIED.json').read_text(encoding='utf-8'))
    for proof in proofs:
        index = json.loads((ROOT / proof['index']).read_text(encoding='utf-8'))
        archive = ROOT / proof['archive']
        assert sha(archive) == proof['archive_sha256'] == index['archive_sha256']
        with archive.open('rb') as stream:
            for part in index['parts']:
                name = part.get('name') or part.get('file')
                digest = hashlib.sha256()
                remaining = part['bytes']
                while remaining:
                    block = stream.read(min(1024**2, remaining))
                    assert block
                    digest.update(block)
                    remaining -= len(block)
                assert digest.hexdigest() == part['sha256']
                add(archive.parent / name, 'TRANSFER_REBUILDABLE_FROM_RETAINED_ZIP', part)
            assert not stream.read(1)
    for directory in FIXTURES:
        for path in (ROOT / directory).rglob('*.pt'):
            assert any(part.startswith('test_') for part in path.relative_to(ROOT / directory).parts)
            add(path, 'SYNTHETIC_PYTEST_CHECKPOINT')
    assert len({row['path'] for row in candidates}) == len(candidates)
    counts = Counter()
    sizes = Counter()
    for row in candidates:
        counts[row['group']] += 1
        sizes[row['group']] += row['bytes']
    result = dict(status='REVIEW_READY_NO_DELETION', candidates=candidates, rejected=rejected,
        groups={group:dict(files=counts[group],bytes=sizes[group]) for group in counts},
        total_candidate_bytes=sum(sizes.values()), files_deleted=0,
        limitations_vi=['Các bản chia cũ có thể dựng lại nguyên byte từ ZIP đầy đủ đang giữ.',
                        'Checkpoint pytest dùng dữ liệu tổng hợp A/B/C, không phải model Junyi/Grade10 nghiên cứu.',
                        'Nếu bỏ checkpoint pytest, binary UUID cũ không còn nguyên bản. Có thể chạy lại test tạo fixture mới, giữ source/log/config/SHA để audit.',
                        'Hai thư mục đang upload và toàn bộ inode liên quan được loại khỏi danh sách. Mọi model/input nghiên cứu chính giữ nguyên.',
                        'Đang chờ người dùng xác nhận danh sách dọn cụ thể trước khi xóa.'])
    save(HERE / 'STORAGE_CLEANUP_REVIEW02.json', result)
    sources = {HERE / 'STORAGE_CLEANUP_REVIEW02.json', HERE / 'DRIVE_UPLOAD_RECEIPT01.json',
               OLD / 'TRANSFER_PARTS_VERIFIED.json', OLD / 'drive-transfer-parts-20261116-01/DRIVE_PARTS_MANIFEST.json'}
    for directory in FIXTURES:
        sources.update((ROOT / directory).rglob('*.json'))
    for directory in ('research_tracking/runs/junyi-a1-compact-adapter-20261113-01',
                      'research_tracking/runs/junyi-a1-fastpath-t4-20261113-01'):
        sources.update(p for p in (ROOT / directory).iterdir() if p.is_file())
    refit = ROOT / 'research_tracking/runs/junyi-refit-pipeline-20261114-01'
    sources.update(refit / name for name in ('tests03.log', 'tests04.log', 'README.md'))
    sources.update(ROOT / 'tests/akt' / name for name in ('test_junyi_compact_context.py','test_junyi_graph_model.py','test_a1_vector_residual.py','test_research_graph_model.py','test_junyi_refit.py'))
    pins = {path.relative_to(ROOT).as_posix():dict(bytes=path.stat().st_size,sha256=sha(path)) for path in sources}
    target = OUT / 'STORAGE_CLEANUP_EVIDENCE.zip'
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for relative in sorted(pins):
            assert 'private' not in relative.lower().split('/')
            archive.write(ROOT / relative, relative)
        archive.writestr('PACKAGE_MANIFEST.json', json.dumps(dict(files=pins,raw_synthetic_binary_checkpoints_included=False),ensure_ascii=False,indent=2))
    with zipfile.ZipFile(target) as archive:
        for relative,pin in pins.items():
            with archive.open(relative) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == pin['sha256']
            assert sha(ROOT / relative) == pin['sha256']
    package=dict(path=target.relative_to(ROOT).as_posix(),bytes=target.stat().st_size,sha256=sha(target),files=len(pins),uploaded=False)
    save(HERE / 'STORAGE_SMALL_PACKAGE02.json',package)
    print(json.dumps(dict(groups=result['groups'],total_bytes=result['total_candidate_bytes'],rejected=len(rejected),package=package),ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
