"""Dựng bản hình sửa khoảng cách chú thích, giữ nguyên bản đầu và CSV."""
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).parent
os.environ['MPLCONFIGDIR'] = str(ROOT / 'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Quy ước figures4papers, Chen Liu, CC BY-NC 4.0. Nguồn ghim trong bundle figure gốc.
with (BUNDLE / 'figure-data.csv').open(encoding='utf-8', newline='') as stream:
    rows = list(csv.DictReader(stream))
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'svg.fonttype': 'none', 'axes.spines.top': False,
                     'axes.spines.right': False})
figure, axis = plt.subplots(figsize=(8.2, 5.2))
figure.subplots_adjust(left=.12, right=.98, top=.86, bottom=.23)
axis.bar(range(4), [float(row['targets_per_second']) / 1000 for row in rows],
         color=['#3c6e82', '#3c6e82', '#3c6e82', '#8f3d3d'])
axis.set_xticks(range(4), [row['batch'] for row in rows])
axis.set_xlabel('Số cửa sổ trong batch', labelpad=10)
axis.set_ylabel('Nghìn target / giây')
axis.set_ylim(0, 23)
axis.set_title('Junyi trên T4 — thông lượng packet 56.332 target',
               loc='left', pad=18, fontsize=12)
for index, row in enumerate(rows):
    value = float(row['targets_per_second']) / 1000
    axis.text(index, value + .5, f'{value:.2f}', ha='center')
figure.text(.12, .05, 'Một lượt mỗi batch, gồm batch đầu.\nChưa đo số epoch để đạt chất lượng.',
            ha='left', fontsize=9, linespacing=1.5)
for extension in ('svg', 'pdf', 'png'):
    target = BUNDLE / ('batch-throughput-v2.' + extension)
    assert not target.exists()
    figure.savefig(target, dpi=160)
plt.close(figure)
print('Saved revision v2, kept original figure and source')
