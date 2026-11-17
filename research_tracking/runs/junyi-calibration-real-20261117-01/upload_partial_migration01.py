"""Stream checkpoint raw Colab sang Drive, không tạo binary trên local."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'scripts/akt'),str(BUNDLE)]
import colab_session as auth
from drive_stream_upload import upload_stream
from fetch_calibration_metadata01 import MetadataDrive, API, ACCOUNT, PARENT, RUN, FOLDER


def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import AuthorizedSession
    import requests
    pin=json.loads((BUNDLE/'COLAB_A2_PARTIAL_ARCHIVE02.json').read_text())
    assert pin['writer_absent'] and pin['status']=='STOPPED_PARTIAL_RAW_ARCHIVED'
    state=json.loads((auth.PRIVATE/'cli-runtime.json').read_text())
    assert state['endpoint']=='m-s-usw3b3-ptwp5ez5u6yy'
    proxy=state['assignment']['runtimeProxyInfo']
    credentials=Credentials.from_authorized_user_file(
        str(ROOT/'artifacts/akt/private/drive-upload/token.json'),['https://www.googleapis.com/auth/drive'])
    auth.refresh_credentials(credentials)
    with AuthorizedSession(credentials) as session:
        drive=MetadataDrive(session)
        assert drive.get('/about',params={'fields':'user(emailAddress)'}).json()['user']['emailAddress']==ACCOUNT
        parent=drive.folder(PARENT,RUN)
        assert parent is not None
        folder=drive.folder(parent,'local-migration-20261117-01')
        if folder is None:
            response=session.post(API+'/files',json={'name':'local-migration-20261117-01',
                'mimeType':FOLDER,'parents':[parent]},params={'fields':'id'},timeout=30)
            response.raise_for_status();folder=response.json()['id']
        metadata=drive.get('/files/'+folder,params={'fields':'parents,owners(emailAddress)'}).json()
        assert metadata['parents']==[parent] and any(o.get('emailAddress')==ACCOUNT for o in metadata['owners'])
        source_id=hashlib.sha256(json.dumps(pin,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        plan={'folder_id':folder,'name':'A2_RAW_PARTIAL_1278474_TARGETS.zip',
              'total_bytes':pin['archive_bytes'],'source_plan_sha256':source_id}
        def factory():
            with requests.Session() as reader:
                url=proxy['url'].rstrip('/')+'/files/'+pin['archive_path'].lstrip('/')
                headers={'X-Colab-Runtime-Proxy-Token':proxy['token'],'Authorization':'Bearer '+proxy['token']}
                with reader.get(url,headers=headers,stream=True,timeout=(10,120),allow_redirects=False) as response:
                    response.raise_for_status()
                    assert response.status_code==200 and int(response.headers['Content-Length'])==pin['archive_bytes']
                    yield from response.iter_content(chunk_size=1024**2)
        receipt=upload_stream(session,plan,factory,auth.PRIVATE/'partial-migration-upload.json')
        assert receipt['sha256']==pin['archive_sha256']
        metadata=drive.get('/files/'+receipt['file_id'],
            params={'fields':'size,sha256Checksum,parents,owners(emailAddress),webViewLink'}).json()
        assert int(metadata['size'])==pin['archive_bytes'] and metadata['sha256Checksum']==pin['archive_sha256']
        assert metadata['parents']==[folder] and any(o.get('emailAddress')==ACCOUNT for o in metadata['owners'])
        receipt.update(status='PARTIAL_RAW_DRIVE_SHA256_VERIFIED',account=ACCOUNT,
            url=metadata.get('webViewLink'),raw_manifest_sha256=pin['raw_manifest_sha256'],
            completed_learners=pin['completed_learners'],prediction_rows=pin['prediction_rows'],
            calibration_fit_complete=False,local_binary_created=False)
        output=BUNDLE/'A2_PARTIAL_RAW_DRIVE01.json'
        with output.open('x',encoding='utf-8') as stream:
            json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({'status':receipt['status'],'bytes':receipt['bytes'],'file_id':receipt['file_id']}))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status':'PARTIAL_RAW_UPLOAD_STOPPED','error_type':type(error).__name__}))
        raise SystemExit(1) from None
