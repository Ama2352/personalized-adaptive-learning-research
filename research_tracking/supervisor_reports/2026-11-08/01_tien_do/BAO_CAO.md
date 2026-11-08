# Báo cáo tiến độ khóa luận — 08/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương và Hồ Nguyễn Minh Sang.

[Báo cáo chi tiết: diễn tiến nghiên cứu, số liệu và biểu đồ](BAO_CAO_NGHIEN_CUU.html).

## Điểm xuất phát và tiến độ hiện tại

Paper 1 cho thấy tính liên tục của lộ trình chịu ảnh hưởng của cách chọn bài, trong khi đồ thị mở rộng chưa cải thiện ổn định mức thành thạo. Paper 2 quan sát cải thiện dự báo nhỏ ở một số nhóm mô phỏng nhưng chưa phát hiện lợi ích rõ ở kết quả học tập chính. Khóa luận đi tiếp từ khoảng trống này: vì sao đồ thị chưa giúp ổn định, khi nào nó có ích và liệu CG-AKT sử dụng độ tin cậy cạnh có cải thiện được không?

**Đã có bằng chứng chẩn đoán mới cho RQ1–RQ2 và bước ước lượng cạnh đã thực chạy cho RQ3. Chưa RQ nào hoàn tất; chưa có kết quả CG-AKT đã huấn luyện để kết luận mô hình này tốt hơn.**

## Quá trình đã thực hiện

**Trước hết, nhóm kiểm lại nền thí nghiệm.** Đã dựng phản ví dụ quay lại chương trên mã Paper 1 hiện có, nhưng chưa xác minh đó là đúng phiên bản tạo PDF nên không dùng để bác bỏ paper. Đã làm rõ khi tiến bộ ròng sau 14 ngày chỉ tỷ lệ với tiến bộ cuối lịch; điều này không chứng minh hai kết quả chính của Paper 2 dư thừa. Trên Junyi, đã lượng hóa trường hợp tỷ lệ khớp thứ tự tăng dù số trường hợp phù hợp giảm, do mẫu số thay đổi. Những kiểm tra này giúp tránh coi giả định mô phỏng hoặc thứ tự luyện là bằng chứng đồ thị dạy tốt.

**Sau đó, nhóm tách riêng đầu vào cạnh trên cùng tình huống.** Trong 1.080 câu hỏi/nhãn được giữ chung, 963 dự báo thay đổi nhưng 943 trong số đó giữ đề xuất khái niệm xem trước; chỉ 22 đề xuất thử đầy đủ thay đổi. Tác động dự báo khác chiều giữa các hồ sơ. Phân tích bản tái dựng quỹ đạo còn cho thấy 2.041/2.740 lượt chọn khái niệm có tiên quyết cần ngoại lệ đã luyện đủ lần, thay vì mọi kiến thức nền được đánh dấu thành thạo. Đã xác định được cơ chế cụ thể trong quyết định cho phép học; chưa chứng minh cơ chế này gây lợi, gây hại hoặc che khuất bao nhiêu tác động của đồ thị.

**Tiếp theo, nhóm kiểm điều kiện người học.** Đối chứng thay lượng lịch sử không cho một chiều tác động đều. Đối chứng năng lực chung và mức phạt thiếu nền tảng không cho lợi thế đồ thị tăng nhất quán khi bật mức phạt. Đây là kết quả hữu hạn trong mô phỏng với ba khối ngẫu nhiên dùng lại, chưa phải quy luật về học sinh thật hoặc đánh giá đầy đủ các mức nhiễu đồ thị.

**Từ đó, nhóm chuẩn bị phép kiểm CG-AKT.** Đã tạo corpus mô phỏng riêng gồm 60 người học ×210 lượt, phân vai 48 huấn luyện /6 chọn số vòng học /6 hiệu chỉnh xác suất. Bước ước lượng cạnh từ TRAIN đã hoàn tất 2.352 lần khớp mô hình CPU và tạo đồ thị ứng viên 31 cạnh theo quy tắc định trước. Điểm cạnh phản ánh mức ổn định của lợi ích dự báo, không phải xác suất tiên quyết đúng; chưa chứng minh khôi phục đúng đồ thị hoặc cải thiện CG-AKT. Các pipeline mô hình tiếp tục được hoàn thiện và kiểm tra.

## Còn phải chứng minh

- **RQ1:** lượng hóa vai trò của hiệu chỉnh xác suất, ngưỡng thành thạo và bộ chọn bài; nối chẩn đoán với kết quả học tập.
- **RQ2:** kiểm khả năng khái quát qua đồ thị nhiễu, nhóm khái niệm và người học mới, với đối chứng đúng quần thể.
- **RQ3:** hoàn tất mô hình và so sánh không đồ thị / đồ thị cố định / confidence / gate theo cùng quy trình, sau đó đánh giá chọn bài và kết quả học vòng kín.

Các mô hình và demo trong đề cương vẫn được giữ. Kết quả không cải thiện hoặc cổng chọn tắt đồ thị vẫn được báo cáo nếu bằng chứng hỗ trợ; chưa có kết luận ưu thế của CG-AKT hoặc hiệu quả giáo dục trên người học thật.
