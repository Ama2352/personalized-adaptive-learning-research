"""Bổ sung phụ thuộc Method24 thật đang nằm trong local-tests, giữ inventory V1."""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    original=json.loads((B/'REQUIRED_INPUTS01.json').read_text(encoding='utf-8'))
    index=json.loads((ROOT/'experiments/akt/results/model-export-20261112-01/MODEL_INDEX.json').read_text())
    expected={}
    for row in index['entries']:
        if row['dataset']=='Grade10':
            method=row['checkpoint_metadata']['identity']['condition'].get('method24_scores')
            if isinstance(method,dict):
                expected.update(dict(method['artifacts_sha256']))
    operation=ROOT/'artifacts/akt/local-tests/akt-research-runner-20261108-01'
    source=json.loads((operation/'method24-native01/input-source-inventory.json').read_text())['sources_before']
    expected.update({name:value for name,value in source.items() if name.startswith('artifacts/')})
    paths={ROOT/name for name in expected}
    paths.update(p for p in (operation/'main60-graph-conditions02').rglob('*') if p.is_file())
    paths.add(ROOT/'artifacts/akt/local-tests/development-corpus-20261108-01/canonical-corpus-inventory01.json')
    rows=[]
    for path in sorted(paths):
        name=path.relative_to(ROOT).as_posix();digest=sha(path)
        if name in expected:
            assert digest==expected[name],name
        rows.append(dict(path=name,bytes=path.stat().st_size,sha256=digest))
    group=dict(name='GRADE10_METHOD24_AND_CONDITIONS',files=rows,bytes=sum(r['bytes'] for r in rows),
        drive_coverage='Gói riêng GRADE10_METHOD24_INPUTS02.zip cần nghiệm thu hoặc phục hồi chính xác trước tiếp tục.',
        reason='Phụ thuộc nghiên cứu thật, được graph/CG-AKT Main60 tham chiếu bằng SHA; tên local-tests chưa biểu thị đúng mức sử dụng.')
    original['groups'].append(group);original['total_bytes']+=group['bytes']
    original['revision']=dict(supersedes='REQUIRED_INPUTS01.json',
        reason='Truy ngược MODEL_INDEX/MainGraphInput phát hiện Method24 thật nằm trong local-tests; bổ sung32file thay vì phân loại toàn thư mục là fixture.')
    (B/'REQUIRED_INPUTS02.json').write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for row in rows:
            raw=(ROOT/row['path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row['sha256']
            info=zipfile.ZipInfo(row['path'],(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,raw)
        archive.writestr('METHOD24_INPUT_INVENTORY.json',json.dumps(group,ensure_ascii=False,indent=2).encode())
    raw=buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert archive.testzip() is None
        for row in rows:
            assert hashlib.sha256(archive.read(row['path'])).hexdigest()==row['sha256']
    print('METHOD24_INPUTS_VERIFIED',len(rows),group['bytes'],'ZIP',len(raw),'TOTAL_CORE',original['total_bytes'],flush=True)
    if '--upload' not in sys.argv:
        return
    sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    import publish_snapshot as pub
    from drive_stream_upload import upload_stream
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    folder=json.loads((B/'DRIVE_FOLDER01.json').read_text())
    def chunks():
        for offset in range(0,len(raw),8*1024**2):
            yield raw[offset:offset+8*1024**2]
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        receipt=upload_stream(session,dict(folder_id=folder['id'],name='GRADE10_METHOD24_INPUTS02.zip',
            total_bytes=len(raw),source_plan_sha256=hashlib.sha256(json.dumps(group,sort_keys=True).encode()).hexdigest()),chunks,
            ROOT/'artifacts/akt/private/drive-upload/project-handoff-readiness-20261118-01/method24-state.json',max_total_bytes=32*1024**2)
        pub.LIMIT=32*1024**2
        accepted=pub.readback(session,receipt['file_id'],len(raw),hashlib.sha256(raw).hexdigest())
        (B/'METHOD24_DRIVE02.json').write_text(json.dumps(accepted,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('METHOD24_INPUTS_DRIVE_ACCEPTED',accepted['url'],flush=True)


if __name__=='__main__':
    main()
