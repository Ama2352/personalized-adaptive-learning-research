# Đọc trước tối đa bốn member khi stream numeric ZIP

## Mục đích

Lượt upload A2 đang chạy cho thấy phần đọc từng object qua API có độ trễ đáng kể. Gói này chỉ thay producer local để chồng thời gian chờ mạng giữa tối đa bốn member. Không thay nội dung archive, model, source KT, dataset hay phương pháp nghiên cứu.

## Cơ chế và hợp đồng

`iter_zip_bytes(volume, plan, chunk_size=8*MiB, prefetch=4)` tạo tối đa bốn task đọc nguồn, vẫn lấy kết quả theo đúng thứ tự plan. Mỗi member tối đa2MiB, được kiểm đủ byte và SHA trước khi ghi vào ZIP. Ngày, attrs, headers, CRC, thứ tự member và ZIP_STORED giữ quy ước trước đó. `prefetch=1` cung cấp đường đối chứng tuần tự.

Queue đầu ra vẫn tối đa hai block. Dự toán bảo thủ cho payload/read buffers dưới48MiB, ngoài buffer8MiB của transport. Đây là dự toán từ giới hạn số reader và kích thước member, chưa phải số đo peakRSS trên upload thật.

## Đã kiểm

`tests03.txt/xml` xác nhận33ca đạt trong0,74giây, gồm18ca archive và15ca transport đã có. Kiểm mới so archive hoàn chỉnh ở prefetch1và4 bằng bytes/SHA, kích thước bằng công thức, max reader hoạt động đồng thời bằng4, hủy consumer đóng toàn bộ reader đã bắt đầu và thread producer, SHA sai đóng cả các task còn chờ.

Tính byte-identical cho phép uploader tái tạo cùng prefix khi tiếp tục từ offset Drive đã xác nhận. Các ca transport mô phỏng vẫn kiểm việc tái tạo/hash toàn stream qua restart. Lượt này chưa thực hiện resume upload thật hoặc đo mức tăng throughput thực tế.

## Failure và giới hạn

Lượt đầu kiểm cancellation đã đóng đủ5reader nhưng fixture đòi đúng4reader tổng cộng. Một reader tiếp theo có thể bắt đầu trước khi consumer đóng, trong khi số reader đồng thời vẫn tối đa4. Assertion được sửa thành mọi reader đã bắt đầu đều đóng, giữ kiểm maxconcurrency4.

`tests02.txt/xml` giữ lượt18pass/15error vì fixture transport dùng thư mục temp Windows không có quyền truy cập. Lượt sau dùng thư mục test mới trong `artifacts/akt/test-temp/modal-volume-prefetch-20261117-01`, không đổi source transport. Cả33ca đạt. Không dùng dữ liệu thật hoặc tạo binary nghiên cứu trên local. Không gọi compute, Volume API hay Drive API trong các tests.

Nguồn đã freeze sau lượt cuối. Parent agent quản lý dừng/khởi động lại uploader local và đối chiếu Drive offset, công việc đó nằm ngoài gói này.
