"""Dựng SVG/PDF/PNG từ CSV đã nghiệm thu, không cần cloud hoặc Torch."""
import argparse
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--kind', choices=('sync', 'attention', 'attention-cache'), required=True)
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
data = json.loads((BUNDLE/(args.kind+'-analysis.json')).read_text(encoding='utf-8'))
os.environ['MPLCONFIGDIR'] = str(ROOT/'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Tiếp tục quy ước hình của figures4papers, Chen Liu, CC BY-NC 4.0.
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':10, 'svg.fonttype':'none',
                     'axes.spines.top':False, 'axes.spines.right':False})
figure, axes = plt.subplots(1, 2, figsize=(10, 4.8))
figure.subplots_adjust(left=.09, right=.98, top=.80, bottom=.26, wspace=.32)
for repeat in range(3):
    pair = [next(row for row in data['rows'] if row['repeat'] == repeat and row['variant'] == variant)
            for variant in ('reference', 'candidate')]
    axes[0].plot([0, 1], [row['targets_per_second']/1000 for row in pair], marker='o', label=f'Cặp {repeat+1}')
    axes[1].plot([0, 1], [row['gpu_utilization_mean'] for row in pair], marker='o')
candidate = {'sync':'Gom đồng bộ', 'attention':'Cast trên GPU',
             'attention-cache':'Cache trên GPU'}[args.kind]
for axis in axes:
    axis.set_xticks([0, 1], ['Hiện hành', candidate])
    axis.set_xlim(-.2, 1.2)
axes[0].set_ylabel('Nghìn target / giây')
axes[0].set_title('Thông lượng sau batch đầu', loc='left')
axes[0].legend(frameon=False)
axes[1].set_ylabel('GPU-Util trung bình (%)')
axes[1].set_ylim(0, 100)
axes[1].set_title('Mẫu nvidia-smi trong từng pha', loc='left')
figure.suptitle('AKT trên T4 — đối chiếu cùng batch4', x=.09, ha='left', fontsize=13)
figure.text(.09, .07, '1.024 cửa sổ, 56.332 target mỗi lượt. Ba cặp cùng khởi tạo và thứ tự dữ liệu.\n'
            'Model, Adam và RNG cuối cặp khớp tuyệt đối. Chưa đo tốc độ toàn epoch.', fontsize=9)
for extension in ('svg', 'pdf', 'png'):
    target = BUNDLE/(args.kind+'-profile-v2.'+extension)
    assert not target.exists()
    figure.savefig(target, dpi=160)
plt.close(figure)
print('Saved standalone SVG, PDF and PNG with paired source data.')
