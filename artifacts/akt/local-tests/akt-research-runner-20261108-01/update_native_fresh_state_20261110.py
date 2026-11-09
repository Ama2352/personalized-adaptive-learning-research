"""Đồng bộ nghiệm thu actual CPU và phép đối chứng đầy đủ, giữ goal toàn KLTN."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


native_path = PREP/'graph-checkpoint-native08-owned/final.json'
native = read(native_path)
model_path = PREP/'gkt-research-model02-owned/final.json'
trainer_path = PREP/'gkt-research-training02-owned/final.json'
model,trainer = read(model_path),read(trainer_path)
recovery_path = PREP/'rq2-fresh-graph-recovery03-outer/final.json'
recovery = read(recovery_path)
assert native['counts']['tests'] == 18 and model['counts']['tests'] == 11 and trainer['counts']['tests'] == 8
assert recovery['status'] == 'ACCEPTED59_RECOVERY_COMPLETE_PRIMARY120_NO_INFERENCE'
state_path = ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state = read(state_path)
state['overnight_session_20261110'] = dict(user_request='Tiếp tục5giờ khiuserngủ, không phụ thuộc manualaccept.',
    requested_at_utc='2026-11-09T17:07:21Z', requested_until_utc='2026-11-09T22:07:21Z',
    permitted='Safe local engineering và bounded operations trong quyền đã giao.',
    external_approval_work='Không dispatch cloud/paid/fullCV/Holdout hoặc thay phương pháp chưaduyệt; chuyển task độc lập.')
state['native08_preparation_20261110']['status'] = 'ACTUAL_18_PASS_CURRENT_SOURCE_CPU_ONLY'
state['native08_preparation_20261110']['receipt_sha256'] = sha(native_path)
state['native08_preparation_20261110']['bundle'] = 'research_tracking/runs/akt-cpu-checkpoint-current-20261110-01'
state['GKT_actual_model_trainer_20261110'] = dict(status='MODEL11_TRAINER8_ACTUAL_PASS_NOT_FITTED',
    model_receipt_sha256=sha(model_path),trainer_receipt_sha256=sha(trainer_path),
    bundle='research_tracking/runs/gkt-research-model-trainer-20261110-01',
    checkpoint='Candidate source-reviewed, applied/native status track separately.',fitted_baseline=False)
state['RQ2_fresh_recovery_actual_20261110'] = dict(status='PRIMARY120_ACCEPTED_DESCRIPTIVE_ANALYSIS_PUBLISHED',
    receipt_sha256=sha(recovery_path),primary_worlds=120,primary_responses=14400,
    physical_constructors=121,physical_responses=14430,paired_blocks=10,
    conditional_contrasts=30,graph_source_contrasts=60,trajectory_pairs=60,
    question_id_differences=4936,ordinal_positions=7200,
    inference='Mô tả, chưa CI/pvalue. HighK0 là source-known inactive negativecontrol.',
    bundles=['research_tracking/runs/rq2-fresh-graph-recovery-20261110-01',
             'research_tracking/runs/rq2-fresh-graph-source-analysis-20261110-01'],
    human_report='research_tracking/supervisor_reports/2026-11-10/01_tien_do',
    RQ_complete=False)
state['goal_turn_previous_classification_20261110'] = 'PROGRESS_NATIVE18_GKT19_FRESH120_AND_REPORT_PUBLICATION'
state['next_recommended_investigation'] = ('Hoàn tất final spacing QA và commit fresh120 báo cáo10/11. '
    'GKT checkpoint28 sau source review/AST/guards. GRAPH29 cần actual publicproducer parity, '
    'genuine currentGate và ROOT closedengineering auth, không dùng handmade mocks làm authority. '
    'Sau đó Linux/CUDA Colab khiusercóthểkếtnối. Không chiModal.')
write(state_path,state)
task_path = ROOT/'docs/thesis_recovery/TASKS.json'
tasks = read(task_path)
for task in tasks['tasks']:
    if task['id'] == 'GRAPH29':
        task['status'] = 'COLD299_NATIVE18_PASS_PUBLIC_PRODUCER_RESUME_PENDING'
        task['blockers'] = ['Genuine currentGate/engineering authorization và actual normal-entry producer pause/resume parity còn thiếu. Native18 là checkpoint/stopping fixture, chưa publicproducer. Crash/CUDA cần bằng chứng riêng.']
    if task['id'] == 'GKT08':
        task['status'] = 'MODEL11_TRAINER8_PASS_CHECKPOINT_PRODUCER_ADAPTER_PENDING'
        task['blockers'] = ['Checkpoint28 chưa native; research producer/export/adaptor/fit còn thiếu.']
        task['verification_evidence'] = 'research_tracking/runs/gkt-research-model-trainer-20261110-01'
    if task['id'] == 'RQDIAG29':
        task['status'] = 'COMPLETED_PRIMARY120_REPLICATION_DESCRIPTIVE_ONLY'
        task['blockers'] = []
        task['completion_evidence'] = 'research_tracking/runs/rq2-fresh-graph-recovery-20261110-01'
        task['actual_counts'] = dict(primary_worlds=120,primary_responses=14400,
            physical_constructors=121,physical_responses=14430,paired_blocks=10)
if not any(t['id']=='WRITE08' for t in tasks['tasks']):
    tasks['tasks'].append(dict(id='WRITE08',rq=['RQ1','RQ2'],workstream='research_reporting',priority='P0',
        owner='Codex',dependencies=['RQDIAG29'],research_objective='Xuất bản đối chứng fresh120 với diễn giải negativecontrol và khác biệtsoE9.',
        required_inputs='Actual recoveredprimary120,60Q/30K, independentreviewd75d20ff.',
        files_components=['research_tracking/reports/rq2_fresh_graph_source_replication_20261110.md',
            'research_tracking/supervisor_reports/2026-11-10/01_tien_do'],
        implementation_objective='Technicalreport và hai fileGVHD theo ngày, giữ11SVG, bảng mô tả3nhóm và claims scoped.',
        acceptance_criteria='K/signs/60trajectory4936/7200 có source, pairedblockunit10, khôngcausalhuman/inferenceclaim, desktop/mobile QA.',
        verification_steps='Root số học+independentreview, static14tables/11SVG/uniqueIDs, finalspacingvisualQA.',
        required_artifacts=['research_tracking/runs/rq2-fresh-graph-source-analysis-20261110-01'],
        estimated_work='Chưa đo effort riêng, không thêmmodelcalls từ phân tích.',compute_cost_category='local_CPU_no_cloud',
        authorization_requirements='User giao boundedCPUdiagnostics và báo cáo, không đổi protocol.',
        status='PUBLISHED_FINAL_SPACING_QA_PENDING',blockers=[]))
write(task_path,tasks)
for filename,links in (
    ('docs/REPOSITORY_MAP.md',('../research_tracking/','../research_tracking/')),
    ('research_tracking/reports/README.md',('../','../')),
    ('research_tracking/EVIDENCE_INDEX.md',('','')),
    ('research_tracking/supervisor_reports/README.md',('../','')),
):
    path = ROOT/filename
    first,rest = path.read_text(encoding='utf-8').split('\n',1)
    prefix = links[0]
    human_prefix = ('../research_tracking/' if filename.startswith('docs/') else
                    '../' if filename=='research_tracking/reports/README.md' else '')
    if filename=='research_tracking/supervisor_reports/README.md':
        human_link='2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html'
    else:
        human_link=human_prefix+'supervisor_reports/2026-11-10/01_tien_do/BAO_CAO_NGHIEN_CUU.html'
    note = ('\n\n## Cập nhật10/11 — đối chứng đủ120ca và nghiệm thu CPU\n\n'
        f'[Báo cáo hiện hành10/11]({human_link}) có Chặng15 và bảng fresh10blocks, giữ đợt09/11. '
        f'[Recovery]({prefix}runs/rq2-fresh-graph-recovery-20261110-01/README.md) đã đủprimary120/14400, '
        'physical121/14430 gồm replay30. K1000 có6dương/4âm, K1150 có8dương/2âm, K1300zero10 là đối chứngbất hoạt. '
        f'[AKT native18]({prefix}runs/akt-cpu-checkpoint-current-20261110-01/README.md) và '
        f'[GKT model11/trainer8]({prefix}runs/gkt-research-model-trainer-20261110-01/README.md) đều0FES/Job0. '
        'Publicproducerresume/CGAKTresearchfit/CUDA và suy luận thống kê vẫn còn riêng. Không chiModal.\n')
    path.write_text(first+note+rest,encoding='utf-8')
with (ROOT/'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a',encoding='utf-8') as stream:
    stream.write('\n\n## 10/11 — native và replication đã tiến qua actualexecution\n\n'
        'RAM5GiB ổn định cho phép chạy tuần tự nativeAKT18 đạt25,9s, RQ2recovery59 đạt30,9s và GKTmodel11/trainer8 đạt18,1s/34,4s. '
        'Tất cảsource/runtime vàownedcleanup đạt. Đã đóng ba bundles kỹ thuật. Fresh120 có independentdescriptive review, '
        'báo cáo10/11 đã xuất bản với11SVG/14tables, finalspacingQA còn chờ. '
        'Không cộngtestNN vàoNnghiên cứu, khônghuman causal/inference hoặcfullRQcompletion. '
        'User yêu cầu tiếp tục5h từ17:07UTC, trạng tháighiđủđểcontinuation.\n')
print('ACTUAL_NATIVE_AND_REPLICATION_STATE_UPDATED')
