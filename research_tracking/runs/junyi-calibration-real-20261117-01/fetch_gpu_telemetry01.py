"""Lấy riêng telemetry vài KB đã ghim từ Drive, không tải model/prediction."""
import argparse
import hashlib
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
API = 'https://www.googleapis.com/drive/v3'
ACCOUNT = 'honguyenminhsang2005@gmail.com'


def main():
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    parser = argparse.ArgumentParser()
    parser.add_argument('variants', nargs='+', choices=['A1','A2','A3'])
    args = parser.parse_args()
    credentials = Credentials.from_authorized_user_file(
        str(ROOT/'artifacts/akt/private/drive-upload/token.json'), ['https://www.googleapis.com/auth/drive'])
    rows = []
    with AuthorizedSession(credentials) as session:
        about = session.get(API+'/about', params={'fields':'user(emailAddress)'}, timeout=30, allow_redirects=False)
        if about.status_code != 200 or about.json()['user']['emailAddress'] != ACCOUNT:
            raise RuntimeError('Drive account check failed')
        for variant in args.variants:
            publication = json.loads((BUNDLE/f'{variant}_GPU_METADATA_DRIVE01.json').read_text())
            entries = [(batch, row) for batch in publication['publications'] for row in batch['files']
                       if row['path'] == 'gpu-utilization.jsonl']
            if len(entries) != 1:
                raise RuntimeError('Unique telemetry receipt required')
            batch, row = entries[0]
            if batch['account'] != ACCOUNT or batch['status'] != 'DRIVE_SHA256_VERIFIED' or not 0 < row['bytes'] <= 16384:
                raise RuntimeError('Telemetry receipt outside permitted scope')
            target = BUNDLE/f'{variant}_GPU_UTILIZATION_ORIGINAL.jsonl'
            if target.exists():
                raw = target.read_bytes()
            else:
                meta = session.get(API+'/files/'+row['file_id'],
                    params={'fields':'id,size,sha256Checksum,parents,trashed'}, timeout=30, allow_redirects=False)
                if meta.status_code != 200:
                    raise RuntimeError('Telemetry metadata unavailable')
                value = meta.json()
                if (value.get('trashed') or value.get('sha256Checksum') != row['sha256']
                        or int(value.get('size',-1)) != row['bytes'] or batch['folder_id'] not in value['parents']):
                    raise RuntimeError('Telemetry remote metadata pin mismatch')
                response = session.get(API+'/files/'+row['file_id'], params={'alt':'media'},
                    stream=True, timeout=30, allow_redirects=False)
                if response.status_code != 200:
                    raise RuntimeError('Telemetry download failed')
                raw = b''
                for block in response.iter_content(4096):
                    raw += block
                    if len(raw) > 16384:
                        raise RuntimeError('Telemetry exceeds byte cap')
                response.close()
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise RuntimeError('Telemetry content pin mismatch')
            if not target.exists():
                with target.open('xb') as stream:
                    stream.write(raw)
            rows.append(dict(variant=variant, bytes=len(raw), sha256=row['sha256'], drive_id=row['file_id']))
    print(json.dumps(dict(status='TINY_TELEMETRY_PINNED', files=rows)))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit('Telemetry retrieval stopped: '+type(error).__name__) from None
