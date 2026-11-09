## 7. Kiểm tiếp trên cùng lịch sử và cùng câu hỏi

Phát hiện về reliability ở mục 6 còn một giới hạn quan trọng. Các cấu hình chọn bài khác nhau có thể phục vụ những câu hỏi và lịch sử khác nhau. Để kiểm hiện tượng gộp nhóm che sai lệch trong điều kiện giữ chung đầu vào, nghiên cứu trở lại chín chuỗi cố định ở các mục 3–5. Hai cấu hình nhận cùng lịch sử, câu hỏi và đáp án. Điểm được đọc là trung bình ba xác suất raw của ba câu tham chiếu cho khái niệm đang hỏi. [E5]

Nguồn sinh dòng dữ liệu lấy câu hỏi ngẫu nhiên đều từ bộ 84 câu, mỗi khái niệm có ba câu. Trong thiết kế này, trung bình ba xác suất có thể được đánh giá như dự báo cho đáp án của một câu lấy ngẫu nhiên trong khái niệm đó. Mỗi đáp án đã quan sát được dùng một lần cho mỗi cấu hình. Có 1.080 tình huống chung, tương ứng 2.160 dòng cấu hình. Ba xác suất trong một điểm trung bình không làm tăng số đáp án lên ba lần.

Điểm trung bình giúp đối chiếu các cấu hình trên một mốc câu hỏi chung. Việc đánh giá nó với đáp án trước hết kiểm mức phù hợp của xác suất trả lời. Độ đúng của quyết định thành thạo cần được kiểm riêng bằng trạng thái kiến thức thật. Cách phân biệt này giữ cùng mục đích của Log Loss, Brier Score và reliability trong các baseline.

| Nhóm | Số tình huống chung | ECE15 khi nhận đủ cạnh | ECE15 khi cạnh rỗng |
|---|---:|---:|---:|
| Gộp | 1.080 | 0,043185 | 0,042526 |
| PG | 360 | 0,263534 | 0,261267 |
| PY | 360 | 0,131945 | 0,137415 |
| PYH | 360 | 0,069198 | 0,075091 |

Phép chia 15 khoảng và công thức ECE giữ như mục 6. Tại PG, dự báo trung bình thấp hơn tỷ lệ đúng. Tại PY và PYH, dự báo cao hơn tỷ lệ đúng. Sai lệch gộp khoảng 4,3 điểm phần trăm có thể đi cùng sai lệch khoảng 26 điểm phần trăm tại PG. Hiện tượng gộp nhóm che sai lệch vì vậy còn xuất hiện ở phép đọc ba câu tham chiếu khi hai cấu hình nhận chung dòng dữ liệu.

Hai cấu hình trong bảng là đủ cạnh và cạnh rỗng bên trong cùng graph package. Nhận đủ cạnh cho ECE thấp hơn ở PY/PYH và cao hơn ở PG. Theo ba khối seed đã dùng lại, ECE của đủ cạnh thấp hơn cạnh rỗng ở khối 20000, cao hơn ở 20001 và 20002. Hướng chênh lệch cần được giữ đầy đủ khi diễn giải kết quả.

Ở vùng điểm trên ngưỡng raw tham chiếu, hai cấu hình lần lượt có 195 và 217 tình huống. Chúng có thể gồm những tình huống khác nhau vì chính điểm dự báo quyết định membership của từng vùng. So sánh trong vùng này cần ghi đúng tập điều kiện của mỗi cấu hình. Ngưỡng raw giữ nguyên 0,5637150147511514, chưa được fit lại từ dữ liệu này.

Đã đối chiếu đủ 32 bảng nhóm, 480 khoảng và 64 vùng ngưỡng bằng phép tính Decimal độc lập. Các bảng nhóm dùng lại cùng chín lịch sử và ba khối ngẫu nhiên. Việc bổ sung cách tổng hợp không tạo thêm mẫu độc lập. Bước tiếp theo là kiểm độ đúng của quyết định thành thạo và hiệu chỉnh trên dữ liệu tách riêng. [E5]

## 8. Xác định điều kiện mà controller bảo đảm không quay lại chương

Paper1 đã tách đồ thị xác định tính khả thi với chính sách quyết định bài nào được chọn. Để giải thích thêm kết quả zero re-entry, nghiên cứu xét trực tiếp các quy tắc ready, cập nhật Elo và giữ chương của PDF bản nộp. Đây là một phân tích cấu trúc có giả thiết rõ ràng. [E6]

Xét đồ thị hữu hạn không chu trình, mọi cạnh nằm trong chương, chỉ khái niệm được chọn được cập nhật, không có quên, reset hoặc thay đồ thị giữa lượt. Ready chỉ chứa khái niệm chưa đạt ngưỡng có mọi tiên quyết đã đạt. Controller giữ chương hiện tại nếu chương đó còn ready.

Khái niệm đã đạt ngưỡng bị loại khỏi ready nên điểm của nó được giữ nguyên. Tập đã đạt ngưỡng vì thế chỉ giữ nguyên hoặc tăng, kể cả khi đáp án sai làm giảm điểm của một khái niệm chưa đạt. Nếu một chương còn khái niệm chưa đạt, đồ thị cảm sinh của chúng có một source. Mọi parent của source đã đạt ngưỡng, nên chương còn khái niệm ready. Controller chỉ rời chương sau khi hoàn tất chương đó. Sau lúc rời, chương không mở lại. Suy ra mỗi chương có tối đa một khối liên tiếp và số lần quay lại bằng 0 dưới các giả thiết này.

Điều kiện trên áp dụng cho dạng B1 với các cạnh nội chương. Một lượt hết ngân sách trong chương đầu vẫn thỏa kết luận. Do đó, khi đọc chỉ tiêu zero re-entry cần đặt nó cạnh quy tắc controller và topology. Kết quả học cần được đối chiếu thêm với trạng thái kiến thức thật và kết quả cuối.

Để xác định ranh giới của lập luận, dựng hai khái niệm a1, a2 thuộc A và một khái niệm b thuộc B, chỉ có cạnh b→a2. Điểm đầu a1=1248, b=1249, a2=1200. Lần đầu chọn a1 vì điểm thấp hơn b. Đáp án đúng đưa a1 qua ngưỡng, còn a2 bị b chặn nên controller sang B. Đáp án đúng ở b mở a2, controller trở lại A. Chuỗi A→B→A được tạo dù mọi lựa chọn tuân thủ continuity và đồ thị giữa chương chỉ có B→A, không chu trình.

Bốn kiểm dựng tay đã đạt qua controller được cài theo PDF. Chúng gồm đồ thị nội chương có nhiều nhánh và đáp án sai, parent ngoại chương đã đạt trước entry, phản ví dụ một cạnh liên chương và đối chứng selector global lowest-Elo nhỏ. Chứng minh cung cấp kết luận với toàn bộ chuỗi đáp án dưới giả thiết đã nêu, còn các kiểm dựng tay xác nhận những trường hợp cụ thể của implementation. Tần suất trên đồ thị liên chương, các hồ sơ người học và ngân sách nghiên cứu vẫn cần được đo. [E6]

