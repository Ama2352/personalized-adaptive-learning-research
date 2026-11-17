# Candidate compact raw calibration trên CPU local

## Mục tiêu và hợp đồng

Public iter_pinned_prediction_export không yêu cầu shard chỉ có một learner. Giới hạn learner-atomic của writer gốc phục vụ resume. Candidate này chỉ nhận raw đã complete và pin đủ manifest/shards, tạo layout dẫn xuất đã complete với resume_supported false, giữ nguyên source. Mỗi shard mới tối đa32.768row. PyArrow đọc batch1.024row, từ chối batch vượt8MiB, giữ nguyên schema/type/column order và scalar values. Public reader vẫn DuckDB128MB, threads1 và tắt spill như frozen source. Không sửa KT source hoặc globals đang dùng bởi A2/A3 thật.

Digest đầy đủ PredictionRecord được tính trước/sau. Sau compaction, public reader đọc lại từng shard để so exact record-stream order/count/digest; chỉ khi khớp mới ghi COMPLETE. Manifest nguồn, shard nguồn và identity/binding/population giữ nguyên, SHA gốc/derived/helper ghi ở receipt. Lỗi readback giữ manifest dẫn xuất incomplete, không có COMPLETE. Một file toàn1,62triệurow đã bị loại khỏi hướng production vì ORDER BY trong public reader có thể vượt128MB khi spill tắt.

## Kiểm thử

tests02 xác nhận7ca đạt11,14giây với cùng source helper bounded hiện hành. So public reader trước/sau và toàn payload fit_raw_spooled trên2learner20target có2OOV/null, cả layout một shard và layout7row/shard chia qua boundary learner. Các ca invalid source/incomplete/pin/diskcap/existingoutput từ chối và giữ nguyên Parquet gốc.

tests03 bổ sung ca2.048row/2learner, batch1.024 và4shard512row. Lượt này gặp gián đoạn host lớn, elapsed2.602giây và hai ca fit timeout theo budget90giây. Sáu ca còn lại đạt, gồm multi-batch2.048row exact public-stream. Giữ nguyên log/xml, không diễn giải elapsed này thành tốc độ fitter hoặc benchmark. Nhánh chính cũng quan sát một lệnh chờ60giây trả sau1.147giây, đã yêu cầu tạm dừng chạy thêm kiểm thử. Vì vậy chưa có lượt full suite hiện hành hoàn tất green sau bổ sung ca mới.

## Trạng thái

CANDIDATE_SYNTHETIC_PARTIALLY_VERIFIED — NOT_REAL_VALIDATED. Chưa chạy raw A2/A3 thật, chưa chạm source/cache/output đang chạy. Cần root review và chạy focused suite khi host ổn trước khi dùng trên raw A3 đã complete. Không có compute cloud, GPU hoặc đọc dataset thật từ bundle này.

## Lợi ích dự kiến

Nếu1.621.484row ghép shard tối đa32.768row, dự kiến50file thay15.847file. Số lần mở reader mỗi replay giảm khoảng317lần. Đây là phép tính về layout và connection count, không phải số đo tăng tốc. Chi phí copy/readback một lần và thời gian thực toàn pipeline chưa đo.

## Tái chạy

Dùng .venv với PYTHONPATH src;scripts/akt;tests/akt, chạy pytest tests/akt/test_local_calibration_compact.py bằng basetemp mới trong artifacts/akt/test-temp. Hàm candidate nằm tại scripts/akt/local_calibration_compact.py::compact_raw_export. Không thay đổi các files helper migration/fitter đang được root dùng.
