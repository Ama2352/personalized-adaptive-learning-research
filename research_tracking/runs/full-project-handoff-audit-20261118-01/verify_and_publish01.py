"""Kiểm allowlist và công bố hồ sơ tiếp quản, giữ rõ các phần chưa chuyển."""
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare():
    inputs=json.loads((B/'REQUIRED_INPUTS02.json').read_text(encoding='utf-8'))
    assert inputs['total_bytes']==611790510
    paths=set()
    for group in inputs['groups']:
        assert sum(r['bytes'] for r in group['files'])==group['bytes']
        for row in group['files']:
            path=ROOT/row['path']
            assert path.is_file() and path.stat().st_size==row['bytes']
            assert row['path'] not in paths
            paths.add(row['path'])
    assert len(paths)==790
    with (B/'FOLDER_DECISIONS01.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==234
    tests=[r for r in rows if r['path']=='artifacts/akt/local-tests']
    assert len(tests)==1 and tests[0]['role']=='RESEARCH_INPUT_AND_TEST_FIXTURES'
    source=json.loads((B/'CODE_AND_LOCAL_WORK01.json').read_text(encoding='utf-8'))
    assert source['remote_origin_configured'] is False and source['tracked_private_paths']==[]
    grade=json.loads((B/'GRADE10_SUPPORT01.json').read_text(encoding='utf-8'))
    assert len(grade['models'])==7 and len(grade['files'])==170
    assert sum(r['archive_status'].startswith('LOCAL_') for r in grade['models'])==5
    receipt=json.loads((B/'GRADE10_SUPPORT_DRIVE01.json').read_text(encoding='utf-8'))
    method=json.loads((B/'METHOD24_DRIVE02.json').read_text(encoding='utf-8'))
    assert receipt['independent_media_readback'] and method['independent_media_readback']
    report=(B/'README.md').read_text(encoding='utf-8')
    assert 'chưa phải bộ tiếp quản toàn project có thể chạy ngay' in report
    assert '0,612GB' in report and '69,83MB' in report
    qa=dict(status='HANDOFF_DEPENDENCIES_AND_FOLDER_DECISIONS_VALIDATED',
        source_files=790,core_bytes=611790510,core_bytes_remaining_without_separate_transfer=541957512,
        folder_decisions=234,grade_selected_models=7,grade_support_members=170,
        new_grade_support_bytes=receipt['bytes'],new_method24_bytes=method['bytes'],
        source_snapshot_transferred_in_this_audit=False,canonical_dataset_transferred_in_this_audit=False,
        cold_restore_executed=False,raw_file_hash_matches_preprocessing_manifest=True)
    (B/'QA01.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files=[p for p in B.iterdir() if p.is_file() and p.suffix in {'.md','.json','.csv','.py'}
           and p.name not in {'AUDIT_SNAPSHOT01.json','PUBLICATION_DRIVE01.json','PACKAGE_INVENTORY01.json'}]
    inventory=[];buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for path in sorted(files):
            raw=path.read_bytes();assert len(raw)<5*1024**2
            inventory.append(dict(path=path.name,bytes=len(raw),sha256=sha(raw)))
            info=zipfile.ZipInfo(path.name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            output.writestr(info,raw)
        output.writestr('INVENTORY.json',json.dumps(inventory,ensure_ascii=False,indent=2).encode())
    (B/'PACKAGE_INVENTORY01.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    raw=buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        assert check.testzip() is None
        for row in inventory:
            assert sha(check.read(row['path']))==row['sha256']
    print('AUDIT_QA_PASS',len(paths),'input files',len(rows),'folder decisions','ZIP',len(raw),flush=True)
    return raw


def main():
    raw=prepare()
    if '--upload' not in sys.argv:
        return
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    import publish_snapshot as pub
    from drive_stream_upload import upload_stream
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    folder=json.loads((B/'DRIVE_FOLDER01.json').read_text())
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        accepted=[];pub.LIMIT=5*1024**2
        for name,mime in (('README.md','text/markdown'),('REQUIRED_INPUTS02.json','application/json'),
                          ('FOLDER_DECISIONS01.csv','text/csv'),('STATE.json','application/json')):
            content=(B/name).read_bytes()
            meta=pub.small_file(session,folder['id'],name,content,mime)
            accepted.append(pub.readback(session,meta['id'],len(content),sha(content)))
        receipt=upload_stream(session,dict(folder_id=folder['id'],name='HANDOFF_DEPENDENCY_AUDIT01.zip',
            total_bytes=len(raw),source_plan_sha256=sha((B/'PACKAGE_INVENTORY01.json').read_bytes())),lambda:iter((raw,)),
            ROOT/'artifacts/akt/private/drive-upload/project-handoff-readiness-20261118-01/audit-state.json',max_total_bytes=5*1024**2)
        accepted.append(pub.readback(session,receipt['file_id'],len(raw),sha(raw)))
        (B/'PUBLICATION_DRIVE01.json').write_text(json.dumps(dict(status='AUDIT_REVIEW_AND_ALLOWLIST_MEDIA_READBACK_VERIFIED',
            folder=folder,files=accepted),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('AUDIT_PUBLISHED',folder['webViewLink'],len(accepted),'files',flush=True)


if __name__=='__main__':
    main()
