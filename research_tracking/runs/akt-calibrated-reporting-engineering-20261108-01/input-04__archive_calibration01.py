"""Đóng log metric integration đã chạy; không chạy lại model/tests."""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'src'))
from knowledge_tracing.evidence import record_evidence_run,verify_evidence_bundle
pure=json.loads((P/'calibration01/result.json').read_bytes())
assert pure['pytest_exit_code']==0 and pure['source_unchanged'] and not pure['heavy_modules_loaded']
cases=ET.parse(P/'calibration01/junit.xml').getroot();assert len(cases.findall('.//testcase'))==36
assert not cases.findall('.//failure') and not cases.findall('.//error') and not cases.findall('.//skipped')
native=json.loads((P/'metrics_native01/result.json').read_bytes());owned=json.loads((P/'metrics_native01/owned_receipt.json').read_bytes())
assert owned['accepted'] and owned['cleanup_accepted'] and owned['job_active_after_cleanup']==0
assert native['model_calls']==native['solver_fits']==native['real_data_reads']==0
assert native['reporting']['full_metrics'] is None and native['reporting']['supported_targets']==4
assert native['final_memory']['process_peak_rss_bytes']<=512*1024**2 and native['final_memory']['system_available_ram_bytes']>=1024**3
for name,digest in native['source_before_after'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
report=R/'research_tracking/reports/akt_calibrated_reporting_readiness_20261108.md'
report.write_text('''# Metric sau calibration — ngày08/11

## Đã bổ sung

AKT research runner nay xuất riêng **raw canonical metrics**, **calibrated canonical metrics** và **objective nội bộ của temperature fit**. Không dùng clipping/objective Tfit thay Log Loss báo cáo. Helper join theo đầy đủ target identity, kiểm cùng population/support, giữ OOV null và không thay prediction gốc. Đánh giá trên chính calibration partition được ghi rõ là in-sample, không phải chất lượng ngoài mẫu hoặc latent mastery đã calibration.

## Bằng chứng kiểm

-36pure runner tests PASS; controller1,1420376s +2s conservative preparation charge =3,1420376s/20. Một lỗi chuẩn bị controller do newline đã giữ trước khi test;0test bodies ở lần chuẩn bị đó. Chỉ stub evaluator, không actual NN/solver.
-Một probe bổ sung dùng **pandas/sklearn evaluator thật**,5hàng tự dựng (4supported+1OOV), đảo thứ tự truth/calibrated rows để kiểm join theo identity. Raw/unsupported giữ nguyên; metric khớp evaluator trực tiếp. **Mọi AUC/LL/Brier trong probe là số liệu fixture, tuyệt đối không là kết quả AKT/CG-AKT hay minh chứng RQ.**
-Probe ở Windows owned Job trước GO, helper elapsed12,881742954s/25, cleanup accepted/job0/handles closed, peak RSS158.949.376B và available RAM cuối1.219.297.280B. Caller không persist total wall sau khi đọc/xuất receipt, nên không tuyên bố25s là end-to-end acceptance của caller. Không cần chạy lại để lấp số đo đó.
-Ngân sách memory được kiểm trước/sau imports và cuối; không phải hard OS memory quota hay đo liên tục. Package metadata/RAM snapshot trước đó3,52GB available không bảo đảm còn đủ RAM khi chạy; probe thực tế chỉ còn khoảng1,22GB sau import. Không suy đủ bộ nhớ để chạy training hoặc toàn Gate.

## Còn thiếu trước research fit

Chưa actual research-fitted model, actual temperature fit trên corpus hoặc final evaluation. Pure101PASS ở bundle trước là phiên bản trước metric export, không gộp thành137quan sát/testcases độc lập. Current full Gate chưa nghiệm thu: source inspection phát hiện xung đột collection giữa20module top-level importTorch và các pure assertions; thêm một module đòi không NumPy/pandas/Torch. Cần process isolation giữ mọi test, cùng global deadline trước khi thử Gate thật. Đây là static finding, không phải fullGate đã chạy và thất bại.

[Bundle36tests và probe evaluator](../runs/akt-calibrated-reporting-engineering-20261108-01/README.md). Không sửa snapshot báo cáo GVHD ngày08/11, không dùng Modal/Holdout/fullCV.
''',encoding='utf-8',newline='\n')
files=[R/'src/knowledge_tracing/akt/research_runner.py',R/'tests/akt/test_research_runner.py',R/'src/knowledge_tracing/gam_kt/evaluation.py',report,Path(__file__),P/'check_calibration01.py',P/'probe_metrics01.py',P/'calibration_controller_preparation_failure01.json',P/'local_readiness01.json',P/'gate_collection_conflict01.json']
for folder in ('calibration01','metrics_native01','pre-calibrated-reporting01'):
    files += [f for f in (P/folder).rglob('*') if f.is_file() and 'tmp' not in f.relative_to(P/folder).parts]
inv=[{'source':f.relative_to(R).as_posix(),'sha256_before':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
runid='akt-calibrated-reporting-engineering-20261108-01'
with record_evidence_run(R,runid,metadata={'kind':'synthetic_calibrated_reporting_integration_not_model_efficacy','pure_tests':36,'manufactured_evaluator_rows':5,'model_calls':0,'solver_fits':0,'real_data_reads':0},sources=files,note='# Calibration reporting engineering\n\n36purePASS và1actualevaluatorprobe trên5hàng tự dựng,0model/solver/realdata. Đọc báo cáo trước metrics: AUC/Brier fixture không là RQ result. Ownedhelper cleanup accepted; caller fulltotal chưa persist. StaticGate conflict không executedGate failure.\n') as out:
    for i,(f,item) in enumerate(zip(files,inv)):
        raw=f.read_bytes();name=f'input-{i:02d}__{f.name}';dest=out/name;dest.write_bytes(raw)
        assert hashlib.sha256(raw).hexdigest()==item['sha256_before']==hashlib.sha256(dest.read_bytes()).hexdigest()==hashlib.sha256(f.read_bytes()).hexdigest()
        item.update(copy=name,sha256_after=item['sha256_before'])
    (out/'copy_inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(verify_evidence_bundle(R/'research_tracking/runs'/runid)))
