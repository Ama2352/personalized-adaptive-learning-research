# Output thống kê tổng hợp ở vị trí lịch sử

Thư mục này hiện giữ [paired_cluster_bootstrap_bkt_gam.json](paired_cluster_bootstrap_bkt_gam.json), một kết quả paired learner bootstrap từ Development CV BKT/GAM-KT đã lưu. Đây không phải thư mục báo cáo chung của toàn KLTN.

- Công cụ tạo: [scripts/bootstrap_bkt_gam_cv.py](../scripts/bootstrap_bkt_gam_cv.py), qua tham số `--output`. Không cần chạy lại để đọc kết quả.
- Bản diễn giải: [docs/bkt-gam-kt-benchmark.md](../docs/bkt-gam-kt-benchmark.md) và [báo cáo nghiên cứu chi tiết](../docs/research/bkt-gam-kt-baseline-benchmark-report.md).
- Phân tích nghiên cứu mới: [research_tracking/reports](../research_tracking/reports/).
- Bằng chứng theo run: [research_tracking/runs](../research_tracking/runs/).
- Bản đồ đầy đủ: [docs/REPOSITORY_MAP.md](../docs/REPOSITORY_MAP.md).

Giữ JSON cũ tại chỗ để bảo toàn đường dẫn trích dẫn. Đầu ra tổng hợp mới của các đợt nghiên cứu dùng research_tracking theo quy ước trong bản đồ; không tạo thêm thư mục top-level tương đương. Không suy kết quả graph/closed-loop từ bootstrap hai baseline graph-free này.
