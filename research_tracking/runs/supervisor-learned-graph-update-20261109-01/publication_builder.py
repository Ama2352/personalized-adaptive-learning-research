"""Đóng gói trình bày và cập nhật tiến độ từ pilot19 đã nghiệm thu."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
HUMAN = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
RUN = 'research_tracking/runs/rq2-learned-graph-ability-20261109-01'
QA_RUN = 'supervisor-learned-graph-update-20261109-01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

assert sha(ROOT / RUN / 'manifest.json') == '6d848a6bd8bbb4b26abd3f3caef4a8de2a1b80c9176cbaa4c3a8bce5164bf5a5'
draft = PREP / 'RQ2_LEARNED_GRAPH_ABILITY_RESULTS_DRAFT01.md'
assert sha(draft) == '5d1b8592d2933a8e9afc100325d15f64e658dccac9eab4528b8f3d6437554687'
report = ROOT / 'research_tracking/reports/rq2_learned_graph_source_ability_results_20261109.md'
assert not report.exists()
text = draft.read_text(encoding='utf-8')
text = text.replace('Báo cáo draft sau actual19worlds, chưa đóng bundle hoặc cập nhật báo cáo người đọc. Canonical đề nghị',
    'Root đã nghiệm thu19worlds, đóng bundle32outputs và cập nhật Chặng13 của hai báo cáo GVHD. Bản phân tích hiện hành')
text = text.replace('; bundle dự kiến ', '; bundle đã đóng ')
report.write_text(text, encoding='utf-8')
save(PREP / 'rq2_learned19_report_publication01.json', dict(
    draft_sha256=sha(draft), published_path=report.relative_to(ROOT).as_posix(),
    published_sha256=sha(report), changes='Chỉ cập nhật trạng thái closure/publication, giữ số liệu và giới hạn.'))

old_html = (PREP / 'supervisor-learned19-before01/BAO_CAO_NGHIEN_CUU.html').read_bytes()
new_html = (HUMAN / 'BAO_CAO_NGHIEN_CUU.html').read_bytes()
pattern = rb'<svg\b.*?</svg>'
old_figures, new_figures = re.findall(pattern, old_html, flags=re.S), re.findall(pattern, new_html, flags=re.S)
assert len(old_figures) == len(new_figures) == 11 and old_figures == new_figures
refined = json.loads((PREP / 'supervisor_learned19_refinement02.json').read_bytes())
assert {name: sha(HUMAN / name) for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html')} == refined['after_sha256']
qa = dict(status='ACCEPTED_CONTENT_DESKTOP_AND_MOBILE_COMPONENT_QA',
    desktop=dict(view_width=1280, section_width=1080, table_width=1080,
                 visual_file='supervisor_learned19_desktop03.png', root_viewed=True),
    mobile=dict(view_width=390, body_width=375, section_width=335,
                table_width=335, horizontal_overflow=False, rows=3,
                visual_file='supervisor_learned19_mobile05.png', root_viewed=True,
                scope='Full-document DOM sizing and isolated original-table component visual inspection, retained stylesheet.'),
    scientific_rows_added=0, svg_bytes_unchanged=11, tables=12, chapters=13,
    limitations='Không kiểm lại thị giác toàn bộ11hình cũ trong lượt này; chỉ xác nhận bytes giữ nguyên.',
    failed_qa_preserved=dict(file_protocol_blocked=True, localhost_remote_route_timed_out=True,
        owned_preview_server_closed=True, server_session=2069, observed_terminal_exit_code=0,
        local_headless_chrome_exit_code=-2147483645, owned_local_browser_exited=True,
        mobile03_04_element_screenshots_wrong_clip=True,
        recovery='Chụp viewport của component bảng nguyên DOM/CSS, tránh lỗi crop element cao hơn viewport.'),
    owned_tabs_remaining=0, unrelated_tab0_closed=False, final_sha256=refined['after_sha256'])
save(PREP / 'supervisor_learned19_qa_review01.json', qa)

aliases = {}
for suffix, folder in [('before01', PREP / 'supervisor-learned19-before01'),
                       ('before02', PREP / 'supervisor-learned19-before02'), ('after', HUMAN)]:
    for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html'):
        aliases[suffix + '__' + name] = folder / name
for name in ('update_supervisor_learned19_01.py', 'refine_supervisor_learned19_02.py',
             'supervisor_learned19_update01.json', 'supervisor_learned19_refinement02.json',
             'supervisor_learned19_qa_review01.json', 'preview_supervisor_learned19_01.py',
             'supervisor_learned19_preview01.stop', 'render_supervisor_learned19_01.ps1',
             'supervisor_learned19_desktop01.render.json', 'supervisor_learned19_desktop01.stdout.log',
             'supervisor_learned19_desktop01.stderr.log', 'supervisor_learned19_desktop02.png',
             'supervisor_learned19_mobile02.png', 'supervisor_learned19_desktop03.png',
             'supervisor_learned19_mobile03.png', 'supervisor_learned19_mobile04.png',
             'supervisor_learned19_mobile05.png'):
    aliases[name] = PREP / name
inventory = [dict(copy=name, source=path.relative_to(ROOT).as_posix(),
                  bytes=path.stat().st_size, sha256=sha(path)) for name, path in aliases.items()]
save(PREP / 'supervisor_learned19_copy_inventory_before01.json', inventory)
sys.path.insert(0, str(ROOT / 'src'))
from knowledge_tracing.evidence import record_evidence_run, verify_evidence_bundle
note = ('# Chặng13 — đối chứng nguồn đồ thị và nhóm năng lực\n\n'
    'Giữ hai bản người đọc trước/sau và quá trình chỉnh bảng mobile, cùng ảnh gốc QA. '
    'Số liệu nghiên cứu đến từ bundle learned19 riêng; QA không tạo thêm mẫu. '
    'Root đã xem desktop03 và mobile05. Mobile05 là component bảng với DOM/CSS gốc; '
    'full document có sizing DOM riêng. Các crop lỗi và lỗi Chrome/preview được giữ. '
    '11SVG cũ giữ exact bytes. Mọi tab/server thuộc lượt kiểm đã đóng.\n')
with record_evidence_run(ROOT, QA_RUN, metadata=dict(kind='SUPERVISOR_REPORT_PRESENTATION_QA',
        scientific_new_N=0, research_bundle=RUN, root_viewed=True),
        sources=[*aliases.values(), ROOT / RUN / 'manifest.json',
                 PREP / 'supervisor_learned19_copy_inventory_before01.json', Path(__file__).resolve()], note=note) as out:
    for row in inventory:
        source = ROOT / row['source']
        assert sha(source) == row['sha256']
        with (out / row['copy']).open('xb') as stream:
            stream.write(source.read_bytes())
        assert sha(source) == sha(out / row['copy']) == row['sha256']
    save(out / 'copy_inventory.json', inventory)
    (out / 'publication_builder.py').write_bytes(Path(__file__).read_bytes())
verified = verify_evidence_bundle(ROOT / 'research_tracking/runs' / QA_RUN)
print(json.dumps(dict(status='PUBLISHED_AND_QA_BUNDLE_CLOSED', report_sha256=sha(report),
    qa_outputs=verified['artifacts'], qa_manifest_sha256=sha(ROOT / 'research_tracking/runs' / QA_RUN / 'manifest.json'))))
