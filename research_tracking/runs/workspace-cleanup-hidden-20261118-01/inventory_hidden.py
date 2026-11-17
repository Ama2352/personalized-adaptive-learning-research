"""Kiểm các fixture sandbox trước đây không đọc được, không thay ACL."""
from pathlib import Path
import os,json,gzip,hashlib,concurrent.futures,collections
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
OLD=ROOT/'research_tracking/runs/workspace-cleanup-20261118-01'

def main():
    with gzip.open(ROOT/'research_tracking/storage/20261118_STORAGE_INDEX.json.gz','rt',encoding='utf-8') as stream:index=json.load(stream)
    protected=json.loads((OLD/'PROTECTED_BEFORE.json').read_text(encoding='utf-8'))
    keep={r['path'].lower() for r in protected['files']}
    errors=json.loads((OLD/'BULK_INVENTORY.json').read_text(encoding='utf-8'))['errors']
    paths=sorted({r['path'] for r in errors},key=len);roots=[]
    for path in paths:
        if not any(path==p or path.startswith(p+'/') for p in roots):roots.append(path)
    found={};failures=[]
    for relative in roots:
        assert relative.startswith('artifacts/akt/') and not relative.startswith('artifacts/akt/private/')
        normal=ROOT/relative;native=Path('\\\\?\\'+str(normal))
        if not native.exists():continue
        def onerror(error):failures.append(dict(path=relative,error=type(error).__name__))
        for directory,dirs,files in os.walk(native,followlinks=False,onerror=onerror):
            dirs[:]=[d for d in dirs if d not in {'.git','.venv','venv','private'} and not (Path(directory)/d).is_symlink() and not (Path(directory)/d).is_junction()]
            for name in files:
                p=Path(directory)/name;rel=(normal/p.relative_to(native)).relative_to(ROOT).as_posix()
                if rel.lower() in keep or p.is_symlink():continue
                if name.lower() in {'token.json','credentials.json','secrets.json','client_secret.json'} or name.lower().startswith('.env'):continue
                found[rel]=p
    def pin(pair):
        relative,p=pair
        try:
            before=p.stat()
            with p.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            st=p.stat();assert st.st_size==before.st_size and st.st_mtime_ns==before.st_mtime_ns
            known=index['contents'].get(digest)
            ref=known['storage'] if known else None
            if known:assert known['bytes']==st.st_size
            return dict(path=relative,bytes=st.st_size,sha256=digest,mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink,remote_reference=ref),None
        except Exception as error:return None,dict(path=relative,error=type(error).__name__)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for i,(row,error) in enumerate(pool.map(pin,found.items()),1):
            if row:rows.append(row)
            if error:failures.append(error)
            if i%15000==0:print('HIDDEN_HASHED',i,'/',len(found),flush=True)
    unique={r['sha256']:r for r in rows};new={k:r for k,r in unique.items() if r['remote_reference'] is None}
    result=dict(status='HIDDEN_FIXTURES_HASHED_PENDING_REMOTE_ACCEPTANCE',files=rows,errors=failures,logical_bytes=sum(r['bytes'] for r in rows),new_contents=len(new),new_content_bytes=sum(r['bytes'] for r in new.values()),roots=roots)
    (B/'BULK_INVENTORY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ('DRIVE_SEPARATION.json','DRIVE_ACCEPTANCE.json','PROTECTED_BEFORE.json'):(B/name).write_bytes((OLD/name).read_bytes())
    print('HIDDEN_INVENTORY',len(rows),result['logical_bytes'],'NEW',len(new),result['new_content_bytes'],'errors',len(failures),flush=True)

if __name__=='__main__':main()
