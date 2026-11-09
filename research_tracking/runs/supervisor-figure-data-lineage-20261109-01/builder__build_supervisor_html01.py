"""Dựng một HTML nghiên cứu từ số liệu đóng băng; ROOT chạy sau review.

Chỉ stdlib, không exec cell/notebook, không đọc raw learners/checkpoints,
không cài đặt, simulator, model hoặc network. Output mới/exclusive.
"""
from pathlib import Path
import ast
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
PACKET = ROOT / 'research_tracking/supervisor_reports/2026-11-08/01_tien_do'
NOTEBOOK = PREP / 'supervisor_notebook_before_html01.ipynb'
SUMMARY_BEFORE = PREP / 'supervisor_summary_before_html01.md'
TARGET = PACKET / 'BAO_CAO_NGHIEN_CUU.html'
RECEIPT = PREP / 'supervisor_html01_build_receipt.json'
NOTEBOOK_SHA = 'd7a7cbd61b242bf1434a19fbb0e24b28ec466bd317c41f90a31204bef53ae506'
SUMMARY_SHA = '065c946376b5cc30f6cc9464098e1421a69ea59f489423d953fa378d9d5bb23e'
BASELINE = 'docs/bkt-gam-kt-benchmark.md'
BASELINE_SHA = 'b67c7d02a28200adee8617896aa377032581caf88875cf015a4bc965912df4eb'
EXPOSURE = 'research_tracking/runs/rq1-ready-set-exposure-20261108-01/summary.json'
EXPOSURE_SHA = '730b7b572213179a2d6db49190494569c478d753b057d5a147abf863de3e9846'
EXPOSURE_VALID = EXPOSURE.replace('summary.json', 'validation.json')
EXPOSURE_VALID_SHA = '8dd1b576b1a9894664970e7199cf09c0dafc090edd2e16dec764eb14215d7a21'
EXPOSURE_REPORT = 'research_tracking/reports/rq1_ready_set_exposure_results_20261108.md'
EXPOSURE_REPORT_SHA = '583535d1e9a8d0ccaf57bd77f6485345fbfd85b54b559148ddde2a1b9fe035b4'
EXPOSURE_MANIFEST = 'research_tracking/runs/rq1-ready-set-exposure-20261108-01/manifest.json'
EXPOSURE_MANIFEST_SHA = '8dc2104b09dd961500afb51ecf454772253ad64e2dc8f18a7acb6ab2bf08d3f7'
e = html.escape


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def read_pinned(relative, expected, inventory):
    path = ROOT / relative
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('Nguồn đã thay đổi: ' + relative)
    inventory[relative] = dict(sha256=expected, bytes=len(raw))
    return raw


def resolve(value, pointer):
    for part in pointer.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def link(path, label):
    # Chỉ các nguồn repository đã biết; không tải nội dung qua link.
    if path.startswith('/') or '..' in Path(path).parts or ':' in path or '\\' in path:
        raise ValueError('Nguồn phải là đường dẫn repository tương đối')
    return '<a href="../../../../' + e(path, quote=True) + '">' + e(label) + '</a>'


def table(caption, headers, rows, *, class_name=''):
    return ('<div class="table-scroll ' + class_name + '" tabindex="0"><table><caption>' + e(caption) +
        '</caption><thead><tr>' + ''.join('<th scope="col">' + e(str(x)) + '</th>' for x in headers) +
        '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<' + ('th scope="row"' if i == 0 else 'td') + '>' +
        e(str(x)) + '</' + ('th' if i == 0 else 'td') + '>' for i, x in enumerate(row)) + '</tr>' for row in rows) +
        '</tbody></table></div>')


def number(value, digits=6):
    if isinstance(value, int):
        return f'{value:,}'.replace(',', '.')
    return f'{value:.{digits}f}'.replace('.', ',')


def figure(svg, caption):
    return '<figure><div class="svg-frame">' + svg + '</div><figcaption>' + caption + '</figcaption></figure>'


def notebook_svg(notebook, cell, label):
    candidates = [o['data']['image/svg+xml'] for o in notebook['cells'][cell].get('outputs', [])
                  if 'image/svg+xml' in o.get('data', {})]
    if len(candidates) != 1:
        raise ValueError('Cần đúng một SVG đã lưu tại cell ' + str(cell))
    raw = candidates[0]
    raw = ''.join(raw) if isinstance(raw, list) else raw
    node = ET.fromstring(raw)
    allowed = {'svg', 'title', 'desc', 'g', 'rect', 'text', 'tspan', 'line', 'path', 'circle',
               'polyline', 'polygon', 'defs', 'marker', 'ellipse'}
    for item in node.iter():
        if item.tag.split('}')[-1] not in allowed:
            raise ValueError('SVG không thuộc allowlist tĩnh')
        for key, value in item.attrib.items():
            if key.lower().startswith('on') or 'href' in key.lower() or 'url(' in value.lower():
                raise ValueError('SVG có nội dung ngoài/hành vi')
    # Chỉ biên tập nhãn trình bày; geometry và toàn bộ số giữ nguyên.
    human_labels = {
        'ΔLog Loss: pooled và từng profile': 'Chênh lệch Log Loss: gộp và từng hồ sơ',
        'pooled (n=1080)': 'Gộp (n=1080)',
        'profile:PG (n=360)': 'PG (n=360)', 'profile:PY (n=360)': 'PY (n=360)',
        'profile:PYH (n=360)': 'PYH (n=360)',
        'ΔLog Loss graph theo available history — tách từng targetH': 'Chênh lệch Log Loss theo lượng lịch sử; tách từng thời điểm cần dự báo',
        'Counterexample controller: A → B → A': 'Phản ví dụ của quy tắc chọn bài: A → B → A',
        'Soft-mastery gain: phản ví dụ readout, không trajectory': 'Thay đổi điểm thành thạo mềm ở hai trạng thái dựng sẵn',
        'Ψ theo ability: cả3block, đơn vị Elo net trung bình28concepts': 'Tương tác đồ thị và mức phạt: cả 3 khối seed, gain ròng thang Elo',
        'Junyi controls: thay cạnh không đồng nghĩa có exposure': 'Junyi: thay cạnh chưa bảo đảm người học đã quan sát cả hai đầu',
        'Control0':'Đối chứng 0', 'Control1':'Đối chứng 1', 'Control2':'Đối chứng 2',
    }
    human_labels.update({'nats/target — âm: metric full thấp hơn; dương: metric full cao hơn.': 'Log Loss trung bình: âm nghĩa đủ cạnh thấp hơn; dương nghĩa đủ cạnh cao hơn.', 'H=10, n=9/cell': 'H=10, n=9/nhóm', 'H=50, n=9/cell': 'H=50, n=9/nhóm', 'H=100, n=9/cell': 'H=100, n=9/nhóm', 'Đơn vị nats/target; cùng y-scale. Không nối cácH khác target. Không đường CI/p-value.': 'Cùng thang Log Loss. Mỗi H là một tập câu hỏi riêng; không nối thành đường học.', 'A1 / chươngA': 'A1 / chương A', 'B1 / chươngB': 'B1 / chương B', 'A2 / chươngA (re-entry)': 'A2 / chương A (quay lại)', 'Cảhai selectors córoute này trong constructed test; không là ước lượng xác suất re-entry.': 'Cả hai quy tắc tạo lộ trình này trong kịch bản dựng sẵn; không đo tần suất quay lại.', 'T+14ngày': 'T + 14 ngày', 'Đơn vị probability/readout points; hai endpoints, không ước lượng đường học hoặc CI.': 'Điểm thành thạo mềm tại hai thời điểm; không phải quỹ đạo học đo được.', 'Block21000': 'Khối 21000', 'Block21001': 'Khối 21001', 'Block21002': 'Khối 21002', 'Vị trí x lệch nhẹ chỉ để thấy điểm trùng; không jitter dữ liệu hoặc precision claim.': 'Các điểm lệch ngang để nhìn thấy khi trùng nhau; không thay giá trị dữ liệu.', 'Đây là coverage diagnostic, không xác suất prerequisite đúng hoặc effectsize dạy học.': 'Đo độ phủ của thay đổi, không đo xác suất cạnh đúng hoặc lợi ích giảng dạy.'})
    for item in node.iter():
        if item.text in human_labels:
            item.text = human_labels[item.text]
    # Nhãn là phần trình bày: giữ nguyên vị trí/giá trị thanh và điểm dữ liệu.
    if cell == 5:
        for item in node.iter():
            if item.tag.endswith('text') and re.fullmatch(r'[+-]?\d+\.\d+', item.text or ''):
                item.set('x', '895')
                item.set('text-anchor', 'end')
    if cell == 16:
        zeros = 0
        for item in node.iter():
            if not item.tag.endswith('text'):
                continue
            if item.text == '+0.00756099':
                item.attrib.update(x='180', y='134', **{'text-anchor':'end', 'fill':'#126f85'})
            elif item.text == '+0.0206209':
                item.attrib.update(x='228', y='88', **{'text-anchor':'start', 'fill':'#70519b'})
            elif item.text == '+0':
                x,y,anchor,color = (('720','116','end','#126f85'),
                    ('760','95','middle','#a73539'),('800','116','start','#70519b'))[zeros]
                item.attrib.update(x=x,y=y,**{'text-anchor':anchor,'fill':color})
                zeros += 1
        if zeros != 3:
            raise ValueError('Cần giữ đủ ba nhãn zero của ba khối')
    node.set('role', 'img')
    node.set('aria-label', label)
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(node, encoding='unicode'), digest(raw.encode())


