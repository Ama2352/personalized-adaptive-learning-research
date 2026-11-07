# Kế hoạch kiểm toán nghiên cứu ban đầu

**Mục tiêu:** kiểm kê bằng chứng trong workspace, dựng lại trạng thái thật của mô hình/thí nghiệm và lập hệ thống truy vết trong research_tracking/.

**Phạm vi:** chỉ đọc phần còn lại của repo; chỉ tạo tài liệu/registry trong research_tracking/. Không chạy thí nghiệm, đánh giá, benchmark hoặc test; không sửa dữ liệu, source, cấu hình hay artifact.

## Các bước

- [x] Xác định root, ignore rules, Git status, untracked và ignored; kiểm kê metadata thư mục nghiên cứu.
- [x] Đọc giao thức, manifests, metrics, reports và log ổn định của BKT, GAM-KT, AKT.
- [x] Đối chiếu metric chính với JSON gốc và kiểm tra nguồn paired bootstrap.
- [x] Phân loại validity, comparability, RQ gaps và sáu sprint.
- [x] Tạo evidence index, registry, ledger, audits và báo cáo ban đầu.
- [x] Đối chiếu cú pháp JSON và danh sách file vừa tạo; không chạy test.

**Giới hạn:** dataset gốc lớn chỉ ghi metadata; không đọc toàn bộ. Không duyệt sâu virtual environments/cache hoặc WSL image. AKT pilot log chỉ được đọc sau khi metadata cho thấy lần ghi cuối ổn định và manifest báo terminal failed.
