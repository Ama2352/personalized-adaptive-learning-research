# Kiểm và dọn fixture bị sandbox chặn ngày18/11/2026

Đợt bổ sung của yêu cầu bàn giao/lưu lạnh toàn repo. Quét thường bỏ qua496thư mục, quét metadata với quyền đọc đầy đủ phát hiện thêm khoảng4,18GB. Không đổi ACL. inventory_hidden.py chỉ chọn các gốc fixture được ghi từ lượt trước, loại private/credentials và790input/15model chuẩn, hash119.068file/4.183.347.282byte, không lỗi đọc.

Tái dùng nội dung có trong catalog Drive trước đó;23.423nội dung mới/3.246.022.285byte được đóng thành7gói/3.071.818.975byte, đọc lại từng member, upload vào kho lịch sử riêng và kiểm SHA Drive. Không đưa fixture vào thư mục bàn giao chính.

run_phase.py tái dùng công cụ của bundle workspace-cleanup-20261118-01 với bundle/prefix riêng để không ghi đè dữ liệu đợt trước. BULK_REMOTE_ACCEPTANCE.json kiểm20tham chiếu Drive trước gỡ; BULK_DELETE_PLAN.json/UNLINK_LOG giữ allowlist và kết quả. HIDDEN_SUMMARY.json giữ nghiệm thu nhỏ cho Git. Raw inventory/log đầy đủ trong archive bằng chứng, không commit các JSON lớn. Catalog nghiên cứu dùng chung được bổ sung, không sửa frozen manifests/model/prediction.

Đây là hồ sơ vận hành và fixture kỹ thuật. Không tạo sample nghiên cứu, chạy model, GPU/Modal hoặc thay kết luận RQ. Root .pytest_cache vẫn là ngoại lệ quyền đọc nếu quét cuối báo PermissionError; không tự thay ACL hoặc xóa mù khi không đủ inventory.
