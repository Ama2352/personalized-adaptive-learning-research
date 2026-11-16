"""Kiểm kê chỉ đọc, đối chiếu SHA và phân loại artifact theo công việc còn lại."""
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'experiments/akt/results/artifact-offload-20261116-01'
BINARY = {'.pt', '.npz', '.zip', '.sqlite', '.parquet', '.npy'}
PROTECTED = ('dataset/', 'artifacts/bkt_baseline/', 'venv/', '.wsl/', '.venv/', '.git/')


def sha_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def is_excluded(path):
    parts = path.split('/')
    return ('private' in parts or any(part.lower() in ('holdout', 'test') for part in parts)
            or path.startswith('experiments/akt/results/artifact-offload-20261116-01/'))


def classify(path):
    if path.startswith(PROTECTED):
        return 'PROTECTED', 'Vùng bảo vệ hoặc runtime local đang dùng'
    if path.startswith(('research_tracking/', 'docs/', 'src/', 'tests/', 'scripts/', 'paper1/', 'paper2/', 'third_party/', '_context/')):
        return 'KEEP_AUDIT_OR_SOURCE', 'Mã nguồn, protocol, báo cáo hoặc bằng chứng'
    if re.match(r'experiments/akt/results/model-export-a[0-3]-(refit|batch128)-\d{8}-\d{2}/', path):
        return 'KEEP_ACTIVE', 'Model refit hoặc checkpoint selection đã chọn, cùng support'
    if path.startswith('experiments/akt/results/model-export-20261112-01/'):
        return 'KEEP_ACTIVE', 'Model Grade10 selected và support cho phần vòng kín còn lại; có một A0Junyi lịch sử'
    if path.startswith(('experiments/gam_kt/results/', 'experiments/bkt_baseline/')):
        return 'KEEP_ACTIVE', 'Baseline lịch sử và dự đoán cần đối chiếu protocol; giữ nguyên phạm vi nguồn'
    if 'modal-junyi-a0-b128-h100-' in path:
        return 'KEEP_PENDING_A0_REPLAY', 'Giữ các epoch A0 để đối chiếu ranking validation batch1/128 còn mở'
    if (path.endswith('/state.pt')
            and re.search(r'outputs/junyi-a[0-3]-refit-20261114-01/checkpoints/refit-batch-epoch-', path)):
        return 'UNUSED_RESUME_FINISHED_RUN', 'Checkpoint giữa epoch hết nhiệm vụ phục hồi sau nghiệm thu refit9epoch; giữ metadata và bản lưu audit'
    if re.match(r'experiments/akt/results/junyi-a[0-3]-refit-20261114-01/', path):
        if '/checkpoints/refit-batch-epoch-' in path and path.endswith('/state.pt'):
            return 'UNUSED_RESUME_FINISHED_RUN', 'Checkpoint phục hồi của refit đã hoàn tất'
        return 'KEEP_ACTIVE', 'Output canonical được MODEL_INDEX/source_output và bộ kiểm model tham chiếu'
    if path.startswith(('artifacts/akt/window-cache/', 'artifacts/akt/graph-context-cache/',
                        'artifacts/akt/junyi-cohorts/', 'artifacts/akt/junyi-roles/',
                        'artifacts/akt/confidence/', 'artifacts/akt/dependencies/')):
        return 'KEEP_ACTIVE', 'Dữ liệu phái sinh, mapping, graph/confidence hoặc dependency còn dùng cho đánh giá và các model còn thiếu'
    if path.startswith('artifacts/akt/staged/'):
        return 'ARCHIVE_ONLY_STAGING', 'Snapshot training cũ phục vụ tái lập; workflow tiếp theo dùng cache/mapping gốc và snapshot mới theo phase'
    if 'model-export-a3-refit-recovery-' in path or 'colab-junyi-a3-refit-' in path:
        return 'ARCHIVE_ONLY_RECOVERY', 'Gói chuyển máy/phục hồi A3 đã hoàn thành; giữ một nguồn đầy đủ cho audit'
    if path.startswith(('artifacts/akt/runtime/', 'artifacts/akt/test-temp/', 'artifacts/akt/local-tests/')):
        return 'REVIEW_RUNTIME_OR_TEST', 'Cần đối chiếu runtime, source và log trước quyết định thu gọn'
    if path.startswith('experiments/'):
        if Path(path).suffix.lower() in ('.json', '.jsonl', '.log', '.xml', '.md', '.csv', '.svg', '.png'):
            return 'KEEP_AUDIT_OR_SOURCE', 'Giữ metadata, nhật ký và số liệu; không suy đây là rác'
        return 'ARCHIVE_ONLY_HISTORY', 'Artifact run lịch sử; giữ để tái lập, chưa cần nạp vào bước làm tiếp'
    return 'REVIEW', 'Chưa đủ bằng chứng để gán unused'


