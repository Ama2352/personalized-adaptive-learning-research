"""Nối mốc GKT vào tiến độ đã xác nhận bằng terminal thật."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[4]
p = Path(__file__).resolve().parent
actual = json.loads((p / 'gkt-selected-fit03/outer-final.json').read_bytes())
assert actual['status'] == 'ACCEPTED_ACTUAL_GKT_SELECTED_ONLY_ENGINEERING'
assert actual['errors'] == [] and actual['owned_receipt']['job_active_after_cleanup'] == 0
check = json.loads((p / 'gkt-selected-fit03/actual-completion-check.json').read_bytes())
assert check['epochs'] == 11 and check['selected_epoch'] == 6 and check['claim']['full_targets'] == 84
out = p / 'supervisor-gkt-cpu-progress01'
out.mkdir(exist_ok=False)
folder = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
anchor = 'Thí nghiệm chính trên corpus nghiên cứu, confidence/gate, huấn luyện lại, hiệu chỉnh xác suất '
addition = ('GKT được kiểm tiếp bằng cấu hình riêng đã cố định. Lượt kiểm hoàn tất 11 vòng học, '
    'chọn vòng 6, nạp lại checkpoint và xuất đủ 84 dự báo. ')
for name in ['BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html']:
    path = folder / name
    before = path.read_bytes()
    (out / ('before_' + name)).write_bytes(before)
    text = before.decode('utf-8')
    assert text.count(anchor) == 1
    text = text.replace(anchor, addition + anchor)
    if name.endswith('.html'):
        assert re.findall(r'<svg\b.*?</svg>', before.decode('utf-8'), re.S) == re.findall(r'<svg\b.*?</svg>', text, re.S)
        assert text.count('<table') == text.count('</table>') == 17
    after = text.encode('utf-8')
    path.write_bytes(after)
    (out / ('after_' + name)).write_bytes(after)
(out / 'result.json').write_text(json.dumps({'published': True, 'visual_qa_pending': True,
    'scientific_scope_vi': 'Hai mốc CPU engineering, không thêm kết luận ưu thế hoặc hoàn tất RQ.'},
    ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('GKT_CPU_MILESTONE_BOTH_REPORTS_STATIC_PASS')
