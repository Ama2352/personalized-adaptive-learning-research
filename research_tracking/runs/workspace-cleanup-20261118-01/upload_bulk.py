"""Upload song song ba gói độc lập, tiếp tục state riêng; đợi producer đóng gói."""
from pathlib import Path
from contextlib import redirect_stdout
import json,sys,time,concurrent.futures,hashlib
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/akt'))
from drive_resumable_upload import Uploader,atomic_json,single_writer
API='https://www.googleapis.com/drive/v3'

def credentials():return Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))

def main():
    separation=json.loads((B/'DRIVE_SEPARATION.json').read_text(encoding='utf-8'))
    parent=separation['archive_folder']['id'];name='06_WORKSPACE_THEO_SHA'
    with AuthorizedSession(credentials()) as s:
        r=s.get(API+'/files',params={'q':"'%s' in parents and name='%s' and trashed=false"%(parent,name),'fields':'files(id,name,parents,webViewLink)'},timeout=60);r.raise_for_status()
        folders=r.json().get('files',[]);assert len(folders)<=1
        if folders:folder=folders[0]
        else:
            r=s.post(API+'/files',json={'name':name,'mimeType':'application/vnd.google-apps.folder','parents':[parent]},params={'fields':'id,name,parents,webViewLink'},timeout=60);r.raise_for_status();folder=r.json()
    private=ROOT/'artifacts/akt/private/drive-upload/workspace-cleanup-20261118-01/bulk';private.mkdir(parents=True,exist_ok=True)
    output=B/'bulk_upload';output.mkdir(exist_ok=True)
    receipt_file=B/'BULK_DRIVE_DATA.json'
    done={r['name']:r for r in json.loads(receipt_file.read_text(encoding='utf-8'))['files']} if receipt_file.exists() else {}
    def send(package):
        path=ROOT/package['path'];stat=path.stat()
        assert stat.st_size==package['bytes']
        evidence=output/path.stem;evidence.mkdir(exist_ok=True)
        plan=dict(source=str(path.parent.resolve()),parent_id=parent,account='honguyenminhsang2005@gmail.com',folder_name=name,bytes=stat.st_size,files=[dict(path=path.name,bytes=stat.st_size,sha256=package['sha256'],mtime_ns=stat.st_mtime_ns)])
        with single_writer(private/(path.name+'.lock')),AuthorizedSession(credentials()) as s:
            Uploader(s,plan,private/(path.name+'.state.json'),evidence,chunk_bytes=64*1024**2,retries=5).run()
            row=json.loads((evidence/'RECEIPTS.json').read_text(encoding='utf-8'))[0]
            response=s.get(API+'/files/'+row['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,trashed,webViewLink'},timeout=60);response.raise_for_status();meta=response.json()
            assert not meta['trashed'] and meta['sha256Checksum']==package['sha256'] and int(meta['size'])==package['bytes'] and folder['id'] in meta['parents']
        return dict(**meta,local_path=package['path'],members=package['members'])
    start=time.monotonic();pending={};submitted=set(done)
    with (output/'console.log').open('a',encoding='utf-8') as log,redirect_stdout(log),concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        while True:
            assert time.monotonic()-start<4*3600,'Giữ state, dừng sau4giờ'
            try:packages=json.loads((B/'BULK_PACKAGES.json').read_text(encoding='utf-8'))
            except (FileNotFoundError,json.JSONDecodeError):time.sleep(2);continue
            for package in packages['packages']:
                if package['name'] not in submitted:
                    pending[pool.submit(send,package)]=package['name'];submitted.add(package['name'])
            finished,_=concurrent.futures.wait(pending,timeout=2,return_when=concurrent.futures.FIRST_COMPLETED) if pending else (set(),set())
            for future in finished:
                row=future.result();done[row['name']]=row;pending.pop(future)
                atomic_json(receipt_file,dict(status='UPLOADING',folder=folder,files=list(done.values())))
                print('BULK_DRIVE_VERIFIED',len(done),row['name'],flush=True)
            if packages['status']=='ALL_NEW_BULK_CONTENT_ARCHIVES_VERIFIED' and len(done)==len(packages['packages']) and not pending:break
            if not pending:time.sleep(2)
    atomic_json(receipt_file,dict(status='ALL_BULK_ARCHIVES_DRIVE_SHA256_VERIFIED',folder=folder,files=sorted(done.values(),key=lambda r:r['name']),bytes=sum(int(r['size']) for r in done.values())))
    print('ALL_BULK_DRIVE_VERIFIED',len(done),sum(int(r['size']) for r in done.values()),folder['webViewLink'],flush=True)

if __name__=='__main__':
    try:main()
    except Exception as error:
        print('STOPPED',type(error).__name__,'Giữ bản local và resumable state; chưa cho phép gỡ bulk.',flush=True)
        raise SystemExit(1)
