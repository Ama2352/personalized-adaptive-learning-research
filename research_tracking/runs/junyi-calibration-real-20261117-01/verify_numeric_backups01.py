"""Đọc lại metadata Drive, nghiệm thu hai numeric archive không tải binary."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
sys.path.insert(0, str(BUNDLE))
from fetch_calibration_metadata01 import ACCOUNT, API


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    credentials = Credentials.from_authorized_user_file(
        str(ROOT/'artifacts/akt/private/drive-upload/token.json'),
        ['https://www.googleapis.com/auth/drive'])
    rows = []
    with AuthorizedSession(credentials) as session:
        response = session.get(API+'/about', params={'fields': 'user(emailAddress)'}, timeout=30)
        response.raise_for_status()
        assert response.json()['user']['emailAddress'] == ACCOUNT
        for variant in ('A2', 'A3'):
            path = BUNDLE/f'{variant}_NUMERIC_DRIVE_BACKUP01.json'
            receipt = json.loads(path.read_text())
            assert receipt['status'] == 'REMOTE_STREAM_SHA256_VERIFIED'
            response = session.get(API+'/files/'+receipt['file_id'], params={
                'fields': 'id,name,size,sha256Checksum,owners(emailAddress),parents,trashed'}, timeout=30)
            response.raise_for_status()
            metadata = response.json()
            assert not metadata['trashed']
            assert metadata['name'] == receipt['name']
            assert int(metadata['size']) == receipt['bytes']
            assert metadata['sha256Checksum'] == receipt['sha256']
            assert metadata['parents'] == [receipt['folder_id']]
            assert any(owner.get('emailAddress') == ACCOUNT for owner in metadata['owners'])
            rows.append(dict(variant=variant, receipt=path.name,
                receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                metadata=metadata))
    telemetry = [json.loads(line) for line in
        (BUNDLE/'NUMERIC_STREAM_RESOURCE01.jsonl').read_text().splitlines()]
    result = dict(status='INDEPENDENT_DRIVE_METADATA_READBACK_PASS',
        verified_at=datetime.now(timezone.utc).isoformat(), account=ACCOUNT,
        variants=rows, total_bytes=sum(int(row['metadata']['size']) for row in rows),
        local_peak_rss_bytes=max(row['rss_bytes'] for row in telemetry),
        binary_download_to_local=False, modal_compute_used=False,
        scientific_limit_vi='Sao lưu numeric inference, chưa nghiệm thu calibration fit A2/A3.')
    output = BUNDLE/'NUMERIC_BACKUP_READBACK01.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], total_bytes=result['total_bytes'],
        local_peak_rss_bytes=result['local_peak_rss_bytes'])))


if __name__ == '__main__':
    main()
