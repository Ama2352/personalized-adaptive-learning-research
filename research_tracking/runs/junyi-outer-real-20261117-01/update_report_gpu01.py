"""Cập nhật mốc suy luận outer, tách rõ bảng chỉ số chưa nghiệm thu."""
import csv
import io
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
REPORT=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
rows=[]
for variant in ('A0','A1','A2','A3'):
    result=json.loads((B/(variant+'_GPU_RESULT01.json')).read_text())
    assert result['status']=='OUTER_GPU_OPERATION_COMPLETE'
    rows.append(dict(model=variant,learners=39616,targets=result['result']['counts']['targets'],
        oov=result['result']['counts']['oov_targets'],worker_seconds=result['result']['worker_seconds']))
csv_path=B/'OUTER_GPU_PROGRESS01.csv'
with csv_path.open('w',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
text='''## Hoàn tất suy luận độc lập Junyi cho bốn mô hình

Sau khi hiệu chỉnh xác suất trên nhóm riêng, ngày17/11 đã dùng cả bốn model để dự đoán trên39.616người học chưa tham gia học tham số, chọn vòng hay fit hệ số hiệu chỉnh. Mỗi model tạo đủ4.137.050lượt dự đoán, trong đó144lượt ngoài từ vựng được đánh dấu riêng. Phạm vi là Development fold4 đã chốt.

| Mô hình | Vai trò | Thời gian worker H100 |
|---|---|---|
'''
labels=['AKT không đồ thị','AKT đồ thị cố định','AKT dùng độ tin cậy cạnh','CG-AKT có cổng đồ thị']
for row,label in zip(rows,labels):
    text+=f"| {row['model']} | {label} | {row['worker_seconds']:.2f}giây |\n"
text+='''
Các App GPU đã dừng. CPU local tiếp tục nối đúng nhãn và tính cùng bộ chỉ số AUC, Log Loss, Brier, ECE để so sánh chất lượng dự báo. Số lượt dự đoán và thời gian chạy chứng minh pipeline đã xử lý đủ dữ liệu. Kết luận mô hình nào tốt hơn cần bảng chỉ số và phân tích thống kê được nghiệm thu. Chi phí Modal ghi nhận tăng khoảng0,70USD trong đợt từ trước đến sau bốn lượt; đây là số đo tại thời điểm kiểm, có thể còn cập nhật billing.

[Nguồn số liệu của mốc suy luận](../../../runs/junyi-outer-real-20261117-01/OUTER_GPU_PROGRESS01.csv).

'''
path=REPORT/'BAO_CAO.md';body=path.read_text(encoding='utf-8')
if '## Hoàn tất suy luận độc lập Junyi cho bốn mô hình' not in body:
    body=body.replace('## Các mốc đã khép theo từng phần',text+'## Các mốc đã khép theo từng phần',1)
body=body.replace('| Junyi · đánh giá độc lập | 0/4 | 0% |','| Junyi · suy luận outer độc lập | 4/4 | 100% |\n| Junyi · bảng chỉ số outer đã nghiệm thu | 0/4 | 0% |')
path.write_text(body,encoding='utf-8')
html='''<section id="outer-progress"><h2>Hoàn tất suy luận độc lập Junyi cho bốn mô hình</h2><p>Ngày17/11, cả bốn model đã dự đoán đủ trên cùng39.616người học độc lập, thuộc Development fold4. Nhóm này chưa tham gia học tham số, chọn vòng hay fit hệ số hiệu chỉnh. Mỗi model xử lý4.137.050lượt, gồm144lượt ngoài từ vựng được đánh dấu riêng.</p><table class="stats"><thead><tr><th>Mô hình</th><th>Vai trò</th><th>Worker H100</th></tr></thead><tbody>'''
for row,label in zip(rows,labels):
    html+=f"<tr><td>{row['model']}</td><td>{label}</td><td>{row['worker_seconds']:.2f}giây</td></tr>"
html+='''</tbody></table><p>Các App GPU đã dừng. CPU local đang nối đúng nhãn và tính AUC, Log Loss, Brier, ECE để so sánh chất lượng dự báo. Đã xử lý đủ dữ liệu; kết luận mô hình nào tốt hơn cần bảng chỉ số và phân tích thống kê được nghiệm thu.</p><p>Modal ghi nhận chi phí tăng khoảng0,70USD từ trước đến sau bốn lượt. Đây là số đo tại thời điểm kiểm; billing có thể cập nhật tiếp.</p></section>'''
path=REPORT/'BAO_CAO_NGHIEN_CUU.html';body=path.read_text(encoding='utf-8')
if '<section id="outer-progress">' not in body:
    body=body.replace('<section id="milestones">',html+'\n<section id="milestones">',1)
body=body.replace('<tr><td>Junyi · đánh giá độc lập</td><td>0/4</td><td>0%</td></tr>',
    '<tr><td>Junyi · suy luận outer độc lập</td><td>4/4</td><td>100%</td></tr><tr><td>Junyi · bảng chỉ số outer đã nghiệm thu</td><td>0/4</td><td>0%</td></tr>')
path.write_text(body,encoding='utf-8')
state=json.loads((B/'STATE.json').read_text())
state.update(status='OUTER_ALL_FOUR_GPU_COMPLETE_CPU_SCORING_AND_DRIVE_BACKUP',numeric_complete=['A0','A1','A2','A3'],
    active_variant=None,gpu_containers_after_run=0,independent_metric_exports_complete=[],
    next='Nghiệm thu bốn archive Drive, nối nhãn CPU, bảng chỉ số và so sánh')
(B/'STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('REPORT_GPU4_OF4_METRICS_PENDING_UPDATED')
