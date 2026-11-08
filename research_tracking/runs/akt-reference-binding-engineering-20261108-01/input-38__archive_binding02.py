"""Gói bản sửa AKT/reference/calibrator và vòng đời object, không chạy lại tests."""
from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
need=lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg))
for attempt in ('binding01','binding02'):
    result=json.loads((P/attempt/'result.json').read_bytes());owned=json.loads((P/(attempt+'-owned')/'receipt.json').read_bytes())
    final=json.loads((P/(attempt+'-owned')/'final.json').read_bytes())
    need(result['pytest_exit_code']==0 and result['source_unchanged'] and result['environment_restored'],'test/env')
    need(result['actual_subprocess_attempts']==result['heavy_modules_loaded']==[],'pure scope')
    need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'],'owned cleanup')
    need(final['status']=='ACCEPTED_PURE_BINDING_ONLY' and final['elapsed_seconds']<45,'outer')
    need(not (P/(attempt+'-owned')/'postwrite_rejection.json').exists(),'late failure')
    tree=ET.parse(P/attempt/'junit.xml').getroot()
    need(len(list(tree.iter('testcase')))==36 and not any(list(tree.iter(tag)) for tag in ('failure','error','skipped')),'JUnit36')
latest=json.loads((P/'binding02/result.json').read_bytes())
for name,sha in latest['source_before'].items():need(hashlib.sha256((R/name).read_bytes()).hexdigest()==sha,'current drift')
report=R/'research_tracking/reports/akt_reference_calibrator_binding_20261108.md'
report.write_text('''# Nối AKT với phép chấm kiến thức tham chiếu — 08/11/2026

Để dùng AKT trong simulator, file mô hình và file hiệu chỉnh xác suất phải đi cùng đúng ngân hàng bài tập và phải đọc lại được bằng API công khai. Sai dây nối có thể làm quy trình dừng dù từng thành phần riêng đã có kiểm thử. Batch này sửa hai lỗi cụ thể trước bất kỳ lượt training nghiên cứu nào.

## Thay đổi và bằng chứng

- Trường `bank_sha256` nay nhận SHA ngân hàng bài tập đúng hợp đồng; SHA toàn miền vẫn ở `domain_sha256`. Model ID đúng SHA checkpoint mà native online backend sử dụng.
- Calibrator được xuất qua `to_payload()`, gồm recipe/clip/bounds; không xuất thiếu schema bằng `asdict()`.
- Không giữ model/Adam refit cũ trong lúc tải checkpoint; không giữ payload/reload Adam khi dự báo; bỏ tham chiếu model sau dự báo trước bước fit scalar temperature. Không đổi trọng số, dữ liệu, RNG restore, epoch selection, fresh-refit hay cấu hình học.

Hai source revisions được kiểm riêng bằng cùng suite 36 cases. Lượt binding01 trước sửa vòng đời qua36; lượt binding02 sau sửa qua36,0failure/error/skip. Thời gian outer lần lượt2,804354100 và2,822563171 giây, mỗi cap45. Không cộng thành72case độc lập. Các orchestration cases nạp JSON calibrator thật qua strict loader rồi chấm84bài/28khái niệm bằng reference scorer thật với backend scalar **giả lập, chưa train**; sai bank bị từ chối trước thêm probe, thiếu recipe bị từ chối. Weakrefs kiểm model/optimizer/payload hết tham chiếu tại các điểm dự kiến.

Source trước/sau khớp; không import Torch/NumPy/pandas/sklearn/SciPy hoặc tạo subprocess từ test. Owned Job đã cleanup/job0/đóng handles. Các input/metadata là fixture; fit temperature chỉ trên các probability tự dựng, không trên corpus nghiên cứu.

## Giới hạn và bước tiếp

Đây là bằng chứng tích hợp phần mềm, không chất lượng AKT/CG-AKT, calibration ngoài mẫu, CUDA hay full Gate. Object hết tham chiếu không bảo đảm RSS trả về OS ngay; exception traceback có thể giữ tensor đến khi worker kết thúc. Phép kiểm bằng weakrefs không thay phép đo RAM thật trên native lifecycle. Cần full Gate/runtime hiện hành và bounded native resource probe trước cấp budget cho toàn lifecycle20epoch.

[Bundle nguồn và log hai revisions](../runs/akt-reference-binding-engineering-20261108-01/README.md). Không sửa dữ liệu, artifacts lịch sử, Holdout, full CV hoặc chi Modal.
''',encoding='utf-8',newline='\n')
files=[R/name for name in latest['source_before']]
files += [P/name for name in ('check_binding01.py','run_binding01.py','check_binding02.py','run_binding02.py')]
for folder in ('binding01','binding01-owned','binding02','binding02-owned','pre-bank-binding-fix01','pre-memory-release01'):
    files += sorted(f for f in (P/folder).iterdir() if f.is_file())
files += [report,Path(__file__)]
inventory=[dict(source=f.relative_to(R).as_posix(),sha256_before=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files]
runid='akt-reference-binding-engineering-20261108-01'
with record_evidence_run(R,runid,metadata=dict(kind='pure_akt_reference_binding_and_object_lifetime_not_model_fit',
    latest_pure_tests=36,source_revisions_tested=2,actual_neural_calls=0,actual_corpus_reads=0),sources=files,
    note='# Kiểm dây nối AKT và lifetime object\n\n36case cùng suite được kiểm ở2source revisions; không72case độc lập. Backend scalar synthetic và actual schema/reference scorer, không actual fitted NN. execution.log là đóng gói, originalpytest/JUnit/ownedreceipts giữ riêng. Đọc báo cáo để hiểu giới hạn RAM và calibration.\n') as out:
    for i,(f,item) in enumerate(zip(files,inventory)):
        raw=f.read_bytes();dest=out/f'input-{i:02d}__{f.name}';dest.write_bytes(raw)
        need(hashlib.sha256(raw).hexdigest()==item['sha256_before']==hashlib.sha256(dest.read_bytes()).hexdigest()==hashlib.sha256(f.read_bytes()).hexdigest(),'copy identity')
        item.update(copy=dest.name,sha256_after=item['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs'/runid)))
