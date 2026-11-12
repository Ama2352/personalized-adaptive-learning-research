"""Dựng hình usage GPU từ CSV đã kiểm, giữ SVG/PDF/PNG độc lập."""
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(ROOT/'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Tiếp tục quy ước figures4papers đang dùng, Chen Liu, CC BY-NC4.0.
with (BUNDLE/'resource-data.csv').open(newline='', encoding='utf-8') as stream:
    rows = list(csv.DictReader(stream))
seconds = [float(row['seconds']) for row in rows]
utilization = [float(row['gpu_utilization']) for row in rows]
used = [float(row['vram_used_mib'])/1024 for row in rows]
total = float(rows[0]['vram_total_mib'])/1024
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.fonttype':'none',
                     'axes.spines.top':False, 'axes.spines.right':False})
figure, axes = plt.subplots(1, 2, figsize=(10, 4.8))
figure.subplots_adjust(left=.08, right=.98, top=.80, bottom=.25, wspace=.28)
axes[0].plot(seconds, utilization, color='#3c6e82')
axes[0].axhline(50, color='#8f3d3d', linestyle='--', label='Mục tiêu50%')
axes[0].set_ylim(0, 100)
axes[0].set_ylabel('GPU-Util (%)')
axes[0].set_title('Trung bình87,5%, khoảng76–90%', loc='left', fontsize=11)
axes[0].legend(frameon=False, loc='lower left')
axes[1].plot(seconds, used, color='#3c6e82', label='Đang dùng1,50GiB')
axes[1].axhline(total, color='#8f3d3d', linestyle='--', label='Tổng15GiB')
axes[1].set_ylim(0, 16)
axes[1].set_ylabel('VRAM (GiB)')
axes[1].set_title('Khoảng10% dung lượng VRAM', loc='left', fontsize=11)
axes[1].legend(frameon=False, loc='center right')
for axis in axes:
    axis.set_xlabel('Giây trong khoảng đo ổn định')
    axis.set_xlim(0, seconds[-1])
    axis.set_xticks([0, 15, 30, 45, 60])
figure.suptitle('AKT batch32 trên T4 — 115 mẫu tài nguyên trong65giây', x=.08, ha='left', fontsize=13)
figure.text(.08, .06, 'Lặp packet TRAIN80 để kiểm tải GPU. Các số đo lấy sau lượt làm nóng.\n'
            'Chất lượng trên toàn Junyi và thời gian hội tụ còn cần đánh giá.', fontsize=9)
for extension in ('svg', 'pdf', 'png'):
    target = BUNDLE/('gpu-usage.'+extension)
    assert not target.exists()
    figure.savefig(target, dpi=160)
plt.close(figure)
print('Saved usage SVG, PDF and PNG from verified CSV.')
