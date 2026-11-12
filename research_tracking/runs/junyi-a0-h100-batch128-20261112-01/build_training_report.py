"""Tổng hợp báo cáo H100 từ bằng chứng đã nghiệm thu, không chạy training."""
import base64
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
ROOT = BUNDLE.parents[2]
snapshot = json.loads((BUNDLE / 'epoch12-analysis-input.json').read_text())
history = snapshot['progress']['history']
training = snapshot['training']
assert len(history) == len(training) == 12
assert snapshot['selected_epoch'] == 9
image = base64.b64encode((BUNDLE / 'a0-h100-progress-final012v2.png').read_bytes()).decode()
rows = ''
for item, train in zip(history, training):
    epoch = item['epoch']
    note = {7:'Tăng nhẹ', 8:'Cải thiện trở lại', 9:'Checkpoint được chọn',
            10:'Giảm dưới mức cải thiện tối thiểu', 11:'Chưa cải thiện đủ',
            12:'Dừng sau ba epoch chưa cải thiện đủ'}.get(epoch, 'Tiếp tục theo quy tắc đã đặt')
    rows += (f'<tr class="{"chosen" if epoch == 9 else ""}"><td>{epoch}</td>'
             f'<td>{item["validation"]["native_bce"]:.9f}</td>'
             f'<td>{train["resource"]["wall_seconds"]:.1f}</td>'
             f'<td>{item["validation_seconds"]:.1f}</td><td>{note}</td></tr>')

