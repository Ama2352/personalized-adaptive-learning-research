# Sao lưu dự đoán A2/A3 sang Drive — 17/11/2026

## Đã nghiệm thu

Hai archive chứa numeric inference đã được stream từ Volume sang Drive của `honguyenminhsang2005@gmail.com`. Tổng 71.546.486 byte, mỗi archive 449 member. Drive xác nhận lại kích thước, SHA-256, thư mục cha và chủ sở hữu. Hồ sơ đọc lại độc lập ở `NUMERIC_BACKUP_READBACK01.json`.

- [A2](https://drive.google.com/file/d/1Y2egpzAZDM8A11vrpZnMIZNqqt_bZZXU/view), 35.773.201 byte.
- [A3](https://drive.google.com/file/d/1DqKeh8dHSYSOgSJWlvpI-4vmzF8ssLf8/view), 35.773.285 byte.
- [Thư mục chứa hai archive](https://drive.google.com/drive/folders/1tUKMQF8TDnFj8LY_KJjH6wC9DH5-bB-Z).

Nguồn và byte từng member được pin trong `A2_NUMERIC_BACKUP_PLAN01.json` và `A3_NUMERIC_BACKUP_PLAN01.json`. Uploader kiểm SHA từng member trước khi chấp nhận. File nguồn trên Volume giữ nguyên.

## Tiến trình và tài nguyên

Lượt serial đầu giữ tiến độ upload A2 đến byte 16.777.216. Sau khi kiểm archive prefetch1 và prefetch4 giống nguyên byte, uploader được khởi động lại với tối đa bốn reader. Transport đối chiếu offset Drive và tái tạo prefix trước khi tiếp tục. `upload-numeric-backups02.log` xác nhận cả hai archive đã kết thúc thành công.

36 ca kiểm archive, resumable transport và tích hợp đạt trong 0,89 giây, log `TESTS_VOLUME_DRIVE_STREAM02.txt`. Các tests mô phỏng kiểm ngắt mạng, tiếp tục upload, SHA và đóng reader. Số đo upload thật trong `NUMERIC_STREAM_RESOURCE01.jsonl` ghi peakRSS 127.397.888 byte, khoảng 121,5 MiB. Đây là peak bộ nhớ của tiến trình uploader theo chu kỳ lấy mẫu hai giây.

CPU chạy local trong `.venv`. Lượt này dùng API lưu trữ, không tạo container Modal. Archive được truyền trong bộ nhớ, không tạo bản ZIP hoặc model nhị phân trên ổ D. Chi phí egress phụ thuộc tài khoản và hạn mức dịch vụ.

## Giới hạn nghiên cứu và bước tiếp theo

Đây là nghiệm thu lưu trữ đầu ra suy luận. Calibration A2/A3 còn bước nối đúng target/nhãn, audit tập calibration và fit temperature theo V1 trên CPU miễn phí. Calibration đã nghiệm thu vẫn là A0/A1, tương ứng 2/4 model. Đánh giá outer độc lập còn chờ. Không dùng kết quả trên tập calibration để kết luận model nào tốt hơn.

## Tái lập

`prepare_numeric_backups01.py` dựng kế hoạch từ Volume và receipt GPU. `upload_numeric_backups01.py` stream sang Drive, trạng thái tiếp tục và credentials nằm trong vùng private. `verify_numeric_backups01.py` chỉ đọc lại metadata và tạo biên nhận độc lập mới. Không đưa các file private vào Git hoặc notebook.
