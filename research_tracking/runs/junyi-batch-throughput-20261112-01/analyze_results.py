"""Đối chiếu bốn phép đo và dựng figure từ receipt GPU đã nghiệm thu."""
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
NATIVE = ROOT / 'experiments/akt/results/modal-junyi-batch-throughput-t4-20261112-01'
receipt = json.loads((NATIVE / 'receipt.json').read_text())
assert receipt['status'] == 'JUNYI_BATCH_PROFILE_COMPLETE'
assert receipt['download_inventory_verified'] is True
assert json.loads((NATIVE / 'app-budget-guard.json').read_text())['stop_acknowledged']
with (NATIVE / 'artifacts.zip').open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == receipt['archive_sha256']
cases = receipt['worker_result']['cases']
assert [row['actual_benchmark_batch_size'] for row in cases] == [4, 8, 16, 32]
assert len({row['initial_backbone_sha256'] for row in cases}) == 1
assert sum(row['optimizer_steps'] for row in cases) == 480
assert all(row['targets'] == 56332 and row['valid_tokens'] == 100032
           and row['fresh_reload_first_window_exact'] for row in cases)
rows = []
for case in cases:
    rows.append(dict(
        batch=case['actual_benchmark_batch_size'],
        optimizer_steps=case['optimizer_steps'],
        targets=case['targets'],
        seconds=case['full_training_wall_seconds'],
        targets_per_second=case['targets_per_second'],
        speedup_full=case['targets_per_second'] / cases[0]['targets_per_second'],
        speedup_exclude_first=case['exclude_first_batch_targets_per_second']
        / cases[0]['exclude_first_batch_targets_per_second'],
        peak_vram_mib=case['cuda_resource']['max_memory_allocated'] / 1024**2,
    ))
with (BUNDLE / 'figure-data.csv').open('x', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(BUNDLE / 'analysis.json').write_text(json.dumps(dict(
    status='VERIFIED_ENGINEERING_PROFILE', rows=rows,
    protocol_changed=False, full_junyi_epoch=False,
    limits_vi='Một lượt mỗi batch trên packet. Batch4 chịu warmup đầu tiên. '
              'Có số đo bỏ batch đầu, chưa đo time-to-quality hoặc hội tụ. '
              'Nhóm batch thay số cập nhật và quỹ đạo Adam. Không ngoại suy trực tiếp toàn training.',
), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Quy ước figures4papers, Chen Liu, CC BY-NC 4.0, nguồn ghim ở bundle figure gốc.
os.environ['MPLCONFIGDIR'] = str(ROOT / 'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'svg.fonttype': 'none', 'axes.spines.top': False,
                     'axes.spines.right': False})
figure, axis = plt.subplots(figsize=(8.2, 4.5), layout='constrained')
axis.bar(range(4), [row['targets_per_second'] / 1000 for row in rows],
         color=['#3c6e82', '#3c6e82', '#3c6e82', '#8f3d3d'])
axis.set_xticks(range(4), [str(row['batch']) for row in rows])
axis.set_xlabel('Số cửa sổ trong batch')
axis.set_ylabel('Nghìn target / giây')
axis.set_ylim(0, 23)
axis.set_title('Junyi trên T4 — thông lượng packet 56.332 target', loc='left', pad=16)
for index, row in enumerate(rows):
    axis.text(index, row['targets_per_second'] / 1000 + .5,
              f"{row['targets_per_second'] / 1000:.2f}", ha='center')
figure.text(.5, .005, 'Một lượt mỗi batch, gồm batch đầu. Chưa đo số epoch để đạt chất lượng.',
            ha='center', fontsize=9)
for extension in ('svg', 'pdf', 'png'):
    target = BUNDLE / ('batch-throughput.' + extension)
    assert not target.exists()
    figure.savefig(target, dpi=160, bbox_inches='tight')
plt.close(figure)
print(json.dumps(dict(status='PASS', rows=rows), ensure_ascii=False))
