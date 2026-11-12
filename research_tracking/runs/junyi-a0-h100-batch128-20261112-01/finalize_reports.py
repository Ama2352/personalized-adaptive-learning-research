"""Cập nhật chỉ mục và báo cáo hiện hành sau nghiệm thu A0 H100."""
import base64
import json
import re
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
summary = '''A0 không đồ thị trên Junyi đã hoàn tất 12 epoch H100 batch128 và chọn checkpoint epoch 9 theo patience 3, min_delta 0,0001. Mỗi epoch có 13.347.331 target train và 1.600.343 target selection, 0 OOV. Đã tải và kiểm ba archive, nạp lại checkpoint được chọn, xuất đủ dự báo và model chính về D. Cả ba App đã dừng, snapshot server ghi 0 container.

Log Loss selection của checkpoint được chọn là 0,353580, AUC 0,805990, Brier 0,107700 và ECE 0,004270. Đây là tập dùng chọn epoch, đánh giá độc lập và so sánh chính thức với BKT/GAM-KT còn ở bước tiếp theo. Refit90 và calibration chưa thực hiện. Training trung bình 2 phút 03 giây và validation 3 phút 18 giây/epoch. Telemetry toàn quá trình xử lý ghi GPU trung bình 26,49%, cao nhất 74%, VRAM cao nhất 5.793 MiB. Còn dư địa tối ưu validation.

Ba phiên H100 ghi credits tăng khoảng 5,39 USD, tổng KLTN đã dùng 8,67 USD và còn 21,33 USD tại snapshot cuối, billed 0 USD. Mọi lần tiếp tục cần dự toán trong phần ngân sách còn lại.
'''

def replace_first_update(path, heading, body):
    content = path.read_text(encoding='utf-8')
    start = content.index('\n## ')
    end = content.find('\n## ', start + 4)
    assert end > start
    path.write_text(content[:start] + '\n\n## ' + heading + '\n\n' + body + '\n' + content[end:], encoding='utf-8')

replace_first_update(ROOT/'research_tracking/reports/AKT_TRAINING_STATUS_20261112.md',
    'Chốt 13/11 — hoàn tất chọn checkpoint A0 H100', summary + '\n[Báo cáo riêng](../supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html). [Bằng chứng](../runs/junyi-a0-h100-batch128-20261112-01/README.md).\n')
current = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
replace_first_update(current/'BAO_CAO.md', 'Chốt 13/11 — A0 H100 đã chọn checkpoint epoch 9',
    summary + '\n[Báo cáo riêng quá trình training](../../2026-11-13/BAO_CAO_A0_H100.html).\n\n![Diễn tiến 12 epoch](../../../runs/junyi-a0-h100-batch128-20261112-01/a0-h100-progress-final012v2.svg)\n')

html_path = current/'BAO_CAO_NGHIEN_CUU.html'
html = html_path.read_text(encoding='utf-8')
png = base64.b64encode((BUNDLE/'a0-h100-progress-final012v2.png').read_bytes()).decode()
section = ('<section id="a0-h100-progress-current"><h2>Chốt 13/11 — hoàn tất chọn checkpoint A0 Junyi trên H100</h2>'
           + ''.join('<p>'+paragraph+'</p>' for paragraph in summary.strip().split('\n\n'))
           + '<p><a href="../../2026-11-13/BAO_CAO_A0_H100.html">Báo cáo riêng diễn tiến training A0 H100</a></p>'
           + '<figure><img style="width:100%;height:auto" alt="Diễn tiến A0 qua 12 epoch" src="data:image/png;base64,'+png+'">'
           + '<figcaption>Checkpoint epoch 9 được chọn theo mức cải thiện tối thiểu. Tách thời gian train và validation.</figcaption></figure></section>')
match = re.search(r'<section\b[^>]*id="a0-h100-progress-current"[^>]*>.*?</section>', html, re.S)
assert match
html = html[:match.start()] + html[match.end():]
# Giữ ngữ cảnh trước các diễn tiến kỹ thuật, bảo toàn nội dung lịch sử.
header = html.index('<header class="masthead"')
main_start = html.rfind('<main', 0, header)
assert main_start >= 0
main_open_end = html.index('>', main_start) + 1
old_updates = html[main_open_end:header].strip()
html = html[:main_open_end] + '\n' + html[header:]
context = re.search(r'<section\b[^>]*id="boi-canh"[^>]*>.*?</section>', html, re.S)
assert context
html = html[:context.end()] + '\n' + section + '\n' + html[context.end():]
if old_updates:
    appendix = '<details><summary>Các bước kiểm tài nguyên trước lượt H100</summary>'+old_updates+'</details>'
    html = html.replace('</main>', appendix+'\n</main>', 1)
