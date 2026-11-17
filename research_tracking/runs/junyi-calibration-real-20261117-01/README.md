# Calibration Junyi A0–A3 — thực thi17/11

Đọc STATE.json trước tiếp tục. Gói giữ request/receipt nhỏ và chỉ mục artifact trên Drive. Bốn model refit đã có, lượt này chỉ suy luận trên calibration10 rồi fit temperature V1 bằng CPU. Phân tích outer và Holdout có ranh giới riêng.

## Mốc hiện hành — chuyển CPU local

Cập nhật sau lượt local. A2 đã hoàn tất temperature V1 trên1.621.484target, hệ số1,0295325171. `LOCAL_A2_FIT_ACCEPTANCE100.json` xác nhận đọc lại nămartifact Drive Sang, đối chiếu SHA/owner/binding/cohort. Calibration nghiệm thu3/4, A3 còn join/audit/fit. `resource.json` trên Drive ghi sampledpeak406MiB và wall4.641giây; có gián đoạn host trong lượt nên thời gian này không dùng làm benchmark CPU. Nguồn adapter của lượt A2 giữ trong commit6370aacb. Hai báo cáo cho GVHD đã nối mốc A2, kiểm nội dung tại `REPORT_A2_STATIC_CHECK100.json`.

Người dùng duyệt cache tạm tối đa4GB tại `artifacts/akt/local-calibration/20261117`. Đầu vào đã kiểm SHA trong `LOCAL_CALIBRATION_INPUTS01.json`. Snapshot A2 gồm1.278.474target/12.439người học đã sao lưu Drive và khôi phục local, kiểm12.440file theo inventory trong ZIP. `LOCAL_A2_SNAPSHOT01.json` ghi cache sau staging546.461.091byte.

Colab đã dừng writer, xóa access token tạm và trả runtime. Nguồn tại `COLAB_LOCAL_MIGRATION_STOP01.json`, `A2_PARTIAL_RAW_DRIVE01.json`, `COLAB_RELEASE_AFTER_MIGRATION01.json`. Lượt A2 local attempt100 nối tiếp snapshot, log `local-a2-join100.txt`. Fitter SQLite được kiểm26ca tổng hợp, commit6370aacb. Calibration nghiệm thu hiện2/4, A2/A3 còn chờ fit và kiểm Drive. Các đoạn dưới giữ diễn tiến trước mốc này.

## Tiến độ ngày17/11

A0 đã xuất1.621.484 xác suất,28.653cửa sổ,0OOV trên cohort calibration15.847người học. `A0_GPU_RESULT01.json` xác nhận snapshot numeric đã commit Volume. `A0_GPU_METADATA_DRIVE01.json` xác nhận cấu hình/log/NVML đã chuyển Drive Sang và kiểmSHA. CPU đang nối xác suất với nhãn, xuất Parquet và fit temperature V1, dùng snapshot này để tránh chạy GPU lại.

`A0_GPU_USAGE_SUMMARY01.json` giữ số đo55mẫu: GPU trung bình6,24%, cực đại43%, VRAM cực đại1.835MiB. Worker57,91giây gồm core12,05giây, trong đó inference6,88giây. Phần ngoài core chưa quy nguyên nhân đầy đủ. Mục tiêu sử dụng GPU trên50% chưa đạt. Lượt A1–A3 bổ sung timing từng bước, giữ nguyên phép tính và dữ liệu. Ưu tiên hoàn tất đầu ra nghiên cứu trong giới hạn chi phí, tránh mở nhánh benchmark tốn thêm credit.

`continue_gpu_variants01.py` kiểm source/runtime thực rồi lần lượt A1/A2/A3, mỗi GPU tối đa300giây, giữ cận0,75USD mỗi lượt. Chỉ `variant` và đường output numeric khác A0. Mỗi lượt có finalizer CPU đưa log lên Drive; GPU không giữ thông tin xác thực Drive.

`TESTS_TIMING_INPUTS02.txt` ghi61kiểm thử đạt. Lượt đầu thiếu PYTHONPATH, lượt sau gặp đường dẫn tạm Windows quá dài. Chạy lại với `PYTHONPATH=src` và `--basetemp artifacts/akt/test-temp/calib-root-1117-01` đạt. Chưa có bằng chứng các lỗi môi trường kiểm thử này ảnh hưởng cloud Linux.

Calibration được fit trên cohort riêng. Mọi cải thiện metric ngay trên cohort fit có thiên lệch lạc quan, phải chờ đánh giá độc lập trước kết luận mô hình nào tốt hơn hoặc RQ3 đã hoàn tất.
