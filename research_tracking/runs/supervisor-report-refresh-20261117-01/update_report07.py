"""Nối kết quả17/11 vào hai báo cáo hiện hành, giữ nguyên hình/PDF nhúng."""
from pathlib import Path
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[3]
FOLDER = ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'
BUNDLE = Path(__file__).resolve().parent


def replace_once(text, before, after):
    assert text.count(before) == 1, before[:100]
    return text.replace(before, after, 1)


def media_pins(text):
    media = re.findall(r'<svg\b.*?</svg>|data:[^"\s]+', text, re.S)
    return [hashlib.sha256(value.encode()).hexdigest() for value in media]


def main():
    md_path, html_path = FOLDER/'BAO_CAO.md', FOLDER/'BAO_CAO_NGHIEN_CUU.html'
    markdown = md_path.read_text(encoding='utf-8')
    webpage = html_path.read_text(encoding='utf-8')
    before_media = media_pins(webpage)
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (md_path, html_path)}
    shared = [
        ('Cả ba RQ còn các tiêu chí nghiệm thu thực nghiệm.',
         'A0/A1 đã hoàn tất hiệu chỉnh xác suất; A2/A3 đã lưu đủ dự báo để tiếp tục. Cả ba RQ còn các tiêu chí nghiệm thu thực nghiệm.'),
        ('A2 và A3 còn bước hiệu chỉnh, sau đó cả bốn cần đánh giá trên nhóm người học độc lập.',
         'Dự báo A2/A3 đã được lưu đầy đủ trên Drive; hai mô hình còn bước fit hệ số hiệu chỉnh, sau đó cả bốn cần đánh giá trên nhóm người học độc lập.'),
        ('Phần này tái lập thống kê từ kết quả mô phỏng đã lưu. Phần tách riêng tác động của cạnh tiếp tục thuộc chương trình chẩn đoán.',
         'Các hàm gốc dùng 3.000 lần lấy mẫu lại cho mỗi phép so. Môi trường hiện hành tái lập đúng số liệu; phiên bản thư viện lịch sử còn thiếu hồ sơ xác nhận. Phần này tái lập thống kê từ kết quả mô phỏng đã lưu. Phần tách riêng tác động của cạnh tiếp tục thuộc chương trình chẩn đoán.'),
        ('nếu không luyện thêm và phần tăng điểm không âm.',
         'nếu không luyện thêm và phần tăng của từng khái niệm không âm.'),
        ('Đã tính đủ dự báo. Ghép đáp án và tìm mức hiệu chỉnh trên CPU còn chờ nghiệm thu',
         'Dự báo đủ 4/4. A0/A1 đã hiệu chỉnh và xác minh artifact; A2/A3 còn fit hệ số'),
        ('Kết quả số, mô hình nguồn và nhật ký đã được lưu để tiếp tục xử lý trên CPU.',
         'Kết quả số, mô hình nguồn và nhật ký đã được lưu. A0/A1 đã fit hệ số; A2/A3 đã sao lưu đầy đủ dự báo để tiếp tục bước này.'),
        ('Bước ghép đáp án và tìm mức hiệu chỉnh đang thực hiện, chưa có kết quả nghiệm thu.',
         'A0/A1 đã có hệ số hiệu chỉnh được nghiệm thu. A2/A3 còn bước fit hệ số từ các dự báo đã lưu.'),
        ('A2 và A3 đã có dự đoán để tiếp tục bước hiệu chỉnh.',
         'Dự báo số A2/A3 đã được lưu đầy đủ và kiểm toàn vẹn trên Drive; hệ số hiệu chỉnh của hai mô hình còn chờ fit.'),
        ('Đã tính lại trung bình, chênh lệch và Holm cho 117 phép so Paper2.',
         'Đã tái lập đúng cả trung bình, chênh lệch, Wilcoxon, bootstrap và Holm cho 117 phép so Paper2.'),
    ]
    for old, new in shared:
        markdown = replace_once(markdown, old, new)
        webpage = replace_once(webpage, old, new)
    webpage = replace_once(webpage, 'Khoảng ước lượng giữ từ Paper 2.',
                           'Khoảng ước lượng đã tính lại bằng hàm gốc từ kết quả theo hạt giống của Paper 2.')
    phase_intro = ('Các tỷ lệ dưới đây đếm mốc có tiêu chí và mẫu số cụ thể. Hai hàng chẩn đoán chỉ đếm các phát biểu hẹp đã đủ nguồn; '
                   'RQ1 còn mastery/hiệu chỉnh và kết quả học, RQ2 còn đối chứng dự báo thứ tự cùng các điều kiện nhiễu/lịch sử. '
                   'Tỷ lệ hoàn thành toàn RQ hoặc toàn KLTN cần một thang nghiệm thu riêng.')
    phase_rows = [
        ('RQ1 · phát biểu chẩn đoán hẹp', '5/7', '71,4%'),
        ('RQ2 · phát biểu hẹp của ba bẫy', '6/7', '85,7%'),
        ('Junyi · chọn vòng A0–A3', '4/4', '100%'),
        ('Junyi · học lại A0–A3', '4/4', '100%'),
        ('Junyi · suy luận trên phần hiệu chỉnh', '4/4', '100%'),
        ('Junyi · fit hệ số hiệu chỉnh đã nghiệm thu', '2/4', '50%'),
        ('Junyi · đánh giá độc lập', '0/4', '0%'),
        ('Grade10 · chọn vòng các mô hình hiện đại', '7/9', '77,8%'),
    ]
    phase_note = ('Các hàng Junyi giới hạn ở A0–A3 với đồ thị chuyên gia, outer fold4. Hàng Grade10 gồm bảy cấu hình AKT/CG-AKT '
                  'đã chọn vòng và hai đối chứng SAKT/GKT còn thiếu ở quy mô nghiên cứu. Hai mô hình này hiện mới có kết quả kiểm kỹ thuật nhỏ.')
    md_section = '\n\n## Các mốc đã khép theo từng phần\n\n'+phase_intro+'\n\n'
    md_section += '| Mốc trong phạm vi đã nêu | Đã khép / tổng | Tỷ lệ của mốc |\n| --- | ---: | ---: |\n'
    md_section += ''.join('| '+' | '.join(row)+' |\n' for row in phase_rows)
    md_section += '\n'+phase_note+'\n\n'
    markdown = replace_once(markdown, '<a id="rq1"></a>', md_section+'<a id="rq1"></a>')
    html_section = '<section id="milestones"><h2>Các mốc đã khép theo từng phần</h2><p>'+phase_intro+'</p>'
    html_section += '<table class="stats"><thead><tr><th>Mốc trong phạm vi đã nêu</th><th>Đã khép / tổng</th><th>Tỷ lệ của mốc</th></tr></thead><tbody>'
    html_section += ''.join('<tr>'+''.join('<td>'+html.escape(value)+'</td>' for value in row)+'</tr>' for row in phase_rows)
    html_section += '</tbody></table><p class="note">'+phase_note+'</p></section>\n'
    webpage = replace_once(webpage, '<section id="rq1">', html_section+'<section id="rq1">')
    webpage = replace_once(webpage, '<a href="#history">Diễn tiến</a><a href="#rq1">',
                           '<a href="#history">Diễn tiến</a><a href="#milestones">Mốc nghiệm thu</a><a href="#rq1">')
    markdown = replace_once(markdown, '**Khép bước ghép đáp án và hiệu chỉnh A0–A3**', '**Hoàn tất hiệu chỉnh A2/A3 và đánh giá độc lập A0–A3**')
    webpage = replace_once(webpage, '<strong>Khép bước ghép đáp án và hiệu chỉnh A0–A3</strong>', '<strong>Hoàn tất hiệu chỉnh A2/A3 và đánh giá độc lập A0–A3</strong>')
    extra_sources = (' Nguồn cập nhật gồm [tái lập thống kê Paper2](../../../runs/paper2-statistical-reproduction-20261117-02/attempt01/RESULT.json), '
                     '[hiệu chỉnh A0/A1](../../../runs/junyi-calibration-real-20261117-01/POSTSTOP_CALIBRATION_METADATA_ACCEPTANCE01.json) và '
                     '[cách đếm các mốc](../../../runs/thesis-results-discussion-writing-20261117-01/PUBLIC_MILESTONES_20261117.json).')
    markdown = replace_once(markdown, 'Bản HTML chứa sẵn PDF để tải về khi đọc độc lập.', 'Bản HTML chứa sẵn PDF để tải về khi đọc độc lập.'+extra_sources)
    assert before_media == media_pins(webpage)
    for path, text in ((md_path, markdown), (html_path, webpage)):
        path.write_text(text, encoding='utf-8')
    (BUNDLE/'UPDATE07.json').write_text(json.dumps(dict(before=before, media_preserved=True,
        changes=['Paper2 V2 and historical runtime caveat', 'Native retention per-concept nonnegative condition',
                 'A0/A1 accepted calibration; A2/A3 numeric Drive backup and fit pending',
                 'Bounded checklist/phase percentages with explicit denominators']), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
