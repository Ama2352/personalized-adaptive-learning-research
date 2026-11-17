# Kiểm đọc lại Drive cho bàn giao KLTN

## Kết quả

Kiểm trực tiếp lúc2026-11-18 01:39 giờ Việt Nam:173/173file trong biên nhận bàn giao hiện hành có mặt, không trong thùng rác, khớp tên/dung lượng/SHA-256/thư mục cha. Tất cả nằm dưới thư mục `KLTN_BAN_GIAO_DAY_DU_20261118`, ID `1T6GseWOnUbbj-eXTcWIELAp2hPemGrLQ`. Quét đệ quy không lỗi, thấy173file. Tổng43.074.413.127byte, gồm35.154.236.922byte nhóm lịch sử; phần còn lại7.920.176.205byte. Không cần tải toàn bộ lịch sử để bắt đầu.

Nguồn đối chiếu là UPLOADED_PACKAGES01, SUPPLEMENT_UPLOAD01, ORIGINAL_RUNS_UPLOAD01 và COPIED_ASSETS01 trong bundle full-project-transfer-20261118-01. Trong lúc kiểm, biên nhận ORIGINAL_RUNS_UPLOAD01 đã hoàn tất đủ6archive. Không sửa các biên nhận này.

## Độ phủ đầu vào

758file của năm nhóm canonical/splits, GAMsource-map, Grade10corpus, roles/refit và exercise/graph khớp SHA/dung lượng trong member inventories của các gói đã kiểm metadata Drive.32file Method24 còn lại ở gói riêng: đã đọc payload13.059.198byte từ Drive, kiểm archiveSHA và SHA/dung lượng từng member, đạt32/32. Tổng790file đầu vào theo REQUIRED_INPUTS02 đều được định vị và đối chiếu. INPUT_COVERAGE.json chỉ ghi độ phủ trong các gói local; phần32file không có trong đó được giải quyết riêng bởi METHOD24_READBACK.json.

## Phần chưa chứng nhận

- Đây là kiểm đủ file theo inventory và biên nhận đã chọn, không kiểm mọi file trong repository hoặc mọi phụ thuộc chưa được khai báo.
- Phần lớn payload dùng SHA-256 do Drive cung cấp đối chiếu biên nhận; chỉ Method24 được tải đọc lại trong lượt này. Không tải hàng chụcGB hoặc nạp model/training.
- Thời điểm quét, gốc thư mục chỉ có bốn thư mục con. Chưa thấy master manifest/hướng dẫn/helper khôi phục độc lập trong cây Drive. Các tài liệu đang được chuẩn bị local không được coi là đã xuất bản.
- Chưa cold restore đầy đủ, chưa chứng nhận chạy tiếp trên máy mới, chưa kiểm quyền truy cập bằng tài khoản người nhận.
- Source là snapshot đóng gói của đợt transfer, không tự bao gồm mọi sửa đổi phát sinh sau snapshot.

## Công cụ và lỗi giữ lại

Skill google-drive được áp dụng. Connector xác nhận thư mục tồn tại nhưng search trả rỗng và metadata chuẩn hóa không có checksum. Dùng GoogleDriveAPI chỉ đọc qua đăng nhập sẵn có, không xuất token và không thay quyền/file remote. Lần chạy trong sandbox gặp WinError10051; chạy lại với quyền mạng được duyệt thành công. Không cấp Modal/container/GPU.

`check_drive.py` thực hiện GETmetadata và list thư mục; `READBACK.json` giữ từng đối chiếu và cây. `check_method24.py` đọc gói nhỏ; `METHOD24_READBACK.json` giữ đối chiếu32member. `INPUT_COVERAGE.json` giữ so khớp inventory đầu vào. `MANIFEST.json` giữ hash các bằng chứng của lượt này.
