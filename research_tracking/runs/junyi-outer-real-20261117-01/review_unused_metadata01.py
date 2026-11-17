"""Đối chiếu danh mục cũ với file còn tồn tại, chưa cấp quyền xóa bằng metadata."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
catalog=ROOT/'experiments/akt/results/artifact-offload-20261116-01/UNUSED.csv'
totals={};keepers={}
with catalog.open(encoding='utf-8-sig',newline='') as stream:
    for row in csv.DictReader(stream):
        if row['category']!='UNUSED_VERIFIED_DUPLICATE':
            continue
        path=ROOT/row['path'];keeper=ROOT/row['keeper']
        size=int(row['bytes'])
        if not path.is_file():
            status='SOURCE_ALREADY_ABSENT'
        else:
            stat=path.stat()
            if row['keeper'] not in keepers:
                keepers[row['keeper']]=keeper.stat().st_size if keeper.is_file() else None
            retained=keepers[row['keeper']]
            if retained is None:
                status='SOURCE_PRESENT_KEEPER_ABSENT_REVIEW_REMOTE_RELOCATION'
            elif stat.st_size!=size or retained!=size:
                status='SIZE_CHANGED_REVIEW_REQUIRED'
            elif stat.st_mtime_ns!=int(row['modified_ns']):
                status='SAME_SIZE_MTIME_CHANGED_REHASH_REQUIRED'
            else:
                status='SAME_SIZE_MTIME_KEEPER_PRESENT_REHASH_AND_LINK_CHECK_REQUIRED'
        group=totals.setdefault(status,dict(files=0,logical_bytes=0))
        group['files']+=1;group['logical_bytes']+=size
result=dict(status='METADATA_REVIEW_ONLY_NOT_DELETE_ALLOWLIST',source=str(catalog.relative_to(ROOT)),
    groups=totals,note='SHA cũ chưa thay việc hash lại source/keeper và kiểm hardlink/Drive. Không cộng các mục thành dung lượng chắc chắn giải phóng.')
(B/'UNUSED_CURRENT_METADATA01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)
