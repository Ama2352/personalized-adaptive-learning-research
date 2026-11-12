"""Nghiệm thu phép đo cùng batch và dựng hình từ artifact đã tải."""
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
NATIVE = ROOT/'experiments/akt/results/modal-junyi-step-sync-t4-20261112-01'
receipt = json.loads((NATIVE/'receipt.json').read_text())
assert receipt['status'] == 'JUNYI_STEP_SYNC_PROFILE_COMPLETE'
assert receipt['download_inventory_verified'] is True
assert json.loads((NATIVE/'app-budget-guard.json').read_text())['stop_acknowledged'] is True
with (NATIVE/'artifacts.zip').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['archive_sha256']
result = receipt['worker_result']
assert result['packet_state_pairs_exact'] == 3
assert result['actual_completed_case_updates'] == 1536
assert result['additional_synthetic_updates'] == 16
assert result['synthetic_equivalence']['status'] == 'PASS_EXACT_SYNTHETIC_EQUIVALENCE'
cases = result['cases']
assert len(cases) == 6 and len({row['initial_backbone_sha256'] for row in cases}) == 1
assert all(row['actual_benchmark_batch_size'] == 4 and row['targets'] == 56332
           and row['optimizer_steps'] == 256 and row['fresh_reload_first_window_exact']
           for row in cases)
with zipfile.ZipFile(NATIVE/'artifacts.zip') as archive:
    assert archive.testzip() is None
    inventory = json.loads(archive.read('SHA256.json'))
    assert set(archive.namelist()) == set(inventory) | {'SHA256.json'}
    for name, entry in inventory.items():
        with archive.open(name) as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == entry['sha256']
    name = next(name for name in inventory if name.endswith('/gpu-telemetry.jsonl'))
    raw = archive.read(name)
    (BUNDLE/'gpu-telemetry.jsonl').write_bytes(raw)
samples = [json.loads(line) for line in raw.splitlines() if line.strip()]
rows = []
for case in cases:
    selected = [sample for sample in samples if sample['phase']['variant'] == case['variant']
                and sample['phase']['repeat'] == case['repeat']]
    assert len(selected) >= 3, 'Insufficient GPU telemetry for a case'
    assert all(sample['exit_code'] == 0 for sample in selected)
    readings = [list(map(float, sample['gpu'].split(','))) for sample in selected]
    rows.append(dict(variant=case['variant'], repeat=case['repeat'],
                     targets=case['targets'], optimizer_steps=case['optimizer_steps'],
                     full_seconds=case['full_training_wall_seconds'],
                     exclude_first_seconds=case['exclude_first_batch_seconds'],
                     exclude_first_targets=case['exclude_first_batch_targets'],
                     targets_per_second=case['exclude_first_batch_targets_per_second'],
                     gpu_utilization_mean=statistics.mean(row[0] for row in readings),
                     vram_mib_mean=statistics.mean(row[1] for row in readings),
                     power_w_mean=statistics.mean(row[3] for row in readings),
                     gpu_samples=len(selected)))
pairs = []
for repeat in range(3):
    reference = next(row for row in rows if row['repeat'] == repeat and row['variant'] == 'reference')
    candidate = next(row for row in rows if row['repeat'] == repeat and row['variant'] == 'candidate')
    assert reference['exclude_first_targets'] == candidate['exclude_first_targets']
    ratio = reference['exclude_first_seconds'] / candidate['exclude_first_seconds']
    pairs.append(dict(repeat=repeat, speedup=ratio, time_reduction_fraction=1-1/ratio))
median = statistics.median(row['time_reduction_fraction'] for row in pairs)
accepted = median >= .05 and all(row['speedup'] > 1 for row in pairs)
summary = dict(status='ACCEPT_PACKET_OPTIMIZATION' if accepted else 'DO_NOT_ADOPT_FROM_PACKET',
               exact_cuda_state_pairs=3, rows=rows, pairs=pairs,
               median_time_reduction_fraction=median,
               next_requirement='Ghim nguồn và kiểm resume/pipeline trước áp dụng training chính.',
               limits_vi='Ba cặp packet trên một T4, chưa đại diện toàn epoch. GPU-Util lấy mẫu '
                         'có trễ và lẫn biên pha. Mức sử dụng GPU cao chưa xác lập tối ưu chi phí.')
with (BUNDLE/'figure-data.csv').open('x', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(BUNDLE/'analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

# Tiếp tục quy ước hình hiện có của figures4papers, Chen Liu, CC BY-NC 4.0.
os.environ['MPLCONFIGDIR'] = str(ROOT/'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.fonttype':'none',
                     'axes.spines.top':False, 'axes.spines.right':False})
figure, axes = plt.subplots(1, 2, figsize=(10, 4.5))
figure.subplots_adjust(left=.09, right=.98, top=.80, bottom=.25, wspace=.32)
for repeat in range(3):
    pair = [next(row for row in rows if row['repeat'] == repeat and row['variant'] == variant)
            for variant in ('reference', 'candidate')]
    axes[0].plot([0, 1], [row['targets_per_second']/1000 for row in pair], marker='o', label=f'Cặp {repeat+1}')
    axes[1].plot([0, 1], [row['gpu_utilization_mean'] for row in pair], marker='o')
for axis in axes:
    axis.set_xticks([0, 1], ['Hiện hành', 'Gom đồng bộ'])
    axis.set_xlim(-.2, 1.2)
axes[0].set_ylabel('Nghìn target / giây')
axes[0].set_title('Thông lượng, bỏ batch đầu', loc='left')
axes[0].legend(frameon=False)
axes[1].set_ylabel('GPU-Util trung bình (%)')
axes[1].set_ylim(0, 100)
axes[1].set_title('Mẫu nvidia-smi trong từng pha', loc='left')
figure.suptitle('AKT trên T4 — cùng batch4 và 56.332target mỗi lượt', x=.09, ha='left', fontsize=12)
figure.text(.09, .07, 'Ba cặp cùng khởi tạo và thứ tự dữ liệu. Model, Adam và RNG cuối cặp khớp tuyệt đối.\n'
            'Số đo packet phục vụ kỹ thuật, chưa xác lập tốc độ toàn epoch.', fontsize=9)
for extension in ('svg', 'pdf', 'png'):
    path = BUNDLE/('step-sync-profile.'+extension)
    assert not path.exists()
    figure.savefig(path, dpi=160)
plt.close(figure)
print(json.dumps(dict(status=summary['status'], median_time_reduction_fraction=median, pairs=pairs)), flush=True)