def collect():
    rows = []
    skipped = []
    errors = []
    stack = [ROOT]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path).relative_to(ROOT).as_posix()
                    if is_excluded(path + ('/' if entry.is_dir(follow_symlinks=False) else '')):
                        skipped.append(path)
                        continue
                    try:
                        if entry.is_symlink() or os.path.isjunction(entry.path):
                            skipped.append(path)
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            stat = entry.stat(follow_symlinks=False)
                            category, reason = classify(path)
                            rows.append(dict(path=path, bytes=stat.st_size, modified_ns=stat.st_mtime_ns,
                                category=category, reason=reason, sha256='', keeper='', keeper_sha256='',
                                source_category=category, action='Giữ nguyên trong lần kiểm này'))
                    except OSError as error:
                        errors.append(dict(path=path, error=str(error)))
        except OSError as error:
            errors.append(dict(path=str(directory), error=str(error)))
    return rows, skipped, errors


def hash_candidates(rows):
    by_size = defaultdict(list)
    for row in rows:
        if (row['category'] != 'PROTECTED' and row['bytes'] >= 1024**2
                and Path(row['path']).suffix.lower() in BINARY
                and row['path'].startswith(('artifacts/akt/', 'experiments/akt/', 'experiments/sakt/', 'experiments/gkt/'))):
            by_size[row['bytes']].append(row)
    targets = [row for size, group in by_size.items() for row in group
               if len(group) > 1 or (Path(row['path']).suffix.lower() == '.zip' and size >= 100 * 1024**2)
               or row['category'].startswith('UNUSED') or row['category'] in ('KEEP_ACTIVE', 'KEEP_PENDING_A0_REPLAY')]
    cache_path = OUTPUT / 'HASHES.jsonl'
    cached = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding='utf-8').splitlines():
            record = json.loads(line)
            cached[(record['path'], record['bytes'], record['modified_ns'])] = record['sha256']
    pending = []
    for row in targets:
        row['sha256'] = cached.get((row['path'], row['bytes'], row['modified_ns']), '')
        if not row['sha256']:
            pending.append(row)
    total = sum(row['bytes'] for row in pending)
    print(json.dumps(dict(event='HASH_START', files=len(pending), bytes=total)), flush=True)

    def calculate(row):
        path = ROOT / row['path']
        before = path.stat()
        assert (before.st_size, before.st_mtime_ns) == (row['bytes'], row['modified_ns'])
        digest = sha_file(path)
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        return digest

    done_bytes = 0
    last_print = time.monotonic()
    with cache_path.open('a', encoding='utf-8') as stream, ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(calculate, row): row for row in pending}
        for future in as_completed(futures):
            row = futures[future]
            row['sha256'] = future.result()
            stream.write(json.dumps({key: row[key] for key in ('path', 'bytes', 'modified_ns', 'sha256')}) + '\n')
            stream.flush()
            done_bytes += row['bytes']
            if time.monotonic() - last_print > 20:
                print(json.dumps(dict(event='HASH_PROGRESS', bytes=done_bytes, total_bytes=total)), flush=True)
                last_print = time.monotonic()


