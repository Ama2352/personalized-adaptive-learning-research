# Notebook CPU và bằng chứng kỹ thuật chuẩn bị đưa lên Drive

Gói phiên bản02 giữ notebook Colab CPU, nguồn wrapper/tests và các bundle free-CPU calibration, outer readiness/wrapper/count03. Nguồn frozen thuộc commit `12a71bd7`. Chỉ có file văn bản và notebook, không model, dataset hoặc credentials. ZIP được dựng xác định trong RAM, mọi entry giữ timestamp cố định.

## Đã kiểm

- 57 file nguồn, tổng346.929byte; ZIP122.083byte, dưới5MiB.
- Notebook124.155byte giữ nguyên JSON, dự kiến upload với MIME `application/vnd.google.colaboratory`.
- Kiểm độc lập13test đạt trong7,51giây ở `INDEPENDENT_TESTS02.txt`, gồm orchestration nhỏ A2/A3, fitV1 và tiếp tục uploadfit. `INDEPENDENT_TESTS01.txt` giữ lỗi môi trường thiếu `scripts/akt` trong PYTHONPATH,9ca đạt/4ca importfail. Notebook đã thêm đường tools cần thiết, bản nguồn và notebook không bị sửa trong lượt này.
- `DESTINATION_READONLY.json` xác nhận đúng tài khoản Sang. Folderinput `1XNJZvRBw62nNh21Qev_Sxt6SsV5u5943` là con trực tiếp của thư mục KLTN người dùng cung cấp và có quyền ghi. Publisher sẽ tạo hoặc tái dùng thư mục con `technical-evidence20261117` ở đó.
- `INVENTORY.json` giữ SHA từng nguồn; `PLAN.json` giữ SHA notebook/ZIP và giới hạn dung lượng.

## Upload đã nghiệm thu sau khi mạng phục hồi

Lượt upload đầu bị bộ duyệt tự động từ chối vì chưa có bằng chứng thư mục đích. Sau khi kiểm metadata và chứng minh quan hệ với thư mục người dùng đã cung cấp, lượt chạy lại được duyệt. Lượt này dừng khi refresh OAuth gặp timeout kết nối tới `oauth2.googleapis.com`, trước yêu cầu Drive tạo thư mục/file. `FAILURE01.json` ghi nguyên nhân và phạm vi, không giữ token hay body xác thực.

Sau probe mạng của root xác nhận OAuth/Drive kết nối lại, publisher được thử lại đúng một lần với token Drive hiện có. Cả hai file đã upload và được đọc lại metadata cùng toàn bộ media để kiểm SHA/size. Giữ `FAILURE01.json` làm lịch sử lỗi transient; nghiệm thu hiện hành nằm trong `DRIVE_READBACK.json`. Không có yêu cầu đăng nhập lại hoặc sử dụng token Colab cho Drive.

- [Notebook mở trực tiếp Colab](https://colab.research.google.com/drive/1y8QBqsHZ52jQ624eQii9bwsRZnYcwxmt), MIME `application/vnd.google.colaboratory` đã kiểm, JSON giữ nguyên.
- [Thư mục bằng chứng kỹ thuật](https://drive.google.com/drive/folders/1rlL7li5Hfh7FjCLrVkREtBL6AJe5W18N), nằm dưới folder input đã xác minh.

Không có Modal compute hoặc ZIP được ghi local trong lượt này. Việc upload notebook chưa xác nhận notebook đã chạy trên Colab.
