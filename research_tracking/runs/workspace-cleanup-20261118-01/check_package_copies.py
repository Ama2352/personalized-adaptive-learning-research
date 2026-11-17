"""Kiểm các ZIP vận chuyển local đã có đúng bản trên Drive; không xóa."""
from pathlib import Path
import json,hashlib,threading,concurrent.futures
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
TRANSFER=ROOT/'research_tracking/runs/full-project-transfer-20261118-01'
LOCAL=threading.local()

def check(pair):
    path,asset=pair
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    st=path.stat()
    assert digest==asset['sha256'] and st.st_size==asset['bytes']
    if not hasattr(LOCAL,'s'):LOCAL.s=AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json')))
    response=LOCAL.s.get('https://www.googleapis.com/drive/v3/files/'+asset['file_id'],params={'fields':'id,name,size,sha256Checksum,parents,trashed,webViewLink'},timeout=60)
    response.raise_for_status();meta=response.json()
    assert meta['sha256Checksum']==digest and int(meta['size'])==st.st_size and not meta['trashed']
    return dict(path=path.relative_to(ROOT).as_posix(),bytes=st.st_size,sha256=digest,mtime_ns=st.st_mtime_ns,file_id=st.st_ino,nlink=st.st_nlink,drive=meta,passed=True)

def main():
    manifest=json.loads((TRANSFER/'MANIFEST_BAN_GIAO.json').read_text(encoding='utf-8'))
    assets={r['name']:r for r in manifest['assets']}
    paths=list((ROOT/'artifacts/akt/runtime/project-transfer-20261118-01/packages').iterdir())
    pairs=[(p,assets[p.name]) for p in paths if p.is_file() and p.name in assets]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(check,pairs))
    (B/'PACKAGE_COPIES_VERIFIED.json').write_text(json.dumps(dict(status='ALL_SELECTED_LOCAL_TRANSPORT_PACKAGES_HAVE_DRIVE_SHA_MATCH',files=rows,bytes=sum(r['bytes'] for r in rows)),ensure_ascii=False,indent=2),encoding='utf-8')
    print('TRANSPORT_COPIES',len(rows),sum(r['bytes'] for r in rows),'bytes verified on Drive',flush=True)

if __name__=='__main__':main()
