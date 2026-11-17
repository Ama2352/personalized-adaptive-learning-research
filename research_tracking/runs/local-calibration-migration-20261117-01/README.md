# Chuyển CPU calibration A2/A3 sang local

## Khả năng thực thi hiện tại

Join/audit từ numeric đã lưu là pipeline streaming và có thể chuẩn bị trên CPU local. Không có huấn luyện hoặc suy luận GPU mới. Tuy nhiên entrypoint join hiện tự gọi fit sau khi publish raw, nên cần adapter tách ở callback raw-ready để tránh vô tình đi vào fit gom toàn bộ dữ liệu.

V1 hiện gom target và key vào list. Fitter tiếp tục tạo tuple, các set kiểm coverage, bản sort, list asdict, chuỗi JSON và logits. Không có disk spool sẵn. Với1.621.484target, guard4KiB/target ước6.641.598.464byte và yêu cầu available ít nhất11.069.330.773byte vì dùng hệ số0,6. Đây là estimate kỹ thuật chưa đo cho toàn bộ Junyi. Benchmark tổng hợp100.000target đã đo167.591.936byte peakRSS,4objective evaluations; ngoại suy toàn cohort khoảng2,1–2,2GiB chưa cộng reader/observation. RAM trống khoảng2GiB không bảo đảm V1 gom đủ dữ liệu.

## Đầu vào và staging tối thiểu

Giữ staging trong artifacts/akt theo run riêng trên D. Cần INPUT.zip134.525.060byte chứa frozen source, canonical calibration10 khoảng14MB, assignments, split manifest, roles, encoding90 và portable export metadata. Mỗi variant cần numeric ZIP khoảng35,77MB, window manifest17.337byte, admission23.893byte và các request/GPU/cache/population metadata đã pin. Không cần model weights, checkpoint optimizer, dataset Junyi gốc hoặc Holdout để nối numeric.

Đầu ra raw dự kiến gồm15.847Parquet, manifest, audit và ZIP cùng config/COMPLETE. Sau upload và đọc lại checksum trên Drive, các đầu ra fit temperature/manifest/resource/COMPLETE phải publish cùng cách. Giữ upload state riêng trong artifacts/akt/private; không ghi token vào source hoặc logs. Không xóa staging trước inventory và nghiệm thu Drive.

## Relocation trên Windows

Source KT phải copy nguyên byte từ input ZIP, source identity d22 giữ nguyên. Request path và cache path cần bản relocation riêng, không sửa bản nguồn cũ. GPU receipt có đường dẫn shard Linux tuyệt đối, cần receipt dẫn xuất với mapping path và before SHA rõ ràng, còn manifest/NPZ bytes giữ nguyên. Bản request dẫn xuất có fingerprint mới, không được chép nguyên Colab progress rồi xem là cùng invocation.

Artifact root cần trỏ physical D stagingroot qua adapter vận hành ngoài source KT; frozen module artifact root vẫn ghi /artifacts. Adapter khai báo và ghi provenance rõ, giữ tất cả guard canonical path/alias và role/checkpoint/source. Không tạo symlink vượt phạm vi để qua guard.

## Phương án RAM ít hơn, cần duyệt trước triển khai

Đề xuất helper ngoài KT dùng SQLite disk spool. Mỗi observation vẫn qua hàm kiểm prefix/target/role hiện hành. UNIQUE(learner,event) và key-table đối chiếu exact coverage. Sort theo learner,event,item,history như V1; hash JSON streaming phải khớp byte identity_hash([asdict(row)...]) với sort_keys, separators và allow_nan=False. Logit giữ phép scalar Python V1, objective giữ math.fsum đúng thứ tự và cùng golden search, bounds,200evaluationbudget. Không thay bằng NumPy reduction hay objective xấp xỉ.

Trước chạy thật phải parity toàn bộ TemperatureCalibration.to_payload giữa helper và V1 trên dữ liệu tổng hợp, kể cả target digest, T/LL/evaluationcount, ties, clipping, unsupported/OOV và coverage failures. Đo RSS thực của helper bằng synthetic bound để chọn budget, giữ nguồn/helper identity riêng trong execution receipt. Chưa triển khai helper, chưa chạy local full Junyi, chưa sửa hoặc nới guard.

## Nguồn

src/knowledge_tracing/akt/research_junyi_calibration.py::_fit_memory_budget và fit_response_temperature_from_raw_export; src/knowledge_tracing/response_calibration.py::fit_temperature; cloud_calibration_numeric_join.py; scripts/akt/free_cpu_calibration.py; research_tracking/runs/calibration-memory-20261117-01/BENCHMARK02.json. Đây là kế hoạch vận hành CPU, chưa tạo kết quả nghiên cứu mới.
