"""Dựng một figure từ aggregate đã lưu, theo palette figures4papers trong repo.

Tham khảo Chen Liu, figures4papers, commit e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15.
Áp dụng quy ước màu/trục/xuất vector đã dùng trong các figure KLTN.
"""

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
from matplotlib.ticker import FuncFormatter


summary = json.loads((HERE / 'summary.json').read_text(encoding='utf-8'))
assert summary['status'] == 'PASS_SAME_STATE_STRICT_FRONTIER_DESCRIPTION'
variants = [
    ('graph_free', 'Không đồ thị'),
    ('graph_package', 'Gói đồ thị đầy đủ'),
    ('empty_graph_package', 'Gói với đồ thị rỗng'),
]
records = []
for variant, label in variants:
    group = summary['groups']['variant:' + variant]
    assert group['events'] == 1080 and group['strict_frontier_empty_events'] == 0
    assert group['strict_frontier_memberships'] + group['removed_by_exposure_memberships'] == group['ready_memberships']
    records.append(dict(
        variant=variant, label=label, snapshots=group['events'],
        strict_memberships=group['strict_frontier_memberships'],
        removed_memberships=group['removed_by_exposure_memberships'],
        original_memberships=group['ready_memberships']))
paths = [HERE / ('strict-readiness-shadow.' + extension) for extension in ('svg', 'pdf', 'png')]
csv_path = HERE / 'figure-data.csv'
assert not any(path.exists() for path in [*paths, csv_path]), 'Giữ nguyên phiên bản đã dựng'
with csv_path.open('x', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
    'legend.frameon': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
})
figure, axis = plt.subplots(figsize=(11, 6.4))
positions = list(range(3))
strict = [record['strict_memberships'] for record in records]
removed = [record['removed_memberships'] for record in records]
axis.barh(positions, strict, height=.48, color='#3c6e82', label='Thỏa thành thạo nghiêm ngặt')
axis.barh(positions, removed, left=strict, height=.48, color='#8f3d3d', label='Bị loại khi bỏ ngoại lệ exposure')
axis.set_yticks(positions, [record['label'] for record in records])
axis.invert_yaxis()
axis.set_xlim(0, 11200)
axis.set_xlabel('Số lượt concept–snapshot thuộc frontier', labelpad=12)
axis.xaxis.set_major_formatter(FuncFormatter(lambda value, position: f'{value:,.0f}'.replace(',', '.')))
axis.tick_params(axis='y', length=0, pad=12)
axis.set_axisbelow(True)
axis.grid(axis='x', color='#e9e9e9', linewidth=.7)
for position, record in zip(positions, records):
    axis.text(record['strict_memberships'] / 2, position,
              f"{record['strict_memberships']:,}".replace(',', '.'),
              ha='center', va='center', color='white', fontsize=12, fontweight='bold')
    axis.text(record['strict_memberships'] + record['removed_memberships'] / 2, position,
              f"{record['removed_memberships']:,}".replace(',', '.'),
              ha='center', va='center', color='white', fontsize=12, fontweight='bold')
    axis.text(record['original_memberships'] + 120, position,
              f"{record['original_memberships']:,}".replace(',', '.'),
              ha='left', va='center', fontsize=10, color='#333333')
figure.text(.055, .945, 'Ngoại lệ exposure mở rộng tập bài đủ điều kiện',
             fontsize=17, fontweight='bold', ha='left')
figure.text(.055, .89, 'Giữ nguyên trạng thái lịch sử, chỉ thay điều kiện tiên quyết tại từng snapshot',
             fontsize=11, ha='left')
figure.legend(*axis.get_legend_handles_labels(), loc='upper left',
              bbox_to_anchor=(.055, .855), ncol=1, fontsize=10)
figure.text(.055, .14, '3.240 snapshot từ 3 seed families · mỗi biến thể 1.080 snapshot.', fontsize=10)
figure.text(.055, .095, 'Frontier strict không rỗng ở 3.240/3.240 snapshot. Một concept có thể được đếm qua nhiều thời điểm.', fontsize=10)
figure.text(.055, .05, 'Chỉ đo eligibility trên cùng trạng thái. Chưa tính hành động thay thế hoặc kết quả học.', fontsize=10)
figure.subplots_adjust(left=.245, right=.97, bottom=.30, top=.72)
try:
    for path in paths:
        figure.savefig(path, dpi=180, facecolor='white')
finally:
    plt.close(figure)
print('Đã dựng một figure SVG/PDF/PNG và CSV nguồn từ summary.json, không chạy lại thí nghiệm.')
