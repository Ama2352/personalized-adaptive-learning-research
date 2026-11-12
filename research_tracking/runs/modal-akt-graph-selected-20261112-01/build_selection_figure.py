"""Dựng chênh lệch selection A0–A3 sau khi đủ sáu graph fits đã nghiệm thu.

Chuyển thể quy ước màu, trục gọn và vector export của Chen Liu/figures4papers,
commit e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, CC BY-NC 4.0.
Nguồn và LICENSE giữ trong bundle figures4papers-akt-20261112-01.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(ROOT / 'artifacts/figure_runtime/figures4papers-20261112-01/matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=BUNDLE / 'figure-selection')
    args = parser.parse_args()
    baseline_path = ROOT / 'research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json'
    baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    allocation = json.loads((BUNDLE / 'allocation.json').read_text())
    verified = [('A0', baseline)]
    sources = [baseline_path]
    for candidate in allocation['candidate_requests']:
        path = BUNDLE / (candidate.lower() + '-verification.json')
        record = json.loads(path.read_text(encoding='utf-8'))
        assert record['status'] == 'VERIFIED_MAIN60_GRAPH_CUDA_SELECTED'
        verified.append((candidate, record))
        sources.append(path)
    output = args.output_dir
    output.mkdir(exist_ok=False)
    records = []
    for candidate, result in verified:
        metrics = result['selection_metrics']
        records.append(dict(candidate_id=candidate, selected_epoch=result['selected_epoch'],
            log_loss=metrics['log_loss'], brier=metrics['brier'],
            delta_log_loss=metrics['log_loss']-baseline['selection_metrics']['log_loss'],
            delta_brier=metrics['brier']-baseline['selection_metrics']['brier']))
    with (output / 'data.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
        'axes.spines.right': False, 'axes.spines.top': False,
        'axes.linewidth': 1.3, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 7), sharey=True)
    names = [row['candidate_id'].replace('_', ' · ').replace('EXPERT', 'expert').replace('LEARNED', 'learned') for row in records]
    colors = {'A0': '#767676', 'A1': '#42949E', 'A2': '#9A4D8E', 'A3': '#0F4D92'}
    for axis, metric, title in zip(axes, ('delta_log_loss', 'delta_brier'),
                                ('Sai số dự báo theo Log Loss', 'Sai số xác suất theo Brier')):
        values = [row[metric] for row in records]
        span = max(max(values)-min(values), 1e-6)
        axis.axvline(0, color='#767676', linewidth=1.0, linestyle='--')
        for position, row in enumerate(records):
            color = colors[row['candidate_id'][:2]]
            marker = 'D' if row['candidate_id'].endswith('LEARNED') else 'o'
            axis.scatter(row[metric], position, color=color, marker=marker, s=58, zorder=3)
            axis.annotate(f"{row[metric]:+.7f}", (row[metric], position), xytext=(8, 0),
                          textcoords='offset points', va='center', fontsize=10, color=color)
        axis.set(title=title, xlabel='Chênh lệch so với A0 (thấp hơn là tốt hơn)',
                 xlim=(min(min(values), 0)-0.2*span, max(max(values), 0)+0.8*span))
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((-3, 3))
        axis.xaxis.set_major_formatter(formatter)
        axis.grid(axis='y', color='#EEEEEE', linewidth=0.7)
    axes[0].set_yticks(range(len(records)), names)
    axes[0].invert_yaxis()
    fig.suptitle('AKT A0–A3 — chênh lệch trên tập chọn epoch', fontsize=17, x=0.04, ha='left', y=0.97)
    fig.text(0.04, 0.88, 'Grade 10 · cùng 6 học viên selection và 1.260 target · cùng backbone khởi tạo · seed 42', fontsize=12)
    fig.text(0.04, 0.10, 'Mỗi biến thể dùng checkpoint đã chọn bằng tập này. Chưa là đánh giá độc lập.', fontsize=11)
    fig.text(0.04, 0.055, 'Cần refit, calibration và đối chứng đánh giá riêng trước khi kết luận về hiệu quả CG-AKT.', fontsize=11)
    fig.subplots_adjust(left=0.17, right=0.98, top=0.76, bottom=0.24, wspace=0.23)
    try:
        for extension in ('svg', 'pdf', 'png'):
            fig.savefig(output / ('selection-differences.' + extension), dpi=300,
                        facecolor='white', bbox_inches='tight', pad_inches=0.2)
    finally:
        plt.close(fig)
    manifest = dict(status='SELECTION_DESCRIPTIVE_ONLY',
        sources={str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        uncertainty='Chưa có khoảng suy luận trên đánh giá độc lập. Một training seed.',
        outputs={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir()) if path.is_file()})
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Đã dựng SVG/PDF/PNG và CSV từ bảy checkpoint selected đã nghiệm thu.')


if __name__ == '__main__':
    main()
