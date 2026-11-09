"""Xuất tiến độ domain28 và cập nhật prose, giữ nguyên11figure hiện có."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == ROOT / '.venv'
assert sys.argv[1:] == ['--recover-preserved-newline-failure']
failure_path = PREP / 'domain-progress-newline-failure01/failure.json'
failure = json.loads(failure_path.read_bytes())
assert failure['status'] == 'PRESERVED_TEXTIO_NEWLINE_FAILURE_HUMAN_REPORTS_RESTORED_EXACT'
run = ROOT / 'research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01'
manifest_pin = 'a12e409be45a3c900154b2f7f1d1118bd2e3cda59a66476d6cb32b886da85131'
assert hashlib.sha256((run / 'manifest.json').read_bytes()).hexdigest() == manifest_pin
manifest = json.loads((run / 'manifest.json').read_bytes())
assert manifest['status'] == 'completed' and len(manifest['outputs_sha256']) == 28
for name, pin in manifest['outputs_sha256'].items():
    assert hashlib.sha256((run / name).read_bytes()).hexdigest() == pin
report_source = PREP / 'PAPER1_SEEDED_DOMAIN_SMOKE_READINESS_REPORT01.md'
source_raw = report_source.read_bytes()
assert hashlib.sha256(source_raw).hexdigest() == 'a9b64f662f0bb05a8bc0ac076638fa5a238cea59d26ae699db3d838ccd4ffd19'
report_path = ROOT / 'research_tracking/reports/paper1_seeded_domain_smoke_readiness_20261109.md'
role_path = ROOT / 'experiments/simulator/README.md'
for path in (report_path, role_path):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == failure['files'][path.relative_to(ROOT).as_posix()]['sha256']
base = ROOT / 'research_tracking/supervisor_reports/2026-11-09/01_tien_do'
human = [base / name for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html')]
tracking = [ROOT / name for name in ('docs/REPOSITORY_MAP.md', 'research_tracking/EVIDENCE_INDEX.md',
    'research_tracking/reports/README.md', 'docs/thesis_recovery/INVESTIGATION_STATE.json',
    'docs/thesis_recovery/INVESTIGATION_LOG.md')]
snapshot = PREP / 'domain-progress-before01'
assert snapshot.is_dir()
before = {path: path.read_bytes() for path in human + tracking}
state = json.loads(before[tracking[3]])
assert 'paper1_seeded_domain_smoke_20261109' not in state
assert state['autonomous_engineering_loop']['verified_new_output_blobs'] == 5978
figure_git = json.loads((ROOT / 'docs/thesis_recovery/evidence/supervisor_figures_raw_git_20261109.json').read_bytes())
assert figure_git['status'] == 'VERIFIED21_RAW_GIT_FILES_FOR11_FIGURES' and figure_git['files_checked'] == 21
inventory = json.loads((snapshot / 'inventory-before.json').read_bytes())
for index, (path, raw) in enumerate(before.items()):
    pin = hashlib.sha256(raw).hexdigest()
    target = snapshot / (str(index) + '__' + path.name)
    assert target.read_bytes() == raw
    assert inventory[path.relative_to(ROOT).as_posix()] == dict(bytes=len(raw), sha256=pin)
report = source_raw.decode('utf-8')
report = report.replace('Bundle nhỏ dự kiến `paper1-seeded-domain-smoke-engineering-20261109-01`',
    'Bundle nhỏ `paper1-seeded-domain-smoke-engineering-20261109-01` đã đóng28outputs và')
report = report.replace('Bản báo cáo này không tự xác nhận archive đã đóng.',
    'ROOT đã kiểm manifest đóng gói `' + manifest_pin + '` cùng toàn bộ28outputs.')
report = report.replace('Liên kết dùng vị trí canonical dự kiến', 'Vị trí canonical của bản diễn giải là')
assert report_path.read_text(encoding='utf-8') == report
old_sentence = 'Còn phải kiểm lượt chạy trên miền 28 khái niệm và hoàn thiện các chính sách so sánh trước thí nghiệm đầy đủ.'
new_sentence = ('Đã kiểm thêm một lượt trên miền 28 khái niệm và 84 câu, giữ cùng hồ sơ US và bộ số ngẫu nhiên theo lần luyện của từng khái niệm. '
    'Trong đúng lượt seed 42 này, hai nhánh đều dừng sau 172 tương tác khi bộ ước lượng đánh dấu đủ 28 khái niệm thành thạo. '
    'Đồ thị 25 cạnh có 0 lần quay lại chương, còn đồ thị 31 cạnh có 2 lần. Trạng thái kiến thức ẩn cuối của hai nhánh giống nhau. '
    'Ví dụ này nối được lập luận về quy tắc chương với một lượt chạy có đầy đủ dấu vết. '
    'Một cặp lượt chạy chưa xác định được thứ hạng đồ thị hoặc lợi ích học tập. '
    'Còn phải hoàn thiện các chính sách so sánh và kiểm các điều kiện làm thay đổi kết quả trước thí nghiệm đầy đủ.')
old_svgs = re.findall(rb'<svg\b.*?</svg>', before[human[1]], re.S)
assert len(old_svgs) == 11
for path in human:
    text = before[path].decode('utf-8')
    assert text.count(old_sentence) == 1
    path.write_bytes(text.replace(old_sentence, new_sentence).encode('utf-8'))
html = human[1].read_bytes()
assert re.findall(rb'<svg\b.*?</svg>', html, re.S) == old_svgs
assert html.count(b'<table') == 11
ids = re.findall(rb'\bid="([^"]+)"', html)
assert len(ids) == len(set(ids)) and all(anchor in ids for anchor in re.findall(rb'href="#([^"]+)"', html))
figure_index = json.loads((ROOT / 'research_tracking/runs/supervisor-figures-20261109-01/figure_index.json').read_bytes())
assert [hashlib.sha256(raw).hexdigest() for raw in old_svgs] == [row['svg_sha256'] for row in figure_index['figures']]
proof = dict(status='DOMAIN_PROGRESS_PROSE_UPDATED_STATIC_CHECKED_FIGURES_UNCHANGED',
    before={path.name:inventory[path.relative_to(ROOT).as_posix()] for path in human},
    after={path.name:dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in human},
    scientific_source_manifest_sha256=manifest_pin, prose_only=True, svg_byte_identical=11,
    tables_unchanged=11, local_anchors_valid=True, new_browser_render=False,
    newline_failure_preserved=failure_path.relative_to(ROOT).as_posix(), restored_before_update=True,
    scope_vi='Chỉ thay một đoạn tiến độ trong mỗi file. Giữ toàn bộ11SVG đã QA; chưa render lại phần prose mới.')
proof_path = ROOT / 'docs/thesis_recovery/evidence/supervisor_domain_progress_update_20261109.json'
with proof_path.open('x', encoding='utf-8') as stream:
    json.dump(proof, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
additions = {
    tracking[0]: ('\n### Prospective domain28 đã kiểm tích hợp\n\n'
        '[Báo cáo](../research_tracking/reports/paper1_seeded_domain_smoke_readiness_20261109.md) '
        'và [bundle28](../research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01/README.md) '
        'giữ actual hai episode US/seed42. Output gốc ở experiments/simulator/results theo [vai trò](../experiments/simulator/README.md). '
        'Đã có344feedback,172mỗi nhánh, không matrix nghiên cứu hoặc suy ưu thế graph.\n'),
    tracking[1]: ('\n- [Paper1 domain28](reports/paper1_seeded_domain_smoke_readiness_20261109.md), '
        '[bundle28](runs/paper1-seeded-domain-smoke-engineering-20261109-01/README.md). '
        'Actual một profile/tape, hai continuity episodes B1/GA,172feedback mỗi nhánh, re-entry0/2. '
        '33pins giữ nguyên, family peak72.155.136B/Job0; chưa matrix hoặc hiệu quả học tập.\n'),
    tracking[2]: ('\n- [Kiểm tích hợp domain28 Paper1](paper1_seeded_domain_smoke_readiness_20261109.md) '
        'là engineering witness một cặp US/seed42, đã đóng28outputs. Không là tái lập số lịch sử hoặc benchmark graph.\n'),
    tracking[4]: ('\n\n## 09/11 — hai episode Paper1 trên miền28 đã được nghiệm thu\n\n'
        'Một prepare14.028events, hai continuity episodes B1/GA,344feedback tổng/172mỗi nhánh, select346. '
        'B1switch2/reentry0, GAswitch4/reentry2, cùng terminal latent identity và28estimated mastered. '
        'Actualwhole1,1570007s/35,33pins trước=sau, family peak72.155.136B, min free2.028.568.576B và Job0. '
        'Bundle28manifesta12e409b…da85131 giữ đủ10scientificoutputs/raw. Có README cho experiments/simulator. '
        'Hai báo cáo người đọc cập nhật prose, kiểm tĩnh anchors và giữ11SVG nguyên byte, chưa render prose mới. '
        'C8metadata01–04 vẫn0testbodies,05NO_GO RAM trước ownedlaunch. Fresh owned pycache prefix05 chỉ mới chuẩn bị, chưa chạy child. '
        'Tiếp theo kiểm chứng điều kiện concept-local invariance và finite-horizon/cap boundaries bằng bounded stdlib fixtures.\n'),
}
for path, addition in additions.items():
    assert path.read_bytes() == before[path]
    path.write_bytes(before[path] + addition.encode('utf-8'))
state_path = tracking[3]
state['paper1_seeded_domain_smoke_20261109'] = dict(status='VERIFIED_TWO_PROSPECTIVE_DOMAIN28_EPISODES_BUNDLE28',
    bundle=run.relative_to(ROOT).as_posix(), manifest_sha256=manifest_pin,
    report=report_path.relative_to(ROOT).as_posix(), outputs=28, logical_profiles=1,
    feedback=344, branch_feedback=dict(B1=172, GA=172), chapter_reentry=dict(B1=0, GA=2),
    same_terminal_latent=True, research_matrix=False, historical_reproduction=False,
    supervisor_update_proof=proof_path.relative_to(ROOT).as_posix())
state['current_focus_20261109']['rq2'] = ('Domain28/84 chạy hai continuity episodes,172mỗi nhánh/reentry0và2, cùng latent cuối. '
    'Một engineering witness, chưa matrix. Tiếp tục conditional localtrajectory theorem/finite-horizon-capped-gain controls.')
state['current_focus_20261109']['rq3'] = ('MainC8 applied/tests pending.01RAMstop,02guardread,03confirmedPytestNUL,04PYCguard,05NO_GO RAM trước launch. '
    '0testbodies; source05freshownedcache chưa được chạy child. Gate STALE/actualCUDA pending.')
fig = state['figure_preservation_20261109']
fig.update(status='VERIFIED_RAW_GIT21_WITH11_SVG', raw_git_proof='docs/thesis_recovery/evidence/supervisor_figures_raw_git_20261109.json')
loop = state['autonomous_engineering_loop']
assert loop['verified_new_output_blobs'] == 5978
loop['verified_new_output_blobs'] = 5999
loop['latest_verified_commit'] = '117b058f68e7d16259b8c067b25fd50205214c87'
state['current_next_step_20261109'] = ('Review/apply bounded concept-local-invariance fixtures qua public Paper1core; '
    'archive metadata01–05 đã dừng; metadata06 chỉ sau actual RAM thay đổi và Rootreview. '
    'C8/CPU checkpoint/current Gate/CUDA vẫn chưa nghiệm thu. Không cloud/fullCV/Holdout.')
state['next_recommended_investigation'] = state['current_next_step_20261109']
assert state_path.read_bytes() == before[state_path]
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status='PUBLISHED_DOMAIN_PROGRESS', raw_git_counter=5999,
    supervisor_prose_only=True, unchanged_figures=11, source_bundle_outputs=28)))
