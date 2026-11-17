"""Đọc gói Method24 nhỏ từ Drive, kiểm đủ32đầu vào theo inventory."""
from pathlib import Path
import json
import io
import hashlib
import zipfile
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
readback=json.loads((B/'READBACK.json').read_text(encoding='utf-8'))
row=next(r for r in readback['checks'] if r['actual']['name']=='GRADE10_METHOD24_INPUTS02.zip')
meta=row['actual']
assert int(meta['size'])<14*1024**2
with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
    response=session.get('https://www.googleapis.com/drive/v3/files/'+meta['id'],params={'alt':'media'},timeout=60,stream=True)
    response.raise_for_status()
    parts=[];total=0
    for chunk in response.iter_content(256*1024):
        total+=len(chunk)
        assert total<=14*1024**2
        parts.append(chunk)
raw=b''.join(parts)
assert len(raw)==int(meta['size']) and hashlib.sha256(raw).hexdigest()==meta['sha256Checksum']
inventory=json.loads((ROOT/'research_tracking/runs/full-project-handoff-audit-20261118-01/REQUIRED_INPUTS02.json').read_text(encoding='utf-8'))
group=next(g for g in inventory['groups'] if g['name']=='GRADE10_METHOD24_AND_CONDITIONS')
results=[]
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    for item in group['files']:
        data=archive.read(item['path'].replace('\\','/'))
        results.append(dict(path=item['path'],passed=len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']))
report=dict(drive_id=meta['id'],archive_sha256=meta['sha256Checksum'],bytes=len(raw),files=len(results),passed=sum(r['passed'] for r in results),checks=results)
(B/'METHOD24_READBACK.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('METHOD24',report['files'],report['passed'],'SHA256 matched')
