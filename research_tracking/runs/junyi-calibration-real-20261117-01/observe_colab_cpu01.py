"""Đọc trạng thái/log của phase CPU đang có, không gửi lại code."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts/akt'))
import colab_session as auth
from colab_cli_session import _proxy_request


def optional_file(session, assignment, path, *, content=True):
    try:
        value = _proxy_request(session, assignment, 'GET', 'api/contents/'+path.lstrip('/'),
                               params={'content':'1' if content else '0', 'format':'text'})
        return value.get('content') if content else value
    except auth.ColabSessionError as error:
        if str(error) == 'COLAB_CLI_HTTP_404':
            return None
        raise


def main():
    import requests
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=('A2','A3'), default='A2')
    args = parser.parse_args()
    phase = args.variant.lower()+'-calibration-free-cpu-20261117-02'
    state = json.loads((auth.PRIVATE/'cli-runtime.json').read_text(encoding='utf-8'))
    job = state.get('phases', {}).get(phase)
    if job is None:
        raise RuntimeError('PHASE_NOT_SENT')
    with requests.Session() as session:
        marker = optional_file(session, state['assignment'], job['remote_status_path'])
        progress = optional_file(session, state['assignment'],
            '/content/kltn-free-cpu-tools/STATUS_'+args.variant+'.json')
        text = optional_file(session, state['assignment'],
            '/content/kltn-free-cpu-tools/'+args.variant+'_CPU02.log')
        secret = optional_file(session, state['assignment'],
            '/content/kltn-agent-private/drive-access.json', content=False)
    row = {'observed_at':datetime.now(timezone.utc).isoformat(), 'variant':args.variant,
           'marker':json.loads(marker) if marker else None,
           'progress':json.loads(progress) if progress else None,
           'temporary_access_file_exists':secret is not None}
    if text is not None:
        local = BUNDLE/('COLAB_'+args.variant+'_CPU_LOG02.txt')
        previous = local.read_text(encoding='utf-8') if local.exists() else ''
        if not text.startswith(previous):
            raise RuntimeError('REMOTE_LOG_PREFIX_CHANGED')
        with local.open('a', encoding='utf-8', newline='') as stream:
            stream.write(text[len(previous):])
        row['log_bytes'] = len(text.encode('utf-8'))
        row['log_tail'] = text[-3500:]
    with (BUNDLE/'COLAB_CPU_OBSERVATIONS01.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, ensure_ascii=False)+'\n')
    print(json.dumps(row, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status':'CPU_OBSERVATION_STOPPED', 'error_type':type(error).__name__}))
        raise SystemExit(1) from None
