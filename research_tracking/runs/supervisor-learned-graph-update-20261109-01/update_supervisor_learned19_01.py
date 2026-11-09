"""Nối Chặng13 từ pilot đã nghiệm thu, giữ nguyên11SVG đã có."""
import hashlib
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
RAW = ROOT / 'experiments/simulator/results/rq2-learned-graph-ability-20261109-01'
OUTER = PREP / 'rq2-learned-graph-ability01-outer/final.json'
PROOF = PREP / 'rq2_learned19_independent_verification01.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

assert sha(OUTER) == '55be940503c2f09cc5b2baf4966a14c3ac039a6ed6918d130792ef9c57b8625b'
assert sha(PROOF) == '5d83fbad61f8f562d44ea0cd9d539684e71534f871ae7d0ecddfc36c4b199808'
actual = json.loads(OUTER.read_bytes())
assert actual['status'] == 'ACCEPTED19_FINITE_LEARNED_GRAPH_SOURCE_EXTENSION'
assert actual['error'] is None and actual['owned_receipt']['job_active_after_cleanup'] == 0
assert all(sha(RAW / name) == value for name, value in actual['outputs_sha256'].items())
q_rows = json.loads((RAW / 'graph_source_contrasts.json').read_bytes())
k_rows = json.loads((RAW / 'conditional_lambda_contrasts.json').read_bytes())
q = {(r['block'], r['ability'], r['mechanism_strength']): r['expert_minus_learned'] for r in q_rows}
k = {(r['block'], r['ability']): r['lambda_difference'] for r in k_rows}
assert len(q) == 18 and len(k) == 9
assert all(q[b, 1300, 0.] == q[b, 1300, .55] and k[b, 1300] == 0.
           for b in (21000, 21001, 21002))
rows = []
for index, block in enumerate((21000, 21001, 21002), 1):
    rows.append([str(index), f'{q[block, 1300, 0.]:+.6f}',
                 *(f'{k[block, ability]:+.6f}' for ability in (1000, 1150, 1300))])

