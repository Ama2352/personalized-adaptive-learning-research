"""Nối phát hiện về quần thể quan sát vào hai báo cáo hiện hành."""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
OUT = PREP / 'supervisor-ability-panels-update01'
names = ['BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html']
before = {name: (REPORT / name).read_bytes() for name in names}
cases = [('1000', 'rq1-f041-native-panel-20261110-01'),
         ('1150', 'rq1-ability-panel-f081-20261110-01'),
         ('1300', 'rq1-ability-panel-f001-20261110-01')]
data = []
for ability, run in cases:
    value = json.loads((ROOT / 'experiments/gam_kt/results' / run / 'summary.json').read_bytes())
    assert value['steps'] == 120 and value['concepts'] == 28 and value['independent_histories'] == 1
    assert str(value['cell']['ability']) == ability and value['groups']['all28']['rows'] == 3360
    data.append((ability, value['groups']))
assert data[0][1]['all28']['TN'] == 3360
assert data[1][1]['all28']['FP'] == 5 and data[1][1]['queried']['TN'] == 120
assert data[2][1]['not_queried']['TP'] == 215 and data[2][1]['queried']['native_true'] == 0
assert sum(groups['all28']['theta_gate_true'] for _, groups in data) == 220
assert all(groups['all28']['uncertainty_suppression'] == 0 for _, groups in data)
assert not OUT.exists()
OUT.mkdir()
with (OUT / 'inventory_before_copy.json').open('x') as stream:
    json.dump({name: hashlib.sha256(raw).hexdigest() for name, raw in before.items()}, stream, indent=2)
for name, raw in before.items():
    with (OUT / ('before_' + name)).open('xb') as stream:
        stream.write(raw)
