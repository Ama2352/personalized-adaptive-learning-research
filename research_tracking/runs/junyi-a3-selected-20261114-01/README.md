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

## Gián đoạn kết nối và phục hồi lượt đầu

Lượt local mất DNS trong khoảng gián đoạn dài. Guard local ghi stop muộn và không xác nhận được qua mạng. Giữ nguyên `app-budget-guard.json` và `local-failure.json` của lượt đầu, cùng log lỗi. Kiểm lại server xác nhận App đã kết thúc lúc 17 giờ 48 ngày 14/11 và không còn container. Worker đã hoàn tất 6 epoch và lưu phần epoch 7 theo giới hạn thời gian trên server. `recovery-stop-acknowledged01.json` giữ bằng chứng dừng độc lập. Thu artifact bằng `recover_artifacts01.py`, không gọi GPU mới trong bước tải.

Thời gian monotonic local trong khoảng mất kết nối không được coi là thời gian GPU thực. Settlement giữ cận tài nguyên request đã nghiệm thu theo timeout server, một container, retries 0. Metering toàn workspace sau lượt đầu khoảng 20,82 USD, billed 0. Các số metering và cận dự phòng được lưu riêng.

Hồi quy local đầu bị ngắt trước collection, giữ log trống và không tính đạt. Lượt chạy lại có quyền đọc thực tế trên D đạt 41 ca trong 1,23 giây, ghi ở `local-regression02.log`. Gate Linux source numerical giữ 2.615 ca đã nghiệm thu từ hồ sơ A2, không cộng hai số kiểm này như các ca độc lập.

## Tiếp tục từ vị trí sampler đã lưu

Đã tải và nghiệm thu 115 artifact của lượt đầu, archive khoảng 1,01 GB, cùng toàn bộ checkpoint trên D. Checkpoint partial ở bước 271 của epoch 7 giữ optimizer, RNG và sampler. `a3-settlement01.json` ghi phạm vi resume chính xác. Lượt02 tiếp tục từ checkpoint đó với source, dữ liệu và cấu hình học giữ nguyên.

Đóng dự toán lượt đầu bằng cận tài nguyên request 2,5626624 USD, giữ riêng số metering thực tế chưa tách hóa đơn theo run. Khoản dự phòng cuối được tạm giảm từ 3 xuống 2,50 USD để cấp lượt02 tối đa 2,60 USD. Cận tổng dự án là 29,96842062486352 USD, gồm biên trễ 1 USD đã có trong cận lịch sử. `reserve-reallocation01.json` giữ quyết định phân bổ của agent. Trần người dùng 30 USD tiếp tục áp dụng. Phần dự phòng 3 USD được khôi phục khi đóng lượt nếu cận chi cho phép.

## Kết quả đã nghiệm thu

A3 đã hoàn tất 12 epoch, chọn epoch 9, học đủ TRAIN80 13.347.331 target mỗi epoch. Đã kiểm đủ 1.600.343 dự đoán selection, target/order/probability identity, 0 OOV, checkpoint/Adam/RNG và gói model bốn file trên D. Log Loss native selection 0.35357115. A0–A3 expert đã hoàn tất selected-fit, đánh giá độc lập và các bước cuối còn chờ.

Hai lượt A3 có tổng function 52.25 phút, mẫu NVML trung bình 28.82%, VRAM đỉnh 5789 MiB. H100 đã dừng trước tải/nén artifact. Mục tiêu GPU trung bình trên 50% còn thiếu. Lượt đầu mất kết nối local, server đã kết thúc đúng giới hạn và đã phục hồi checkpoint partial epoch7/bước271. Metered toàn workspace 22.61 USD, billed0. Cận lịch sử 27.0585 USD cộng dự phòng 2.50 USD nằm trong trần toàn KLTN30USD.

`a3-selection-metrics.json` tái chấm prediction bằng hàm metrics chung GAM-KT. `a3-comparison-audit.json` giữ giới hạn A0 và thông tin so sánh. `a3-gate-selection-audit.json` mô tả cơ chế gate từ checkpoint và cache trênCPU. Figure độc lập nằm trong `figures/`, có SVG/PNG/CSV/provenance và script dựng lại. Hai báo cáo tại `research_tracking/supervisor_reports/2026-11-10/01_tien_do/` đã cập nhật. HTML đã kiểm tĩnh, PNG được xem trực tiếp. API inference độc lập của gói export còn chờ kiểm.
