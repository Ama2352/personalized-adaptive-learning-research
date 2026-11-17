"""Đóng trạng thái bàn giao, giữ biên nhận hoàn tất công khai trên Drive."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'research_tracking/runs/report-drive-snapshot-20261117-01'))
import publish_snapshot as pub


def main():
    state=json.loads((B/'STATE.json').read_text(encoding='utf-8'))
    publication=json.loads((B/'PUBLICATION_DRIVE01.json').read_text(encoding='utf-8'))
    assert publication['status']=='HANDOFF_INDEX_AND_EVIDENCE_MEDIA_READBACK_VERIFIED'
    assert len(publication['files'])==7 and all(r['independent_media_readback'] for r in publication['files'])
    state.update(status='COMPLETE_TRAINING_OUTPUTS_HANDOFF_DRIVE_ACCEPTED',updated='2026-11-18',
        closed=True,drive_folder=publication['folder'],publication='PUBLICATION_DRIVE01.json',
        next='Người nhận đọc README/HTML, được chia sẻ quyền thư mục gốc, nghiệm thu input dependencies trước chạy tiếp; ưu tiên bằng chứng quyết định/vòng kín và đối chứng cốt lõi.',
        limitations=['Đã bàn giao đầu ra training; dataset gốc, runtime và SQLite/cache đầu vào cần chuyển hoặc tái dựng riêng đúng manifest.',
                     'Quyền truy cập đã kiểm bằng chủ Sang; tài khoản người nhận chưa được cung cấp để kiểm.',
                     'Source/protocol archive là snapshot lúc kiểm kê; hai chỉ mục vận hành cập nhật sau đó có bản mới trong gói evidence.',
                     'Đã kiểm cấu trúc HTML và nội dung/Drive readback; lượt này chưa kiểm giao diện bằng trình duyệt.'],
        cloud_compute_used=False,new_training_executed=False,
        research_interpretation='Kết luận theo mức bằng chứng, hiệu ứng, bất định và điều kiện áp dụng; kết quả âm hoặc bất định được giữ.')
    (B/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.credentials import Credentials
    with AuthorizedSession(Credentials.from_authorized_user_file(str(ROOT/'artifacts/akt/private/drive-upload/token.json'))) as session:
        rows=[];pub.LIMIT=5*1024**2
        for name,source in (('HANDOFF_STATUS01.json',B/'STATE.json'),('PUBLICATION_READBACK01.json',B/'PUBLICATION_DRIVE01.json')):
            raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            meta=pub.small_file(session,publication['folder']['id'],name,raw,'application/json')
            rows.append(pub.readback(session,meta['id'],len(raw),digest))
        (B/'COMPLETION_DRIVE01.json').write_text(json.dumps(dict(status='FINAL_STATUS_AND_RECEIPT_MEDIA_READBACK_VERIFIED',files=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paths=[p for p in B.iterdir() if p.is_file() and p.name!='FINAL_MANIFEST01.json']
    paths.extend(ROOT/p for p in ('docs/REPOSITORY_MAP.md','research_tracking/reports/README.md',
        'research_tracking/reports/SCOPE_AND_RESULT_INTEGRITY_REVIEW_20261118.md',
        'research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO.md',
        'research_tracking/supervisor_reports/2026-11-16/01_tien_do/BAO_CAO_NGHIEN_CUU.html'))
    inventory=[]
    for path in sorted(paths):
        raw=path.read_bytes()
        inventory.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    (B/'FINAL_MANIFEST01.json').write_text(json.dumps(dict(status='CLOSED_HANDOFF_LOCAL_FILE_MANIFEST',files=inventory),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('HANDOFF_CLOSED',len(inventory),'files',publication['folder']['webViewLink'],flush=True)


if __name__=='__main__':
    main()
