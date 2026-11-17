"""Kiểm kê và sao lưu nguyên byte đầu ra training; không nạp model hay chạy Test."""
from pathlib import Path
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
B = Path(__file__).resolve().parent
PRIVATE = ROOT/'artifacts/akt/private/drive-upload/training-handoff-20261117-01'
NAME = 'training-handoff-20261117-01'
EXCLUDE = {'__pycache__', 'pycache', 'tmp', 'scratch', '.git', '.venv', 'venv', 'private'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(name, data):
    (B/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def walk(relative):
    base = ROOT/relative
    if base.is_file():
        return [base]
    files = []
    for directory, dirs, names in os.walk(base, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE)
        for name in sorted(names):
            path = Path(directory)/name
            if path.is_file() and not path.is_symlink() and path.suffix not in {'.pyc', '.pyo'}:
                files.append(path)
    return files


def groups():
    result = {}
    for phase in ('cv_cpp', 'final_cpp', 'test_cpp', 'benchmark', 'cv_cpp_smoke'):
        result['BKT_'+phase] = walk('experiments/bkt_baseline/results/wsl_cpp/'+phase)
    result['GAM_KT_CV5'] = walk('experiments/gam_kt/results')
    for model in ('sakt', 'gkt'):
        result[model.upper()+'_ENGINEERING_ONLY'] = walk('experiments/'+model+'/results')
    result['PAPER2_LEGACY'] = walk('paper2/rivf2026_gam_kt_artifact_v20.zip')
    result['PAPER1_LEGACY'] = [p for p in walk('paper1') if p.suffix in {'.ipynb', '.pdf', '.md'}]
    confidence = ROOT/'artifacts/akt/confidence/full-train80-20261114-02'
    result['JUNYI_TRAIN80_CONFIDENCE_AUDIT'] = [p for p in confidence.iterdir() if p.is_file() and p.suffix in {'.json', '.jsonl'}]
    # OOF/fit ledger từng child được đóng riêng bằng confidence_outputs01.py.
    roots = ('src/', 'scripts/', 'tests/', 'third_party/', 'docs/', 'experiments/')
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    allowed = {'.py', '.md', '.json', '.toml', '.txt', '.yml', '.yaml', '.sh', '.ps1', '.patch', '.cfg', '.ini'}
    sources = []
    for relative in tracked:
        path = ROOT/relative
        if not relative or not path.is_file() or path.is_symlink() or any(p in EXCLUDE for p in path.parts):
            continue
        if '/results/' in relative or '/evidence/' in relative or '/artifacts/' in relative:
            continue
        if path.suffix.lower() in allowed and (relative.startswith(roots) or '/' not in relative):
            if path.stat().st_size <= 5*1024**2:
                sources.append(path)
    result['SOURCE_PROTOCOLS'] = sorted(set(sources))
    return result


def prepare():
    batches = []
    for name, paths in groups().items():
        assert paths, name
        rows = [dict(path=p.relative_to(ROOT).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(paths)]
        # Giữ mỗi phần dưới giới hạn stream, không tạo bản sao ZIP lớn trên ổ D.
        parts, current, size = [], [], 0
        for row in rows:
            if current and size+row['bytes'] > 180*1024**2:
                parts.append(current); current=[]; size=0
            assert row['bytes'] <= 180*1024**2, row['path']
            current.append(row); size += row['bytes']
        if current:
            parts.append(current)
        for number, part in enumerate(parts, 1):
            batches.append(dict(name=f'{name}_{number:02d}.zip', files=part,
                                source_bytes=sum(r['bytes'] for r in part)))
    inventory = dict(status='SOURCE_SHA256_INVENTORIED_BEFORE_TRANSFER', batches=batches,
                     exclusions=['Credentials, runtime, binary cache và thư mục tmp/scratch',
                                 'Dataset gốc và SQLite/cache đầu vào có thể tái dựng',
                                 'Model AKT đã sao lưu Drive được tái dùng bằng chỉ mục'],
                     historical_test='test_cpp chỉ sao chép nguyên byte, không nạp nhãn hoặc tái đánh giá',
                     source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip())
    write('PACKAGE_INVENTORY01.json', inventory)
    print('PREPARED', len(batches), 'archives', sum(len(b['files']) for b in batches), 'files',
          sum(b['source_bytes'] for b in batches), 'bytes', flush=True)
    return inventory


def archive(batch):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as output:
        for row in batch['files']:
            raw = (ROOT/row['path']).read_bytes()
            assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'], row['path']
            info = zipfile.ZipInfo(row['path'], (1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, raw, compresslevel=3)
        output.writestr('HANDOFF_MEMBER_INVENTORY.json', json.dumps(batch, ensure_ascii=False, indent=2).encode())
    raw = buffer.getvalue()
    assert len(raw) <= 256*1024**2
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        assert check.testzip() is None
        for row in batch['files']:
            assert hashlib.sha256(check.read(row['path'])).hexdigest()==row['sha256']
    return raw


def blocks(raw):
    for offset in range(0, len(raw), 8*1024**2):
        yield raw[offset:offset+8*1024**2]


def upload(inventory, receipt_name='NEW_ARCHIVES_DRIVE01.json'):
    sys.path.insert(0, str(ROOT/'scripts/akt'))
    sys.path.insert(0, str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    from drive_stream_upload import upload_stream
    import publish_snapshot as pub
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    pub.NAME = NAME
    receipts = []
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        folder = pub.folder(session)
        write('DRIVE_FOLDER01.json', folder)
        for batch in inventory['batches']:
            raw = archive(batch)
            digest = hashlib.sha256(raw).hexdigest()
            plan_sha = hashlib.sha256(json.dumps(batch, sort_keys=True).encode()).hexdigest()
            plan = dict(folder_id=folder['id'], name=batch['name'], total_bytes=len(raw), source_plan_sha256=plan_sha)
            receipt = upload_stream(session, plan, lambda:blocks(raw), PRIVATE/(batch['name']+'.state.json'))
            assert receipt['sha256']==digest
            # Đọc metadata độc lập sau upload và kiểm lại toàn bộ inventory nguồn.
            meta = pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],
                params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=60))
            assert meta['sha256Checksum']==digest and meta['parents']==[folder['id']]
            assert meta['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
            for row in batch['files']:
                assert sha(ROOT/row['path'])==row['sha256'], row['path']
            receipts.append(dict(**meta, member_count=len(batch['files']), source_bytes=batch['source_bytes'],
                                 source_rehashed_after_transfer=True, zip_members_verified=True))
            write(receipt_name, dict(status='UPLOADING', folder=folder, files=receipts))
            print('VERIFIED', batch['name'], len(raw), len(batch['files']), flush=True)
        write(receipt_name, dict(status='ALL_NEW_ARCHIVES_SERVER_SHA256_VERIFIED', folder=folder, files=receipts))
        print('ALL_UPLOADED', folder['webViewLink'], flush=True)


if __name__ == '__main__':
    if '--prepare' in sys.argv:
        prepare()
    if '--upload' in sys.argv:
        upload(json.loads((B/'PACKAGE_INVENTORY01.json').read_text(encoding='utf-8')))
