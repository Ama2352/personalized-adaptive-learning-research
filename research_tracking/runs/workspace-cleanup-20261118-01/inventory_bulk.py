"""Hash phần output/cache nặng còn lại, tái dùng archive Drive đã có theo SHA."""
from pathlib import Path
import json,hashlib,os,concurrent.futures,collections,time
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent

def main():
    start=time.monotonic()
    protected=json.loads((B/'PROTECTED_BEFORE.json').read_text(encoding='utf-8'))
    keep={r['path'].lower() for r in protected['files']}
    model_dirs={str(Path(r['path']).parent).replace('\\','/').lower() for r in protected['files'] if '/model-export' in r['path']}
    old=json.loads((B/'STAGING_PLAN.json').read_text(encoding='utf-8'))
    excluded={r['path'].lower() for r in old['files']}
    if (B/'PACKAGE_COPIES_VERIFIED.json').exists():excluded.update(r['path'].lower() for r in json.loads((B/'PACKAGE_COPIES_VERIFIED.json').read_text(encoding='utf-8'))['files'])
    manifest=json.loads((ROOT/'research_tracking/runs/full-project-transfer-20261118-01/MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    known={r['sha256']:dict(kind='drive_file',file_id=r['file_id'],bytes=r['bytes'],name=r['name'],tier=r['tier']) for r in manifest['assets']}
    ids={r['drive_path']:r['file_id'] for r in manifest['assets']}
    for g in manifest['multipart_groups']:
        known[g['sha256']]=dict(kind='drive_multipart',name=g['archive_name'],bytes=g['bytes'],file_ids=[ids[p] for p in g['parts']])
    dedup=json.loads((B/'DEDUP_PACKAGE.json').read_text(encoding='utf-8'))
    for r in dedup['members']:
        known.setdefault(r['sha256'],dict(kind='dedup_member',member=r['path'],archive_sha256=dedup['sha256'],bytes=r['bytes']))
    full_prefixes=('artifacts/akt/staged/','artifacts/akt/local-tests/','artifacts/akt/colab/','artifacts/akt/synthetic/','artifacts/akt/tmp/','artifacts/akt/staged-archives/','artifacts/akt/pip-cache/','artifacts/akt/preflight/')
    binary={'.pt','.pth','.npz','.npy','.parquet','.sqlite','.db','.zip','.gz','.pkl','.pickle','.bin','.arrow','.jsonl','.tmp','.part','.whl','.tar','.zst','.7z'}
    candidates=[];errors=[];kept=collections.Counter()
    for base in (ROOT/'artifacts/akt',ROOT/'experiments/akt/results'):
        stack=[base]
        while stack:
            directory=stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        p=Path(entry.path);relative=p.relative_to(ROOT).as_posix();lower=relative.lower()
                        if entry.is_symlink() or getattr(entry,'is_junction',lambda:False)():continue
                        if entry.is_dir(follow_symlinks=False):
                            if any(s in {'.git','.venv','venv','__pycache__'} for s in p.relative_to(ROOT).parts):continue
                            if lower.startswith(('artifacts/akt/private','artifacts/akt/runtime/workspace-cleanup-20261118-01','artifacts/akt/runtime/project-transfer-20261118-01/cold-project','experiments/akt/results/drive-offload-duplicates-20261116-01/content')):continue
                            stack.append(p)
                        elif entry.is_file(follow_symlinks=False):
                            st=entry.stat(follow_symlinks=False)
                            if lower in keep or lower in excluded or any(lower.startswith(d+'/') for d in model_dirs):kept['protected_or_phase1']+=st.st_size;continue
                            name=p.name.lower()
                            if name.startswith('.env') or name in {'token.json','credentials.json','secrets.json','client_secret.json'} or name.endswith(('.pem','.p12','.pfx')):kept['credential_name_exclusion']+=st.st_size;continue
                            whole=lower.startswith(full_prefixes) or lower.startswith('artifacts/akt/runtime/')
                            if whole or p.suffix.lower() in binary or st.st_size>2*1024**2:
                                candidates.append((relative,st.st_size,st.st_mtime_ns))
                            else:kept['small_metadata_source']+=st.st_size
            except (PermissionError,FileNotFoundError) as e:errors.append(dict(path=directory.relative_to(ROOT).as_posix(),error=type(e).__name__))
    def pin(item):
        relative,size,mtime=item;p=ROOT/relative
        try:
            before=p.stat()
            with p.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            st=p.stat();assert st.st_size==size and st.st_mtime_ns==mtime and before.st_ino==st.st_ino
            reference=known.get(digest)
            if reference:assert reference['bytes']==size
            return dict(path=relative,bytes=size,sha256=digest,mtime_ns=mtime,file_id=st.st_ino,nlink=st.st_nlink,remote_reference=reference),None
        except Exception as e:return None,dict(path=relative,error=type(e).__name__)
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,(r,e) in enumerate(pool.map(pin,candidates),1):
            if r:rows.append(r)
            if e:errors.append(e)
            if i%4000==0:print('BULK_HASHED',i,'/',len(candidates),flush=True)
    unique={r['sha256']:r for r in rows}
    unknown={k:v for k,v in unique.items() if v['remote_reference'] is None}
    report=dict(status='BULK_INVENTORY_HASHED_PENDING_REMOTE_ACCEPTANCE',files=rows,errors=errors,kept_bytes=dict(kept),logical_bytes=sum(r['bytes'] for r in rows),unique_contents=len(unique),unique_bytes=sum(r['bytes'] for r in unique.values()),new_contents=len(unknown),new_content_bytes=sum(r['bytes'] for r in unknown.values()),seconds=time.monotonic()-start)
    (B/'BULK_INVENTORY.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('BULK_INVENTORY',len(rows),report['logical_bytes'],'bytes; NEW',len(unknown),report['new_content_bytes'],'errors',len(errors),flush=True)

if __name__=='__main__':main()
