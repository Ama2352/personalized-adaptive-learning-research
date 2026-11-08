# RQ1 — hai con số22 không phải cùng những lần thay đổi

**Phát hiện bổ sung:** trên1.080 cặp snapshot full–empty đã có, tiêu chí xác suất tham chiếu của khái niệm đang được hỏi thay đổi22lần; khái niệm được controller đề xuất cũng thay đổi22lần. Hai nhóm này chỉ trùng **2snapshot**. Vì vậy không thể nối hai con số22 thành câu chuyện “dự đoán vượt ngưỡng22lần nên hệ thống đổi bài22lần”.

## Câu hỏi này tiếp nối nghiên cứu trước như thế nào?

Paper2 so sánh dự đoán khi giữ chung lịch sử và so sánh trình tự học trong simulator. RQ1 của KLTN hỏi vì sao thông tin prerequisite chưa chuyển thành lợi ích ổn định. Để trả lời, cần phân biệt dự đoán của câu đang được hỏi, phân loại mastery và bài mà controller sẽ chọn. Ba phép đọc này có thể phản ánh những khái niệm khác nhau tại cùng thời điểm.

[Chẩn đoán mastery](rq1_native_mastery_reference_diagnostic_20261109.md) đã xác định nativeM dùng cả điểm kiến thức ước lượng và điều kiện bất định; không trực tiếp lấy xác suất trả lời câu hiện tại so với một ngưỡng. [Tái dựng controller](rq1_fixed_controller_candidates_20261109.md) đã giải thích các bước lọc ứng viên và xếp hạng để chọn CID. Phân tích bổ sung này ghép hai bộ kết quả theo đúng seed, hồ sơ và thời điểm, kiểm tra cùng khái niệm query và cùng M-set, rồi đếm sự đồng xuất hiện. Không chạy lại mô hình hoặc simulator.

## Đã làm và đã tìm thấy gì?

Hai nguồn đều có đủ9chuỗi ×120snapshot; phép ghép một-một giữ đủ1.080cặp. Định nghĩa dưới đây là **khác biệt full–empty tại cùng snapshot**, không phải số lần một người học vượt ngưỡng theo thời gian:

- **Query-M:** native mastery của khái niệm trong câu hỏi đã ghi.
- **Tiêu chí xác suất tham chiếu:** trung bình xác suất raw trên ba câu tham chiếu của khái niệm đó, so với ngưỡngV1 đã định nghĩa. Chưa có temperature calibrator; không gọi đây là mastery thật hoặc xác suất đã hiệu chuẩn.
- **CID:** khái niệm controller sẽ đề xuất trên bản preview. Preview chưa được phục vụ để tạo learning outcome.

|Query-M khác?|Tiêu chí xác suất khác?|CID khác?|Cặp snapshot|
|---|---|---|---:|
|Không|Không|Không|1033|
|Không|Không|Có|20|
|Không|Có|Không|20|
|Không|Có|Có|2|
|Có|Không|Không|5|
|Có|Không|Có|0|
|Có|Có|Không|0|
|Có|Có|Có|0|
|**Tổng**|||**1080**|

Như vậy20trong22lần thay đổi tiêu chí xác suất không đi kèm thay đổi CID; chiều ngược lại cũng có20trường hợp. Cả5bất đồng Query-M đều không trùng bất đồng CID trong mẫu này. Điều đó không mâu thuẫn với90snapshot có bất đồng M-set trên toàn28khái niệm: Query-M chỉ xem **một** khái niệm của câu đã ghi, còn controller có thể chọn một khái niệm khác. Không dùng kết quả Query-M để kết luận toàn bộ mastery không ảnh hưởng lựa chọn.

|Hồ sơ|Cặp snapshot|Query-M khác|Tiêu chí xác suất khác|CID khác|Cả tiêu chí xác suất vàCID khác|
|---|---:|---:|---:|---:|---:|
|PG|360|4|8|20|2|
|PY|360|0|7|2|0|
|PYH|360|1|7|0|0|

Kết quả đầy đủ giữ16nhóm gồm pooled, từng hồ sơ, từng seed và từng quỹ đạo; mỗi nhóm đều giữ8ô, kể cả0. Không chọn riêng nhóm có graph thuận lợi. Witness đầu tiên theo thứ tự seed/profile/event được lưu để đối chiếu, không chọn theo learning gain.

## Tiến độ và giới hạn của kết luận

**Đã xác nhận:** hai readout cùng có22bất đồng nhưng phần lớn thuộc những snapshot khác nhau. Phép ghép khớp M-set và concept query ở toàn bộ population. Tám fixtures phần mềm đạt, kể cả ca known-answer đủ8ô và các ca từ chối khóa trùng, thiếu dòng, lệch query, mâu thuẫn mastery/CID và boolean sai kiểu. Phân tích cached hoàn tất trong giới hạn10giây, không model call, không thêm learner/seed/lịch sử tương tác.

**Chưa xác nhận:** xác suất nào đúng hơn, mastery nào đúng hơn, graph có cải thiện học tập hay không, hoặc tác động trung gian nhân quả của xác suất/mastery lên lựa chọn. Không có nhãn truth mới, calibration fit, learning outcome mới, p-value hoặc confidence interval. Cùng9chuỗi cũ được tái sử dụng, không phải1.080người học độc lập.

Đóng góp hiện tại choRQ1 là loại một cách diễn giải sai và nối các bằng chứng dự đoán–phân loại–lựa chọn bằng phép đối chiếu từng snapshot. Bước nghiên cứu còn lại vẫn là so sánh có kiểm soát và kết quả closed-loop hợp lệ; không coi bảng này là hoàn tấtRQ1.

## Nguồn và bằng chứng có thể kiểm tra

- [Kết quả ghép và toàn bộ16nhóm](../runs/rq1-query-decision-overlap-20261109-01/summary.json).
- [Kiểm tra chéo độc lập](../runs/rq1-query-decision-overlap-20261109-01/independent_crosscheck.json), không gọi hàm analyzer.
- [Log tám fixtures](../runs/rq1-query-decision-overlap-20261109-01/child__unittest.log) và [validation](../runs/rq1-query-decision-overlap-20261109-01/child__validation.json).
- [Giới hạn và nguồn của run](../runs/rq1-query-decision-overlap-20261109-01/README.md). Hai bundle nguồn cũ được tham chiếu nguyên trạng, không di chuyển hoặc sửa kết quả lịch sử.
