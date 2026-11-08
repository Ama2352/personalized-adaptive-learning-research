"""Đóng bằng chứng consistency Log Loss; không chạy lại metric/test/model."""
from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
need=lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg))
result=json.loads((P/'metric_epsilon02/result.json').read_bytes())
owned=json.loads((P/'metric_epsilon02-owned/receipt.json').read_bytes())
final=json.loads((P/'metric_epsilon02-owned/final.json').read_bytes())
need(final['status']=='ACCEPTED_METRIC_FIXTURE_ONLY' and final['elapsed_seconds']<45,'terminal')
need(result['pytest_exit_code']==0 and result['source_unchanged'] and result['environment_restored'],'test/source/env')
need(result['actual_subprocess_attempts']==result['heavy_modules_loaded']==[],'scope')
need(result['available_ram_start']>=1024**3 and result['available_ram_end']>=1024**3 and result['process_peak_rss_bytes']<=512*1024**2,'observed memory')
need(owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0 and owned['popen_handle_closed'],'owned cleanup')
need(not (P/'metric_epsilon02-owned/postwrite_rejection.json').exists(),'postwrite')
tree=ET.parse(P/'metric_epsilon02/junit.xml').getroot()
need(len(list(tree.iter('testcase')))==13 and not any(list(tree.iter(t)) for t in ('failure','error','skipped')),'exact13JUnit')
for name,sha in result['source_before'].items():need(hashlib.sha256((R/name).read_bytes()).hexdigest()==sha,'current drift')
report=R/'research_tracking/reports/akt_metric_consistency_20261108.md'
report.write_text('''# Nhất quán Log Loss báo cáo và bootstrap — 08/11/2026

Các mô hình phải được so bằng cùng định nghĩa phép đo, ngoài việc dùng cùng quần thể tương tác. Evaluator báo cáo BKT/GAM/AKT đã dùng xác suất float64 và Log Loss của sklearn. Tuy nhiên, sufficient statistics phục vụ bootstrap AKT còn chặn xác suất ở 1e-15 thay vì epsilon float64. Ở dự báo cực đoan sai, hai cách tính có thể khác: -log(1e-15) khoảng34,5388, còn -log(epsilon64) khoảng36,0437.

Sửa duy nhất trong thuật toán thống kê là dùng np.finfo(np.float64).eps, khớp evaluator canonical và script bootstrap BKT/GAM lịch sử. Không đổi tập tương tác, trọng số learner/fold, kiểu bootstrap, ECE15, Accuracy0,5, objective training, hyperparameters hay dữ liệu. Chưa kiểm ảnh hưởng lên artifacts thật; không tính lại hoặc sửa bất kỳ bảng lịch sử nào.

## Kiểm tra thực tế

13tests trên dữ liệu tự dựng PASS,0failure/error/skip. Test mới so actual DuckDB sufficient statistics ở xác suất0/1 đúng và sai với actual canonical sklearn evaluator: kiểm tổng LL mỗi learner và chênh lệch fold sau nhân trọng số lấy mẫu[2,1]. Các kiểm cũ về OOV/null/coverage/common identities/aggregation cũng giữ nguyên. Không dùng AUC/Brier/LL fixture như kết quả AKT đã train.

Outer7,787169900s trong cap45; source5files trước/sau bằng nhau, environment restored,0Torch/NN/solver/corpus reads; actual DuckDB/NumPy/pandas/sklearn được import. Observed peak RSS196.890.624B, available RAM đầu1.714.991.104B/cuối1.644.703.744B; đây là snapshot/Windowspeak, không monitor liên tục hoặc hardmemory quota. OwnedJob cleanupaccepted/active0/handleclosed. Không chứng nhận fullGate hay longrun readiness.

Lượt trước không chạy test bodies: audit socket.* quá rộng đã chặn gethostname metadata khi collection/JUnit. XMLpartial và traceback giữ nguyên; outer còn lỗi parseXMLpartial. Controller sau chỉ cho phép gethostname metadata, vẫn chặn socket operations/Popen/dữ liệu thật, bắt parseerror thành rejected. Không sửa source/test để né lỗi. Hai allocation45s đã ghi, không tự cộng13thành26case hoặc fabricatedRED.

[Bundle nguồn, snapshots và hai lượt kiểm](../runs/akt-metric-consistency-engineering-20261108-01/README.md). Full Gate vẫn chờ source-bound run và admission RAM≥4GiB; không lấy13targeted tests làm Gate. Không Holdout/fullCV/GPU/Modal.
''',encoding='utf-8',newline='\n')
files=[R/name for name in result['source_before']]
files += [P/name for name in ('check_metric_epsilon01.py','run_metric_epsilon01.py','check_metric_epsilon02.py','run_metric_epsilon02.py','metric_epsilon_attempt01_rejection.json')]
for folder in ('metric_epsilon01','metric_epsilon01-owned','metric_epsilon02','metric_epsilon02-owned','pre-paired-metric-epsilon01'):
    files += sorted(f for f in (P/folder).iterdir() if f.is_file())
files += [report,Path(__file__)]
inventory=[dict(source=f.relative_to(R).as_posix(),sha256_before=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files]
runid='akt-metric-consistency-engineering-20261108-01'
with record_evidence_run(R,runid,metadata=dict(kind='actual_metric_evaluator_fixture_consistency_not_model_efficacy',tests=13,
    actual_model_calls=0,actual_solver_fits=0,actual_corpus_reads=0,prior_attempt_accepted=False),sources=files,
    note='# Consistency Log Loss AKT\n\n13actual metric fixture tests PASS,0NN/researchdata. Chưa tác động đo lại bảng lịch sử hoặc fullGate. Giữ lỗi controller trước ở stderr/XMLpartial. execution.log chỉ đóng gói; pytest/owned logs mới là execution proof. Đọc report trước dùng số metric.\n') as out:
    for i,(f,item) in enumerate(zip(files,inventory)):
        raw=f.read_bytes();dest=out/f'input-{i:02d}__{f.name}';dest.write_bytes(raw)
        need(hashlib.sha256(raw).hexdigest()==item['sha256_before']==hashlib.sha256(dest.read_bytes()).hexdigest()==hashlib.sha256(f.read_bytes()).hexdigest(),'copy identity')
        item.update(copy=dest.name,sha256_after=item['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs'/runid)))
