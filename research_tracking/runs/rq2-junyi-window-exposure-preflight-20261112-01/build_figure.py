"""Bốn nhóm cạnh tách biệt theo cơ hội xuất hiện trong native prefix TRAIN80."""

import csv
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ['MPLCONFIGDIR'] = str(
    ROOT / 'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


proof = json.loads((HERE / 'independent-full-check.json').read_text(encoding='utf-8'))
assert proof['status'] == 'PASS_CSV_AND_64_WINDOW_SEEN_SET_PARITY'
categories = proof['disjoint_edge_categories']
rows = [
    dict(category='prior_exposure_present', label='Có parent trước target trong native prefix', count=categories['prior_exposure_present']),
    dict(category='child_unfitted', label='Child không có trong vocabulary TRAIN', count=categories['child_unfitted']),
    dict(category='parent_unfitted_child_fitted', label='Child fitted, parent ngoài vocabulary TRAIN', count=categories['parent_unfitted_child_fitted']),
    dict(category='both_fitted_no_prior_exposure', label='Cả hai fitted, chưa có parent trước target', count=categories['both_fitted_no_prior_exposure']),
]
assert sum(row['count'] for row in rows) == 976
paths = [HERE / ('junyi-native-window-edge-coverage.' + extension) for extension in ('svg', 'pdf', 'png')]
csv_path = HERE / 'figure-data.csv'
assert not any(path.exists() for path in [*paths, csv_path])
with csv_path.open('x', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
})
figure, axis = plt.subplots(figsize=(12, 6.8))
positions = list(range(4))
axis.barh(positions, [row['count'] for row in rows], height=.5,
          color=['#3c6e82', '#8f3d3d', '#71619b', '#777777'])
axis.set_yticks(positions, [row['label'] for row in rows], fontsize=10)
axis.tick_params(axis='y', length=0, pad=12)
axis.invert_yaxis()
axis.set_xlim(0, 980)
axis.set_xlabel('Số cạnh trong đồ thị catalog', labelpad=10)
axis.set_axisbelow(True)
axis.grid(axis='x', color='#e9e9e9', linewidth=.7)
for position, row in zip(positions, rows):
    axis.text(row['count'] + 12, position, str(row['count']), ha='left', va='center', fontsize=12, fontweight='bold')
figure.text(.045, .94, 'Junyi — cạnh nào có cơ hội cung cấp thông tin quá khứ?', fontsize=17, fontweight='bold')
figure.text(.045, .88, '976 cạnh catalog · bốn nhóm tách biệt · chỉ TRAIN80 outer-fold 4', fontsize=12)
figure.text(.045, .155, 'Đã kiểm 232.662 cửa sổ, 13.347.331 target từ 126.774 learner. Prefix đặt lại ở mỗi native window.', fontsize=10)
figure.text(.045, .105, '876 cạnh có ít nhất một target quan sát parent trước đó. Các con số này mô tả cơ hội exposure.', fontsize=10)
figure.text(.045, .055, 'Chưa đo ảnh hưởng lên dự báo, lợi ích học tập hoặc độ đúng của cạnh tiên quyết.', fontsize=10)
figure.subplots_adjust(left=.40, right=.97, top=.77, bottom=.29)
try:
    for path in paths:
        figure.savefig(path, dpi=180, facecolor='white')
finally:
    plt.close(figure)
print('Đã dựng một figure bốn nhóm cạnh từ kết quả fullscan đã kiểm, giữ SVG/PDF/PNG và CSV.')