title = 'Quan sát toàn bộ trạng thái để thấy điều nhật ký câu hỏi bỏ sót'
paragraphs = [
    'Chặng 14 đã đặt ra giới hạn của việc chỉ đối chiếu khái niệm đang được giao bài. Một câu hỏi tiếp theo là mô hình có công nhận thành thạo ở những khái niệm không được hỏi lúc đó hay không, và các công nhận ấy có đúng với trạng thái thật của simulator hay không. Nếu thiếu phần quan sát này, nhật ký bài làm có thể che cả đánh giá đúng lẫn đánh giá sai của hệ thống.',
    'Nhóm giữ cùng một cấu hình GAM kế thừa và đồ thị chuyên gia, tắt cơ chế phạt thiếu tiên quyết trong thế giới mô phỏng, rồi kiểm ba mức kiến thức nền 1000, 1150 và 1300 trong cùng một khối khởi tạo. Các lịch sử này khác quần thể của Chặng 14. Tại mỗi thời điểm trong 120 bước, nhóm ghi đủ 28 khái niệm từ các lần đọc trạng thái vốn có của bộ chọn bài. Lựa chọn, dự báo và trạng thái cuối phải khớp lịch sử gốc trước khi đối chiếu với trạng thái thật được dựng lại từ initial và các cập nhật đã lưu.',
    'Mỗi mức có 3360 lần đo khái niệm–thời điểm, trong đó 120 lần thuộc khái niệm đang được hỏi và 3240 lần thuộc các khái niệm còn lại. Ba lịch sử cùng thuộc một khối ngẫu nhiên. Số lần đo lặp không được xem là số người học hoặc số khối độc lập. Bảng dưới đối chiếu quyết định thành thạo với tiêu chí latent ở ngưỡng 1250 của simulator.',
    'Ở mức 1300, mô hình công nhận đúng 215 lần đo trạng thái, toàn bộ ở các khái niệm không được hỏi lúc đó. Nhật ký chỉ gồm khái niệm đang được giao bài sẽ không cho thấy những công nhận đúng này. Ở mức 1150, năm lần công nhận thành thạo đều là công nhận nhầm và cũng nằm ngoài khái niệm đang được hỏi. Chỉ nhìn 120 lần hỏi của mức này sẽ thấy toàn trường hợp chưa đạt được đánh giá chưa đạt, nhưng bỏ sót cả năm công nhận nhầm trong trạng thái còn lại.',
    'Phát hiện mới là phạm vi quan sát làm thay đổi điều có thể kết luận về mô hình. Không thể từ việc chưa thấy công nhận thành thạo ở câu được giao suy ra mô hình chưa công nhận bất kỳ khái niệm nào. Đồng thời, một bảng chỉ có các trường hợp chưa đạt cũng chưa kiểm được khả năng nhận diện trạng thái đã đạt. Kết quả phù hợp với quy tắc ưu tiên các khái niệm chưa được mô hình công nhận trong bộ chọn bài, nhưng chưa định lượng tác động của quy tắc đó lên kết quả học.',
    'Nhóm còn kiểm được điều kiện bất định ở những thời điểm điểm kiến thức ước lượng đã đạt ngưỡng. Có 220 cơ hội như vậy trong cả ba lịch sử, nhưng điều kiện bất định không chặn công nhận thành thạo lần nào. Đây là quan sát có điều kiện trong cửa sổ 120 bước của cấu hình đang kiểm. Chưa thể suy điều kiện bất định luôn dư thừa ở mọi hồ sơ hoặc thời gian học.',
    'Mô hình bắt đầu với điểm ước lượng 1200, còn trạng thái nền của simulator được thay giữa ba mức. Vì vậy, khởi tạo và độ dài lịch sử phải được đọc cùng các chênh lệch thành thạo. Phép kiểm mới tạo được phản ví dụ rõ về giới hạn của nhật ký câu hỏi và nối RQ1 với điều kiện người học trong RQ2. Nó chưa là so sánh đồ thị, bằng chứng CG-AKT cải thiện hoặc kết luận trên người học thật. Phần tiếp theo cần kiểm nhiều khối độc lập và nối các chẩn đoán với so sánh mô hình đã huấn luyện.'
]
rows1 = [(ability, str(g['all28']['latent_true']), str(g['all28']['native_true']), str(g['queried']['native_true'])) for ability, g in data]
rows2 = [(ability, str(g['not_queried']['TP']), str(g['not_queried']['FP'])) for ability, g in data]


def md_table(headers, rows):
    return '| ' + ' | '.join(headers) + ' |\n|' + '|'.join(['---']*len(headers)) + '|\n' + ''.join('| ' + ' | '.join(row) + ' |\n' for row in rows)


def html_table(caption, headers, rows):
    result = '<div class="table-scroll" tabindex="0"><table><caption>' + html.escape(caption) + '</caption><thead><tr>'
    result += ''.join('<th>' + html.escape(h) + '</th>' for h in headers) + '</tr></thead><tbody>'
    for row in rows:
        result += '<tr><th scope="row">' + html.escape(row[0]) + '</th>' + ''.join('<td>' + html.escape(v) + '</td>' for v in row[1:]) + '</tr>'
    return result + '</tbody></table></div>'


