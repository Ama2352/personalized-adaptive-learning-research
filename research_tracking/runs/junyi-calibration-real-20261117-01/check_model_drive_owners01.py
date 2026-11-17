"""Chỉ GET metadata ownership qua Drive Sang, không tải payload hoặc gọi Modal."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
API = 'https://www.googleapis.com/drive/v3'
ACCOUNT = 'honguyenminhsang2005@gmail.com'


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    parser = argparse.ArgumentParser()
    parser.add_argument('--history',action='store_true')
    args = parser.parse_args()
    if args.history:
        coverage = json.loads((HERE/'MODEL_DRIVE_COVERAGE01.json').read_text(encoding='utf-8'))
        wanted = {row['archive_sha256'] for row in coverage['latest_checkpoints']}
        relocation = json.loads((ROOT/'research_tracking/runs/history-cleanup-20261117-01/RELOCATION_MANIFEST.json').read_text())
        inputs = [dict(id=row['remote_id'],name=row['remote_path'],expected_bytes=row['bytes'],expected_sha256=row['sha256'])
                  for row in relocation['groups'] if row['sha256'] in wanted]
        destination = HERE/'MODEL_DRIVE_HISTORY_OWNERS01.json'
    else:
        receipt = json.loads((ROOT/'research_tracking/runs/artifact-retention-audit-20261116-01/DRIVE_UPLOAD_RECEIPT01.json').read_text())
        inputs = [dict(id=row['id'],name=row['name'],expected_bytes=row['bytes'],expected_sha256=row['sha256'])
                  for row in receipt['files']]
        inputs.append(dict(id='1GlPhrWOLwFNeUiv1unYaEATypWmV9_Vy',name='CURRENT_INPUT_ZIP',
            expected_bytes=134525060,expected_sha256='a34cee8e961baf7056e8f16159d2b9a25afcca72f3c19b3a37bd0d711aab2d6a'))
        destination = HERE/'MODEL_DRIVE_OWNERS01.json'
    credentials = Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'),
        ['https://www.googleapis.com/auth/drive'])
    rows=[]
    with AuthorizedSession(credentials) as session:
        response=session.get(API+'/about',params={'fields':'user(emailAddress)'},timeout=30,allow_redirects=False)
        if response.status_code!=200 or response.json()['user']['emailAddress'].lower()!=ACCOUNT:
            raise ValueError('Drive account mismatch')
        for entry in inputs:
            response=session.get(API+'/files/'+entry['id'],params={
                'fields':'id,name,owners(emailAddress,displayName),parents,size,sha256Checksum,trashed'},
                timeout=30,allow_redirects=False)
            if response.status_code!=200:
                rows.append(dict(entry,status='METADATA_UNAVAILABLE',http_status=response.status_code))
                continue
            metadata=response.json()
            if (metadata.get('trashed') or int(metadata.get('size',-1))!=entry['expected_bytes']
                    or metadata.get('sha256Checksum')!=entry['expected_sha256']):
                raise ValueError('Existing Drive metadata pin mismatch')
            owners=[owner.get('emailAddress') for owner in metadata.get('owners',[])]
            rows.append(dict(entry,status='DRIVE_METADATA_SHA_VERIFIED',owners=owners,
                owned_by_sang=ACCOUNT in owners,parents=metadata.get('parents',[]),
                drive_url='https://drive.google.com/file/d/'+entry['id']+'/view'))
    result=dict(status='READONLY_DRIVE_OWNER_METADATA_CHECK',authenticated_account=ACCOUNT,
        files=rows,payload_downloaded=False,modal_called=False,
        limits_vi='Owner được đọc trực tiếp từ metadata, tách khỏi tài khoản uploader lịch sử. '
        'Chưa copy/chuyển quyền sở hữu hoặc xóa file.')
    with destination.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(status=result['status'],files=len(rows),owned_by_sang=sum(row.get('owned_by_sang',False) for row in rows),
        other_owner=sum(row.get('status')=='DRIVE_METADATA_SHA_VERIFIED' and not row.get('owned_by_sang',False) for row in rows),
        unavailable=sum(row['status']=='METADATA_UNAVAILABLE' for row in rows))))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('Owner metadata check stopped: '+type(error).__name__) from None
