"""Lấy ba member Grade10 A0 bằng HTTP Range, không tải archive/checkpoint."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CAP = 4*1024**2


class RangedZip(io.RawIOBase):
    def __init__(self, session, file_id, size, budget):
        self.session, self.file_id, self.size, self.budget = session, file_id, size, budget
        self.position = 0
        self.bytes_read = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position+offset if whence == 1 else self.size+offset
        if whence not in (0,1,2) or not 0 <= position <= self.size:
            raise ValueError('ZIP seek ngoài archive')
        self.position = position
        return position

    def read(self, count=-1):
        count = self.size-self.position if count < 0 else min(count, self.size-self.position)
        if count == 0:
            return b''
        if count > self.budget-self.bytes_read:
            raise ValueError('Range response vượt ngân sách4MiB')
        start, stop = self.position, self.position+count-1
        url = 'https://www.googleapis.com/drive/v3/files/'+self.file_id
        with self.session.get(url, params={'alt':'media'}, headers={'Range':f'bytes={start}-{stop}',
                'Accept-Encoding':'identity'}, stream=True, timeout=30) as response:
            if response.status_code != 206 or response.headers.get('Content-Range') != f'bytes {start}-{stop}/{self.size}':
                raise ValueError('Drive không trả đúng Range, không đọc full body')
            data = bytearray()
            for chunk in response.iter_content(65536):
                if len(data)+len(chunk) > count:
                    raise ValueError('Range body vượt kích thước đã yêu cầu')
                data.extend(chunk)
            if len(data) != count:
                raise ValueError('Range body thiếu byte')
        self.bytes_read += count
        self.position += count
        return bytes(data)


def bounded_json(session, url, params):
    with session.get(url, params=params, stream=True, timeout=30) as response:
        if response.status_code != 200:
            raise ValueError('Drive metadata chưa đọc được')
        raw = bytearray()
        for chunk in response.iter_content(4096):
            if len(raw)+len(chunk)>32768:
                raise ValueError('Drive metadata vượt giới hạn')
            raw.extend(chunk)
    return json.loads(raw), len(raw)


def fetch(session, model='A0'):
    runs={'A0':'modal-main60-a0-selected-20261112-01','A1_EXPERT':'modal-main60-a1-expert-selected-20261112-02'}
    if model not in runs:
        raise ValueError('Demo rangefetch chỉ nhận hai archive đã xác định')
    run=runs[model]
    relocation = json.loads((ROOT/'research_tracking/runs/history-cleanup-20261117-01/RELOCATION_MANIFEST.json').read_text())
    group = next(row for row in relocation['groups']
                 if 'experiments/akt/results/'+run+'/artifacts.zip' in row['paths'])
    account, account_bytes = bounded_json(session, 'https://www.googleapis.com/drive/v3/about', {'fields':'user(emailAddress)'})
    if account['user']['emailAddress'] != 'honguyenminhsang2005@gmail.com':
        raise ValueError('Drive account chưa đúng Sang')
    meta, meta_bytes = bounded_json(session, 'https://www.googleapis.com/drive/v3/files/'+group['remote_id'],
        {'fields':'id,name,size,sha256Checksum,trashed,owners(emailAddress)'})
    if (meta['id'] != group['remote_id'] or int(meta['size']) != group['bytes']
            or meta['sha256Checksum'] != group['sha256'] or meta.get('trashed')):
        raise ValueError('Archive Drive không khớp relocation đã nghiệm thu')
    previous=sum(json.loads(path.read_text())['response_bytes'] for path in HERE.glob('*_RANGE_RECEIPT.json'))
    stream = RangedZip(session, group['remote_id'], group['bytes'], CAP-previous-account_bytes-meta_bytes)
    prefix = 'experiments/akt/results/'+run+'/'
    names = ['SHA256.json', prefix+'selection/predictions.csv', prefix+'selection/targets.csv']
    members = {}
    with zipfile.ZipFile(stream) as archive:
        for name in names:
            info = archive.getinfo(name)
            if info.file_size > 1024**2 or info.compress_size > 1024**2:
                raise ValueError('Member demo vượt1MiB')
            members[name] = archive.read(info)
    certificate = json.loads(members['SHA256.json'])
    entries = {}
    destination = HERE/('source-'+model.lower().replace('_','-'))
    destination.mkdir(exist_ok=False)
    for name, raw in members.items():
        sha = hashlib.sha256(raw).hexdigest()
        if name != 'SHA256.json' and (certificate[name]['sha256'] != sha or certificate[name]['bytes'] != len(raw)):
            raise ValueError('Member SHA/size không khớp certificate')
        path = destination/Path(name).name
        with path.open('xb') as output:
            output.write(raw)
        entries[path.name] = dict(bytes=len(raw), sha256=sha, archive_member=name)
    receipt = dict(status='SELECTED_MEMBERS_RANGE_VERIFIED', model=model, archive_drive_id=group['remote_id'],
        archive_bytes=group['bytes'], archive_sha256=group['sha256'], media_bytes=stream.bytes_read,
        metadata_bytes=account_bytes+meta_bytes, response_bytes=stream.bytes_read+account_bytes+meta_bytes,
        budget_bytes=CAP, cumulative_response_bytes=previous+stream.bytes_read+account_bytes+meta_bytes,
        members=entries, full_archive_downloaded=False, model_weights_downloaded=False)
    with (HERE/(model+'_RANGE_RECEIPT.json')).open('x', encoding='utf-8') as output:
        json.dump(receipt, output, ensure_ascii=False, indent=2)
    print(json.dumps(dict(status=receipt['status'], response_bytes=receipt['response_bytes'], members=len(entries))))


if __name__ == '__main__':
    try:
        import argparse
        parser=argparse.ArgumentParser()
        parser.add_argument('--model',choices=('A0','A1_EXPERT'),default='A0')
        args=parser.parse_args()
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2.credentials import Credentials
        credentials = Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))
        with AuthorizedSession(credentials) as session:
            fetch(session,args.model)
    except Exception as exc:
        with (HERE/'RANGE_FAILURE.json').open('x', encoding='utf-8') as output:
            json.dump(dict(status='RANGE_FETCH_FAILED', error_type=type(exc).__name__), output)
        raise SystemExit('Lấy member A0 dừng ở '+type(exc).__name__) from None
