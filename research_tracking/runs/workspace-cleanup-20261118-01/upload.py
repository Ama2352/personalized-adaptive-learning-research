"""Upload archive audit có thể tiếp tục; kiểm metadata Drive trước cho phép dọn."""
from pathlib import Path
import json,sys,hashlib,time
from contextlib import redirect_stdout
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/akt'))
from drive_resumable_upload import Uploader,atomic_json,single_writer
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

def main():
    package=json.loads((B/'DEDUP_PACKAGE.json').read_text(encoding='utf-8'))
    assert package['status']=='ARCHIVE_AND_ALL_MEMBERS_VERIFIED'
    path=(ROOT/package['path']).resolve()
    with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==package['sha256']
    master=json.loads((ROOT/'research_tracking/runs/full-project-transfer-20261118-01/DRIVE_MASTER01.json').read_text(encoding='utf-8'))
    private=ROOT/'artifacts/akt/private/drive-upload/workspace-cleanup-20261118-01'
    private.mkdir(parents=True,exist_ok=True)
    evidence=B/'upload';evidence.mkdir(exist_ok=True)
    with single_writer(private/'upload.lock'),AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        api='https://www.googleapis.com/drive/v3'
        account=session.get(api+'/about',params={'fields':'user(emailAddress),storageQuota'},timeout=60)
        account.raise_for_status();info=account.json()
        assert info['user']['emailAddress']=='honguyenminhsang2005@gmail.com'
        quota=info.get('storageQuota',{})
        if quota.get('limit'):assert int(quota['limit'])-int(quota.get('usage',0))>package['bytes']
        atomic_json(B/'DRIVE_QUOTA_BEFORE.json',{'storageQuota':quota})
        plan=dict(source=str(path.parent),parent_id=master['id'],account=info['user']['emailAddress'],
                  folder_name='05_LUU_TRU_DON_DEP_20261118',bytes=package['bytes'],
                  files=[dict(path=path.name,bytes=package['bytes'],sha256=package['sha256'],mtime_ns=path.stat().st_mtime_ns)])
        atomic_json(evidence/'PLAN.json',plan)
        with (evidence/'console.log').open('a',encoding='utf-8') as log,redirect_stdout(log):
            Uploader(session,plan,private/'state.json',evidence,chunk_bytes=32*1024**2,retries=5).run()
        receipts=json.loads((evidence/'RECEIPTS.json').read_text(encoding='utf-8'));receipt=receipts[0]
        result=session.get(api+'/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),trashed,webViewLink'},timeout=60)
        result.raise_for_status();meta=result.json()
        assert not meta['trashed'] and meta['sha256Checksum']==package['sha256'] and int(meta['size'])==package['bytes']
        assert meta['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
        folder=session.get(api+'/files/'+meta['parents'][0],params={'fields':'id,name,parents,trashed,webViewLink'},timeout=60)
        folder.raise_for_status();folder_meta=folder.json()
        assert master['id'] in folder_meta['parents'] and not folder_meta['trashed']
        atomic_json(B/'DRIVE_ACCEPTANCE.json',dict(status='REMOTE_ARCHIVE_SHA256_SIZE_OWNER_PARENT_VERIFIED',file=meta,folder=folder_meta,source=package['path'],member_count=len(package['members'])))
        print('DRIVE_ACCEPTED',meta['size'],meta['webViewLink'],flush=True)

if __name__=='__main__':
    try:main()
    except Exception as error:
        print('STOPPED',type(error).__name__,'Giữ file gốc và state, không xóa khi chưa có nghiệm thu.',flush=True)
        raise SystemExit(1)
