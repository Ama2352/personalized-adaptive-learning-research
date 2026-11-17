"""Chuyển runner/payload và access token đã duyệt tới đúng own CPU Colab."""
from datetime import datetime, timedelta, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts/akt'))
import colab_session as auth
from colab_cli_session import ensure_kernel, _proxy_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', default='COLAB_CPU_STAGING01.json')
    args = parser.parse_args()
    if not re.fullmatch(r'COLAB_CPU_STAGING[0-9]{2}\.json', args.receipt):
        raise RuntimeError('BOUNDED_STAGING_RECEIPT_REQUIRED')
    output = BUNDLE/args.receipt
    if output.exists():
        raise FileExistsError('STAGING_RECEIPT_ALREADY_EXISTS')
    from google.auth.transport.requests import AuthorizedSession
    import requests
    credentials = auth.load_credentials(auth.PRIVATE/'credentials.json')
    with AuthorizedSession(credentials) as account_session:
        assignment, kernel = ensure_kernel(account_session, auth.PRIVATE/'cli-runtime.json')
    auth.save_credentials(auth.PRIVATE/'credentials.json', credentials)
    host = urlsplit(assignment['runtimeProxyInfo']['url']).hostname
    if not host or not host.endswith('.prod.r.colab.dev'):
        raise RuntimeError('OWN_GOOGLE_COLAB_PROXY_REQUIRED')
    paths = [ROOT/'scripts/akt/colab_calibration_token_runner.py',
             ROOT/'research_tracking/runs/colab-token-calibration-20261117-01/PAYLOAD.json']
    rows = []
    with requests.Session() as proxy_session:
        for directory in ('content/kltn-free-cpu-tools', 'content/kltn-agent-private'):
            _proxy_request(proxy_session, assignment, 'PUT', 'api/contents/'+directory,
                           json={'type':'directory'})
        for path in paths:
            data = path.read_bytes()
            if len(data) > 256*1024:
                raise RuntimeError('TEXT_SOURCE_LIMIT_EXCEEDED')
            digest = hashlib.sha256(data).hexdigest()
            name = path.stem+'-'+digest[:12]+path.suffix
            remote = 'content/kltn-free-cpu-tools/'+name
            _proxy_request(proxy_session, assignment, 'PUT', 'api/contents/'+remote,
                           json={'type':'file', 'format':'text', 'content':data.decode('utf-8')})
            readback = _proxy_request(proxy_session, assignment, 'GET', 'api/contents/'+remote,
                                     params={'content':'1', 'format':'text'})
            if hashlib.sha256(readback['content'].encode('utf-8')).hexdigest() != digest:
                raise RuntimeError('REMOTE_SOURCE_SHA_MISMATCH')
            rows.append({'source':path.relative_to(ROOT).as_posix(), 'remote':'/'+remote,
                         'sha256':digest, 'bytes':len(data)})
        access = json.loads((auth.PRIVATE/'drive-access-export.json').read_text(encoding='utf-8'))
        if set(access) != {'access_token', 'expiry'}:
            raise RuntimeError('ONLY_ACCESS_AND_EXPIRY_ALLOWED')
        expiry = access['expiry']
        if (not isinstance(access['access_token'], str) or not access['access_token']
                or datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                < datetime.now(timezone.utc)+timedelta(minutes=45)):
            raise RuntimeError('FRESH_LOCAL_ACCESS_TOKEN_REQUIRED')
        remote = 'content/kltn-agent-private/drive-access.json'
        _proxy_request(proxy_session, assignment, 'PUT', 'api/contents/'+remote,
                       json={'type':'file', 'format':'text', 'content':json.dumps(access)})
        # Chỉ metadata được đọc lại cho file access token.
        metadata = _proxy_request(proxy_session, assignment, 'GET', 'api/contents/'+remote,
                                  params={'content':'0'})
        if (metadata.get('path') != remote or metadata.get('type') != 'file'
                or metadata.get('size') != len(json.dumps(access).encode('utf-8'))):
            raise RuntimeError('ACCESS_FILE_METADATA_MISMATCH')
    result = {'status':'CPU_SOURCE_PAYLOAD_AND_APPROVED_ACCESS_STAGED',
              'endpoint':assignment['endpoint'], 'kernel':kernel, 'files':rows,
              'access_file':'/'+remote, 'access_expiry':expiry,
              'authorization':'COLAB_EPHEMERAL_DRIVE_AUTHORIZATION01.json',
              'refresh_token_transferred':False, 'client_secret_transferred':False,
              'calibration_started':False}
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status':result['status'], 'source_files':len(rows),
                      'access_expiry':expiry, 'calibration_started':False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status':'CPU_STAGING_STOPPED', 'error_type':type(error).__name__}))
        raise SystemExit(1) from None
