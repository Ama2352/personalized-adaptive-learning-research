# DEMO03 · Đối chiếu nguồn đồ thị từ fresh120

## Phạm vi đã triển khai

Sáu file demo và test được sửa. Bảng mới ở cùng trang, có bộ chọn block, năng lực nền và λ. Endpoint cố định `/api/rq2-source-contrast` trả các outcome, Q và K đã lưu. Nguồn được ghim vào manifest recovery riêng, schema ba trường, cùng bảy JSON chọn lọc có giới hạn 64 KiB mỗi file. Loader replay cũ giữ nguyên. Nguồn lớn, checkpoint và dataset không được đọc.

Danh mục giữ chín điều kiện A0, A1/A2/A3 theo expert hoặc learned graph, SAKT và GKT. Chúng được ghi rõ chưa phục vụ replay nghiên cứu trong demo. GAM là replay sẵn có. BKT là tham chiếu Junyi lịch sử. Thông báo startup dùng số thực tế năm manifest và 16 output chọn lọc.

## Bằng chứng kiểm

`pure01-receipt.json` ghi 39 ca đạt, 0 failure/error/skip, 8,9337592 giây trong cap 30 giây. Pytest báo 7,76 giây. Log, JUnit và source SHA trước–sau được giữ tại đây. Audit sau làm nóng metadata Windows thật chặn socket và child process. Không có denied event hoặc import Torch/NumPy/Pandas/knowledge_tracing.

Routing được gọi bằng handler thật trên transport thay thế chưa bind. Các ca kiểm đủ 60 lựa chọn, coupling, Q/K, phạm vi query, nguồn hỏng trước listener và an toàn DOM tĩnh. Lượt này chưa kiểm server HTTP đang chạy, thực thi JavaScript trên browser hoặc bố cục render. Bộ test HTTP cũ vẫn còn trong module và nằm ngoài nhóm 39 ca được chạy.

## Giới hạn diễn giải

120 thế giới thuộc mười block ghép cặp, một graph học cố định. Graph môi trường và controller vẫn chung. Q là expert trừ learned. K là Q ở λ = 0,55 trừ Q ở λ = 0. K bằng 0 ở mức 1300 là đối chứng bất hoạt dự kiến theo nguồn. Confidence không được dùng làm trọng số GAM. Viewer thêm 0 mẫu, không gọi mô hình và không cấp kết luận hiệu quả hoặc hoàn tất RQ/T21.

## Hồ sơ

`inventory-before.json` giữ copy proof cho sáu file trước sửa. `handoff-inventory.json` giữ nguồn sau sửa và inventory logs, xác nhận phần loader closed-loop/validation cũ nguyên nội dung sau chuẩn hóa line ending. CSS giữ nguyên. Không có failure mới trong lần pure01. Đây là hồ sơ engineering cục bộ, chưa phải bundle đã đóng hoặc nghiệm thu UI.
