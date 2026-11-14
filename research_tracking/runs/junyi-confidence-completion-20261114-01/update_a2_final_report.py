"""Cập nhật hai báo cáo GVHD bằng kết quả A2 đã nghiệm thu và figure độc lập."""
from collections import Counter
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REPORT=ROOT/'research_tracking/supervisor_reports/2026-11-10/01_tien_do'
acceptance=json.loads((HERE/'a2-final-acceptance.json').read_text())
assert acceptance['status']=='PASS_A2_SELECTED_FIT80_ARTIFACT_AND_PREDICTION_CONTRACT'
metrics=json.loads((HERE/'a2-selection-metrics.json').read_text())['metrics']
comparison=json.loads((HERE/'a2-comparison-audit.json').read_text())
performance=json.loads((HERE/'a2-final-performance.json').read_text())
export=json.loads((HERE/'a2-export-result.json').read_text())
billing=json.loads((HERE/'a2-billing-after10.json').read_text())


def vn(value):
    return f'{value:.6f}'.replace('.',',')


heading='14/11 — A2 hoàn tất bước chọn checkpoint trên Junyi'
paragraphs=[
    'Để kiểm tra độ tin cậy từng cạnh có giúp mô hình dự báo tốt hơn hay không trong RQ3, đã hoàn tất huấn luyện A2 trên Junyi. A2 bổ sung trọng số độ tin cậy vào AKT NonRasch. Bộ trọng số được ước lượng từ TRAIN80 trước khi học mô hình. Lượt này dùng Development outer fold 4 theo protocol đã chốt. Tập train gồm 126.774 người học và 13.347.331 lượt trả lời, tập chọn checkpoint gồm 15.847 người học và 1.600.343 lượt trả lời. Các nhóm người học được tách riêng và giữ đúng ranh giới dữ liệu của A0/A1.',
    'Sau mỗi epoch, mô hình dự đoán trên nhóm chọn checkpoint. Log Loss theo dõi mức phù hợp của xác suất dự báo với câu trả lời thực tế và phạt mạnh các dự đoán sai nhưng quá tự tin. A2 đã chạy 12 epoch, chọn checkpoint epoch 9 và nạp lại thành công. Toàn bộ 1.600.343 dự đoán xuất ra khớp quần thể và thứ tự thời gian, không có bài tập OOV.',
    'Epoch 10 có điểm thấp hơn epoch 9 khoảng 0,000045, chưa vượt mức cải thiện tối thiểu 0,0001 đã chốt. Vì vậy bộ chọn giữ epoch 9 và dừng sau ba epoch chưa cải thiện đủ. Đây là kết quả của cùng quy tắc chọn checkpoint được áp dụng cho các biến thể AKT.',
    'Các điểm chọn checkpoint của A0, A1 và A2 hiện rất gần nhau. Quan sát này chưa cho thấy một khác biệt lớn về dự báo do thêm độ tin cậy cạnh trên nhóm selection. Cần đánh giá độc lập và lượng hóa độ bất định trước khi kết luận hơn kém. A0 đã được chấm lại tại checkpoint epoch 9 bằng batch 128, phần đối chiếu lại toàn bộ lịch sử chọn epoch A0 còn chờ.',
    'Đã tải và kiểm đủ 210 artifact của lượt cuối, lưu checkpoint, dự đoán và log trên ổ D. Gói model A2 gồm một file .pt cùng cấu hình, graph, confidence và nguồn để dựng lại. Nhánh Junyi hiện có A0, A1 và A2 đã hoàn tất selected-fit. A3 có thêm cổng điều chỉnh ảnh hưởng đồ thị, refit, calibration và đánh giá độc lập còn chờ. Kết quả hiện tại bổ sung bằng chứng triển khai và dự báo, chưa hoàn tất phần quyết định lộ trình và mô phỏng vòng kín của RQ3.'
]
rows=[(item['model'].replace('_EXPERT',''),{'A0':'AKT không đồ thị','A1_EXPERT':'AKT đồ thị cố định','A2_EXPERT':'AKT theo độ tin cậy cạnh'}[item['model']],vn(item['native_bce'])) for item in comparison['models']]
metric_rows=[('AUC',vn(metrics['auc']),'Khả năng phân biệt câu trả lời đúng và sai'),
    ('Log Loss',vn(metrics['log_loss']),'Độ phù hợp của xác suất dự báo với kết quả'),
    ('Brier',vn(metrics['brier']),'Sai lệch bình phương của xác suất'),
    ('ECE',vn(metrics['ece']),'Độ khớp xác suất và tỷ lệ đúng trong 15 nhóm')]
sample_count=format(performance['nvml_samples'],',').replace(',','.')
gpu_mean=format(performance['mean_sampled_gpu_utilization'],'.2f').replace('.',',')
resource=('Hai lượt H100 dùng tổng cộng 47 phút 19 giây trong function, trung bình pha train khoảng 3 phút 03 giây mỗi epoch. '
    f'Trung bình {sample_count} mẫu NVML là {gpu_mean}%, VRAM đỉnh khoảng 5,65 GiB. '
    'Mục tiêu GPU trên 50% chưa đạt. Chuẩn bị input, upload và tải/nén artifact chạy ngoài thời gian thuê GPU. '
    'Mức CPU bảo đảm được tăng từ 0,25 lên 2 vCPU ở lượt tiếp tục, cùng hai luồng Torch, chưa có đối chứng xác nhận tăng tốc. '
    'Modal báo tổng metered toàn workspace khoảng 19,10 USD ở lần đọc sau training, billed cost bằng 0. Trần toàn KLTN vẫn là 30 USD.')
