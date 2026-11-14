"""Giữ figure, số liệu tài nguyên và cập nhật hai báo cáo sau nghiệm thu A3."""
from collections import Counter
import csv
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def vn(value, digits=6):
    return f'{value:.{digits}f}'.replace('.', ',')


class IdInventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for name, value in attrs if name == 'id')


def main():
    accepted = read(HERE / 'a3-final-acceptance.json')
    assert accepted['status'] == 'PASS_A3_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT'
    state = read(HERE / 'STATE.json')
    final_run = ROOT / state['latest_output']
    terminal = read(final_run / 'remote-inventory.json')['worker_result']['terminal']
    samples, function_seconds, rss = [], 0., 0
    training_by_epoch = {}
    for name in state['verified_tranches']:
        run = ROOT / 'experiments/akt/results' / name
        remote = read(run / 'remote-inventory.json')
        function_seconds += remote['gpu_worker_seconds']
        telemetry = run / 'files/outputs' / (name + '-operation') / 'gpu-telemetry.jsonl'
        samples.extend(json.loads(line) for line in telemetry.read_text().splitlines() if line)
        # Mỗi attempt có training files riêng. Partial được cộng như tài nguyên đã dùng.
        logical = run / 'files/outputs/junyi-a3-expert-selected-20261114-01'
        attempt_ids = {path.stem.removeprefix('attempt-') for path in logical.glob('attempt-*.json')}
        # Lượt resume chứa cả file cũ. Chỉ lấy attempt mới xuất hiện trong tranche này.
        prior_ids = set()
        for prior in state['verified_tranches'][:state['verified_tranches'].index(name)]:
            prior_root = ROOT / 'experiments/akt/results' / prior / 'files/outputs/junyi-a3-expert-selected-20261114-01'
            prior_ids.update(path.stem.removeprefix('attempt-') for path in prior_root.glob('attempt-*.json'))
        for attempt_id in attempt_ids - prior_ids:
            for path in logical.glob(f'epoch-*-{attempt_id}-training.json'):
                stats = read(path)
                epoch = int(re.match(r'epoch-(\d+)-', path.name)[1])
                training_by_epoch[epoch] = max(training_by_epoch.get(epoch, 0.), stats['resource']['wall_seconds'])
                rss = max(rss, stats['resource'].get('peak_rss_bytes', 0))
    # Lịch sử terminal giữ validation mỗi epoch đúng một lần.
    selection_seconds = sum(row['validation_seconds'] for row in terminal['history'])
    training_seconds = sum(training_by_epoch.values())
    mean_gpu = sum(row['gpu_utilization'] for row in samples) / len(samples)
    performance = dict(gpu_function_seconds_total=function_seconds,
        train_seconds_reported_total=training_seconds,
        train_seconds_mean=training_seconds / terminal['complete_epochs'],
        train_seconds_by_epoch=training_by_epoch, selection_seconds_total=selection_seconds,
        nvml_samples=len(samples), mean_sampled_gpu_utilization=mean_gpu,
        peak_vram_mib=max(row['vram_used_mib'] for row in samples), peak_training_rss_bytes=rss,
        gpu_utilization_goal_50_percent_met=mean_gpu >= 50,
        source_runs=state['verified_tranches'],
        limits_vi='NVML lấy mẫu khoảng2giây. Với partial/resume chính xác, lấy wall_seconds tích lũy lớn nhất '
        'theo epoch để tránh cộng đôi phần trước resume. Tổng function là thời gian thực của các lượt. '
        'Không có đối chứng full-epoch cached/uncached trong lượt này.')
    write_new(HERE / 'a3-final-performance.json', performance)
    figure_dir = HERE / 'figures'
    figure_dir.mkdir(exist_ok=False)
    rows = [dict(epoch=row['epoch'], native_selection_bce=row['validation']['native_bce'],
                 selected=row['epoch'] == terminal['selected_epoch'],
                 selection_seconds=row['validation_seconds'], targets=row['validation']['targets'])
            for row in terminal['history']]
    prefix = figure_dir / 'a3-junyi-selection-v01'
    with prefix.with_suffix('.csv').open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.environ['MPLCONFIGDIR'] = str(ROOT / 'artifacts/figure_runtime/matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FormatStrFormatter
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none',
        'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
    figure, axes = plt.subplots(figsize=(8.2, 4.8))
    figure.subplots_adjust(left=.13, right=.97, bottom=.22, top=.86)
    axes.plot([row['epoch'] for row in rows], [row['native_selection_bce'] for row in rows],
              color='#0F4D92', marker='o', markersize=5, linewidth=2)
    chosen = rows[terminal['selected_epoch'] - 1]
    axes.scatter([chosen['epoch']], [chosen['native_selection_bce']], color='#B64342', s=95, zorder=4)
    axes.annotate(f"Checkpoint đã chọn\nepoch {chosen['epoch']} · Log Loss {vn(chosen['native_selection_bce'])}",
        xy=(chosen['epoch'], chosen['native_selection_bce']), xycoords='data',
        xytext=(.45, .82), textcoords='axes fraction', fontsize=10.5,
        bbox=dict(boxstyle='round,pad=.45', facecolor='white', edgecolor='#d5dee6'),
        arrowprops=dict(arrowstyle='->', color='#B64342'))
    axes.set(title='Diễn biến chọn checkpoint A3 trên Junyi', xlabel='Epoch', ylabel='Log Loss trên tập chọn checkpoint')
    axes.set_xticks(range(1, terminal['complete_epochs'] + 1))
    axes.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
    axes.grid(axis='y', alpha=.2)
    axes.margins(x=.04, y=.12)
    figure.text(.13, .08, 'Selection cố định · 15.847 người học · 1.600.343 tương tác · seed 42', fontsize=10)
    figure.text(.13, .035, 'Chọn checkpoint theo cải thiện tối thiểu 0,0001 và patience 3.', fontsize=9.5)
    figure.savefig(prefix.with_suffix('.svg'), metadata={'Creator': 'KLTN, quy ước figures4papers của Chen Liu'})
    figure.savefig(prefix.with_suffix('.png'), dpi=200)
    plt.close(figure)
    write_new(prefix.with_suffix('.json'), dict(source=str((final_run / 'remote-inventory.json').relative_to(ROOT)),
        source_sha256=sha(final_run / 'remote-inventory.json'), model='A3_EXPERT', phase='selected_fit80',
        style_reference='research_tracking/runs/figures4papers-akt-20261112-01/upstream-reference.json',
        style_upstream_commit='e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15', license='CC BY-NC 4.0',
        files={prefix.with_suffix(ext).name: dict(bytes=prefix.with_suffix(ext).stat().st_size,
                 sha256=sha(prefix.with_suffix(ext))) for ext in ('.svg', '.png', '.csv')}))
    comparison = read(HERE / 'a3-comparison-audit.json')
    metrics = read(HERE / 'a3-selection-metrics.json')['metrics']
    gate_audit = read(HERE / 'a3-gate-selection-audit.json')
    assert gate_audit['status'] == 'PASS_CPU_SELECTED_GATE_CONTEXT_AUDIT'
    billing = read(HERE / 'billing-after.json')
    heading = '14/11 — A0–A3 đã hoàn tất chọn checkpoint trên Junyi'
    paragraphs = [
        'Sau A0 không dùng đồ thị, A1 dùng đồ thị cố định và A2 dùng độ tin cậy từng cạnh, '
        'đã hoàn tất A3 với thêm một cổng học điều chỉnh ảnh hưởng đồ thị. Bốn cấu hình tạo thành '
        'chuỗi đối chứng dự báo cho RQ3. Confidence được ước lượng riêng từ TRAIN80 trước khi học A2/A3.',
        f"A3 đã chạy {terminal['complete_epochs']} epoch và chọn checkpoint epoch {terminal['selected_epoch']} "
        'theo cùng quy tắc cải thiện tối thiểu 0,0001 và patience 3. Mỗi epoch học đủ 13.347.331 lượt trả lời '
        'của 126.774 người học. Tập chọn checkpoint giữ riêng 15.847 người học, với 1.600.343 lượt trả lời. '
        'Đã đối chiếu split, vocabulary, 27 trường cấu hình học, seed và khởi tạo backbone với các bản trước.',
        'Sau khi học, đã nạp lại checkpoint được chọn và xuất đủ dự đoán selection, kiểm đúng thứ tự thời gian '
        'và tập tương tác, 0 bài tập ngoài vocabulary. Log Loss được dùng để theo dõi mức phù hợp của xác suất '
        'với câu trả lời thực tế, giúp chọn checkpoint theo một quy tắc thống nhất.',
        'Các điểm trong bảng thuộc tập dùng chọn checkpoint. Cần đánh giá độc lập và khoảng bất định để '
        'kết luận mức độ cải thiện. A0 lịch sử chọn epoch bằng validation batch 1, riêng checkpoint epoch 9 '
        'đã được chấm lại bằng batch 128. Đối chiếu lại toàn bộ lịch sử chọn epoch A0 vẫn còn thiếu.',
        'Để biết mô hình thực sự đưa thông tin đồ thị vào dự báo đến mức nào, '
        'đã đọc riêng cơ chế cổng từ checkpoint được chọn và ngữ cảnh quá khứ trong cache. '
        f"Có {vn(gate_audit['active_fraction'] * 100, 2)}% lượt trả lời selection có ngữ cảnh đồ thị đủ điều kiện. "
        f"Trên nhóm này, giá trị cổng trung vị là {vn(gate_audit['gate_on_active_targets']['median'], 4)} trên thang 0–1. "
        'Ảnh hưởng cuối còn phụ thuộc hệ số đồ thị và thông tin tiên quyết quan sát được. '
        'Thống kê cơ chế được dựng lại trên CPU, kiểm CUDA riêng và đối chứng tắt đồ thị trên tập độc lập còn chờ.',
        'Nhánh Junyi đã có đủ A0–A3 ở bước selected-fit. Kết quả bổ sung bằng chứng mô hình học được và '
        'xuất dự đoán có thể so sánh theo cùng tập target. Refit, calibration, đánh giá độc lập, '
        'đối chứng cổng trên tập độc lập và hiệu quả quyết định lộ trình trong mô phỏng còn chờ. '
        'RQ3 cần các bước đó để kết luận về hệ thống học tập thích ứng.'
    ]
    labels = {'A0': 'AKT không đồ thị', 'A1': 'Đồ thị cố định',
              'A2': 'Độ tin cậy cạnh', 'A3': 'Độ tin cậy cạnh và cổng'}
    table_rows = [(item['model'].replace('_EXPERT', ''), labels[item['model'].replace('_EXPERT', '')],
                   str(item['complete_epochs']), str(item['selected_epoch']), vn(item['native_bce']))
                  for item in comparison['models']]
    count_text = format(len(samples), ',').replace(',', '.')
    resource = (f"Các lượt A3 dùng tổng {vn(function_seconds / 60, 1)} phút trong function GPU. "
        f"Pha train trung bình {vn(performance['train_seconds_mean'], 1)} giây mỗi epoch. "
        f"Trung bình {count_text} mẫu NVML là {vn(mean_gpu, 2)}%, VRAM đỉnh "
        f"{vn(performance['peak_vram_mib'] / 1024, 2)} GiB. "
        'Chuẩn bị snapshot và upload diễn ra trước gọi GPU. Việc tải và nén artifact diễn ra sau xác nhận dừng App. '
        f"Modal báo tổng metered toàn workspace {vn(float(billing['billing']['metered_cost']), 2)} USD, "
        f"billed {vn(float(billing['billing']['billed_cost']), 2)} USD. Trần toàn KLTN là 30 USD.")
    if mean_gpu < 50:
        resource += ' Mục tiêu GPU trung bình trên 50% còn chưa đạt.'
    svg = prefix.with_suffix('.svg').read_text(encoding='utf-8')
    svg = svg[svg.index('<svg'):]
    ids = {value: 'a3-v01-' + value for value in re.findall(r'\bid="([^"]+)"', svg)}
    svg = re.sub(r'\bid="([^"]+)"', lambda match: 'id="' + ids[match[1]] + '"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', lambda match: 'url(#' + ids.get(match[1], match[1]) + ')', svg)
    svg = re.sub(r'((?:xlink:)?href)="#([^"]+)"', lambda match: match[1] + '="#' + ids.get(match[2], match[2]) + '"', svg)
    table_header = ['Mô hình', 'Cấu hình', 'Epoch đã chạy', 'Epoch đã chọn', 'Log Loss selection']
    table = '<div class="table-scroll"><table><thead><tr>' + ''.join('<th>' + escape(value) + '</th>' for value in table_header) + '</tr></thead><tbody>'
    table += ''.join('<tr>' + ''.join('<td>' + escape(value) + '</td>' for value in row) + '</tr>' for row in table_rows) + '</tbody></table></div>'
    html_section = '<section id="cap-nhat-20261114-a3-complete"><h2>' + heading + '</h2>'
    html_section += ''.join('<p>' + escape(text) + '</p>' for text in paragraphs[:3])
    html_section += '<figure><div class="svg-frame">' + svg + '</div><figcaption>Chọn checkpoint A3 trên cùng nhóm selection, seed 42. Chấm đỏ đánh dấu checkpoint được chọn theo quy tắc đã chốt.</figcaption></figure>'
    html_section += table + ''.join('<p>' + escape(text) + '</p>' for text in paragraphs[3:])
    html_section += '<details><summary>Metric dự báo và tài nguyên đã kiểm</summary><p>'
    html_section += escape(f"A3 có AUC {vn(metrics['auc'])}, Log Loss {vn(metrics['log_loss'])}, "
        f"Brier {vn(metrics['brier'])}, ECE {vn(metrics['ece'])}. Hàm chấm metric dùng chung với GAM-KT, ECE 15 nhóm. "
        'AUC theo dõi phân biệt đúng/sai, Brier và ECE bổ sung kiểm chất lượng xác suất. ' + resource)
    html_section += '</p></details></section>\n'
    html_path = REPORT / 'BAO_CAO_NGHIEN_CUU.html'
    raw = html_path.read_bytes().decode('utf-8')
    assert 'cap-nhat-20261114-a3-complete' not in raw
    marker = '<section id="cap-nhat-20261114-a2-dispatch">'
    assert marker in raw
    raw = raw.replace(marker, html_section + marker, 1)
    inventory = IdInventory()
    inventory.feed(raw)
    assert all(count == 1 for count in Counter(inventory.ids).values())
    html_path.write_bytes(raw.encode('utf-8'))
    markdown = '## ' + heading + '\n\n' + '\n\n'.join(paragraphs[:3]) + '\n\n'
    markdown += '![Chọn checkpoint A3](../../../runs/junyi-a3-selected-20261114-01/figures/a3-junyi-selection-v01.svg)\n\n'
    markdown += '| ' + ' | '.join(table_header) + ' |\n|---|---|---|---|---|\n'
    markdown += ''.join('| ' + ' | '.join(row) + ' |\n' for row in table_rows) + '\n'
    markdown += '\n\n'.join(paragraphs[3:]) + '\n\n' + resource + '\n\n'
    markdown += '| Metric A3 trên selection | Giá trị | Mục đích |\n|---|---|---|\n'
    for label, key, purpose in (('AUC', 'auc', 'Phân biệt câu trả lời đúng/sai'),
            ('Log Loss', 'log_loss', 'Độ phù hợp của xác suất'),
            ('Brier', 'brier', 'Sai lệch bình phương xác suất'),
            ('ECE', 'ece', 'Độ khớp xác suất và tỷ lệ đúng, 15 nhóm')):
        markdown += f'| {label} | {vn(metrics[key])} | {purpose} |\n'
    markdown += '\n'
    markdown += '[Nghiệm thu A3](../../../runs/junyi-a3-selected-20261114-01/a3-final-acceptance.json), '
    markdown += '[hồ sơ và giới hạn](../../../runs/junyi-a3-selected-20261114-01/README.md), '
    markdown += '[gói model](../../../../experiments/akt/results/model-export-a3-batch128-20261114-01/README.md).\n\n'
    md_path = REPORT / 'BAO_CAO.md'
    text = md_path.read_bytes().decode('utf-8')
    marker_md = '## 14/11 — A2 hoàn tất bước chọn checkpoint trên Junyi'
    assert marker_md in text and heading not in text
    md_path.write_bytes(text.replace(marker_md, markdown + marker_md, 1).encode('utf-8'))
    write_new(HERE / 'a3-report-verification.json', dict(status='PASS_STATIC_A3_REPORT_AND_FIGURE_OUTPUTS',
        duplicate_html_ids=False, standalone_figure_files=4, browser_layout_tested=False,
        reports={str(path.relative_to(ROOT)): sha(path) for path in (html_path, md_path)}))
    print(json.dumps(dict(status='A3_REPORTS_AND_FIGURE_SAVED', performance=performance)))


if __name__ == '__main__':
    main()
