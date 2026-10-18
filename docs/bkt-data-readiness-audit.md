# Kiểm toán mức sẵn sàng dữ liệu BKT — Junyi Academy

**Phạm vi:** chỉ kiểm toán, không sửa dữ liệu gốc, không huấn luyện trên ProblemLog và không tạo tập train/validation/test. Các truy vấn toàn bộ log chạy bằng DuckDB 1.5.6 trong thư mục tạm; bảng phân chia chỉ tồn tại trong phiên truy vấn. ID học sinh trong ví dụ đã được ẩn.

## 1. Tóm tắt điều hành

**Đánh giá: CONDITIONAL GO** cho baseline BKT chuẩn theo từng `exercise`. CSV có nhãn nhị phân, mã học sinh và thời gian microsecond; phần lớn bản ghi có thứ tự thời gian xác định. Có 1.439 nhóm bản ghi trùng hoàn toàn và thêm 402 nhóm trùng theo `(user_id, exercise, problem_number)` nhưng có nội dung khác. Không có khóa chính tương tác đáng tin cậy.

Các điều kiện cần chốt trước khi triển khai: cách giữ và truy vết bản ghi trùng; dùng `correct` (nhãn này luôn false khi có hint); coi `exercise` là skill; và dùng phép chia học sinh toàn cục. Chuỗi ngắn và độ phủ thấp ở một số exercise hạn chế độ tin cậy của tham số riêng cho các skill hiếm, nhưng không cần đặt ngưỡng lọc tùy ý.

## 2. Kết quả profiling đã tái sử dụng

- [Báo cáo ProblemLog](../dataset/junyi_problem_log_profiling.html) ghi nhận 25.925.992 tương tác, 247.606 học sinh, 722 exercise, trung vị lịch sử mỗi học sinh là 10 tương tác, độ đúng chung 82,79%; tương tác được gợi ý đúng gần 100%, mật độ tương tác giữa exercise rất lệch.
- [Báo cáo còn lại](../dataset/junyi_data-profilling.html) mô tả bảng exercise 837 dòng và 11 cột, không phải ProblemLog. Tên ProblemLog thực tế là `dataset/junyi_ProblemLog_original.csv`; bảng exercise là `dataset/junyi_Exercise_table.csv`.
- Mã dự án liên quan duy nhất là `dataset/view-dataset.py`, script đọc preview ProblemLog theo chunk 1.000 dòng và in schema; không có pipeline BKT hoặc logic tạo split hiện hữu. Hai CSV relationship annotation không được dùng để suy diễn skill mapping trong audit này.
- Các kết quả ở mục 5 tính chuỗi theo **học sinh–exercise**, khác với lịch sử tổng hợp theo học sinh ở báo cáo trước. Không lặp lại EDA tổng quát.

## 3. Danh tính tương tác và bản ghi trùng

**Phát hiện đã xác nhận.** ProblemLog có 17 cột: `user_id`, `exercise`, `problem_type`, `problem_number`, `topic_mode`, `suggested`, `review_mode`, `time_done`, `time_taken`, `time_taken_attempts`, `correct`, `count_attempts`, `hint_used`, `count_hints`, `hint_time_taken_list`, `earned_proficiency`, `points_earned`. Không có cột ID tương tác.

| Khóa ứng viên | Nhóm trùng | Dòng bị ảnh hưởng | Dòng dư sau bản đầu | Nhóm có nội dung khác |
|---|---:|---:|---:|---:|
| `(user_id, exercise, problem_number)` | 1.841 | 3.682 | 1.841 | 402 |
| `(user_id, exercise, time_done)` | 1.439 | 2.878 | 1.439 | 0 |
| `(user_id, exercise, problem_number, time_done)` | 1.439 | 2.878 | 1.439 | 0 |

So sánh toàn bộ 17 cột tìm thấy **1.439 nhóm trùng chính xác**, gồm 2.878 dòng và 1.439 dòng dư. Vì vậy các nhóm trùng theo hai khóa có timestamp chỉ là những dòng trùng chính xác trong tệp. Khóa không có timestamp còn có 402 nhóm chứa 804 dòng với nội dung khác nhau (402 dòng dư), nên `problem_number` không thể tự nó xác định tương tác duy nhất.

