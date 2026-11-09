"""Đồng bộ tiến độ từ actual receipt, không tự mở gate native/GPU."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
receipt = json.loads((PREP / 'graph29-metadata-tests06-owned/final.json').read_bytes())
assert receipt['status'] == 'ACCEPTED_BATCHC_METADATA_TESTS_NOT_NATIVE'
assert receipt['child_result']['counts'] == dict(tests=299, failures=0, errors=0, skipped=0)
assert receipt['receipt']['job_active_after_cleanup'] == 0

state_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['GRAPH29_cold299_20261109'] = dict(
    status='ACTUAL_299_PASS_CURRENT_SOURCE_NATIVE_PENDING',
    receipt_sha256='9d29efe4f37f10d6674918be83c24cbd8e0c92477949804f4e0e3683768b96a8',
    tests=299, failures=0, errors=0, skipped=0,
    elapsed_seconds=receipt['elapsed_seconds'],
    resources=receipt['child_result']['resources'],
    bundle='research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01',
    native=False, CUDA=False, Modal_spend=0,
)
state['WRITE06_visual_progress_20261109'] = dict(desktop='ACCEPTED_SECTION_SCREENSHOT',
    mobile='WIDTH_MEASURED_CAPTURE_INCOMPLETE_BROWSER_HANDLE_LOST',
    owned_preview_servers='TERMINAL', complete=False)
state['GKT_optimizer_preflight_20261109'] = dict(status='GUARD_APPLIED_AST_ONLY',
    detail='Từ chối exp_avg_sq âm trước compute; trainer8 harness cần cập nhật2pins và API counts.',
    trainer_sha256='305fccf1038f41751a1137444cb2be469baf6f15090e27dc1595334ce3cb19cc')
state['goal_turn_previous_classification_20261109'] = 'PROGRESS_ACTUAL_COLD299_PASS_AND_GKT_GUARD'
state['next_recommended_investigation'] = 'Review native08 sau cold299; RAM>=4GiB trước native18. RQ2recovery cần3GiB. Hoàn tất mobilecapture WRITE06. Giữ goal và CUDA gate chưa hoàn tất.'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

task_path = ROOT / 'docs/thesis_recovery/TASKS.json'
tasks = json.loads(task_path.read_bytes())
for task in tasks['tasks']:
    if task['id'] == 'GRAPH29':
        task['status'] = 'CURRENT_COLD299_PASS_NATIVE_PRODUCER_PARITY_PENDING'
        task['acceptance_criteria'] = 'Nguồn hiện hành đã chạy299test bodies/0FES, source/runtime ổn định, Job0. Còn actual native18 và public producer continuous/resume parity. Crash/CUDA recovery cần acceptance riêng.'
        task['blockers'] = ['Native harness08 cần review, admission4GiB; actual producer parity/crash/CUDA còn thiếu.']
    if task['id'] == 'WRITE06':
        task['status'] = 'PUBLISHED_STATIC_AND_DESKTOP_QA_MOBILE_CAPTURE_PENDING'
        task['blockers'] = ['Mobilewidth không tràn, nhưng capture lệch và browser mất handle, chưa nghiệm thu hình mobile.']
    if task['id'] == 'GKT08':
        task['acceptance_criteria'] = 'Model/trainer đã áp dụng, trainer04 chặn second moment âm và kiểm AST. Cần native model11/trainer8, checkpoint/export/producer/adaptor và fitted evidence riêng.'
task_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

paragraph = ('**Chuẩn bị huấn luyện AKT đã tiến thêm một mốc kiểm phần mềm.** '
    'Sau khi bổ sung khả năng tiếp tục ở cuối một vòng huấn luyện, bộ kiểm hợp đồng hiện hành đã đạt 299/299 ca. '
    'Bước tiếp theo là kiểm mô hình và checkpoint thật theo nguồn mới, rồi kiểm CUDA. '
    'Kết quả này tăng độ tin cậy của pipeline, chưa bổ sung kết quả so sánh các mô hình cho RQ3.')
human = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
md = human / 'BAO_CAO.md'
text = md.read_text(encoding='utf-8')
marker = '**Mốc tích hợp mới nhất, AKT đã đi qua quy trình chọn checkpoint thực tế.**'
assert text.count(marker) == 1
text = text.replace(marker, paragraph + '\n\n' + marker)
md.write_text(text, encoding='utf-8')
html = human / 'BAO_CAO_NGHIEN_CUU.html'
text = html.read_text(encoding='utf-8')
old_svg = re.findall(r'<svg\b.*?</svg>', text, flags=re.S)
marker = '<section id="chang-14"'
assert text.count(marker) == 1
addition = '<p>' + paragraph.replace('**', '', 2) + '</p>\n'
text = text.replace(marker, addition + marker)
assert re.findall(r'<svg\b.*?</svg>', text, flags=re.S) == old_svg
assert len(old_svg) == 11
html.write_text(text, encoding='utf-8')

note = ('\n\n## 09/11 — AKT current cold299 đã đạt\n\n'
    'Collection05 timeout và cleanup Job0 được giữ. Sau khi tắt preview, collection06 đạt299IDs/0body, '
    'tests06 đạt299bodies/0FES trong67,76s, peak59.211.776B/minfree2.556.534.784B. '
    'Source/runtime trước–sau khớp và ownedJob0. [Bundle kiểm](LINK) giữ rawlogs, failures và hai screenshot gốc. '
    'Chặng14 desktop đã xem, mobile cówidth390/document375/table335 nhưng capture lệch và mấtbrowserhandle, '
    'chưa đóng WRITE06. Hai previewservers đã terminal, tab riêng không còn. '
    'GKTguard second moment âm đã áp dụng và AST, chưa native. Currentcold299 không cấp native/CUDA/GPUfit authorization.\n')
for filename, link in (
    ('docs/REPOSITORY_MAP.md', '../research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01/README.md'),
    ('research_tracking/reports/README.md', '../runs/akt-resume-metadata-and-report-qa-20261109-01/README.md'),
    ('research_tracking/EVIDENCE_INDEX.md', 'runs/akt-resume-metadata-and-report-qa-20261109-01/README.md'),
    ('docs/thesis_recovery/INVESTIGATION_LOG.md', '../../research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01/README.md'),
):
    path = ROOT / filename
    text = path.read_text(encoding='utf-8')
    if filename.endswith('INVESTIGATION_LOG.md'):
        text += note.replace('LINK', link)
    else:
        first, rest = text.split('\n', 1)
        text = first + note.replace('LINK', link) + rest
    path.write_text(text, encoding='utf-8')
print('STATE_AND_TASKS_UPDATED_299_PASS_11_SVG_PRESERVED')
