"""Lưu báo cáo và bằng chứng nhỏ lên Drive, ZIP chỉ tồn tại trong RAM."""
from pathlib import Path
import hashlib
import io
import json
import re
import sys
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
PARENT = '1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7'
NAME = 'research-reports-20261117'
LIMIT = 5 * 1024**2
PRIVATE = ROOT/'artifacts/akt/private/drive-upload/report-snapshot-20261117-01'
REPORT = ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
API = 'https://www.googleapis.com/drive/v3'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare():
    files = {REPORT/'BAO_CAO.md', REPORT/'BAO_CAO_NGHIEN_CUU.html'}
    for run in ('paper2-statistical-reproduction-20261117-02',
                'rq12-mechanism-closure-20261117-01',
                'thesis-results-discussion-writing-20261117-01'):
        folder = ROOT/'research_tracking/runs'/run
        files.update(path for path in folder.rglob('*') if path.is_file() and '__pycache__' not in path.parts)
    files.update(ROOT/path for path in (
        'research_tracking/reports/THESIS_RESULTS_DISCUSSION_DRAFT_20261117.md',
        'research_tracking/reports/RQ12_EXISTING_EVIDENCE_20261117.md',
        'research_tracking/reports/TRAINING_RQ_SCOPE_REVIEW_20261116.md',
        'research_tracking/runs/paper2-statistical-reproduction-20261117-01/paper2-prediction-outcome-v01.svg',
        'research_tracking/runs/rq12-existing-evidence-20261117-01/rq1-ready-preview-v01.svg',
        'paper2/DC KLTN0127 23520355&23521338_LeVanTuan.pdf',
        'research_tracking/runs/supervisor-report-refresh-20261117-01/QA07.json',
        'research_tracking/runs/supervisor-report-refresh-20261117-01/MANIFEST07.json',
    ))
    links = []
    for path in (REPORT/'BAO_CAO.md', REPORT/'BAO_CAO_NGHIEN_CUU.html'):
        text = path.read_text(encoding='utf-8')
        targets = (re.findall(r'\]\(([^)]+)\)', text) if path.suffix == '.md'
                   else re.findall(r'(?:href|src)="([^\"]+)"', text))
        for target in targets:
            if target.startswith(('data:', 'http:', 'https:', '#')):
                continue
            source = (path.parent/unquote(target.strip('<>'))).resolve()
            if not source.is_file() or not source.is_relative_to(ROOT):
                raise ValueError('Liên kết nguồn báo cáo không tồn tại trong repository.')
            links.append(dict(report=path.relative_to(ROOT).as_posix(), target=target,
                              resolved=source.relative_to(ROOT).as_posix()))
            files.add(source)
    inventory, payloads = [], {}
    for path in sorted(files):
        relative = path.relative_to(ROOT).as_posix()
        if path.is_symlink() or '/private/' in relative or path.suffix.lower() not in {'.md','.html','.json','.csv','.py','.txt','.log','.svg','.pdf'}:
            raise ValueError('Có nguồn ngoài allowlist đóng gói.')
        raw = path.read_bytes()
        if len(raw) > LIMIT:
            raise ValueError('Một file vượt giới hạn snapshot nhỏ.')
        inventory.append(dict(path=relative, bytes=len(raw), sha256=digest(raw)))
        payloads[relative] = raw
    public = dict(kind='REPORT_RESEARCH_SNAPSHOT_V1', files=inventory,
                  local_source_links=links, limit_bytes=LIMIT,
                  exclusions=['Credentials', 'Model/checkpoint binaries', 'Datasets', 'Private upload state'])
    public_raw = (json.dumps(public, ensure_ascii=False, indent=2)+'\n').encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, raw in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
        archive.writestr('SNAPSHOT_INVENTORY.json', public_raw)
    archive_bytes = buffer.getvalue()
    if len(archive_bytes) > LIMIT or sum(row['bytes'] for row in inventory) > LIMIT:
        raise ValueError('Snapshot vượt giới hạn 5MiB, cần thu hẹp allowlist.')
    (BUNDLE/'INVENTORY.json').write_bytes(public_raw)
    (BUNDLE/'PLAN.json').write_text(json.dumps(dict(status='PREPARED_RAM_ONLY',
        parent=PARENT, folder_name=NAME, source_files=len(inventory),
        source_bytes=sum(row['bytes'] for row in inventory), zip_bytes=len(archive_bytes),
        zip_sha256=digest(archive_bytes), plan_sha256=digest(public_raw)), indent=2)+'\n')
    return archive_bytes, digest(public_raw)


def checked(response):
    if response.status_code not in (200, 201):
        raise RuntimeError(f'Drive HTTP {response.status_code}, không ghi body nhạy cảm.')
    return response.json()


