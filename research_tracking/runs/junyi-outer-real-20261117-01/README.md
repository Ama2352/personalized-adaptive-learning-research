# Đánh giá Junyi outer A0–A3 —17/11/2026

## Mục đích và phạm vi

Dùng bốn checkpoint refit90 và bốn temperature đã nghiệm thu để dự đoán độc lập trên Development fold4. Cùng người học, target, vocabulary, cửa sổ100/100, FP32 và batch128. Các hệ số temperature được giữ nguyên từ calibration10. Không học thêm bằng đáp án outer. Không đọc Holdout Test và không đại diện cho kết quả CV năm fold.

## Những bước đã nghiệm thu

- `SOURCE_ACCEPTANCE01.json` xác nhận39.616người học,4.137.050target thuộc outer,144OOV và nguồn gốc đã pin.
- `CACHE_RESULT01.json` xác nhận72.423cửa sổ cùng ba cache đồ thị, không fit lại cạnh hoặc confidence.
- `HANDOFF_INVENTORY01.json` giữ SHA của303file chuyển lên Volume. Bản gốc manifest/cache giữ nguyên, request dùng vị trí mới riêng.
- `tests-root01.txt` ghi42kiểm thử đạt. Hai lỗi import khi gọi pytest thiếu PYTHONPATH đã sửa cách gọi trước lượt xác minh này.

## Điều khiển tài nguyên

CPU dựng cache, upload, kiểm checksum, nối nhãn, tính metric và sao lưu chạy local bằng `.venv`. H100 chỉ chạy inference numeric từ cache đã nghiệm thu. Mỗi model tối đa300giây function,240giây numeric, một GPU, không tự retry, dự phòng0,75USD trong trần workspace30USD. Checkpoint không cập nhật.

`run_h10001.py` chỉ chạy sau biên nhận đọc lại toàn bộ input. Dùng image của lượt calibration đã đạt, gắn đúng một file sửa điều kiện OOV và các worker ngoài KT. Hợp đồng77file bắt buộc kiểm đúng phiên bản trước forward. API kiểm image cũ trả UnimplementedError, vì vậy provenance image dựa vào log build/run cũ và kiểm runtime thực trong worker.

## Lưu trữ và tiến trình

`STATE.json` giữ điểm tiếp tục. `A*_GPU_RESULT01.json` chỉ xuất hiện khi numeric đã commit. `backup_outer01.py` giữ bản tạm có hạn mức trong cache được duyệt, kiểm manifest/payload rồi đóng archive cùng log lên Drive Sang. `A*_DRIVE_BACKUP01.json` chỉ xuất hiện sau kiểm SHA và owner/folder Drive. Các tệp truyền dở và lỗi quan trọng được giữ trong log theo lần, không thay kết quả đã đóng.

Uploader lần03 kẹt cầu nối Python đồng bộ/bất đồng bộ và được dừng đúng tiến trình của agent. Lần04 upload hoàn tất, lần05 tiếp tục riêng đọc lại bằng sáu luồng. Trong các bước này không cấp GPU. Một SQLite A3 tạm1.184.935.936byte đã được dọn sau khi calibration A3 được nghiệm thu trên Drive, inventory và biên nhận ở `A3_TEMP_SQLITE_CLEANUP_*01.json`. Model, checkpoint và kết quả calibration được giữ.

## Điều kiện được phép kết luận

Numeric hoàn tất và lưu trữ đúng chưa đủ kết luận mô hình tốt hơn. CPU còn phải nối đủ target đúng thứ tự/nhãn/OOV, áp dụng temperature đã pin và xuất AUC, Log Loss, Brier, ECE cùng coverage. So sánh BKT/GAM-KT phải lấy đúng fold4 và cùng tập dòng được dự đoán. Thống kê dùng đơn vị người học, không coi hàng triệu tương tác là quan sát độc lập. Junyi là bằng chứng dự báo quan sát; kết quả vòng kín Grade10 thuộc bước riêng.
