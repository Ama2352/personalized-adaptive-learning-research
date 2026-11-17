# Sửa lineage thư mục Drive trước khi launch

Root đã đọc metadata thực và xác nhận ZIP thuộc thư mục con `1xFW0BKnfph3jZdsJABW3WWB8b5TnGCSg`, nằm trong thư mục KLTN `1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7`. Nguồn đối chiếu nằm tại `research_tracking/runs/cloud-calibration-input-upload-20261117-01/STRICT_ACCEPTANCE.json`.

Worker hiện kiểm ba metadata call trước tải media. Email phải là Sang, file phải có parent đúng thư mục con, thư mục con cần là folder chưa xóa và có parent đúng thư mục KLTN. Pin ZIP/plan giữ nguyên. Lần đầu giả định ZIP nằm trực tiếp trong thư mục KLTN, đã sửa trước khi child agent gọi cloud. Manifest trước giữ SHA của bản software ban đầu, MANIFEST02.json ghi bản hiệu chỉnh.

Thêm `routing_region='ap-south'` theo kết quả CPU gate của root, tránh input plane mặc định đã timeout. SDK local có cả tham số routing_region và serialized. Đây là kiểm tính tương thích chữ ký, chưa xác nhận cloud staging hoạt động.

`tests04.txt` đạt **15/15** trong 0,46 giây. Ca mới xác nhận ba metadata call và từ chối lineage sai trước media. Source hiện đóng để root review/launch. Không có tải thật, chi phí cloud hoặc GPU từ nhánh này.
