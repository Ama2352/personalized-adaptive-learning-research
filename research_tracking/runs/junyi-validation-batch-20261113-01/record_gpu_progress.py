"""Nghiệm thu kiểm T4 tổng hợp, lưu báo cáo và đóng bundle sau snapshot CPU."""
import ast
import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
positive = json.loads((BUNDLE / 'positive-result.json').read_text())
balanced = json.loads((BUNDLE / 'balanced-result.json').read_text())
receipt = json.loads((BUNDLE / 'artifact-verification.json').read_text())
assert receipt['status'] == 'PASS_SHA_CRC_INVENTORY_PARITY_AND_NONZERO_GRAPH'
assert positive['fixture_signal'] == 'positive'
assert positive['results'][1]['graph_residual_vs_a0_max_abs'] > 0.01
suite = ET.parse(BUNDLE / 'colab-test-attempt-01.xml').getroot().find('testsuite')
assert suite.attrib['tests'] == '126'
assert all(suite.attrib[key] == '0' for key in ('failures', 'errors', 'skipped'))
bridge = json.loads((ROOT / 'artifacts/akt/private/colab-bridge/current.json').read_text())
assert bridge['event'] == 'closed' and not bridge['connected']

paragraph = (
    'Validation trước đây xử lý lần lượt từng cửa sổ lịch sử, khiến GPU phải nhận nhiều lượt nhỏ. '
    'Đã nối cách gom tối đa 128 cửa sổ độc lập và kiểm trên T4 miễn phí của Colab. '
    'Bộ kiểm Linux đạt 126 ca. Phép đo dùng 64 người học tổng hợp, 12.800 lượt dự báo, '
    'mỗi mô hình đo ba cặp để đối chiếu thời gian và kết quả. Đây là kiểm dự đoán, không cập nhật trọng số.'
)
limitation = (
    'Target, nhãn và thứ tự khớp hoàn toàn. Sai lệch xác suất lớn nhất khoảng 1,2×10⁻⁷. '
    'VRAM do PyTorch cấp phát cao nhất khoảng 1,14 GiB. Đã giữ cả phép kiểm tín hiệu đồ thị triệt tiêu '
    'và phép kiểm có tín hiệu khác 0. Hai chương trình kiểm GPU chạy tổng khoảng 84 giây. '
    'Chưa kiểm lại toàn selection bằng checkpoint A0 đã train hoặc đo chi phí đọc dữ liệu Junyi. '
    'Vì vậy, số đo này xác nhận tăng tốc dự đoán trên dữ liệu tổng hợp, còn việc giữ nguyên chọn epoch A0 '
    'và mức tăng tốc toàn pipeline cần kiểm tiếp. Artifact đã tải về ổ D, kiểm toàn vẹn, '
    'gửi lệnh giải phóng runtime và đóng cầu nối. Lượt này dùng 0 USD Modal.'
)
table_md = (
    '| Mô hình | Từng cửa sổ | Batch128 | Tăng tốc |\n'
    '|---|---:|---:|---:|\n'
    '| A0 — AKT không đồ thị | 1,32 giây | 0,34 giây | 3,88 lần |\n'
    '| A1 — AKT đồ thị cố định | 5,07 giây | 2,52 giây | 2,01 lần |'
)

def replace_markdown(path, heading, body):
    text = path.read_text(encoding='utf-8')
    pattern = r'\n## ' + re.escape(heading) + r'\n.*?(?=\n## |\Z)'
    assert re.search(pattern, text, re.S), (path, heading)
    text = re.sub(pattern, lambda _: '\n## ' + heading + '\n\n' + body + '\n', text, count=1, flags=re.S)
    path.write_text(text, encoding='utf-8')

report = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
replace_markdown(report / 'BAO_CAO.md', '13/11 — chuẩn bị tối ưu validation',
    paragraph + '\n\n' + table_md + '\n\nTrung bình ba lượt trên bộ tổng hợp có tín hiệu đồ thị.\n\n'
    + limitation + '\n\n![Thời gian và bộ nhớ validation T4](../../../runs/junyi-validation-batch-20261113-01/validation-batch-t4-v2.svg)')