paragraphs = [
    'Các chặng trước đã cho thấy kết quả học có thể chịu ảnh hưởng của cơ chế mô phỏng và cách mô hình sử dụng thông tin cha. Từ đây, nhóm đặt câu hỏi tiếp theo cho RQ2. Khi thay đồ thị chuyên gia bằng đồ thị được ước lượng từ dữ liệu, chênh lệch học tập có thực sự đi qua cơ chế thiếu kiến thức nền, hay còn xuất hiện qua những đường khác của hệ thống?',
    'Nhóm dùng đồ thị31cạnh đã ước lượng từ phần huấn luyện, chỉ thay đầu vào đồ thị của mô hình GAM. Đồ thị mô tả thế giới và đồ thị của bộ điều khiển giữ nguyên theo chuyên gia. Các cơ chế dùng tín hiệu cha và điều chỉnh theo cha được giữ bật, điều chỉnh cục bộ giữ tắt. Mỗi cặp giữ cùng trạng thái kiến thức thật ban đầu, lịch thời gian và dòng số ngẫu nhiên. Lượt mở rộng có18ca mới, tương ứng ba khối ngẫu nhiên, ba mức năng lực và hai mức phạt thiếu nền tảng. Trước đó, một ca đối chứng cũ được chạy lại và khớp đủ120lượt cùng trạng thái cuối.',
    'Để đánh giá học thêm được bao nhiêu, nhóm đo mức tăng ròng của kiến thức ẩn trung bình trên28khái niệm ở cuối lịch41ngày, trên thang Elo của simulator. Đây là đầu ra học tập của thế giới mô phỏng. Các thước đo dự báo đáp án như Log Loss vẫn có vai trò riêng ở bước đánh giá mô hình ước lượng.',
    'Kết quả cho thấy cả18cặp chuyên gia–đồ thị học đều có chuỗi câu hỏi khác nhau. Tổng cộng1409trong2160vị trí thứ tự dùng câu hỏi khác, trong đó nhóm năng lực1300có600trong720vị trí. Sau khi đường đi phân kỳ, cùng vị trí thứ tự có thể là hai bài khác nhau, nên cần đọc chênh lệch học tập trong bối cảnh hai lộ trình đã khác.',
    'Ở nhóm năng lực1300, mô phỏng xác nhận thiếu hụt tiên quyết bằng0trong toàn bộ các lượt mới. Với từng đồ thị, bật mức phạt từ0lên0,55giữ nguyên cả lịch sử và trạng thái cuối. Tuy vậy, khi đổi nguồn đồ thị, mức tăng kiến thức vẫn khác. Chênh lệch giữa hai đồ thị ở ba khối lần lượt là−0,197266, +0,181461và+0,076440Elo, và giữ nguyên khi bật mức phạt. Như vậy, chênh lệch tổng thể còn có thể xuất hiện qua đường ước lượng và chọn bài khi cơ chế phạt thiếu nền tảng đang bất hoạt.',
    'Nhóm lấy mức tăng của cấu hình chuyên gia trừ cấu hình đồ thị học, rồi kiểm chênh lệch đó thay đổi bao nhiêu khi bật mức phạt. Bảng dưới giữ đầy đủ ba khối. Ở mức năng lực1150, cả ba thay đổi đều âm. Ở mức1000, dấu thay đổi trái chiều giữa các khối. Ở mức1300, cả ba bằng0theo đối chứng bất hoạt đã kiểm. Các mức năng lực này là can thiệp vào trạng thái ban đầu trong mô phỏng.',
    'Phần mở rộng đã tách thêm được nguồn đồ thị của bộ ước lượng khỏi đồ thị thế giới và bộ điều khiển, đồng thời xác định một chênh lệch vẫn tồn tại khi cơ chế thiếu tiên quyết bất hoạt. Ba khối được dùng lại từ chẩn đoán trước, nên chưa tăng số khối độc lập. Điều kiện cũ được tái dựng từ nguồn và kiểm khớp qua một ca đối chứng đầy đủ. Khả năng khái quát sang người học mới, mức nhiễu khác và chất lượng đồ thị tiên quyết còn cần đánh giá tiếp. Kết quả hiện tại chưa xác lập thứ hạng chung giữa đồ thị chuyên gia và đồ thị học.'
]
# Giữ khoảng trắng quanh con số trong văn xuôi để đọc tự nhiên.
fixes = {'đồ thị31': 'đồ thị 31', 'có18': 'có 18', 'đủ120': 'đủ 120',
         'trên28': 'trên 28', 'lịch41': 'lịch 41', 'cả18': 'cả 18',
         'cộng1409trong2160': 'cộng 1.409 trong 2.160', 'lực1300có600trong720': 'lực 1300 có 600 trong 720',
         'lực1300': 'lực 1300', 'bằng0trong': 'bằng 0 trong', 'từ0lên0,55giữ': 'từ 0 lên 0,55 giữ',
         'là−0,197266': 'là −0,197266', '+0,181461và+0,076440Elo': '+0,181461 và +0,076440 Elo',
         'lực1150': 'lực 1150', 'mức1000': 'mức 1000', 'mức1300': 'mức 1300', 'bằng0theo': 'bằng 0 theo'}
for source, target in fixes.items():
    paragraphs = [p.replace(source, target) for p in paragraphs]

headers = ['Khối', 'Chuyên gia − đồ thị học ở năng lực 1300',
           'Thay đổi khi bật phạt, năng lực 1000',
           'Thay đổi khi bật phạt, năng lực 1150',
           'Thay đổi khi bật phạt, năng lực 1300']
caption = 'Đối chứng theo ba khối mô phỏng, đơn vị Elo của mức tăng kiến thức ẩn'
note = 'Giá trị âm ở cột chênh lệch nghĩa là cấu hình đồ thị học có mức tăng lớn hơn. Ba cột cuối là chênh lệch tại mức phạt 0,55 trừ chênh lệch tại mức phạt 0. Các giá trị chỉ mô tả những trường hợp đã khảo sát.'
claim = '**Mốc mới cho RQ2.** Đã mở rộng đối chứng sang đồ thị học từ dữ liệu. Cả 18 cặp đổi chuỗi bài. Ở nhóm năng lực cao có cơ chế thiếu tiên quyết bất hoạt, đổi nguồn đồ thị vẫn làm kết quả học khác nhau, còn bật mức phạt giữ nguyên lịch sử và trạng thái cuối. Điều này tách được một chênh lệch ngoài cơ chế phạt thiếu nền tảng; khả năng khái quát và thứ hạng đồ thị còn phải kiểm tiếp.'

