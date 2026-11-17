# Tìm lại và nghiệm thu metadata calibration trên Drive

Đã chuẩn bị `fetch_calibration_metadata01.py`, chưa gọi Drive trong đợt chuẩn bị này. Chờ root xác nhận fit xong trước khi lấy index thực. Script chỉ đọc metadata/json nhỏ, không lấy raw ZIP, prediction hoặc model.

Đích là tài khoản Sang, thư mục KLTN `1vaojIEDvwtE-vZgjlybwzrsjrGNE_8O7`, runfolder `junyi-calibration-real-20261117-01`. Mỗi variant có tranche `a<i>-fit-calibration-a<i>-join-20261117-01`. Script yêu cầu một thư mục duy nhất đúng parent và kiểm account trước truy vấn.

Mỗi fit giữ năm JSON cần nghiệm thu gồm COMPLETE.json, config.json, resource.json, fit/temperature.json và fit/manifest.json. Chỉ tải ba file nhỏ COMPLETE, resource và temperature nếu có COMPLETE. Hai file config và fit/manifest chứa hàng nghìn shard pin nên chỉ lưu ID, byte, SHA server và link Drive, không tải về PC. Thiếu fit được ghi FIT_METADATA_NOT_PUBLISHED_YET, không suy ra fit thất bại. Giới hạn 256 KiB/file tải và 2 MiB tổng tải cho một lần gọi. File local giữ đúng raw byte từ Drive.

Metadata cần khớp SHA-256 do Drive trả và inventory của COMPLETE, kể cả hai file chỉ lập index. Temperature cần đúng identity, recipe V1, giới hạn T, class counts, số target và binding. Script đối chiếu checkpoint, encoding, roles, inference source và canonical domain với MODEL_INDEX/REQUEST/POPULATION đã ghim. Population identity dự kiến được ghi riêng từ nguồn frozen, không tuyên bố đã đọc nội dung fit manifest lớn. Các file nguồn đối chiếu chỉ là JSON nhỏ. Không đọc dataset hoặc weights.

`CALIBRATION_METADATA_PREFLIGHT01.json` xác nhận đủ pin nguồn metadata của bốn model. `CALIBRATION_METADATA_TESTS04.txt` đạt **8/8** trong 0,14 giây trên Drive giả, gồm account sai, folder trùng, file tải vượt cap, checksum sai, fit chưa xuất bản, binding frozen sai, config lớn được giữ index-only và lượt fetch hợp lệ/idempotent. Các lượt trước được giữ để truy vết. Đây là nghiệm thu software, chưa xác nhận bốn fit thực đã hoàn tất.

```powershell
.\.venv\Scripts\python.exe -B research_tracking/runs/junyi-calibration-real-20261117-01/fetch_calibration_metadata01.py --output research_tracking/runs/junyi-calibration-real-20261117-01/CALIBRATION_DRIVE_INDEX01.json
```

Khi index thực có đủ bốn trạng thái CALIBRATION_DRIVE_METADATA_VERIFIED, metadata cho phép tìm lại temperature/config/provenance/resource trên Drive. Log Loss trước/sau trong temperature là số đo trên chính calibration đã dùng fit T. Cần đánh giá độc lập sau đó để kết luận khả năng khái quát.
