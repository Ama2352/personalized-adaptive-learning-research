"""Đóng parity public CPU, giữ checkpoint lớn tại output gốc."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[4]
PREP = Path(__file__).resolve().parent
BUNDLE = ROOT / 'research_tracking/runs/akt-public-selected-resume-20261110-01'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


control = read(PREP / 'graph29-a0-continuous01/outer-final.json')
parent = read(PREP / 'graph29-a0-pause5-02/outer-final.json')
child = read(PREP / 'graph29-a0-resume01/outer-final.json')
assert control['status'] == 'ACCEPTED_ACTUAL_TINY_A0_SELECTED_ONLY_ENGINEERING'
assert parent['status'] == 'ACCEPTED_ACTUAL_GRAPH29_PARENT_PAUSE5_SEALED'
assert child['status'] == 'ACCEPTED_ACTUAL_GRAPH29_INTENTIONAL_RESUME_PARITY_ONLY'
for payload in (control, parent, child):
    assert payload['error'] is None
    assert payload['owned_receipt']['cleanup_accepted'] and payload['owned_receipt']['job_active_after_cleanup'] == 0
parity = read(PREP / 'graph29-a0-resume01/actual-completion-check.json')
assert parity['exact_control_all_seven_epochs'] and parity['parent_prefix_verbatim']
assert parity['raw84_exports_byte_exact'] and parity['selected_epoch'] == 4
assert parity['restored_latest_epoch'] == 5 and parity['inherited_best_epoch'] == 4
assert parity['unexpected_crash_recovery_supported'] is False
paths = [path for path in PREP.iterdir() if path.is_file()
         and ('graph29' in path.name.lower()) and path.suffix in ('.py', '.json', '.md')]
for directory in PREP.iterdir():
    if directory.is_dir() and directory.name.startswith('graph29-a0-'):
        paths.extend(path for path in directory.rglob('*') if path.is_file()
                     and path.suffix in ('.json', '.jsonl', '.log', '.md', '.csv', '.xml'))
native_references = []
for suffix in ('continuous-engineering10x84-20261110-01',
               'pause5-engineering10x84-20261110-01',
               'pause5-engineering10x84-20261110-02',
               'resume-engineering10x84-20261110-01'):
    run_id = 'main-a0-graph29-' + suffix
    paths.extend(ROOT / f'experiments/akt/{kind}/{run_id}.json' for kind in ('configs', 'authorizations'))
    native = ROOT / 'experiments/akt/results' / run_id
    for path in native.rglob('*'):
        if path.is_file():
            native_references.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size, sha256=sha(path)))
            if path.suffix in ('.json', '.jsonl', '.csv', '.log'):
                paths.append(path)
paths.append(Path(__file__))
paths = sorted(set(paths))
assert not BUNDLE.exists()
inventory = []
for path in paths:
    assert path.is_file() and not path.is_symlink() and path.stat().st_size <= 4 * 1024**2
    relative = path.relative_to(ROOT).as_posix()
    target = relative if not path.is_relative_to(PREP) else 'execution/' + path.relative_to(PREP).as_posix()
    inventory.append(dict(source=relative, destination=target, bytes=path.stat().st_size, sha256=sha(path)))
assert sum(row['bytes'] for row in inventory) <= 24 * 1024**2
BUNDLE.mkdir()
write(BUNDLE / 'inventory_before_copy.json', inventory)
for row in inventory:
    target = BUNDLE / row['destination']
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / row['source'], target)
    assert sha(target) == row['sha256'] == sha(ROOT / row['source'])
write(BUNDLE / 'native_artifact_references.json', native_references)
write(BUNDLE / 'acceptance.json', dict(
    scope='PUBLIC_CPU_INTENTIONAL_COMPLETE_EPOCH_RESUME_ENGINEERING_ONLY',
    continuous_epochs=7, parent_epochs=5, latest_epoch=5, best_epoch=4,
    child_new_epochs=[6, 7], raw_selection_targets=84,
    all_seven_epochs_numerical_parity=True, best_exports_byte_exact=True,
    failed_parent01_worker_seconds=89.69250139995711, failed_parent01_outer_seconds=91.72829509997973,
    accepted_parent02_outer_seconds=parent['elapsed_seconds'], child_outer_seconds=child['elapsed_seconds'],
    planned_parent_charge_seconds=180, planned_child_cap_seconds=360,
    unexpected_fault_recovery=False, cuda_verified=False, fitted_main_matrix=False, modal_spent_usd=0))
(BUNDLE / 'README.md').write_text(
    '# AKT chạy tiếp qua public entry đã khớp đối chứng CPU\n\n'
    'Corpus engineering có8 train learners với672targets,1 selection learner với84targets và1calibration learner. '
    'Calibration không chọn epoch. Giữ nguyên cấu hình d256 và seed42. Control hoàn tất7epochs, best4. '
    'Parent02 dừng sauepoch5, latest5 khácbest4 và stale1. Child nạp latest5 qua guard/inspector thật, '
    'chạy2epochs tiếp theo rồi xuất84targets từbest4. Cả7history receipts/loss/selection summaries khớp control, '
    'ba file raw selection khớp nguyên byte. Parent vàchild đều Job0, nguồn/runtime không đổi.\n\n'
    'Giữ lỗi import trướcGO và assertion thư mục rỗng của lượt01, gồm chi phí10updates3360targets đã tiêu. '
    'Lượt01 không seal và không được dùng để resume. Checkpoint lớn giữ nguyên ở experiments/akt/results, '
    'inventory tham chiếu giữ SHA vàsize, không sao chép tensor vào bundle.\n\n'
    'Đã nghiệm thu intentional complete-epoch resume trên Windows CPU trong corpus nhỏ. '
    'Unexpected fault/partial epoch, fresh Linux/CUDA, cloud durability, full research matrix và Holdout còn riêng. '
    'Đây là bằng chứng kỹ thuật, chưa chứng minh ưu thế mô hình hoặc đóngRQ3. Không chi Modal.\n', encoding='utf-8')
outputs = {path.relative_to(BUNDLE).as_posix(): sha(path) for path in BUNDLE.rglob('*') if path.is_file()}
write(BUNDLE / 'manifest.json', dict(kind='akt_public_cpu_selected_resume_actual_parity', outputs_sha256=outputs))
print(json.dumps(dict(bundle=str(BUNDLE), copied_inputs=len(inventory), copied_bytes=sum(row['bytes'] for row in inventory),
    native_artifact_references=len(native_references))))
