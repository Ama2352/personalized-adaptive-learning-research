"""Đồng bộ tracker/backlog và hai bản GVHD từ bằng chứng đã có, không thêm thí nghiệm."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parents[4]
prep = Path(__file__).resolve().parent
out = prep / 'research-readiness-reconciliation01'
assert out.is_dir()
sha = lambda data: hashlib.sha256(data).hexdigest()
pdf_proof = json.loads((out / 'pdf-identity.json').read_bytes())
assert len(pdf_proof) == 3 and all(record['identical_bytes'] for record in pdf_proof)
bundle = 'research_tracking/runs/research-readiness-reconciliation-20261110-01'
paths = ['research_tracking/RESEARCH_GAPS.md', 'research_tracking/RESEARCH_PROGRESS.md',
    'docs/thesis_recovery/TASKS.json',
    'research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO.md',
    'research_tracking/supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html']
before = {}
for name in paths:
    data = (subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=root)
            if name in paths[:2] else (root / name).read_bytes())
    before[name] = data
    (out / ('before__' + name.replace('/', '__'))).write_bytes(data)

task_path = root / 'docs/thesis_recovery/TASKS.json'
data = json.loads(task_path.read_bytes())
ids = [task['id'] for task in data['tasks']]
assert len(ids) == len(set(ids)) == 178 and data['execution_authorized'] is False
updates = {
    'T01': ('PARTIALLY_VERIFIED_CANONICAL_PDF_IDENTITIES_REQUIREMENT_REVIEW_PENDING',
        ['docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md', bundle + '/README.md'],
        'Ba PDF chuẩn có mặt và khớp bytes file người dùng cung cấp; review đầy đủ requirements/owner/article còn riêng.'),
    'T07': ('PARTIALLY_VERIFIED_CPU_CHECKPOINT_EXPORT_AND_IO_UNEXPECTED_FAULT_PENDING',
        ['research_tracking/runs/akt-public-selected-resume-20261110-01/README.md',
         'research_tracking/runs/nine-file-scaling-20261110-01/README.md'],
        'Có CPU best exports, complete-epoch resume và file IO; không đóng failure Task14/Junyi hoặc cloud recovery.'),
    'T12': ('PARTIALLY_VERIFIED_TRAIN48_METHOD24_CONDITIONS_MAIN_EDGE_EVALUATION_PENDING',
        ['research_tracking/runs/main60-graph-condition-binding-20261110-01/README.md'],
        'Sáu condition Main60 đã bind artifact train48; edge-confidence quality/oracle separation/evaluation chính còn thiếu.'),
    'T17': ('PARTIALLY_VERIFIED_SELECTED_CPU_ENGINEERING_MAIN_FIT_AND_ONLINE_PENDING',
        ['research_tracking/runs/sakt-selected-engineering-20261110-01/README.md'],
        'SAKT có actual selected CPU6epochs/best1/full84exports, chưa main fits/online comparator đầy đủ.'),
    'T18': ('PARTIALLY_VERIFIED_SELECTED_CPU_ENGINEERING_MAIN_FIT_AND_ONLINE_PENDING',
        ['research_tracking/runs/gkt-selected-engineering-20261110-01/README.md'],
        'GKT có actual selected CPU11epochs/best6/full84exports, chưa main fits/online comparator đầy đủ.'),
    'GRAPH12': ('PARTIALLY_VERIFIED_FOUR_ENGINEERING_PRODUCERS_NINE_MAIN_RECEIPTS_PENDING',
        ['research_tracking/runs/selected-operation-reconciliation-20261110-01/README.md'],
        'Bốn controller engineering đã đối chiếu; chưa đủ9Main selected receipts, không cấp refit.'),
    'GRAPH13': ('PARTIALLY_VERIFIED_NINE_FILE_STATISTICS_SCALED1260_CLOSED_FREEZE_PENDING',
        ['research_tracking/runs/nine-selected-file-statistics-20261110-01/README.md',
         'research_tracking/runs/nine-file-scaling-20261110-01/README.md'],
        'Reader/metadata/rows/accumulator/kernel đã nối bằng fixtures; còn independent operation review, late-failure và publication.'),
    'T23': ('IN_PROGRESS_E13_EVIDENCE_BOUND_DRAFT_FINAL_THESIS_AND_ARTICLE_PENDING',
        ['research_tracking/runs/thesis-rq1-e13-full-panel-20261110-01/README.md'],
        'E13 đã nối vào bản thảo; chưa đủ thesis, bài báo hoặc defense package hoàn chỉnh.'),
}
changed = []
for task in data['tasks']:
    if task['id'] in updates:
        status, evidence, scope = updates[task['id']]
        changed.append(dict(id=task['id'], previous_status=task['status'], status=status,
                            evidence=evidence, verified_scope_and_remaining_vi=scope))
        task['status'] = status
        task['verification_update_20261110'] = changed[-1]
data['as_of'] = '2026-11-10'
data['last_evidence_audit'] = bundle
data['current_execution_owner'] = 'Codex Root, tuần tự, không subagent theo yêu cầu tiết kiệm tài nguyên'
data['current_execution_queue'] = [
    dict(id='GRAPH13', action_vi='Hoàn thiện đóng kết quả độc quyền và review late-failure trên fixtures',
         stop_before_vi='Actual final selection/refit khi chưa có grant và đủ9fit'),
    dict(id='T08', action_vi='Hoàn tất shared code rồi collect/Gate mới khi dư RAM4GiB; chuẩn bị máy Linux/CUDA',
         stop_before_vi='Không bỏ Gate hoặc tự dùng Modal'),
    dict(id='T16', action_vi='Kiểm và hoàn thiện producer Junyi theo split/vocabulary đã chốt',
         stop_before_vi='Không sửa split, dùng Holdout hoặc tự chạy fullCV'),
    dict(id='T20', action_vi='Chuẩn bị matrix noise/history/profile theo đề cương và controls đã có',
         stop_before_vi='Không chạy thí nghiệm ngoài authorization hoặc đổi phương pháp ngầm'),
    dict(id='T21', action_vi='Nối hợp đồng fitted models vào demo khi có artifact hợp lệ',
         stop_before_vi='Không coi viewer lịch sử là demo người học mới đã hoàn tất'),
    dict(id='T23', action_vi='Viết tiếp từ claim ledger đã đóng, giữ phân biệt evidence và giới hạn',
         stop_before_vi='Không tự gửi báo cáo hoặc claim ưu thế CG-AKT khi chưa có kết quả'),
]
assert all(item['id'] in ids for item in data['current_execution_queue'])
task_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

old_phrase = 'Bộ nghiệm thu tích hợp hiện hành đã đạt 1.913 ca'
new_phrase = 'Bộ nghiệm thu tích hợp tại mốc trước đã đạt 1.913 ca'
note = ('Để chuẩn bị thí nghiệm chính, nhóm đã kiểm cách ghép đầu ra của chín điều kiện so sánh '
    'trên dữ liệu giả ở quy mô 1.260 lượt trả lời. Bước này kiểm việc đối chiếu đúng người học, '
    'câu hỏi, lịch sử và nhãn, để kết quả sau huấn luyện có thể so sánh trên cùng quần thể. '
    'Bộ kiểm tổng thể cần chạy lại trên nguồn mới trước lượt GPU. Huấn luyện GPU chính thức, '
    'kiểm phục hồi khi lỗi bất ngờ và các so sánh neural trên corpus nghiên cứu vẫn còn phải thực hiện.')
md_name, html_name = paths[3:]
md = before[md_name].decode('utf-8')
html = before[html_name].decode('utf-8')
assert md.count(old_phrase) == html.count(old_phrase) == 1
md_anchor = '## Quá trình đã thực hiện'
assert md.count(md_anchor) == 1
html_anchor = 'chưa là kết quả so sánh SAKT trong thí nghiệm chính.</p></div>'
assert html.count(html_anchor) == 1
new_md = md.replace(old_phrase, new_phrase).replace(md_anchor, note + '\n\n' + md_anchor)
html_note = '<p>' + note + '</p>'
new_html = html.replace(old_phrase, new_phrase).replace(html_anchor, html_anchor + html_note)
svgs = lambda value: re.findall(r'<svg\b.*?</svg>', value, re.S)
assert len(svgs(html)) == 11 and svgs(html) == svgs(new_html)
assert html.count('<table') == new_html.count('<table') == 17
assert new_html.replace(html_note, '').replace(new_phrase, old_phrase) == html
assert new_md.replace(note + '\n\n', '').replace(new_phrase, old_phrase) == md
(root / md_name).write_text(new_md, encoding='utf-8')
(root / html_name).write_text(new_html, encoding='utf-8')

qa = dict(status='RECONCILED_TRACKERS_BACKLOG_AND_REPORT_TEXT_NO_NEW_EXPERIMENTS',
    tasks=178, changed_tasks=changed, execution_authorized=False, figures_unchanged=11, tables_unchanged=17,
    report_changes='Một đoạn tiến độ phần mềm, một cụm thời gian Gate; ngoài hai phép sửa HTML giữ nguyên byte text.',
    new_research_samples=0, new_model_calls=0, new_Holdout_access=False, modal_usd=0,
    visual_browser_review=False,
    files={name: dict(before_sha256=sha(before[name]), after_sha256=sha((root / name).read_bytes())) for name in paths})
(out / 'reconciliation.json').write_text(json.dumps(qa, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Reconciled14current gaps /8parent tasks, PDFs3same, reportSVG11/table17 unchanged, no researchN.')
