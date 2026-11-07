# Quy tắc làm việc trong repository

- Không chỉnh sửa hoặc di chuyển `dataset/`, `artifacts/bkt_baseline/`, `venv/` và `.wsl/JunyiBKT-Ubuntu/` khi chưa có yêu cầu rõ ràng.
- Không sửa dataset gốc hay các CV/refit/Test artifacts. Thí nghiệm BKT nặng chỉ chạy khi người dùng yêu cầu; không dùng holdout Test để chọn cấu hình.
- Giữ chuẩn BKT và protocol frozen: một mô hình mỗi `exercise`, outcome `correct`, thứ tự thời gian đã lưu, `num_fits=1`, `forgets=False`, `tol=0.005`, `maxiter=100`, seed 42; dự đoán tuần tự một bước trước khi dùng đáp án hiện tại để cập nhật state.
- `suggested` chỉ dùng phân nhóm kết quả. Skill không có model train không được tính metric như thể có dự đoán BKT fitted.
- Không tự viết lại pyBKT/EM. Giữ patch tại `third_party/pyBKT/` và đọc `docs/pybkt-provenance.md` trước khi sửa dependency vendored.
- Trước khi chuyển artifact, ghi inventory SHA-256 và so sánh lại. Không sửa nội dung manifest/model/prediction cũ; cập nhật vị trí bằng relocation manifest.
- Mọi tài liệu vận hành và ghi chú nghiên cứu mới viết bằng tiếng Việt, rõ nguồn dữ liệu và giới hạn.
- Chạy smoke/import/test phù hợp sau thay đổi; không tuyên bố đã kiểm tra điều gì nếu không có output xác nhận.

## Cấu trúc và lưu bằng chứng

- Bắt đầu ở `docs/REPOSITORY_MAP.md`; cập nhật bản đồ và tham chiếu khi đổi cấu trúc. Không tạo thêm thư mục top-level tương đương `reports_new`, `results_latest`, `final_v2` nếu chưa có vai trò riêng rõ ràng.
- Báo cáo/phân tích tổng hợp mới dùng `research_tracking/reports/`, cập nhật mục lục `research_tracking/reports/README.md`. Phân biệt kết quả nghiên cứu, pilot, kiểm kỹ thuật, draft protocol và hồ sơ vận hành; không coi chúng là cùng mức bằng chứng.
- Bằng chứng nhỏ theo run dùng `research_tracking/runs/<run-id>/` với README tiếng Việt, manifest nguồn/input/output SHA-256, logs và giới hạn. Giữ cả failure quan trọng. Không sửa hoặc di chuyển bundle đã đóng; trỏ bằng chỉ mục/relocation manifest nếu cần.
- Models/checkpoints/predictions và logs lớn giữ trong output theo run của `experiments/<model>/results/`; dữ liệu phái sinh, dependencies/runtime/cache giữ theo vị trí pipeline quy định trong `artifacts/`. Không đổi các đường dẫn này chỉ để làm cây thư mục đẹp hơn. Các vùng bảo vệ ở trên vẫn áp dụng.
- `docs/thesis_recovery/evidence/` giữ hồ sơ/logs lịch sử của audit. Ưu tiên bundle theo run cho bằng chứng mới; không nhân đôi mọi log vào nhiều chỗ nếu không có lý do truy vết rõ ràng. Đường dẫn log bắt buộc của pipeline vẫn giữ nguyên.
- `_context/` là ngữ cảnh/protocol BKT ban đầu; không thay ba RQ toàn KLTN bằng mục tiêu baseline ở đây. Kế hoạch/thông tin tổng thể nằm trong `docs/thesis_recovery/` và `research_tracking/`.
- Chỉ dùng `.venv` trong repository cho Python/pip local; không tự cài dependency vào Python global hoặc `venv/` cũ. File tạm đặt trong vùng làm việc/test đã quy định, không rải ra root; chỉ dọn sau inventory và xác nhận không cần cho evidence hoặc resume.
- Sau mỗi gói thay đổi hoàn thiện: kiểm tra phù hợp, lưu ghi chú/bằng chứng cần thiết và commit riêng theo yêu cầu người dùng. Không commit dataset, credentials hoặc artifacts lớn; không push tự động.
