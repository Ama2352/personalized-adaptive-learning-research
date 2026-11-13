"""Lưu kết quả kiểm nhanh, cập nhật báo cáo và đóng bundle."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
result = json.loads((BUNDLE / 'result.json').read_text(encoding='utf-8'))
assert result['status'] == 'FAIL_STRICT_PROBABILITY_PARITY'
note = ('Kiểm tiếp bằng checkpoint A0 epoch 9 thật trên CPU với 3.538 target tổng hợp đã xác nhận '
    'nạp đúng trọng số, target/thứ tự khớp và model không đổi. Sai lệch xác suất lớn nhất 0,0000224 '
    'vượt ngưỡng kiểm đã đặt, dù chênh lệch Log Loss chỉ khoảng 0,0000000218. '
    'Giữ nguyên ngưỡng kiểm, chưa nghiệm thu batch128 cho training chính. '
    'Cần đối chiếu checkpoint này trên CUDA và selection Junyi thật. Lượt kiểm dùng 0 USD Modal.')
report = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
path = report / 'BAO_CAO.md'
text = path.read_text(encoding='utf-8')
pattern = r'(\n## 13/11 — chuẩn bị tối ưu validation\n.*?)(?=\n## |\Z)'
assert re.search(pattern, text, re.S)
text = re.sub(pattern, lambda match: match[1].rstrip() + '\n\n**Kiểm checkpoint đã train tiếp theo.** '
    + note + '\n', text, count=1, flags=re.S)
path.write_text(text, encoding='utf-8')
path = report / 'BAO_CAO_NGHIEN_CUU.html'
text = path.read_text(encoding='utf-8')
pattern = r'(<section id="junyi-validation-batch-20261113">.*?)</section>'
assert len(re.findall(pattern, text, re.S)) == 1
text = re.sub(pattern, lambda match: match[1] + '<p><strong>Kiểm checkpoint đã train tiếp theo.</strong> '
    + note + '</p></section>', text, count=1, flags=re.S)
path.write_text(text, encoding='utf-8')
for name, link in [
    ('research_tracking/reports/README.md', '../runs/junyi-a0-checkpoint-parity-20261113-01/README.md'),
    ('docs/REPOSITORY_MAP.md', '../research_tracking/runs/junyi-a0-checkpoint-parity-20261113-01/README.md'),
]:
    path = ROOT / name
    text = path.read_text(encoding='utf-8')
    position = text.index('\n')
    text = text[:position] + '\n\n## 13/11 — kiểm checkpoint A0 thật\n\n' + note + '\n\n[Hồ sơ](' + link + ')\n' + text[position:]
    path.write_text(text, encoding='utf-8')
path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(path.read_text(encoding='utf-8-sig'))
state['junyi_a0_real_checkpoint_quick_check_20261113'] = dict(
    evidence=BUNDLE.relative_to(ROOT).as_posix(), result=result,
    next_vi='Giữ kết quả kiểm không đạt. Chưa dùng batch128 chính thức. Đối chiếu checkpoint trên CUDA và selection thật trước tiếp nhận.')
path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
inputs = [ROOT/'experiments/akt/results/model-export-a0-batch128-20261112-01'/name for name in (
    'A0_JUNYI_SELECTED.pt', 'MODEL_INDEX.json')]
def identity(path):
    return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
files = sorted(path for path in BUNDLE.iterdir() if path.is_file() and path.name != 'manifest.json')
manifest = dict(status='CLOSED_TECHNICAL_CHECK_FAILED_ACCEPTANCE',
    inputs={path.relative_to(ROOT).as_posix(): identity(path) for path in inputs},
    outputs={path.relative_to(ROOT).as_posix(): identity(path) for path in files},
    modal_spent_usd=0, training_epochs=0)
(BUNDLE/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('Đã lưu kiểm không đạt, cập nhật báo cáo và đóng bundle.')