def system_diagram():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 230" role="img" aria-labelledby="system-title system-desc">
<title id="system-title">Ba thành phần của hệ thống học tập thích ứng</title>
<desc id="system-desc">Mô hình ước lượng từ bài làm; đồ thị mô tả quan hệ kiến thức nền; quy tắc chọn bài kết hợp thông tin để đề xuất hoạt động. Sơ đồ thành phần, không mô hình nhân quả đã được chứng minh.</desc>
<rect x="16" y="20" width="286" height="160" rx="5" fill="#f1f6fa" stroke="#a9becd"/>
<rect x="337" y="20" width="286" height="160" rx="5" fill="#f1f6fa" stroke="#a9becd"/>
<rect x="658" y="20" width="286" height="160" rx="5" fill="#eaf5f5" stroke="#087d86"/>
<g font-family="Segoe UI,Arial,sans-serif" text-anchor="middle" fill="#17324d">
<text x="159" y="62" font-size="22" font-weight="600">Ước lượng người học</text>
<text x="159" y="101" font-size="17">Từ lịch sử bài làm</text><text x="159" y="130" font-size="17">Dự báo và trạng thái ước lượng</text>
<text x="480" y="62" font-size="22" font-weight="600">Quan hệ tiên quyết</text>
<text x="480" y="101" font-size="17">Kiến thức nền cần có</text><text x="480" y="130" font-size="17">Ràng buộc các nội dung có thể học</text>
<text x="801" y="62" font-size="22" font-weight="600">Quy tắc chọn bài</text>
<text x="801" y="101" font-size="17">Kết hợp trạng thái và ràng buộc</text><text x="801" y="130" font-size="17">Chọn hoạt động tiếp theo</text>
<text x="480" y="215" font-size="17">Đánh giá riêng: dự báo · quyết định · kết quả học trong mô phỏng</text></g></svg>'''


def exposure_diagram(pooled):
    roots = pooled['served_roots']; total = pooled['events']; nonroots = total - roots
    exceptions = pooled['served_classes']['exposure_exception']
    strict = pooled['served_classes']['strict_mastery'] - roots
    if (total, roots, nonroots, exceptions, strict) != (3240, 500, 2740, 2041, 699):
        raise ValueError('Exposure không khớp kết quả đã review')
    w = 780 * exceptions / nonroots
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 250" role="img" aria-labelledby="exposure-title exposure-desc">
<title id="exposure-title">Điều kiện cho phép chọn trong 2740 lượt phục vụ khái niệm có tiên quyết</title>
<desc id="exposure-desc">2041 lượt qua ngoại lệ đã tiếp xúc đủ,699 lượt mọi kiến thức nền được mô hình đánh dấu thành thạo.500 lượt khái niệm gốc tách riêng; tổng3240 lượt đều ở nhánh frontier và trong tập ready trả về.</desc>
<g font-family="Segoe UI,Arial,sans-serif" fill="#17324d"><text x="40" y="38" font-size="21" font-weight="600">Trong 2.740 lượt chọn khái niệm có tiên quyết</text>
<rect x="40" y="70" width="{w:.3f}" height="50" fill="#087d86"/><rect x="{40+w:.3f}" y="70" width="{780-w:.3f}" height="50" fill="#346fa0"/>
<text x="{40+w/2:.3f}" y="103" fill="white" text-anchor="middle" font-size="21" font-weight="600">2.041</text><text x="{40+w+(780-w)/2:.3f}" y="103" fill="white" text-anchor="middle" font-size="21" font-weight="600">699</text><text x="40" y="155" font-size="19">2.041 / 2.740: qua ngoại lệ đã tiếp xúc đủ</text>
<text x="40" y="186" font-size="19">699 / 2.740: mọi kiến thức nền đã được đánh dấu thành thạo</text>
<text x="40" y="223" font-size="17">Tách riêng 500 lượt khái niệm gốc; tổng 3.240 lượt đều thuộc tập cho phép.</text></g></svg>'''


