"""Đóng evidence nhỏ từ native tests và recovery, giữ traces/checkpoints gốc."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def small_files(directory):
    return [p for p in directory.rglob('*') if p.is_file()
            and p.suffix in ('.json', '.jsonl', '.xml', '.log', '.md')
            and 'runtime-temp' not in p.parts and p.stat().st_size <= 1024**2]


def archive(name, sources, details, note):
    bundle = ROOT / 'research_tracking/runs' / name
    bundle.mkdir(exist_ok=False)
    sources = list(dict.fromkeys([*sources, Path(__file__).resolve()]))
    inventory = {p.relative_to(ROOT).as_posix(): dict(sha256=sha(p), bytes=p.stat().st_size) for p in sources}
    write(bundle / 'inventory_before_copy.json', inventory)
    for source in sources:
        relative = source.relative_to(ROOT)
        if source.is_relative_to(PREP):
            relative = Path('execution') / source.relative_to(PREP)
        destination = bundle / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert sha(destination) == inventory[source.relative_to(ROOT).as_posix()]['sha256']
    write(bundle / 'acceptance.json', details)
    (bundle / 'README.md').write_text(note + '\n', encoding='utf-8')
    write(bundle / 'manifest.json', dict(kind=details['kind'], input_inventory=inventory,
        outputs_sha256={p.relative_to(bundle).as_posix(): sha(p) for p in bundle.rglob('*') if p.is_file()}))
    print(name, 'CLOSED', len(inventory), 'inputs')


native = read(PREP / 'graph-checkpoint-native08-owned/final.json')
assert native['status'] == 'ACCEPTED_CPU_CHECKPOINT_BATCHB_NATIVE18_NOT_CUDA_OR_RESEARCH_FIT'
assert native['counts'] == dict(tests=18, failures=0, errors=0, skipped=0)
assert native['source_before'] == native['source_after']
assert native['owned_receipt']['cleanup_accepted'] and native['owned_receipt']['job_active_after_cleanup'] == 0
child = read(PREP / 'graph-checkpoint-native08/result.json')
assert child['runtime_before'] == child['runtime_after']
archive('akt-cpu-checkpoint-current-20261110-01',
    small_files(PREP/'graph-checkpoint-native08') + small_files(PREP/'graph-checkpoint-native08-owned')
    + [PREP/name for name in ('check_graph_checkpoint_native08.py', 'run_graph_checkpoint_native08.py',
        'graph_checkpoint_native08_allocation.json', 'GRAPH_CHECKPOINT_NATIVE08_HANDOFF01.md')],
    dict(kind='CPU_native_checkpoint_and_stopper_regression', counts=native['counts'],
        native_counts=native['native_counts'], resources=child['resources'],
        elapsed_seconds=native['elapsed_seconds'], source_stable=True, runtime_stable=True,
        CPU_native_only=True, public_producer_resume_verified=False, CUDA_verified=False),
    '# AKT checkpoint theo nguồn hiện hành\n\n18ca đạt0FES, gồm16checkpoint và2stopper. '
    'Có actual2model constructors/6forward/4Adam/7save/8load và phục hồi3RNG/modulemodes trên fixture dựng sẵn. '
    'Source/runtime trước–sau khớp, owned Job0. Chưa public producer continuous/resume parity hoặc CUDA/researchfit. '
    'Payload engineering ở vị trí test gốc, các receipt/source hashes giữ trong bundle. Không sửa kết quả cũ.')

recovery_path = PREP / 'rq2-fresh-graph-recovery03-outer/final.json'
recovery = read(recovery_path)
assert recovery['status'] == 'ACCEPTED59_RECOVERY_COMPLETE_PRIMARY120_NO_INFERENCE'
assert recovery['error'] is None and recovery['source_input_before_sha256'] == recovery['source_input_after_sha256']
assert recovery['owned_receipt']['cleanup_accepted'] and recovery['owned_receipt']['job_active_after_cleanup'] == 0
native_dir = ROOT / 'experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03'
summary = read(native_dir/'summary.json')
assert (summary['primary_worlds'], summary['primary_responses'], summary['components'], summary['contrasts']) == (120,14400,60,30)
assert (summary['physical_constructors'], summary['physical_response_calls']) == (121,14430)
archive('rq2-fresh-graph-recovery-20261110-01',
    small_files(PREP/'rq2-fresh-graph-recovery03-outer')
    + small_files(PREP/'rq2-fresh-graph-recovery03-owned')
    + [PREP/name for name in ('worker_rq2_fresh_graph_recovery03.py','run_rq2_fresh_graph_recovery03.py',
        'rq2_fresh_graph_recovery03_plan.json')]
    + [p for p in small_files(native_dir) if not p.name.startswith('initial-')],
    dict(kind='recovered_fresh_simulation_replication_no_inference', summary=summary,
        outer_sha256=sha(recovery_path), elapsed_seconds=recovery['elapsed_seconds'],
        source_input_stable=True, primary_blocks=recovery['primary_predeclared_scientific_blocks'],
        no_human_causal_claim=True, raw_output_sha256=recovery['outputs_sha256']),
    '# RQ2 khôi phục phép đối chứng đủ120ca\n\nGiữ61ca parent và thực hiện59ca còn thiếu, '
    'kiểm chính xác initial snapshot cùng30bước prefix củaF062 trước bước31. '
    'Primary120worlds/14400responses tách khỏi physical121constructors/14430responses, gồm30lượt replay. '
    'Không thêmRNG draws, giữ10base/U đã chuẩn bị của các block21010–21019. '
    'Bundle giữ logs và kết quả nhỏ. Rawtraces/initialstates vẫn ở native experiments path và manifest hashes. '
    'Failure parent giữ nguyên, không xóa/ghi lại artifacts cũ. '
    'Acceptance là đầy đủ và đúng hợp đồng; thống kê suy luận và kết luận RQ còn cần phân tích riêng.')
