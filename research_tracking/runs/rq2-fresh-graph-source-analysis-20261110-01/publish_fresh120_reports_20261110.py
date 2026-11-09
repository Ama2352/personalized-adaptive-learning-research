"""Xuất bản mô tả fresh120 và báo cáo10/11, không thêm thống kê suy luận."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03'
BUNDLE = ROOT/'research_tracking/runs/rq2-fresh-graph-source-analysis-20261110-01'
REPORT = ROOT/'research_tracking/reports/rq2_fresh_graph_source_replication_20261110.md'
OLD = ROOT/'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
NEW = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


q = json.loads((NATIVE/'graph_source_contrasts.json').read_bytes())
k = json.loads((NATIVE/'conditional_lambda_contrasts.json').read_bytes())
pairs = json.loads((NATIVE/'trajectory_pairs.json').read_bytes())
assert len(q) == len(pairs) == 60 and len(k) == 30
assert {r['block'] for r in k} == set(range(21010,21020))
assert all(r['labels_equal_before_first_question_difference'] for r in pairs)
different = sum(r['question_id_differences'] for r in pairs)
assert different == 4936 and all(r['question_id_differences'] > 0 for r in pairs)
groups = {}
for ability in (1000,1150,1300):
    values = [r['lambda_difference'] for r in k if r['ability'] == ability]
    assert len(values) == 10
    for row in k:
        if row['ability'] == ability:
            matches = {r['mechanism_strength']:r['expert_minus_learned'] for r in q
                       if r['block'] == row['block'] and r['ability'] == ability}
            assert row['lambda_difference'] == matches[.55]-matches[0.]
    groups[str(ability)] = dict(mean=statistics.mean(values), minimum=min(values), maximum=max(values),
        positive=sum(v>0 for v in values), negative=sum(v<0 for v in values), zero=sum(v==0 for v in values))
assert groups['1000']['positive'] == 6 and groups['1150']['positive'] == 8
assert groups['1300']['zero'] == 10
assert all(r['expert_minus_learned'] != 0 for r in q if r['ability'] == 1300)
BUNDLE.mkdir(exist_ok=False)
NEW.mkdir(parents=True,exist_ok=False)
sources = [NATIVE/name for name in ('summary.json','graph_source_contrasts.json',
    'conditional_lambda_contrasts.json','trajectory_pairs.json','high_controls.json','prefix_parity.json')]
sources += [PREP/'RQ2_RECOVERY03_DESCRIPTIVE_REVIEW01.md', OLD/'BAO_CAO.md',OLD/'BAO_CAO_NGHIEN_CUU.html']
write(BUNDLE/'inventory_before_copy.json', {p.relative_to(ROOT).as_posix():sha(p) for p in sources})
write(BUNDLE/'descriptive_statistics.json',dict(unit='Elo mean latent net gain, conditional mechanism difference',
    groups=groups, blocks=list(range(21010,21020)), trajectory_question_differences=4936,
    trajectory_positions=7200, trajectory_pairs=60, confidence_intervals=None,p_values=None))
shutil.copyfile(PREP/'RQ2_RECOVERY03_DESCRIPTIVE_REVIEW01.md',BUNDLE/'independent_review.md')
assert sha(BUNDLE/'independent_review.md') == sha(PREP/'RQ2_RECOVERY03_DESCRIPTIVE_REVIEW01.md')
rows = []
for ability, group in groups.items():
    rows.append(f"| {ability} | {group['mean']:+.6f} | {group['minimum']:+.6f} đến {group['maximum']:+.6f} | {group['positive']} / {group['negative']} / {group['zero']} |")
table = '\n'.join(['| Mức khởi tạo | Trung bình | Khoảng quan sát | Số block dương / âm / bằng0 |',
    '|---|---:|---|---|',*rows])
story = '''
## Chặng 15. Kiểm lại đối chứng đồ thị trên mười khối mô phỏng mới

Ba khối trước cho thấy thay đồ thị trong bộ ước lượng có thể đổi đường đi ngay cả khi cơ chế phạt thiếu tiên quyết không hoạt động. Tuy nhiên, ba trường hợp còn ít và dùng lại trạng thái cũ. Nhóm tiếp tục một phép kiểm với mười khối khởi tạo mới đã định trước, giữ cùng trạng thái ban đầu và cùng chuỗi số ngẫu nhiên trong từng cặp so sánh.

Mỗi khối có ba mức khởi tạo1000,1150,1300, hai nguồn đồ thị và hai mức cơ chế phạt. Tổng cộng120ca, mỗi ca120lượt, đã hoàn tất. Đồ thị trong môi trường và bộ chọn bài giữ nguyên. Chỉ nguồn đồ thị trong bộ ước lượng thay giữa đồ thị chuyên gia và một đồ thị31cạnh được ước lượng từ dữ liệu huấn luyện. Hai đường tín hiệu và điều chỉnh theo cha cùng bật, điều chỉnh cục bộ tắt. Đây là một đồ thị học được cố định, chưa đại diện cho mọi đồ thị học từ dữ liệu.

Để biết chênh lệch giữa hai đồ thị có thực sự đi qua cơ chế phạt hay không, trước hết lấy mức tăng kiến thức trung bình của đồ thị chuyên gia trừ đồ thị học được. Sau đó đối chiếu chênh lệch này giữa lúc bật và lúc tắt cơ chế phạt. Đại lượng thu được diễn tả phần thay đổi của chênh lệch khi cơ chế được bật, theo thang Elo của simulator.

TABLE

Ở mức1000 và1150, phần thay đổi có cả dấu dương lẫn âm giữa các khối. Trung bình dương vẫn cần được đọc cùng những trường hợp âm và độ phân tán. Đây là thống kê mô tả trên mười khối, chưa có kiểm định hoặc khoảng tin cậy để kết luận ưu thế ổn định.

Ở mức1300, phần thay đổi bằng0 trong cả mười khối. Đây là đối chứng bất hoạt đã được dự kiến từ điều kiện của simulator. Đồng thời, chênh lệch trực tiếp giữa hai đồ thị vẫn khác0 và có cả hai dấu. Vì vậy, khác biệt do đổi nguồn đồ thị còn có thể đi qua các đường khác ngoài riêng cơ chế phạt thiếu tiên quyết. Kết quả chưa tách riêng vai trò của tín hiệu đồ thị, điều chỉnh theo cha và mức thử thách của câu được chọn.

Cả60cặp so sánh đổi chuỗi câu hỏi, với4936/7200vị trí khác câu. Sau khi đường đi phân kỳ, cùng số thứ tự không bảo đảm cùng câu và cùng lịch sử, nên chưa dùng những vị trí này để so sai số dự báo trên cùng targets.

Phép kiểm mới củng cố chẩn đoán cần tách nguồn đồ thị, năng lực khởi tạo và cơ chế môi trường. Nó cũng cho thấy dấu hiệu ở ba khối cũ chưa đủ để khái quát. Phần còn thiếu là thống kê theo đơn vị khối, khảo sát thêm chất lượng đồ thị và các so sánh chính của mô hình mới. Chưa RQ nào hoàn tất.
'''.replace('TABLE',table)
technical = '''# RQ2 — tái kiểm nguồn đồ thị trên10khối mô phỏng mới

Ngày10/11/2026. Đơn vị so sánh là paired seed block, không120người học độc lập.

## Câu hỏi và thiết kế

Phép kiểm tiếp nối E9 bằng10block21010–21019 mới, ba mức khởi tạo và hai mức lambda0/0,55. Giữ G_env và G_controller expert31, chỉ thay G_estimator expert31/learned31. S=P=True và L=False. Learned artifact/topology giống E9, không có10đồ thị học độc lập.

Y là trung bình trên28concept của theta cuối trừ base ban đầu. Q(a,lambda)=Y_expert−Y_learned. K(a)=Q(a,0,55)−Q(a,0). Đây là controlled simulator interaction contrast. Không thiết kế pre/post DiD trên người học và không có giả định parallel trends cho dữ liệu người thật.

## Kết quả mô tả
''' + story + '''
## Kiểm đầy đủ và khôi phục

Logical120worlds/14400responses gồm parent61 và child59. Physical121constructors/14430responses có30lượt replay. F062 initial snapshot và30dòng observable/oracle khớp chính xác trước khi chạy bước31. Giữ failure parent và không đổi ledger cũ.20highcontrols đầy đủ. Saved10base/U được tái sử dụng, recovery không sinhRNGdraw mới.

## Giới hạn

Mười block chưa xác lập kết luận tổng quát về năng lực. Các lượt thời gian trong một trajectory có tương quan. Một learned artifact và một biến thể GAM chưa chứng minh edge truth, confidence calibration, hiệu quả neural/Junyi hoặc instructional benefit. Không pooling ba block E9 với mười block mới. K1300=0 là negative control được cơ chế dự kiến. Chưa tính CI, p-value hoặc hiệu chỉnh multiple comparisons trong đợt xuất bản này.

## Bằng chứng

[Bundle recovery](../runs/rq2-fresh-graph-recovery-20261110-01/README.md) giữ actual receipts và nguồn. [Bundle phân tích](../runs/rq2-fresh-graph-source-analysis-20261110-01/README.md) giữ dữ liệu mô tả, review độc lập và bản báo cáo. Rawtraces giữ nguyên trong experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03 cùng parent02. Đã kiểm lại đủ60Q,30K,20highcontrols và60trajectory pairs. Các đường dẫn kỹ thuật không đưa vào bản HTML dành cho GVHD.
'''
REPORT.write_text(technical,encoding='utf-8')
md = (OLD/'BAO_CAO.md').read_text(encoding='utf-8')
md = md.replace('# Báo cáo tiến độ khóa luận — 09/11/2026','# Báo cáo tiến độ khóa luận — 10/11/2026',1)
assert md.count('## Còn phải chứng minh') == 1
md = md.replace('## Còn phải chứng minh',story+'\n## Còn phải chứng minh',1)
software = ('Chuẩn bị AKT đã đạt299kiểm hợp đồng và18kiểm checkpoint thật trên CPU theo nguồn hiện hành. '
    'GKT đã đạt11kiểm mô hình và8kiểm trainer trên dữ liệu dựng sẵn. '
    'Các mốc này chưa là so sánh mô hình đã huấn luyện, chưa kiểm public producer resume hoặc CUDA.')
md = md.replace('## Quá trình đã thực hiện',software+'\n\n## Quá trình đã thực hiện',1)
(NEW/'BAO_CAO.md').write_text(md,encoding='utf-8')
html = (OLD/'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
original_svg = re.findall(r'<svg\b.*?</svg>',html,re.S)
html = html.replace('Báo cáo nghiên cứu KLTN — 09/11/2026','Báo cáo nghiên cứu KLTN — 10/11/2026',1)
html = html.replace('Báo cáo tiến độ nghiên cứu · 09/11/2026','Báo cáo tiến độ nghiên cứu · 10/11/2026',1)
html = html.replace('<a href="#con-thieu">','<a href="#chang-14">14. Đối chiếu trạng thái thật</a><a href="#chang-15">15. Kiểm trên mười khối mới</a><a href="#con-thieu">',1)
html_rows = ''.join(f'<tr><th scope="row">{a}</th><td>{g["mean"]:+.6f}<br><span class="small">{g["minimum"]:+.6f} đến {g["maximum"]:+.6f}</span></td><td>{g["positive"]} / {g["negative"]} / {g["zero"]}</td></tr>' for a,g in groups.items())
html_table = '<div class="table-scroll" tabindex="0"><table><caption>Phần thay đổi của chênh lệch đồ thị khi bật cơ chế phạt</caption><thead><tr><th>Mức khởi tạo</th><th>Trung bình và khoảng quan sát</th><th>Số block dương / âm / bằng0</th></tr></thead><tbody>'+html_rows+'</tbody></table></div>'
paras = story.strip().split('\n\n')[1:]
body = ''.join(html_table if p.startswith('| Mức') else '<div class="measure"><p>'+p+'</p></div>' for p in paras)
section = '<section id="chang-15"><div class="label">Chặng15 · Cập nhật10/11</div><h2>Kiểm lại đối chứng đồ thị trên mười khối mô phỏng mới</h2>'+body+'</section>\n'
assert html.count('<section id="con-thieu"') == 1
html = html.replace('<section id="con-thieu"',section+'<section id="con-thieu"',1)
html = html.replace('<section id="chang-1"','<div class="measure"><p>'+software+'</p></div>\n<section id="chang-1"',1)
assert re.findall(r'<svg\b.*?</svg>',html,re.S) == original_svg
assert html.count('<table') == html.count('</table>') == 14
ids = re.findall(r'\bid="([^"]+)"',html)
assert len(ids) == len(set(ids))
(NEW/'BAO_CAO_NGHIEN_CUU.html').write_text(html,encoding='utf-8')
for source in (REPORT,NEW/'BAO_CAO.md',NEW/'BAO_CAO_NGHIEN_CUU.html',Path(__file__).resolve()):
    shutil.copyfile(source,BUNDLE/source.name)
    assert sha(source) == sha(BUNDLE/source.name)
write(BUNDLE/'static_QA.json',dict(svg_preserved=11,tables=14,unique_ids=True,
    descriptive_group_count=3,visual_QA=False,previous_date_reports_unchanged=True))
(BUNDLE/'README.md').write_text('# Phân tích mô tả fresh120 và xuất bản10/11\n\n'
    'Tính lại60Q/30K từ output đã lưu, giữ review độc lập và thống kê mô tả. '
    'Tạo đợt báo cáo10/11 đúng hai file, giữ đợt09/11 và11SVG nguyên văn. '
    'Bảng mới có trung bình/khoảng quan sát/sign counts. Chưa visualQA hoặc thống kê suy luận. '
    'Không thêm model/world calls, không chi cloud.\n',encoding='utf-8')
write(BUNDLE/'manifest.json',dict(kind='descriptive_analysis_and_human_report_publication',
    outputs_sha256={p.relative_to(BUNDLE).as_posix():sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
print('FRESH120_DESCRIPTIVE_AND_TWO_REPORTS_PUBLISHED_STATIC_ONLY')