Ví dụ đã ẩn ID: `adding_and_subtracting_within_20`, `problem_number=1`, `time_done=1419997556717660`, hai dòng giống nhau; và `adding_subtracting_carry_3`, `problem_number=2`, `time_done=1409723315118630`, hai dòng cùng khóa `(user, exercise, problem_number)` nhưng nội dung khác. Đây là ví dụ cấu trúc, không phải kết luận dòng nào sai.

**Giới hạn / giả thuyết.** Không thể biết từ CSV liệu các dòng giống hệt là hai sự kiện hợp lệ không phân biệt được hay bản sao khi xuất dữ liệu; các nhóm có cùng `problem_number` nhưng khác nội dung có thể là lần ghi lặp/thử lại hoặc vấn đề dữ liệu. Chưa có bằng chứng để chọn cách giải thích. **Khuyến nghị:** không xóa/gộp dòng trong kiểm toán này. Một số thứ tự dòng nguồn có thể được thêm để truy vết từng dòng, nhưng chỉ là surrogate ID phục vụ lineage, không phải khóa chính hay bằng chứng về danh tính sự kiện.

## 4. Tính toàn vẹn của thứ tự thời gian

**Phát hiện đã xác nhận.** `time_done` đọc được dưới dạng số nguyên trên cả 25.925.992 dòng; không thiếu giá trị. Miền dữ liệu là 1.350.003.835.131.230 đến 1.421.000.065.654.030 microsecond Unix, tương ứng 2012-10-12 đến 2015-01-11 UTC. Tài liệu trường dữ liệu Junyi mô tả `time_done` là Unix timestamp theo microsecond và `problem_number` là số lần học sinh luyện exercise đó; tài liệu này dẫn hồ sơ DataShop #1198. [Tài liệu Junyi được EduData lưu trữ](https://edudata.readthedocs.io/en/latest/build/blitz/junyi/junyi.html). Trang hồ sơ DataShop chính thức bị chặn 403 trong môi trường kiểm toán, nên định nghĩa được đối chiếu với tài liệu lưu trữ và cấu trúc dữ liệu, không xác minh trực tiếp trên trang gốc.

- Có 1.439 nhóm timestamp trùng trong cùng học sinh (2.878 dòng); toàn bộ cũng trùng trong cùng `(user_id, exercise)` và là các nhóm trùng toàn dòng đã nêu ở mục 3. Không tìm thấy timestamp tie giữa các dòng khác nhau.
- So sánh `problem_number` theo thời gian trong 1.886.390 chuỗi có ít nhất hai dòng: 52 bước giảm nằm trong 50 chuỗi, bao phủ 1.329 dòng của các chuỗi đó; 8 bước giữ nguyên số và không có trường hợp hai dòng khác nhau cùng timestamp nhưng khác `problem_number`. Do đó biến này gần như tăng theo thời gian, nhưng có ngoại lệ và không nên thay timestamp làm thứ tự chính.
- `time_taken` có 1.048 giá trị âm và 239 giá trị lớn hơn một ngày; min/max lần lượt là −504.921.173 và 406.757.166 giây. Đây là giá trị đáng ngờ theo đơn vị giây trong tài liệu, nhưng cột này không cần cho BKT chuẩn.

**Khuyến nghị có điều kiện.** Dùng `time_done` tăng dần trong từng `(user_id, exercise)` để sắp thứ tự. Với 1.439 nhóm trùng chính xác, thời gian không phân định được thứ tự giữa các bản sao; giữ nguyên và đánh dấu tie để quyết định chính sách sau. Nếu cần thứ tự chạy tái lập, số dòng nguồn chỉ nên dùng làm tie-break phục vụ tái lập, không được diễn giải là thứ tự thời gian đã xác nhận. Không dùng `problem_number` để âm thầm phá tie hoặc sắp xếp chính.

## 5. Đặc điểm chuỗi học sinh–skill

**Kết quả xác nhận.** Với `exercise` là skill tạm thời, có **2.289.789 chuỗi học sinh–exercise**. Độ dài: min 1; Q25 2; trung vị 8; trung bình 11,32; Q75 12; P90 24; P95 34; P99 80; max 5.174. Quantiles dùng phép tính chính xác trên độ dài chuỗi.

