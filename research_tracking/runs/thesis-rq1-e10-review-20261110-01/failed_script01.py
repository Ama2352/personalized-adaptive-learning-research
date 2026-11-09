"""Áp dụng hai làm rõ từ review độc lập, giữ bundle trước nguyên vẹn."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = ROOT / 'research_tracking/runs/thesis-rq1-e10-review-20261110-01'
BUNDLE.mkdir(exist_ok=False)
DRAFT = ROOT / 'research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'
files = [DRAFT, ROOT / 'research_tracking/reports/rq1_on_policy_mastery_witness_20261109.md',
    ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO.md',
    ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


inventory = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in files}
write(BUNDLE / 'inventory_before_copy.json', inventory)
for source in files:
    target = BUNDLE / 'before' / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(source) == sha(target)

text = DRAFT.read_text(encoding='utf-8')
prefix = DRAFT.read_bytes()[:52432]
old = 'Nhóm đối chiếu lại một lịch sử PG đã lưu, gồm120 lượt hỏi trước khi cập nhật bằng đáp án hiện tại.'
new = old + ' Lịch sử dùng seed21000, cơ chế phạt do thiếu tiên quyết trong world được tắt, tương ứng λ=0.'
assert text.count(old) == 1
text = text.replace(old, new)
old = 'Các phép so sánh đồ thị, hiệu chỉnh xác suất, trạng thái khởi đầu thấp hơn và đánh giá kết quả học trên nhiều người học vẫn còn thiếu.'
new = 'Trong phép đối chiếu quyết định thành thạo với latent này, so sánh giữa các đồ thị, hiệu chỉnh xác suất, trạng thái khởi đầu thấp hơn và đánh giá kết quả học trên nhiều người học vẫn còn thiếu. Các đối chứng nguồn đồ thị ở E9 có phạm vi riêng.'
assert text.count(old) == 1
text = text.replace(old, new)
DRAFT.write_text(text, encoding='utf-8')
assert DRAFT.read_bytes()[:52432] == prefix
for file in files[1:]:
    text = file.read_text(encoding='utf-8')
    old = 'Bộ chọn bài vẫn giữ đồ thị tiên quyết.'
    assert text.count(old) == 1
    text = text.replace(old, old + ' Cơ chế phạt do thiếu tiên quyết trong thế giới mô phỏng được tắt.')
    file.write_text(text, encoding='utf-8')
for source in files:
    target = BUNDLE / 'after' / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(source) == sha(target)
copy = BUNDLE / Path(__file__).name
shutil.copyfile(Path(__file__).resolve(), copy)
write(BUNDLE / 'review.json', dict(
    reviewer='rq12_evidence_synthesis', verdict='SCOPED_PASS_TWO_REFINEMENTS_APPLIED',
    checks=['120rows/22concepts/onehistory', 'estimator off keeps controllergraph',
        'zero theta-eligible opportunities, no pi irrelevance claim',
        'firstvisit22 limits learning transition, unserved6 unknown'],
    refinements=['seed21000/worldlambda0 explicit', 'remaining graph comparison scoped to this native mastery/latent witness, E9 retained'],
    old_prefix_bytes_preserved=52432, new_model_calls=0, new_independent_N=0,
))
(BUNDLE / 'README.md').write_text(
    '# Review độc lập E10 và làm rõ phạm vi\n\n'
    'Review xác nhận số liệu và giới hạn diễn giải, đề nghị nói rõ seed/world mechanism và giới hạn câu so sánh đồ thị còn thiếu. '
    'Đã áp dụng cả hai. Hai fileGVHD cùng technicalreport bổ sung cơ chế phạt thiếu tiên quyết được tắt. '
    'E9 không bị phủ nhận, E1–E9 giữ prefix52432bytes. Bundle viết trước được giữ nguyên. '
    'Không thực nghiệm mới hoặc thay protocol.\n', encoding='utf-8')
write(BUNDLE / 'manifest.json', dict(outputs_sha256={str(p.relative_to(BUNDLE)).replace('\\', '/'): sha(p)
    for p in BUNDLE.rglob('*') if p.is_file()}))
tasks_path = ROOT / 'docs/thesis_recovery/TASKS.json'
tasks = json.loads(tasks_path.read_bytes())
for task in tasks['tasks']:
    if task['id'] == 'WRITE07':
        task['status'] = 'COMPLETED_WRITING_FROM_CLOSED_EVIDENCE'
        task['required_artifacts'].append(str(BUNDLE.relative_to(ROOT)).replace('\\', '/'))
tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['thesis_E10_20261110']['status'] = 'PUBLISHED_NUMERIC_PREFIX_AND_INDEPENDENT_REVIEW_COMPLETE'
state['thesis_E10_20261110']['review_bundle'] = str(BUNDLE.relative_to(ROOT)).replace('\\', '/')
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (ROOT / 'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a', encoding='utf-8') as stream:
    stream.write('\nReview E10 scopedPASS đã áp dụng hai làm rõ, nêu seed/worldλ0 và giới hạn phần graphcomparison còn thiếu trong witness này. Giữ E9contrast và prefix52432bytes. WRITE07 hoàn tất, không thêmN hoặcmodelcall.\n')
print('E10_INDEPENDENT_REVIEW_APPLIED_PREFIX_PRESERVED')
