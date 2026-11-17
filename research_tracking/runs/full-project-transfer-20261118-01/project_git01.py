"""Bảo toàn Git history sau rà secret; snapshot bytes hiện hành vẫn giữ trong ZIP source."""
from pathlib import Path
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B))
from build_packages01 import SECRET


def main():
    objects=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT).decode().splitlines()
    entries=[];denied=[]
    for line in objects:
        oid,_,name=line.partition(' ')
        if not name:
            continue
        if '/private/' in '/'+name or Path(name).name.lower() in {'token.json','client_secret.json','modal.toml','.env'}:
            denied.append(name)
        entries.append((oid,name))
    assert not denied,'Git history có đường dẫn tài khoản cần review.'
    checked=set();matches=[]
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,name in entries:
        if oid in checked or Path(name).suffix.lower() not in {'.py','.json','.jsonl','.md','.txt','.ipynb','.toml','.ps1','.sh','.yml','.yaml'}:
            continue
        process.stdin.write((oid+'\n').encode());process.stdin.flush()
        header=process.stdout.readline().decode().strip().split()
        assert len(header)==3 and header[1]=='blob'
        size=int(header[2]);raw=process.stdout.read(size);assert process.stdout.read(1)==b'\n'
        if SECRET.search(raw):matches.append(name)
        checked.add(oid)
    process.stdin.close();process.wait(timeout=60)
    result=dict(status='REACHABLE_GIT_TEXT_BLOBS_AND_PATHS_CHECKED',text_blobs=len(checked),findings=sorted(set(matches)),
                limits='Kiểm mẫu secret trực tiếp và đường dẫn private; không chứng nhận bí mật ở ảnh/binary.')
    (B/'GIT_HISTORY_REVIEW01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not matches,'Có secret pattern trong Git history, giữ local và review trước chia sẻ.'
    output=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages/13_KLTN_GIT.bundle'
    assert not output.exists()
    subprocess.run(['git','bundle','create',str(output),'HEAD'],cwd=ROOT,check=True)
    subprocess.run(['git','bundle','verify',str(output)],cwd=ROOT,check=True)
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    from drive_resumable_upload import Uploader,atomic_json,hashes
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    import publish_snapshot as pub
    master=json.loads((B/'DRIVE_MASTER01.json').read_text());pin=hashes(output)
    plan=dict(source=str(output.parent.resolve()),parent_id=master['id'],account='honguyenminhsang2005@gmail.com',
        folder_name='01_SOURCE',files=[dict(path=output.name,**{k:pin[k] for k in ('bytes','mtime_ns','sha256')})],bytes=pin['bytes'])
    evidence=B/'upload_logs/project_git';evidence.mkdir(parents=True,exist_ok=True)
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        Uploader(session,plan,ROOT/'artifacts/akt/private/drive-upload/full-project-transfer-20261118-01/project13-state.json',evidence,retries=3).run()
        receipt=json.loads((evidence/'RECEIPTS.json').read_text())[0]
        meta=pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=120))
        assert meta['sha256Checksum']==pin['sha256']
        atomic_json(B/'PROJECT_GIT_UPLOAD01.json',dict(**meta,role='PROJECT_GIT_BUNDLE',drive_path='01_SOURCE/'+output.name,
            original_package=output.relative_to(ROOT).as_posix(),independent_metadata_readback=True))
    print('PROJECT_GIT_HISTORY_ACCEPTED',len(checked),pin['bytes'],flush=True)


if __name__=='__main__':
    main()