| Độ dài chuỗi | Số chuỗi | % chuỗi | Số tương tác | % tương tác |
|---|---:|---:|---:|---:|
| 1 | 403.399 | 17,62% | 403.399 | 1,56% |
| 2 | 212.376 | 9,27% | 424.752 | 1,64% |
| 3–5 | 274.331 | 11,98% | 1.091.521 | 4,21% |
| 6–10 | 750.970 | 32,80% | 5.898.346 | 22,75% |
| >10 | 648.713 | 28,33% | 18.107.974 | 69,84% |

Độ phủ giữa 722 exercise cũng lệch mạnh: 9 exercise chỉ có 1 học sinh; 21 có dưới 10 học sinh; 54 dưới 50; 105 dưới 100; 380 dưới 1.000. Có 22 exercise có dưới 100 tương tác. Các chuỗi dài đóng góp phần lớn dữ liệu để ước lượng chuyển trạng thái, trong khi phần lớn chuỗi riêng lẻ còn ngắn; các exercise cực hiếm không đủ căn cứ để ước lượng tham số ổn định riêng. Không áp ngưỡng độ dài tùy ý trong kiểm toán này.

## 6. Đánh giá rò rỉ nhãn và đặc trưng

**Kết quả xác nhận.** Tài liệu trường dữ liệu mô tả `correct` là đúng ở lần thử đầu và false nếu có yêu cầu hint. Điều này khớp chính xác với log: trong 1.673.993 dòng `hint_used=true`, tất cả đều `correct=false`; không có dòng nào vừa hint vừa `correct=true`. [Định nghĩa trường Junyi](https://edudata.readthedocs.io/en/latest/build/blitz/junyi/junyi.html). Vì tài liệu DataShop gốc không truy cập được (403), định nghĩa này được xác nhận qua tài liệu lưu trữ và đối chiếu toàn bộ bảng chéo thực tế.

| Cột | Vai trò trong audit | Đánh giá cho BKT chuẩn |
|---|---|---|
| `user_id` | Định danh học sinh / nhóm chuỗi | Bắt buộc để tạo chuỗi và chia nhóm; không là predictor. |
| `exercise` | Ngữ cảnh skill | Dùng tạm làm `skill_name`; cần duyệt mapping. |
| `problem_type` | Ngữ cảnh mẫu/câu hỏi | Có thể biết khi câu hỏi được đưa ra; không cần cho BKT chuẩn. |
| `problem_number` | Số lần luyện theo exercise, theo tài liệu | Có thể mang thứ tự gần đúng; có 52 bước giảm. Không dùng thay timestamp/ID. |
| `topic_mode` | Chế độ điều hướng/chọn chủ đề | Ngữ cảnh khi bắt đầu; có thể phản ánh cách học. Không cần cho BKT chuẩn. |
| `suggested` | Gợi ý của hệ thống theo quan hệ tiên quyết | Biết lúc chọn bài nhưng phụ thuộc chính sách. Không đưa làm feature chuẩn; báo cáo riêng theo nhóm. |
| `review_mode` | Chế độ ôn sau khi đạt proficiency | Ngữ cảnh chính sách, phụ thuộc trạng thái proficiency trước đó; bỏ khỏi baseline chuẩn. |
| `time_done` | Thời điểm sự kiện | Dùng sắp thứ tự; không đưa làm predictor hiện tại. |
| `time_taken` | Thời gian hoàn tất hiện tại | Chỉ biết trong/sau tương tác; không dùng dự đoán chính tương tác đó. |
| `time_taken_attempts` | Thời gian từng lần thử | Quan sát trong/sau tương tác; có thể lộ kết quả/quá trình hiện tại. |
| `correct` | Kết quả nhị phân hiện tại | Nhãn cần dự đoán; tuyệt đối không làm feature cùng thời điểm. Hint làm nhãn false theo định nghĩa dữ liệu. |
| `count_attempts` | Số lần thử hiện tại | Quan sát sau quá trình trả lời; rò rỉ nếu dùng dự đoán kết quả cùng dòng. |
| `hint_used` | Hành vi hint hiện tại | Quan sát trong/sau sự kiện và quyết định `correct`; không dùng làm feature hiện tại. |
| `count_hints` | Số hint hiện tại | Quan sát sau sự kiện; loại khỏi feature hiện tại. |
| `hint_time_taken_list` | Thời gian dành cho hint hiện tại | Quan sát sau sự kiện; loại khỏi feature hiện tại. |
| `earned_proficiency` | Đạt ngưỡng proficiency | Kết quả hậu tương tác, phụ thuộc lịch sử/thuật toán; target-derived, không dùng làm feature. |
| `points_earned` | Điểm thưởng hiện tại | Kết quả sau tương tác/chính sách điểm; không dùng làm feature hiện tại. |

BKT chuẩn cần chuỗi `user_id`, skill, thứ tự và phản hồi đúng/sai. `problem_type`, lựa chọn topic/gợi ý, thời gian hay hint có thể nghiên cứu ở biến thể sau, nhưng cần xác định rõ chỉ dùng thông tin có trước thời điểm dự đoán. **Giả thuyết cần kiểm chứng, không phải kết luận nhân quả:** chênh lệch suggested/non-suggested có thể đến từ cơ chế đề xuất và cách phục vụ câu hỏi. Tỷ lệ đúng observed của nhóm `suggested` là 99,9993% (5.327.335 dòng), so với 78,3360% của nhóm không gợi ý (20.598.657 dòng). Trong báo cáo split, tỷ lệ gần như giữ nguyên ở Dev và Test.

## 7. Mô phỏng chia tập theo học sinh

**Kết quả mô phỏng.** Seed tag `42` tạo thứ tự giả ngẫu nhiên, tái lập theo hash học sinh; chia 80/20 chính xác theo số học sinh; Dev được chia thành năm fold cân bằng theo cùng thứ tự. Đây là mô phỏng chỉ đọc; không lưu split. Assertion xác nhận giao giữa tập học sinh Dev và Test bằng 0.

| Phân vùng | Học sinh | Tương tác | Đúng (tỷ lệ) | Sai | Exercise có mặt |
|---|---:|---:|---:|---:|---:|
| Development | 198.084 | 20.726.271 | 17.169.967 (82,84%) | 3.556.304 | 720 |
| Test | 49.522 | 5.199.721 | 4.293.499 (82,57%) | 906.222 | 707 |

Năm fold validation bên trong Development:

| Fold | HS validation / train | Tương tác validation / train | Đúng validation | Exercise; không có trong train | Exercise ≤10 HS / tương tác |
|---|---:|---:|---:|---:|---:|
| 0 | 39.617 / 158.467 | 4.276.462 / 16.449.809 | 3.532.858 (82,61%) | 2 / 12 dòng | 53 / 2.897 |
| 1 | 39.617 / 158.467 | 4.076.498 / 16.649.773 | 3.373.949 (82,77%) | 1 / 8 dòng | 52 / 3.260 |
| 2 | 39.617 / 158.467 | 4.107.709 / 16.618.562 | 3.408.051 (82,97%) | 2 / 25 dòng | 64 / 3.214 |
| 3 | 39.617 / 158.467 | 4.145.440 / 16.580.831 | 3.439.431 (82,97%) | 4 / 13 dòng | 59 / 3.048 |
| 4 | 39.616 / 158.468 | 4.120.162 / 16.606.109 | 3.415.678 (82,90%) | 0 / 0 dòng | 51 / 2.996 |

Trong Test có 47 exercise với tối đa 10 học sinh (2.101 tương tác), 177 exercise với tối đa 50 học sinh (36.849 tương tác); 2 exercise xuất hiện trong Test nhưng không có trong Dev, tổng 104 tương tác. Các số tương ứng theo fold được ghi ở bảng trên. Tỷ lệ đúng trong các nhóm Test gần như tương đương Dev: với tương tác được gợi ý là 99,9995% so với 99,9992%; không gợi ý là 78,0596% so với 78,4054%. Hint rate không gợi ý là 8,45% Test và 8,05% Dev.

Chia theo học sinh ngăn trùng học sinh giữa các tập, nhưng tự nó không ngăn rò rỉ theo thời gian hay từ bước tiền xử lý học trên toàn bộ dữ liệu. Cách đánh giá BKT tuần tự còn cần nêu rõ: các phản hồi trước đó trong chuỗi Test có được dùng cập nhật trạng thái để dự đoán bước kế tiếp hay mục tiêu là dự đoán lạnh không cập nhật.

## 8. Tương thích pyBKT và ngữ nghĩa dự đoán

**Đã xác nhận từ mã nguồn; giới hạn:** không có pyBKT trong môi trường dự án. Đã kiểm tra mã nguồn CAHLR/pyBKT tại commit [`cc1682e`](https://github.com/CAHLR/pyBKT/tree/cc1682e652e6d41d5aaa7a286a01c4b76cd0da167): metadata `setup.py` là 1.4.3, còn nhãn module Python ghi `1.4 (Python)`. Vì package không được cài trong môi trường dự án, đây là kiểm toán mã nguồn upstream, không phải xác nhận runtime của một bản cài đặt local.

- **Schema và mapping:** `Model` mặc định cần `user_id`, `skill_name`, `correct`; `order_id` tùy chọn. Junyi không khớp mặc định Assistments/Cognitive Tutor, nên cần mapping rõ: `user_id → user_id`, `skill_name → exercise`, `correct → correct`, `order_id → time_done`. pyBKT nhận đúng `{0,1}` (hoặc `-1` cho không trả lời); cột bool cần chuyển rõ sang số nguyên.
- **Tạo chuỗi và skill độc lập:** converter sắp xếp theo `order_id`, rồi sắp xếp ổn định theo học sinh; tạo `starts/lengths` theo học sinh bên trong từng skill. `Model.fit` chạy mô hình riêng trong vòng lặp từng skill. Với cấu hình chuẩn, mỗi `exercise` có một mô hình BKT độc lập; quan hệ giữa exercise không được học.
- **Ước lượng EM:** E-step dùng phản hồi quan sát để tính lọc tiến/lùi và soft counts cho chuyển trạng thái, phát xạ và prior; M-step cập nhật tham số. Vì thế chỉ được fit trên phản hồi Dev, không fit mô hình trên chuỗi Test.
- **`predict()` một bước:** mã `predict_onestep` tính trạng thái dự đoán ở bước đầu từ prior; ở bước tiếp theo dùng chuyển trạng thái từ posterior sau phản hồi trước đó. Nhãn tại dòng hiện tại không dùng tạo dự đoán cho chính dòng ấy, nhưng có thể cập nhật trạng thái cho dòng kế tiếp. Vì vậy đây là dự đoán tuần tự một bước khi phản hồi lịch sử của cùng học sinh được phép quan sát.
- **Skill lạ / chuỗi ngắn:** `Model.predict` khởi tạo xác suất 0,5 cho mọi dòng; skill không có mô hình fit giữ giá trị đó. `evaluate()` lọc theo skill đã fit nên không nhất thiết tính những dòng skill mới vào metric. Chuỗi dài 1 vẫn được nhận, nhưng không cung cấp chuyển tiếp để ước lượng learning rate. Các exercise quá hiếm do đó hợp lệ về cấu trúc nhưng tham số yếu. Mã cross-validation dùng `len(starts)//folds`; dưới năm học sinh cho 5-fold có fold validation rỗng.
- **Cross-validation theo nhóm:** cách chia số fold mặc định hoán vị các chuỗi học sinh trong từng skill, nên tách học sinh trong mô hình skill đó. Tuy nhiên `Model.crossvalidate` gọi riêng theo skill; nó không tự bảo đảm một phép chia học sinh toàn cục nhất quán giữa mọi skill. Cần truyền nhãn fold toàn cục nhất quán hoặc tự chia bên ngoài.

**Kiểm tra tổng hợp cô lập.** Fit EM trên hai chuỗi train tổng hợp độc lập, rồi đổi nhãn tại timestep 2 và các timestep sau trong chuỗi đánh giá. Xác suất dự đoán đến và gồm timestep 2 không đổi; dự đoán timestep 3 thay đổi. Điều này khớp mã nguồn một bước. Không fit ProblemLog. Để chạy kiểm tra với NumPy 2.5.4 hiện có, cần một wrapper tạm chuyển likelihood một phần tử về scalar: mã EM Python upstream gán mảng likelihood 1×1 vào scalar và phát sinh `ValueError` nếu không có wrapper. Vì vậy kết quả xác nhận đường dự đoán trên source có shim tương thích, không xác nhận cài đặt pyBKT hoàn chỉnh trong môi trường.

Tham chiếu mã nguồn: [`Model.py`](https://github.com/CAHLR/pyBKT/blob/cc1682e652e6d41d5aaa7a286a01c4b76cd0da167/source-py/pyBKT/models/Model.py#L25-L42), [`data_helper.py`](https://github.com/CAHLR/pyBKT/blob/cc1682e652e6d41d5aaa7a286a01c4b76cd0da167/source-py/pyBKT/util/data_helper.py#L97-L164), [`predict_onestep.py`](https://github.com/CAHLR/pyBKT/blob/cc1682e652e6d41d5aaa7a286a01c4b76cd0da167/source-py/pyBKT/fit/predict_onestep.py#L15-L73), [`crossvalidate.py`](https://github.com/CAHLR/pyBKT/blob/cc1682e652e6d41d5aaa7a286a01c4b76cd0da167/source-py/pyBKT/util/crossvalidate.py#L108-L137), [`EM_fit.py`](https://github.com/CAHLR/pyBKT/blob/cc1682e652e6d41d5aaa7a286a01c4b76cd0da167/source-py/pyBKT/fit/EM_fit.py#L51-L90).

## 9. Khuyến nghị tiền xử lý

1. Giữ nguyên mọi dòng gốc; thêm số dòng nguồn nếu cần lineage. Báo cáo số bản sao và chạy phân tích độ nhạy sau khi có quyết định xử lý duplicate.
2. Dùng `time_done` để sắp thứ tự từng chuỗi; đánh dấu tie gồm các dòng trùng chính xác. Không dùng `problem_number` làm khóa chính.
3. Dùng `exercise` làm mapping skill tạm thời, và `correct` làm nhãn 0/1 sau khi chốt cách diễn giải false khi có hint. Không dùng các cột cùng dòng sau tương tác làm predictor.
4. Chia học sinh toàn cục trước mọi bước học tham số/tiền xử lý; giữ cùng nhãn fold cho tất cả skill. Báo cáo độ phủ skill và metric nhóm suggested/non-suggested; xử lý skill chưa thấy theo quy tắc được duyệt.
5. Không lọc chuỗi theo ngưỡng tùy ý. Báo cáo số chuỗi/độ phủ khi diễn giải tham số, nhất là các skill hiếm; không dùng `time_taken` trong BKT chuẩn.

## 10. Câu hỏi còn cần phê duyệt

- Chấp nhận `correct` làm target với quy ước mọi dòng có hint là sai, hay cần target khác?
- Giữ nguyên duplicate trong baseline và đánh giá độ nhạy thế nào với 1.439 nhóm trùng toàn dòng? Không thể xác định từ file liệu đây là sự kiện lặp hợp lệ hay lỗi xuất.
- Phê duyệt `exercise` làm skill cho baseline đầu tiên, hay cần mapping sang knowledge component từ metadata/relationship annotations?
- Đưa tương tác `suggested` vào tập đánh giá chính hay chỉ báo cáo riêng, do nhóm này gần như luôn đúng theo chính sách?
- Mục tiêu đánh giá trên học sinh mới là dự đoán tuần tự có dùng phản hồi trước trong Test, hay dự đoán lạnh không cập nhật trạng thái từ Test?
- Chấp nhận quy tắc thứ tự theo `time_done` và cách ghi nhận tie bằng dòng nguồn để tái lập, dù không suy ra được thứ tự thời gian giữa các bản sao?

**Kết luận sẵn sàng: CONDITIONAL GO.** Dữ liệu đủ cấu trúc để thử baseline BKT chuẩn theo `exercise`, với thứ tự chủ yếu xác định và phép chia nhóm khả thi. Cần phê duyệt định nghĩa target, xử lý/ghi nhận duplicate, mapping skill và quy trình đánh giá trước khi triển khai; kết quả của skill có rất ít học sinh phải được diễn giải thận trọng.
