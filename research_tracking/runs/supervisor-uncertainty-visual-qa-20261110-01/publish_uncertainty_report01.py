"""Nối diễn tiến RQ2 vào hai báo cáo, giữ toàn bộ hình đã có."""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
OUT = PREP / 'supervisor-uncertainty-update01'
names = ['BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html']
before = {name: (REPORT / name).read_bytes() for name in names}
summary_path = PREP / 'rq2-fresh-block-uncertainty01/summary.json'
review_path = PREP / 'rq2_fresh_uncertainty_independent01.json'
summary = json.loads(summary_path.read_bytes())
review = json.loads(review_path.read_bytes())
assert summary['status'] == 'POSTHOC_EXPLORATORY_NOT_RQ_COMPLETE'
assert summary['family_estimands'] == ['K1000', 'K1150', 'K1150_minus_K1000']
assert 'PASS' in str(review) or 'ACCEPTED' in str(review)
assert not OUT.exists()
OUT.mkdir()
inventory = {name: hashlib.sha256(raw).hexdigest() for name, raw in before.items()}
with (OUT / 'inventory_before_copy.json').open('x') as stream:
    json.dump(inventory, stream, indent=2)
for name, raw in before.items():
    with (OUT / ('before_' + name)).open('xb') as stream:
        stream.write(raw)

title = 'Kiểm độ bất định của xu hướng giữa các khối mô phỏng'
paragraphs = [
    'Sau khi hoàn tất mười khối mới, câu hỏi tiếp theo là trung bình dương có còn đủ rõ khi xét sự biến động giữa các khối hay không. Nhóm dùng lại đúng dữ liệu của Chặng 15, lấy mẫu lại toàn bộ khối để giữ các điều kiện so sánh đi cùng nhau. Có 10.000 lần lấy mẫu lại, nhưng số khối độc lập vẫn là mười và không có lượt mô phỏng mới.',
    'Ba so sánh được xét cùng nhau gồm phần thay đổi khi bật cơ chế phạt ở mức khởi tạo 1000, ở mức 1150, và hiệu của hai phần thay đổi trong cùng khối. So sánh thứ ba là bước cần thiết để hỏi tác động có khác giữa hai mức khởi tạo hay không. Việc một khoảng chứa 0 còn khoảng kia không chứa 0 tự nó chưa trả lời được câu hỏi này.',
    'Ở mức 1000, khoảng thăm dò còn chứa cả giá trị âm và dương. Ở mức 1150, khoảng nằm phía dương trong phép phân tích này. Tuy nhiên, khoảng của chênh lệch giữa hai mức vẫn chứa 0. Vì vậy dữ liệu hiện có chưa phân biệt rõ tác động giữa hai mức khởi tạo, dù các trung bình khác nhau.',
    'Phân tích được bổ sung sau khi đã xem kết quả nên giữ nhãn thăm dò. Các khoảng đã điều chỉnh cho ba so sánh, với mức danh nghĩa 98,33% cho từng khoảng và mức đồng thời danh nghĩa 95%. Đây là xấp xỉ bootstrap trên mười khối, không bảo đảm mức bao phủ chính xác. Lấy mẫu lại nhiều lần không khắc phục được số khối còn ít.',
    'Đã lượng hóa thêm độ bất định và kiểm độc lập các phép tính. Phạm vi vẫn là một đồ thị học được cố định và các giả định của simulator. Đối chứng 1300 bằng 0 theo cơ chế tiếp tục được giữ riêng, không dùng làm bằng chứng thống kê về năng lực. Còn phải khảo sát đồ thị nhiễu, độ ổn định qua các nguồn đồ thị khác và các so sánh CG-AKT đã huấn luyện.'
]
labels = ['Mức khởi tạo 1000', 'Mức khởi tạo 1150', 'Chênh lệch 1150 trừ 1000 trong cùng khối']
rows = []
for label, row in zip(labels, summary['estimates']):
    rows.append((label, f"{row['mean']:+.6f}",
        f"{row['percentile_lower']:+.6f} đến {row['percentile_upper']:+.6f}"))
