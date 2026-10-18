# Quyết định đã chốt

- Dùng standard BKT từ CAHLR/pyBKT 1.4.3; một model cho mỗi `exercise`, không tự viết EM.
- Outcome là trường `correct` gốc của Junyi. Sắp thứ tự bằng `time_done`; dùng `source_row` làm tie-break xác định khi timestamp trùng.
- Dedupe chính xác chỉ trong dữ liệu phái sinh, giữ lineage; không sửa CSV gốc.
- Chia 80/20 theo `user_id`; 5 fold student-disjoint trong Development.
- Cấu hình cuối: `num_fits=1`, `forgets=False`, `tol=0.005`, `maxiter=100`, seed 42.
- pyBKT C++ được dùng ở WSL2. Patch số học likelihood là một phần của provenance, không được bỏ hoặc sửa ngầm.
- Giữ nguyên vị trí dataset, artifacts Windows, venv và distro WSL; chỉ chuyển source, runner, kết quả WSL và tài liệu theo relocation manifest.
