# Đếm bài tập ngoài vocabulary trên outer fold4

Ngày 17/11/2026. Đã hoàn tất kiểm metadata Development, không tính metric hoặc suy luận model.

## Kết quả

Vocabulary refit90 có 717 exercise. Năm partition ngoài vocabulary có tổng dung lượng 7.381 byte. Truy vấn chỉ đọc `user_id`, `exercise` và metadata phân chia, chọn `partition=development` và `fold=4`.

Kết quả có **144 tương tác thuộc ba exercise ngoài vocabulary**.

| Exercise | Tương tác outer |
|---|---:|
| application_of_linear_equations_2 | 41 |
| count_number_to_50 | 40 |
| variables_word_problems_2 | 63 |

Đây là phép đếm theo vocabulary refit90 thực, độc lập với số OOV được ghi trong BKT lịch sử. Việc hai số cùng bằng144 chỉ được xác nhận sau truy vấn này. Chưa xác nhận tổng target của toàn outer hoặc hình học window.

## Vì sao có lượt kiểm mới

Lượt02 trong bundle `junyi-outer-readiness-20261117-01` dừng khi import thư viện do giới hạn Windows Job128MiB quá thấp, log có lỗi OpenBLAS cấp bộ nhớ. Lượt mới giới hạn số thread BLAS/OMP/MKL/NumExpr về1 trước import và tăng trần bộ nhớ tiến trình lên512MiB. Phạm vi dữ liệu vẫn chỉ năm file nhỏ, timeout60giây, không quét lại toàn corpus.

Worker hoàn thành0,58giây, wall tổng0,82giây, peakRSS115.204.096byte, khoảng109,9MiB. Job đã terminate sau khi hoàn tất, số tiến trình còn lại0. Giữ `OOV_COUNT_RESOURCES03.json` và log cho phép kiểm lại giới hạn thực tế. Sửa giới hạn vận hành không thay phương pháp nghiên cứu hoặc dữ liệu.

## Nguồn và giới hạn

`OOV_FILE_INVENTORY03.json` giữ SHA-256 và số dòng footer của năm file. `OOV_COUNTS03.json` giữ pin assignment và encoding, truy vấn và kết quả. Không yêu cầu cột correctness, không chọn Holdout để phân tích, không xuất ID người học hoặc target labels. Các vùng dữ liệu được giữ nguyên.

144 row phải được giữ trong coverage với xác suất null và lý do OOV. Không bỏ dòng, gán xác suất giả hoặc đổi fold để vượt kiểm cache. Nhánh window cache hiện tại chưa nhận OOV fold4, còn đường native hỗ trợ. Wrapper và nguồn inference phải được nghiệm thu riêng trước suy luận H100.
