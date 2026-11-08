"""Gói 76 fixture checks và diagnostics; không actual full Gate/test rerun."""
from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
need=lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg))
res=json.loads((P/'gate_pure04/result.json').read_bytes());owned=json.loads((P/'gate_pure04-owned/receipt.json').read_bytes())
final=json.loads((P/'gate_pure04-owned/final.json').read_bytes())
need(final['status']=='ACCEPTED_76PURE_NOT_FULL_GATE' and final['elapsed_seconds']<240,'terminal')
need(res['pytest_exit_code']==0 and res['source_unchanged'] and res['environment_restored'],'result/env')
need(res['actual_subprocess_attempts']==res['heavy_modules_loaded']==res['protected_data_attempts']==[],'pure scope')
need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'],'cleanup')
need(not (P/'gate_pure04-owned/postwrite_rejection.json').exists(),'postwrite failure')
tree=ET.parse(P/'gate_pure04/junit.xml').getroot()
need(len(list(tree.iter('testcase')))==76 and not any(list(tree.iter(t)) for t in ('failure','error','skipped')),'JUnit')
need(len(res['collected_nodeids'])==len(set(res['collected_nodeids']))==76 and res['report_count']==228,'collection and stages')
for name,digest in res['source_before'].items():need(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'source drift')
report=R/'research_tracking/reports/akt_gate_process_isolation_20261108.md'
report.write_text('''# Chia tiến trình kiểm AKT — 08/11/2026

Pipeline cần một lần kiểm toàn bộ phần mềm trên đúng nguồn hiện hành trước khi dùng kết quả đó cho training. Tuy nhiên, một số test kiểm nghiêm không được import Torch hoặc thư viện dữ liệu, trong khi test neural khác đã import chúng ngay khi collection. Chạy chung một Python process làm hai yêu cầu hợp lệ xung đột. Sửa này chia tiến trình, không bỏ test hoặc hạ điều kiện kiểm.

## Cách sửa

Inventory hiện có67test modules được chia3processes:1stdlib-only,6no-Torch,60còn lại. Kiểm union đầy đủ/mỗi module đúng một lần; ghép JUnit không trùng testcase; giữ cùng global deadline và source/lock identity xuyên các nhóm. Pointer hiện hành chỉ công bố sau tất cả nhóm đạt. Nếu quá hạn ngay sau công bố, khôi phục đúng bytes pointer cũ và ghi rejected cho report mới thuộc invocation đó; không sửa report lịch sử.

## Bằng chứng hiện có

76fixture cases thực sự PASS,0failure/error/skip,62,045502901 giây/240. Các child process, upstream verifier và full Gate trong fixture là stubs. Nguồn8files trước/sau khớp;228setup/call/teardown reports,76unique node IDs; không import Torch/NumPy/pandas/sklearn/SciPy, không Popen hoặc mở vùng dữ liệu thật bị cấm từtest; environment restored. Owned Job cleanup còn0process và đóng handles.

Hai lượt kiểm trước chỉ có52/57dấu chấm, không JUnit cuối, vẫn giữ UNKNOWN/REJECTED trong bundle cũ; không đổi thànhPASS. Một diagnostic riêng2nodes đã qua và một probe8files mất0,1153giây. Chúng không chứng minh nguyên nhân thời gian chậm trước. Allocation phần mềm240giây được ghi trước lượt76cases, không tăng cap training/fit. Không dùng Timer trong child; outer owned Job có giới hạn237giây gồm5giâycleanup, tổng240gồmfinalization.

## Chưa hoàn tất

Đây chưa phải full Gate đã chạy đủ67modules và chưa phát hành source-bound Gate mới. Cần admission RAM thực, actual full software suite trong3processes có globaldeadline≤600, source/lock trước=sau và ownedcleanup. Sau đó mới dùng Gate cho native runtime/resource probe. Không suy readiness CUDA hoặc fulltraining từ76fixtures.

[Bundle76checks/diagnostics](../runs/akt-gate-process-isolation-engineering-20261108-01/README.md); [hai lượt thiếu nghiệm thu trước](../runs/akt-gate-isolation-bounded-checks-20261108-01/README.md). Không Holdout, training nghiên cứu, GPU hoặc chi Modal.
''',encoding='utf-8',newline='\n')
files=[R/name for name in res['source_before']]
files += [P/name for name in ('check_gate_pure04.py','run_gate_pure04.py','gate_pure04_allocation.json','gate_diagnostic03.py','probe_filesystem01.py','gate_collection_conflict01.json')]
for folder in ('gate_pure04','gate_pure04-owned','gate_diagnostic03','gate_diagnostic03-owned','filesystem_probe01','filesystem_probe01-owned'):
    files += sorted(f for f in (P/folder).iterdir() if f.is_file())
files += [report,Path(__file__)]
inv=[dict(source=f.relative_to(R).as_posix(),sha256_before=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files]
runid='akt-gate-process-isolation-engineering-20261108-01'
with record_evidence_run(R,runid,metadata=dict(kind='pure_gate_process_isolation_not_actual_full_gate',pure_cases=76,
    actual_full_gate=False,actual_model_calls=0,prior_rejected_seconds=54.055553913116455),sources=files,
    note='# Gate process isolation: phần mềm\n\n76fixtures PASS; không actual67module/fullGate. Diagnostic2node và8fileprobe có phạm vi riêng, không causal timeout explanation. Log đóng gói không là pytest log. Đọc report trước dùng trạng thái.\n') as out:
    for i,(f,item) in enumerate(zip(files,inv)):
        raw=f.read_bytes();dest=out/f'input-{i:02d}__{f.name}';dest.write_bytes(raw)
        need(hashlib.sha256(raw).hexdigest()==item['sha256_before']==hashlib.sha256(dest.read_bytes()).hexdigest()==hashlib.sha256(f.read_bytes()).hexdigest(),'copy identity')
        item.update(copy=dest.name,sha256_after=item['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs'/runid)))
