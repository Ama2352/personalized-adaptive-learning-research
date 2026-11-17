"""Lưu notebook CPU và bằng chứng kỹ thuật nhỏ, không tạo archive local."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
LIMIT = 5 * 1024**2
PARENT = '1XNJZvRBw62nNh21Qev_Sxt6SsV5u5943'
NOTEBOOK = ROOT/'notebooks/akt_colab_response_calibration_cpu.ipynb'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def helper():
    source = BUNDLE.parent/'report-drive-snapshot-20261117-01/publish_snapshot.py'
    spec = importlib.util.spec_from_file_location('snapshot_publish_reuse', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.PARENT, module.NAME = PARENT, 'technical-evidence20261117'
    return module


def prepare():
    files = {NOTEBOOK}
    for name in ('free-cpu-calibration-20261117-01','junyi-outer-readiness-20261117-01',
                 'junyi-outer-wrapper-20261117-01','junyi-outer-count-20261117-03'):
        files.update(path for path in (BUNDLE.parent/name).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts)
    files.update(ROOT/name for name in (
        'scripts/akt/free_cpu_calibration.py', 'scripts/akt/free_outer_evaluation.py',
        'scripts/akt/drive_resumable_upload.py', 'scripts/akt/calibration_audit_transaction.py',
        'tests/akt/test_free_cpu_calibration.py', 'tests/akt/test_free_outer_evaluation.py',
        'tests/akt/test_outer_frozen_cache_readiness.py',
        'research_tracking/reports/JUNYI_OUTER_EXECUTION_READINESS_20261117.md',
    ))
    files.update([BUNDLE/'INDEPENDENT_TESTS01.txt',BUNDLE/'INDEPENDENT_TESTS02.txt'])
    payloads, inventory = {}, []
    for path in sorted(files):
        name = path.relative_to(ROOT).as_posix()
        if path.is_symlink() or '/private/' in name or path.suffix not in {'.ipynb','.py','.md','.json','.jsonl','.txt','.xml','.log'}:
            raise ValueError('Nguồn ngoài allowlist kỹ thuật.')
        raw = path.read_bytes()
        if len(raw) > LIMIT:
            raise ValueError('Nguồn quá lớn.')
        inventory.append(dict(path=name,bytes=len(raw),sha256=digest(raw)))
        payloads[name] = raw
    if sum(row['bytes'] for row in inventory) > LIMIT:
        raise ValueError('Tổng nguồn vượt 5MiB.')
    document = dict(kind='FREE_CPU_TECHNICAL_EVIDENCE_SNAPSHOT_V2',files=inventory,
                    notebook_sha256=digest(NOTEBOOK.read_bytes()),source_commit='12a71bd7',
                    purpose='Launcher miễn phí và chuẩn bị outer, chưa là kết quả calibration A2/A3 hoặc outer thật')
    public_raw = (json.dumps(document,ensure_ascii=False,indent=2)+'\n').encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,raw in sorted({**payloads,'SNAPSHOT_INVENTORY.json':public_raw}.items()):
            info = zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type,info.external_attr=zipfile.ZIP_DEFLATED,0o100644 << 16
            archive.writestr(info,raw)
    raw_zip = output.getvalue()
    if len(raw_zip) > LIMIT:
        raise ValueError('ZIP vượt 5MiB.')
    (BUNDLE/'INVENTORY.json').write_bytes(public_raw)
    plan = dict(status='PREPARED_RAM_ONLY',source_files=len(inventory),
                source_bytes=sum(row['bytes'] for row in inventory),zip_bytes=len(raw_zip),
                zip_sha256=digest(raw_zip),source_plan_sha256=digest(public_raw),
                notebook_bytes=NOTEBOOK.stat().st_size,notebook_sha256=digest(NOTEBOOK.read_bytes()))
    (BUNDLE/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    return raw_zip,plan


def main():
    archive,plan = prepare()
    if '--upload' not in sys.argv:
        print(json.dumps(plan))
        return
    utility = helper()
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    from drive_stream_upload import upload_stream
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    credentials = Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    with AuthorizedSession(credentials) as session:
        folder = utility.folder(session)
        target = folder['id']
        notebook = NOTEBOOK.read_bytes()
        if digest(notebook) != plan['notebook_sha256']:
            raise ValueError('Notebook đổi sau khi đóng nguồn.')
        meta = utility.small_file(session,target,NOTEBOOK.name,notebook,'application/vnd.google.colaboratory')
        files = [utility.readback(session,meta['id'],len(notebook),digest(notebook))]
        metadata = utility.checked(session.get(utility.API+'/files/'+meta['id'],
            params={'fields':'id,mimeType,webViewLink'},timeout=30))
        if metadata['mimeType'] != 'application/vnd.google.colaboratory':
            raise ValueError('Notebook MIME chưa đúng Colab.')
        files[0]['mime_type'] = metadata['mimeType']
        zip_plan = dict(folder_id=target,name='KLTN_FREE_CPU_TECHNICAL_20261117_02.zip',
                        total_bytes=len(archive),source_plan_sha256=plan['source_plan_sha256'])
        state=ROOT/'artifacts/akt/private/drive-upload/technical-snapshot-20261117-02/stream-state.json'
        zipped=upload_stream(session,zip_plan,lambda:iter((archive,)),state,max_total_bytes=LIMIT)
        files.append(utility.readback(session,zipped['file_id'],len(archive),digest(archive)))
        result=dict(status='NOTEBOOK_AND_TECHNICAL_ZIP_INDEPENDENT_READBACK_VERIFIED',
                    folder=folder,files=files,local_binary_created=False,cloud_compute=False)
        (BUNDLE/'DRIVE_READBACK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'folder':folder.get('webViewLink'),'notebook_id':meta['id'],'notebook_url':meta.get('webViewLink')},ensure_ascii=False))


if __name__=='__main__':
    main()