def keeper_score(row):
    category = row['category']
    order = {'KEEP_ACTIVE': 0, 'KEEP_PENDING_A0_REPLAY': 1, 'KEEP_AUDIT_OR_SOURCE': 2,
             'ARCHIVE_ONLY_HISTORY': 4, 'ARCHIVE_ONLY_RECOVERY': 5, 'ARCHIVE_ONLY_STAGING': 6}
    return order.get(category, 7), len(row['path']), row['path']


def flag_duplicates(rows):
    groups = defaultdict(list)
    for row in rows:
        if row['sha256']:
            groups[(row['bytes'], row['sha256'])].append(row)
    duplicates = []
    for (size, sha), group in groups.items():
        if len(group) < 2:
            continue
        keeper = min(group, key=keeper_score)
        if keeper['category'].startswith('UNUSED_'):
            keeper.update(category='ARCHIVE_ONLY_RESUME_WITNESS',
                          reason='Giữ một bản đại diện của nhóm checkpoint phục hồi trùng cho audit; hết nhiệm vụ resume')
        duplicates.append(dict(bytes_each=size, sha256=sha, keeper=keeper['path'], files=[row['path'] for row in group]))
        for row in group:
            if row is keeper:
                continue
            if row['category'].startswith(('KEEP_', 'PROTECTED')):
                continue
            row.update(category='UNUSED_VERIFIED_DUPLICATE', keeper=keeper['path'], keeper_sha256=sha,
                       reason='Đã hash thực tế, cùng kích thước và SHA với bản giữ; bản local trùng không cần cho workflow tiếp theo',
                       action='Chỉ thu gọn sau duyệt và relocation/reconstruction manifest nếu thuộc snapshot hoặc bundle đã đóng')
    return duplicates


def verify_transfer_parts(rows):
    by_path = {row['path']: row for row in rows}
    proofs = []
    for index in sorted((ROOT / 'experiments/akt/results').glob('model-export-a3-refit-recovery-*/DRIVE_PARTS*.json')):
        record = json.loads(index.read_text())
        archive = index.parent / 'COLAB_RESUME.zip'
        if not archive.is_file() or 'parts' not in record:
            continue
        archive_sha = sha_file(archive)
        if archive_sha != record.get('archive_sha256'):
            raise ValueError('Archive chuyển máy khác inventory')
        combined = hashlib.sha256()
        verified = []
        for part in record['parts']:
            name = part.get('name') or part.get('file')
            assert name and Path(name).name == name
            path = index.parent / name
            pin = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024**2), b''):
                    combined.update(chunk)
                    pin.update(chunk)
            assert pin.hexdigest() == part['sha256'] and path.stat().st_size == part['bytes']
            relative = path.relative_to(ROOT).as_posix()
            row = by_path[relative]
            row.update(category='UNUSED_VERIFIED_TRANSFER_PART', sha256=pin.hexdigest(),
                       keeper=archive.relative_to(ROOT).as_posix(), keeper_sha256=archive_sha,
                       reason='Phần upload cũ ghép lại đúngSHA của ZIP đầy đủ đang giữ; A3 đã refit hoàn tất',
                       action='Có thể bỏ bản chia phần sau duyệt; giữ ZIP đầy đủ và manifest')
            verified.append(relative)
        assert combined.hexdigest() == archive_sha
        proofs.append(dict(index=index.relative_to(ROOT).as_posix(), archive=archive.relative_to(ROOT).as_posix(),
                           archive_sha256=archive_sha, parts=verified, concatenation_matches=True))
    return proofs


