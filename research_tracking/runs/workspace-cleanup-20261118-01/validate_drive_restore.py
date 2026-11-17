"""Đọc lại gói nhỏ thật từ Drive và phục hồi một member qua công cụ mới."""
from pathlib import Path
import json,gzip,sys,hashlib
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/storage'))
from restore_workspace import restore_one,digest
data=json.loads((B/'BULK_DRIVE_DATA.json').read_text(encoding='utf-8'))
package=min(data['files'],key=lambda r:int(r['size']))
assert int(package['size'])<2*1024**2
probe=ROOT/'artifacts/akt/runtime/workspace-cleanup-20261118-01/drive-restore-probe'
downloads=probe/'downloads';downloads.mkdir(parents=True,exist_ok=True)
with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
    response=session.get('https://www.googleapis.com/drive/v3/files/'+package['id'],params={'alt':'media'},timeout=60)
    response.raise_for_status();raw=response.content
assert len(raw)==int(package['size']) and hashlib.sha256(raw).hexdigest()==package['sha256Checksum']
archive=downloads/(package['id']+'--'+package['name']);archive.write_bytes(raw)
with gzip.open(ROOT/'research_tracking/storage/20261118_STORAGE_INDEX.json.gz','rt',encoding='utf-8') as stream:index=json.load(stream)
member=min(package['members'],key=lambda r:r['bytes'])
row=next(r for r in index['files'] if r['sha256']==member['sha256'] and index['contents'][r['sha256']]['storage'].get('file_id')==package['id'])
target=probe/'project';target.mkdir(exist_ok=True)
assert restore_one(index,row['path'],downloads,target)
assert digest(target/row['path'])==row['sha256']
result=dict(status='ACTUAL_DRIVE_ARCHIVE_AND_REAL_MEMBER_RESTORE_SHA256_VERIFIED',download_archive_id=package['id'],download_bytes=len(raw),path=row['path'],bytes=row['bytes'],sha256=row['sha256'],probe_files=[str(archive.relative_to(ROOT)),str((target/row['path']).relative_to(ROOT))])
(B/'ACTUAL_RESTORE_ACCEPTANCE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('REAL_DRIVE_RESTORE',row['bytes'],'bytes verified',row['path'])
