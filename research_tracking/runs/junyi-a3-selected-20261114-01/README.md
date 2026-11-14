# A3 Junyi — confidence TRAIN80 và cổng đồ thị

## Mục tiêu và phạm vi

A3 bổ sung cổng điều khiển ảnh hưởng đồ thị trên AKT có trọng số confidence A2. Đợt này hoàn thiện bước chọn checkpoint trên Development outer fold4, phục vụ đối chứng RQ3. Kết quả selection dùng chọn epoch. Refit, calibration, đánh giá độc lập và mô phỏng vòng kín là các bước tiếp theo.

Hồ sơ A2 trước đó đã niêm phong tại `../junyi-confidence-completion-20261114-01/`. Confidence TRAIN80 và các cache A3 đã có được tái dùng theo SHA, không fit lại. Source numerical03 và Gate Linux2.615ca giữ cùng đầu vào với A2. `STATE.json` là điểm tiếp tục.

## Các bước đã làm

1. Đọc lại hồ sơ A2, giữ bundle cũ bất biến.
2. Đọc billing mới và xác nhận không còn container. Đối soát khoản dự phòng lịch sử A1 bằng mốc billing sau A1 và giữ toàn bộ cận các lượt sau mốc đó, cộng1USD cho điều chỉnh trễ. Dự phòng cuối3USD và trần30USD tiếp tục áp dụng. `budget-reconciliation.json` giữ cách tính và ledger cũ SHA.
3. Tạo snapshot A3 mới trên D bằng source03, Gate03, dữ liệu và confidence đã niêm phong. Kiểm27trường cấu hình học, input/encoding/split, seed, profile số học và upstream thực. `a3-a2-preparation-comparison.json`, `snapshot-dependency-verification.json`, `snapshot-preflight01.log` giữ kết quả.
4. Token được người dùng cấp lại đủ thời hạn. Một lượt H100 được phân bổ tối đa2,60USD, child1740giây/function1800giây/watchdog1860giây. CPU provider kiểm SHA/runtime trước gọi GPU. Lưu checkpoint định kỳ, dừng App trước tải/nén artifact.

## Dữ liệu và giới hạn

- TRAIN80 có126.774người học,13.347.331target mỗi epoch. Selection có15.847người học,1.600.343target. Vocabulary717bài tập.
- Seed42, batch train/selection128, FP32, Adam và early stopping giữ cùng cấu hình A2. A0 lịch sử chọn epoch bằng batch1, chỉ checkpoint9 đã replay batch128. Ranking đầy đủ của A0 theo batch128 vẫn còn thiếu.
- Confidence biểu diễn độ ổn định dự báo có điều kiện, fit riêng TRAIN80. Confidence không được diễn giải là xác suất cạnh đúng.
- GPU sử dụng trung bình trên50% chưa được xác nhận. Tách chuẩn bị và tải artifact khỏi GPU đã có cơ chế và bằng chứng A2, nhưng tính toán CPU giữa batch vẫn tồn tại. Đợt A3 tiếp tục lưu NVML và thời gian thực.
- Không sử dụng calibration, outer validation hoặc Holdout cho lượt chọn checkpoint này.

## Vị trí kết quả

Hồ sơ và log nhỏ nằm trong bundle này. Checkpoint, predictions, telemetry và archive tải về nằm trong `experiments/akt/results/modal-junyi-a3-staged-h100-20261114-*/`. Snapshot và cache nằm trong `artifacts/akt/`. Mọi artifact tải về đều phải nghiệm thu inventory/SHA trước coi hoàn tất.