path = report / 'BAO_CAO_NGHIEN_CUU.html'
text = path.read_text(encoding='utf-8')
image = base64.b64encode((BUNDLE / 'validation-batch-t4-v2.png').read_bytes()).decode()
section = ('<section id="junyi-validation-batch-20261113"><h2>13/11 — đã đo validation theo batch trên T4</h2>'
    '<p>' + paragraph + '</p><table><thead><tr><th>Mô hình</th><th>Từng cửa sổ</th>'
    '<th>Batch128</th><th>Tăng tốc</th></tr></thead><tbody>'
    '<tr><td>A0 — AKT không đồ thị</td><td>1,32 giây</td><td>0,34 giây</td><td>3,88 lần</td></tr>'
    '<tr><td>A1 — AKT đồ thị cố định</td><td>5,07 giây</td><td>2,52 giây</td><td>2,01 lần</td></tr>'
    '</tbody></table><p>Trung bình ba lượt trên bộ tổng hợp có tín hiệu đồ thị.</p>'
    '<figure><img style="width:100%;height:auto" alt="Thời gian và bộ nhớ validation trên T4" '
    'src="data:image/png;base64,' + image + '"></figure><p>' + limitation + '</p></section>')
pattern = r'<section id="junyi-validation-batch-20261113">.*?</section>'
assert len(re.findall(pattern, text, re.S)) == 1
text = re.sub(pattern, lambda _: section, text, count=1, flags=re.S)

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == 'id')

parser = IdParser()
parser.feed(text)
assert len(parser.ids) == len(set(parser.ids)), 'Trùng ID HTML'
path.write_text(text, encoding='utf-8')
for name, link in [
    ('docs/REPOSITORY_MAP.md', '../research_tracking/runs/junyi-validation-batch-20261113-01/README.md'),
    ('research_tracking/reports/README.md', '../runs/junyi-validation-batch-20261113-01/README.md'),
    ('notebooks/README.md', '../research_tracking/runs/junyi-validation-batch-20261113-01/README.md'),
]:
    replace_markdown(ROOT / name, '13/11 — validation theo batch',
        '[Hồ sơ](' + link + ') giữ 126 ca Linux đạt, hai phép kiểm T4, log và figure. '
        'Trên 12.800 target tổng hợp có tín hiệu đồ thị, A0 tăng tốc 3,88 lần, A1 2,01 lần. '
        'Chưa kiểm lại toàn selection bằng checkpoint A0. Không train epoch, không dùng Modal.')

state_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_text(encoding='utf-8-sig'))
state['junyi_validation_batch_20261113'] = dict(
    evidence=BUNDLE.relative_to(ROOT).as_posix(), cpu_tests=126, linux_tests=126,
    mode='batched_windows_v1_batch128', t4_verified=True,
    t4_scope='A0_A1_SYNTHETIC_IN_MEMORY_INFERENCE_ONLY',
    a0_full_selection_parity=False, main_training_adopted=False,
    modal_spent_this_batch=0, colab_bridge_closed=True,
    runtime_release_command_completed=True, training_epochs=0,
    speedup_positive_fixture={row['variant']: row['speedup'] for row in positive['results']},
    next_vi='Kiểm checkpoint A0 thật và chi phí đọc/validation Junyi trước tiếp nhận mode mới vào training chính.')
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for path in [ROOT / 'scripts/akt/synthetic_validation_batch_probe.py', BUNDLE / 'build_notebook.py', Path(__file__)]:
    ast.parse(path.read_text(encoding='utf-8-sig'))
notebook = json.loads((ROOT / 'notebooks/akt_colab_validation_batch.ipynb').read_text(encoding='utf-8'))
for index, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        compile(''.join(cell['source']), f'cell-{index}', 'exec')

def file_identity(path):
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

sources = [ROOT / 'scripts/akt/synthetic_validation_batch_probe.py', ROOT / 'notebooks/akt_colab_validation_batch.ipynb']
files = sorted(path for path in BUNDLE.iterdir() if path.is_file() and path.name != 'manifest-final.json')
manifest = dict(status='CLOSED_T4_SYNTHETIC_PASS_A0_REAL_REPLAY_PENDING',
    files={path.relative_to(ROOT).as_posix(): file_identity(path) for path in files + sources},
    source_packages={name: file_identity(ROOT / name) for name in [
        'artifacts/akt/colab/junyi-validation-batch-20261113-02.zip',
        'artifacts/akt/colab/junyi-validation-batch-20261113-03.zip']},
    archive=receipt, qa=dict(html_unique_ids=True, notebook_compiles=True, probe_ast=True,
        figure_v2_visually_checked=True, linux_tests=126, colab_bridge_closed=True))
(BUNDLE / 'manifest-final.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status=manifest['status'], files=len(files), qa=manifest['qa']), ensure_ascii=False))