html_path.write_text(html, encoding='utf-8')

for relative, text in [
    ('docs/REPOSITORY_MAP.md', '[A0 H100 hoàn tất](../research_tracking/runs/junyi-a0-h100-batch128-20261112-01/README.md) có 12 epoch, selected 9, 1.600.343 dự báo đã kiểm, model xuất về D và cả ba App đã dừng. [Báo cáo training riêng](../research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html). Các mốc bên dưới giữ theo thời điểm lịch sử.'),
    ('research_tracking/reports/README.md', '[A0 H100](../supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html) đã hoàn tất chọn checkpoint epoch 9 sau 12 epoch, model và dự báo đã lưu trên D. [Bằng chứng](../runs/junyi-a0-h100-batch128-20261112-01/README.md). Refit/calibration/đánh giá độc lập còn chờ.'),
    ('research_tracking/supervisor_reports/README.md', '[Báo cáo riêng A0 H100](2026-11-13/BAO_CAO_A0_H100.html) là một HTML tự chứa, trình bày cấu hình, ba phiên H100, 12 epoch, checkpoint epoch 9, metrics selection, tài nguyên, chi phí và bước còn thiếu. Báo cáo tiến độ tổng thể tiếp tục ở đợt 10/11 và đã cập nhật kết quả này.')]:
    path = ROOT/relative
    content = path.read_text(encoding='utf-8')
    heading_end = content.index('\n')
    path.write_text(content[:heading_end]+'\n\n## Chốt 13/11 — A0 H100 hoàn tất chọn checkpoint\n\n'+text+'\n'+content[heading_end:], encoding='utf-8')

state_path = BUNDLE/'INVOCATION_STATE.json'
state = json.loads(state_path.read_text())
state.update(status='VERIFIED_SELECTED_EXPORTED_REPORT_COMPLETE', current_execution_verified=True,
    latest_selected_ll=0.3535645306110382, remaining_project_credits_snapshot=21.33,
    stale_epochs=3, latest_epoch_snapshot='epoch12-analysis-input.json', local_monitor_session=None,
    verification_session=None, next='Refit/calibration/independent evaluation pending. No GPU launched by report task.',
    standalone_report='research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html',
    exported_model='experiments/akt/results/model-export-a0-batch128-20261112-01/A0_JUNYI_SELECTED.pt')
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
investigation = ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(investigation.read_text(encoding='utf-8-sig'))
state['as_of'] = '2026-11-13'
state['a0_h100_selected_final'] = dict(epochs=12, selected_epoch=9, independent_evaluation=False,
    model_export='experiments/akt/results/model-export-a0-batch128-20261112-01/',
    evidence=str(BUNDLE.relative_to(ROOT)), gpu_active=False, credits_remaining_snapshot=21.33,
    report='research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html',
    next_vi='Chốt giao thức đối chứng batch128, dự toán refit/calibration và đánh giá độc lập trước launch.')
investigation.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
with (BUNDLE/'README.md').open('a', encoding='utf-8') as stream:
    stream.write('\n\n## Nghiệm thu cuối và báo cáo riêng ngày 13/11\n\n'+summary)
    stream.write('\nModel chính ở `experiments/akt/results/model-export-a0-batch128-20261112-01/`, có một `.pt` cùng SUPPORT, MODEL_INDEX và README. '
                 'Báo cáo tự chứa ở `research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html`. '
                 'Dựng lại bằng `build_training_report.py`, số liệu từ epoch12-analysis-input/selection-metrics/resource-summary và các verification/billing/stop-confirmation. '
                 'Figure cuối final012v2 giữ SVG/PDF/PNG/CSV cùng script.\n\n'
                 'Đối soát ledger giữ bản trước thay đổi và toàn bộ reservation lịch sử trong closed_reservations, giải phóng cap đã đóng để tránh tính trùng với metered usage. '
                 'Không thay đổi trần 30 USD, cấm trả thêm và dự phòng 3 USD. Cận trên kế toán 9,002 USD giữ lớn hơn snapshot meter 8,679 USD. '
                 'Không cấp job mới trong gói làm báo cáo.\n')
print('Đã cập nhật báo cáo, chỉ mục và trạng thái phục hồi.')
