"""Kiểm dung lượng và quyền Drive trước chuyển toàn bộ bộ bàn giao."""
from pathlib import Path
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))


def main():
    import publish_snapshot as pub
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        about=pub.checked(session.get(pub.API+'/about',params={'fields':'user(emailAddress),storageQuota'},timeout=60))
        assert about['user']['emailAddress']=='honguyenminhsang2005@gmail.com'
        quota=about['storageQuota']
        free=int(quota['limit'])-int(quota['usage']) if 'limit' in quota else None
        assert free is None or free>=12*1024**3
        parent=pub.checked(session.get(pub.API+'/files/'+pub.PARENT,params={'fields':'id,mimeType,capabilities(canAddChildren)'},timeout=60))
        assert parent['capabilities']['canAddChildren']
        usage=shutil.disk_usage(ROOT)
        assert usage.free>=12*1024**3
        result=dict(status='STORAGE_AND_ACCOUNT_READY',account=about['user']['emailAddress'],drive_parent=pub.PARENT,
            drive_free_bytes=free,local_free_bytes=usage.free,minimum_reserved_bytes=12*1024**3,
            plan='Source/hồ sơ đầy đủ, rawCSV, canonical/splits/sidecar/corpus, cache chuẩn chọn một bản, confidence spool và các outputs Drive đã kiểm; giữ nguyên gốc.')
        (B/'PREFLIGHT01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
