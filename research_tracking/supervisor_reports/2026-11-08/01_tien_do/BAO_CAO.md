# Tiến độ khóa luận đến ngày 08/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương và Hồ Nguyễn Minh Sang.

## 1. Hiện đã đạt được gì?

Nhóm đã có các kết quả chẩn đoán giúp giải thích vì sao đưa đồ thị tiên quyết vào hệ thống không luôn cải thiện kết quả. Nhóm cũng đã tạo được bộ dữ liệu mô phỏng Development để bắt đầu đánh giá mô hình trên cùng dữ liệu. Các thành quả hiện có chia thành ba loại:

| Thành quả | Ý nghĩa cho khóa luận | Đọc kết quả |
|---|---|---|
| Đã đối chiếu dự báo, phân loại thành thạo, tập sẵn sàng và lựa chọn xem trước trên cùng lịch sử | Chỉ ra trường hợp dự báo đổi nhưng lựa chọn không đổi; chưa suy ra cơ chế trung gian nhân quả | [RQ1: so sánh cùng hệ thống](tai_lieu/02_chuoi_du_bao_quyet_dinh.md) |
| Đã thực hiện các đối chứng về lịch sử, năng lực và cơ chế tiên quyết | Phân biệt tác động của thông tin đầu vào với tác động do cách xây simulator | [Lịch sử](tai_lieu/03_can_thiep_lich_su.md), [năng lực](tai_lieu/04_nang_luc_va_tien_quyet.md) |
| Đã sinh dữ liệu mô phỏng60 người học, 12.600 tương tác | Có đầu vào thực cho quy trình train/chọn epoch/refit/calibration; trước đây mới có dữ liệu smoke nhỏ | [Corpus](tai_lieu/07_corpus.md) |

**Chưa có kết quả so sánh CG-AKT đã huấn luyện nghiên cứu với AKT không đồ thị và AKT đồ thị cố định. Chưa RQ nào hoàn tất.** Các kiểm thử phần mềm không được tính như bằng chứng mô hình cải thiện việc học.

## 2. RQ1 — Vì sao đồ thị không luôn tạo ra lợi ích?

So sánh hai bộ ước lượng có cùng cơ chế, khác đầu vào cạnh tiên quyết, trên 1.080 điểm dự báo chung (3 block ngẫu nhiên × 3 profile × 120 bước) cho thấy: 963 điểm đổi xác suất dự báo, nhưng 943 trong số đó vẫn giữ lựa chọn khái niệm xem trước. Xác suất ở đây dành cho bài đang hỏi, không đại diện toàn bộ vector điểm 28 khái niệm. Tổng cộng chỉ 22/1.080 lựa chọn xem trước khác nhau. Sai số Log Loss trung bình giảm khoảng 0,000637; chiều cải thiện không đồng đều giữa các nhóm người học mô phỏng.

**Nhận định được hỗ trợ:** thay đổi xác suất cho bài đang hỏi có thể đi cùng lựa chọn xem trước không đổi; các tổng trên chưa chứng minh chuỗi tác động nhân quả. Đánh giá riêng điểm dự báo chưa đủ để chứng minh hệ thống chọn bài tốt hơn.

**Chưa kết luận được:**22 lựa chọn xem trước khác nhau có cải thiện học tập thực hay không. Đây không phải 1.080 người học độc lập; cũng chưa phải bằng chứng nhân quả trên học sinh thật. [Số liệu và nguồn](tai_lieu/02_chuoi_du_bao_quyet_dinh.md).

## 3. RQ2 — Khi nào thông tin tiên quyết có ích, trung tính hoặc bất lợi?

Ba nguy cơ thiết kế theo góp ý GVHD đã được đưa vào chương trình chẩn đoán:

| Nguy cơ | Đã làm và thấy gì | Còn phải làm |
|---|---|---|
| Simulator có thể cài sẵn kết quả | Khi không luyện thêm sau T, forgetting đồng nhất và gain không âm so với base cố định, retained net mean-theta gain sau 14 ngày chỉ là 0,4317105 lần final net gain. Tuy nhiên phản ví dụ cho thấy chỉ số soft-mastery retention có thể đảo thứ hạng | Kiểm trên quỹ đạo có thể sinh thật; không suy mọi chỉ số retention đều vô dụng. [Chi tiết](tai_lieu/05_retention.md) |
| Lợi thế graph bị lẫn với năng lực chung | Đã chạy 36 quỹ đạo / 4.320 tương tác, giữ cấu trúc trạng thái và chuỗi ngẫu nhiên chung, thay năng lực và bật/tắt penalty tiên quyết. Lợi thế tương đối không nhất quán dương; graph vẫn có thể khác ở nơi penalty không tác động | Chưa đủ kết luận cho quần thể người học;3 block ngẫu nhiên được tái sử dụng. Cần phân tích cơ chế và mở rộng theo protocol. [Chi tiết](tai_lieu/04_nang_luc_va_tien_quyet.md) |
| Thứ tự Junyi có thể tạo lợi thế giả cho graph thật | Đã phân tích order-only trên 256 người học inner-train / 12.575 tương tác, có graph controls và kiểm tra trên tập so sánh chung | Liên hệ giữa thứ tự đã ghi và graph không chứng minh lợi ích giảng dạy. Chưa được coi kết quả này là hiệu quả graph. [Chi tiết](tai_lieu/06_dieu_kien_va_junyi.md) |

