"""Cập nhật backlog viết luận văn và thứ tự chẩn đoán theo bằng chứng đã có."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
task_path = ROOT / 'docs/thesis_recovery/TASKS.json'
tasks = json.loads(task_path.read_bytes())
assert not any(t['id'] == 'WRITE07' for t in tasks['tasks'])
for task in tasks['tasks']:
    if task['id'] == 'RQDIAG30':
        task['blockers'] = ['Phạm vi witness đã hoàn tất. Global panel và full replay là các task riêng, không suy RQ complete.']
        task['completion_evidence']['canonical_and_two_human_reports_updated'] = True
        task['completion_evidence']['status'] = 'ACCEPTED_FINITE_WITNESS_PUBLICATION_AND_QA_COMPLETE'
    if task['id'] == 'RQDIAG23':
        task['priority'] = 'P2'
        task['scheduling_decision_20261110'] = 'Chưa chạy lại full14400selectedreadouts trước khi đóng estimand/quần thể cho chẩn đoán mastery. Witness120 đã cho thấy selectionconditioning, mở rộng cùng kiểu mẫu riêng lẻ chưa giải quyết vấn đề đó. Giữ requirement và failure lịch sử, không xóa hoặc gán completed.'
tasks['tasks'].append(dict(id='WRITE07', rq=['RQ1', 'RQ2'], workstream='thesis_writing',
    priority='P0', owner='Codex', dependencies=['RQDIAG30', 'WRITE06'],
    research_objective='Đưa chẩn đoán on-policy mastery và initialization vào bản thảo luận văn.',
    required_inputs='Witness120 đã đóng và crosscheck độc lập, source interpretation review.',
    files_components=['research_tracking/reports/THESIS_RQ1_MECHANISMS_DRAFT_20261109.md'],
    implementation_objective='Nối E10 sau E9, giữ prefix52432bytes; làm rõ120lượt/22khái niệm trong báo cáo hiện hành.',
    acceptance_criteria='Các số120/22/1/0 có nguồn JSON, prefix cũ nguyên byte, giới hạn selector/initialability/uncertainty rõ. Không RQ completion.',
    verification_steps='Đối chiếu summary/crosscheck, SHA before/after và source review, independent prose review trước commit.',
    required_artifacts=['research_tracking/runs/thesis-rq1-e10-writing-20261110-01'],
    estimated_work='Effort chưa đo riêng, không model/world calls.', compute_cost_category='local_CPU_no_cloud',
    authorization_requirements='User giao viết luận văn và lưu bằng chứng, không đổi phương pháp.',
    status='PUBLISHED_NUMERIC_AND_PREFIX_VERIFIED_INDEPENDENT_REVIEW_PENDING', blockers=[]))
task_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
state_path = ROOT / 'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = json.loads(state_path.read_bytes())
state['thesis_E10_20261110'] = dict(status='PUBLISHED_PENDING_INDEPENDENT_PROSE_REVIEW',
    prefix_bytes_preserved=52432, new_model_calls=0,
    bundle='research_tracking/runs/thesis-rq1-e10-writing-20261110-01',
    wording_clarification='120lượt hỏi trên22khái niệm riêng biệt, một lịch sử.')
state['native08_preparation_20261110'] = dict(status='SOURCE_READY_NOT_DISPATCHED',
    worker_sha256='e5c713c0ce18a7be34745a1c664bdc325d4b9030db86935b2c4d678dfea5e1dc',
    outer_sha256='c95ee5cb0a4e7c707eda33a797ac5420fc24f3b40dc90fb5662c8be918e0dbf2',
    allocation_sha256='7fac9d95c6e25307e2352c349235af7b063c870531a787d0fec250caa319dea3',
    required_free_ram_bytes=4*1024**3, test_count=18)
state['RQDIAG23_priority_review_20261110'] = 'Giữ full replay chưa hoàn tất ởP2. Ưu tiên panel/estimand review và RQ2replication khi đủRAM, tránh mở rộng selected-onlytable mà chưa sửa câu hỏi đánh giá.'
state['goal_turn_previous_classification_20261110'] = 'PROGRESS_E10_PUBLISHED_AND_REQUIRED_MODEL_CHECKPOINT_IMPLEMENTATION_IN_PROGRESS'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
note = '\n\n## 10/11 — E10 nối chẩn đoán thành thạo vào bản thảo\n\n[Bundle viết E10](LINK) giữ before/after, source map và prefix52432bytes nguyên.120lượt hỏi trên22khái niệm của một lịch sử được làm rõ trong technicalreport và hai fileGVHD. Không thêmN/modelcall. Fullselectedreplay RQDIAG23 giữ chưa hoàn tất nhưng xuốngP2 vì mở rộng cùng mẫu policy-chọn chưa giải quyết selectionconditioning. Ưu tiên review estimand/panel và actualRQ2recovery khiRAMđủ. Không áp dụng phương pháp mới.\n'
for filename, link in (
    ('docs/REPOSITORY_MAP.md', '../research_tracking/runs/thesis-rq1-e10-writing-20261110-01/README.md'),
    ('research_tracking/reports/README.md', '../runs/thesis-rq1-e10-writing-20261110-01/README.md'),
    ('research_tracking/EVIDENCE_INDEX.md', 'runs/thesis-rq1-e10-writing-20261110-01/README.md'),
    ('docs/thesis_recovery/INVESTIGATION_LOG.md', '../../research_tracking/runs/thesis-rq1-e10-writing-20261110-01/README.md'),
):
    path = ROOT / filename
    text = path.read_text(encoding='utf-8')
    if filename.endswith('INVESTIGATION_LOG.md'):
        text += note.replace('LINK', link)
    else:
        first, rest = text.split('\n', 1)
        text = first + note.replace('LINK', link) + rest
    path.write_text(text, encoding='utf-8')
decision = ROOT / 'research_tracking/DECISION_LOG.md'
with decision.open('a', encoding='utf-8') as stream:
    stream.write('\n\n## DEC-PRIORITY-20261110 — giảm chạy lại chẩn đoán chưa đúng quần thể\n\n'
        'Root hạ ưu tiên RQDIAG23fullreplay sangP2 từ witness120 và review selection. Giữ nguyên task, failure và protocol chưa hoàn tất. '
        'Mở rộng14400readouts của các câu policy chọn riêng lẻ chưa cho globalmasteryaccuracy. '
        'Đây là thay thứ tự công việc trong quyền engineering, không đổi split/model/estimand đã duyệt, không bỏ baseline hoặc tự áp dụng panel mới. '
        'Nguồn là witness120, Chặng14 và E10. ActualRQ2replication/GKT/AKT acceptance vẫn cần resource guard trước dispatch.\n')
print('E10_TRACKING_173_TASKS_UPDATED')
