"""Upload từng gói đã nghiệm thu, giữ state resumable riêng và SHA đọc lại."""
from pathlib import Path
from contextlib import redirect_stdout
import hashlib
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
OUT=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages'
PRIVATE=ROOT/'artifacts/akt/private/drive-upload/full-project-transfer-20261118-01'
sys.path.insert(0,str(ROOT/'scripts/akt'))
sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
from drive_resumable_upload import Uploader, hashes, atomic_json, single_writer
import publish_snapshot as pub


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    PRIVATE.mkdir(parents=True,exist_ok=True)
    done={};started=time.monotonic()
    receipt_file=B/'UPLOADED_PACKAGES01.json'
    if receipt_file.exists():
        done={r['name']:r for r in json.loads(receipt_file.read_text())['files']}
    with single_writer(PRIVATE/'packages.lock'),AuthorizedSession(credentials) as session:
        while True:
            if time.monotonic()-started>3*3600:
                raise TimeoutError('Hết cửa sổ điều phối3giờ, giữ state để tiếp tục.')
            master_file=B/'DRIVE_MASTER01.json';packages_file=B/'PACKAGES01.json'
            if not master_file.exists() or not packages_file.exists():
                time.sleep(5);continue
            try:
                master=json.loads(master_file.read_text());index=json.loads(packages_file.read_text())
            except json.JSONDecodeError:
                time.sleep(2);continue
            packages=list(index['packages'])
            bundle=OUT/'10_AKT_UPSTREAM.bundle'
            if bundle.exists():
                packages.append(dict(name=bundle.name,role='UPSTREAM_BUNDLE',path=bundle.relative_to(ROOT).as_posix(),
                    bytes=bundle.stat().st_size,sha256=hashes(bundle)['sha256']))
            for package in packages:
                name=package['name'];path=ROOT/package['path']
                if name in done:
                    continue
                category=('01_SOURCE' if package['role'] in {'SOURCE','UPSTREAM_BUNDLE'} else
                          '02_DU_LIEU' if package['role'] in {'RAW_DATA','REQUIRED_INPUT'} else
                          '03_ARTIFACTS_VA_KET_QUA')
                row=dict(path=name,bytes=package['bytes'],mtime_ns=path.stat().st_mtime_ns,sha256=package['sha256'])
                plan=dict(source=str(OUT.resolve()),parent_id=master['id'],account='honguyenminhsang2005@gmail.com',
                    folder_name=category,files=[row],bytes=row['bytes'])
                evidence=B/'upload_logs'/path.stem
                evidence.mkdir(parents=True,exist_ok=True)
                atomic_json(evidence/'PLAN.json',plan)
                with (evidence/'console.log').open('a',encoding='utf-8') as log,redirect_stdout(log):
                    uploader=Uploader(session,plan,PRIVATE/(name+'.state.json'),evidence,chunk_bytes=32*1024**2,retries=5)
                    uploader.run()
                receipt=json.loads((evidence/'RECEIPTS.json').read_text())[0]
                meta=pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],
                    params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=120))
                assert meta['sha256Checksum']==package['sha256'] and int(meta['size'])==package['bytes']
                assert meta['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
                assert hashes(path)['sha256']==package['sha256']
                done[name]=dict(**meta,role=package['role'],drive_path=category+'/'+name,
                    original_package=package['path'],independent_metadata_readback=True,
                    source_files=package.get('source_files'),source_bytes=package.get('source_bytes'))
                atomic_json(receipt_file,dict(status='UPLOADING',master=master,files=list(done.values())))
                print('UPLOAD_VERIFIED',name,package['bytes'],flush=True)
            if index['status']=='ALL_PACKAGES_MEMBER_AND_SOURCE_SHA256_VERIFIED' and len(done)==len(packages):
                atomic_json(receipt_file,dict(status='ALL_LOCAL_PACKAGES_DRIVE_SHA256_VERIFIED',master=master,files=list(done.values())))
                print('ALL_LOCAL_UPLOADS_COMPLETE',len(done),sum(int(r['size']) for r in done.values()),flush=True)
                break
            time.sleep(5)
    atomic_json(ROOT/'artifacts/akt/private/drive-upload/token.json',json.loads(credentials.to_json()))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print('STOPPED',type(error).__name__,'Giữ logs/state riêng để tiếp tục, không hiển thị HTTP/OAuth secret.',flush=True)
        raise SystemExit(1)
