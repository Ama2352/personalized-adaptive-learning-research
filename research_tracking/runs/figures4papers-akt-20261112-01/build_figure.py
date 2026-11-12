"""Dựng figure A0 theo quy ước figures4papers, từ lịch sử đã nghiệm thu.

Tham khảo Chen Liu, figures4papers, commit e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15.
Áp dụng palette, trục gọn, xuất vector và bố cục từ tài liệu CC BY-NC 4.0.
Phần đọc bằng chứng, kiểm nguồn, chú giải và hình A0 được viết cho KLTN.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUNDLE = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'research_tracking/runs/modal-akt-recovery-20261112-01'
RUNTIME = ROOT / 'artifacts/figure_runtime/figures4papers-20261112-01'
os.environ['MPLCONFIGDIR'] = str(RUNTIME / 'matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=BUNDLE)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    formats = ('svg', 'pdf', 'png')
    paths = [output / f'akt-a0-checkpoint-selection.{extension}' for extension in formats]
    records_path = output / 'figure-data.csv'
    manifest_path = output / 'figure-manifest.json'
    if any(path.exists() for path in [*paths, records_path, manifest_path]):
        raise FileExistsError('Đầu ra đã tồn tại. Dùng --output-dir mới để giữ phiên bản figure cũ.')

    source = EVIDENCE / 'main60-a0__fit80__epochs.json'
    verification_path = EVIDENCE / 'main60-a0-verification.json'
    source_bytes = source.read_bytes()
    rows = json.loads(source_bytes)
    verification = json.loads(verification_path.read_bytes())
    assert verification['status'] == 'VERIFIED_MAIN60_A0_CUDA_SELECTED'
    assert [row['epoch'] for row in rows] == list(range(1, verification['epochs'] + 1))
    assert all(row['raw_selection']['full_targets'] == 1260 for row in rows)
    records = [dict(
        epoch=row['epoch'],
        native_selection_log_loss=row['raw_selection']['native_bce_mean'],
        exported_selection_log_loss=row['raw_selection']['full_metrics']['log_loss'],
        selection_auc=row['raw_selection']['full_metrics']['auc'],
        selected=row['epoch'] == verification['selected_epoch'],
    ) for row in rows]
    with records_path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 12,
        'axes.spines.right': False, 'axes.spines.top': False,
        'axes.linewidth': 1.4, 'legend.frameon': False,
        'svg.fonttype': 'none', 'pdf.fonttype': 42,
    })
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.4))
    selected = next(row for row in records if row['selected'])
    epochs = [row['epoch'] for row in records]
    panels = (
        ('native_selection_log_loss', 'Chọn epoch theo sai số dự báo', 'Log Loss (thấp hơn là tốt hơn)'),
        ('selection_auc', 'Theo dõi khả năng phân biệt đúng / sai', 'AUC (cao hơn là tốt hơn)'),
    )
    for index, (axis, (key, title, ylabel)) in enumerate(zip(axes, panels)):
        axis.plot(epochs, [row[key] for row in records], color='#0F4D92', marker='o', linewidth=2.3)
        axis.axvline(selected['epoch'], color='#767676', linestyle='--', linewidth=1.1)
        axis.scatter([selected['epoch']], [selected[key]], color='#B64342', s=80, zorder=4)
        axis.set(title=title, xlabel='Epoch', ylabel=ylabel, xticks=epochs, xlim=(0.65, 8.35))
        axis.margins(y=0.23)
        axis.grid(axis='y', color='#E9E9E9', linewidth=0.7)
        annotation_position = ((12, 26), (-10, 45))[index]
        annotation_alignment = ('left', 'right')[index]
        axis.annotate(f"Epoch 5\n{selected[key]:.4f}",
                      xy=(selected['epoch'], selected[key]), xytext=annotation_position,
                      ha=annotation_alignment,
                      textcoords='offset points', fontsize=11, color='#B64342',
                      arrowprops=dict(arrowstyle='-', color='#B64342', linewidth=0.8))
    fig.suptitle('AKT không đồ thị — diễn tiến chọn checkpoint trên GPU Modal', fontsize=17, x=0.06, ha='left', y=0.97)
    fig.text(0.06, 0.875, 'Grade 10 · 48 học viên huấn luyện · 6 học viên selection · 1.260 dự báo mỗi epoch', fontsize=12)
    fig.text(0.06, 0.10, 'Epoch 5 được chọn theo Log Loss. AUC được theo dõi bổ sung.', fontsize=11)
    fig.text(0.06, 0.055, 'Số liệu thuộc tập chọn epoch. Đánh giá độc lập và so sánh các biến thể đồ thị còn cần thực hiện.', fontsize=11)
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.25, top=0.76, wspace=0.32)
    try:
        for path in paths:
            fig.savefig(path, dpi=300, facecolor='white', bbox_inches='tight', pad_inches=0.18)
    finally:
        plt.close(fig)

    source_info = [dict(path=str(path.relative_to(ROOT)).replace('\\', '/'),
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                   for path in (source, verification_path)]
    manifest = dict(
        status='RENDERED_FROM_VERIFIED_A0_MAIN60_SELECTION',
        upstream_revision='e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15',
        matplotlib=matplotlib.__version__, sources=source_info,
        selected_epoch=selected['epoch'], uncertainty_band=False,
        caption='Quá trình chọn checkpoint A0 trên tập selection. Epoch5 được chọn theo native BCE float32 của protocol.',
        limits='Một seed và sáu học viên selection. Chưa là đánh giá độc lập, chưa so sánh graph hoặc suy luận lợi ích học tập.',
        outputs={path.name: dict(bytes=path.stat().st_size,
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                 for path in [*paths, records_path]},
    )
    with manifest_path.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=manifest['status'], outputs=[str(path) for path in paths]), ensure_ascii=False))


if __name__ == '__main__':
    main()
