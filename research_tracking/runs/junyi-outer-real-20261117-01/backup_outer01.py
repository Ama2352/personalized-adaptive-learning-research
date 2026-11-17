"""CPU local nhận numeric đã đóng, sao lưu Drive Sang trước phân tích."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
import warnings
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
CACHE=ROOT/'artifacts/akt/local-calibration/20261117'
PHYSICAL='/__modal/volumes/vo-dv1975utRQbmagCjA0brSe'
os.environ['MODAL_CONFIG_PATH']=str(ROOT/'artifacts/akt/private/modal2016.toml')
os.environ['MODAL_PROFILE']='kltn2016'
warnings.filterwarnings('ignore',message=r'Your Modal token .*')
sys.path[:0]=[str(ROOT/'scripts/akt'),str(ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01')]

def save(path,value):
    encoded=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    if path.exists():
        assert path.read_bytes()==encoded,path
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(encoded)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main(variant):
    import modal
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from drive_stream_upload import upload_stream
    from fetch_calibration_metadata01 import MetadataDrive,API,ACCOUNT,PARENT,FOLDER
    result=json.loads((B/(variant+'_GPU_RESULT01.json')).read_text())
    assert result['status']=='OUTER_GPU_OPERATION_COMPLETE'
    volume=modal.Volume.from_name('kltn-junyi-calibration-artifacts-v1',environment_name='main')
    numeric=f'junyi-outer-real-20261117-01/{variant.lower()}-outer-numeric/payloads'
    operation=result['operation_path'].removeprefix(PHYSICAL+'/')
    entries=[]
    for directory in (numeric,operation):
        for item in volume.iterdir(directory,recursive=False):
            path=PurePosixPath(item.path).as_posix().lstrip('/')
            assert path.startswith(directory+'/') and 0<item.size<=4*1024**2
            entries.append(dict(path=path,bytes=item.size))
    assert len(entries)<=1300 and sum(x['bytes'] for x in entries)<=180*1024**2
    used=sum(path.stat().st_size for path in CACHE.rglob('*') if path.is_file())
    destination=CACHE/'outer-numeric-download01'
    pending=sum(e['bytes'] for e in entries if not (destination/e['path']).exists())
    assert used+pending<=4*1024**3,('TEMP_CACHE_CAP',used,pending)
    def download(entry):
        path=destination/entry['path']
        digest=hashlib.sha256();count=0
        if path.exists():
            assert path.stat().st_size==entry['bytes']
            return dict(**entry,sha256=sha(path))
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_name(path.name+'.partial')
        with temporary.open('wb') as stream:
            for chunk in volume.read_file(entry['path']):
                count+=len(chunk)
                assert count<=entry['bytes']
                digest.update(chunk);stream.write(chunk)
        assert count==entry['bytes']
        temporary.rename(path)
        return dict(**entry,sha256=digest.hexdigest())
    with ThreadPoolExecutor(max_workers=6) as pool:
        verified=list(pool.map(download,entries))
    receipt=destination/numeric/'RECEIPT.json'
    assert sha(receipt)==result['result']['receipt_sha256']
    gpu=json.loads(receipt.read_text())
    assert gpu['status']=='COMPLETE' and gpu['counts']['targets']==4137050
    by_path={e['path']:e for e in verified}
    for shard in gpu['shards']:
        name=shard['manifest_path'].removeprefix(PHYSICAL+'/')
        assert by_path[name]['sha256']==shard['manifest_sha256']
        metadata=json.loads((destination/name).read_text())
        payload=str(PurePosixPath(name).with_suffix('.npz'))
        assert by_path[payload]['sha256']==metadata['payload_sha256']
    inventory=dict(status='GPU_NUMERIC_AND_OPERATION_LOCAL_CACHE_VERIFIED',variant=variant,
        files=sorted(verified,key=lambda e:e['path']),receipt_sha256=sha(receipt),
        cache_root=str(destination),temporary_cache_limit_bytes=4*1024**3)
    save(B/(variant+'_NUMERIC_INVENTORY01.json'),inventory)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('INVENTORY.json',json.dumps(inventory,sort_keys=True))
        for entry in inventory['files']:
            archive.write(destination/entry['path'],entry['path'])
    assert buffer.tell()<=200*1024**2
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    session=AuthorizedSession(credentials)
    drive=MetadataDrive(session)
    assert drive.get('/about',params={'fields':'user(emailAddress)'}).json()['user']['emailAddress']==ACCOUNT
    name='junyi-outer-real-20261117-01'
    folder=drive.folder(PARENT,name)
    if folder is None:
        response=session.post(API+'/files',json=dict(name=name,mimeType=FOLDER,parents=[PARENT]),params={'fields':'id'},timeout=30)
        response.raise_for_status();folder=response.json()['id']
    plan=dict(folder_id=folder,name=variant+'_OUTER_NUMERIC_AND_LOGS01.zip',total_bytes=buffer.tell(),
        source_plan_sha256=hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest())
    def chunks():
        buffer.seek(0)
        while chunk:=buffer.read(8*1024**2):
            yield chunk
    publication=upload_stream(session,plan,chunks,
        ROOT/'artifacts/akt/private/drive-upload/outer-20261117-01'/(variant+'.json'))
    metadata=drive.get('/files/'+publication['file_id'],params={'fields':'id,size,sha256Checksum,parents,owners(emailAddress)'}).json()
    assert int(metadata['size'])==plan['total_bytes'] and metadata['sha256Checksum']==publication['sha256']
    assert metadata['parents']==[folder] and any(x.get('emailAddress')==ACCOUNT for x in metadata['owners'])
    publication.update(account=ACCOUNT,folder_id=folder,source_inventory_sha256=sha(B/(variant+'_NUMERIC_INVENTORY01.json')),
        url='https://drive.google.com/file/d/'+publication['file_id']+'/view')
    save(B/(variant+'_DRIVE_BACKUP01.json'),publication)
    print(variant,'OUTER_NUMERIC_LOGS_DRIVE_SHA_VERIFIED',publication['bytes'],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',required=True,choices=('A0','A1','A2','A3'))
    main(parser.parse_args().variant)
