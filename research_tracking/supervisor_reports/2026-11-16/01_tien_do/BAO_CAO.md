BÁO CÁO KẾT QUẢ VÀ TIẾN ĐỘ KLTN · 16/11/2026

# Đã giải quyết được gì trong ba câu hỏi nghiên cứu?

KLTN nghiên cứu cách chọn bài phù hợp với từng người học bằng sơ đồ kiến thức tiên quyết, tức kiến thức cần học trước–sau. Paper 1 đã khảo sát đồ thị và chính sách chọn bài. Paper 2 bổ sung mô hình dự báo kiến thức. Vấn đề tiếp nối là vì sao thêm đồ thị vẫn chưa cải thiện kết quả học rõ rệt.

**Đã có các phát hiện chẩn đoán cho RQ1–RQ2 và hoàn tất huấn luyện bốn phiên bản AKT trên Junyi.** Còn thiếu đánh giá độc lập và mô phỏng vòng kín để kết luận hiệu quả của CG-AKT trong RQ3.

## RQ1 — Vì sao đồ thị chưa giúp người học tiến bộ?

Cần phân biệt ba khả năng — dự báo chưa đủ tốt, xác suất chưa phù hợp với ngưỡng thành thạo, hoặc bộ chọn bài làm suy giảm ảnh hưởng của đồ thị.

### Thành quả đã có

**Đã giải thích được một số kết quả do quy tắc mô phỏng chi phối.** Với đồ thị nội chương và các điều kiện đã kiểm, số lần quay lại chương bằng **0** được bảo đảm bởi bộ chọn bài. Dưới luật quên đồng nhất, phần tăng điểm năng lực trung bình còn **43,17%** sau 14 ngày nếu không luyện thêm và phần tăng điểm không âm. Những kết quả này cần được đọc cùng giả định của mô phỏng.

**Đã đo sự suy giảm ảnh hưởng từ dự báo đến gợi ý chủ đề.** Trong pilot GAM-KT và gói bổ sung đồ thị, mỗi phép đối chiếu dùng cùng trạng thái người học.

| Thay đổi được ghi nhận | Số cặp / 1.080 | Tỷ lệ |
| --- | --- | --- |
| Xác suất dự báo đáp án | 964 | 89,3% |
| Đánh giá ít nhất một khái niệm đã thành thạo | 90 | 8,3% |
| Tập chủ đề đủ điều kiện học | 60 | 5,6% |
| Gợi ý chủ đề xem trước | 22 | 2,0% |


Bốn số đo riêng trên cùng 1.080 cặp. Các số đo ghi nhận sự thay đổi. Kết luận về cải thiện cần đánh giá riêng. Gợi ý xem trước chưa phải kết quả học tập vòng kín, mẫu này chưa đánh giá AKT.

**Đã trả lời được một phần nguyên nhân** — một số chỉ số bị thiết kế chi phối, và thay đổi dự báo thường chưa đi tới thay đổi gợi ý học.

**Còn thiếu để kết thúc RQ1** — hiệu chỉnh xác suất quanh ngưỡng thành thạo, kiểm đánh giá thành thạo so với trạng thái thật trong mô phỏng, rồi nối quyết định chọn bài với mức tiến bộ trên các lượt đánh giá độc lập.

## RQ2 — Đồ thị hữu ích, trung tính hoặc có hại trong điều kiện nào?

Cần xét chất lượng đồ thị, lượng lịch sử đã quan sát và đặc điểm người học, đồng thời tránh nhầm lợi ích của đồ thị với năng lực hoặc thứ tự luyện sẵn có.

### Đã tách thử ảnh hưởng của năng lực và cơ chế tiên quyết

Đã hoàn tất **120 lượt mô phỏng, mỗi lượt 120 bước**, gồm 10 bộ khởi tạo ghép cặp. Trong mỗi bộ, lần lượt đổi ba mức năng lực ban đầu, hai nguồn đồ thị và bật/tắt cơ chế phạt thiếu kiến thức tiên quyết.

Phép đo lấy chênh lệch giữa đồ thị chuyên gia và đồ thị học từ dữ liệu, rồi so chênh lệch đó khi bật/tắt cơ chế tiên quyết. Ở mức khởi tạo trung bình, phần tác động bổ sung dương trong **8/10 bộ** và âm trong **2/10 bộ**. Đối chứng mức cao cho tác động bổ sung bằng **0 trong cả 10/10 bộ**.

