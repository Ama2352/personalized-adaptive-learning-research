"""Cập nhật mốc AKT có đồ thị, chỉ theo terminal đã nghiệm thu."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[4]
p = Path(__file__).resolve().parent
actual = json.loads((p / 'a1-expert-engineering03/outer-final.json').read_bytes())
assert actual['status'] == 'ACCEPTED_ACTUAL_A1_EXPERT_SELECTED_ONLY_ENGINEERING'
assert actual['error'] is None and actual['owned_receipt']['job_active_after_cleanup'] == 0
check = json.loads((p / 'a1-expert-engineering03/actual-completion-check.json').read_bytes())
assert check['claim']['full_targets'] == check['claim']['supported_targets'] == 84
out = p / 'supervisor-fixed-graph-cpu-progress01'
out.mkdir(exist_ok=False)
folder = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
paragraph = ('Đường chạy AKT có đồ thị cố định cũng đã hoàn tất kiểm kỹ thuật trên cùng corpus nhỏ. '
    'Nhóm giữ cùng dữ liệu và cấu hình học với AKT không đồ thị, kiểm khởi tạo backbone trùng nhau, '
    'rồi chạy đủ quy trình huấn luyện, chọn checkpoint, nạp lại và xuất 84 dự báo. '
    'Kết quả này xác nhận thêm một đường so sánh đã hoạt động bằng mô hình thật. '
    'Thí nghiệm chính trên corpus nghiên cứu, confidence/gate, huấn luyện lại, hiệu chỉnh xác suất '
    'và đánh giá học tập vòng kín vẫn còn phải thực hiện.')
hashes = {}
for name in ['BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html']:
    path = folder / name
    raw = path.read_bytes()
    (out / ('before_' + name)).write_bytes(raw)
    text = raw.decode('utf-8')
    if name.endswith('.md'):
        anchor = '## Quá trình đã thực hiện'
        assert text.count(anchor) == 1
        text = text.replace(anchor, paragraph + '\n\n' + anchor)
    else:
        anchor = '<section id="tien-do"><h2>Đến ngày 10/11, nghiên cứu đã đi đến đâu?</h2>'
        assert text.count(anchor) == 1
        text = text.replace(anchor, anchor + '<div class="measure"><p>' + paragraph + '</p></div>')
        assert re.findall(r'<svg\b.*?</svg>', raw.decode('utf-8'), re.S) == re.findall(r'<svg\b.*?</svg>', text, re.S)
        assert text.count('<table') == text.count('</table>') == 17
    after = text.encode('utf-8')
    path.write_bytes(after)
    (out / ('after_' + name)).write_bytes(after)
    hashes[name] = {'before': hashlib.sha256(raw).hexdigest(), 'after': hashlib.sha256(after).hexdigest()}
(out / 'result.json').write_text(json.dumps({'hashes': hashes, 'svg_preserved': 11, 'tables': 17,
    'status': 'NARRATIVE_UPDATED_VISUAL_QA_PENDING', 'scope_vi': 'Mốc kiểm phần mềm, không thêm kết luận hiệu quả.'},
    ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('BOTH_REPORTS_UPDATED_A1_CPU_MILESTONE_STATIC_PASS')
