# Nối calibration A0–A3 ngày 17/11

## Đã hoàn thiện về phần mềm

Đã có đường API nạp snapshot refit đã ghim, xuất raw prediction, đối chiếu đúng event/lịch sử rồi fit temperature bằng implementation sẵn có. Phần fit temperature đọc raw artifact trên local CPU và có thể chạy sau khi worker GPU kết thúc. [Nguồn và hợp đồng](../runs/calibration-producer-20261117-01/README.md).

Các kiểm cuối đạt 29 ca trong 22,96 giây, gồm 25 ca producer/provenance và 4 ca native A0–A3 trên mô hình CPU tổng hợp rất nhỏ. Bốn ca native đi qua snapshot loader thật, Parquet export, fit temperature và consumer, dùng checkpoint khoảng 77–79 KB. Process có working-set peak khoảng 369.5 MB trong lượt toy. Đây là kiểm đường phần mềm, chưa phải benchmark hoặc kết quả học tập.

## Rủi ro leakage đã được kiểm

Key calibration dùng source-row thật và full history trước đáp án hiện tại. Các ca đổi nhãn current/future/past xác nhận đúng hướng phụ thuộc của history hash. OOV và target đầu lịch sử được giữ trong coverage. Window overlap và OOV barrier được đối chiếu với iterator prediction hiện có. Sai learner/target/label/checkpoint/population hoặc raw artifact hash sẽ làm producer dừng. Identity nguồn training giữ nguyên, nguồn inference ghi riêng.

## Phần cần tiếp tục

Các model Junyi thật vẫn cần adapter builder/current-source runtime admission, source calibration10 riêng, population manifest được nghiệm thu và bounded inference thật. Cần đo RAM cho fitter toàn cohort và throughput cho bước prediction, cùng đóng request/resource budget trước chạy. Lượt này giữ heuristic RAM ở trạng thái estimate và cung cấp đường CPU-only để tránh giữ GPU trong lúc fit T.

Vì vậy chưa có kết luận mới về chất lượng calibration hoặc ưu thế A0–A3 trên Junyi từ gói này. Calibration và outer evaluation đầy đủ vẫn là những mốc nghiên cứu tiếp theo.