Đơn vị độc lập là 10 bộ khởi tạo. Kết quả thăm dò còn biến động, chưa xác nhận nhóm năng lực nào hưởng lợi hơn. Chênh lệch trực tiếp giữa hai đồ thị vẫn có thể tồn tại khi cơ chế tiên quyết bị tắt.

### Đã xác định giới hạn quan sát đồ thị trên Junyi

Kiểm **13.347.331 tương tác** của **126.774 người học** trong phần huấn luyện cho thấy trong 976 quan hệ tiên quyết, có 876 quan hệ từng gặp kiến thức cha trước câu hỏi con trong cửa sổ đầu vào, còn **100 quan hệ** thiếu điều kiện đó. Trong 100 quan hệ, 86 có ít nhất một bài nằm ngoài danh mục xuất hiện trong tập huấn luyện và 14 có đủ bài nhưng thiếu thứ tự phù hợp.

**Thành quả hiện có** — đã thiết lập đối chứng năng lực trong mô phỏng và chỉ ra vì sao một số phép thay đồ thị trên Junyi có thể quá ít tác động để tạo so sánh hữu ích. Còn cần kiểm liệu thứ tự luyện có làm lợi ích dự báo của đồ thị bị đánh giá quá cao.

**Còn thiếu để kết thúc RQ2** — đối chứng dự báo Junyi kiểm soát thứ tự luyện, thí nghiệm nhiễu thêm/xóa/đảo cạnh, lịch sử ngắn/dài, khái niệm ít dữ liệu, nhóm người học và quan hệ nội/liên chương, kèm bất định thống kê trên đánh giá chính.

## RQ3 — CG-AKT có cải thiện dự báo và kết quả học?

Giải pháp dùng độ tin cậy cho từng quan hệ và một cổng điều tiết để giảm hoặc tắt ảnh hưởng của đồ thị khi cần.

### Đã cài đặt và huấn luyện các biến thể cần so sánh

| Phiên bản | Vai trò nghiên cứu | Junyi · đồ thị chuyên gia |
| --- | --- | --- |
| A0 | AKT không đồ thị, làm đối chứng | Đã chọn bản mô hình và học lại 9 vòng |
| A1 | Đồ thị cố định | Đã chọn bản mô hình và học lại 9 vòng |
| A2 | Trọng số tin cậy từng cạnh | Đã chọn bản mô hình và học lại 9 vòng |
| A3 · CG-AKT | Độ tin cậy cạnh và cổng có thể tắt đồ thị | Đã chọn bản mô hình và học lại 9 vòng |


Mỗi bản học lại trên **142.621 người học**, với **14.947.674 tương tác mục tiêu mỗi vòng**. Các bản lưu mô hình và nhật ký đã được lưu và nghiệm thu. Phạm vi hiện có là một phép chia dữ liệu phát triển, một lần khởi tạo huấn luyện và nhóm đồ thị chuyên gia.

**Grade10** là môi trường Toán 10 riêng, có 28 khái niệm và biết trạng thái người học. Đã chọn bản mô hình cho **7 điều kiện** trên bộ 60 người học mô phỏng. Các mô hình này còn bước học lại và hiệu chỉnh để chạy đánh giá vòng kín.

**Thành quả RQ3 hiện tại là mô hình đã triển khai và các bản huấn luyện đã lưu.** Các mô hình cung cấp đầu vào để kiểm giải pháp. Hiệu quả so với đồ thị cố định và không đồ thị còn chờ đánh giá độc lập.

**Còn thiếu để kết thúc RQ3** — hiệu chỉnh và đánh giá dự báo độc lập, hoàn thiện mô hình Grade10, so A0–A3 trên cạnh thật/nhiễu, tách đóng góp độ tin cậy/cổng và đo kết quả học vòng kín. Kết quả cổng tắt đồ thị vẫn được chấp nhận nếu có bằng chứng.

## Đối chiếu sáu sprint trong đề cương

Đối chiếu theo đầu ra đã có và mốc còn thiếu. Các sprint đang được thực hiện đan xen. Hoàn tất huấn luyện mới khép một phần yêu cầu của Sprint 2 và Sprint 4.