h1 = ['Mức nền', 'Trạng thái thật đạt ngưỡng', 'Mô hình công nhận', 'Công nhận tại câu đang hỏi']
h2 = ['Mức nền', 'Công nhận đúng ngoài câu đang hỏi', 'Công nhận nhầm ngoài câu đang hỏi']
section_md = '\n## Tiếp theo, ' + title[0].lower() + title[1:] + '\n\n'
section_md += '\n\n'.join(paragraphs[:3]) + '\n\n' + md_table(h1, rows1) + '\n'
section_md += paragraphs[3] + '\n\n' + md_table(h2, rows2) + '\n'
section_md += '\n\n'.join(paragraphs[4:]) + '\n\n'
md = before[names[0]].decode('utf-8')
assert md.count('## Còn phải chứng minh') == 1
md = md.replace('## Còn phải chứng minh', section_md + '## Còn phải chứng minh')
claim = '**Phát hiện mới về cách đo thành thạo.** Trên ba lịch sử cùng một khối, quan sát toàn bộ 28 khái niệm cho thấy nhật ký chỉ gồm câu đang giao bỏ ngoài 215 công nhận đúng và 5 công nhận nhầm ở những khái niệm khác tại cùng thời điểm. Đã kiểm độc lập trạng thái dựng lại ở mọi bước. Các con số là lần đo lặp, chưa là bằng chứng khái quát qua nhiều người học.\n\n'
md = md.replace('## Quá trình đã thực hiện', claim + '## Quá trình đã thực hiện')
old = '- **RQ1** đã có đối chiếu tại câu được giao của một lịch sử. Cần mở rộng sang quần thể khái niệm–thời điểm độc lập với selector, hiệu chỉnh xác suất và nối với kết quả học tập.'
new = '- **RQ1** đã có đối chiếu đủ 28 khái niệm tại mỗi bước trên ba lịch sử cùng một khối. Cần kiểm độ phổ biến qua nhiều khối độc lập, hiệu chỉnh xác suất và nối với kết quả học tập trong các so sánh mô hình.'
assert md.count(old) == 1
md = md.replace(old, new)
document = before[names[1]].decode('utf-8')
assert 'id="chang-17"' not in document
document = document.replace('</nav>', '<a href="#chang-17">17. Kiểm trạng thái ngoài câu đang hỏi</a></nav>')
section = '<section id="chang-17"><div class="label">Chặng 17</div><h2>' + title + '</h2><div class="measure">'
section += ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs[:3]) + '</div>'
section += html_table('Toàn bộ 28 khái niệm tại 120 thời điểm, 3360 lần đo mỗi mức', h1, rows1)
section += '<div class="measure"><p>' + html.escape(paragraphs[3]) + '</p></div>'
section += html_table('Các công nhận nằm ngoài khái niệm đang được hỏi tại cùng thời điểm', h2, rows2)
section += '<div class="measure">' + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs[4:]) + '</div></section>\n'
anchor = re.search(r'<section[^>]*id="([^"]+)"[^>]*>\s*<h2>[^<]*(?:Nguồn|Tài liệu)', document)
assert anchor is not None
document = document[:anchor.start()] + section + document[anchor.start():]
progress = '<section id="tien-do"><h2>Đến ngày 10/11, nghiên cứu đã đi đến đâu?</h2>'
assert document.count(progress) == 1
document = document.replace(progress, progress + '<div class="finding"><p><strong>Đã xác định thêm một giới hạn của phép đo thành thạo.</strong> Khi quan sát đủ 28 khái niệm ở mọi bước, ba lịch sử cùng một khối làm lộ 215 công nhận đúng và 5 công nhận nhầm nằm ngoài câu đang hỏi. Chặng 17 giải thích vì sao nhật ký bài làm chưa phản ánh toàn bộ trạng thái và giới hạn của bằng chứng này.</p></div>')
svg_before = re.findall(rb'<svg\b.*?</svg>', before[names[1]], re.S)
svg_after = re.findall(rb'<svg\b.*?</svg>', document.encode('utf-8'), re.S)
assert len(svg_before) == 11 and svg_before == svg_after
assert document.count('<table') == document.count('</table>') == 17
assert document.count('<section') == document.count('</section>')
for name, text in [(names[0], md), (names[1], document)]:
    raw = text.encode('utf-8')
    (REPORT / name).write_bytes(raw)
    with (OUT / ('after_' + name)).open('xb') as stream:
        stream.write(raw)
with (OUT / 'result.json').open('x') as stream:
    json.dump(dict(published=True, old_svg_count=11, old_svg_bytes_unchanged=True,
        table_count=17, chapter17=True, visual_qa_pending=True, groups=data,
        scope='Three histories, one block. No new simulation/model training or RQ completion.'), stream, indent=2)
print('Both reports updated with Chapter17; original11SVG exact,17tables; visual QA pending')