svg_path=HERE/'figures/a2-junyi-selection-v01.svg'
svg=svg_path.read_text(encoding='utf-8')
svg=svg[svg.index('<svg'):]
mapping={value:'a2-junyi-v01-'+value for value in re.findall(r'\bid="([^"]+)"',svg)}
svg=re.sub(r'\bid="([^"]+)"',lambda match:'id="'+mapping[match[1]]+'"',svg)
svg=re.sub(r'url\(#([^)]+)\)',lambda match:'url(#'+mapping.get(match[1],match[1])+')',svg)
svg=re.sub(r'((?:xlink:)?href)="#([^"]+)"',lambda match:match[1]+'="#'+mapping.get(match[2],match[2])+'"',svg)
table='<div class="table-scroll"><table><caption>Điểm dùng chọn checkpoint trên cùng nhóm selection</caption><thead><tr><th>Mô hình</th><th>Cấu hình</th><th>Log Loss</th></tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(value)+'</td>' for value in row)+'</tr>' for row in rows)+'</tbody></table></div>'
details='<details><summary>Chấm lại file dự đoán bằng bộ metric dùng chung</summary><p>Đã tính lại từ file dự đoán bằng hàm chấm được dùng cho GAM-KT. Các điểm này mô tả nhóm dùng chọn epoch, chưa phải kết quả đánh giá độc lập. ECE toàn cục còn cần được bổ sung bằng kiểm tra quanh ngưỡng thành thạo.</p><div class="table-scroll"><table><thead><tr><th>Metric</th><th>A2</th><th>Mục đích</th></tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(value)+'</td>' for value in row)+'</tr>' for row in metric_rows)+'</tbody></table></div></details>'
figure='<figure><div class="svg-frame">'+svg+'</div><figcaption>Diễn biến chọn checkpoint A2 trên 1.600.343 lượt trả lời selection. Chấm đỏ đánh dấu epoch được chọn theo quy tắc cải thiện tối thiểu và patience đã chốt. Đã giữ SVG, PNG, bảng số liệu và cách dựng lại trong hồ sơ nghiên cứu.</figcaption></figure>'
html_section='<section id="cap-nhat-20261114-a2-dispatch"><h2>'+heading+'</h2>'
html_section+=''.join('<p>'+escape(p)+'</p>' for p in paragraphs[:3])+figure+table
html_section+=''.join('<p>'+escape(p)+'</p>' for p in paragraphs[3:])+details
html_section+='<details><summary>Thời gian thực thi và sử dụng tài nguyên</summary><p>'+escape(resource)+'</p></details></section>\n'
html=REPORT/'BAO_CAO_NGHIEN_CUU.html'
raw=html.read_bytes()
start=raw.index(b'<section id="cap-nhat-20261114-a2-dispatch">')
end=raw.index(b'<section id="cap-nhat-20261114-confidence-completion">',start)
raw=raw[:start]+html_section.encode()+raw[end:]
raw=raw.replace('<title>Báo cáo nghiên cứu KLTN — 13/11/2026</title>'.encode(),'<title>Báo cáo nghiên cứu KLTN — 14/11/2026</title>'.encode())
html.write_bytes(raw)
md=REPORT/'BAO_CAO.md'
raw=md.read_bytes()
start=raw.index('## 14/11 — A2 '.encode())
end=raw.index('## 14/11 — Hoàn tất confidence'.encode(),start)
md_section='## '+heading+'\n\n'+'\n\n'.join(paragraphs[:3])+'\n\n'
md_section+='![Lịch sử chọn checkpoint A2](../../../runs/junyi-confidence-completion-20261114-01/figures/a2-junyi-selection-v01.svg)\n\n'
md_section+='| Mô hình | Cấu hình | Log Loss chọn checkpoint |\n|---|---|---|\n'+''.join('| '+' | '.join(row)+' |\n' for row in rows)+'\n'
md_section+='\n\n'.join(paragraphs[3:])+'\n\n'
md_section+='| Metric trên selection | A2 | Mục đích |\n|---|---|---|\n'+''.join('| '+' | '.join(row)+' |\n' for row in metric_rows)+'\n'+resource+'\n\n'
md_section+='[Hồ sơ nghiệm thu A2](../../../runs/junyi-confidence-completion-20261114-01/a2-final-acceptance.json), [bằng chứng và giới hạn](../../../runs/junyi-confidence-completion-20261114-01/README.md), [gói model trên D](../../../../experiments/akt/results/model-export-a2-batch128-20261114-01/README.md).\n\n'
md.write_bytes(raw[:start]+md_section.encode()+raw[end:])


class Inventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        self.ids.extend(value for name,value in attrs if name=='id')


inventory=Inventory()
inventory.feed(html.read_text(encoding='utf-8'))
duplicates=[name for name,count in Counter(inventory.ids).items() if count>1]
assert not duplicates,duplicates
assert html_section.count('<svg')==1 and 'sha256' not in html_section.lower()
check=dict(status='PASS_A2_REPORT_STATIC_AND_FIGURE_QA',svg_ids_namespaced=True,duplicate_ids=duplicates,
    displayed_models=3,selected_epoch=9,complete_epochs=12,figure_source=str(svg_path.relative_to(ROOT)),
    qa_vi='Đã xem PNG độc lập, nhãn không đè nhau. Kiểm cấu trúc HTML/ID, chưa mở trình duyệt.')
(HERE/'a2-report-verification.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(check,ensure_ascii=False))
