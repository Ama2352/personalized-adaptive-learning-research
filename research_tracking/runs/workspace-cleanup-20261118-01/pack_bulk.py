"""Gom nội dung workspace chưa có Drive thành các gói theo SHA, không chứa private."""
from pathlib import Path
import json,hashlib,zipfile,re,time
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
WORK=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01/bulk-packages'
SECRET=re.compile(rb'"(?:access_token|refresh_token|client_secret)"\s*:\s*"[A-Za-z0-9._~-]{20,}"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer\s+ya29\.[A-Za-z0-9._~-]+')
PREFIX='WORKSPACE_CONTENT'

def main():
    inv=json.loads((B/'BULK_INVENTORY.json').read_text(encoding='utf-8'))
    unique={r['sha256']:r for r in inv['files'] if r['remote_reference'] is None}
    WORK.mkdir(parents=True,exist_ok=True)
    groups=[];group=[];size=0
    for row in sorted(unique.values(),key=lambda r:r['sha256']):
        if group and size+row['bytes']>512*1024**2:groups.append(group);group=[];size=0
        group.append(row);size+=row['bytes']
    if group:groups.append(group)
    packages=[];excluded=[]
    for number,rows in enumerate(groups,1):
        path=WORK/f'{PREFIX}_{number:03d}.zip'
        receipt=WORK/f'{PREFIX}_{number:03d}.json'
        if path.exists() and receipt.exists():
            package=json.loads(receipt.read_text(encoding='utf-8'));packages.append(package);continue
        assert not path.exists(),'Không ghi đè archive chưa nghiệm thu'
        members=[]
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            for row in rows:
                source=(ROOT/row['path']).resolve()
                assert source.is_relative_to(ROOT) and '/private/' not in source.as_posix().lower()
                if len(str(source))>=240:source=Path('\\\\?\\'+str(source))
                before=source.stat();assert before.st_size==row['bytes'] and before.st_mtime_ns==row['mtime_ns']
                if source.suffix.lower() in {'.json','.jsonl','.log','.txt','.yaml','.yml','.toml','.env'} and before.st_size<2*1024**2:
                    if SECRET.search(source.read_bytes()):
                        excluded.append(dict(path=row['path'],sha256=row['sha256'],reason='POTENTIAL_SECRET_KEPT_LOCAL'));continue
                with source.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
                assert digest==row['sha256'] and source.stat().st_mtime_ns==row['mtime_ns']
                arc='CONTENT/'+digest
                stored=source.suffix.lower() in {'.pt','.pth','.npz','.parquet','.zip','.gz','.whl','.7z','.zst','.pdf','.png','.jpg','.jpeg'}
                archive.write(source,arc,compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED,compresslevel=None if stored else 1)
                members.append(dict(path=arc,sha256=digest,bytes=row['bytes']))
            archive.writestr('MEMBERS.json',json.dumps(members,ensure_ascii=False,separators=(',',':')))
        with zipfile.ZipFile(path) as archive:
            for row in members:
                with archive.open(row['path']) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        package=dict(path=path.relative_to(ROOT).as_posix(),name=path.name,bytes=path.stat().st_size,sha256=digest,members=members)
        receipt.write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8')
        packages.append(package)
        (B/'BULK_PACKAGES.json').write_text(json.dumps(dict(status='PACKING',packages=packages,excluded=excluded),ensure_ascii=False,indent=2),encoding='utf-8')
        print('BULK_PACKED',number,'/',len(groups),path.stat().st_size,'bytes',flush=True)
    result=dict(status='ALL_NEW_BULK_CONTENT_ARCHIVES_VERIFIED',packages=packages,excluded=excluded,bytes=sum(p['bytes'] for p in packages))
    (B/'BULK_PACKAGES.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('BULK_PACKAGES_VERIFIED',len(packages),result['bytes'],'secret_exclusions',len(excluded),flush=True)

if __name__=='__main__':main()
