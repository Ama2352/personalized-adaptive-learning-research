# RQ1 — đối chiếu thành thạo tại các câu do hệ thống chọn

Ngày 09/11/2026. Phân tích mô tả trên một lịch sử dùng lại, không tăng số mẫu độc lập.

Paper2 dùng dự báo đáp án để cập nhật trạng thái kiến thức, rồi dựa vào trạng thái đó để quyết định khái niệm nào đã thành thạo. Sau các phép kiểm đường đi, nhóm quay lại câu hỏi nền của RQ1. Quyết định thành thạo có phản ánh trạng thái thật trong simulator tại các câu đang được giao hay không?

Nhóm dùng lại nhật ký đã kiểm của một lịch sử thuộc hồ sơ năng lực cao PG, gồm 120 lượt hỏi trước khi cập nhật bằng đáp án hiện tại. Hai đường đưa tín hiệu và điều chỉnh theo cha vào bộ ước lượng được tắt, điều chỉnh cục bộ được tắt. Bộ chọn bài vẫn giữ đồ thị tiên quyết. Các bản ghi được ghép chính xác theo câu hỏi, khái niệm, dự báo và lịch thời gian với trạng thái thật đã lưu của simulator.

Theo quy tắc Paper2, mô hình công nhận thành thạo khi điểm kiến thức ước lượng đạt 1250 và điều kiện về bất định cùng đạt. Phép đối chiếu dùng tiêu chí latent của simulator tại cùng ngưỡng 1250. Cả 120 khái niệm đang được hỏi đều đạt tiêu chí latent, trong khi điểm ước lượng ở những thời điểm đó đều dưới ngưỡng. Số lượt có điểm ước lượng đạt để xét vai trò chặn bổ sung của điều kiện bất định bằng 0.

| Đánh giá của mô hình tại câu được hỏi | Simulator chưa đạt ngưỡng | Simulator đạt ngưỡng |
|---|---:|---:|
| Chưa công nhận thành thạo | 0 | 120 |
| Công nhận thành thạo | 0 | 0 |

Bảng cần được đọc cùng cách chọn bài. Bộ chọn ưu tiên khái niệm mà mô hình đang đánh giá chưa thành thạo, rồi ưu tiên điểm thành thạo thấp trong các ứng viên. Vì vậy những trạng thái xuất hiện ở câu được giao đã chịu ảnh hưởng của chính mô hình và chính sách. Bộ chọn còn có nhánh ôn tập và nhánh khi mọi khái niệm đã thành thạo, nên kết quả điểm ước lượng dưới ngưỡng ở cả 120 lượt vẫn là một quan sát của lịch sử này.

Kiểm lần thực hành đầu tiên cho thấy cả 22 khái niệm được phục vụ đã đạt tiêu chí latent ngay từ lần đầu xuất hiện. Mô hình bắt đầu với điểm ước lượng 1200. Trong cơ chế hiện tại, trạng thái thật chỉ nhận mức tăng không âm và quên dần về mức nền, nên các khái niệm có mức nền đã đạt ngưỡng tiếp tục thuộc lớp đạt ngưỡng. Phép kiểm này vì thế chưa quan sát một lần chuyển từ chưa đạt sang đạt của thế giới mô phỏng. Trạng thái của sáu khái niệm còn lại cần bằng chứng riêng.

Phát hiện bổ sung cho RQ1 là cần kiểm soát quần thể khi đánh giá trạng thái kiến thức. Một bảng chỉ gồm các câu do chính hệ thống chọn chưa đủ để đánh giá chất lượng toàn bộ trạng thái. Vai trò riêng của điều kiện bất định cũng còn cần các trường hợp điểm kiến thức đã đạt. Bước kiểm tiếp theo được đề xuất là một tập khái niệm và thời điểm định trước, độc lập với quyết định chọn bài, có cả trạng thái mô hình lẫn trạng thái thật tương ứng. Thiết kế đó còn cần được chốt trong hợp đồng thực nghiệm chính.

Kết quả hiện tại là một lịch sử dùng lại, với 120 thời điểm có tương quan. Nó bổ sung chẩn đoán về cách đo và ảnh hưởng của năng lực ban đầu. So sánh giữa các đồ thị, hiệu chỉnh xác suất, thay đổi kết quả học và khả năng khái quát sang nhiều người học vẫn là những phần còn thiếu.

## Bằng chứng và phạm vi kiểm

[Bundle đã đóng](../runs/rq1-observer03-cached-truth-20261109-01/README.md) giữ nguồn, kết quả và failure. [Bảng kết quả](../runs/rq1-observer03-cached-truth-20261109-01/cached02_child__summary.json), [120 hàng đã ghép](../runs/rq1-observer03-cached-truth-20261109-01/cached02_child__joined120.json) và [kiểm độc lập, gồm first-visit](../runs/rq1-observer03-cached-truth-20261109-01/observer03_truth120_independent_crosscheck01.json) hỗ trợ các con số trên.

Reader đã kiểm đủ14.400 hàng cache và CRC trước khi lấy120 hàng. Hai phiên bản controller cùng đạt8fixture; cached01 dừng vì bộ đo giữ lại ctypes types, cached02 đạt sau sửa bộ đo với analyzer/tests/caps giữ nguyên. Đỉnh RAM worker của lượt đạt là51.486.720byte, owned Job đã về0. Kiểm độc lập đã đối chiếu lại từ gzip và readout gốc. First-visit là phân tích cơ chế hậu nghiệm.
