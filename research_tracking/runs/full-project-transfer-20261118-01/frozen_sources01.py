"""Giữ source packets theo run và input pins đã thực sự dùng, bên cạnh source hiện hành."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B))
from build_packages01 import SECRET


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    sources=list((ROOT/'artifacts/akt/modal').glob('*/source.zip'))
    stage=json.loads((ROOT/'research_tracking/runs/junyi-a3-selected-20261114-01/a3-stage-inputs03.json').read_text())
    paths=set(sources);pins={}
    for row in stage['archives'].values():
        path=ROOT/row['path'];assert sha(path)==row['sha256'];paths.add(path);pins[row['path']]=row['sha256']
    for path in sources:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                assert '/private/' not in '/'+info.filename
                if info.filename.endswith(('.py','.json','.ipynb','.toml')) and info.file_size<5*1024**2:
                    assert not SECRET.search(archive.read(info)), 'Cần rà source packet: '+str(path)
    output=ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages/12_SOURCE_PACKETS_VA_INPUT_PINS.zip'
    assert not output.exists()
    rows=[]
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for path in sorted(paths):
            name=path.relative_to(ROOT).as_posix();digest=sha(path)
            archive.write(path,name);rows.append(dict(path=name,bytes=path.stat().st_size,sha256=digest))
            assert sha(path)==digest
        archive.writestr('HANDOFF_INVENTORY.json',json.dumps(dict(files=rows,accepted_a3_stage_pins=pins),ensure_ascii=False,indent=2).encode())
    with zipfile.ZipFile(output) as archive:
        for row in rows:
            with archive.open(row['path']) as stream:
                assert hashlib.file_digest(stream,'sha256').hexdigest()==row['sha256']
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    from drive_resumable_upload import Uploader,atomic_json
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    import publish_snapshot as pub
    master=json.loads((B/'DRIVE_MASTER01.json').read_text())
    plan=dict(source=str(output.parent.resolve()),parent_id=master['id'],account='honguyenminhsang2005@gmail.com',folder_name='01_SOURCE',
        files=[dict(path=output.name,bytes=output.stat().st_size,mtime_ns=output.stat().st_mtime_ns,sha256=sha(output))],bytes=output.stat().st_size)
    evidence=B/'upload_logs/frozen_sources';evidence.mkdir(parents=True,exist_ok=True)
    atomic_json(B/'FROZEN_SOURCE_INPUTS01.json',dict(files=rows,accepted_a3_stage_pins=pins))
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        Uploader(session,plan,ROOT/'artifacts/akt/private/drive-upload/full-project-transfer-20261118-01/frozen12-state.json',evidence,retries=3).run()
        receipt=json.loads((evidence/'RECEIPTS.json').read_text())[0]
        meta=pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=60))
        assert meta['sha256Checksum']==sha(output)
        atomic_json(B/'FROZEN_INPUTS_UPLOAD01.json',dict(**meta,role='FROZEN_SOURCE_PACKETS',drive_path='01_SOURCE/'+output.name,
                                                     original_package=output.relative_to(ROOT).as_posix(),independent_metadata_readback=True))
    print('FROZEN_SOURCES_AND_INPUT_PINS_ACCEPTED',len(paths),output.stat().st_size,flush=True)


if __name__=='__main__':
    main()
