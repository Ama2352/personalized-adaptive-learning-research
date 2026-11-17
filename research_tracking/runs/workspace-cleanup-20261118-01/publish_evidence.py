"""Lưu hồ sơ dọn và hướng dẫn phục hồi lên cùng folder Drive, không sửa manifest cũ."""
from pathlib import Path
import json,hashlib,sys,zipfile
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
WORK=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01'
sys.path.insert(0,str(ROOT/'scripts/akt'))
from drive_resumable_upload import Uploader,atomic_json,single_writer
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

def main():
    after=json.loads((B/'AFTER_VERIFICATION.json').read_text(encoding='utf-8'))
    assert not after['kept_on_error']
    remote=json.loads((B/'DRIVE_ACCEPTANCE.json').read_text(encoding='utf-8'))
    protected=json.loads((B/'PROTECTED_AFTER.json').read_text(encoding='utf-8'))
    assert protected['count']==805
    hidden=ROOT/'research_tracking/runs/workspace-cleanup-hidden-20261118-01'
    assert json.loads((hidden/'HIDDEN_SUMMARY.json').read_text(encoding='utf-8'))['errors']==0
    path=WORK/'KLTN_HO_SO_DON_DEP_20261118.zip'
    assert not path.exists()
    inventory=[]
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for bundle in (B,hidden):
            files=[p for p in bundle.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('MANIFEST.json','EVIDENCE_DRIVE.json')]
            for p in files:
                raw=p.read_bytes();relative=bundle.name+'/'+p.relative_to(bundle).as_posix()
                archive.writestr(relative,raw)
                inventory.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        catalog=ROOT/'research_tracking/storage/20261118_STORAGE_INDEX.json.gz'
        raw=catalog.read_bytes();relative='shared/research_tracking/storage/'+catalog.name
        archive.writestr(relative,raw);inventory.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    with zipfile.ZipFile(path) as archive:
        for row in inventory:
            with archive.open(row['path']) as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    st=path.stat();parent=json.loads((B/'DRIVE_SEPARATION.json').read_text(encoding='utf-8'))['archive_folder']['id']
    plan=dict(source=str(WORK.resolve()),parent_id=parent,account='honguyenminhsang2005@gmail.com',folder_name=remote['folder']['name'],bytes=st.st_size,
              files=[dict(path=path.name,bytes=st.st_size,sha256=digest,mtime_ns=st.st_mtime_ns)])
    evidence=B/'evidence_upload';evidence.mkdir(exist_ok=True)
    private=ROOT/'artifacts/akt/private/drive-upload/workspace-cleanup-20261118-01'
    with single_writer(private/'evidence.lock'),AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        with (evidence/'console.log').open('a',encoding='utf-8') as log,redirect_stdout(log):
            Uploader(session,plan,private/'evidence-state.json',evidence,retries=5).run()
        receipt=json.loads((evidence/'RECEIPTS.json').read_text(encoding='utf-8'))[0]
        response=session.get('https://www.googleapis.com/drive/v3/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,trashed,webViewLink'},timeout=60)
        response.raise_for_status();meta=response.json()
        assert not meta['trashed'] and meta['sha256Checksum']==digest and int(meta['size'])==st.st_size and remote['folder']['id'] in meta['parents']
    atomic_json(B/'EVIDENCE_DRIVE.json',dict(status='CLEANUP_EVIDENCE_ARCHIVE_REMOTE_SHA256_VERIFIED',file=meta,members=inventory,local_archive=path.relative_to(ROOT).as_posix()))
    print('EVIDENCE_DRIVE',meta['webViewLink'],st.st_size,flush=True)

if __name__=='__main__':main()