def folder(session):
    about = checked(session.get(API+'/about', params={'fields':'user(emailAddress)'}, timeout=30))
    if about['user']['emailAddress'].lower() != 'honguyenminhsang2005@gmail.com':
        raise RuntimeError('Sai tài khoản Drive.')
    parent = checked(session.get(API+'/files/'+PARENT, params={'fields':'id,mimeType,trashed,capabilities(canAddChildren)'}, timeout=30))
    if (parent.get('trashed') or parent['mimeType'] != 'application/vnd.google-apps.folder'
            or not parent.get('capabilities',{}).get('canAddChildren')):
        raise RuntimeError('Chưa ghi được thư mục cha đã duyệt.')
    result = checked(session.get(API+'/files', params={'q':f"'{PARENT}' in parents and name = '{NAME}' and trashed = false", 'fields':'files(id,name,mimeType,parents,webViewLink)', 'pageSize':100}, timeout=30))
    matches = result['files']
    if len(matches) > 1:
        raise RuntimeError('Có nhiều thư mục snapshot cùng tên, cần phân giải.')
    if matches:
        target = matches[0]
    else:
        target = checked(session.post(API+'/files', json={'name':NAME,'mimeType':'application/vnd.google-apps.folder','parents':[PARENT]}, params={'fields':'id,name,mimeType,parents,webViewLink'}, timeout=30))
    if target['mimeType'] != 'application/vnd.google-apps.folder' or target['parents'] != [PARENT]:
        raise RuntimeError('Folder snapshot không khớp.')
    return target


def small_file(session, target, name, raw, mime):
    rows = checked(session.get(API+'/files', params={'q':f"'{target}' in parents and name = '{name}' and trashed = false", 'fields':'files(id,name,size,sha256Checksum,parents,webViewLink)', 'pageSize':100}, timeout=30))['files']
    if len(rows) > 1:
        raise RuntimeError('Có nhiều snapshot cùng tên, không ghi đè.')
    if rows:
        metadata = rows[0]
    else:
        boundary = 'kltn_snapshot_20261117_fixed'
        metadata_raw = json.dumps({'name':name,'parents':[target],'mimeType':mime}).encode()
        body = (f'--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'.encode()+metadata_raw+
                f'\r\n--{boundary}\r\nContent-Type: {mime}\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
        metadata = checked(session.post('https://www.googleapis.com/upload/drive/v3/files',
            params={'uploadType':'multipart','fields':'id,name,size,sha256Checksum,parents,webViewLink'},
            headers={'Content-Type':f'multipart/related; boundary={boundary}'}, data=body, timeout=180))
    if metadata.get('size') != str(len(raw)) or metadata.get('sha256Checksum') != digest(raw) or metadata.get('parents') != [target]:
        raise RuntimeError('File báo cáo đã tồn tại khác nội dung hoặc upload chưa đúng.')
    return metadata


def readback(session, file_id, expected_bytes, expected_sha):
    metadata = checked(session.get(API+'/files/'+file_id, params={'fields':'id,name,size,sha256Checksum,parents,webViewLink'}, timeout=30))
    if metadata.get('size') != str(expected_bytes) or metadata.get('sha256Checksum') != expected_sha:
        raise RuntimeError('Metadata đọc độc lập không khớp.')
    response = session.get(API+'/files/'+file_id, params={'alt':'media'}, stream=True, timeout=180)
    sha, count = hashlib.sha256(), 0
    try:
        if response.status_code != 200:
            raise RuntimeError('Không đọc lại được snapshot.')
        for block in response.iter_content(64*1024):
            count += len(block)
            if count > expected_bytes or count > LIMIT:
                raise RuntimeError('Readback vượt giới hạn byte.')
            sha.update(block)
    finally:
        response.close()
    if count != expected_bytes or sha.hexdigest() != expected_sha:
        raise RuntimeError('Nội dung readback không khớp SHA nguồn.')
    return dict(file_id=file_id, name=metadata['name'], bytes=count, sha256=expected_sha,
                url=metadata.get('webViewLink'), independent_media_readback=True)


def main():
    archive, source_sha = prepare()
    if '--upload' not in sys.argv:
        print('PREPARED',len(archive),'bytes; ZIP chỉ giữ trong RAM.')
        return
    sys.path.insert(0,str(ROOT/'scripts/akt'))
    from drive_stream_upload import upload_stream
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    credentials = Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    with AuthorizedSession(credentials) as session:
        destination = folder(session)
        target = destination['id']
        public = []
        for name,mime in (('BAO_CAO.md','text/markdown'),('BAO_CAO_NGHIEN_CUU.html','text/html')):
            raw=(REPORT/name).read_bytes()
            meta=small_file(session,target,name,raw,mime)
            public.append(readback(session,meta['id'],len(raw),digest(raw)))
        plan=dict(folder_id=target,name='KLTN_REPORT_EVIDENCE_20261117.zip',total_bytes=len(archive),source_plan_sha256=source_sha)
        receipt=upload_stream(session,plan,lambda:iter((archive,)),PRIVATE/'stream-state.json',max_total_bytes=LIMIT)
        public.append(readback(session,receipt['file_id'],len(archive),digest(archive)))
        result=dict(status='THREE_REPORT_FILES_INDEPENDENT_READBACK_VERIFIED',
                    folder=destination,files=public,archive_in_memory_only=True,
                    cloud_compute=False,model_binaries_uploaded=False)
        (BUNDLE/'DRIVE_READBACK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'folder':destination.get('webViewLink'),'files':len(public)},ensure_ascii=False))


if __name__=='__main__':
    main()