CSS = '''
:root{--navy:#17324d;--petrol:#087d86;--blue:#346fa0;--ink:#243747;--muted:#617484;--pale:#f1f6fa;--line:#cbd9e2}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:1rem}body{margin:0;background:white;color:var(--ink);font:18px/1.72 Cambria,Georgia,serif}
a{color:#155c88;text-decoration-thickness:1px;text-underline-offset:3px}a:hover{color:var(--petrol)}a:focus-visible,summary:focus-visible,.table-scroll:focus-visible{outline:3px solid var(--petrol);outline-offset:4px}
.skip{position:absolute;top:-80px;left:1rem;background:white;padding:.5rem}.skip:focus{top:0;z-index:3}.page{max-width:1160px;margin:auto;padding:3rem 40px 5rem}.measure{max-width:760px}.masthead{border-top:7px solid var(--navy);padding-top:2.1rem}h1,h2,h3{color:var(--navy);font-weight:600;line-height:1.2}h1{font-size:clamp(2.2rem,4.1vw,3.65rem);max-width:1000px;margin:.7rem 0 1.3rem;letter-spacing:-.025em}h2{font-size:2.05rem;margin:0 0 1.2rem}h3{font-size:1.46rem;margin:2rem 0 .8rem}p{margin:.85rem 0 1.2rem}p.lead{font-size:1.3rem;line-height:1.58;max-width:820px}.byline,.label,.small,figcaption,table,nav,summary,footer,.sources{font-family:'Segoe UI',Arial,sans-serif}.byline{color:var(--muted);font-size:.93rem;line-height:1.7}.byline strong{color:var(--navy)}nav{display:flex;flex-wrap:wrap;gap:.6rem 1.3rem;border-block:1px solid var(--line);margin:2rem 0 2.8rem;padding:1rem 0;font-size:.98rem}nav a{text-decoration:none}section{margin-top:3.8rem;padding-top:2.2rem;border-top:2px solid var(--line)}section.opening{margin-top:0;padding-top:0;border:0}.label{color:var(--petrol);font-size:1rem;font-weight:650;margin-bottom:.5rem}.finding{max-width:850px;border-left:4px solid var(--petrol);padding:.4rem 0 .4rem 1.4rem;margin:1.6rem 0;font-size:1.16rem;line-height:1.6}.limits{max-width:850px;background:var(--pale);padding:1rem 1.3rem;margin:1.6rem 0;border-left:3px solid #a8bfce}.limits p:last-child{margin-bottom:0}.limits strong{color:var(--navy)}.compare{display:grid;grid-template-columns:1fr 1fr;gap:2rem;margin:1.5rem 0}.compare article{border-top:3px solid var(--blue);padding-top:.3rem}.compare article h3{margin:1rem 0}.table-scroll{overflow-x:auto;margin:1.6rem 0 2rem}table{width:100%;border-collapse:collapse;font-size:.93rem;line-height:1.55;font-variant-numeric:tabular-nums;text-align:left}caption{text-align:left;font-size:1rem;color:var(--navy);font-weight:600;margin-bottom:.75rem}th,td{padding:.7rem .85rem;border-bottom:1px solid var(--line);vertical-align:top}thead th{background:var(--pale);border-top:1px solid var(--line);color:var(--navy)}tbody th{font-weight:600}tbody tr:nth-child(even){background:#fafcfd}figure{margin:2rem 0 2.4rem}.svg-frame{overflow:auto;border-block:1px solid #dfE8ee;padding:.8rem 0}.svg-frame svg{display:block;width:100%;height:auto;min-width:620px}figcaption{font-size:.95rem;line-height:1.65;color:#435b6e;margin:.8rem 0;max-width:950px}.small{font-size:.93rem;line-height:1.65;color:var(--muted)}details{border-top:1px solid var(--line);padding:1rem 0;margin:1rem 0}summary{cursor:pointer;color:var(--navy);font-weight:600}.methods{max-width:850px}ul,ol{padding-left:1.4rem}li{margin:.5rem 0}.sources{font-size:.91rem;line-height:1.65}.sources li{margin:.8rem 0}footer{margin-top:3rem;border-top:1px solid var(--line);padding-top:1rem;font-size:.9rem;color:var(--muted)}
@media(max-width:700px){.page{padding:1.5rem 20px 3rem}body{font-size:17px}.compare{grid-template-columns:1fr;gap:.5rem}h2{font-size:1.75rem}section{margin-top:2.5rem}.finding{padding-left:1rem}th,td{padding:.6rem .65rem;min-width:100px}nav{gap:.7rem 1rem}.svg-frame{margin-inline:-5px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{@page{size:A4;margin:17mm}body{font-size:11pt;line-height:1.5}.page{max-width:none;padding:0}nav,.skip,.full-inventory{display:none}.masthead{padding-top:1rem}h1{font-size:28pt}h2{font-size:20pt}h3{font-size:15pt}section{margin-top:1.5rem;padding-top:1rem}figure,.finding,.limits{break-inside:avoid}.svg-frame{overflow:visible}.svg-frame svg{min-width:0}table{font-size:9pt}thead{display:table-header-group}.table-scroll{overflow:visible}a{color:var(--navy);text-decoration:none}.compare{display:block}.compare article{break-inside:avoid}p{orphans:3;widows:3}details{break-inside:avoid}details>*:not(summary){display:block!important}footer{font-size:9pt}}
'''


