"""Đóng gói bản sao nguyên byte theo allowlist; nguồn và dữ liệu gốc giữ nguyên."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import time
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
OUT=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages'
EXCLUDED={'__pycache__','.git','.venv','venv','private','.pytest_cache'}
TEXT={'.py','.json','.jsonl','.md','.html','.csv','.txt','.ipynb','.toml','.ini','.cfg','.yml','.yaml','.ps1','.sh','.bat'}
SECRET=re.compile(rb'ya29\.[A-Za-z0-9_-]{20,}|Bearer [A-Za-z0-9._-]{25,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"(?:access_token|refresh_token|client_secret|token_secret)"\s*:\s*"[^"\r\n]{20,}"|[?&](?:access_token|refresh_token|client_secret|code)=[A-Za-z0-9_.%-]{24,}')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def write(name,value):
    (B/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def walk(relative):
    base=ROOT/relative
    if base.is_file():
        return [base]
    assert base.is_dir(),relative
    files=[]
    for directory,dirs,names in os.walk(base,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in EXCLUDED)
        if Path(directory)==B:
            dirs[:]=[];continue
        for name in sorted(names):
            path=Path(directory)/name
            if path.is_file() and not path.is_symlink() and path.suffix not in {'.pyc','.pyo'}:
                files.append(path)
    return files


def source_files():
    roots=('src','scripts','tests','docs','research_tracking','paper1','paper2','ref-papers','third_party','_context','notebooks')
    paths=[p for relative in roots for p in walk(relative)]
    paths.extend(p for p in ROOT.iterdir() if p.is_file())
    for model in (ROOT/'experiments').iterdir():
        if not model.is_dir():
            continue
        for item in model.iterdir():
            if item.name=='results':
                continue
            paths.extend(walk(item.relative_to(ROOT)))
    accepted=[];excluded=[]
    for path in sorted(set(paths)):
        relative=path.relative_to(ROOT).as_posix()
        if path.name.lower() in {'token.json','client_secret.json','modal.toml','.env'} or '/private/' in relative:
            excluded.append(dict(path=relative,reason='ACCOUNT_PRIVATE_FILENAME'));continue
        # Chỉ lưu tên file có dấu hiệu tài khoản; nội dung nhạy cảm giữ local.
        if path.suffix.lower() in TEXT:
            raw=path.read_bytes()
            if SECRET.search(raw):
                excluded.append(dict(path=relative,reason='ACCOUNT_SESSION_OR_CREDENTIAL_PATTERN'));continue
        accepted.append(path)
    write('SOURCE_EXCLUSIONS01.json',dict(files=excluded,rule='Giữ nguyên file gốc; loại khỏi bản sao chia sẻ và yêu cầu review nếu là source thực thi cần thiết.'))
    critical=[r for r in excluded if r['path'].startswith(('src/','scripts/','tests/','third_party/'))]
    if critical:
        raise RuntimeError('Cần rà source thực thi có dấu hiệu credential: '+','.join(r['path'] for r in critical))
    return accepted


def package_specs():
    inputs=json.loads((ROOT/'research_tracking/runs/full-project-handoff-audit-20261118-01/REQUIRED_INPUTS02.json').read_text())
    specs=[dict(name='01_SOURCE_VA_HO_SO_NGHIEN_CUU.zip',role='SOURCE',files=source_files()),
           dict(name='02_JUNYI_CSV_GOC.zip',role='RAW_DATA',files=[ROOT/'dataset/junyi_ProblemLog_original.csv'])]
    for group in inputs['groups']:
        if group['name']=='GRADE10_METHOD24_AND_CONDITIONS':
            continue # Gói đã nghiệm thu trên Drive, bản copy sẽ đi cùng master registry.
        specs.append(dict(name='03_'+group['name']+'.zip',role='REQUIRED_INPUT',
                          files=[ROOT/r['path'] for r in group['files']],expected={r['path']:r for r in group['files']}))
    specs.append(dict(name='04_SIMULATOR_TRACES.zip',role='RESEARCH_OUTPUT',files=walk('experiments/simulator/results')))
    specs.append(dict(name='05_JUNYI_COHORTS_CACHE.zip',role='READY_CACHE',files=[p for relative in (
        'artifacts/akt/junyi-cohorts/outer4-selected-full-20261112-03',
        'artifacts/akt/junyi-cohorts/outer4-calibration-full-20261117-01') for p in walk(relative)]))
    window=[]
    for relative in ('full-train80-20261112-02','full-selection10-staged-20261114-02','full-refit90-20261114-01'):
        window.extend(walk('artifacts/akt/window-cache/'+relative))
    window.extend(p for p in (ROOT/'artifacts/akt/window-cache').iterdir() if p.is_file() and p.suffix=='.json')
    specs.append(dict(name='06_WINDOW_CACHE_CHUAN.zip',role='READY_CACHE',files=window))
    specs.append(dict(name='07_GRAPH_CONTEXT_CACHE.zip',role='READY_CACHE',files=walk('artifacts/akt/graph-context-cache')))
    confidence=ROOT/'artifacts/akt/confidence/full-train80-20261114-02'
    specs.append(dict(name='08_CONFIDENCE_SQLITE_VA_MANIFEST.zip',role='CONFIDENCE_REPLAY_CACHE',
        files=[p for p in confidence.iterdir() if p.is_file() and (p.name=='rows.sqlite' or p.suffix=='.json')]))
    specs.append(dict(name='09_PREFLIGHT_VA_RUNTIME_MANIFEST.zip',role='PROVENANCE',files=walk('artifacts/akt/preflight')))
    return specs


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    specs=package_specs();records=[]
    write('PLAN01.json',dict(status='PACKAGING_EXACT_SOURCE_COPIES',
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        source_modified=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines(),
        packages=[dict(name=s['name'],role=s['role'],files=len(s['files']),source_bytes=sum(p.stat().st_size for p in s['files'])) for s in specs],
        decisions=['Tạo bản sao nén; giữ nguyên file nguồn.',
                   'Chọn một bộ cache chuẩn mỗi phase thay cho nhiều staged snapshot trùng.',
                   'Kèm CSV gốc, confidence spool và cache để người nhận đủ dữ liệu tái lập sâu.',
                   'Source snapshot là bytes hiện hành, giữ thay đổi notebook đang có; thông tin tài khoản giữ riêng.']))
    for spec in specs:
        path=OUT/spec['name'];manifest_path=B/(spec['name']+'.manifest.json')
        if path.exists() and manifest_path.exists():
            record=json.loads(manifest_path.read_text())
            assert path.stat().st_size==record['bytes'] and sha(path)==record['sha256']
            records.append(record);print('REUSED_VERIFIED_PACKAGE',spec['name'],flush=True);continue
        assert not path.exists(),'Archive chưa có manifest, giữ để chẩn đoán: '+str(path)
        rows=[];start=time.monotonic()
        print('PACKAGING',spec['name'],len(spec['files']),flush=True)
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            for source in sorted(set(spec['files'])):
                relative=source.relative_to(ROOT).as_posix();before=source.stat()
                digest=sha(source)
                expected=spec.get('expected',{}).get(relative)
                if expected:
                    assert before.st_size==expected['bytes'] and digest==expected['sha256'],relative
                archive.write(source,relative)
                after=source.stat()
                assert before.st_size==after.st_size and before.st_mtime_ns==after.st_mtime_ns,relative
                rows.append(dict(path=relative,bytes=before.st_size,sha256=digest))
            archive.writestr('HANDOFF_INVENTORY.json',json.dumps(dict(kind='EXACT_PROJECT_HANDOFF_V1',role=spec['role'],files=rows),ensure_ascii=False,indent=2).encode())
        with zipfile.ZipFile(path) as archive:
            assert len(archive.namelist())==len(set(archive.namelist()))
            for row in rows:
                with archive.open(row['path']) as stream:
                    actual=hashlib.file_digest(stream,'sha256').hexdigest()
                assert actual==row['sha256'],row['path']
                assert sha(ROOT/row['path'])==row['sha256'],row['path']
        record=dict(name=spec['name'],role=spec['role'],path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,
            sha256=sha(path),source_files=len(rows),source_bytes=sum(r['bytes'] for r in rows),
            seconds=time.monotonic()-start,member_inventory=rows,originals_rehashed_after_archive=True,
            archive_members_sha256_verified=True)
        write(manifest_path.name,record);records.append(record)
        write('PACKAGES01.json',dict(status='PACKAGING',packages=records))
        print('PACKAGE_VERIFIED',spec['name'],record['bytes'],round(record['seconds'],1),'seconds',flush=True)
    write('PACKAGES01.json',dict(status='ALL_PACKAGES_MEMBER_AND_SOURCE_SHA256_VERIFIED',packages=records))
    print('ALL_PACKAGES_READY',len(records),sum(r['bytes'] for r in records),flush=True)


if __name__=='__main__':
    main()
