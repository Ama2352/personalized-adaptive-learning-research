"""Hash lại bản trùng staging và đóng gói nội dung lịch sử; chưa xóa."""
from pathlib import Path
import csv,json,hashlib,concurrent.futures,threading,time,zipfile
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
WORK=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01'
OLD=ROOT/'experiments/akt/results/drive-offload-duplicates-20261116-01'
WORK.mkdir(parents=True,exist_ok=True)
LOCK=threading.Lock();CACHE={}

def sha(path):
    before=path.stat()
    key=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
    with LOCK:value=CACHE.get(key) if before.st_ino else None
    if value is None:
        with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
    after=path.stat()
    assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),'File thay đổi khi hash'
    if before.st_ino:
        with LOCK:CACHE[key]=value
    return value,after

def validate(row):
    source=(ROOT/row['path']).resolve();keeper=(ROOT/row['keeper']).resolve()
    assert source.is_relative_to((ROOT/'artifacts/akt/staged').resolve())
    assert keeper.is_relative_to(ROOT) and not keeper.is_relative_to((ROOT/'artifacts/akt/staged').resolve())
    assert not source.is_symlink() and not keeper.is_symlink()
    a,st=sha(source);b,kst=sha(keeper)
    assert a==b==row['sha256']==row['keeper_sha256'] and st.st_size==kst.st_size==int(row['bytes'])
    manifest=(ROOT/row['snapshot_manifest']).resolve()
    assert manifest.is_file() and manifest.is_relative_to((ROOT/'artifacts/akt/staged').resolve())
    # INPUTS.json gắn SHA nguồn với đúng đường dẫn bên trong snapshot.
    with LOCK:md=CACHE.get(str(manifest))
    if md is None:
        md=json.loads(manifest.read_text(encoding='utf-8'))
        with LOCK:CACHE[str(manifest)]=md
    key=source.relative_to(manifest.parent/'project').as_posix()
    pin=md['files'][key]
    assert pin['sha256']==a and pin['bytes']==st.st_size
    return dict(path=row['path'],keeper=row['keeper'],bytes=st.st_size,sha256=a,
                mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink,
                keeper_file_id=kst.st_ino,keeper_mtime_ns=kst.st_mtime_ns,
                snapshot_manifest=row['snapshot_manifest'],snapshot_member=key)

def main():
    started=time.monotonic()
    with (ROOT/'experiments/akt/results/artifact-offload-20261116-01/RETENTION_REVIEW02.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=[r for r in csv.DictReader(stream) if r['category']=='UNUSED_VERIFIED_DUPLICATE' and r['path'].startswith('artifacts/akt/staged/')]
    results=[];failed=[]
    def safe(row):
        try:return validate(row),None
        except Exception as error:return None,dict(path=row['path'],error=type(error).__name__,reason=str(error))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,(valid,error) in enumerate(pool.map(safe,rows),1):
            if valid:results.append(valid)
            if error:failed.append(error)
            if i%2000==0:print('HASHED',i,'/',len(rows),'FAILED',len(failed),flush=True)
    plan=dict(status='HASH_VERIFIED_PENDING_DRIVE_BACKUP',authorization_vi='18/11 người dùng yêu cầu upload phần lớn, xóa bản trùng hoặc không có giá trị; giữ artifact nghiên cứu gốc.',
              files=results,failed=failed,logical_bytes=sum(r['bytes'] for r in results),seconds=time.monotonic()-started)
    (B/'STAGING_PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    print('STAGING_VERIFIED',len(results),plan['logical_bytes'],'FAILED',len(failed),flush=True)
    # Gói dedup đã có manifest2219nội dung; giữ cả ánh xạ/metadata lịch sử.
    manifest=json.loads((OLD/'MANIFEST.json').read_text(encoding='utf-8'))
    members=[]
    archive_path=WORK/'KLTN_DEDUP_AUDIT_20261118.zip'
    assert not archive_path.exists(),'Không ghi đè archive đã tạo'
    with zipfile.ZipFile(archive_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as archive:
        for i,row in enumerate(manifest['content_files'],1):
            assert '/private/' not in row['keeper'].replace('\\','/')
            path=(OLD/row['path']).resolve()
            assert path.is_relative_to(OLD.resolve())
            digest,stat=sha(path)
            assert digest==row['sha256'] and stat.st_size==row['bytes']
            arc='drive-offload-duplicates-20261116-01/'+row['path']
            archive.write(path,arc)
            members.append(dict(path=arc,bytes=stat.st_size,sha256=digest))
            if i%400==0:print('PACKED_DEDUP',i,'/',len(manifest['content_files']),flush=True)
        for name in ('MANIFEST.json','AUDIT_METADATA.zip','00_DOC_TRUOC.md','audit_backup.py'):
            path=OLD/name;digest,stat=sha(path);arc='drive-offload-duplicates-20261116-01/'+name
            archive.write(path,arc);members.append(dict(path=arc,bytes=stat.st_size,sha256=digest))
        for name in ('STAGING_PLAN.json',):
            path=B/name;digest,stat=sha(path);arc='workspace-cleanup-20261118-01/'+name
            archive.write(path,arc);members.append(dict(path=arc,bytes=stat.st_size,sha256=digest))
    # Đọc lại từng member để kiểm archive trước upload.
    with zipfile.ZipFile(archive_path) as archive:
        for row in members:
            with archive.open(row['path']) as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            assert digest==row['sha256'] and archive.getinfo(row['path']).file_size==row['bytes']
    digest,stat=sha(archive_path)
    package=dict(status='ARCHIVE_AND_ALL_MEMBERS_VERIFIED',path=archive_path.relative_to(ROOT).as_posix(),bytes=stat.st_size,sha256=digest,
                 logical_content_bytes=sum(r['bytes'] for r in members),members=members)
    (B/'DEDUP_PACKAGE.json').write_text(json.dumps(package,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PACKAGE_VERIFIED',stat.st_size,digest,'SECONDS',time.monotonic()-started,flush=True)

if __name__=='__main__':main()
