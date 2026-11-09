"""Đặt phát hiện nghiên cứu trước mốc phần mềm trong phần tiến độ."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[4]
p = Path(__file__).resolve().parent
out = p / 'final-report-story-polish01'
out.mkdir(exist_ok=False)
folder = root / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
replacements = {'corpus nhỏ': 'bộ dữ liệu mô phỏng nhỏ', 'corpus kiểm kỹ thuật': 'bộ dữ liệu kiểm kỹ thuật',
    'kiểm khởi tạo backbone trùng nhau': 'kiểm phần AKT gốc có cùng trạng thái khởi tạo',
    'Thí nghiệm chính trên corpus nghiên cứu, confidence/gate,':
        'Thí nghiệm chính, độ tin cậy cạnh và cơ chế điều tiết ảnh hưởng đồ thị,'}
for name in ['BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html']:
    path = folder / name
    before = path.read_bytes()
    (out / ('before_' + name)).write_bytes(before)
    text = before.decode('utf-8')
    if name.endswith('.html'):
        pattern = r'(<section id="tien-do"><h2>.*?</h2>)(<div class="measure"><p>Đường chạy AKT.*?</p></div>)(<div class="measure"><p>SAKT.*?</p></div>)'
        match = re.search(pattern, text, re.S)
        assert match is not None
        blocks = match.group(2) + match.group(3)
        for old, new in replacements.items():
            blocks = blocks.replace(old, new)
        text = text[:match.start()] + match.group(1) + text[match.end():]
        section = re.search(r'<section id="tien-do">.*?</section>', text, re.S)
        assert section is not None
        insertion = '<h3 id="chuan-bi-mo-hinh">Chuẩn bị mô hình cho thí nghiệm tiếp theo</h3>' + blocks
        position = section.end() - len('</section>')
        text = text[:position] + insertion + text[position:]
        assert re.findall(r'<svg\b.*?</svg>', before.decode('utf-8'), re.S) == re.findall(r'<svg\b.*?</svg>', text, re.S)
        assert text.count('<table') == text.count('</table>') == 17
    else:
        for prefix in ['SAKT đã hoàn tất một vòng đời', 'Đường chạy AKT có đồ thị cố định']:
            match = re.search(re.escape(prefix) + r'.*?(?=\n\n)', text, re.S)
            assert match is not None
            paragraph = match.group(0)
            for old, new in replacements.items():
                paragraph = paragraph.replace(old, new)
            text = text[:match.start()] + paragraph + text[match.end():]
        text = text.replace('SAKT đã hoàn tất một vòng đời', '### Chuẩn bị mô hình cho thí nghiệm tiếp theo\n\nSAKT đã hoàn tất một vòng đời', 1)
    after = text.encode('utf-8')
    path.write_bytes(after)
    (out / ('after_' + name)).write_bytes(after)
print('RESEARCH_FINDINGS_FIRST_11SVG_17TABLES_PRESERVED')
