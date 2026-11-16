# Chuẩn bị calibration và đánh giá độc lập A0–A3 ngày 17/11

## Kết quả có thể nghiệm thu

Đã khép đường phần mềm đưa đúng learner outer fold4 vào prediction view sau refit90. Phase mới giữ khả năng từ chối learner nội bộ, encoding TRAIN80, metadata role bị đổi và optimizer batch. Ba graph adapter A1/A2/A3 đã refit dự đoán được trong phase mới trên toy CPU. Lượt kiểm cuối đạt 66 ca, có log và JUnit. [Hồ sơ kỹ thuật](../runs/calibration-eval-readiness-20261117-01/README.md).

Đã đối chiếu metadata thực của bốn export với role và epoch-plan. Refit90 có 142.621 người học, calibration có 15.847, outer fold4 có 39.616. Ba tập này rời nhau theo metadata. Hash roles khớp pin trong bốn stage-inputs, refit-input identity và encoding90 identity tái tính khớp bốn export. Lượt này đọc JSON và encoding nhỏ, chưa đọc assignments/events hoặc model weights. [Kết quả đối chiếu](../runs/calibration-eval-readiness-20261117-01/ROLE_LINEAGE.json).

## Ý nghĩa đối với RQ1 và RQ3

Các model đã refit có thêm ranh giới reader/adapter phù hợp để triển khai đánh giá độc lập. Điều này giảm nguy cơ dùng nhầm dữ liệu calibration hoặc tập đã train khi tạo bảng so sánh. Đây là tiến triển engineering cần thiết trước khi đo prediction, calibration và tác động lên quyết định. Chưa có số liệu mới để kết luận confidence/gate cải thiện dự báo hoặc kết quả học tập.

## Phần chưa hoàn tất

Producer đầy đủ vẫn cần nạp/check refit export, dựng nguồn calibration10 riêng, tạo prediction có target/prefix provenance, fit temperature với dự toán RAM, rồi nối outer prediction/export theo grant/config và current-source Gate/runtime. Consumer temperature đã có từ lượt16/11. Lượt này bổ sung view/fold routing và graph adapter support; chưa thực thi các phase dữ liệu thật đó. Export index của bốn model hiện vẫn ghi calibration và independent evaluation chưa hoàn tất.

Protocol21 giữ BKT5fold cũ làm historical reference vì dùng outer-train đầy đủ trong khi ma trận mới refit90, đồng thời yêu cầu matched GAM/Graph-GAM riêng. Bảng cuối cần ghi đúng training population và common-target coverage. [Protocol21 mục3](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md).