def write_catalogs(rows, duplicates, parts, skipped, errors):
    fields = list(rows[0])
    paths = {}
    catalogs = {
        'UNUSED.csv': [row for row in rows if row['category'].startswith('UNUSED_')],
        'KEEP_ACTIVE.csv': [row for row in rows if row['category'] in ('KEEP_ACTIVE', 'KEEP_PENDING_A0_REPLAY')],
        'ARCHIVE_ONLY.csv': [row for row in rows if row['category'].startswith('ARCHIVE_ONLY')],
        'REVIEW.csv': [row for row in rows if row['category'].startswith('REVIEW')],
    }
    for name, records in catalogs.items():
        path = OUTPUT / name
        with path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(sorted(records, key=lambda row: (-row['bytes'], row['path'])))
        paths[name] = dict(path=path.relative_to(ROOT).as_posix(), files=len(records),
                           bytes=sum(row['bytes'] for row in records), sha256=sha_file(path))
    with (OUTPUT / 'INVENTORY.jsonl').open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    (OUTPUT / 'DUPLICATES.json').write_text(json.dumps(duplicates, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUTPUT / 'TRANSFER_PARTS_VERIFIED.json').write_text(json.dumps(parts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    totals = defaultdict(lambda: dict(files=0, bytes=0))
    for row in rows:
        totals[row['category']]['files'] += 1
        totals[row['category']]['bytes'] += row['bytes']
    existing = [dict(path=row['path'], bytes=row['bytes'], sha256=row['sha256'], category=row['category'],
                     note='Có thể upload nguyên file; nội dung archive có thể chứa IDs/labels Junyi, cần chọn nơi lưu phù hợp')
                for row in rows if Path(row['path']).suffix.lower() == '.zip' and row['bytes'] >= 100 * 1024**2
                and row['category'].startswith('ARCHIVE_ONLY') and row['sha256']]
    (OUTPUT / 'EXISTING_ARCHIVES_READY.json').write_text(json.dumps(existing, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary = dict(status='READ_ONLY_RETENTION_AUDIT_COMPLETE', observed_at_utc=datetime.now(timezone.utc).isoformat(),
        inventory_files=len(rows), inventory_bytes=sum(row['bytes'] for row in rows), categories=dict(totals),
        catalogs=paths, duplicate_groups=len(duplicates), verified_transfer_sets=len(parts),
        existing_archives_ready=len(existing), skipped_scopes=skipped, errors=errors,
        free_bytes=shutil.disk_usage(ROOT).free,
        limits_vi=['Không xóa/di chuyển bản gốc; UNUSED là danh mục quyết định, chưa là quyền xóa.',
                   'Bản trùng chỉ công bố khi đã hash thực tế. Các file hash cùng nội dung ở hai nơi KEEP vẫn được giữ để không gãy lineage.',
                   'Không chấm metrics hoặc đọc Holdout; vùngprivate/Holdout/Test và output audit được bỏ qua.',
                   'SHA thực tế tập trung binary>=1MiB có cùng kích thước, model/cache cần dùng và archive>=100MiB. File nhỏ chưa kiểm trùng toàn bộ.',
                   'ARCHIVE_ONLY vẫn là bằng chứng có giá trị. Các việc mới về sau có thể cần tải lại bản lưu trữ.',
                   'Các phase training đã nghiệm thu chỉ dùng để gán hết nhiệm vụ resume cho refit hiện tại; chưa coi các RQ hoàn tất.'])
    with (HERE / 'SUMMARY.json').open('w', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=summary['status'], catalogs=paths, categories=dict(totals), errors=len(errors)), ensure_ascii=False), flush=True)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert shutil.disk_usage(ROOT).free > 5 * 1024**3
    accepted = json.loads((ROOT / 'research_tracking/runs/junyi-refit-pipeline-20261114-01/exports-verified-a0-a1-a2-a3-portable-memory-cap-v1.json').read_text())
    assert accepted['status'] == 'PASS_EXISTING_REFIT_EXPORTS' and len(accepted['models']) == 4
    rows, skipped, errors = collect()
    print(json.dumps(dict(event='INVENTORY', files=len(rows), bytes=sum(row['bytes'] for row in rows))), flush=True)
    hash_candidates(rows)
    duplicates = flag_duplicates(rows)
    parts = verify_transfer_parts(rows)
    write_catalogs(rows, duplicates, parts, skipped, errors)


if __name__ == '__main__':
    main()
