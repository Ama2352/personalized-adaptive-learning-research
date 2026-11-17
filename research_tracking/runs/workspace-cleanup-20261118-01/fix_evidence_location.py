"""Sửa parent cũ của gói hồ sơ đã upload; giữ nguyên byte, không upload trùng."""
from pathlib import Path
import json,hashlib,zipfile
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
path=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01/KLTN_HO_SO_DON_DEP_20261118.zip'
with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
receipt=json.loads((B/'evidence_upload/RECEIPTS.json').read_text(encoding='utf-8'))[0]
remote=json.loads((B/'DRIVE_ACCEPTANCE.json').read_text(encoding='utf-8'))
separation=json.loads((B/'DRIVE_SEPARATION.json').read_text(encoding='utf-8'))
api='https://www.googleapis.com/drive/v3';fields='id,name,size,sha256Checksum,parents,trashed,webViewLink,mimeType'
with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as s:
    def request(method,route,**kwargs):
        r=s.request(method,api+route,timeout=60,**kwargs);r.raise_for_status();return r.json()
    before=request('GET','/files/'+receipt['file_id'],params={'fields':fields})
    assert not before['trashed'] and before['sha256Checksum']==digest and int(before['size'])==path.stat().st_size
    target=request('GET','/files/'+remote['folder']['id'],params={'fields':fields})
    assert separation['archive_folder']['id'] in target['parents'] and not target['trashed']
    prior_parent=before['parents'][0]
    if target['id'] not in before['parents']:
        after=request('PATCH','/files/'+before['id'],params={'addParents':target['id'],'removeParents':prior_parent,'fields':fields},json={})
    else:after=before
    assert after['sha256Checksum']==digest and target['id'] in after['parents']
    duplicate=None
    if prior_parent!=target['id']:
        parent=request('GET','/files/'+prior_parent,params={'fields':fields})
        children=request('GET','/files',params={'q':"'%s' in parents and trashed=false"%prior_parent,'fields':'files(id)'})['files']
        assert parent['name']==target['name'] and separation['handoff_folder']['id'] in parent['parents'] and not children
        duplicate=request('PATCH','/files/'+prior_parent,params={'fields':fields},json={'trashed':True})
    members=[]
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            with archive.open(info) as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
            members.append(dict(path=info.filename,bytes=info.file_size,sha256=sha))
    result=dict(status='CLEANUP_EVIDENCE_ARCHIVE_REMOTE_SHA256_VERIFIED',file=after,folder=target,members=members,local_archive=path.relative_to(ROOT).as_posix(),stale_parent_fix=dict(before=before,after=after,empty_agent_folder_trashed=duplicate),limitation='Gói được đóng trước commit; source cuối và Git bundle được xuất bản riêng theo commit.')
    (B/'EVIDENCE_DRIVE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('EVIDENCE_RELOCATED_AND_VERIFIED',after['webViewLink'],path.stat().st_size,flush=True)