def build():
    if TARGET.exists() or RECEIPT.exists():
        raise FileExistsError('HTML/receipt đã có; không tự ghi đè')
    inventory = {}
    notebook_raw = read_pinned(NOTEBOOK.relative_to(ROOT).as_posix(), NOTEBOOK_SHA, inventory)
    # Historical snapshot để trace, không đọc mutable summary làm numeric input.
    read_pinned(SUMMARY_BEFORE.relative_to(ROOT).as_posix(), SUMMARY_SHA, inventory)
    baseline_raw = read_pinned(BASELINE, BASELINE_SHA, inventory)
    exposure = json.loads(read_pinned(EXPOSURE, EXPOSURE_SHA, inventory))
    validation = json.loads(read_pinned(EXPOSURE_VALID, EXPOSURE_VALID_SHA, inventory))
    read_pinned(EXPOSURE_REPORT, EXPOSURE_REPORT_SHA, inventory)
    exposure_manifest = json.loads(read_pinned(EXPOSURE_MANIFEST, EXPOSURE_MANIFEST_SHA, inventory))
    if (exposure_manifest['outputs_sha256']['summary.json'] != EXPOSURE_SHA
            or exposure_manifest['outputs_sha256']['validation.json'] != EXPOSURE_VALID_SHA):
        raise ValueError('Exposure selected outputs không khớp closed manifest')
    notebook = json.loads(notebook_raw)
    assignments = ast.parse(''.join(notebook['cells'][1]['source'])).body
    values = {n.targets[0].id: ast.literal_eval(n.value) for n in assignments
              if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id in ('EMBEDDED_JSON', 'EXPECTED_EMBEDDED_SHA256')}
    if digest(values['EMBEDDED_JSON'].encode()) != values['EXPECTED_EMBEDDED_SHA256']:
        raise ValueError('Embedded JSON không khớp SHA')
    evidence = json.loads(values['EMBEDDED_JSON'])
    if len(evidence['records']) != 58 or len(evidence['source_inventory']) != 73:
        raise ValueError('Không đúng frozen evidence population')
    for path, item in evidence['source_inventory'].items():
        read_pinned(path, item['sha256'], inventory)
    cache = {}
    for record in evidence['records']:
        path = record['source_path']
        cache.setdefault(path, json.loads((ROOT / path).read_bytes()))
        if resolve(cache[path], record['json_pointer']) != record['value']:
            raise ValueError('Numeric slice thay đổi: ' + record['id'])
    data = {r['id']: r['value'] for r in evidence['records']}
    if validation['status'] != 'ALL3240_SOURCE_READY_SETS_ORDER_EXACT' or validation['rows'] != 3240:
        raise ValueError('Exposure validation không đúng')
    pooled = next(g for g in exposure['groups'] if g['group'] == 'pooled')
    if (pooled['ready_branches']['frontier'] != 3240 or pooled['served_outside_returned_ready'] != 0
            or exposure['new_independent_N'] != 0):
        raise ValueError('Exposure population/semantics mismatch')
    baseline = []
    baseline_section = baseline_raw.decode().split('## Kết quả common-row', 1)[1].split('## Paired cluster bootstrap', 1)[0]
    for line in baseline_section.splitlines():
        if re.match(r'^\| (AUC|Log Loss|Brier|ECE|Accuracy) \|', line):
            baseline.append([v.strip() for v in line.split('|')[1:-1]])
    if len(baseline) != 5 or '20,706,014' not in baseline_raw.decode():
        raise ValueError('Không tìm đúng historical common-row metrics')
    svg = {}; svg_hashes = {}
    for cell, name, label in [(5,'fixed','Chênh lệch dự báo full–empty theo hồ sơ người học'),
        (8,'history','Tác động theo lượng lịch sử trong cùng cached target'),
        (11,'chapter','Phản ví dụ lộ trình A–B–A trên revision selector hiện có'),
        (13,'retention','Soft-mastery gain ở hai trạng thái dựng sẵn'),
        (16,'ability','Tương tác đồ thị và penalty tiên quyết trong ba block'),
        (20,'junyi','Mức co-observation của các cạnh Junyi đã thay đổi')]:
        svg[name], svg_hashes[name] = notebook_svg(notebook, cell, label)
    fixed = data['fixed_groups']; main = [r for r in fixed if r['group']=='pooled' or r['group'].startswith('profile:')]
    p = fixed[0]
    if p['P_changed'] != 963 or p['P_preview_table'][2]['count'] != 943:
        raise ValueError('Sai full–empty contrast')
    metric_purpose = table('Đánh giá dự báo: mỗi thước đo trả lời một câu hỏi khác nhau',
        ['Thước đo','Câu hỏi','Chiều tốt hơn / giới hạn'],[
        ('AUC','Mô hình có xếp câu trả lời đúng cao hơn câu sai không?','Cao hơn; không kiểm trực tiếp mức tự tin.'),
        ('Log Loss','Xác suất có phù hợp đáp án quan sát không?','Thấp hơn; phạt mạnh khi sai mà quá tự tin.'),
        ('Brier','Xác suất cách nhãn đúng bao xa theo sai số bình phương?','Thấp hơn; dùng toàn giá trị xác suất.'),
        ('ECE, 15 khoảng','Trong từng khoảng xác suất, tỷ lệ đúng thực tế có khớp không?','Thấp hơn; phụ thuộc cách chia khoảng, không là thành thạo tiềm ẩn.'),
        ('Accuracy, ngưỡng 0,5','Bao nhiêu dự báo đúng khi chuyển xác suất thành đúng/sai?','Cao hơn; chịu ảnh hưởng tỷ lệ nhãn, bỏ qua mức tự tin.')])
    baseline_table = table('Junyi Development lịch sử: trung bình 5 fold ± độ lệch chuẩn mẫu',
        ['Thước đo','BKT','GAM-KT','GAM-KT − BKT'], baseline)
    fixed_table = table('Cùng 1.080 câu hỏi/nhãn: đủ cạnh so với tập cạnh rỗng, cùng các cơ chế đi kèm',
        ['Nhóm','Số tình huống','ΔLog Loss','ΔBrier','Đề xuất thử đổi'],
        [(r['group'].replace('pooled','Gộp').replace('profile:',''),number(r['paired_snapshot_targets']),
          number(r['LL_full_minus_empty']),number(r['Brier_full_minus_empty']),r['full_preview_tuple_changed']) for r in main])
    flags_table = table('Các đầu ra song song; không phải các bước lọt qua một phễu',
        ['Đầu ra được so','Số tình huống thay đổi','Mẫu số'],[
        ('Xác suất của câu hỏi đang xét',p['P_changed'],1080),('Quyết định thành thạo',p['M_event_changed'],1080),
        ('Tập khái niệm được phép chọn',p['R_event_changed'],1080),('Đề xuất thử đầy đủ',p['full_preview_tuple_changed'],1080)])
    role_table = table('Corpus mô phỏng Development đã chuẩn bị; chưa phải kết quả mô hình',
        ['Vai trò','Người học mô phỏng','Tương tác','Bài tập được quan sát'],
        [(dict(train='Huấn luyện',selection='Chọn số vòng học',calibration='Hiệu chỉnh xác suất')[role],
          r['learners'],number(r['events']),r['covered_items']) for role in ('train','selection','calibration') for r in [data['corpus_roles'][role]]])
    chunks = [f'''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<meta name="description" content="Báo cáo tiến độ nghiên cứu KLTN: từ hai nghiên cứu trước đến chẩn đoán RQ1–RQ2 và nền dữ liệu cho CG-AKT.">
<title>Báo cáo nghiên cứu KLTN — 08/11/2026</title><style>{CSS}</style></head><body>
<a class="skip" href="#noi-dung">Đến nội dung</a><main class="page" id="noi-dung">
<header class="masthead"><div class="byline">Báo cáo tiến độ nghiên cứu · 08/11/2026</div>
<h1>Khi nào thông tin tiên quyết thực sự giúp chọn bài và học tốt hơn?</h1>
<p class="lead">Từ hai nghiên cứu đã có, khóa luận tiếp tục tìm nguyên nhân, kiểm tra điều kiện hiệu lực và phát triển cách sử dụng đồ thị theo độ tin cậy.</p>
<p class="byline"><strong>Đề tài:</strong> Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.<br>
<strong>Sinh viên:</strong> Phạm Triều Dương · Hồ Nguyễn Minh Sang<br><strong>GVHD:</strong> TS. Lê Văn Tuấn</p></header>
<nav aria-label="Mục lục"><a href="#boi-canh">Bối cảnh</a><a href="#rq1">RQ1: nguyên nhân</a><a href="#rq2">RQ2: điều kiện</a><a href="#rq3">RQ3: giải pháp</a><a href="#tiep-theo">Phần làm tiếp</a><a href="#nguon">Nguồn và phương pháp</a></nav>
<section id="boi-canh" class="opening"><h2>Từ bản đồ kiến thức đến quyết định học tập</h2>
<div class="measure"><p>Một hệ thống thích ứng phải trả lời: <strong>với những bài người học đã làm, nên giao bài nào tiếp theo?</strong> Hệ thống cần ước lượng người học đang biết gì, xác định kiến thức nền cần có và chọn một hoạt động phù hợp. Đồ thị tiên quyết là bản mô tả các quan hệ kiến thức nền ấy. Có bản đồ tốt chưa bảo đảm chọn bài tốt; một lộ trình liền mạch hơn cũng chưa bảo đảm học được nhiều hơn.</p></div>
{figure(system_diagram(),'Ba thành phần có vai trò khác nhau. Đây là sơ đồ tổ chức hệ thống, không phải chuỗi nhân quả đã được các kết quả bên dưới chứng minh.')}
<div class="compare"><article><h3>Paper 1: đồ thị và cách chọn đường đi</h3><p>Đồ thị giới hạn nội dung được phép chọn; chính sách quyết định nội dung thực sự xuất hiện tiếp theo. Ưu tiên học liên tục trong chương giúp giảm chuyển chương và quay lại chương. Tuy nhiên, đồ thị mở rộng chưa cải thiện ổn định mức thành thạo so với đồ thị nội chương.</p></article>
<article><h3>Paper 2: dự báo và kết quả học</h3><p>Phần bổ sung có đồ thị cải thiện nhẹ dự báo ở một số nhóm mô phỏng, nhưng chưa phát hiện cải thiện rõ ở hai kết quả học tập chính sau hiệu chỉnh thống kê. Bước chọn cấu hình trên Junyi ưu tiên tắt các cơ chế đồ thị đã thử. Paper cũng thừa nhận phép so sánh còn gộp nhiều cơ chế ngoài riêng các cạnh.</p></article></div>
<div class="measure"><p>Khóa luận kế thừa những nhận định này. Phần tiếp nối là xác định <strong>điều gì xảy ra giữa dự báo và lựa chọn</strong>, tìm <strong>điều kiện làm tác động thay đổi</strong>, rồi kiểm chứng <strong>cơ chế dùng đồ thị thận trọng hơn</strong>. Ba RQ sau giữ phạm vi của đề cương; không trùng hệ đánh số RQ riêng trong hai paper.</p></div>
<div class="limits"><strong>Phạm vi bằng chứng.</strong> Kết quả hiện có gồm chẩn đoán nguồn, phân tích dữ liệu đã lưu và các đối chứng hữu hạn trong mô phỏng. Chưa RQ nào hoàn tất; chưa có cơ sở khẳng định hiệu quả giáo dục trên học sinh thật hoặc ưu thế nghiên cứu của CG-AKT.</div></section>
<section id="rq1"><div class="label">RQ1 · Nguyên nhân</div><h2>Vì sao dự báo thay đổi nhưng đề xuất có thể giữ nguyên?</h2>
<div class="measure"><p>Hai paper để lại khoảng cách giữa “ước lượng tốt hơn” và “chọn bài tốt hơn”. Nếu dự báo đổi quá ít để làm thay nhận định thành thạo, tập nội dung được phép học có thể giữ nguyên. Ngay cả khi tập đó đổi, quy tắc chọn bài vẫn có thể đưa ra cùng đề xuất. Vì vậy cần quan sát từng đầu ra riêng, đồng thời đo chất lượng dự báo bằng các thước đo chuẩn.</p><p>Một thước đo dự báo kiểm tra xác suất đúng so với đáp án quan sát. Nó không trực tiếp cho biết người học đã học thêm bao nhiêu; mức thành thạo ước lượng, đề xuất thử và kết quả học phải được đánh giá riêng.</p></div>
{metric_purpose}
<h3>Mốc dự báo đã có: BKT và GAM-KT trên Junyi</h3><div class="measure"><p>Bảng lịch sử sau cho biết các mô hình tham chiếu đã dự báo đến đâu trên dữ liệu thực. Hai hệ thống được đối chiếu trên <strong>20.706.014 dòng có dự đoán từ mô hình đã huấn luyện ở cả hai bên</strong>, trong 20.706.208 dòng Development ghép được. Có 194 dòng không có dự đoán như vậy ở cả hai; chúng được giữ trong kiểm tra độ phủ và loại khỏi bảng chất lượng dự báo chung.</p></div>
{baseline_table}
<p class="small">Nguồn: đối chiếu BKT–GAM-KT trên các tương tác Development chung. Trung bình 5 fold ± độ lệch chuẩn mẫu, không phải khoảng tin cậy 95%. ECE dùng 15 khoảng đều; Accuracy dùng p≥0,5; đây là ngưỡng dự báo đáp án, không phải ngưỡng thành thạo. Paper 2 dùng ECE với 10 khoảng trong một thiết kế khác. Bảng này không cùng quần thể với mô phỏng và không chứa CG-AKT.</p>
<div class="measure"><p>BKT tốt hơn trên cả năm thước đo trong từng fold của phép đối chiếu này. Đây là mốc dự báo lịch sử, không chứng minh BKT chọn bài tốt hơn hoặc phù hợp mọi quần thể. Các thí nghiệm hiện tại đi tiếp bằng cách hỏi sự khác nhau ở đầu ra có dẫn tới khác lựa chọn hay không.</p></div>
<h3>Giữ đầu vào để tách phần do quan hệ tiên quyết</h3><div class="measure"><p>Trên Graph-GAM-KT kế thừa từ Paper 2, nhóm so phương án nhận đủ cạnh với phương án nhận tập cạnh rỗng, trong khi vẫn bật cùng các cơ chế đi kèm. Câu hỏi, đáp án, lịch sử, tham số và trạng thái ban đầu giống nhau; bản đồ của môi trường và phần chọn bài giữ nguyên. Đây là bước tách mà phép bật/tắt cả package của Paper 2 chưa thực hiện.</p><p>Log Loss/Brier thấp hơn nghĩa là phù hợp đáp án hơn theo thước đo đó. Chênh lệch âm bên dưới thuận cho cấu hình đủ cạnh; chưa phải tiến bộ học tập.</p></div>
{fixed_table}
<p class="small">PG: mạnh đều; PY: yếu đều; PYH: yếu ở một số nội dung hàm số. Đây là ba hồ sơ mô phỏng, không phải nhóm học sinh thực được lấy mẫu.</p>
{figure(svg['fixed'],'Chênh lệch full–empty trên cùng targets. Kết quả gộp nhỏ và thuận full, nhưng cả ba quỹ đạo PG cho chiều bất lợi; không dùng trung bình gộp để xóa trường hợp âm.')}
<div class="finding"><strong>Trong 963 tình huống xác suất đổi, 943 vẫn giữ đề xuất khái niệm xem trước.</strong> Tổng cộng 22/1.080 đề xuất thử đầy đủ thay đổi. Dự báo và đề xuất không có quan hệ đổi một–một trong các tình huống này.</div>
{flags_table}
<div class="limits"><p><strong>Diễn giải đúng.</strong> Mỗi hàng có cùng mẫu số 1.080 cặp trạng thái, không phải số còn lại sau hàng trước. Xác suất là của câu hỏi đang xét; không đại diện toàn bộ 28 điểm trạng thái. Đề xuất được thăm dò trên bản sao trạng thái, chưa phải bài đã phục vụ. Ba khối seed được dùng lại qua ba hồ sơ mô phỏng; 1.080 dòng không là 1.080 người học độc lập.</p><p>Chưa xác định đầy đủ nguyên nhân nằm ở mức tự tin, quyết định thành thạo hay quy tắc chọn bài. Các số đếm không tạo thành chuỗi nguyên nhân đã được chứng minh, cũng không chứng minh mức thành thạo đã hiệu chuẩn hoặc lợi ích học tập.</p></div>
<h3>Tập “được phép chọn” thực sự có nghĩa gì?</h3><div class="measure"><p>Trước khi quy khác biệt cho ngưỡng thành thạo, cần kiểm đúng quy tắc của controller. Paper 2 cho phép học một khái niệm khi mọi kiến thức nền đã được đánh dấu thành thạo, <em>hoặc</em> khi từng kiến thức nền chưa thành thạo đã được chọn ít nhất sáu lần trước đó. Vì thế, “được phép chọn” không đồng nghĩa “mọi kiến thức nền đã thành thạo”.</p><p>Phân tích mới đối chiếu tập cho phép và bài đã phục vụ trên các vết chạy đã lưu. Khái niệm gốc được tách riêng vì không có cha; không đưa chúng vào mẫu số khi hỏi điều kiện tiên quyết của khái niệm có tiên quyết.</p></div>
{figure(exposure_diagram(pooled),'Đơn vị là lượt phục vụ theo từng phiên bản: 3.240 lượt thuộc 27 quỹ đạo, dùng lại 3 khối seed. Có 500 lượt khái niệm gốc; trong 2.740 lượt khái niệm có tiên quyết, 2.041 qua ngoại lệ đã tiếp xúc đủ và 699 thỏa mọi kiến thức nền thành thạo. Toàn bộ 3.240 lượt thuộc nhánh tập nội dung khả dụng thông thường và không lượt nào ngoài tập được phép trả về.')}
<div class="measure"><p><strong>Ý nghĩa:</strong> đây là một cơ chế cụ thể cần xét khi giải thích quyết định. Việc một kiến thức nền chưa được đánh dấu thành thạo không tự động chứng minh lựa chọn vi phạm quy tắc, bởi chính controller cho phép ngoại lệ. Kết quả không chứng minh ngoại lệ tốt hoặc xấu cho việc học, cũng chưa đo tác động của việc loại bỏ nó.</p></div>
<div class="limits"><strong>Giới hạn:</strong> phân tích hậu nghiệm trên vết chạy của phiên bản mã hiện có; không tạo thêm seed độc lập. 2.041 là số lượt, không phải số người học hoặc số cạnh sai. Không ghép các lịch sử đã phân kỳ thành cùng đầu vào và không biến giải thích nguồn thành kết luận nhân quả.</div></section>
<section id="rq2"><div class="label">RQ2 · Điều kiện hiệu lực</div><h2>Khi nào đồ thị hữu ích, trung tính hoặc bất lợi?</h2><div class="measure"><p>Kết quả chưa tích cực trong hai paper không đủ kết luận đồ thị vô ích ở mọi trường hợp. Quan hệ kiến thức nền có thể tác động khác khi hệ thống biết ít về người học, khi năng lực đã cao hoặc khi đồ thị chỉ khớp thứ tự luyện đã ghi. Các nhánh sau kiểm từng điều kiện và cả nguy cơ phép đo tạo sẵn một phần kết luận. Các phép kiểm mô phỏng tiếp tục dùng bộ ước lượng GAM-KT/Graph-GAM-KT và quy tắc chọn bài của Paper 2.</p></div>
<h3>Thay lượng lịch sử nhưng giữ cùng tình huống cần dự báo</h3><div class="measure"><p>So người học có nhiều và ít dữ liệu dễ lẫn khác biệt hồ sơ. Nhóm giữ cùng câu hỏi đã lưu và cho hệ thống xem 10 lượt gần nhất, 50 lượt gần nhất hoặc toàn bộ quá khứ hiện có. Trước khi rút ngắn, 54 đối chứng đầy đủ lịch sử phải khớp các đầu ra gốc. Có 27 tình huống, 54 cặp tình huống–độ dài quá khứ riêng biệt và 108 nhánh chạy. Nếu một độ dài đã bằng toàn lịch sử, trường hợp trùng đó không được coi là mẫu mới.</p><p>Trong hình, H là số lượt quá khứ thực có tại thời điểm cần dự báo; L là số lượt hệ thống được xem. So các cột trong cùng H để xem tác động thay đổi thế nào khi bớt lịch sử. Các thời điểm khác nhau có thể là câu hỏi và đáp án khác nhau.</p></div>
{figure(svg['history'],'Tác động không tăng hoặc giảm đều theo lượng lịch sử trong các tình huống đã chọn. Can thiệp thay cả quá khứ dùng cho bộ ước lượng lẫn bộ nhớ của quy tắc chọn bài; chưa cô lập bộ nhớ của mô hình theo dõi tri thức hoặc tác động của luyện tập thực tế.')}
<h3>Kiểm nguồn gốc của lộ trình ít quay lại chương</h3><div class="measure"><p>Paper 1 đã quy việc không quay lại chương trong các lượt thử cho quy tắc ưu tiên tính liên tục, thay vì riêng các cạnh liên chương. Khóa luận không nhận điều đó là phát hiện mới. Phép kiểm hiện tại hẹp hơn: quy tắc lựa chọn trong phiên bản mã đang có có bảo đảm không quay lại chương ở mọi tình huống không?</p><p>Nhóm dựng một đồ thị nhỏ không có chu trình và định trước diễn biến thành thạo. Quy tắc đang có tạo được lộ trình A → B → A. Đây là phản ví dụ cho một bảo đảm phổ quát của phiên bản mã đó; chưa xác minh đúng mã tạo ra kết quả PDF, nên không dùng nó để bác bỏ paper.</p></div>
{figure(svg['chapter'],'Lộ trình tạo từ đồ thị và diễn biến thành thạo dựng sẵn. Phản ví dụ không cho biết việc quay lại chương thường xảy ra thế nào hoặc kết quả PDF sai.')}
<h3>Đo kiến thức giữ lại sau hai tuần có cho thêm thông tin?</h3><div class="measure"><p>Nhóm kiểm công thức quên trước khi dùng kết quả sau 14 ngày như một bằng chứng bổ sung. Khi phần tăng ròng không âm quanh mức nền cố định, các khái niệm có cùng tốc độ quên và không luyện thêm sau khi kết thúc, tiến bộ ròng còn giữ sau 14 ngày bằng 0,4317105 lần tiến bộ ròng lúc kết thúc. Hai đại lượng này có cùng thứ hạng trong điều kiện đó.</p><p>Paper 2 còn đo <strong>phần học thêm tức thời, trước tác động quên về sau</strong> (gross immediate learning gain). Đại lượng này khác tiến bộ ròng cuối lịch. Quan hệ tuyến tính trên không chứng minh hai kết quả chính của Paper 2 dư thừa và chưa giải thích được vì sao paper không phát hiện khác biệt ở phần học thêm tức thời.</p><p>Nhóm tiếp tục thử cách đọc mức thành thạo phi tuyến. Hai trạng thái A/B có cùng 28 mức nền và phần tăng không âm, được chốt trước; đây không phải kết quả hai mô hình đã huấn luyện.</p></div>
{figure(svg['retention'],'Ở cách đọc thành thạo mềm, B cao hơn A khi kết thúc nhưng A cao hơn B sau 14 ngày. Cách đọc theo ngưỡng cứng chỉ chuyển từ hòa sang khác nhau. Hai trạng thái được dựng sẵn; chưa chứng minh một quy tắc chọn bài có thể tạo ra chúng.')}
<div class="limits"><strong>Kết luận giới hạn theo metric:</strong> quan hệ tỷ lệ chỉ áp dụng cho cách đọc tuyến tính trong điều kiện đã nêu. Phản ví dụ chưa chứng minh lợi ích của đồ thị, thành thạo tiềm ẩn đã được hiệu chuẩn hay hai kết quả đo độc lập về thống kê.</div>
<h3>Tách năng lực chung khỏi cơ chế thiếu kiến thức nền</h3><div class="measure"><p>Một nhóm có năng lực cao có thể làm tốt dù đồ thị có giúp hay không. Phép kiểm giữ cấu trúc mạnh/yếu giữa 28 khái niệm và chuỗi ngẫu nhiên theo khối seed, rồi thay mức năng lực chung và mức phạt khi thiếu nền tảng. Nhóm so lợi thế tương đối của cấu hình dùng đồ thị khi bật mức phạt với lợi thế khi tắt nó.</p><p>Thiết kế gồm 36 quỹ đạo, 4.320 tương tác nhưng chỉ 3 khối seed đã có. Kết quả là tiến bộ ròng trung bình trên thang Elo của mô phỏng, không phải điểm kiểm tra. Giá trị dương mới cho thấy lợi thế tương đối tăng khi bật cơ chế; không phải thành tích tuyệt đối.</p><p>Phép đo trong hình là: chênh lệch đủ cạnh so với rỗng khi bật mức phạt, trừ chênh lệch tương ứng khi tắt mức phạt. Ba mức năng lực khởi tạo là 1.000, 1.150 và 1.300 trên thang Elo. Đây là đối chiếu hai chênh lệch trong mô phỏng, không phải phân tích trước–sau trên học sinh thật.</p></div>
{figure(svg['ability'],'Lợi thế tương đối không tăng nhất quán khi bật mức phạt. Ở mức năng lực cao, chênh lệch tương tác bằng 0 đã được thiết kế dự kiến vì không thiếu nền tảng. Đồ thị vẫn tạo khác biệt khi tắt mức phạt; chưa thể quy mọi lợi thế cho cơ chế này.')}
<div class="limits"><strong>Không suy rộng quá thiết kế:</strong> Chuỗi số ngẫu nhiên chung theo bước không giữ câu hỏi và đáp án giống nhau sau khi các lộ trình khác nhau. Ba khối ngẫu nhiên được dùng lại không tạo thành 36 người học độc lập; chưa suy rộng kết quả thành quy luật năng lực hoặc kết luận trên học sinh thật.</div>
<h3>Junyi: khớp thứ tự luyện chưa chứng minh đồ thị dạy tốt</h3><div class="measure"><p>Dữ liệu bài làm đã ghi có thể phản ánh cách người học được dẫn bài từ trước. Nhóm so đồ thị đã xử lý với các đồ thị đối chứng và phân biệt những quan hệ thật sự được cùng người học quan sát. Nếu tổng số trường hợp dùng tính tỷ lệ thay đổi, tỷ lệ cao hơn có thể không đi cùng nhiều trường hợp phù hợp hơn.</p><p>Trên 256 người học và 12.575 tương tác Development đã lưu, đồ thị đối chứng 2 có ít trường hợp kiến thức nền xuất hiện trước hơn: 574 so với 575. Nhưng số trường hợp đủ điều kiện tính tỷ lệ cũng giảm, từ 649 xuống 645, nên tỷ lệ gộp lại cao hơn. Khi cho mỗi người học trọng số bằng nhau, chiều chênh lệch là âm; trên tập cùng đủ điều kiện quan sát, chênh lệch bằng 0. Ba phép tính trả lời những câu hỏi khác nhau.</p></div>
{figure(svg['junyi'],'Mỗi đối chứng thay 20 trong 976 cạnh, tức 20 cạnh xóa và 20 cạnh thêm. Chỉ 2, 10 và 6 trong 40 mục thay đổi ở từng đối chứng có cả hai đầu được cùng người học quan sát. Đổi cạnh chưa bảo đảm có dữ liệu để nhận diện ảnh hưởng.')}
<div class="limits"><strong>Giới hạn Junyi:</strong> Khớp thứ tự bài làm chưa chứng minh quan hệ tiên quyết đúng hoặc giúp dạy tốt hơn. Tập chung yêu cầu có ít nhất một kiến thức nền được cùng quan sát trong mỗi đồ thị, không nhất thiết cùng một cạnh. Chênh lệch bằng 0 chưa chứng minh tương đương; phải giữ rõ mẫu số của từng phép so.</div></section>
<section id="rq3"><div class="label">RQ3 · Giải pháp cần kiểm chứng</div><h2>Sử dụng các quan hệ chưa chắc chắn một cách thận trọng hơn</h2><div class="measure"><p>Đề cương đề xuất CG-AKT trên nền AKT: điều chỉnh ảnh hưởng từng quan hệ theo bằng chứng hỗ trợ, và giữ phương án không dùng đồ thị khi tập phát triển chưa cho thấy lợi ích đủ rõ. Đây là giả thuyết giải pháp cần kiểm chứng; các chẩn đoán trên chưa chứng minh nó hiệu quả.</p><p>Muốn so sánh, cần dữ liệu và quy trình không lẫn vai trò học, chọn cấu hình và hiệu chỉnh mức tự tin. Nhóm đã chuẩn bị bộ dữ liệu mô phỏng dưới đây; việc thu thập dùng quy tắc thu thập dữ liệu riêng, không chọn bài theo thành thạo hoặc trạng thái thật mà hệ thống thực nghiệm không được phép biết.</p></div>
{role_table}
<div class="measure"><p>Bộ dữ liệu có 60 người học mô phỏng và 12.600 tương tác, 210 lượt mỗi người; đủ 84 bài tập ở mỗi vai trò. Cách chọn bài ngẫu nhiên đều không làm môi trường trở thành không có tiên quyết: cơ chế học vẫn dùng đồ thị. Độ phủ chỉ tạo điều kiện để huấn luyện và đánh giá, chưa là bằng chứng về chất lượng mô hình hoặc độ tin cậy cạnh.</p></div>
<div class="finding"><strong>Chưa có kết quả nghiên cứu đầy đủ để khẳng định CG-AKT tốt hơn đồ thị cố định hoặc không dùng đồ thị.</strong> Corpus và phần mềm là nền để thực hiện phép so sánh, không thay kết quả mô hình.</div>
<p class="measure">AKT, SAKT, GKT, GAM-KT, Graph-GAM-KT cùng BKT tham chiếu vẫn thuộc phạm vi đề cương. Độ tin cậy dự kiến phản ánh bằng chứng dự báo có điều kiện, không tự động là xác suất quan hệ tiên quyết đúng. Các phương án phải được chọn trên dữ liệu phát triển trước khi đánh giá cuối.</p></section>
<section id="tiep-theo"><h2>Đã làm rõ điều gì, còn phải chứng minh gì?</h2><div class="measure"><p>RQ1 đã có phép tách trên cùng đầu vào và quan sát đầu ra trung gian. RQ2 đã có đối chứng lịch sử và năng lực cùng các kiểm tra độ nhạy của metric và quần thể. RQ3 mới có nền dữ liệu và các thành phần phục vụ thực nghiệm. Các kết quả chẩn đoán chưa thay thế phép đánh giá mô hình và kết quả học tập còn thiếu.</p><ol><li>Hoàn tất đối chứng về hiệu chỉnh xác suất và quyết định thành thạo; phân biệt đầu ra thay đổi với tác động nhân quả lên lựa chọn.</li><li>Đánh giá đồ thị chuyên gia, đồ thị học từ dữ liệu và đồ thị bị gây nhiễu trên cùng tập tương tác được chấm; giữ các kết quả bất lợi.</li><li>Thực hiện so sánh các mô hình đã huấn luyện theo quy trình đánh giá chung, rồi đánh giá riêng dự báo, quyết định và kết quả mô phỏng vòng kín.</li><li>Hoàn thiện demo nghiên cứu bằng mô hình được nghiệm thu; giữ rõ khác biệt giữa minh họa bằng kết quả lưu sẵn và cá nhân hóa đã được đánh giá.</li></ol></div></section>''']
    sources = [
        ('paper2/DC KLTN0127 23520355&23521338_LeVanTuan.pdf','Đề cương được cung cấp: trang1–4; ba RQ và mô hình/đánh giá bắt buộc.'),
        ('paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf','Paper 1: trang1,4–5; graph/policy và giới hạn mô phỏng.'),
        ('paper2/Paper2_RIVF_2026_Prerequisite_Aware_Knowledge_Tracing.pdf','Paper 2: trang1,4–6; package contrast, gross/retained outcomes và limitations.'),
        (BASELINE,'BKT/GAM-KT: Junyi Development common-row metrics, coverage và cách cân fold.'),
        ('research_tracking/runs/rq1-fixed-edge-set-contrast-20261108-01/summary.json','Full–empty: /groups; cùng1080targets, mọi profiles được giữ.'),
        ('research_tracking/runs/rq1-history-availability-20261108-02/native__control_parity.json','History:54full-prefix controls trước truncated phase.'),
        ('research_tracking/runs/rq1-history-availability-20261108-02/analysis__summary.json','History: /groups và /aliases;27targets/54pairs/108arms.'),
        (EXPOSURE_REPORT,'Kết quả và phương pháp readiness exposure; giới hạn source-local, không policy intervention.'),
        (EXPOSURE,'Readiness exposure: /groups với group=pooled;3240events,500roots,2041exceptions.'),
        (EXPOSURE_VALID,'Đối chiếu source-ready sets:3240/3240exact, không tạo model/teacher events mới.'),
        ('research_tracking/runs/cpu-rq12-20261107-03/paper1_counterexample.json','Available-selector counterexample; không PDFreproduction.'),
        ('research_tracking/runs/rq2-retention-readout-separation-20261108-01/readouts.json','Retention: /states,/orderings; counterexample constructed states.'),
        ('research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/native__summary.json','Ability: /abilities; finite controlled contrasts/3reused blocks.'),
        ('research_tracking/runs/rq2-conditions-evidence-20261108-01/conditions.json','Junyi: /junyi/corrected_base,/controls,/common_population_sensitivity.'),
        ('research_tracking/runs/development-corpus-native-20261108-01/input-04__independent-verification01.json','Corpus: /roles và coverage; không model efficacy.')]
    chunks.append('<section id="nguon"><h2>Tài liệu nền và phạm vi kết luận</h2>\n<div class="measure"><p>Ba câu hỏi của khóa luận được đặt trong đề cương đã duyệt. Hai nghiên cứu trước cung cấp kết quả kế thừa; các phép kiểm trong báo cáo này bổ sung bằng chứng về những cơ chế và điều kiện còn chưa được tách rõ.</p>\n<ol class="sources"><li>Phạm Triều Dương, Hồ Nguyễn Minh Sang. <em>Đề cương KLTN: Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình</em> (2026), tr. 1–4.</li>\n<li>Phạm Triều Dương, Hồ Nguyễn Minh Sang, Lê Văn Tuấn. <em>Separating Graph and Policy Effects in Adaptive Mathematics Sequencing: A Simulation Study</em>. Bản nộp RIVF 2026, tr. 1 và 4–5.</li>\n<li>Phạm Triều Dương, Hồ Nguyễn Minh Sang, Lê Văn Tuấn. <em>Auditing Prerequisite Context in Online Knowledge Tracing: Shared-Stream Prediction, Development Gating, and Closed-Loop Simulation</em>. Bản nộp RIVF 2026, tr. 1 và 3–6.</li></ol>\n<p>Những khác biệt đã quan sát là bằng chứng trong các điều kiện thí nghiệm được nêu, chưa là kết luận về hiệu quả trên học sinh thật. Vai trò của cách chọn bài và khoảng cách giữa dự báo với kết quả học đã được hai paper thừa nhận; phần bổ sung của khóa luận là các đối chứng và phép định lượng cụ thể được trình bày ở trên.</p>\n<p>Chưa xác minh đúng phiên bản mã tạo ra kết quả Paper 1. Vì vậy, phản ví dụ trên mã hiện có được giữ riêng, không dùng để thay thế hay bác bỏ bảng kết quả của paper.</p></div></section>\n<footer>Phạm Triều Dương · Hồ Nguyễn Minh Sang — KLTN, 08/11/2026.</footer></main></body></html>')
    document = '\n'.join(chunks).encode('utf-8')
    if re.search(rb'<(?:script|link|img|iframe|object|embed)\b[^>]*(?:src|href)\s*=\s*[\"\x27](?:https?:|//)', document, re.I):
        raise ValueError('HTML không được tải nguồn ngoài')
    for path, item in inventory.items():
        if digest((ROOT/path).read_bytes()) != item['sha256']:
            raise ValueError('Nguồn đổi trong lúc dựng: ' + path)
    with TARGET.open('xb') as stream:
        stream.write(document)
    receipt = dict(schema_version=1,status='HTML_BUILT_FROM_FROZEN_EVIDENCE_PENDING_VISUAL_REVIEW',
        target=TARGET.relative_to(ROOT).as_posix(),output_sha256=digest(document),output_bytes=len(document),
        builder_sha256=digest(Path(__file__).read_bytes()),source_inventory=inventory,
        sources_before_after_equal=True,numeric_records=58,existing_svg_count=6,existing_svg_raw_sha256=svg_hashes,
        additional_figures=['three-component schematic','readiness exposure denominator'],
        metric_population='Historical paired common-fitted Junyi Development; separate from simulator',
        notebook_cells_executed=0,model_teacher_training_network_calls=0,
        visual_or_browser_acceptance=False)
    with RECEIPT.open('x',encoding='utf-8') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_inventory','existing_svg_raw_sha256')},ensure_ascii=False))


if __name__ == '__main__':
    build()
