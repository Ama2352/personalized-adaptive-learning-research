"""Niêm phong hồ sơ confidence/A2 sau khi model, số liệu và báo cáo đã nghiệm thu."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
acceptance=json.loads((HERE/'a2-final-acceptance.json').read_text())
export=json.loads((HERE/'a2-export-result.json').read_text())
qa=json.loads((HERE/'a2-report-verification.json').read_text())
ledger=json.loads((ROOT/'research_tracking/COMPUTE_BUDGET.json').read_text())
assert acceptance['status']=='PASS_A2_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT'
assert export['status']=='EXPORTED_A2_SELECTED_ON_D'
assert qa['status']=='PASS_A2_REPORT_STATIC_AND_FIGURE_QA'
assert ledger['new_allocations']==[]
assert not (HERE/'CLOSEOUT_MANIFEST.json').exists()
for attempt in ('09','10'):
    output=ROOT/'experiments/akt/results'/('modal-junyi-a2-staged-h100-20261114-'+attempt)
    assert json.loads((output/'app-budget-guard.json').read_text())['stop_acknowledged']
    assert json.loads((output/'COMPLETE.json').read_text())['status']=='LOCAL_ARTIFACTS_VERIFIED_GPU_STOPPED'
state_path=HERE/'STATE.json'
state=json.loads(state_path.read_text())
state.update(status='A2_SELECTED_FIT80_COMPLETE_ARTIFACTS_VERIFIED',closed=True,
    active_operation=None,active_exec_session=None,active_processes=[],
    action='READ_ONLY_CLOSED_EVIDENCE',selected_epoch=9,complete_epochs=12,
    gpu_start_confirmed=False,gpu_stopped_acknowledged=True,
    export_model='experiments/akt/results/model-export-a2-batch128-20261114-01/MODEL_INDEX.json',
    acceptance='a2-final-acceptance.json',standard_metrics='a2-selection-metrics.json',
    figure='figures/a2-junyi-selection-v01.svg',report_qa='a2-report-verification.json',
    gpu_utilization_goal_50_percent_met=False,
    measured_mean_sampled_gpu_utilization=32.231818181818184,
    refit_completed=False,calibration_completed=False,independent_evaluation_completed=False,
    next_steps=[
        'Tạo bundle mới cho A3 hoặc công việc kế tiếp, tham chiếu hồ sơ này, không sửa bundle đã đóng',
        'Đối soát reservation lịch sử trước cấp GPU A3 vì cận bảo thủ cộng dự phòng còn ít hơn cap2,60USD',
        'Giữ trần toàn KLTN30USD; không tự coi billing hoặc credit reset là quyền tăng ngân sách',
        'Chuẩn bị A3 với source numerical03 đã sửa runtime và confidence/caches thật hiện có',
        'Hoàn thiện refit, calibration, đánh giá độc lập và mô phỏng vòng kín theo protocol đã chốt',
        'Mục tiêu GPU trên50% còn thiếu, tránh diễn giải việc tách chuẩn bị/thu artifact như bằng chứng đạt mục tiêu'])
state['budget_at_closeout']=dict(historical_reserved_upper_usd=ledger['historical_usage_reserved_upper_usd'],
    safety_reserve_usd=ledger['safety_and_final_inference_reserve_usd'],
    unallocated_headroom_under_conservative_policy_usd=30-ledger['historical_usage_reserved_upper_usd']-ledger['safety_and_final_inference_reserve_usd'],
    last_provider_metered_usd=19.09665620,last_provider_billed_usd=0)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=HERE/'README.md'
old=readme.read_bytes()
first_end=old.index(b'\n')+1
summary='''# Confidence TRAIN80 và A2 Junyi — đã hoàn tất selected-fit ngày 14/11

## Kết quả đã nghiệm thu

A2 đã học 12 epoch trên đủ 13.347.331 target TRAIN80 mỗi epoch, chọn checkpoint epoch 9 và xuất đúng 1.600.343 dự đoán của 15.847 người học selection. Đã kiểm target/order, xác suất, checkpoint, Adam và RNG. Hai lượt H100 đã dừng trước khi thu artifact. Lượt cuối có 210 file, 2.925.030.322 byte, archive đã đối chiếu. Gói model bốn file giữ một checkpoint .pt tại `experiments/akt/results/model-export-a2-batch128-20261114-01/`.

- `a2-final-acceptance.json` và `a2-export-result.json` là điểm kiểm A2 và model.
- `a2-selection-metrics.json` giữ AUC 0,805993, Log Loss chuẩn 0,353567, Brier 0,107698 và ECE 0,004138 từ hàm chấm dùng cho GAM-KT.
- `a2-comparison-audit.json` giữ cùng quần thể/cấu hình học A0–A2 và giới hạn A0 chưa replay đầy đủ ranking epoch bằng batch128.
- `a2-final-performance.json` ghi 47 phút 19 giây trong hai function GPU, trung bình train 3 phút 03 giây/epoch, 1.320 mẫu NVML trung bình 32,23%, VRAM đỉnh 5.789 MiB. Mục tiêu GPU trên 50% chưa đạt.
- `figures/` giữ SVG, PNG, CSV và manifest. `build_a2_selection_figure.py` dựng lại sang prefix/thư mục mới, theo quy ước figures4papers đã lưu.
- `a2-report-verification.json` giữ kiểm HTML/ID và quan sát PNG. Hai báo cáo GVHD tại `research_tracking/supervisor_reports/2026-11-10/01_tien_do/` đã cập nhật.

## Phạm vi kết luận và bước sau

Đã hoàn tất selected-fit của A2 trên Development outer fold 4, một seed. Điểm chọn checkpoint A0/A1/A2 lần lượt 0,35358018/0,35356185/0,35356694, là quan sát mô tả trên selection. A3, refit/calibration, đánh giá độc lập, kiểm quanh ngưỡng và mô phỏng vòng kín còn chờ. Không suy ra lợi ích đồ thị hoặc RQ3 đã hoàn tất từ các điểm này.

CPU chuẩn bị và tải/nén đã tách khỏi thời gian thuê GPU. Tăng mức CPU bảo đảm lên 2 vCPU ở lượt tiếp tục chưa có đối chứng xác nhận tăng tốc. Billing sau training ghi 19,09665620 USD metered toàn workspace, billed bằng 0. Ledger giữ cận lịch sử 25,22710605 USD và dự phòng 3 USD. Phải đối soát cận cũ trước một allocation A3 2,60 USD, giữ trần toàn KLTN 30 USD.

Hồ sơ này đã niêm phong. Dùng STATE để đọc điểm tiếp tục, tạo bundle mới khi phát sinh công việc mới. Giữ nguyên các log lỗi, source và checkpoint lịch sử.

## Lịch sử triển khai được giữ nguyên bên dưới

'''
readme.write_bytes(summary.encode()+old[first_end:])


def pin(path):
    with path.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return dict(bytes=path.stat().st_size,sha256=digest)


inventory={path.relative_to(HERE).as_posix():pin(path) for path in sorted(HERE.rglob('*')) if path.is_file()}
model_root=ROOT/'experiments/akt/results/model-export-a2-batch128-20261114-01'
manifest=dict(status='CLOSED_A2_SELECTED_FIT80_EVIDENCE',date_local='2026-11-14',
    files=inventory,model_export={path.name:pin(path) for path in sorted(model_root.iterdir())},
    artifact_references={attempt:json.loads((ROOT/'experiments/akt/results'/
        ('modal-junyi-a2-staged-h100-20261114-'+attempt)/'COMPLETE.json').read_text()) for attempt in ('09','10')},
    source_snapshot='artifacts/akt/staged/junyi-a2-expert-20261114-03',
    source_snapshot_inventory_sha256='b9e467ab4f1431bb59788e5ba83e20db9d851c804996f45c69e533c436d249d4',
    limits_vi='Selected-fit Development một seed. A3/refit/calibration/đánh giá độc lập còn chờ. GPU trung bình dưới50%.')
with (HERE/'CLOSEOUT_MANIFEST.json').open('x',encoding='utf-8') as stream:
    json.dump(manifest,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps(dict(status=manifest['status'],files=len(inventory),export_files=len(manifest['model_export']))))
