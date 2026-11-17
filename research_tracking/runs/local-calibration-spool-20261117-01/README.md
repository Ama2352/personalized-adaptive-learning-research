# Fitter calibration V1 giới hạn RAM trên CPU local

## Kết quả kiểm

Adapter SQLite ngoài source KT trả toàn bộ payload TemperatureCalibration khớp chính xác fitter public V1 trên20ca kiểm. Các ca gồm probability clipping, OOV/null, nhãn một lớp, không có dự đoán, các nghiệm hòa, Unicode và giá trị gần nhau, đảo thứ tự input; budgets4/17/200giữ đúng T, hai LogLoss, số lần objective, target digest, unsupported reasons và metadata. Missing/extra/duplicate/wrong-role/binding bị từ chối. tests02.log xác nhận20ca đạt trong0,75giây. Lỗi collection trước implementation giữ tại tests-red01.log.

## Cách giữ toán học V1

Adapter đọc AST của hàm public fit_temperature, lấy nguyên phần từ nested loss đến return cuối và compile không sửa. Cùng globals V1 được dùng cho scalar objective, math.fsum, golden search, bounds, tie-break và số lần đánh giá. SQLite chỉ thay biểu diễn/unique/sort. Mỗi logit được tính bằng V1._logit. Cursor đi theo cùng thứ tự learner/event/item/history. Digest của list target được băm streaming với đúng JSON sort_keys/separators/allow_nan như identity_hash gốc. Receipt riêng ghi adapter SHA, original V1 identity và solver AST SHA. Nguồn KT và _fit_memory_budget cũ giữ nguyên.

## Tài nguyên thực đo

benchmark01.py chạy100.000target tổng hợp, đúng4objective evaluations, wall13,97giây, sampledpeakRSS35.598.336byte, database68.730.880byte. Trần512MiB/90giây đạt. RSS lấy mỗi1024row, không phải hard limit hệ điều hành. Không ngoại suy4evaluation thành thời gian fit Junyi200evaluation. Database tổng hợp giữ tại artifacts/akt/tmp/local-calibration-spool-20261117-01/fit.sqlite, không kèm binary trong bundle evidence. Đây không phải số liệu nghiên cứu Junyi.

## API tích hợp

scripts/akt/local_response_calibration.py::fit_temperature_spooled nhận targets iterator, binding và partition V1, expected_target_keys iterator, database mới canonical, LocalCalibrationBudget và max_evaluations mặc định200. Trả TemperatureCalibration V1, ghi receipt cạnh database. Caller phải kiểm source/phase/calibration-only/prefix/raw shard pins trước, dùng iter_calibration_observations hiện hữu. Không bỏ guard source hoặc roles. Không dùng itertools.tee cho1,62triệu observations vì buffer có thể lớn; nếu cần hai iterator độc lập thì replay reader đã pin, hoặc bổ sung API paired stream có kiểm riêng sau review.

Caller cần pin bản frozen source từ INPUT.zip trước import, thay vì coi identity CRLF checkout Windows là source d22 Linux. Source adapter ghi identity V1 thực tế được import. Database chỉ trong staging run trên D; upload config/raw/temperature/receipt lên Drive và đọc lại SHA. Không tự xóa các đầu ra cũ.

## Giới hạn

Chưa chạy full A2/A3 thật bằng adapter này. Bounded resource check là hợp đồng adapter mới đã đo tổng hợp, không phải nới guard fitter cũ. Không thay split, mô hình, hyperparameter, temperature bounds, evaluation budget hoặc protocol. Chưa có claim đánh giá độc lập outer-fold. Root phải nghiệm thu adapter, nguồn frozen và Windows relocation trước real run.
