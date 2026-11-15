# Dung lượng KLTN và đợt dọn cache ngày16/11/2026

## Nguồn tăng dung lượng

Đã kiểm metadata268.328file trước dọn. Tổng dung lượng logic149,94GB, tương đương139,64GiB, phù hợp số139GB người dùng thấy trongWindows. Bảng sau dùngGiB để dễ đối chiếu.

| Vùng | Dung lượng trước dọn | Vai trò |
|---|---:|---|
| experiments/akt/results |64,13GiB|Checkpoint, artifactZIP, prediction và các bản export theo run|
| artifacts/akt/staged |38,67GiB|Bản snapshot input/cache phục vụ các lượt training|
| artifacts/akt/test-temp |6,73GiB|Fixture pytest tạm13–14/11|
| artifacts/akt/window-cache |3,93GiB|Cache cửa sổ dữ liệu|
| artifacts/akt/confidence |3,88GiB|Đầu vào và kết quả fit confidence|
| artifacts/akt/local-tests |3,55GiB|Hồ sơ/nguồn kiểm local, cần phân loại riêng|

Toànrepo có37,49GiB ZIP và36,53GiB file.pt. Các giá trị này chồng với bảng thư mục, không cộng thêm vào tổng. Những file ZIP lớn nhất khoảng1,7–2,4GB, cómtime12–14/11. Model refit gọn A0/A1/A2 mỗi gói khoảng28MiB. Do đó dung lượng65GB của vùngAKT chủ yếu phản ánh toàn lịch sửcheckpoint/archive và bản trung gian. Không thể xác định chính xác thời điểm ổD giảm đột ngột chỉ từmtime khi chưa có baseline trước đó.

Lượt nhập Drive023 mới có ZIP26,8MB và checkpoint29MB. Dependency CUDA trong lượt dựngimage mới được tải trênCPU Modal. File tạm của client mới đặt trênD.

## Đợt dọn đã thực hiện

1. Ghi inventorySHA-256 đầy đủ của fixture cũ.
2. Đối chiếuSHA lầnhai và lưu ZIP8.435file log/config/nguồn văn bản, kiểm lại toàn bộ file giữ.
3. Chọn37thư mục pytest cũ13–14/11, loại các thư mục mới16/11 khỏi danh sách. Kiểm đường dẫn tuyệt đối và junction trước xóa.
4. Bộduyệt tự động ban đầu chặn vì cần quyền xóa cụ thể và archive không giữ tất cảbinary. Người dùng xác nhận rõ cho phép xóa đúng danh sách. Lệnh được thực hiện sau xác nhận.
5. Dọn thành công37/37thư mục, không lỗi. Fixture binary đã bị xóa, cần dựng lại từ test nếu muốn chạy lại. File log ởroot test-temp và các test mới16/11 giữ nguyên.

Đã giải phóng quan sát7.238.733.824byte, khoảng7,24GB. ỔD tăng từ7.138.615.296 lên14.377.349.120byte trống, khoảng14,38GB. Biến động đồng thời của tiến trình khác có thể làm chênh nhẹ với tổng dung lượnglogic7.229.160.853byte của danh sáchfixture.

Dataset, BKT lịch sử, venv cũ, WSL, source, staging đang dùng, model/checkpoint nghiên cứu và các bundle bằng chứng nằm ngoài phạm vi xóa. Các gói model cuối cùng A0–A3 đã được agent training nghiệm thu riêng.

## Hồ sơ có thể tra cứu

- [Kiểm kê trước dọn](../runs/junyi-refit-pipeline-20261114-01/disk-usage-20261115-01.json).
- [Danh sách đã kiểm và archive giữ log](../runs/junyi-refit-pipeline-20261114-01/disk-cleanup-ready-20261116-01.json).
- [Kết quả xóa và dung lượng thực đo](../runs/junyi-refit-pipeline-20261114-01/disk-cleanup-result-20261116-01.json).
- Inventory đầy đủ tại `artifacts/akt/runtime/disk-cleanup-test-cache-20261115-01.jsonl`; archive tại `artifacts/akt/runtime/pytest-cache-logs-before-cleanup-20261116-01.zip`. Cả hai giữ nguyên trênD.

Đây là đợt dọn cache đầu tiên. Các staging/archive lớn còn lại cần đối chiếu phụ thuộc, bản lưu và SHA trước một đợt thu gọn riêng. Chưa xóa model, source snapshot hoặc lịch sử thí nghiệm để giải phóng thêm dung lượng.
