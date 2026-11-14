"""Sửa câu dẫn, bổ sung metric trong summary và lưu QA cuối, giữ số liệu gốc."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = ROOT / 'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
sys.path.insert(0, str(ROOT / 'experiments/akt'))
from junyi_staged_io import sha, write_new


def main():
    performance = json.loads((HERE / 'a3-final-performance.json').read_text())
    metrics = json.loads((HERE / 'a3-selection-metrics.json').read_text())['metrics']
    qa_path = HERE / 'a3-report-verification.json'
    qa = json.loads(qa_path.read_text())
    qa['initial_report_hashes'] = qa['reports']
    seconds = f"{performance['train_seconds_mean']:.1f}".replace('.', ',')
    for name in ('BAO_CAO.md', 'BAO_CAO_NGHIEN_CUU.html'):
        path = REPORT / name
        text = path.read_bytes().decode('utf-8')
        text = text.replace('Các điểm dưới đây thuộc tập dùng chọn checkpoint.',
                            'Các điểm trong bảng thuộc tập dùng chọn checkpoint.')
        text = text.replace('phân tích cổng theo từng tương tác và hiệu quả quyết định lộ trình',
                            'đối chứng cổng trên tập độc lập và hiệu quả quyết định lộ trình')
        text = text.replace('Các lượt A3 dùng tổng 52.2 phút trong function GPU. Trung bình 1,439 mẫu NVML',
            f'Các lượt A3 dùng tổng 52,2 phút trong function GPU. Pha train trung bình {seconds} giây mỗi epoch. Trung bình 1.439 mẫu NVML')
        if name.endswith('.md'):
            table = '| Metric A3 trên selection | Giá trị | Mục đích |\n|---|---|---|\n'
            for label, key, purpose in (('AUC', 'auc', 'Phân biệt câu trả lời đúng/sai'),
                    ('Log Loss', 'log_loss', 'Độ phù hợp của xác suất'),
                    ('Brier', 'brier', 'Sai lệch bình phương xác suất'),
                    ('ECE', 'ece', 'Độ khớp xác suất và tỷ lệ đúng, 15 nhóm')):
                value = f'{metrics[key]:.6f}'.replace('.', ',')
                table += f'| {label} | {value} | {purpose} |\n'
            marker = '[Nghiệm thu A3]'
            assert marker in text and 'Metric A3 trên selection' not in text
            text = text.replace(marker, table + '\n' + marker, 1)
        path.write_bytes(text.encode('utf-8'))
    qa['reports'] = {str(path.relative_to(ROOT)): sha(path) for path in
                    (REPORT / 'BAO_CAO.md', REPORT / 'BAO_CAO_NGHIEN_CUU.html')}
    qa['copy_revision_vi'] = 'Chỉnh câu dẫn, mô tả phần gate đã làm/chưa làm, thêm metric chung vào summary và thời gian train trung bình.'
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    png = HERE / 'figures/a3-junyi-selection-v01.png'
    write_new(HERE / 'figure-visual-qa.json', dict(png_viewed=True,
        file=png.relative_to(ROOT).as_posix(), sha256=sha(png),
        note_vi='Đã xem PNG trực tiếp, tiêu đề/nhãn/số đọc được, annotation không chồng đường hoặc nhãn trục. '
        'HTML chỉ kiểm tĩnh, không mở browser hoặc preview server.'))
    print(json.dumps(dict(status='A3_REPORT_COPY_AND_VISUAL_QA_SAVED')))


if __name__ == '__main__':
    main()