Đối chứng lịch sử mới kiểm 54 trường hợp dùng đầy đủ lịch sử khớp kết quả gốc trước khi rút ngắn đầu vào. Kết quả cho thấy ảnh hưởng của graph không tăng đều theo lượng lịch sử. Việc rút ngắn đã tác động cả bộ ghi nhớ của controller, nên chưa tách riêng hiệu ứng của mô hình KT. [Thiết kế và kết quả](tai_lieu/03_can_thiep_lich_su.md).

## 4. RQ3 — CG-AKT đang ở đâu?

Đã có các thành phần mã nguồn AKT, graph confidence/gate và kiểm kỹ thuật ở quy mô nhỏ. Corpus mới tách 48 người học train, 6chọn epoch và 6 calibration, mỗi người 210 tương tác; có 84 bài tập. 150 người học final mới ở dạng metadata, chưa sinh tương tác final.

**Phần còn thiếu để có kết quả nghiên cứu:** nghiệm thu toàn bộ quy trình huấn luyện → chọn epoch → refit mới → calibration → xuất dự báo; sau đó chạy các mô hình đối chứng trên cùng giao thức và đo cả dự báo, quyết định, kết quả học trong simulator.

Junyi và simulator Toán10 có từ vựng khác nhau, phải huấn luyện riêng; không dùng trực tiếp checkpoint Junyi để kết luận trong simulator. Cấu hình không đồ thị là đối chứng bắt buộc; kết quả graph không cải thiện vẫn được giữ.

## 5. Vấn đề đã xử lý và việc chưa xử lý

**Đã xử lý trong phạm vi đã kiểm:** bảo toàn nguồn và kết quả lịch sử; đối chiếu đầy đủ lịch sử trước can thiệp; tạo đối chứng năng lực có giữ residual/chuỗi ngẫu nhiên chung; sinh, kiểm và xuất corpus có phân vai dữ liệu rõ ràng. Xem [bảng nghiệm thu theo file](BANG_CHUNG.md).

**Chưa xử lý xong:** huấn luyện nghiên cứu AKT/CG-AKT; confidence ước lượng từ train; so sánh đầy đủ required models; thống kê cuối và closed-loop với mô hình fitted; demo cá nhân hóa trực tiếp; bản luận văn hoàn chỉnh. Exact revision Paper1 khớp PDF vẫn chưa xác định được. BKT Holdout đã từng được truy cập trong lịch sử, nên không gọi đó là tập kiểm tra chưa đụng tới.

## 6. Ba mốc tiếp theo

1. **Nghiệm thu A0 không đồ thị:** checkpoint, dự báo chọn epoch/refit/calibration và manifest đầy đủ; chứng minh không dùng calibration để chọn epoch. Đây là pilot quy trình, chưa là mô hình thắng chung.
2. **Nối và kiểm các đối chứng:** fixed-graph, confidence/gate và các baseline theo đề cương; cùng dữ liệu/target, có graph-off và graph-noise controls.
3. **Đánh giá và viết:** tổng hợp tác động từ dự báo đến hành động/kết quả học, thống kê theo đơn vị người học/seed phù hợp, cập nhật notebook và chương kết quả, giữ cả kết quả âm.

Ngân sách chỉ 30 USD free credits, trả thêm 0 USD; chưa sử dụng Modal trong các batch được tổng hợp. Chưa đo runtime và tổng chi phí GPU cho quy trình nghiên cứu đầy đủ cùng workload reference/controller; các kiểm tra GPU nhỏ trước đây không đủ để dự toán phần này. Kế hoạch đầy đủ hiện có 36 pha tối ưu hóa neural ở hai môi trường, chưa tính mọi bước phụ; không thể coi một lần train AKT là hoàn tất khóa luận. [Dự toán khối lượng](tai_lieu/09_khoi_luong_training.md).
