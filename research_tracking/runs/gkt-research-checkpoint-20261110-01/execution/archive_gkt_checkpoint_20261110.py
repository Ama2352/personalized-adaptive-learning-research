"""Đóng nghiệm thu checkpoint GKT28, giữ payload tại basetemp gốc."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT/'research_tracking/runs/gkt-research-checkpoint-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


outer_path = PREP/'gkt-research-checkpoint01-owned/final.json'
outer = json.loads(outer_path.read_bytes())
child = outer['child_result']
assert outer['status']=='ACCEPTED_GKT28_CPU_EPOCH_CHECKPOINT_NOT_LIFECYCLE_FIT'
assert outer['counts']==dict(tests=28,failures=0,errors=0,skipped=0)
assert outer['source_before']==outer['source_after'] and outer['runtime_before']==outer['runtime_after']
assert outer['owned_receipt']['cleanup_accepted'] and outer['owned_receipt']['job_active_after_cleanup']==0
phases = child['phase_proofs']
assert len(phases)==3
for name in ('model_state_after','owned_rng_sha256','adam_sha256','cumulative_counters'):
    assert phases[1][name]==phases[2][name],name
assert child['counters']['actual_optimized_target_exposures']==96
assert child['counters']['adam_step_returned']==6
files = []
for name in ('gkt-research-checkpoint01','gkt-research-checkpoint01-owned','gkt-research-checkpoint-apply01'):
    directory=PREP/name
    files.extend(p for p in directory.rglob('*') if p.is_file() and 'runtime-temp' not in p.parts
        and p.suffix in ('.json','.jsonl','.xml','.log','.py'))
files += [PREP/name for name in ('check_gkt_research_checkpoint01.py','run_gkt_research_checkpoint01.py',
    'gkt_research_checkpoint01_packet.json','GKT_RESEARCH_CHECKPOINT_NATIVE01_HANDOFF.md',
    'GKT_RESEARCH_CHECKPOINT_CANDIDATE01_HANDOFF.md')]
files += [ROOT/'src/knowledge_tracing/gkt/research_checkpoint.py',ROOT/'tests/gkt/test_research_checkpoint.py',
    Path(__file__).resolve()]
BUNDLE.mkdir(exist_ok=False)
write(BUNDLE/'inventory_before_copy.json',{p.relative_to(ROOT).as_posix():sha(p) for p in files})
for source in files:
    relative=source.relative_to(ROOT)
    if source.is_relative_to(PREP):
        relative=Path('execution')/source.relative_to(PREP)
    target=BUNDLE/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    assert sha(source)==sha(target)
write(BUNDLE/'acceptance.json',dict(kind='GKT_CPU_complete_epoch_checkpoint',counts=outer['counts'],
    outer_sha256=sha(outer_path),elapsed_seconds=outer['elapsed_seconds'],
    native_counters=child['counters'],resources=child['resources'],
    control_and_restored_next_epoch_exact=True,cumulative_budget_origin_preserved=True,
    same_process_only=True,public_producer_resume=False,fitted_baseline=False))
(BUNDLE/'README.md').write_text('# GKT checkpoint cuối vòng huấn luyện đã nghiệm thu\n\n'
    '28ca đạt0FES, gồm save/restore và các artifact bị sửa có chứng thực lại. '
    'Hai model/Adam,6forward/updates và96target exposures là workload thực. '
    'Sau restore, vòng kế tiếp khớp model/BN, Adam, owned RNG và cumulative counters với control. '
    'Đã kiểm trước mutation và poisoned state khi mutation lỗi, giữ caller RNG. '
    'Source/runtime khớp và Job0. Phạm vi same-process/same-budget-origin, '
    'chưa publicproducer/freshOS/crash/CUDA hoặc fitted baseline. Payload vẫn ở basetemp pipeline, không đưa vàoGit.\n',encoding='utf-8')
write(BUNDLE/'manifest.json',dict(kind='GKT_checkpoint_engineering',
    outputs_sha256={p.relative_to(BUNDLE).as_posix():sha(p) for p in BUNDLE.rglob('*') if p.is_file()}))
state_path=ROOT/'docs/thesis_recovery/INVESTIGATION_STATE.json'
state=json.loads(state_path.read_bytes())
state['GKT_actual_model_trainer_20261110']['checkpoint']='ACTUAL_28_PASS_SAME_PROCESS_EPOCH_BOUNDARY'
state['GKT_actual_model_trainer_20261110']['checkpoint_bundle']=BUNDLE.relative_to(ROOT).as_posix()
state['GKT_actual_model_trainer_20261110']['checkpoint_receipt_sha256']=sha(outer_path)
write(state_path,state)
task_path=ROOT/'docs/thesis_recovery/TASKS.json'
tasks=json.loads(task_path.read_bytes())
for task in tasks['tasks']:
    if task['id']=='GKT08':
        task['status']='MODEL11_TRAINER8_CHECKPOINT28_PASS_PRODUCER_ADAPTER_PENDING'
        task['blockers']=['Research producer/export/adaptor/fit còn thiếu. Checkpoint28 là same-process complete-epoch, chưa lifecycle/freshOS resume.']
write(task_path,tasks)
for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
    path=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'/name
    text=path.read_text(encoding='utf-8')
    old='GKT đã đạt 11 kiểm mô hình và 8 kiểm trainer trên dữ liệu dựng sẵn.'
    new=old+' Phần lưu và nạp trạng thái cuối vòng huấn luyện cũng đã qua 28 kiểm trên CPU, vòng học kế tiếp khớp đối chứng trong phạm vi đã kiểm.'
    assert text.count(old)==1
    path.write_text(text.replace(old,new),encoding='utf-8')
with (ROOT/'docs/thesis_recovery/INVESTIGATION_LOG.md').open('a',encoding='utf-8') as stream:
    stream.write('\n\n## 10/11 — checkpointGKT28 đã đạt\n\n'
        'Actual28/0FES trong12,38s, peakworker311156736B/Jobfamily322756608B/minfree5023895552B. '
        'Root đối chiếu E2control/restored model/BN/Adam/ownedRNG/counters exact. '
        'Bundle giữnguồn/cases/logs và sourceapply inventory. Chưa producer hoặcfreshOSresume. '
        'Hai fileGVHD10/11 đã cập nhật mốc kỹ thuật này, Chặng15/table/11SVG không đổi.\n')
print('GKT_CHECKPOINT28_BUNDLE_AND_STATE_CLOSED')
