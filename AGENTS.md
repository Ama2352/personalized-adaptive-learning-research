# Quy tắc làm việc trong repository

- Không chỉnh sửa hoặc di chuyển `dataset/`, `artifacts/bkt_baseline/`, `venv/` và `.wsl/JunyiBKT-Ubuntu/` khi chưa có yêu cầu rõ ràng.
- Không sửa dataset gốc hay các CV/refit/Test artifacts. Thí nghiệm BKT nặng chỉ chạy khi người dùng yêu cầu; không dùng holdout Test để chọn cấu hình.
- Giữ chuẩn BKT và protocol frozen: một mô hình mỗi `exercise`, outcome `correct`, thứ tự thời gian đã lưu, `num_fits=1`, `forgets=False`, `tol=0.005`, `maxiter=100`, seed 42; dự đoán tuần tự một bước trước khi dùng đáp án hiện tại để cập nhật state.
- `suggested` chỉ dùng phân nhóm kết quả. Skill không có model train không được tính metric như thể có dự đoán BKT fitted.
- Không tự viết lại pyBKT/EM. Giữ patch tại `third_party/pyBKT/` và đọc `docs/pybkt-provenance.md` trước khi sửa dependency vendored.
- Trước khi chuyển artifact, ghi inventory SHA-256 và so sánh lại. Không sửa nội dung manifest/model/prediction cũ; cập nhật vị trí bằng relocation manifest.
- Mọi tài liệu vận hành và ghi chú nghiên cứu mới viết bằng tiếng Việt, rõ nguồn dữ liệu và giới hạn.
- Chạy smoke/import/test phù hợp sau thay đổi; không tuyên bố đã kiểm tra điều gì nếu không có output xác nhận.
