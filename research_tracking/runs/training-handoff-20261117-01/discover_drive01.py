"""Đọc metadata Drive Sang để tái dùng archive đã có, không upload hoặc đổi quyền."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'))

def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from fetch_calibration_metadata01 import MetadataDrive,API,ACCOUNT,PARENT
    session=AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json')))
    drive=MetadataDrive(session)
    assert drive.get('/about',params={'fields':'user(emailAddress)'}).json()['user']['emailAddress']==ACCOUNT
    def listing(parent):
        rows=[];token=None
        while True:
            params=dict(q=f"'{parent}' in parents and trashed=false",pageSize=1000,
                fields='nextPageToken,files(id,name,mimeType,size,sha256Checksum,parents,owners(emailAddress))')
            if token:
                params['pageToken']=token
            data=drive.get('/files',params=params).json();rows.extend(data.get('files',[]))
            token=data.get('nextPageToken')
            if not token:
                return rows
    root=listing(PARENT)
    folders={'root':dict(id=PARENT,files=root)}
    chosen=[row for row in root if row['mimeType']=='application/vnd.google-apps.folder'
        and any(word in row['name'].lower() for word in ('model','artifact-offload','training','backup'))]
    for row in chosen:
        folders[row['id']]=dict(id=row['id'],name=row['name'],files=listing(row['id']))
    result=dict(status='SANG_DRIVE_EXISTING_FILES_METADATA_INDEXED',account=ACCOUNT,parent=PARENT,folders=folders)
    (B/'DRIVE_DISCOVERY01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ROOT_FOLDERS',[(row['name'],row['id']) for row in root if row['mimeType']=='application/vnd.google-apps.folder'],flush=True)
    for key,value in folders.items():
        if key!='root':
            print(value.get('name'),[(row['name'],row.get('size')) for row in value['files']],flush=True)

if __name__=='__main__':
    main()
