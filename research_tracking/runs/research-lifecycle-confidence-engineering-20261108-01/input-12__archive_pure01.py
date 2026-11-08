"""ROOT đóng bằng chứng kiểm phần mềm đã chạy; không chạy lại tests/model."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4]
P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
result=json.loads((P/'pure03/result.json').read_bytes())
assert result['pytest_exit_code']==0 and result['source_unchanged'] and not result['heavy_modules_loaded'] and not result['actual_subprocess_attempts']
x=ET.parse(P/'pure03/junit.xml').getroot()
cases=x.findall('.//testcase');assert len(cases)==101 and not x.findall('.//failure') and not x.findall('.//error')
counts=dict(Counter(c.attrib['classname'] for c in cases))
sources=[R/p for p in result['source_before']]
sources += [R/'research_tracking/reports/edge_confidence_method24_plan_20261108.md',R/'research_tracking/reports/edge_confidence_method24_plan_20261108.sources.json']
report=R/'research_tracking/reports/research_lifecycle_confidence_readiness_20261108.md'
report.write_text('''# AKT lifecycle và confidence train-only — kiểm phần mềm ngày08/11

## Kết quả đã xác nhận

ROOT đã chạy một lượt pytest thực sự với **101 PASS**, không fail/error/skip; ba nhóm gồm ledger, runner và confidence. Đối chiếu số lượng từng nhóm trong `test_counts.json` của bundle. Đây là tests thuần metadata, temporary fixtures và stub; không có actual model/optimizer/solver fit, không thêm learner observations.

Runner mới nối authorization → public corpus audit → train80 → raw epoch selection10 → fresh refit90 → calibration10 → full-target exports, tái sử dụng native training/checkpoint primitives. Pure tests kiểm thứ tự và dữ liệu được chuyển tới từng pha; chưa chứng minh một lượt native lifecycle đã hoàn tất. Optimization context không giữ toàn corpus. Epoch không lưu checkpoint có SHA null; selected epoch bắt buộc có checkpoint riêng. Không ghép checkpoint cũ với predictions của epoch mới.

Method24 dùng observable TRAIN, whole-learner cross-fitting, đặc trưng strict-past và bootstrap theo learner. Seed ghép cặp không phụ thuộc đáp án. Confidence là độ ổn định cải thiện dự báo có điều kiện, không xác suất cạnh tiên quyết thật. Giữ unary evaluation rows; chỉ yêu cầu hai lớp ở FIT. Graph thiếu đủ31cạnh dương hợp lệ phải báo unsupported, không tự thêm cạnh để đủ số. Nhánh hệ số NaN/Inf nay trả unsupported với diagnostics hữu hạn; regression kiểm serialization toàn kết quả mà không solver thật.

## Lỗi vận hành được giữ lại

- Pure01 dừng trước pytest vì Python local chưa có `platform.invalidate_caches`. Sửa controller test-only dùng `_uname_cache`; không đổi production source.
- Pure02 dừng trước pytest vì cờ `-S` vô hiệu hóa site-packages của .venv. Pure03 dùng `.venv\\Scripts\\python.exe -I -B`; không cài thêm dependency.
- Hai lần đầu có0test bodies. Không gọi đó là tests fail rồi sửa thành PASS. Pure03 elapsed1,6554365s; phí thời gian conservative hai lần đầu2s, cumulative controller3,6554365s/30. Nếu tính cả tool envelope lần cuối thì bound4,2683491s/30. Timer là cooperative/GIL-dependent, không hard OS quota.

Kiểm có audit từ chối actual subprocess và không có NumPy/pandas/sklearn/Torch trong module table sau lượt chạy. Fallback metadata Windows chỉ dùng actual WinAPI version10.0.26100 để tránh lệnh shell do stdlib; không chứng nhận RuntimeGate, CUDA hoặc môi trường production.

## Chưa được nghiệm thu và bước kế tiếp

Chưa actual research fit, actual crossfit2352solver calls, learned graph, GPU/CUDA/full Gate hoặc recovery/resume. Runner pilot hiện `resume_supported=False`; không dùng để khẳng định sẵn sàng thuê GPU dài hạn. Chưa benchmark runtime/RAM của full research lifecycle. Canonical metrics của dự báo sau calibration còn phải xuất riêng; không dùng objective clip nội bộ Tfit thay metric báo cáo. Outer owned-process acceptance, source/runtime pins và workload exact cần freeze trước actual execution.

[Bundle nguồn/log/kết quả](../runs/research-lifecycle-confidence-engineering-20261108-01/README.md). Báo cáo theo ngày đã commit trước batch này được giữ nguyên, không ghi đè snapshot hoặc tự coi batch engineering là RQ3 kết quả.
''',encoding='utf-8')
sources.append(report)
files=sources+[P/'check_pure01.py',P/'check_pure02.py',P/'check_pure03.py',Path(__file__)]
for folder in ('pure01','pure02','pure03'):
    files += [f for f in (P/folder).iterdir() if f.is_file()]
for folder in ('pre-integration-review01','pre-process-guard-review02','pre-edge-nonfinite-review01'):
    files += [f for f in (P/folder).rglob('*') if f.is_file()]
files=list(dict.fromkeys(files))
inventory=[{'source':f.relative_to(R).as_posix(),'sha256_before':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files]
runid='research-lifecycle-confidence-engineering-20261108-01'
note='# Kiểm phần mềm AKT lifecycle/confidence\n\n101pure PASS; không actual model/solver/RNG learner/teacher/GPU. Hai controller failures trước pytest được giữ,0test bodies. Source/stubs không chứng minh fitted efficacy, actual runtime hoặc RQcomplete. Đọc report và result/JUnit trước khi trích. execution.log ở đây chỉ là log đóng gói, không log training.\n'
with record_evidence_run(R,runid,metadata={'kind':'software_engineering_pure_stubs_not_research_fit','test_bodies_passed':101,'actual_model_calls':0,'actual_solver_calls':0,'native_corpus_replay':False},sources=files,note=note) as out:
    for i,(f,entry) in enumerate(zip(files,inventory)):
        name=f'input-{i:02d}__{f.name}'
        raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()==entry['sha256_before']
        dest=out/name;dest.write_bytes(raw)
        assert hashlib.sha256(dest.read_bytes()).hexdigest()==entry['sha256_before']==hashlib.sha256(f.read_bytes()).hexdigest()
        entry.update(copy=name,sha256_after=entry['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'test_counts.json').write_text(json.dumps(counts,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs'/runid),ensure_ascii=False))
