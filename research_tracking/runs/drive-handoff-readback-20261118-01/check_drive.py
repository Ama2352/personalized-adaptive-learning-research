"""Kiểm chỉ đọc metadata Drive theo biên nhận bàn giao; không tải payload."""
from pathlib import Path
import json
import concurrent.futures
import threading
import datetime
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'research_tracking/runs/full-project-transfer-20261118-01'
OUT = Path(__file__).resolve().parent
API = 'https://www.googleapis.com/drive/v3'
FIELDS = 'id,name,mimeType,size,sha256Checksum,parents,trashed,webViewLink,owners(emailAddress)'
LOCAL = threading.local()

def read(name):
    return json.loads((B / name).read_text(encoding='utf-8'))

def get(route, params):
    if not hasattr(LOCAL, 'session'):
        LOCAL.session = AuthorizedSession(Credentials.from_authorized_user_file(
            str(ROOT / 'artifacts/akt/private/drive-upload/token.json')))
    response = LOCAL.session.get(API + route, params=params, timeout=45)
    if response.status_code != 200:
        return {'http_status': response.status_code}
    return response.json()

def check(row):
    expected = row['meta']
    actual = get('/files/' + expected['id'], {'fields': FIELDS})
    errors = [k for k in ('id', 'name', 'size', 'sha256Checksum', 'parents')
              if actual.get(k) != expected.get(k)]
    if actual.get('trashed') is not False:
        errors.append('trashed')
    return dict(role=row['role'], drive_path=row['path'], expected=expected,
                actual=actual, passed=not errors, mismatches=errors)

def children(folder):
    found = []
    token = None
    while True:
        params = {'q': "'%s' in parents and trashed=false" % folder,
                  'pageSize': 1000, 'fields': 'nextPageToken,files(' + FIELDS + ')'}
        if token:
            params['pageToken'] = token
        data = get('/files', params)
        if 'http_status' in data:
            return folder, data
        found.extend(data.get('files', []))
        token = data.get('nextPageToken')
        if not token:
            return folder, found

def main():
    rows = []
    for row in (read('UPLOADED_PACKAGES01.json')['files'] +
                [read('SUPPLEMENT_UPLOAD01.json')] + read('ORIGINAL_RUNS_UPLOAD01.json')['files']):
        rows.append(dict(meta=row, role=row['role'], path=row['drive_path']))
    for row in read('COPIED_ASSETS01.json')['files']:
        rows.append(dict(meta=row['destination'], role=row['role'], path=row['drive_path']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(check, rows))
    folders = {}
    queue = [read('DRIVE_MASTER01.json')['id']]
    tree = []
    while queue:
        batch, queue = queue, []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for folder, found in pool.map(children, batch):
                folders[folder] = found
                if isinstance(found, list):
                    tree.extend(found)
                    queue.extend(r['id'] for r in found
                                 if r['mimeType'] == 'application/vnd.google-apps.folder')
    known = {r['meta']['id'] for r in rows}
    tree_ids = {r['id'] for r in tree}
    groups = {}
    for row in results:
        group = groups.setdefault(row['role'], dict(files=0, bytes=0, passed=0))
        group['files'] += 1
        group['bytes'] += int(row['expected']['size'])
        group['passed'] += row['passed']
    summary = dict(as_of_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   expected_files=len(results), passed=sum(r['passed'] for r in results),
                   failed=[r for r in results if not r['passed']],
                   outside_master=[r['drive_path'] for r in results if r['expected']['id'] not in tree_ids],
                   groups=groups,
                   folder_errors={k:v for k,v in folders.items() if not isinstance(v,list)},
                   tree_files=sum(r['mimeType'] != 'application/vnd.google-apps.folder' for r in tree),
                   extra_files=[r for r in tree if r['mimeType'] != 'application/vnd.google-apps.folder' and r['id'] not in known],
                   limits=['Kiểm metadata SHA256, không tải lại payload hoặc cold restore; chưa kiểm quyền tài khoản người nhận.'])
    (OUT / 'READBACK.json').write_text(json.dumps(dict(summary=summary, checks=results, folders=folders),
                                                ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
