"""Đóng bằng chứng ảnh mobile đã đọc, giữ nguyên lượt capture lỗi trước."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT / 'research_tracking/runs/supervisor-witness-mobile-qa-20261109-02'
BUNDLE.mkdir(exist_ok=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


files = [PREP / 'witness120_mobile_top02.png', PREP / 'witness120_mobile_table02.png',
         Path(__file__).resolve()]
inventory = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in files}
write(BUNDLE / 'inventory_before_copy.json', inventory)
for source in files:
    target = BUNDLE / source.name
    shutil.copyfile(source, target)
    assert sha(target) == inventory[str(source.relative_to(ROOT)).replace('\\', '/')]
write(BUNDLE / 'visual_QA.json', dict(
    viewport=dict(width=390, height=844), document_scroll_width=375,
    section_width=335, table_width=335, svg_count=11,
    review='Root đã xem cả2ảnh gốc, tiêu đề, prose và bảng2x2 rõ, không text/numeric overlap hoặc overflow ngang.',
    capture='CSS chỉ trong browser tắt smooth scrolling/animations để viewport chụp ổn định. FileHTML nguồn không đổi bởi thao tác này.',
    cleanup='Ownedtab index1 đã đóng, browserlist chỉabout:blank. Server95967 terminal sauCtrl-C.',
    scope='QA Chặng14, không kiểm lại mọi biểu đồ cũ hoặc thêm bằng chứng nghiên cứu.',
))
(BUNDLE / 'README.md').write_text(
    '# Nghiệm thu bố cục mobile Chặng14\n\n'
    'Lượt trước có ảnh component lệch vị trí cuộn, giữ trong bundle engineering trước. '
    'Lượt này dùng cuộn tức thời và chụp viewport390×844. Root đã đọc ảnh tiêu đề/đoạn đầu và bảng cùng diễn giải. '
    'Bảng có đủ0/120/0/0, không đè số. Document375px nhỏ hơn viewport390px, bảng335px. '
    'Giữ11SVG. QA này đóng phần mobile của WRITE06 cùng desktop đã kiểm trước. '
    'Không thêm N hoặc mô hình. Preview và tab riêng đã đóng.\n', encoding='utf-8')
write(BUNDLE / 'manifest.json', dict(inputs_sha256=inventory,
    outputs_sha256={p.name: sha(p) for p in BUNDLE.iterdir() if p.is_file()}))

state_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['WRITE06_visual_progress_20261109'] = dict(status='COMPLETED_SECTION_DESKTOP_AND_MOBILE_QA',
    desktop_bundle='research_tracking/runs/akt-resume-metadata-and-report-qa-20261109-01',
    mobile_bundle=str(BUNDLE.relative_to(ROOT)).replace('\\', '/'),
    complete=True, browser_and_server_cleanup=True)
state['RQ1_cached_truth120_20261109']['publication']['visual_QA'] = True
state['RQ1_cached_truth120_20261109']['publication']['status'] = 'PUBLISHED_CONTENT_STATIC_DESKTOP_MOBILE_QA'
state['next_recommended_investigation'] = 'Review native08 rồi kiểm RAM>=4GiB trước native18. RQ2recovery cần3GiB. GKTtrainer04 harness2pins/counters cần refresh trước native. CUDA/actualproducerparity còn thiếu.'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
task_path = ROOT / 'docs/thesis_recovery/TASKS.json'
tasks = json.loads(task_path.read_bytes())
for task in tasks['tasks']:
    if task['id'] == 'WRITE06':
        task['status'] = 'COMPLETED'
        task['blockers'] = []
        task['required_artifacts'] = ['Technicalreport và hai fileGVHD đã xuất bản; bundle publication/static, desktop và mobile02 có ảnh gốc/manifest.']
task_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
note = '\n\n## 09/11 — Chặng14 đã nghiệm thu desktop và mobile\n\nLượt capture mới tắt smooth scrolling trong browser, Root đã đọc hai ảnh viewport390. Bảng không đè số, không tràn ngang. WRITE06 đã đóng. [Ảnh và QA](LINK) giữ nguyên bản và nguồnHTML tham chiếu. Preview/tab riêng đã đóng, không tăng mẫu nghiên cứu.\n'
for filename, link in (
    ('docs/REPOSITORY_MAP.md', '../research_tracking/runs/supervisor-witness-mobile-qa-20261109-02/README.md'),
    ('research_tracking/EVIDENCE_INDEX.md', 'runs/supervisor-witness-mobile-qa-20261109-02/README.md'),
    ('research_tracking/reports/README.md', '../runs/supervisor-witness-mobile-qa-20261109-02/README.md'),
    ('docs/thesis_recovery/INVESTIGATION_LOG.md', '../../research_tracking/runs/supervisor-witness-mobile-qa-20261109-02/README.md'),
):
    path = ROOT / filename
    text = path.read_text(encoding='utf-8')
    if filename.endswith('INVESTIGATION_LOG.md'):
        text += note.replace('LINK', link)
    else:
        first, rest = text.split('\n', 1)
        text = first + note.replace('LINK', link) + rest
    path.write_text(text, encoding='utf-8')
print('WRITE06_COMPLETE_DESKTOP_MOBILE_QA_SAVED')
