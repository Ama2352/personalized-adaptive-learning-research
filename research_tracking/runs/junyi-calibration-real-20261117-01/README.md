# Calibration Junyi A0–A3 — thực thi17/11

Đọc STATE.json trước tiếp tục. Gói giữ request/receipt nhỏ và chỉ mục artifact trên Drive. Bốn model refit đã có, lượt này chỉ suy luận trên calibration10 rồi fit temperature V1 bằng CPU. Phân tích outer và Holdout có ranh giới riêng.

## Tiến độ ngày17/11

A0 đã xuất1.621.484 xác suất,28.653cửa sổ,0OOV trên cohort calibration15.847người học. `A0_GPU_RESULT01.json` xác nhận snapshot numeric đã commit Volume. `A0_GPU_METADATA_DRIVE01.json` xác nhận cấu hình/log/NVML đã chuyển Drive Sang và kiểmSHA. CPU đang nối xác suất với nhãn, xuất Parquet và fit temperature V1, dùng snapshot này để tránh chạy GPU lại.

`A0_GPU_USAGE_SUMMARY01.json` giữ số đo55mẫu: GPU trung bình6,24%, cực đại43%, VRAM cực đại1.835MiB. Worker57,91giây gồm core12,05giây, trong đó inference6,88giây. Phần ngoài core chưa quy nguyên nhân đầy đủ. Mục tiêu sử dụng GPU trên50% chưa đạt. Lượt A1–A3 bổ sung timing từng bước, giữ nguyên phép tính và dữ liệu. Ưu tiên hoàn tất đầu ra nghiên cứu trong giới hạn chi phí, tránh mở nhánh benchmark tốn thêm credit.

`continue_gpu_variants01.py` kiểm source/runtime thực rồi lần lượt A1/A2/A3, mỗi GPU tối đa300giây, giữ cận0,75USD mỗi lượt. Chỉ `variant` và đường output numeric khác A0. Mỗi lượt có finalizer CPU đưa log lên Drive; GPU không giữ thông tin xác thực Drive.

`TESTS_TIMING_INPUTS02.txt` ghi61kiểm thử đạt. Lượt đầu thiếu PYTHONPATH, lượt sau gặp đường dẫn tạm Windows quá dài. Chạy lại với `PYTHONPATH=src` và `--basetemp artifacts/akt/test-temp/calib-root-1117-01` đạt. Chưa có bằng chứng các lỗi môi trường kiểm thử này ảnh hưởng cloud Linux.

Calibration được fit trên cohort riêng. Mọi cải thiện metric ngay trên cohort fit có thiên lệch lạc quan, phải chờ đánh giá độc lập trước kết luận mô hình nào tốt hơn hoặc RQ3 đã hoàn tất.