md_section = '\n## Tiếp theo, ' + title[0].lower() + title[1:] + '\n\n'
md_section += '\n\n'.join(paragraphs[:2]) + '\n\n'
md_section += '| So sánh | Trung bình | Khoảng thăm dò đã điều chỉnh |\n|---|---:|---|\n'
md_section += ''.join('| ' + ' | '.join(row) + ' |\n' for row in rows)
md_section += '\n' + '\n\n'.join(paragraphs[2:]) + '\n\n'
md = before[names[0]].decode('utf-8')
assert md.count('## Còn phải chứng minh') == 1
md = md.replace('## Còn phải chứng minh', md_section + '## Còn phải chứng minh')
old = 'Đây là thống kê mô tả trên mười khối, chưa có kiểm định hoặc khoảng tin cậy để kết luận ưu thế ổn định.'
new = 'Chặng này ghi thống kê mô tả trên mười khối. Phần tiếp theo bổ sung khoảng thăm dò theo khối và các giới hạn của cách diễn giải.'
assert md.count(old) == 1
md = md.replace(old, new)
claim = '**Cập nhật phân tích bất định.** Đã kiểm ba so sánh trên cùng mười khối. Khoảng thăm dò ở mức 1150 nằm phía dương, nhưng chênh lệch tác động giữa mức 1150 và 1000 vẫn chưa phân biệt rõ với 0. Kết quả bổ sung sau khi xem dữ liệu được giữ ở mức thăm dò.\n\n'
md = md.replace('## Quá trình đã thực hiện', claim + '## Quá trình đã thực hiện')

document = before[names[1]].decode('utf-8')
assert 'id="chang-16"' not in document and document.count(old) == 1
document = document.replace(old, new)
document = document.replace('Đến ngày 09/11, nghiên cứu đã đi đến đâu?', 'Đến ngày 10/11, nghiên cứu đã đi đến đâu?')
toc = '<a href="#chang-16">16. Kiểm độ bất định giữa các khối</a>'
assert document.count('</nav>') == 1
document = document.replace('</nav>', toc + '</nav>')
section = '<section id="chang-16"><div class="label">Chặng 16</div><h2>' + title + '</h2>'
section += '<div class="measure">' + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs[:2]) + '</div>'
section += '<div class="table-scroll" tabindex="0"><table><caption>Phần thay đổi của chênh lệch đồ thị khi bật cơ chế phạt, đơn vị Elo của simulator</caption><thead><tr><th>So sánh</th><th>Trung bình</th><th>Khoảng thăm dò đã điều chỉnh</th></tr></thead><tbody>'
section += ''.join('<tr><th scope="row">' + html.escape(row[0]) + '</th><td>' + row[1] + '</td><td>' + row[2] + '</td></tr>' for row in rows)
section += '</tbody></table></div><div class="measure">' + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs[2:]) + '</div></section>\n'
match = re.search(r'<section[^>]*id="([^"]+)"[^>]*>\s*<h2>[^<]*(?:Nguồn|Tài liệu)', document)
assert match is not None, 'Source section anchor must be inspected, never guess placement'
document = document[:match.start()] + section + document[match.start():]
summary_anchor = '<section id="tien-do"><h2>Đến ngày 10/11, nghiên cứu đã đi đến đâu?</h2>'
assert document.count(summary_anchor) == 1
document = document.replace(summary_anchor, summary_anchor + '<div class="measure"><p><strong>Đã kiểm thêm độ bất định theo khối.</strong> Khoảng thăm dò ở mức 1150 nằm phía dương, nhưng so sánh trực tiếp với mức 1000 còn chưa phân biệt rõ với 0. Chặng 16 trình bày phép tính, cách đọc và giới hạn hậu nghiệm.</p></div>')
svg_before = re.findall(rb'<svg\b.*?</svg>', before[names[1]], re.S)
svg_after = re.findall(rb'<svg\b.*?</svg>', document.encode('utf-8'), re.S)
assert len(svg_before) == 11 and svg_before == svg_after
assert document.count('<table') == document.count('</table>') == 15
assert document.count('<section') == document.count('</section>')
for name, text in [(names[0], md), (names[1], document)]:
    raw = text.encode('utf-8')
    (REPORT / name).write_bytes(raw)
    with (OUT / ('after_' + name)).open('xb') as stream:
        stream.write(raw)
with (OUT / 'result.json').open('x') as stream:
    json.dump(dict(published=True, old_svg_count=11, old_svg_bytes_unchanged=True,
        table_count=15, section16=True, visual_qa_pending=True,
        summary_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        review_sha256=hashlib.sha256(review_path.read_bytes()).hexdigest()), stream, indent=2)
print('Both human reports updated; 11 SVG exact, 15 tables; visual QA pending')
