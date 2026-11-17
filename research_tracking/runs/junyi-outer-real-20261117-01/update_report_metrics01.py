"""Đưa kết quả outer đã nghiệm thu vào mạch báo cáo, giữ giới hạn nghiên cứu."""
import json
from pathlib import Path
import re
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[3]
B=Path(__file__).resolve().parent
REPORT=ROOT/'research_tracking/supervisor_reports/2026-11-16/01_tien_do'

def number(value,digits=6):
    return f'{value:.{digits}f}'.replace('.',',')

def main():
    result=json.loads((B/'OUTER_COMPARISON01.json').read_text())
    for model in ('A0','A1','A2','A3'):
        assert (B/(model+'_CPU_EXPORT_DRIVE01.json')).is_file()
    rows=[]
    for model,metrics in result['models'].items():
        rows.append([model,number(metrics['raw']['log_loss']),number(metrics['calibrated']['log_loss']),
            number(metrics['calibrated']['auc'],5),number(metrics['calibrated']['brier']),number(metrics['calibrated']['ece'])])
    selected=[r for r in result['comparisons'] if r['reference']=='A0' and r['candidate']=='A3' and r['metric']=='log_loss']
    assert len(selected)==2
    raw=next(r for r in selected if r['probabilities']=='raw')
    calibrated=next(r for r in selected if r['probabilities']=='calibrated')
    assert raw['holm_p']<.05 and calibrated['holm_p']>.05
    intro='Sau khi có mô hình và hệ số hiệu chỉnh, bước tiếp theo là kiểm tra trên người học mới. Mục tiêu là xem đồ thị có giúp dự báo đáp án tốt hơn hay chủ yếu làm thay đổi mức tự tin. Cả A0–A3 được đánh giá trên cùng 39.616 người học thuộc Development fold 4, nằm ngoài các khâu học tham số, chọn vòng và fit hệ số hiệu chỉnh của AKT.'
    coverage='Mỗi mô hình xử lý đủ 4.137.050 lượt. Bộ chỉ số được tính trên cùng 4.136.906 lượt có bài đã xuất hiện trong nhóm huấn luyện. Có 144 lượt ngoài từ vựng được ghi riêng. Log Loss và Brier đo mức sai của xác suất, AUC đo khả năng phân biệt đúng/sai, ECE đối chiếu độ tự tin với tỷ lệ đúng quan sát.'
    finding='Ở xác suất gốc, A1 và A3 có sai số thấp hơn A0 ở mức chênh lệch tuyệt đối nhỏ. Phân tích lấy mẫu lại theo người học và hiệu chỉnh Holm ghi nhận khác biệt ở cả Log Loss và Brier. Sau khi hiệu chỉnh xác suất bằng nhóm người học riêng, các phép so A1/A2/A3 với A0 trên hai chỉ số chính đều chưa đạt ngưỡng 0,05 sau Holm.'
    conclusion='Với A3, chênh lệch Log Loss so với A0 đi từ −0,000062 trước hiệu chỉnh đến −0,000020 sau hiệu chỉnh. Khoảng tin cậy sau hiệu chỉnh từ −0,000044 đến +0,000005 vẫn chứa 0. Kết quả đặt ra yêu cầu kiểm soát mức tự tin khi đánh giá lợi ích đồ thị. Cần thí nghiệm riêng để quy sự thay đổi này cho một cơ chế cụ thể.'
    scope='Mốc này bổ sung bằng chứng cho nhánh dự báo và hiệu chỉnh của RQ1, cùng phép đối chứng Junyi của RQ3. Tác động tới quyết định chọn bài và kết quả học cần tiếp tục kiểm trong Grade10 với cạnh thật/nhiễu. Các điều kiện về lịch sử, hồ sơ người học và chất lượng đồ thị của RQ2 còn phần thực nghiệm riêng.'
    limit='Phân tích giới hạn ở một fold phát triển và một lần khởi tạo huấn luyện. Danh sách 24 phép so chính cùng cách tính p được khóa sau suy luận GPU, trước khi xem chỉ số đánh giá, với mốc thời gian được giữ trong hồ sơ. Bootstrap cho p xấp xỉ theo cụm người học. Các kết luận thống kê được trình bày ở mức thăm dò với ngoại lệ quy trình này.'
    table='| Mô hình | Log Loss gốc | Log Loss hiệu chỉnh | AUC hiệu chỉnh | Brier hiệu chỉnh | ECE hiệu chỉnh |\n|---|---:|---:|---:|---:|---:|\n'
    table+=''.join('| '+' | '.join(row)+' |\n' for row in rows)
    text='## 17/11 — Kết quả dự báo trên người học mới\n\n'+intro+'\n\n'+coverage+'\n\n'+table+'\n'+finding+'\n\n'+conclusion+'\n\n'
    text+='![Hiệu chỉnh và chênh lệch dự báo trên cùng nhóm người học](../../../runs/junyi-outer-real-20261117-01/outer-comparison-v02.svg)\n\n'
    text+=scope+'\n\n'+limit+'\n\n[Số liệu đầy đủ](../../../runs/junyi-outer-real-20261117-01/OUTER_METRICS01.csv) và [24 phép so chính](../../../runs/junyi-outer-real-20261117-01/OUTER_PAIRED_PRIMARY01.csv).\n\n'
    path=REPORT/'BAO_CAO.md';body=path.read_text(encoding='utf-8')
    body=re.sub(r'## (?:Hoàn tất suy luận độc lập Junyi cho bốn mô hình|17/11 — Kết quả dự báo trên người học mới)\n.*?(?=## Các mốc đã khép)',lambda _:text,body,count=1,flags=re.S)
    body=body.replace('| Junyi · bảng chỉ số outer đã nghiệm thu | 0/4 | 0% |','| Junyi · bảng chỉ số outer đã nghiệm thu | 4/4 | 100% |')
    body=body.replace('**Thành quả RQ3 hiện tại gồm mô hình đã triển khai, các bản huấn luyện đã lưu và đầu ra A0–A3 phục vụ hiệu chỉnh.**','**Thành quả RQ3 hiện tại gồm mô hình đã triển khai, các bản huấn luyện đã lưu và benchmark dự báo A0–A3 trên Junyi Development fold 4.**')
    body=body.replace('Hiệu quả dự báo, lựa chọn bài và kết quả học còn chờ đánh giá độc lập.','Bảng dự báo độc lập Junyi đã có. Lựa chọn bài và kết quả học cần tiếp tục đánh giá trong mô phỏng.')
    body=body.replace('So sánh chất lượng mô hình trên nhóm độc lập và kiểm chuẩn quanh ngưỡng thành thạo trong Grade10 còn chờ thực hiện.','So sánh trên nhóm độc lập Junyi đã hoàn tất trong mốc phía trên. Kiểm chuẩn quanh ngưỡng thành thạo trong Grade10 còn chờ thực hiện.')
    body=body.replace('**Còn thiếu để kết thúc RQ3** — đánh giá dự báo độc lập trên Junyi, học lại','**Còn thiếu để kết thúc RQ3** — đối chiếu các baseline trong cùng giao thức, học lại')
    body=body.replace('Junyi đã học lại và tính đủ dự báo hiệu chỉnh.','Junyi đã học lại, hiệu chỉnh và đánh giá A0–A3 trên một fold độc lập.')
    body=body.replace('Khép hiệu chỉnh và đánh giá độc lập, kiểm riêng đóng góp','Khép học lại/hiệu chỉnh và đánh giá Grade10, kiểm riêng đóng góp')
    body=body.replace('1. **Đánh giá độc lập A0–A3 trên Junyi** bằng bốn mô hình và hệ số đã đóng băng, giữ cùng nhóm người học và tương tác để so sánh dự báo và độ tin cậy xác suất.',
        '1. **Khép đối chiếu baseline và chuyển sang Grade10.** Benchmark Junyi A0–A3 hiện hành đã hoàn tất. Tiếp tục giữ cùng quần thể và giới hạn thông tin khi ghép các baseline; học lại/hiệu chỉnh Grade10 để kiểm lựa chọn bài và kết quả học.')
    top='**Mốc đã đạt** gồm các chẩn đoán RQ1–RQ2 và chuỗi chọn vòng, học lại, hiệu chỉnh, đánh giá dự báo độc lập của bốn mô hình Junyi. **Mốc còn thiếu** tập trung ở các đối chứng bắt buộc, điều kiện hiệu lực, quyết định lộ trình và mô phỏng vòng kín Grade10, cùng luận văn và demo hoàn chỉnh.'
    body=re.sub(r'\*\*Mốc đã đạt\*\*.*?(?=\n\n)',lambda _:top,body,count=1,flags=re.S)
    path.write_text(body,encoding='utf-8')
    html='<section id="outer-progress"><h2>17/11 — Kết quả dự báo trên người học mới</h2>'
    html+=''.join('<p>'+paragraph+'</p>' for paragraph in (intro,coverage))
    html+='<div class="table-scroll"><table class="outer-metrics"><thead><tr>'+''.join('<th>'+label+'</th>' for label in ['Model','Log Loss gốc','Log Loss hiệu chỉnh','AUC hiệu chỉnh','Brier hiệu chỉnh','ECE hiệu chỉnh'])+'</tr></thead><tbody>'
    html+=''.join('<tr>'+''.join('<td>'+value+'</td>' for value in row)+'</tr>' for row in rows)+'</tbody></table></div>'
    html+='<p>'+finding+'</p><p>'+conclusion+'</p>'
    svg=(B/'outer-comparison-v02.svg').read_text(encoding='utf-8')
    svg=re.search(r'<svg\b.*?</svg>',svg,re.S).group(0)
    svg=svg.replace('<svg ', '<svg style="width:100%;height:auto;display:block" ',1)
    html+='<div class="outer-chart">'+svg+'</div><p>'+scope+'</p><p class="note">'+limit+'</p>'
    for name,label in [('OUTER_METRICS01.csv','Tải bảng chỉ số đầy đủ'),('OUTER_PAIRED_PRIMARY01.csv','Tải 24 phép so chính')]:
        html+='<p><a download="'+name+'" href="data:text/csv;charset=utf-8,'+quote((B/name).read_text(encoding='utf-8'))+'">'+label+'</a></p>'
    html+='</section>'
    path=REPORT/'BAO_CAO_NGHIEN_CUU.html';body=path.read_text(encoding='utf-8')
    body=re.sub(r'<section id="outer-progress">.*?</section>',lambda _:html,body,count=1,flags=re.S)
    body=body.replace('<tr><td>Junyi · bảng chỉ số outer đã nghiệm thu</td><td>0/4</td><td>0%</td></tr>',
        '<tr><td>Junyi · bảng chỉ số outer đã nghiệm thu</td><td>4/4</td><td>100%</td></tr>')
    body=body.replace('Thành quả RQ3 hiện tại gồm mô hình đã triển khai, các bản huấn luyện đã lưu và đầu ra A0–A3 phục vụ hiệu chỉnh.',
        'Thành quả RQ3 hiện tại gồm mô hình đã triển khai, các bản huấn luyện đã lưu và benchmark dự báo A0–A3 trên Junyi Development fold 4.')
    body=body.replace('Hiệu quả dự báo, lựa chọn bài và kết quả học còn chờ đánh giá độc lập.','Bảng dự báo độc lập Junyi đã có. Lựa chọn bài và kết quả học cần tiếp tục đánh giá trong mô phỏng.')
    body=body.replace('So sánh chất lượng mô hình trên nhóm độc lập và kiểm chuẩn quanh ngưỡng thành thạo trong Grade10 còn chờ thực hiện.','So sánh trên nhóm độc lập Junyi đã hoàn tất trong mốc phía trên. Kiểm chuẩn quanh ngưỡng thành thạo trong Grade10 còn chờ thực hiện.')
    body=body.replace('đánh giá dự báo độc lập trên Junyi, học lại','đối chiếu các baseline trong cùng giao thức, học lại')
    body=body.replace('Junyi đã học lại và tính đủ dự báo hiệu chỉnh.','Junyi đã học lại, hiệu chỉnh và đánh giá A0–A3 trên một fold độc lập.')
    body=body.replace('Khép hiệu chỉnh và đánh giá độc lập, kiểm riêng đóng góp','Khép học lại/hiệu chỉnh và đánh giá Grade10, kiểm riêng đóng góp')
    body=re.sub(r'<p><strong>Mốc đã đạt</strong>.*?</p>',lambda _:'<p>'+top.replace('**Mốc đã đạt**','<strong>Mốc đã đạt</strong>').replace('**Mốc còn thiếu**','<strong>Mốc còn thiếu</strong>')+'</p>',body,count=1,flags=re.S)
    css='.table-scroll{overflow-x:auto}.outer-metrics{min-width:700px}.outer-metrics th:first-child{width:12%}.outer-chart{margin:18px 0}'
    if css not in body:
        body=body.replace('</style>',css+'\n</style>',1)
    path.write_text(body,encoding='utf-8')
    for name in ('BAO_CAO.md','BAO_CAO_NGHIEN_CUU.html'):
        path=REPORT/name
        body=path.read_text(encoding='utf-8')
        body=body.replace('Còn bảng kết quả trên nhóm người học đánh giá riêng',
            'Đã có bảng chỉ số A0–A3 và so sánh theo người học trên fold 4')
        body=body.replace('**Tiến bộ mới là đã có đủ đầu ra dự báo của cả bốn mô hình trên phần hiệu chỉnh thực.**',
            '**Bước hiệu chỉnh đã hoàn tất cho cả bốn mô hình.**')
        body=body.replace('<strong>Tiến bộ mới là đã có đủ đầu ra dự báo của cả bốn mô hình trên phần hiệu chỉnh thực.</strong>',
            '<strong>Bước hiệu chỉnh đã hoàn tất cho cả bốn mô hình.</strong>')
        body=body.replace('So sánh chất lượng dự báo sau hiệu chỉnh và hiệu quả của đồ thị còn cần tập đánh giá độc lập.',
            'Bảng so sánh dự báo trên nhóm người học độc lập đã hoàn tất ở mốc kết quả phía trên.')
        body=body.replace('| Hiệu chỉnh | Dự báo đủ 4/4. A0–A3 đã hiệu chỉnh và xác minh artifact | Đã hoàn tất trên Junyi fold4 |',
            '| Hiệu chỉnh | Dự báo đủ 4/4. A0–A3 đã hiệu chỉnh và xác minh artifact | Còn hiệu chỉnh trên nhóm mô phỏng riêng |')
        body=body.replace('<td>Đã hoàn tất trên Junyi fold4</td>',
            '<td>Còn hiệu chỉnh trên nhóm mô phỏng riêng</td>')
        body=body.replace('Đánh giá trên quần thể nghiên cứu đầy đủ còn chờ.',
            'Đánh giá SAKT/GKT và ghép cùng quần thể với các baseline còn chờ.')
        body=body.replace('<strong>Đánh giá độc lập A0–A3 trên Junyi</strong> bằng bốn mô hình và hệ số đã đóng băng, giữ cùng nhóm người học và tương tác để so sánh dự báo và độ tin cậy xác suất.',
            '<strong>Khép đối chiếu baseline và chuyển sang Grade10.</strong> Benchmark Junyi A0–A3 hiện hành đã hoàn tất. Tiếp tục giữ cùng quần thể và giới hạn thông tin khi ghép các baseline; học lại/hiệu chỉnh Grade10 để kiểm lựa chọn bài và kết quả học.')
        path.write_text(body,encoding='utf-8')
    print('REPORT_UPDATED_FOUR_OUTER_MODELS_WITH_RAW_CALIBRATED_LIMITS')

if __name__=='__main__':
    main()
