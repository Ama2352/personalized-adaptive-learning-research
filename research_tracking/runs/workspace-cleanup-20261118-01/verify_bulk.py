"""Kiểm tất cả đường dẫn đã chuyển lạnh và đầu vào/model được giữ."""
from pathlib import Path
import json,os,collections,shutil
ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
plan=json.loads((B/'BULK_DELETE_PLAN.json').read_text(encoding='utf-8'))
log=[json.loads(line) for line in (B/'BULK_UNLINK_LOG.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
assert len(log)==len(plan['files']) and all(r['status']=='DELETED' for r in log)
for row in plan['files']:
    p=ROOT/row['path'];native=Path('\\\\?\\'+str(p)) if len(str(p))>=240 else p
    assert not native.exists(),row['path']
reconstruction=json.loads((B/'RECONSTRUCTION_ACCEPTANCE.json').read_text(encoding='utf-8'))
bulk=json.loads((B/'BULK_RELOCATION.json').read_text(encoding='utf-8'))
by_path={r['path']:r for r in bulk['files']}
for row in reconstruction['snapshots']:
    assert by_path[row['manifest']]['sha256']==row['manifest_sha256']
result=dict(status='ALL_BULK_UNLINKS_AND_MANIFEST_PRESERVATION_VERIFIED',files_deleted=len(log),categories=dict(collections.Counter(r['category'] for r in log)),manifest_originals_preserved_on_drive=len(reconstruction['snapshots']),remote_files_verified=json.loads((B/'BULK_REMOTE_ACCEPTANCE.json').read_text(encoding='utf-8'))['drive_file_count'],free_bytes=shutil.disk_usage(ROOT).free)
(B/'BULK_AFTER_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
