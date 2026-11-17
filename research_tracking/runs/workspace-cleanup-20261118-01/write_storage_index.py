"""Tạo chỉ mục phục hồi gọn cho source/output lịch sử đã chuyển lạnh."""
from pathlib import Path
import json,gzip,hashlib
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent

def main():
    bulk=json.loads((B/'BULK_RELOCATION.json').read_text(encoding='utf-8'))
    staging=json.loads((B/'STAGING_PLAN.json').read_text(encoding='utf-8'))
    dedup=json.loads((B/'DEDUP_PACKAGE.json').read_text(encoding='utf-8'))
    remote=json.loads((B/'DRIVE_ACCEPTANCE.json').read_text(encoding='utf-8'))
    separation=json.loads((B/'DRIVE_SEPARATION.json').read_text(encoding='utf-8'))
    files=[];contents={};drive=dict(bulk['drive_files'])
    drive[remote['file']['id']]=remote['file']
    members={r['sha256']:r for r in dedup['members']}
    for r in bulk['files']:
        contents.setdefault(r['sha256'],dict(bytes=r['bytes'],storage=r['storage']))
        files.append(dict(path=r['path'],bytes=r['bytes'],sha256=r['sha256']))
    for r in staging['files']:
        if r['sha256'] not in contents:
            member=members[r['sha256']]
            contents[r['sha256']]=dict(bytes=r['bytes'],storage=dict(kind='dedup_member',file_id=remote['file']['id'],archive_sha256=remote['file']['sha256Checksum'],member=member['path']))
        files.append(dict(path=r['path'],bytes=r['bytes'],sha256=r['sha256'],mtime_ns=r['mtime_ns']))
    hidden=ROOT/'research_tracking/runs/workspace-cleanup-hidden-20261118-01/BULK_RELOCATION.json'
    if hidden.exists():
        extra=json.loads(hidden.read_text(encoding='utf-8'))
        drive.update(extra['drive_files'])
        for r in extra['files']:
            contents.setdefault(r['sha256'],dict(bytes=r['bytes'],storage=r['storage']))
            files.append(dict(path=r['path'],bytes=r['bytes'],sha256=r['sha256']))
    assert len({r['path'] for r in files})==len(files)
    result=dict(schema='KLTN_STORAGE_INDEX_V1',as_of='2026-11-18',archive_folder=separation['archive_folder'],handoff_folder=separation['handoff_folder'],files=files,contents=contents,drive_files=drive,limits=['Bản tạm/cold-project và ZIP vận chuyển đã xóa không nằm trong chỉ mục phục hồi vì dựng lại được.','Dữ liệu/model gọn vẫn local và bộ bàn giao ready có manifest riêng.'])
    out=ROOT/'research_tracking/storage';out.mkdir(exist_ok=True)
    path=out/'20261118_STORAGE_INDEX.json.gz'
    with path.open('wb') as stream:
        with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as compressed:compressed.write(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode())
    summary=dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,paths=len(files),unique_contents=len(contents),drive_files=len(drive))
    (B/'STORAGE_INDEX_ACCEPTANCE.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print('STORAGE_INDEX',summary,flush=True)

if __name__=='__main__':main()
