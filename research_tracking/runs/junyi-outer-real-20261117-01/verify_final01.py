"""Kiểm cuối source archive Drive và hai báo cáo, không model/data/GPU."""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research_tracking/runs/junyi-calibration-real-20261117-01'))

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    from fetch_calibration_metadata01 import MetadataDrive,API
    publication=json.loads((B/'REPORT_DRIVE01.json').read_text())
    report=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
    for entry in publication['files']:
        assert digest((report/entry['name']).read_bytes())==entry['sha256']
    html=(report/'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
    outer=re.search(r'<section id="outer-progress">.*?</section>',html,re.S).group(0)
    assert len(re.findall('<tr><td>A[0-3]</td>',outer))==4
    assert outer.count('<svg ')==1 and '24 phép so' in outer
    assert 'ngoại lệ quy trình' in outer and '0,360433' in outer
    credentials=Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
    session=AuthorizedSession(credentials);drive=MetadataDrive(session)
    evidence=json.loads((B/'EVIDENCE_DRIVE01.json').read_text())
    response=drive.get('/files/'+evidence['file_id'],params={'alt':'media'})
    raw=response.content
    assert len(raw)==evidence['bytes'] and digest(raw)==evidence['sha256']
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        inventory=json.loads(archive.read('INVENTORY.json'))
        for name,pin in inventory.items():
            payload=archive.read(name)
            assert len(payload)==pin['bytes'] and digest(payload)==pin['sha256']
        compatibility=json.loads((B/'handoff/A0.compatibility.json').read_text())
        for name,pin in compatibility['new_files'].items():
            assert digest(archive.read('frozen-source/'+name))==pin
    result=dict(status='FINAL_REPORTS_AND_DRIVE_SOURCE_ARCHIVE_BODY_VERIFIED',source_files=len(inventory),
        exact_runtime_source_files=len(compatibility['new_files']),evidence_file_id=evidence['file_id'],
        evidence_bytes=len(raw),report_file_hashes_match_drive=True,outer_table_rows=4,
        scope='Junyi Developmentfold4 expert one training seed; documented late statistical-plan freeze')
    (B/'FINAL_ACCEPTANCE01.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    main()
