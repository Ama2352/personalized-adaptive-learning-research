"""Lấy cache calibration đã pin về D, giữ nguồn gốc và dữ liệu gốc bất biến."""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[3]
BUNDLE=Path(__file__).resolve().parent
VOLUME=ROOT/'artifacts/akt/local-calibration/20261117'
sys.path.insert(0,str(ROOT/'scripts/akt'))
import colab_session as auth
from free_cpu_calibration import download, extract_numeric
from modal_calibration_input_stage import extract_verified_input


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import AuthorizedSession
    import requests
    if shutil.disk_usage('D:/').free<4*1024**3:
        raise RuntimeError('LOCAL_CACHE_DISK_BUDGET_REQUIRED')
    VOLUME.mkdir(parents=True,exist_ok=True)
    assert VOLUME.resolve()==VOLUME
    incoming=VOLUME/'incoming'
    incoming.mkdir(exist_ok=True)
    payload_path=ROOT/'research_tracking/runs/colab-token-calibration-20261117-01/PAYLOAD.json'
    assert sha(payload_path)=='6fa3012a6d2f321d12d4ae42be2c1fb4ee2e832f26f45459cdb2c51e8e652647'
    payload=json.loads(payload_path.read_text(encoding='utf-8'))
    plan=payload['plan']
    credentials=Credentials.from_authorized_user_file(
        str(ROOT/'artifacts/akt/private/drive-upload/token.json'),['https://www.googleapis.com/auth/drive'])
    auth.refresh_credentials(credentials)
    auth.save_private(auth.PRIVATE/'drive-controller-credentials.json',json.loads(credentials.to_json()))
    rows=[]
    with AuthorizedSession(credentials) as session:
        who=session.get('https://www.googleapis.com/drive/v3/about',params={'fields':'user(emailAddress)'},timeout=30)
        who.raise_for_status()
        assert who.json()['user']['emailAddress']==auth.ACCOUNT
        pins=[('INPUT.zip',plan['input']),('A2_NUMERIC.zip',plan['numeric']['A2']),
              ('A3_NUMERIC.zip',plan['numeric']['A3'])]
        for name,pin in pins:
            metadata=session.get('https://www.googleapis.com/drive/v3/files/'+pin['file_id'],
                params={'fields':'id,size,sha256Checksum,mimeType,owners(emailAddress)'},timeout=30)
            metadata.raise_for_status()
            value=metadata.json()
            assert int(value['size'])==pin['bytes'] and value['sha256Checksum']==pin['sha256']
            assert any(owner.get('emailAddress')==auth.ACCOUNT for owner in value['owners'])
            for attempt in range(3):
                try:
                    path=download(session,pin,incoming/name)
                    break
                except requests.RequestException:
                    if attempt==2:raise
                    time.sleep(attempt+1)
            rows.append({'name':name,'bytes':pin['bytes'],'sha256':pin['sha256'],'file_id':pin['file_id']})
            print(name,'LOCAL_CACHE_SHA256_VERIFIED',pin['bytes'],flush=True)
        source=VOLUME/'calibration-inputs-20261117-01/source'
        if not source.exists():
            extract_verified_input(incoming/'INPUT.zip',source)
        else:
            with zipfile.ZipFile(incoming/'INPUT.zip') as archive:
                inventory=json.loads(archive.read('CLOUD_INPUT_PLAN.json'))
            assert all(sha(source/row['path'])==row['sha256'] for row in inventory['files'])
        upstream=source/'artifacts/akt/dependencies/upstream/akt.py'
        data=base64.b64decode(payload['upstream_b64'])
        assert hashlib.sha256(data).hexdigest()=='ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67'
        upstream.parent.mkdir(parents=True,exist_ok=True)
        if upstream.exists():assert upstream.read_bytes()==data
        else:upstream.write_bytes(data)
        for variant in ('A2','A3'):
            extract_numeric(incoming/(variant+'_NUMERIC.zip'),plan['numeric'][variant],VOLUME,variant)
        windows=plan['cache']['windows']
        for pin in plan['window_metadata']:
            original=(PurePosixPath(windows['path'])/'manifest.json' if pin['path']=='WINDOW_MANIFEST.json'
                      else PurePosixPath(windows['admission_path']))
            relative=original.relative_to('/__modal/volumes/vo-dv1975utRQbmagCjA0brSe')
            destination=VOLUME.joinpath(*relative.parts)
            download(session,pin,destination)
            rows.append({'name':pin['path'],'bytes':pin['bytes'],'sha256':pin['sha256'],'file_id':pin['file_id']})
    result={'status':'LOCAL_FROZEN_INPUT_NUMERIC_WINDOWS_READY','volume':str(VOLUME),
            'frozen_source':str(source),'inputs':rows,'python':str(ROOT/'.venv/Scripts/python.exe'),
            'authoritative_results':'Drive Sang; dữ liệu D là cache thực thi local',
            'protected_dataset_modified':False,'full_calibration_started':False}
    (BUNDLE/'LOCAL_CALIBRATION_INPUTS01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(result['status'],flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status':'LOCAL_INPUT_PREPARATION_STOPPED','error_type':type(error).__name__}),flush=True)
        raise SystemExit(1) from None
