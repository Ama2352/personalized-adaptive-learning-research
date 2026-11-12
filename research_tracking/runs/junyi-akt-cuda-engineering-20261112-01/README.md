# AKT Junyi — một epoch CUDA đã nghiệm thu

## Kết quả đạt ngày12/11/2026

Lượt `modal-junyi-a0-epoch-20261112-02` chạy NVIDIA A10, giữ AKT NonRasch không đồ thị với recipe đã chốt. Cohort kỹ thuật gồm256learner train và32selection, mỗi learner tối đa300event, chọn bằng IDhash độc lập correctness. Đã hoàn tất11.833target/315window/79Adam updates trong một epoch. Bộ kiểm nguồn Linux trước lượt này đạt2.037tests,0failure/error/skip.

Đã xuất đủ1.530target selection, trong đó1.405có dự đoán fitted và125OOV giữ null. Đối chiếu local xác nhận target/source/learner/time/outcome/fold khớp cohort, checkpoint binding đúng, metric tính lại khớp chính xác. Nạp checkpoint vào model mới cho cùng toàn bộ dự đoán. Model/Adam/RNG/counters nằm trong checkpoint27.665.783bytes. Ba file của checkpoint đã được đọc/hash độc lập từ Modal Volume sau khi App GPU dừng.

## Tìm bằng chứng

- `verification.json`, `verification.log`, `verify_artifacts.py` giữ kiểm archive và target/metric độc lập.
- `checkpoint-index.json` trỏ archive local, Volume và checkpoint; `verify_durable.py`/log giữ phép đọc lại.
- `epoch01.json`, `training-events.jsonl`, `engineering-terminal.json` giữ tiến trình và telemetry. Archive đầy đủ và checkpoint lớn nằm tại `experiments/akt/results/modal-junyi-a0-epoch-20261112-02/artifacts.zip`.
- `cpu02__*.json/xml`, `cpu-execution02.log` và archive native của `modal-junyi-cpu-gate-20261112-02` giữ Gate nguồn.
- `figure-junyi/` giữ SVG/PDF/PNG và CSV. `build_figure.py` dựng lại. Đã xem PNG, nhãn/giá trị không đè nhau. Style chuyển thể figures4papers đã ghim, không dùng ImageGen.
- `allocation.json`, `gpu-request.json`, reservations và billing snapshots ghi gói0,50USD đã duyệt. Billing sau lượt ghi tổng kỳ0,57056749USD, net billed0USD; snapshot có độ trễ và không dùng như hard budget.

## Lỗi giữ lại và cách sửa

1. CPU01 dừng trước test do thiếu thư mục runtime trong image. CPU02 tạo đúng thư mục trước copy lock. Không đổi model/test để đạt Gate.
2. GPU01 dừng lúc import controller do đường dẫn module ở Modal nông hơn repository. GPU02 dùng cách xác định parent an toàn, chuyển import phụ thuộc local vào entrypoint, kiểm standalone import trước dispatch. Nguồn phiên bản lỗi, log và dispatch giữ nguyên. Worker training chỉ chạy thành công ở lượt02.
3. Review độc lập yêu cầu seed Python/NumPy/CPU/CUDA. Worker đã ghim42 trước fit. Controller xử lý marker JSON còn đang đóng và quét checkpoint lần cuối khi worker kết thúc.

## Diễn giải và giới hạn

Đây là nghiệm thu engineering một epoch. `selected_epoch=null`. Chưa có lựa epoch chính, refit90, calibration10, outer-fold evaluation, Junyi graph variants hoặc so sánh với BKT/GAM. Metric supported chỉ mô tả1.405target của cohort này. Toàn population chưa có score vì125OOV. Checkpoint chứng minh khôi phục model/optimizer/RNG ở cuối epoch; chưa chứng minh sampler/workflow resume giữa epoch.

Đếm dữ liệu chính chỉ chiếu user_id và join train/selection Development. Có126.774train learners/13.347.331events và15.847selection learners/1.600.343events. Script và kết quả trong `count_development_targets.py`, `development-population-counts.json`. Không đọc correctness/calibration/Holdout trong phép đếm.

## Bước tiếp

Chuẩn bị producer Junyi selected/refit/calibration theo đúng80/10/10, graph835nodes/976edges và confidence TRAIN riêng. Đo thêm throughput đại diện chuỗi dài, cache/validation/I/O trước cấp ngân sách full. Không suy toàn bộJunyi từ cohort bị giới hạn300events. Không chuyển checkpoint Grade10 sang vocabulary Junyi.