md_path, html_path = REPORT / 'BAO_CAO.md', REPORT / 'BAO_CAO_NGHIEN_CUU.html'
expected = {md_path.name: '5cad0e89bdf3fc2e2bdff37da72da88d26f482eb22856f30c2fbe3eca78a7dac',
            html_path.name: 'a19d007c0272061317af470eda6df93bec5818dd51349040f8cf0f44cb33496f'}
assert {p.name: sha(p) for p in (md_path, html_path)} == expected
backup = PREP / 'supervisor-learned19-before01'
backup.mkdir(exist_ok=False)
for path in (md_path, html_path):
    (backup / path.name).write_bytes(path.read_bytes())
    assert sha(backup / path.name) == expected[path.name]
md = md_path.read_bytes().decode('utf-8')
page = html_path.read_bytes().decode('utf-8')
assert '## Chặng 13.' not in md and 'id="chang-13"' not in page
md = md.replace('## Quá trình đã thực hiện', claim + '\n\n## Quá trình đã thực hiện', 1)
table_md = '| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join(['---'] * len(headers)) + ' |\n'
table_md += ''.join('| ' + ' | '.join(row) + ' |\n' for row in rows)
section_md = ('## Chặng 13. Đổi nguồn đồ thị khi cơ chế thiếu nền tảng bất hoạt\n\n'
    + '\n\n'.join(paragraphs[:-1]) + '\n\n' + table_md + '\n' + note + '\n\n' + paragraphs[-1] + '\n\n')
md = md.replace('## Còn phải chứng minh', section_md + '## Còn phải chứng minh', 1)
page = page.replace('<a href="#con-thieu">Phần còn thiếu</a>',
    '<a href="#chang-13">13. Đổi nguồn đồ thị và đối chứng bất hoạt</a><a href="#con-thieu">Phần còn thiếu</a>', 1)
claim_html = '<p class="measure"><strong>' + html.escape(claim.replace('**', '')) + '</strong></p>\n'
needle = '<tr><th scope="row">RQ1'
position = page.index('<div class="table-scroll', page.index('<section id="tien-do"'))
page = page[:position] + claim_html + page[position:]
table_html = ('<div class="table-scroll" tabindex="0"><table><caption>' + html.escape(caption)
    + '</caption><thead><tr>' + ''.join('<th scope="col">' + html.escape(h) + '</th>' for h in headers)
    + '</tr></thead><tbody>')
for row in rows:
    table_html += '<tr><th scope="row">' + row[0] + '</th>'
    table_html += ''.join('<td data-label="' + html.escape(h, quote=True) + '">' + html.escape(v) + '</td>'
                          for h, v in zip(headers[1:], row[1:])) + '</tr>'
table_html += '</tbody></table></div><p class="small">' + html.escape(note) + '</p>'
section_html = ('<section id="chang-13"><div class="label">Chặng 13</div><h2>Đổi nguồn đồ thị khi cơ chế thiếu nền tảng bất hoạt</h2><div class="measure">'
    + ''.join('<p>' + html.escape(p) + '</p>' for p in paragraphs[:-1]) + '</div>' + table_html
    + '<div class="measure"><p>' + html.escape(paragraphs[-1]) + '</p></div></section>\n')
page = page.replace('<section id="con-thieu">', section_html + '<section id="con-thieu">', 1)
old_svgs = re.findall(r'<svg\b.*?</svg>', html_path.read_bytes().decode('utf-8'), flags=re.S)
assert len(old_svgs) == 11 and re.findall(r'<svg\b.*?</svg>', page, flags=re.S) == old_svgs
assert page.count('<table>') == 12 and len(re.findall(r'id="chang-\d+"', page)) == 13
md_path.write_bytes(md.encode('utf-8'))
html_path.write_bytes(page.encode('utf-8'))
write_json(PREP / 'supervisor_learned19_update01.json', dict(
    status='CONTENT_UPDATED_PENDING_VISUAL_QA', before_sha256=expected,
    after_sha256={p.name: sha(p) for p in (md_path, html_path)},
    actual_outer_sha256=sha(OUTER), independent_proof_sha256=sha(PROOF),
    chapter=13, tables=12, unchanged_standalone_svg_count=11,
    numeric_rows=rows, generated_new_scientific_observations=False))
print(json.dumps(dict(status='UPDATED13_PENDING_VISUAL_QA', svg_count=11, table_count=12)))
