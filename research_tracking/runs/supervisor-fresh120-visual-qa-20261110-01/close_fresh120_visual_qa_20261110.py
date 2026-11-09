"""Đóng ảnh gốc và hai bản báo cáo cuối sau typography/visual QA."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT/'research_tracking/runs/supervisor-fresh120-visual-qa-20261110-01'
HUMAN = ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


html = (HUMAN/'BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
old = (ROOT/'research_tracking/supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html').read_text(encoding='utf-8')
assert re.findall(r'<svg\b.*?</svg>',html,re.S) == re.findall(r'<svg\b.*?</svg>',old,re.S)
assert html.count('<table') == html.count('</table>') == 14
assert 'Bước tiếp theo là kiểm mô hình và checkpoint thật theo nguồn mới' not in html
assert 'Chặng 15' in html and 'Cập nhật 10/11' in html
BUNDLE.mkdir(exist_ok=False)
files = [HUMAN/'BAO_CAO.md',HUMAN/'BAO_CAO_NGHIEN_CUU.html']
files += [PREP/name for name in ('fresh120_desktop01.png','fresh120_mobile01.png',
    'fresh120_desktop02.png','fresh120_mobile02.png','polish_fresh120_progress_20261110.py',
    'polish_fresh120_spacing_20261110.py')]
files.append(Path(__file__).resolve())
write(BUNDLE/'inventory_before_copy.json',{p.relative_to(ROOT).as_posix():sha(p) for p in files})
for source in files:
    target = BUNDLE/source.name
    shutil.copyfile(source,target)
    assert sha(target)==sha(source)
write(BUNDLE/'visual_QA.json',dict(
    scope='Chặng15 bảng và diễn giải mới, không rerender lại mọi figure cũ.',
    desktop=dict(viewport_width=1280,document_scroll_width=1280),
    mobile=dict(viewport_width=390,document_scroll_width=375,table_width=335),
    source_SVG_preserved=11,tables_balanced=14,
    review='Root đã đọc cảdesktop/mobile02, bảng không đè số và khôngoverflow ngang.01giữ trước chỉnhkhoảngcách chữsố.',
    owned_cleanup='page.close trongfinally, servers6127/47852 terminal sauCtrl-C.',
    scientific_scope='Không modelcall mới, không tăngN hoặc inference.',
))
(BUNDLE/'README.md').write_text('# Kiểm báo cáo10/11 sau xuất bản fresh120\n\n'
    'Hai file cuối, ảnh desktop/mobile nguyên bản và nguồn typography được giữ cùngSHA. '
    'Root đã đọc bản02, không chồng chữ/số hoặc tràn ngang.11SVG cũ nguyên văn và14bảng cân bằng. '
    'Bản09/11 giữ nguyên. Preview và tab riêng đã đóng. '
    'Phân tích mô tả, chưa kiểm định hoặcRQcompletion.\n',encoding='utf-8')
write(BUNDLE/'manifest.json',dict(kind='human_report_visual_QA_final',
    outputs_sha256={p.relative_to(BUNDLE).as_posix():sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
state_path = ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['RQ2_fresh_recovery_actual_20261110']['human_report_visual_QA']='ACCEPTED_DESKTOP_MOBILE_CHANG15'
state['RQ2_fresh_recovery_actual_20261110']['visual_QA_bundle']=BUNDLE.relative_to(ROOT).as_posix()
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
task_path = ROOT/'docs/thesis_recovery/TASKS.json'
tasks = json.loads(task_path.read_bytes())
for task in tasks['tasks']:
    if task['id']=='WRITE08':
        task['status']='COMPLETED_DESCRIPTIVE_REPORT_AND_VISUAL_QA'
        task['required_artifacts'].append(BUNDLE.relative_to(ROOT).as_posix())
task_path.write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a',encoding='utf-8') as stream:
    stream.write('\nFinalfresh120QA đã đạtdesktop1280/mobile390, table335/document375. '
        'Giữ11SVG/14tables, hai report10/11 có đoạn tiến độ mới và wordingcheckpointcurrent. '
        'Screenshots01/02 và source typography đãđóng, WRITE08hoàn tất. '
        'Hai previewservers và tab riêng đãđóng. Không tăngN hoặcmodelcalls.\n')
print('FRESH120_FINAL_REPORT_QA_ACCEPTED_AND_CLOSED')
