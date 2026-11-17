"""Đóng hồ sơ nhỏ kèm nguồn frozen, kiểm8archive và lưu hai báo cáo Drive."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'scripts/akt'),str(ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01')]

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from drive_stream_upload import upload_stream
    from fetch_calibration_metadata01 import MetadataDrive,API,ACCOUNT
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    session=AuthorizedSession(credentials);drive=MetadataDrive(session)
    assert drive.get('/about',params={'fields':'user(emailAddress)'}).json()['user']['emailAddress']==ACCOUNT
    verified=[];folder=None
    for model in ('A0','A1','A2','A3'):
        for suffix in ('_DRIVE_BACKUP01.json','_CPU_EXPORT_DRIVE01.json'):
            receipt=json.loads((B/(model+suffix)).read_text())
            metadata=drive.get('/files/'+receipt['file_id'],params={'fields':'id,size,sha256Checksum,parents,owners(emailAddress),trashed'}).json()
            assert int(metadata['size'])==receipt['bytes'] and metadata['sha256Checksum']==receipt['sha256']
            assert not metadata['trashed'] and metadata['parents']==[receipt['folder_id']]
            assert any(x.get('emailAddress')==ACCOUNT for x in metadata['owners'])
            if folder is None:
                folder=receipt['folder_id']
            assert folder==receipt['folder_id']
            verified.append(dict(model=model,archive=receipt['name'],file_id=receipt['file_id'],
                bytes=receipt['bytes'],sha256=receipt['sha256']))
    acceptance=dict(status='EIGHT_OUTER_ARCHIVES_INDEPENDENT_DRIVE_METADATA_VERIFIED',
        account=ACCOUNT,folder_id=folder,archives=verified)
    (B/'DRIVE_FINAL_ARCHIVE_ACCEPTANCE01.json').write_text(json.dumps(acceptance,indent=2)+'\n')
    payloads={}
    for path in B.iterdir():
        if path.is_file() and path.suffix.lower() in ('.py','.json','.csv','.md','.txt','.svg','.png','.pdf'):
            if path.name.startswith('STORAGE') or path.name.startswith('storage_'):
                continue
            assert path.stat().st_size<=2*1024**2
            payloads['run/'+path.name]=path.read_bytes()
    for path in (B/'handoff').glob('*.json'):
        payloads['run/handoff/'+path.name]=path.read_bytes()
    source=ROOT/'artifacts/akt/local-calibration/20261117/outer-source-guard-release/source'
    source_paths=list((source/'src').rglob('*.py'))
    source_paths += [source/'docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md']
    source_paths += [source/'artifacts/akt/dependencies/upstream/akt.py']
    for path in source_paths:
        assert path.is_file() and not path.is_symlink()
        payloads['frozen-source/'+path.relative_to(source).as_posix()]=path.read_bytes()
    recipe=ROOT/'docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md'
    payloads['project-documents/'+recipe.name]=recipe.read_bytes()
    for name in ('test_outer_gpu_worker.py','test_outer_numeric_cpu_export.py',
            'test_outer_primary_bootstrap.py','test_prepare_junyi_outer_caches.py',
            'test_prepare_junyi_outer_source.py','test_free_outer_evaluation.py'):
        payloads['execution-tests/'+name]=(ROOT/'tests/akt'/name).read_bytes()
    for name in ('outer_gpu_worker.py','modal_junyi_outer.py','outer_numeric_cpu_export.py',
            'free_outer_evaluation.py','calibration_cloud_worker.py','modal_junyi_calibration.py',
            'run_junyi_refit.py','prepare_junyi_outer_source.py','prepare_junyi_outer_caches.py'):
        payloads['execution-scripts/'+name]=(ROOT/'scripts/akt'/name).read_bytes()
    handoff=json.loads((B/'HANDOFF_INVENTORY01.json').read_text())
    for model in ('A0','A1','A2','A3'):
        entry=next(e for e in handoff['files'] if e['remote_path'].endswith('/calibrators/'+model+'.temperature.json'))
        raw=Path(entry['local_path']).read_bytes();assert digest(raw)==entry['sha256']
        payloads['calibrators/'+model+'.temperature.json']=raw
    assert sum(len(raw) for raw in payloads.values())<=15*1024**2
    inventory={name:dict(bytes=len(raw),sha256=digest(raw)) for name,raw in sorted(payloads.items())}
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,raw in sorted(payloads.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,raw)
        archive.writestr(zipfile.ZipInfo('INVENTORY.json',(1980,1,1,0,0,0)),json.dumps(inventory,sort_keys=True))
    assert buffer.tell()<=5*1024**2
    plan=dict(folder_id=folder,name='OUTER_EVIDENCE_SOURCE_AND_FIGURES01.zip',total_bytes=buffer.tell(),
        source_plan_sha256=digest(json.dumps(inventory,sort_keys=True).encode()))
    private=ROOT/'artifacts/akt/private/drive-upload/outer-20261117-01'
    def chunks():
        buffer.seek(0)
        while chunk:=buffer.read(1024**2):
            yield chunk
    receipt=upload_stream(session,plan,chunks,private/'evidence.json')
    (B/'EVIDENCE_DRIVE01.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (B/'EVIDENCE_SOURCE_INVENTORY01.json').write_text(json.dumps(inventory,indent=2)+'\n')
    publisher_path=ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01/publish_snapshot.py'
    spec=importlib.util.spec_from_file_location('report_publisher_outer',publisher_path)
    publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
    publisher.NAME='research-reports-20261117-v4-outer-complete'
    destination=publisher.folder(session)
    report=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
    reports=[]
    for name,mime in (('BAO_CAO.md','text/markdown'),('BAO_CAO_NGHIEN_CUU.html','text/html')):
        raw=(report/name).read_bytes()
        metadata=publisher.small_file(session,destination['id'],name,raw,mime)
        reports.append(publisher.readback(session,metadata['id'],len(raw),digest(raw)))
    publication=dict(status='TWO_HUMAN_REPORTS_INDEPENDENT_BODY_READBACK_VERIFIED',
        folder=destination,files=reports,evidence_file_id=receipt['file_id'],outer_folder_id=folder)
    (B/'REPORT_DRIVE01.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('EIGHT_ARCHIVES_SOURCE_FIGURES_TWO_REPORTS_DRIVE_VERIFIED',destination.get('webViewLink'),flush=True)

if __name__=='__main__':
    main()
