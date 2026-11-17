"""Ghi mốcCPU đã nghiệm thu, giữ lịch sử và phạm vi fold4."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
state=json.loads((B/'STATE.json').read_text())
state.update(status='OUTER_CPU_COMPLETE_LOCAL_STAGING_TO_MODAL',
    next='Kiểm byte trên Volume, H100 A0–A3 tuần tự, lưu Drive rồi CPU đánh giá',
    cpu_cache_receipt='CACHE_RESULT01.json',windows=72423,targets=4137050,
    calibration_accepted=4,GPU_started=False)
(B/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
    path=report/name
    body=path.read_text(encoding='utf-8')
    body=body.replace('**Mốc còn thiếu** là hoàn tất hiệu chỉnh xác suất, đánh giá độc lập và mô phỏng vòng kín để kiểm hiệu quả của giải pháp.',
        '**Mốc còn thiếu** là đánh giá độc lập và mô phỏng vòng kín để kiểm hiệu quả của giải pháp.')
    body=body.replace('Mốc còn thiếu</strong> là hoàn tất hiệu chỉnh xác suất, đánh giá độc lập và mô phỏng vòng kín để kiểm hiệu quả của giải pháp.',
        'Mốc còn thiếu</strong> là đánh giá độc lập và mô phỏng vòng kín để kiểm hiệu quả của giải pháp.')
    path.write_text(body,encoding='utf-8')
map_path=ROOT/'docs/REPOSITORY_MAP.md'
body=map_path.read_text(encoding='utf-8')
section='''## 17/11 — Calibration Junyi4/4 và cache outer đã sẵn sàng

[Nghiệm thu A3](../research_tracking/runs/junyi-calibration-real-20261117-01/LOCAL_A3_FIT_ACCEPTANCE101.json) khép bước hiệu chỉnh xác suất cả bốn model trên cùng cohort, đã đọc lại Drive Sang. [Cache outer](../research_tracking/runs/junyi-outer-real-20261117-01/CACHE_RESULT01.json) có72.423cửa sổ,4.137.050target/39.616người học và144OOV. Ba cache đồ thị được kiểm riêng. Lượt H100 outer và phân tích so sánh còn chờ. Các mốc bên dưới là lịch sử.

'''
if section not in body:
    body=body.replace('\n\n','\n\n'+section,1)
map_path.write_text(body,encoding='utf-8')
print('STATE_AND_CONTEXT_UPDATED_NO_OUTER_METRIC_CLAIM')
