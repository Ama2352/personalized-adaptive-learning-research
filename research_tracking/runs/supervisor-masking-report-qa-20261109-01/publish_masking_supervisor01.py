"""Nối chặng11 vào hai báo cáo, giữ nguyên10SVG trước và lưu snapshot."""
import hashlib
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
proof = json.loads((PREP / 'masking_independent_native_recount02.json').read_bytes())
assert proof['status'] == 'INDEPENDENT_NATIVE_SNAPSHOT_PREDICATE_RECOUNT_PASS'
assert proof['event_reason_counts'] == dict(no_direct_child_and_own_prerequisites_blocked=18,
    child_mastered_without_exposure=8, child_mastered_and_exposure=4)
assert proof['nonexclusive_predicate_counts'] == dict(child_mastered_both=12, exposure_exception=4, both=4)
base = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
paths = [base / 'BAO_CAO.md', base / 'BAO_CAO_NGHIEN_CUU.html']
originals = {path.name: path.read_bytes() for path in paths}
snapshot = PREP / 'supervisor-before-masking01'
snapshot.mkdir(exist_ok=False)
before = {name: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) for name, raw in originals.items()}
(snapshot / 'inventory-before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for name, raw in originals.items():
    with (snapshot / name).open('xb') as stream:
        stream.write(raw)
    assert hashlib.sha256((snapshot / name).read_bytes()).hexdigest() == before[name]['sha256']

draft = (PREP / 'SUPERVISOR_MASKING_INSERT_DRAFT01.md').read_text(encoding='utf-8')
paragraphs = draft.strip().split('\n\n')
assert len(paragraphs) == 6 and paragraphs[0].startswith('## ')
body = [f'<p>{escape(paragraph)}</p>' for paragraph in paragraphs[1:]]
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 330" role="img" aria-labelledby="masking-stops-title masking-stops-desc">
<title id="masking-stops-title">Ba nhóm trong30thời điểm có nhãn khác nhau và cùng tập R</title>
<desc id="masking-stops-desc">18khái niệm không có con trực tiếp;8khái niệm con có nhãn thành thạo và chưa đủ6lần luyện;4khái niệm con có nhãn thành thạo đồng thời đủ6lần luyện. Cả30thuộc hồ sơ PG trên lịch sử đã lưu.</desc>
<rect width="100%" height="100%" fill="white"/>
<g font-family="Segoe UI,Arial,sans-serif" fill="#17324d">
<text x="20" y="29" font-size="20" font-weight="600">30 thời điểm có nhãn khác nhau nhưng cùng tập R</text>
<line x1="465" y1="52" x2="465" y2="295" stroke="#a9becd"/>
<text x="20" y="83" font-size="18">Không có khái niệm con trực tiếp</text>
<text x="20" y="106" font-size="16">và chính nó vẫn bị tiên quyết chặn khỏi R</text>
<rect x="465" y="68" width="320" height="46" rx="3" fill="#346fa0"/>
<text x="875" y="100" text-anchor="end" font-size="24" font-weight="650">18</text>
<text x="20" y="169" font-size="18">Con có cùng nhãn thành thạo</text>
<text x="20" y="192" font-size="16">chưa đủ 6 lần luyện ở tiên quyết</text>
<rect x="465" y="154" width="142.222222" height="46" rx="3" fill="#087d86"/>
<text x="875" y="186" text-anchor="end" font-size="24" font-weight="650">8</text>
<text x="20" y="255" font-size="18">Con có cùng nhãn thành thạo</text>
<text x="20" y="278" font-size="16">đồng thời đủ 6 lần luyện ở tiên quyết</text>
<rect x="465" y="240" width="71.111111" height="46" rx="3" fill="#a57524"/>
<text x="875" y="272" text-anchor="end" font-size="24" font-weight="650">4</text>
<text x="20" y="319" font-size="14">Hai nhóm sau cùng gồm12thời điểm, trong đó4thời điểm có hai điều kiện cùng hiện diện.</text>
</g></svg>'''
section = ('<section id="chang-11"><div class="label">Chặng 11</div>'
    '<h2>Giải thích nơi khác biệt thành thạo bị giữ lại trước bước chọn bài</h2>'
    '<div class="measure">' + ''.join(body[:3]) + '</div>'
    '<figure><div class="svg-frame">' + svg + '</div><figcaption>'
    'Phân loại theo các điều kiện cùng quan sát được. Trong12thời điểm có khái niệm con mang nhãn thành thạo, '
    '4thời điểm còn thỏa ngoại lệ số lần luyện. Các nhãn là trạng thái ước lượng của mô hình. '
    'R là tập sẵn sàng ban đầu trước các bước lọc và mở rộng ứng viên tiếp theo.'
    '</figcaption></figure><div class="measure">' + ''.join(body[3:]) + '</div></section>\n')
html = originals['BAO_CAO_NGHIEN_CUU.html'].decode('utf-8')
old_svgs = re.findall(r'<svg\b.*?</svg>', html, flags=re.DOTALL)
assert len(old_svgs) == 10 and html.count('<section id="con-thieu">') == 1
html = html.replace('<section id="con-thieu">', section + '<section id="con-thieu">')
nav = '<a href="#con-thieu">Phần còn thiếu</a>'
assert html.count(nav) == 1
html = html.replace(nav, '<a href="#chang-11">11. Từ thành thạo đến tập sẵn sàng</a>' + nav)
marker = 'Chưa có phép so sánh các mô hình đã huấn luyện đủ để kết luận CG-AKT cải thiện dự báo, chọn bài hoặc kết quả học.</div>'
assert html.count(marker) == 1
current = ('<p class="measure"><strong>Phát hiện mới nhất cho RQ1.</strong> '
    'Đã giải thích đủ30thời điểm hai cấu hình có nhãn thành thạo khác nhau nhưng cùng tập sẵn sàng ban đầu. '
    'Có18trường hợp ở khái niệm không có con trực tiếp và12trường hợp có con mang nhãn thành thạo, '
    'trong đó4trường hợp đồng thời thỏa ngoại lệ đủ số lần luyện. '
    'Phép kiểm đã được tính lại từ trạng thái gốc; phần đánh giá kiến thức thật và tác động lên học tập tiếp tục còn thiếu.</p>')
html = html.replace(marker, marker + current)
table_marker = 'Đã chứng minh điều kiện đủ để quy tắc giữ chương bảo đảm không quay lại, cùng phản ví dụ xác định ranh giới khi có cạnh liên chương.'
assert html.count(table_marker) == 1
html = html.replace(table_marker, table_marker + ' Đã nối tiếp chẩn đoán tới bước dựng tập sẵn sàng ban đầu, giải thích đủ30thời điểm nhãn khác nhau mà tập này giống nhau, kể cả điều kiện trùng nhau.')
new_svgs = re.findall(r'<svg\b.*?</svg>', html, flags=re.DOTALL)
assert len(new_svgs) == 11 and new_svgs[:10] == old_svgs
assert html.count('<table') == 11
ids = re.findall(r'\bid="([^"]+)"', html)
assert len(ids) == len(set(ids))
assert all(anchor in ids for anchor in re.findall(r'href="#([^"]+)"', html))

summary = originals['BAO_CAO.md'].decode('utf-8')
marker = '## Còn phải chứng minh'
assert summary.count(marker) == 1
addition = ('**Giải thích bước từ thành thạo đến tập sẵn sàng ban đầu.** '
    'Trên cùng1.080thời điểm, hai cấu hình Graph-GAM-KT nhận31và0cạnh có90thời điểm khác nhãn thành thạo ở một khái niệm. '
    'Tập sẵn sàng ban đầu R khác nhau ở60thời điểm và giống nhau ở30thời điểm. '
    'R là đầu vào cho các bước lọc và mở rộng ứng viên tiếp theo của bộ chọn bài. '
    'Trong cả90thời điểm, chính khái niệm mang nhãn khác nhau đều còn bị điều kiện tiên quyết chặn khỏi R.\n\n'
    'Đã giải thích đủ30thời điểm có cùng R. Có18trường hợp ở khái niệm không có con trực tiếp trong đồ thị của bộ điều khiển, '
    'còn12trường hợp có khái niệm con đã mang nhãn thành thạo ở cả hai cấu hình. '
    'Trong12trường hợp sau có4trường hợp đồng thời đủ6lần luyện ở tiên quyết, nên cần ghi rõ phần trùng nhau khi giải thích. '
    'Tất cả30trường hợp thuộc hồ sơ PG. Kết quả đã được tính lại trực tiếp từ18trace gốc của cùng chín lịch sử. '
    'Phần đánh giá độ đúng của nhãn so với kiến thức thật và tác động lên học tập vẫn cần làm tiếp.\n\n')
summary = summary.replace(marker, addition + marker)
opening = '**Đã có bằng chứng chẩn đoán mới cho RQ1–RQ2,'
assert opening in summary
prefix_end = summary.index('\n\n', summary.index(opening))
summary = summary[:prefix_end] + '\n\n**Mốc RQ1 mới nhất.** Đã giải thích đủ30thời điểm nhãn thành thạo khác nhau nhưng tập sẵn sàng ban đầu giống nhau, với phần trùng nhau giữa các điều kiện được kiểm riêng.' + summary[prefix_end:]
outputs = {paths[0]: summary.encode('utf-8'), paths[1]: html.encode('utf-8')}
for path, raw in outputs.items():
    path.write_bytes(raw)
result = dict(status='SUPERVISOR_STAGE11_UPDATED_STATIC_QA_PENDING_RENDER', before=before,
    after={path.name: dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()) for path, raw in outputs.items()},
    previous_svg_byte_identical=10, total_svg=11, tables=11, local_anchors_valid=True,
    source_recount='artifacts/akt/local-tests/akt-research-runner-20261108-01/masking_independent_native_recount02.json',
    event_counts=dict(no_child=18, child_mastered_without_exposure=8, child_mastered_and_exposure=4),
    nonexclusive_predicates=dict(child_mastered=12, exposure=4, overlap=4), visual_render=False)
target = ROOT / 'docs/thesis_recovery/evidence/supervisor_masking_update_20261109.json'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items() if key not in ('before', 'after')}))
