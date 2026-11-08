"""Đóng gói hai lượt kiểm worker confidence; không chạy solver hay đọc corpus."""
from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
result=json.loads((P/'method24-pure02/result.json').read_bytes())
final=json.loads((P/'method24-pure02-owned/final.json').read_bytes())
owned=json.loads((P/'method24-pure02-owned/receipt.json').read_bytes())
allocation=json.loads((P/'method24_pure02_allocation.json').read_bytes())
require=lambda condition,message: None if condition else (_ for _ in ()).throw(ValueError(message))
require(final['status']=='ACCEPTED_PURE_ONLY_NOT_NATIVE_FIT','terminal verdict')
require(result['source_unchanged'] is True and result['source_before']==result['source_after'],'source drift')
require(result['pytest_exit_code']==0 and result['environment_restored'] is True,'test/env')
require(result['actual_subprocess_attempts']==result['heavy_modules_loaded']==[],'purity')
require(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'],'owned cleanup')
require(final['elapsed_seconds']<150 and not (P/'method24-pure02-owned/postwrite_rejection.json').exists(),'postwrite deadline')
tree=ET.parse(P/'method24-pure02/junit.xml').getroot()
require(len(list(tree.iter('testcase')))==21 and not any(list(tree.iter(tag)) for tag in ('failure','error','skipped')),'JUnit population')
for name,digest in result['source_before'].items():
    require(hashlib.sha256((P/name).read_bytes()).hexdigest()==digest,'current source drift '+name)
report=R/'research_tracking/reports/edge_confidence_worker_readiness_20261108.md'
report.write_text('''# Worker độ tin cậy cạnh — kiểm kỹ thuật ngày 08/11/2026

Mục tiêu là chuẩn bị cách ước lượng mức hỗ trợ của từng quan hệ từ dữ liệu huấn luyện, để CG-AKT không phải tin mọi cạnh như nhau. Kết quả ở đây chỉ nghiệm thu dây nối và các trường hợp từ chối của worker. Chưa có cạnh được fit hoặc đồ thị học được để báo cáo chất lượng.

## Đã sửa và kiểm

Worker nhận đúng launch manifest tuyệt đối do bộ quản lý tiến trình sở hữu phát hành, nhưng vẫn từ chối đường dẫn bất kỳ. Danh sách nguồn được ghim thêm initializer của gói AKT thực sự bị import, thành 11 Python sources. Không đổi recipe, số fit, solver, partition hay cap của lượt fit dự kiến.

Lượt pure đầu giới hạn 45 giây bị dừng: nhật ký chỉ đủ 7 case hoàn chỉnh, không có JUnit cuối; không gọi toàn suite là PASS. Sau khi xem thời gian setup thực, một allocation phần mềm riêng 150 giây được ghi trước lượt hai; nguồn và 21 case giữ nguyên. Lượt hai thực sự qua 21 case, không failure/error/skip; outer 37,260902643 giây. Đây không phải 28 case độc lập hoặc kết quả nghiên cứu cạnh.

Sau kiểm, source trước/sau khớp; không import NumPy/pandas/sklearn/SciPy/Torch, không tạo tiến trình từ test, môi trường test được khôi phục. Windows owned Job đã thu hồi đúng tiến trình của lượt chạy, còn 0 tiến trình và đóng handles. Fallback thông tin Windows chỉ ở fixture, không là chứng nhận runtime thật.

## Phần chưa nghiệm thu

Chưa import/fit solver thật, chưa đọc corpus trong lượt này, chưa chạy 2.352 fit slots hoặc xuất 272.160 dòng OOF. Chưa chứng minh hoàn tất trong active 110/outer 120 giây hoặc RAM 512 MiB. Allocation 150 giây chỉ dành kiểm phần mềm và không thay cap fit. Cần request/nguồn/runtime/resource được chốt và duyệt đúng lượt trước native fit. Mức hỗ trợ dự kiến là độ ổn định dự báo có điều kiện, không phải xác suất cạnh là thật.

[Nguồn, nhật ký cả lượt thất bại và thành công](../runs/edge-confidence-worker-engineering-20261108-01/README.md). Không có training AKT, Holdout, full CV, GPU hoặc chi Modal.
''',encoding='utf-8',newline='\n')
files=[P/name for name in result['source_before']]
files += [P/name for name in ('check_method24_pure01.py','run_method24_pure01.py','check_method24_pure02.py',
                            'run_method24_pure02.py','method24_pure02_allocation.json','method24_native_design.md')]
for folder in ('method24-pure01','method24-pure01-owned','method24-pure02','method24-pure02-owned','pre-method24-owned-bridge-fix01'):
    files += sorted(f for f in (P/folder).iterdir() if f.is_file())
files += [report,Path(__file__)]
inventory=[dict(source=f.relative_to(R).as_posix(),sha256_before=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files]
runid='edge-confidence-worker-engineering-20261108-01'
with record_evidence_run(R,runid,metadata=dict(kind='pure_edge_confidence_worker_engineering_not_research_fit',
    pure_tests_passed=21,prior_attempt_accepted=False,actual_solver_fits=0,actual_model_calls=0,actual_corpus_reads=0),
    sources=files,note='# Kiểm kỹ thuật worker confidence\n\nĐọc báo cáo trước số đếm: 21 pure PASS, lượt trước rejected giữ nguyên. Chưa native solver/corpus/AKT. Các execution.log là log đóng gói; pytest.log/JUnit/owned receipts mới ghi kiểm thực. Không suy hiệu quả RQ3 từ test.\n') as out:
    for i,(f,item) in enumerate(zip(files,inventory)):
        raw=f.read_bytes();copy=out/f'input-{i:02d}__{f.name}';copy.write_bytes(raw)
        require(hashlib.sha256(raw).hexdigest()==item['sha256_before']==hashlib.sha256(copy.read_bytes()).hexdigest()==hashlib.sha256(f.read_bytes()).hexdigest(),'copy identity')
        item.update(copy=copy.name,sha256_after=item['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs'/runid)))
