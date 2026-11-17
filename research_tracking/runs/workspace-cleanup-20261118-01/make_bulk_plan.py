"""Đọc lại mọi tham chiếu Drive và lập allowlist chuyển lạnh phần workspace còn lại."""
from pathlib import Path
import json,threading,concurrent.futures,os,gzip
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
LOCAL=threading.local()

def get(file_id):
    if not hasattr(LOCAL,'s'):LOCAL.s=AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json')))
    r=LOCAL.s.get('https://www.googleapis.com/drive/v3/files/'+file_id,params={'fields':'id,name,size,sha256Checksum,parents,trashed,webViewLink'},timeout=60)
    r.raise_for_status();return r.json()

def main():
    inv=json.loads((B/'BULK_INVENTORY.json').read_text(encoding='utf-8'))
    packages=json.loads((B/'BULK_PACKAGES.json').read_text(encoding='utf-8'))
    uploaded=json.loads((B/'BULK_DRIVE_DATA.json').read_text(encoding='utf-8'))
    assert packages['status']=='ALL_NEW_BULK_CONTENT_ARCHIVES_VERIFIED' and uploaded['status']=='ALL_BULK_ARCHIVES_DRIVE_SHA256_VERIFIED'
    master=json.loads((ROOT/'research_tracking/runs/full-project-transfer-20261118-01/MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    old={r['file_id']:r for r in master['assets']}
    with gzip.open(ROOT/'research_tracking/storage/20261118_STORAGE_INDEX.json.gz','rt',encoding='utf-8') as stream:extra_drive=json.load(stream)['drive_files']
    dedup=json.loads((B/'DRIVE_ACCEPTANCE.json').read_text(encoding='utf-8'))
    excluded={r['sha256'] for r in packages['excluded']}
    blobs={r['sha256']:dict(kind='bulk_member',file_id=p['id'],archive_sha256=p['sha256Checksum'],member=r['path'],bytes=r['bytes']) for p in uploaded['files'] for r in p['members']}
    expectations={}
    for row in inv['files']:
        ref=row['remote_reference']
        if ref:
            if ref['kind']=='drive_file':expectations[ref['file_id']]=old[ref['file_id']]
            elif ref['kind']=='drive_multipart':
                for file_id in ref['file_ids']:expectations[file_id]=old[file_id]
            elif ref['kind']=='dedup_member':expectations[dedup['file']['id']]=dict(sha256=dedup['file']['sha256Checksum'],bytes=int(dedup['file']['size']))
            elif ref['kind']=='bulk_member':
                meta=extra_drive[ref['file_id']]
                expectations[ref['file_id']]=dict(sha256=meta['sha256Checksum'],bytes=int(meta['size']))
    for p in uploaded['files']:expectations[p['id']]=dict(sha256=p['sha256Checksum'],bytes=int(p['size']))
    def verify(pair):
        file_id,pin=pair;meta=get(file_id)
        assert not meta['trashed'] and meta['sha256Checksum']==pin['sha256'] and int(meta['size'])==pin['bytes']
        return meta
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:metas=list(pool.map(verify,expectations.items()))
    meta_by_id={r['id']:r for r in metas}
    files=[];relocations=[];kept=[]
    protected={r['path'].lower() for r in json.loads((B/'PROTECTED_BEFORE.json').read_text(encoding='utf-8'))['files']}
    for row in inv['files']:
        if row['sha256'] in excluded:kept.append(dict(path=row['path'],reason='POTENTIAL_SECRET_KEPT_LOCAL'));continue
        ref=row['remote_reference'] or blobs.get(row['sha256'])
        assert ref,row['path']
        ref=dict(ref)
        if ref['kind']=='dedup_member':ref['file_id']=dedup['file']['id']
        p=(ROOT/row['path']).resolve()
        assert p.is_relative_to(ROOT) and row['path'].lower() not in protected
        assert not row['path'].lower().startswith('artifacts/akt/private/')
        native=Path('\\\\?\\'+str(p)) if len(str(p))>=240 else p
        st=native.stat();assert st.st_size==row['bytes'] and st.st_mtime_ns==row['mtime_ns']
        files.append({k:v for k,v in row.items() if k!='remote_reference'}|dict(category='VERIFIED_COLD_WORKSPACE_FILE'))
        relocations.append(dict(path=row['path'],sha256=row['sha256'],bytes=row['bytes'],storage=ref))
    # Gói vận chuyển vừa tạo không cần giữ ở local sau khi Drive nghiệm thu.
    for p in packages['packages']:
        path=ROOT/p['path'];st=path.stat();remote=next(r for r in uploaded['files'] if r['name']==p['name'])
        assert remote['sha256Checksum']==p['sha256'] and int(remote['size'])==st.st_size==p['bytes']
        files.append(dict(path=p['path'],bytes=st.st_size,sha256=p['sha256'],mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink,category='UPLOADED_BULK_TRANSPORT'))
    cold=B/'COLD_COPY_INVENTORY.json'
    if cold.exists():
        fixture=json.loads(cold.read_text(encoding='utf-8'));assert fixture['status']=='OWN_COMPLETED_RESTORE_FIXTURE_INVENTORIED'
        files.extend(dict(**r,category='COMPLETED_COLD_RESTORE_FIXTURE') for r in fixture['files'])
    assert len({r['path'] for r in files})==len(files)
    remote_report=dict(status='ALL_BULK_REFERENCES_AND_NEW_ARCHIVES_VERIFIED',files=metas,drive_file_count=len(metas),excluded=kept)
    (B/'BULK_REMOTE_ACCEPTANCE.json').write_text(json.dumps(remote_report,ensure_ascii=False,indent=2),encoding='utf-8')
    plan=dict(status='READY_FOR_AUTHORIZED_BULK_OFFLOAD_UNLINK',root=str(ROOT.resolve()),allowed_roots=[str((ROOT/'artifacts/akt').resolve()),str((ROOT/'experiments/akt/results').resolve())],files=files,logical_bytes=sum(r['bytes'] for r in files))
    (B/'BULK_DELETE_PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    (B/'BULK_RELOCATION.json').write_text(json.dumps(dict(schema='KLTN_COLD_WORKSPACE_RELOCATION_V1',files=relocations,drive_files=meta_by_id,kept=kept,original_bytes_preserved=True),ensure_ascii=False,indent=2),encoding='utf-8')
    print('BULK_DELETE_READY',len(files),plan['logical_bytes'],'remote refs',len(metas),'excluded',len(kept),flush=True)

if __name__=='__main__':main()
