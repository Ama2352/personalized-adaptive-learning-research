# Cache Junyi cho training chính — dữ liệu đã chuẩn bị

## Đã hoàn thành

Ngày12/11/2026 đã tạo cache train80/selection10 đầy đủ tại `artifacts/akt/junyi-cohorts/outer4-selected-full-20261112-03/`. Cache giữ126.774train learners/13.347.331events và15.847selection learners/1.600.343events. Có140.259.430bytes parquet events và378.819bytes assignments riêng. Cache không có event calibration, outer-validation hoặc Holdout. Không huấn luyện mô hình.

Source parquet, assignments và manifest gốc được hash trước/sau, giữ nguyên trong vùng BKT. COPY chỉ projection/join learner đã ghim. Native reader tiếp tục sắp timeline bằng user/time/source-row. Không cắt300event hoặc lấy mẫu learner ở cache này.

`verification.json/log` và `verify_cache.py` xác nhận hash toàn output, count learner/target và so native reader gốc/cache trên288learner,18.678events, khớp toàn event/thứ tự. Metadata support train có717exercise, toàn bộ1.600.343target selection nằm trong vocabulary này. `train-exercise-support.csv` lưu support chỉ TRAIN. Đây là audit vocabulary, chưa checkpoint/metric model hoặc refit90 encoding.

## Các lượt lỗi được giữ

- Lượt01 dừng do thứ tự bind positional parameters của DuckDB COPY khác dự kiến. Đổi sang named parameters rõ source/destination. Snapshot nguồn và log giữ tại bundle.
- Lượt02 ghi xong canonical parquet rồi dừng vì alias SQL `partition` cần quote. Đã thêm kiểm regression thực thi cả COPY events và assignments trên fixture nhỏ. `tests02.log/xml` xác nhận ca đạt.
- Lượt03 hoàn tất. Cache lỗi01/02 và manifests giữ nguyên, không dùng làm input training.

## Phạm vi và bước tiếp

Đây là tiền xử lý có kiểm chứng, không phải training Junyi đầy đủ. Chưa upload cache đầy đủ lên Modal. Lượt user đã duyệt0,50USD chỉ chuyển cohort kỹ thuật trước. Cloud producer phải kiểm manifest/hash và tạo DataPaths đúng vị trí Linux khi đóng gói. `data_paths` trong cache là ghi nhận vị trí Windows lúc tạo, không dùng thẳng làm cấu hình Linux.

Tiếp theo là producer selected/refit/calibration, benchmark đại diện và cấp allocation riêng. Không suy metric mô hình từ coverage100%. Không dùng kết quả selection để tinh chỉnh graph theo outcome thuận lợi.
