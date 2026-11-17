"""Giữ Linux CUDA lock thực tế và snapshot runtime riêng, tránh thiếu phụ thuộc GPU."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
OUT=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    names=('torch','numpy','pandas','scipy','scikit-learn','pyarrow','duckdb','matplotlib','psutil',
           'requests','google-auth','google-auth-oauthlib','joblib','threadpoolctl','pytest')
    versions={name:importlib.metadata.version(name) for name in names}
    (B/'LOCAL_RUNTIME_VERSIONS01.json').write_text(json.dumps(dict(python=sys.version,versions=versions,
        note='Runtime local tham chiếu; Linux GPU dùng lock và source của run. Không trộn wheel Windows với Linux.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (B/'requirements-tai-goi.txt').write_text('\n'.join(name+'=='+versions[name] for name in ('requests','google-auth','google-auth-oauthlib'))+'\n',encoding='utf-8')
    (B/'requirements-local-bo-sung.txt').write_text('\n'.join(name+'=='+versions[name] for name in ('pyarrow','matplotlib','requests','google-auth','google-auth-oauthlib'))+'\n',encoding='utf-8')
    patch=subprocess.check_output(['git','diff','--','notebooks/akt_colab_response_calibration_cpu.ipynb'],cwd=ROOT)
    (B/'NOTEBOOK_WORKING_TREE.patch').write_bytes(patch)
    paths=[ROOT/'artifacts/akt/runtime/modal-linux-cuda.lock.txt',B/'LOCAL_RUNTIME_VERSIONS01.json',
           B/'requirements-tai-goi.txt',B/'requirements-local-bo-sung.txt',B/'NOTEBOOK_WORKING_TREE.patch']
    output=OUT/'11_RUNTIME_LOCKS_VA_SOURCE_STATE.zip'
    assert not output.exists(),'Giữ gói cũ nếu đã có, cần review trước thay.'
    rows=[]
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in paths:
            relative=path.relative_to(ROOT).as_posix();sha=digest(path)
            rows.append(dict(path=relative,bytes=path.stat().st_size,sha256=sha));archive.write(path,relative)
        archive.writestr('HANDOFF_INVENTORY.json',json.dumps(dict(files=rows),ensure_ascii=False,indent=2).encode())
    with zipfile.ZipFile(output) as archive:
        for row in rows:
            assert hashlib.sha256(archive.read(row['path'])).hexdigest()==row['sha256']
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    from drive_resumable_upload import Uploader,atomic_json
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    import publish_snapshot as pub
    master=json.loads((B/'DRIVE_MASTER01.json').read_text())
    plan=dict(source=str(OUT.resolve()),parent_id=master['id'],account='honguyenminhsang2005@gmail.com',
        folder_name='01_SOURCE',files=[dict(path=output.name,bytes=output.stat().st_size,mtime_ns=output.stat().st_mtime_ns,sha256=digest(output))],bytes=output.stat().st_size)
    evidence=B/'upload_logs/runtime_supplement';evidence.mkdir(parents=True,exist_ok=True)
    atomic_json(B/'SUPPLEMENT_PACKAGE01.json',dict(name=output.name,path=output.relative_to(ROOT).as_posix(),role='PROVENANCE',
        bytes=output.stat().st_size,sha256=digest(output),member_inventory=rows))
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        Uploader(session,plan,ROOT/'artifacts/akt/private/drive-upload/full-project-transfer-20261118-01/runtime11-state.json',evidence,retries=3).run()
        receipt=json.loads((evidence/'RECEIPTS.json').read_text())[0]
        meta=pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=60))
        assert meta['sha256Checksum']==digest(output)
        atomic_json(B/'SUPPLEMENT_UPLOAD01.json',dict(**meta,role='PROVENANCE',drive_path='01_SOURCE/'+output.name,
            original_package=output.relative_to(ROOT).as_posix(),independent_metadata_readback=True))
    print('RUNTIME_LOCK_AND_WORKING_STATE_VERIFIED',output.stat().st_size,flush=True)


if __name__=='__main__':
    main()