content = f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>A0 trên H100 — báo cáo training Junyi</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f5f5;color:#203139;font:17px/1.65 system-ui,Segoe UI,sans-serif}}
main{{max-width:1120px;margin:auto;padding:48px 40px;background:white}}h1{{font-size:40px;line-height:1.2;margin:12px 0 20px}}
h2{{font-size:26px;margin:42px 0 14px}}h3{{font-size:20px}}p{{max-width:90ch}}.date,figcaption{{color:#52656d;font-size:14px}}
.lead{{font-size:20px}}.result{{background:#eaf3f3;border-left:5px solid #387488;padding:20px 24px;margin:24px 0}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{border:1px solid #d8e1e4;padding:16px}}.card strong{{display:block;font-size:27px;color:#2e6378}}
table{{width:100%;border-collapse:collapse;font-size:15px}}th,td{{text-align:left;padding:11px 12px;border-bottom:1px solid #dde4e7;vertical-align:top}}th{{background:#eef3f4}}.chosen{{background:#eaf3f3;font-weight:600}}
.table-wrap{{overflow-x:auto}}figure{{margin:24px 0}}img{{width:100%;height:auto}}a{{color:#28677f}}li{{margin:8px 0}}
footer{{border-top:1px solid #d8e1e4;margin-top:36px;padding-top:18px;font-size:14px;color:#52656d}}
@media(max-width:700px){{main{{padding:26px 18px}}h1{{font-size:30px}}.cards{{grid-template-columns:repeat(2,1fr)}}}}
@media print{{body{{background:white}}main{{padding:0}}h2,figure{{break-inside:avoid}}}}
</style></head><body><main>
<header><p class="date">KLTN · Training ngày 12/11/2026 · Tổng hợp ngày 13/11/2026 · Giờ Việt Nam</p>
<h1>Hoàn tất chọn checkpoint A0 trên Junyi bằng H100</h1>
<p class="lead">Đã huấn luyện AKT không dùng đồ thị qua 12 epoch, chọn checkpoint epoch 9 và lưu toàn bộ kết quả về ổ D. Ba phiên H100 đã dừng, số container hoạt động ở lần kiểm cuối bằng 0.</p></header>
<section><h2>Vai trò của lượt training này trong khóa luận</h2>
<p>Khóa luận cần kiểm tra liệu thông tin tiên quyết có giúp dự báo và quyết định lộ trình học hay không. A0 cung cấp mô hình AKT nền để đối chiếu với A1 dùng đồ thị cố định, A2 bổ sung độ tin cậy từng cạnh và A3 thêm cổng điều tiết ảnh hưởng đồ thị. Biến thể NonRasch bỏ thành phần độ khó Rasch. Cấu hình A0 hiện tại dùng lịch sử tương tác và giữ nhánh đồ thị tắt.</p>
<p>Junyi cung cấp tương tác học thật để đánh giá dự báo. Bộ mô phỏng Grade 10 có 28 khái niệm phục vụ các đối chứng kiểm soát và kết quả học vòng kín. Hai môi trường có bộ mã bài tập riêng, cần checkpoint được huấn luyện riêng. Báo cáo này tập trung vào A0 trên Junyi.</p>
<div class="result"><strong>Mốc đã đạt</strong><p>Hoàn tất giai đoạn huấn luyện trên train80 và chọn thời điểm dừng bằng selection10. Đã xuất 1.600.343 xác suất dự báo, nạp lại checkpoint được chọn và đối chiếu đầu ra. Refit trên train90, hiệu chỉnh xác suất và đánh giá độc lập còn ở giai đoạn tiếp theo.</p></div>
<div class="cards"><div class="card"><strong>12</strong>epoch hoàn tất</div><div class="card"><strong>9</strong>epoch được chọn</div><div class="card"><strong>1,60 triệu</strong>dự báo đã lưu</div><div class="card"><strong>0</strong>container còn chạy</div></div>
</section>
<section><h2>Từ chuẩn bị dữ liệu đến ba phiên H100</h2>
<p>Trước khi huấn luyện, gói nguồn được kiểm trên Linux CPU với 2.234 ca đạt. Lượt batch128 có phiên bản cấu hình riêng và bắt đầu từ seed 42. Sáu epoch batch4 trước đó được giữ thành lịch sử riêng. Sau đó, cùng một quá trình huấn luyện được chia thành ba phiên có giới hạn thời gian để giữ ngân sách và lưu trạng thái phục hồi.</p>
<div class="table-wrap"><table><thead><tr><th>Phiên</th><th>Khoảng thời gian</th><th>Tiến trình</th><th>Kết quả lưu lại</th><th>Credits tăng</th></tr></thead><tbody>
<tr><td>1</td><td>22:30:53–22:59:37</td><td>Epoch 1–5</td><td>20 gói checkpoint, archive 532 MB</td><td>$1,98</td></tr>
<tr><td>2</td><td>23:03:06–23:32:14</td><td>Phục hồi từ epoch 5, chạy 6–10</td><td>25 gói checkpoint gồm bản tiếp nhận từ phiên trước, archive 664 MB</td><td>$2,19</td></tr>
<tr><td>3</td><td>23:36:10–23:55:58</td><td>Phục hồi từ epoch 10, chạy 11–12, dừng và xuất dự báo</td><td>18 gói checkpoint gồm bản tiếp nhận từ phiên trước, archive 556 MB</td><td>$1,22</td></tr>
</tbody></table></div>
<p class="date">Khoảng thời gian tính từ lúc tạo đến lúc dừng App, bao gồm khởi động và kết thúc. Số gói checkpoint giữa các phiên có bản kế thừa, cần đọc theo cùng một quá trình huấn luyện.</p>
<p>Mỗi lần phục hồi sử dụng checkpoint cùng trạng thái optimizer, bộ sinh số ngẫu nhiên và bộ đếm bước. Các archive được tải về, kiểm toàn vẹn và đối chiếu inventory. Checkpoint epoch 9 được nạp lại để xuất bộ dự báo cuối, xác nhận đủ người học và đúng thứ tự thời gian.</p>
</section>
<section><h2>Dữ liệu và cấu hình đã sử dụng</h2>
<p>Giữ ranh giới người học theo outer fold 4 đã cố định. Bên trong outer-train, train80 dùng cập nhật trọng số, selection10 dùng chọn epoch và calibration10 được dành cho bước hiệu chỉnh tiếp theo. Tập outer-validation và Holdout được dành cho đánh giá độc lập.</p>
<table><tbody><tr><th>Train80</th><td>126.774 người học · 13.347.331 target mỗi epoch · 232.662 cửa sổ</td></tr>
<tr><th>Selection10</th><td>15.847 người học · 1.600.343 target · 0 bài tập ngoài vocabulary</td></tr>
<tr><th>Calibration10 dành riêng</th><td>15.847 người học, chưa dùng trong lượt chọn epoch này</td></tr>
<tr><th>Vocabulary</th><td>717 bài tập, mô hình AKT NonRasch ở cấp bài tập</td></tr>
<tr><th>Kiến trúc</th><td>d_model 256 · 8 đầu attention · 1 block · d_ff 1.024 · lớp cuối 512 · dropout 0,05</td></tr>
<tr><th>Tối ưu hóa</th><td>Adam · learning rate 0,0001 · clip gradient 1 · batch 128 · seed 42</td></tr>
<tr><th>Chuỗi và số học</th><td>Context 100 · target block 100 · độ dài tối đa 200 · FP32 · tắt TF32</td></tr>
<tr><th>Điều kiện dừng</th><td>Tối đa 20 epoch · patience 3 · cải thiện tối thiểu 0,0001</td></tr></tbody></table>
<p>Batch128 thay đổi số cập nhật optimizer so với batch4. Kết quả cần được đánh giá theo phiên bản cấu hình này, với các đối chứng được chốt ranh giới dữ liệu và cách chọn mô hình tương ứng. Mã nền AKT đã được ghim phiên bản để tái lập. <a href="https://github.com/arghosh/AKT/tree/01b7e8d7d7c862cabc9467108e3e7f2555653a88">Nguồn AKT gốc</a>.</p>
</section>
<section><h2>Diễn tiến học và lý do chọn epoch 9</h2>
<p>Sau mỗi lượt qua train80, mô hình dự báo trên cùng tập selection10. Log Loss đo mức phù hợp giữa xác suất dự báo và đáp án thật, giá trị thấp hơn cho thấy dự báo tốt hơn theo tiêu chí này. Theo dõi qua nhiều epoch giúp chọn thời điểm dừng trước khi tiếp tục huấn luyện mang lại quá ít cải thiện.</p>
<figure><img alt="Log Loss selection và thời gian train, validation qua 12 epoch" src="data:image/png;base64,{image}"><figcaption>Ngôi sao đánh dấu checkpoint được chọn theo quy tắc cải thiện tối thiểu. Thời gian validation được tách khỏi thời gian cập nhật trọng số. Mỗi epoch giữ nguyên tập target.</figcaption></figure>
<div class="table-wrap"><table><thead><tr><th>Epoch</th><th>Log Loss selection</th><th>Train, giây</th><th>Validation, giây</th><th>Diễn giải</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Epoch 7 tăng nhẹ, sau đó epoch 8 và 9 tiếp tục cải thiện. Quy tắc patience 3 cho phép quan sát diễn tiến này. Epoch 10 có giá trị thô thấp hơn epoch 9 khoảng 0,000020, nhỏ hơn mức cải thiện tối thiểu 0,0001 nên checkpoint được chọn vẫn ở epoch 9. Ba epoch 10–12 đều chưa đạt mức cải thiện yêu cầu và lượt học dừng sau epoch 12.</p>
<p>Toàn lượt có 21.816 cập nhật optimizer và 160.167.972 lượt target qua 12 epoch. Checkpoint được chọn chứa trọng số sau 9 epoch.</p>
</section>
<section><h2>Chất lượng dự báo hiện có thể báo cáo</h2>
<p>Các chỉ số sau được tính từ dự báo checkpoint epoch 9 trên selection10, dùng chung hàm metric với pipeline GAM-KT. Chúng mô tả kết quả chọn checkpoint. So sánh chính thức với BKT/GAM-KT cần bộ dự báo trên cùng tập đánh giá độc lập và cùng quy định coverage.</p>
<table><thead><tr><th>Chỉ số</th><th>Giá trị</th><th>Mục đích theo dõi</th></tr></thead><tbody>
<tr><td>AUC</td><td>0,805990</td><td>Khả năng xếp tương tác trả lời đúng cao hơn tương tác trả lời sai.</td></tr>
<tr><td>Log Loss</td><td>0,353580</td><td>Chất lượng xác suất, có phạt mạnh khi mô hình rất tự tin nhưng dự báo sai.</td></tr>
<tr><td>Brier Score</td><td>0,107700</td><td>Sai lệch bình phương giữa xác suất và đáp án.</td></tr>
<tr><td>ECE, 15 khoảng đều</td><td>0,004270</td><td>Mức chênh giữa xác suất và tần suất đúng trong các nhóm dự báo.</td></tr></tbody></table>
<p>ECE toàn tập còn cần được bổ sung bằng kiểm tra quanh ngưỡng thành thạo để phục vụ RQ1. Các kết quả trên chưa xác lập lợi ích của đồ thị, cải thiện lộ trình hoặc kết quả học vòng kín.</p>
</section>
<section><h2>Thời gian, tài nguyên và chi phí thực tế</h2>
<p>Trung bình mỗi epoch mất khoảng <strong>2 phút 03 giây train</strong> và <strong>3 phút 18 giây validation</strong>, tổng khoảng <strong>5 phút 21 giây</strong>. Cộng 12 epoch có 24 phút 32 giây train và 39 phút 42 giây validation. Khởi động, phục hồi, lưu checkpoint và xuất dự báo cuối phát sinh thêm thời gian.</p>
<p>2.187 mẫu đo trong quá trình xử lý ghi mức hoạt động GPU trung bình 26,49%, cao nhất 74%, VRAM cao nhất 5.793 MiB và công suất trung bình 195,3 W. Mẫu đo bao gồm train, validation và xuất dự báo cuối. Mức sử dụng toàn lượt cho thấy còn dư địa tối ưu, đặc biệt validation đang chiếm nhiều thời gian hơn train. Cần đo riêng từng pha để xác định lợi ích của thay đổi tiếp theo.</p>
<p>Chuyển sang H100 cùng batch128 đã rút ngắn chu kỳ thực tế so với lượt T4 batch4 trước đó. Hai yếu tố phần cứng và batch cùng thay đổi, nên cần giữ giới hạn diễn giải khi quy mức tăng tốc cho từng yếu tố.</p>
<table><tbody><tr><th>Ba phiên H100 của A0</th><td>Credits tăng khoảng <strong>$5,39</strong></td></tr>
<tr><th>Tổng KLTN tại snapshot cuối</th><td>Đã dùng khoảng <strong>$8,67</strong> · còn <strong>$21,33</strong> trong $30 free credits</td></tr>
<tr><th>Tiền billed được ghi nhận</th><td>$0 tại snapshot cuối</td></tr>
<tr><th>Trạng thái tài nguyên</th><td>Cả ba App đã dừng · kiểm server ghi 0 container</td></tr></tbody></table>
<p class="date">Chi phí là chênh lệch snapshot credits trong các phiên, có thể chịu độ trễ cập nhật billing. Chi phí kiểm CPU trước H100 được ghi riêng. Modal tính tài nguyên theo thời gian sử dụng, gồm GPU, CPU và RAM. <a href="https://modal.com/pricing">Bảng giá Modal</a>.</p>
</section>
<section><h2>Kết quả đã giữ và bước tiếp theo</h2>
<p>Đã xuất model chính thành một file <strong>A0_JUNYI_SELECTED.pt</strong>, kèm cấu hình, vocabulary và nguồn cần để nạp bằng adapter AKT của dự án. Checkpoint lưu cả trọng số, optimizer và trạng thái phục hồi. Các checkpoint trung gian, dự báo, nhật ký, dữ liệu dựng hình và bản SVG/PDF độc lập được giữ trong hồ sơ nghiên cứu trên ổ D.</p>
<ol><li>Chốt giao thức so sánh cho cấu hình batch128 và các biến thể AKT còn lại, cùng dự toán theo ngân sách còn lại.</li>
<li>Thực hiện refit trên train90 theo số epoch đã chọn, giữ ranh giới calibration và đánh giá độc lập.</li>
<li>Hiệu chỉnh xác suất trên phần dành riêng, xuất dự báo đánh giá cùng các baseline và khoảng tin cậy theo người học.</li>
<li>Hoàn thiện đối chứng A1/A2/A3 và đánh giá mô phỏng để trả lời RQ3 về dự báo, gate, quyết định và kết quả vòng kín.</li></ol>
<div class="result"><strong>Kết luận tiến độ</strong><p>A0 Junyi đã hoàn tất giai đoạn chọn checkpoint trên dữ liệu train80 đầy đủ của một outer fold, có model và bộ dự báo được lưu, kiểm và truy xuất lại. Các bước refit, hiệu chỉnh và đánh giá độc lập sẽ cung cấp bằng chứng cho kết luận so sánh của khóa luận.</p></div>
</section><footer>Báo cáo được tổng hợp từ lịch sử 12 epoch, kiểm archive/checkpoint, dự báo đã xuất, telemetry GPU và snapshot billing của ba phiên H100. Hình và bảng được dựng từ số liệu đã lưu. Ngày chốt 13/11/2026.</footer>
</main></body></html>'''
destination = ROOT / 'research_tracking/supervisor_reports/2026-11-13/BAO_CAO_A0_H100.html'
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(content, encoding='utf-8')
print(destination)
