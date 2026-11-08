"""Lưu hai lượt kiểm chưa được nghiệm thu; không chạy lại tests hoặc Gate."""
from pathlib import Path
import sys,hashlib,json
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
one=json.loads((P/'gate_isolation01/terminal_unknown.json').read_bytes())
two=json.loads((P/'gate_isolation02-owned/final.json').read_bytes())
owned=json.loads((P/'gate_isolation02-owned/outer_receipt.json').read_bytes())
assert not one['matching_live_python_pids'] and not two['counts'] and not two['owned_accepted']
assert owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0
assert not any((P/folder/'junit.xml').exists() for folder in ('gate_isolation01','gate_isolation02'))
files=[R/'scripts/akt/refresh_gate2.py',R/'tests/akt/test_gate2_refresh.py',
       P/'check_gate_isolation01.py',P/'check_gate_isolation02.py',P/'run_gate_pure02.py',
       P/'gate_collection_conflict01.json',P/'a0_native_readiness_design.md',Path(__file__),
       R/'docs/thesis_recovery/evidence/gate_partition_bounded_checks_20261108.json']
for folder in ('gate_isolation01','gate_isolation02','gate_isolation02-owned','gate-isolation-review01'):
    files += [f for f in (P/folder).rglob('*') if f.is_file() and 'tmp' not in f.relative_to(P/folder).parts]
files=list(dict.fromkeys(files))
inv=[{'source':f.relative_to(R).as_posix(),'sha256_before':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files]
note='''# Archive kiểm Gate partition — chưa nghiệm thu

Đây là đóng gói bằng chứng lỗi/không đủ kết quả, KHÔNG GatePASS hoặc fullGate run. Source được AST/review, không đủ nghiệm thu runtime.

- Attempt01 terminalRC1,52stdoutdots, thiếuJUnit/result → UNKNOWN. Exactscriptprocessscan không còn matching process.
- Attempt02 owned helper reject vì active deadline;57stdoutdots, thiếuJUnit/result. Cleanup accepted/job0/handlesclosed. Whole recorded boundary34.0555539+prior20=54.0555539s/60; không có phép lặp tiếp trong batch này.
- Không công nhận52/57testsPASS hay0test bodies. Planned76cases chỉ là static source count.0native model/GPU/Holdout/fullCV/Modal.
- Filesystem/teardown và máy chậm là giả thuyết, chưa được chứng minh là nguyên nhân. Không hạ assert, bỏ tests hoặc thay old Gate history để có PASS.

`manifest.status=completed` chỉ nói ARCHIVE đã đóng; `gate_execution_accepted=false` giữ rõ kết quả. execution.log là log đóng gói. Dữ liệu temporary fixture không được chép; giữ source, progresslogs, launch/cleanup và terminal receipts.
'''
with record_evidence_run(R,'akt-gate-isolation-bounded-checks-20261108-01',
    metadata={'kind':'rejected_or_unknown_pure_test_attempt_archive_not_full_gate','gate_execution_accepted':False,
              'full_gate_executed':False,'verified_pass_count':None,'model_calls':0},sources=files,note=note) as out:
    for i,(f,item) in enumerate(zip(files,inv)):
        raw=f.read_bytes();dest=out/f'input-{i:02d}__{f.name}';dest.write_bytes(raw)
        assert hashlib.sha256(raw).hexdigest()==item['sha256_before']==hashlib.sha256(dest.read_bytes()).hexdigest()==hashlib.sha256(f.read_bytes()).hexdigest()
        item.update(copy=dest.name,sha256_after=item['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs/akt-gate-isolation-bounded-checks-20261108-01')))
