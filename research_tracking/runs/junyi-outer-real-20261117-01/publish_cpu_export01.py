"""Đưa Parquet raw/calibrated đã nghiệm thu lên Drive, ZIP chỉ giữ trong RAM."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'scripts/akt'),str(ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01')]

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main(variant):
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from drive_stream_upload import upload_stream
    from fetch_calibration_metadata01 import MetadataDrive,API,ACCOUNT
    folder=ROOT/'artifacts/akt/local-calibration/20261117/outer-export01'/variant
    complete=json.loads((folder/'COMPLETE.json').read_text())
    assert complete['status']=='COMPLETE_OUTER_NUMERIC_CPU_EXPORT' and complete['targets']==4137050
    entries=[]
    for entry in complete['files']:
        assert Path(entry['path']).name==entry['path'] and sha(folder/entry['path'])==entry['sha256']
    for path in sorted(folder.iterdir()):
        assert path.is_file() and path.suffix in ('.parquet','.json') and not path.is_symlink()
        entries.append(dict(path=path.name,bytes=path.stat().st_size,sha256=sha(path)))
    assert sum(e['bytes'] for e in entries)<=200*1024**2
    inventory=dict(status='COMPLETE_OUTER_PREDICTIONS_WITH_LABELS_RAW_AND_CALIBRATED',variant=variant,
        source_complete_sha256=sha(folder/'COMPLETE.json'),files=entries)
    encoded=(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n').encode()
    inventory_path=B/(variant+'_CPU_EXPORT_INVENTORY01.json')
    if inventory_path.exists():
        assert inventory_path.read_bytes()==encoded
    else:
        inventory_path.write_bytes(encoded)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(zipfile.ZipInfo('INVENTORY.json',(1980,1,1,0,0,0)),encoded)
        for entry in entries:
            archive.writestr(zipfile.ZipInfo(entry['path'],(1980,1,1,0,0,0)),(folder/entry['path']).read_bytes())
    backup=json.loads((B/(variant+'_DRIVE_BACKUP01.json')).read_text())
    plan=dict(folder_id=backup['folder_id'],name=variant+'_OUTER_PREDICTIONS_CALIBRATED01.zip',
        total_bytes=buffer.tell(),source_plan_sha256=hashlib.sha256(encoded).hexdigest())
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    session=AuthorizedSession(credentials)
    def chunks():
        buffer.seek(0)
        while chunk:=buffer.read(8*1024**2):
            yield chunk
    receipt=upload_stream(session,plan,chunks,
        ROOT/'artifacts/akt/private/drive-upload/outer-20261117-01'/(variant+'-cpu.json'))
    drive=MetadataDrive(session)
    metadata=drive.get('/files/'+receipt['file_id'],params={'fields':'id,parents,size,sha256Checksum,owners(emailAddress)'}).json()
    assert metadata['parents']==[plan['folder_id']] and int(metadata['size'])==plan['total_bytes']
    assert metadata['sha256Checksum']==receipt['sha256'] and any(x.get('emailAddress')==ACCOUNT for x in metadata['owners'])
    receipt.update(account=ACCOUNT,source_complete_sha256=inventory['source_complete_sha256'],
        url='https://drive.google.com/file/d/'+receipt['file_id']+'/view')
    with (B/(variant+'_CPU_EXPORT_DRIVE01.json')).open('x',encoding='utf-8') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(variant,'FINAL_PREDICTIONS_CALIBRATED_DRIVE_VERIFIED',receipt['bytes'],flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--variant',required=True,choices=('A0','A1','A2','A3'))
    main(parser.parse_args().variant)
