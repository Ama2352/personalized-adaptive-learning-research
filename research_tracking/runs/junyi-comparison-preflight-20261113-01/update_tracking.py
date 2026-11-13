"""Ghi mốc kiểm pipeline và các điều kiện còn thiếu vào hồ sơ hiện hành."""
import ast
import hashlib
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
verification = json.loads((BUNDLE/'artifact-verification.json').read_text())
assert verification['status'] == 'PASS_ARCHIVE_SHA_CRC_INVENTORY_T4_RESULT'
body = '''Đã đối chiếu split A0 với assignments BKT/GAM-KT, tái dựng đúng bốn nhóm người học và kiểm hash cache train/selection cùng vocabulary 717. Colab đạt 156 ca kiểm trên Linux. Kiểm CUDA tổng hợp A0/A1 trên T4 dùng batch128, chiều dài200 và vocabulary717 đã đạt trong khoảng14giây, VRAM cấp phát cao nhất4,70GiB. Backbone khởi tạo khớp chính xác với A0 H100, graph-off khớp A0 và nhãn hiện tại/tương lai giữ đúng ranh giới nhân quả. Model và Adam sau phục hồi khớp chạy liên tục. Checkpoint, dự báo kiểm, runtime và logs đã tải về D, đối chiếu SHA/CRC/inventory.

Mốc này xác nhận thêm độ tin cậy kỹ thuật cho A0/A1. A2/A3 Junyi còn thiếu confidence fitted đúng train80 và tích hợp producer. Hợp đồng so sánh mới đã có kiểm âm, còn cần nối bắt buộc vào các entrypoint trước training chính. Các variant cần cùng batch128, split/vocabulary, cửa sổ, khởi tạo backbone và quy tắc tối đa20epoch/patience3/min_delta0,0001. Epoch tốt nhất có thể khác nhau. Đề xuất giới hạn9epoch và bỏrefit trong hội thoại chưa được áp dụng vào protocol.

BKT/GAM-KT lịch sử dùng toàn outer-train, còn A0 hiện fit train80. Metric selection A0 phục vụ chọn checkpoint. Bảng so sánh chính thức cần cùng outer-validation, target identity và coverage, đồng thời công khai khác biệt dữ liệu train hoặc thực hiện matched baseline fit riêng. Các công thức AUC/LogLoss/Brier/ECE15bins được giữ tương ứng. Cả ma trận fit/refit/calibration/inference còn cần dự toán trong credits còn lại trước lượt H100 tiếp theo.
'''

current = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
path = current/'BAO_CAO.md'
text = path.read_text(encoding='utf-8')
end = text.index('\n')
text = text[:end]+'\n\n## 13/11 — kiểm tính tương thích trước training các biến thể\n\n'+body+text[end:]
path.write_text(text,encoding='utf-8')
path = current/'BAO_CAO_NGHIEN_CUU.html'
text = path.read_text(encoding='utf-8')
section = '<section id="junyi-comparison-preflight-20261113"><h2>13/11 — kiểm tính tương thích trước training các biến thể</h2>'
section += ''.join('<p>'+paragraph+'</p>' for paragraph in body.strip().split('\n\n'))+'</section>\n'
anchor = '<section id="a0-h100-progress-current"'
assert anchor in text and 'id="junyi-comparison-preflight-20261113"' not in text
text = text.replace(anchor,section+anchor,1)
path.write_text(text,encoding='utf-8')

links = [
    ('docs/REPOSITORY_MAP.md','../research_tracking/runs/junyi-comparison-preflight-20261113-01/README.md'),
    ('research_tracking/reports/README.md','../runs/junyi-comparison-preflight-20261113-01/README.md'),
    ('notebooks/README.md','../research_tracking/runs/junyi-comparison-preflight-20261113-01/README.md')]
for relative,link in links:
    path = ROOT/relative
    text = path.read_text(encoding='utf-8')
    end = text.index('\n')
    update = '\n\n## 13/11 — kiểm Junyi trước các biến thể AKT\n\n'
    update += '[Hồ sơ kiểm]('+link+') có audit split/vocabulary, hợp đồng so sánh và kết quả T4 A0/A1 batch128 cùng checkpoint đã tải về D. '
    if relative.startswith('notebooks'):
        update += '[Notebook T4](akt_colab_junyi_comparison.ipynb) dùng gói nguồn03 và venv trong dự án. '
    update += 'A2/A3 Junyi và ràng buộc entrypoint còn cần hoàn thiện trước training chính.\n'
    path.write_text(text[:end]+update+text[end:],encoding='utf-8')

state_path = ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_text(encoding='utf-8-sig'))
state['junyi_comparison_preflight_20261113'] = dict(
    evidence=BUNDLE.relative_to(ROOT).as_posix(),data_lineage='PASS',
    linux_tests=156,t4_synthetic_a0_a1='PASS',artifact_download='VERIFIED_ON_D',
    backbone_matches_h100_a0=True,a2_a3_junyi_ready=False,paid_training_ready=False,
    next_vi='Gắn hợp đồng vào entrypoint, xây artifact confidence đúng train80 cho A2/A3, kiểm T4 các variant và dự toán trọn gói trước H100.',
    protocol_changes_adopted=False)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (BUNDLE/'README.md').open('a',encoding='utf-8') as stream:
    stream.write('\n\n## Nghiệm thu cuối đợt\n\n'+body)
    stream.write('\nArtifact ở `experiments/akt/results/colab-junyi-comparison-20261113-01/artifacts.zip`, 25.111.987byte, 11file đã đối chiếu inventory. '
        'Gói chứa checkpoint tổng hợp của lượt đạt, dự báo, logs, JUnit, runtime và source-overlay. '
        'Failure checkpoint thiếu epoch ở lượt đầu được giữ trên Colab, log/schema lỗi giữ về D. '
        'Bản nguyên source02 và source03 vẫn ở artifacts/akt/colab. Source03 chỉ sửa progress.epoch của probe, overlay đã đối chiếu với source local. '
        'Không thay thuật toán checkpoint hoặc kiến trúc để xử lý lỗi probe.\n')

for path in [ROOT/'src/knowledge_tracing/akt/comparison_contract.py',
    ROOT/'scripts/akt/audit_junyi_comparison.py', ROOT/'scripts/akt/synthetic_junyi_comparison_probe.py',
    *BUNDLE.glob('*.py')]:
    ast.parse(path.read_text(encoding='utf-8-sig'))
notebook = json.loads((ROOT/'notebooks/akt_colab_junyi_comparison.ipynb').read_text(encoding='utf-8'))
for index, cell in enumerate(notebook['cells']):
    if cell['cell_type']=='code':
        compile(''.join(cell['source']),f'cell-{index}','exec')
inventory = {}
for path in [*sorted(BUNDLE.glob('*')),ROOT/'notebooks/akt_colab_junyi_comparison.ipynb',
    ROOT/'src/knowledge_tracing/akt/comparison_contract.py', ROOT/'scripts/akt/audit_junyi_comparison.py',
    ROOT/'scripts/akt/synthetic_junyi_comparison_probe.py',ROOT/'tests/akt/test_comparison_contract.py']:
    if path.is_file():
        inventory[path.relative_to(ROOT).as_posix()] = dict(bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
(BUNDLE/'manifest.json').write_text(json.dumps(dict(status='CLOSED',files=inventory,
    check='Python AST và các cell notebook compile đạt, test và T4 theo artifact-verification'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Đã cập nhật báo cáo và đóng hồ sơ kiểm pipeline.')
