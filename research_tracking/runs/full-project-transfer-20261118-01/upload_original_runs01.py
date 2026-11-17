"""Bảo toàn archive Grade10 gốc và A0 đủ12epoch để giữ đường dẫn truy vết."""
from pathlib import Path
import json
import sys
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts/akt'))
sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
from drive_resumable_upload import Uploader,atomic_json,hashes
import publish_snapshot as pub


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    index=json.loads((ROOT/'experiments/akt/results/model-export-20261112-01/MODEL_INDEX.json').read_text())
    paths=sorted({r['source_archive'] for r in index['entries'] if r['dataset']=='Grade10' and (ROOT/r['source_archive']).is_file()})
    paths.append('experiments/akt/results/modal-junyi-a0-b128-h100-20261112-03/artifacts.zip')
    assert len(paths)==6
    master=json.loads((B/'DRIVE_MASTER01.json').read_text());receipts=[]
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        for relative in paths:
            source=ROOT/relative;pin=hashes(source)
            plan=dict(source=str(ROOT.resolve()),parent_id=master['id'],account='honguyenminhsang2005@gmail.com',
                folder_name='03_ARTIFACTS_VA_KET_QUA',files=[dict(path=relative,**{k:pin[k] for k in ('bytes','mtime_ns','sha256')})],bytes=pin['bytes'])
            evidence=B/'upload_logs'/('original-'+source.parent.name);evidence.mkdir(parents=True,exist_ok=True)
            state=ROOT/'artifacts/akt/private/drive-upload/full-project-transfer-20261118-01'/('original-'+source.parent.name+'.json')
            with (evidence/'console.log').open('a',encoding='utf-8') as log,redirect_stdout(log):
                Uploader(session,plan,state,evidence,retries=5).run()
            receipt=json.loads((evidence/'RECEIPTS.json').read_text())[0]
            meta=pub.checked(session.get(pub.API+'/files/'+receipt['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink'},timeout=120))
            assert meta['sha256Checksum']==pin['sha256'] and hashes(source)['sha256']==pin['sha256']
            role='A0_SELECTED_FULL_RUN' if 'modal-junyi-a0' in relative else 'GRADE10_ORIGINAL_RUN'
            receipts.append(dict(**meta,role=role,original_archive=relative,
                drive_path='03_ARTIFACTS_VA_KET_QUA/'+relative,source_rehashed_after_upload=True))
            atomic_json(B/'ORIGINAL_RUNS_UPLOAD01.json',dict(status='UPLOADING',files=receipts))
            print('ORIGINAL_ARCHIVE_VERIFIED',source.parent.name,pin['bytes'],flush=True)
    atomic_json(B/'ORIGINAL_RUNS_UPLOAD01.json',dict(status='ALL_SIX_ORIGINAL_RUN_ARCHIVES_VERIFIED',files=receipts))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print('STOPPED',type(error).__name__,'Giữ logs/state để tiếp tục; gốc giữ nguyên.',flush=True)
        raise SystemExit(1)
