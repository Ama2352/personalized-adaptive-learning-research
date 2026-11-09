"""Cập nhật mốc CPU SAKT đã nghiệm thu, giữ nguyên hình nghiên cứu."""
from pathlib import Path
import hashlib
import json
import re

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
report = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
out = prep / 'supervisor-ability-polish02'
out.mkdir(exist_ok=False)
actual = json.loads((prep / 'sakt-selected-fit05/outer-final.json').read_bytes())
assert actual['status'] == 'ACCEPTED_ACTUAL_SAKT_SELECTED_ONLY_ENGINEERING'
assert not actual['gpu_ready'] and not actual['refit_or_calibration_performed']
paragraph = ('SAKT đã hoàn tất một vòng đời kiểm kỹ thuật CPU trên corpus nhỏ gồm 8 người học huấn luyện, '
    '1 người học chọn vòng và 1 người học dành riêng cho hiệu chỉnh. Lượt kiểm chạy 6 vòng học, '
    'chọn checkpoint vòng 1, nạp lại checkpoint và xuất đủ 84 dự báo của tập chọn vòng. '
    'Tập hiệu chỉnh chưa được dùng để tối ưu hoặc đánh giá mô hình. Đây là bằng chứng pipeline hoạt động '
    'trên corpus kiểm kỹ thuật, chưa là kết quả so sánh SAKT trong thí nghiệm chính.')
hashes = {}
for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html'):
    path = report / name
    raw = path.read_bytes()
    (out / ('before_' + name)).write_bytes(raw)
    text = raw.decode('utf-8').replace('dựng lại từ initial và', 'dựng lại từ trạng thái khởi tạo và')
    text = text.replace('tiêu chí latent ở ngưỡng', 'tiêu chí trạng thái ẩn ở ngưỡng')
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
(out / 'result.json').write_text(json.dumps({'hashes': hashes, 'visual_qa_pending': True,
    'scope': 'Narrative/CPU engineering milestone only; no new research sample.'}, indent=2) + '\n', encoding='utf-8')
print('POLISH02_APPLIED_11SVG_PRESERVED_17TABLES')
