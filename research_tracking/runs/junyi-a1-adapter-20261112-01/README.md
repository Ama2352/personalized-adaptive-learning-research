# Adapter A1 Junyi — chờ nghiệm thu native CPU/CUDA

## Phần cài đặt

Gói ngày12/11/2026 thêm riêng hai file mới `research_junyi_graph_model.py` và `test_junyi_graph_model.py`. Nguồn A0 đang frozen cho pilot được giữ nguyên.

`JunyiGraphAKTAdapter` dùng một `ResearchGraphNative` để tạo đúng một backbone AKT và alpha A1. `AKTAdapter.step` hiện có thực hiện loss, backward, clipping và Adam. Optimizer phải sở hữu toàn bộ tham số, gồm alpha. Công thức graph augmentation giữ implementation `research_graph_model.py` đã nghiệm thu trước.

Phase được cấp bằng `JunyiGraphPhaseSession`. Khi chuyển train80/selection, adapter kiểm condition/encoding và audit đầy đủ. Mỗi batch dùng kiểm header nhẹ cùng prefix evidence đã có, tránh hash toàn bộ learner roles mỗi window.

`collate_training` tạo ticket cho batch, evidence và phase. `step` tiêu thụ đúng ticket trước native forward. Prediction gom cửa sổ theo batch đã chốt, bind context mới cho mỗi call, phục hồi mode từng module và RNG sau inference. Graph có điều khiển Boolean qua `set_graph_enabled`.

Admission production yêu cầu phase Junyi và typed CUDA profile thông qua validator hiện hành. Condition A1 cố định confidence1 được tái dùng. A2/A3 tiếp tục cần confidence TRAIN80 riêng.

## Kiểm đã thực hiện

`ast-check.json` xác nhận parse thành công hai file và16test cases dự kiến. Chưa import Torch hoặc chạy model trên máy local thiếu RAM. Không có kết quả PASS runtime trong gói này ở thời điểm tạo.

## Các ca chờ chạy ở Linux Gate

Test dùng native AKT/graph math thật trên CPU với ba exercise và sáu event. Chỉ phần admission CUDA được mock để giữ cấu hình fixture CPU rõ ràng. Các ca bao gồm một lần dựng backbone, graph-off/empty-graph khớp đúng backbone, backward và Adam cập nhật alpha, ownership optimizer, phase tách biệt, ticket, mode/RNG, current/future leakage, source và condition drift.

Tiếp theo cần Linux Gate đủ RAM, sau đó GPU có allocation riêng trước khi dùng adapter cho training Junyi nghiên cứu. Chưa có checkpoint A1 Junyi hoặc benchmark tốc độ từ gói này.

Bundle đang mở để nhánh chính nghiệm thu. Không cloud run, dependency installation hoặc commit trong phần việc của subagent.

## Nghiệm thu Linux ngày12/11

Full Gate source04 đạt2.218ca, bao gồm16ca native A1 của gói này. CPU03 trước đó chỉ gặp lỗi tạo scratch, đã giữ nguyên. CPU04 tạo parent đúng và chạy đạt. Bằng chứng ở [hồ sơ chẩn đoán](../junyi-numerical-diagnostic-20261112-01/README.md). Adapter đã kiểm CPU, còn CUDA A1, nối selected producer và các condition A2/A3 Junyi chưa hoàn tất.
