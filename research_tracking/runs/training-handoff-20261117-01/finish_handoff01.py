"""Nghiệm thu bản Drive đã có, công bố chỉ mục và hồ sơ bàn giao nhỏ."""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(B))
sys.path.insert(0,str(ROOT/'scripts/akt'))
sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
from package_outputs01 import blocks, sha, write, PRIVATE
import publish_snapshot as pub


def metadata(session, file_id):
    return pub.checked(session.get(pub.API+'/files/'+file_id,
        params={'fields':'id,name,size,sha256Checksum,parents,owners(emailAddress),webViewLink,trashed'},timeout=90))


def verify_reused(session):
    discovery=json.loads((B/'DRIVE_DISCOVERY01.json').read_text(encoding='utf-8'))
    folder=discovery['folders']['1--Q-yO2ja7q2RwWWfyv6nDtw80PDrnyZ']
    known={r['name']:r for r in folder['files']}
    root=ROOT/'experiments/akt/results/artifact-offload-20261116-01'
    rows=[]
    for name in ('01_JUNYI_REFIT_A0_A3.zip','02_JUNYI_SELECTED_A0_A3.zip',
                 '03_GRADE10_SELECTED_AND_LEGACY.zip','04_CORE_TRAINING_AUDIT.zip',
                 '05_RETENTION_CATALOGS.zip','06_AUDIT_RETENTION_REVIEW.zip'):
        path=root/name
        parts=sorted((r for n,r in known.items() if n==name or n.startswith(name+'.part')),key=lambda r:r['name'])
        assert parts, name
        with path.open('rb') as stream:
            combined=hashlib.sha256()
            for part in parts:
                raw=stream.read(int(part['size']))
                combined.update(raw)
                digest=hashlib.sha256(raw).hexdigest()
                assert len(raw)==int(part['size']) and digest==part['sha256Checksum']
                live=metadata(session,part['id'])
                assert live['sha256Checksum']==digest and live['size']==part['size'] and live['trashed'] is False
                assert live['parents']==[folder['id']] and live['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
                rows.append(dict(**live, archive=name, local_part_sha256=digest))
            assert stream.read(1)==b''
        assert sha(path)==combined.hexdigest()
    # Tám file outer và evidence được đối chiếu với biên nhận nghiệm thu đã đóng.
    outer=ROOT/'research_tracking/runs/junyi-outer-real-20261117-01'
    accepted=json.loads((outer/'DRIVE_FINAL_ARCHIVE_ACCEPTANCE01.json').read_text(encoding='utf-8'))
    write('REUSED_MODEL_DRIVE01.json', dict(status='LOCAL_ARCHIVE_PARTS_MATCH_LIVE_DRIVE_SHA256', files=rows,
        outer_original_acceptance=accepted,
        coverage_index='research_tracking/runs/junyi-calibration-real-20261117-01/MODEL_DRIVE_COVERAGE03.json'))
    print('REUSED_MODELS_VERIFIED', len(rows), flush=True)


def make_catalog():
    original=json.loads((B/'TRAINING_OUTPUTS_CATALOG_DRAFT01.json').read_text(encoding='utf-8'))
    original['status']='INVENTORIED_TRAINING_OUTPUTS_WITH_VERIFIED_DRIVE_HANDOFF'
    original['remaining_neural_training_phases']=dict(total=21,junyi_learned=6,junyi_sakt_gkt=4,
        grade10_akt_refit=7,grade10_sakt_gkt_main=4,learned_junyi_deferral_applied=False)
    original['drive_new_archives']=json.loads((B/'NEW_ARCHIVES_DRIVE01.json').read_text(encoding='utf-8'))
    extra=json.loads((B/'CONFIDENCE_ARCHIVES_DRIVE01.json').read_text(encoding='utf-8'))
    original['drive_new_archives']['files']+=extra['files']
    original['drive_reused_models']=json.loads((B/'REUSED_MODEL_DRIVE01.json').read_text(encoding='utf-8'))
    original['drive_reused_evaluation_and_history']=json.loads((B/'REUSED_EVALUATION_HISTORY_DRIVE01.json').read_text(encoding='utf-8'))
    write('TRAINING_OUTPUTS_CATALOG01.json', original)
    inventory=json.loads((B/'PACKAGE_INVENTORY01.json').read_text(encoding='utf-8'))
    inventory['batches']+=json.loads((B/'CONFIDENCE_OUTPUTS_INVENTORY01.json').read_text(encoding='utf-8'))['batches']
    with (B/'FILE_INDEX01.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['archive','path','bytes','sha256'])
        writer.writeheader()
        for batch in inventory['batches']:
            for row in batch['files']:
                writer.writerow(dict(archive=batch['name'],**row))


def verify_existing_links(session):
    outer=json.loads((ROOT/'research_tracking/runs/junyi-outer-real-20261117-01/DRIVE_FINAL_ARCHIVE_ACCEPTANCE01.json').read_text(encoding='utf-8'))
    history=json.loads((ROOT/'research_tracking/runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json').read_text(encoding='utf-8'))
    rows=[]
    for row in outer['archives']:
        live=metadata(session,row['file_id'])
        assert live['sha256Checksum']==row['sha256'] and int(live['size'])==row['bytes']
        assert live['parents']==[outer['folder_id']] and live['trashed'] is False
        assert live['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
        rows.append(dict(group='outer',**live))
    allowed={r['id'] for r in history['folders']}
    for row in history['files']:
        live=metadata(session,row['id'])
        assert live['sha256Checksum']==row['local_sha256'] and int(live['size'])==row['bytes']
        assert len(live['parents'])==1 and live['parents'][0] in allowed and live['trashed'] is False
        assert live['owners'][0]['emailAddress']=='honguyenminhsang2005@gmail.com'
        rows.append(dict(group='history',**live))
    write('REUSED_EVALUATION_HISTORY_DRIVE01.json',dict(status='LIVE_DRIVE_CHECKSUM_OWNER_AND_PARENT_VERIFIED',files=rows,
        historical_source_preserved=True,original_history_receipt=str(ROOT/'research_tracking/runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json')))
    print('OUTER_AND_HISTORY_LINKS_VERIFIED',len(rows),flush=True)


def small_packet():
    paths={p for p in B.iterdir() if p.is_file() and p.suffix in {'.md','.html','.json','.csv','.py','.txt'}}
    paths.update(ROOT/p for p in (
        'docs/REPOSITORY_MAP.md',
        'research_tracking/reports/README.md',
        'research_tracking/reports/TRAINING_SCOPE_RECONCILIATION_20261115.md',
        'research_tracking/reports/SCOPE_AND_RESULT_INTEGRITY_REVIEW_20261118.md',
        'research_tracking/reports/RQ12_EXISTING_EVIDENCE_20261117.md',
        'research_tracking/reports/RQ12_MECHANISM_CLAIMS_20261117.md',
        'research_tracking/reports/THESIS_RESULTS_DISCUSSION_DRAFT_20261117.md',
        'research_tracking/runs/junyi-calibration-real-20261117-01/MODEL_DRIVE_COVERAGE03.json',
        'research_tracking/runs/junyi-calibration-real-20261117-01/GPU_OUTPUT_ACCEPTANCE01.json',
        'research_tracking/runs/junyi-calibration-real-20261117-01/LOCAL_A2_FIT_ACCEPTANCE100.json',
        'research_tracking/runs/junyi-calibration-real-20261117-01/LOCAL_A3_FIT_ACCEPTANCE101.json',
        'research_tracking/runs/drive-history-upload-20261116-01/READBACK_ACCEPTANCE.json',
    ))
    for run in ('paper2-statistical-reproduction-20261117-02','rq12-mechanism-closure-20261117-01',
                'rq12-existing-evidence-20261117-01','thesis-results-discussion-writing-20261117-01',
                'baseline-evaluation-readiness-20261117-01'):
        paths.update(p for p in (ROOT/'research_tracking/runs'/run).rglob('*') if p.is_file()
            and p.suffix in {'.md','.json','.csv','.py','.svg','.png','.txt','.log'} and '__pycache__' not in p.parts)
    paths.update(ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'/name
                 for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'))
    rows=[]; buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for path in sorted(paths):
            if path.name in {'PUBLICATION_DRIVE01.json','FINAL_MANIFEST01.json','HANDOFF_PACKET_INVENTORY01.json'}:
                continue
            assert path.exists() and path.stat().st_size<=10*1024**2, str(path)
            assert 'private' not in path.parts
            raw=path.read_bytes(); relative=path.relative_to(ROOT).as_posix()
            rows.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
            info=zipfile.ZipInfo(relative,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            output.writestr(info,raw)
        output.writestr('INVENTORY.json',json.dumps(rows,ensure_ascii=False,indent=2).encode())
    write('HANDOFF_PACKET_INVENTORY01.json',dict(files=rows))
    raw=buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        assert check.testzip() is None
        for row in rows:
            assert hashlib.sha256(check.read(row['path'])).hexdigest()==row['sha256']
    return raw


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from drive_stream_upload import upload_stream
    from write_handoff01 import main as write_report
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        assert pub.checked(session.get(pub.API+'/about',params={'fields':'user(emailAddress)'},timeout=60))['user']['emailAddress']=='honguyenminhsang2005@gmail.com'
        if '--verify-reused' in sys.argv:
            verify_reused(session)
            return
        if '--verify-links' in sys.argv:
            verify_existing_links(session)
            return
        folder=json.loads((B/'DRIVE_FOLDER01.json').read_text(encoding='utf-8'))
        make_catalog()
        write_report()
        from validate_handoff01 import main as validate
        validate()
        raw_packet=small_packet()
        published=[]
        pub.LIMIT=32*1024**2
        for name,mime in (('README.md','text/markdown'),('BAN_GIAO_TRAINING.html','text/html'),
                          ('TRAINING_OUTPUTS_CATALOG01.json','application/json'),('FILE_INDEX01.csv','text/csv'),
                          ('BAO_CAO.md','text/markdown'),('BAO_CAO_NGHIEN_CUU.html','text/html')):
            source = (B/name) if (B/name).exists() else ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'/name
            raw=source.read_bytes()
            meta=pub.small_file(session,folder['id'],name,raw,mime)
            published.append(pub.readback(session,meta['id'],len(raw),hashlib.sha256(raw).hexdigest()))
        raw=raw_packet
        digest=hashlib.sha256(raw).hexdigest()
        receipt=upload_stream(session,dict(folder_id=folder['id'],name='HANDOFF_EVIDENCE_AND_REPORT01.zip',
            total_bytes=len(raw),source_plan_sha256=sha(B/'HANDOFF_PACKET_INVENTORY01.json')),
            lambda:blocks(raw),PRIVATE/'handoff-packet-state.json',max_total_bytes=32*1024**2)
        published.append(pub.readback(session,receipt['file_id'],len(raw),digest))
        write('PUBLICATION_DRIVE01.json',dict(status='HANDOFF_INDEX_AND_EVIDENCE_MEDIA_READBACK_VERIFIED',folder=folder,files=published))
        print('HANDOFF_PUBLISHED',folder['webViewLink'],len(published),len(raw),flush=True)


if __name__=='__main__':
    main()
