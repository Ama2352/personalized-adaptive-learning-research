# Transport stream local sang Google Drive

## Phạm vi

`scripts/akt/drive_stream_upload.py` nhận generator byte tái tạo được, chuyển trực tiếp sang phiên upload Drive và giữ riêng trạng thái phục hồi. Không tạo file ZIP, predictions hay binary khác trên đĩa local. Gói này chỉ kiểm bằng Drive giả lập, chưa gọi upload thật, Modal compute hoặc GPU.

API công khai nhận `session`, kế hoạch bốn trường `folder_id`, `name`, `total_bytes`, `source_plan_sha256`, hàm `factory()` sinh các block byte và đường dẫn state trong `artifacts/akt/private/`. Caller phải cấp đúng kế hoạch nguồn và quyền chuyển các member. Transport kiểm tài khoản `honguyenminhsang2005@gmail.com` cùng quyền thêm file vào folder đã chốt.

## Cơ chế phục hồi và kiểm toàn vẹn

- Dùng OAuth session và helper atomic state/single-writer lock của uploader hiện có. URI upload chỉ ghi vào state private, không có trong receipt trả về.
- Mặc định gửi chunk 8 MiB, căn bội 256 KiB. Tổng ZIP tối đa 256 MiB, từng block nguồn tối đa 8 MiB. Generator được đóng trong `finally` khi thành công, bị ngắt hoặc lỗi.
- Hỏi offset Drive trước mỗi lượt tiếp tục. Với phản hồi partial hoặc mất mạng, dựng lại generator, bỏ qua prefix đã commit nhưng vẫn hash toàn bộ byte từ đầu. Dữ liệu chỉ đi qua bộ nhớ.
- Tối đa hai lần thử lại trong một lời gọi và một phiên upload thay thế trong vòng đời state. File ID được cấp trước và giữ cố định để tránh tạo file trùng khi mở lại phiên.
- Khi mất phản hồi hoàn thành rồi phiên hết hạn, kiểm file ID đã tồn tại trước khi mở phiên mới. File đã đủ byte vẫn phải dựng lại và hash toàn bộ nguồn để xác minh.
- Chỉ nghiệm thu sau GET metadata cuối khớp ID, tên, parent, tổng byte, SHA-256 và trạng thái chưa bị xóa. State đã hoàn thành cho phép GET xác minh lại mà không dựng generator.

`source_plan_sha256` khóa kế hoạch qua các lần chạy. Generator phía archive phải tự xác minh từng member theo SHA trong kế hoạch. Hash Drive cuối chứng minh byte stream thực tế đã tới Drive đầy đủ.

## Kết quả kiểm

`TESTS01.txt` ghi 45 ca đạt trong 4,20 giây, gồm 15 ca stream và 30 ca uploader cũ. Các ca mới kiểm upload bình thường, partial chunk, mất mạng sau commit, process restart, phiên hết hạn, commit hoàn chỉnh trước mất phản hồi, đổi kế hoạch nguồn, sai tài khoản, sai SHA cuối, giới hạn dung lượng, thiếu/thừa byte, giới hạn retry và đường dẫn private. Không dùng mạng hoặc credentials thật.

Kiểm bằng môi trường dự án.

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/akt/test_drive_stream_upload.py tests/akt/test_drive_resumable_upload.py -q -p no:cacheprovider
```

## Giới hạn còn lại

Chưa đo RSS hoặc throughput của đường truyền thật. Caller cần nghiệm thu generator ZIP từ Volume và kế hoạch member trước khi chuyển artifact nghiên cứu. Caller cũng giữ receipt nhỏ và đối chiếu thành công trước khi cân nhắc xóa bất kỳ bản nguồn nào.
