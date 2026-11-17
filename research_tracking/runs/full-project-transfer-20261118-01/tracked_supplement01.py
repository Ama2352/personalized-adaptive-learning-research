"""Đóng phần Gittracked ngoài source roots để khôi phục đủ workingtree, gồm corpus engineering."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    source={r['path'] for r in json.loads((B/'01_SOURCE_VA_HO_SO_NGHIEN_CUU.zip.manifest.json').read_text())['member_inventory']}
    tracked=[p for p in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0') if p]
    paths=[ROOT/p for p in tracked if p not in source and (ROOT/p).is_file()]
    rows=[];output=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages/14_GIT_TRACKED_BO_SUNG.zip'
    assert not output.exists()
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for path in paths:
            name=path.relative_to(ROOT).as_posix();assert '/private/' not in '/'+name
            row=dict(path=name,bytes=path.stat().st_size,sha256=sha(path));rows.append(row);archive.write(path,name)
        archive.writestr('HANDOFF_INVENTORY.json',json.dumps(dict(files=rows),ensure_ascii=False,indent=2).encode())
    with zipfile.ZipFile(output) as archive:
        for row in rows:assert hashlib.sha256(archive.read(row['path'])).hexdigest()==row['sha256']
    (B/'TRACKED_COVERAGE01.json').write_text(json.dumps(dict(tracked_files=len(tracked),source_snapshot_files=len(source),
        supplement=rows,missing_after_supplement=[p for p in tracked if p not in source and p not in {r['path'] for r in rows}]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    sys.path.insert(0,str(ROOT/'scripts/akt'));sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    from drive_resumable_upload import Uploader,atomic_json
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    import publish_snapshot as pub
    master=json.loads((B/'DRIVE_MASTER01.json').read_text())
    plan=dict(source=str(output.parent.resolve()),parent_id=master['id'],account='honguyenminhsang2005@gmail.com',folder_name='01_SOURCE',
        files=[dict(path=output.name,bytes=output.stat().st_size,mtime_ns=output.stat().st_mtime_ns,sha256=sha(output))],bytes=output.stat().st_size)
    evidence=B/'upload_logs/tracked_supplement';evidence.mkdir(parents=True,exist_ok=True)
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        Uploader(session,plan,ROOT/'artifacts/akt/private/drive-upload/full-project-transfer-20261118-01/tracked14-state.json',evidence,retries=3).run()
        receipt=json.loads((evidence/'RECEIPTS.json').read_text())[0]
        meta=pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=90))
        assert meta['sha256Checksum']==sha(output)
        atomic_json(B/'TRACKED_UPLOAD01.json',dict(**meta,role='TRACKED_SOURCE_SUPPLEMENT',drive_path='01_SOURCE/'+output.name,
            original_package=output.relative_to(ROOT).as_posix(),independent_metadata_readback=True))
    print('ALL_GIT_TRACKED_FILES_COVERED',len(tracked),len(paths),output.stat().st_size,flush=True)


if __name__=='__main__':main()
