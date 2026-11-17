"""Xác nhận bản gỡ, keeper, manifest và dung lượng thực sau dọn."""
from pathlib import Path
import json,hashlib,shutil,collections,concurrent.futures
from prepare import ROOT,B,sha

def main():
    plan=json.loads((B/'DELETE_PLAN.json').read_text(encoding='utf-8'))
    log=[json.loads(line) for line in (B/'UNLINK_LOG.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    deleted={r['path']:r for r in log if r['status']=='DELETED'}
    assert len(log)==len(plan['files']) and len({r['path'] for r in log})==len(log)
    for row in plan['files']:
        if row['path'] in deleted:assert not (ROOT/row['path']).exists(),row['path']
    keepers={r['keeper']:(r['bytes'],r['sha256']) for r in plan['files'] if r.get('keeper')}
    def check(item):
        path,pin=item;digest,st=sha(ROOT/path)
        assert st.st_size==pin[0] and digest==pin[1],path
        return True
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:verified=sum(pool.map(check,keepers.items()))
    recon=json.loads((B/'RECONSTRUCTION_ACCEPTANCE.json').read_text(encoding='utf-8'))
    for row in recon['snapshots']:
        assert hashlib.sha256((ROOT/row['manifest']).read_bytes()).hexdigest()==row['manifest_sha256']
    before=json.loads((B/'SCAN_BEFORE.json').read_text(encoding='utf-8'))['free_bytes']
    free=shutil.disk_usage(ROOT).free
    counts=collections.Counter(r['category'] for r in deleted.values())
    result=dict(status='DELETED_ABSENT_KEEPERS_AND_ORIGINAL_SNAPSHOT_MANIFESTS_VERIFIED',deleted_files=len(deleted),kept_on_error=[r for r in log if r['status']!='DELETED'],keeper_files_verified=verified,snapshot_manifests_unchanged=len(recon['snapshots']),categories=dict(counts),free_before_run_bytes=before,free_after_run_bytes=free,measured_free_increase_from_run_start_bytes=free-before,logical_unlinked_bytes=sum(r['bytes'] for r in deleted.values()),limits=['Tổng logic không bằng dung lượng trả lại vì hardlink; phần zip tạm được tạo và gỡ trong cùng lượt.','496thư mục quét bị chặn quyền được giữ nguyên, không đổi ACL.'])
    (B/'AFTER_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
