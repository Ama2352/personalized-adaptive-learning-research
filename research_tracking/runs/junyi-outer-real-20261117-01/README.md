# Đánh giá Junyi outer A0–A3 —17/11/2026

## Kết quả hiện hành đã hoàn tất

Cả bốn lượt H100 đã hoàn tất và trả container. Mỗi model có4.137.050target/39.616người học,4.136.906dự đoán fitted và144OOVnull. CPU đã nối đủ target/nhãn theo thứ tự, xuất cả xác suất gốc và hiệu chỉnh, tính bộ chỉ số chung và kiểm cùng source-key digest. Tám archive numeric/log và Parquet có nhãn đã được lưu Drive Sang. `A*_GPU_RESULT01.json`, `A*_CPU_EXPORT_DRIVE01.json` và `OUTER_COMPARISON01.json` giữ nguồn trực tiếp.

| Model | Log Loss sau hiệu chỉnh | AUC | Brier | ECE15 |
|---|---:|---:|---:|---:|
| A0 |0,360452822|0,804765483|0,110201520|0,000614434|
| A1 |0,360444300|0,804778419|0,110198524|0,000703182|
| A2 |0,360452748|0,804769088|0,110201066|0,000621000|
| A3 |0,360432824|0,804775033|0,110192474|0,000788904|

Trước hiệu chỉnh, A1/A3 giảm Log Loss và Brier so với A0 với pHolm dưới0,05 trong family đã khai báo. Sau hiệu chỉnh, ba model đồ thị so với A0 đều chưa đạt ngưỡng ấy ở hai endpoint chính. A3−A0 ở Log Loss hiệu chỉnh là−0,000019998, CI95%[−0,000043986,+0,000004741], pHolm1,0. Đây là bằng chứng dự báo có điều kiện trên một fold/một lần khởi tạo. Cần thí nghiệm riêng để xác định cơ chế và tác động học vòng kín.

`STATISTICAL_PLAN01.json` và `STATISTICAL_PLAN_TIMING01.json` ghi ngoại lệ quy trình. Family24/cách tính p được khóa sau suy luận GPU, trước xem bất kỳ chỉ số outer nào. Không mô tả là preregistration trước thu thập dữ liệu. Bootstrap ghép người học2.000lượt, seed42, giữ estimand gộp theo response. pbootstrap được tính bằng phân phối null tái định tâm rồi Holm chung24test, CI95% là khoảng biên. Hai kiểm mới đối chiếu LL/Brier và draws với estimator bootstrap sẵn có đạt trong `tests-bootstrap01.txt`. Phạm vi diễn giải thống kê ở mức thăm dò.

Nguồn figure là `OUTER_COMPARISON01.json`, `OUTER_METRICS01.csv` và `OUTER_PAIRED_PRIMARY01.csv`. `build_outer_figure02.py` dựng SVG/PNG/PDFv02, dùng palette/quy ước figures4papers đã lưu giấy phép. v01 được giữ để truy vết chỉnh khoảng cách chữ. Figure v02 đã xem trực tiếp bản PNG để kiểm chữ/số. Hai báo cáo GVHD được cập nhật bằng `update_report_metrics01.py`.

Modal ghi mức dùng trước0,91158794USD và sau1,61158794USD ở hai lần API chỉ đọc, tăng0,70USD tại thời điểm kiểm. Billing có thể cập nhật. Bốn worker mất196,15/82,53/89,21/90,62giây. A0 có setup lạnh159,86giây, A1 có setup10,50giây. Số đo không chứng minh GPU luôn bận hoặc đã đạt50%utilization. CPU export A1/A2/A3 lần lượt365,17/340,17/435,20giây trên local, peak process-tree RSS lấy mẫu khoảng1,23–1,24GiB. Toàn bộ CPU dựng/join/metrics/upload trong lượt này chạy local.

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