| Sprint theo đề cương | Đầu ra đã có đến 16/11 | Mốc còn thiếu để khép sprint |
| --- | --- | --- |
| 1 · Khảo sát và tái lập | Có nguồn hai paper, đề cương, giả thuyết/quy trình. Đã kế thừa kết quả và tái kiểm chọn lọc các cơ chế mô phỏng. | Chốt đối chiếu từng kết quả chính cần tái lập của hai paper. Hồ sơ hiện tại chưa đủ xác nhận toàn sprint. |
| 2 · Dữ liệu và mô hình đối chứng | Junyi, Grade10 và phép chia đã chuẩn hóa. BKT/GAM-KT có benchmark 5-fold với 20.706.014 dự đoán ghép tương ứng, AKT đã huấn luyện. SAKT/GKT có cài đặt và kiểm trên bộ nhỏ. | SAKT/GKT và các đối chứng cần huấn luyện/đánh giá trên quần thể nghiên cứu phù hợp, hoàn thiện bảng so sánh chung. |
| 3 · Chẩn đoán nguyên nhân | Có các phát hiện RQ1 về mô phỏng, dự báo/thành thạo/gợi ý và ảnh hưởng bộ chọn bài. | Hiệu chỉnh quanh ngưỡng, kiểm quyết định chọn bài đầy đủ và kết quả trên lượt độc lập. |
| 4 · Phát triển phương pháp | Đã triển khai A0–A3, độ tin cậy cạnh, cổng và nhánh tắt đồ thị. Bốn bản Junyi với đồ thị chuyên gia đã học lại đầy đủ, Grade10 có 7 bản mô hình đã chọn. | Chốt chọn cấu hình, kiểm dự phòng, tách đóng góp từng thành phần và hoàn thiện huấn luyện/hiệu chỉnh Grade10. |
| 5 · Điều kiện hiệu lực | Có 120 lượt đối chứng mô phỏng, kiểm độ phủ Junyi và bất định thăm dò. | Ma trận nhiễu/lịch sử/ít dữ liệu/hồ sơ người học, vòng kín, thống kê và Holm cho đánh giá chính. |
| 6 · Hoàn thiện | Có báo cáo, bằng chứng/bản lưu mô hình và demo xem lại kết quả mô phỏng đã lưu. | Demo dùng mô hình mới, luận văn, gói tái lập cuối, bản thảo bài báo theo đề cương (sau phần KLTN), phản hồi GVHD và chuẩn bị bảo vệ. |


**Các mốc hoàn tất rõ nhất** gồm dữ liệu/phép chia, baseline BKT/GAM-KT, một số chẩn đoán cơ chế, cài đặt CG-AKT và huấn luyện bốn bản Junyi với đồ thị chuyên gia. Những mốc nghiệm thu còn thiếu tập trung ở đánh giá của Sprint 3–5 và phần hoàn thiện Sprint 6.

## Công việc ưu tiên tiếp theo
1. **Tận dụng bốn mô hình Junyi đã có** để hiệu chỉnh và đánh giá độc lập trên cùng các tương tác, hoàn thiện so sánh dự báo và độ tin cậy xác suất.
2. **Hoàn thiện huấn luyện/hiệu chỉnh Grade10 và chạy đánh giá dùng chung ba RQ**, theo dõi dự báo, thành thạo, chọn bài và mức tiến bộ trên các lượt mô phỏng ghép cặp.
3. **Thực hiện đối chứng thứ tự Junyi và các điều kiện RQ2**, rồi tổng hợp thống kê, demo và luận văn.

**Cơ sở báo cáo** · Đề cương KLTN trang 5 về sáu sprint, hai paper RIVF 2026, các thí nghiệm chẩn đoán 07–12/11 và nghiệm thu huấn luyện 12–16/11/2026. Kết quả thăm dò và kết quả huấn luyện được ghi theo phạm vi thực tế. Báo cáo chưa kết luận CG-AKT cải thiện kết quả học.

Nguồn chi tiết ở [rà soát RQ1–RQ2](../../../reports/RQ12_COMPLETION_REVIEW_20261116.md), [đối chiếu training](../../../reports/TRAINING_RQ_SCOPE_REVIEW_20261116.md) và [đề cương trang 5](../../../../docs/thesis_recovery/evidence/user_documents_20261108_proposal.txt).
