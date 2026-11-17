# Retry CPU, metadata Drive và đo GPU thực

## Thay đổi phần mềm

Root đã xác nhận image C0 qua PREFLIGHT03 trước lượt sửa này. C0 dùng source image bất biến cũ, không bị thay đổi bởi source wrapper local mới. Không gọi cloud/GPU trong nhánh này, KT source giữ nguyên.

Allocation ID nay phải là identifier tối đa48ký tự. Operation dùng tên variant/stage/allocation riêng, child nhận `--attempt-id`. CPU raw, fit và numeric archive có suffix attempt. Retry CPU bằng allocation mới tái sử dụng **đúng request GPU và receipt numeric cũ**, không đổi source/population/budget trong request. Allocation CPU mới nằm ngoài request và phải được root budget controller duyệt riêng. Lý do giữ nguyên request là numeric config đã được ghim, archive kiểm equality với request gốc. Không chạy lại GPU chỉ vì fit hoặc upload CPU lỗi.

`request_pin` chuyển đúng output `{path,sha256,bytes}` của put_request sang `{path,sha256}` trước consumer. Consumer pinned vẫn từ chối field lạ. Đây là sửa hợp đồng nối producer/consumer, không nới kiểm SHA hoặc source. Regression gọi put_request→normalize→pinned thật.

## Metadata Drive trước và sau GPU

`create_app()` thêm `publish_metadata(run_id, operation_names)`, CPU1core/1024MiB/timeout900, Drive Secret riêng, không GPU. Root gọi sau CPU cache hoàn tất để config/result/log có biên nhận Drive trước H100. Sau GPU thành công hoặc exception, gọi cùng finalizer cho operation GPU để giữ raw telemetry/logs trên Drive. Operation names có trong return của `_run`, hoặc dựng bằng `operation_tranche(variant,stage,allocation_id)`. Finalizer cũng chấp nhận tên operation cũ của C0.

Finalizer chỉ nhận operation đã có COMPLETE hoặc FAILED. Allowlist gồm config,worker.log,result,COMPLETE,FAILED,gpu-utilization.jsonl. File rỗng được liệt kê trong PUBLICATION.json và không gửi qua sink, file thiếu cũng được ghi rõ. Không có model/token hoặc dữ liệu target trong danh sách tự chọn. Metadata được copy sang tranche snapshot mới theo digest nội dung, inventory SHA và PUBLICATION đi cùng. Giữ nguyên operation gốc. Retry cùng snapshot idempotent, nếu COMPLETE/FAILED bổ sung về sau thì tạo snapshot khác, tránh sửa immutable Drive plan.

Nếu function bị provider kill trước khi ghi COMPLETE/FAILED, finalizer từ chối operation chưa đóng. Root cần xác minh function đã dừng, lưu hồ sơ failure riêng rồi dùng CPU recovery được review. Không tự thêm marker để hợp thức hóa operation đang chạy.

## Telemetry GPU

GPU `_run` dùng Popen riêng cho numerical child. Parent lấy `nvidia-smi` utilization.gpu,memory.used,memory.total khoảng mỗi giây, ghi JSONL trên Volume gồm seconds,gpu_utilization,vram_used_mib,vram_total_mib. Dữ liệu bao gồm cả setup trong child, không chỉ lúc kernel chạy. Kết hợp timings core/setup/publish/commit để phân biệt GPU chờ host với inference thật. Không đặt tỷ lệ utilization mong muốn làm kết quả đã đạt.

Monitor timeout270s trong function300s, mỗi query timeout5s. Nếu query hỏng, sample sai, child lỗi hoặc timeout thì dừng. `finally` terminate→wait5s→kill→wait5s khi cần, có xử lý race child vừa thoát. Không có Drive Secret hoặc upload trong GPU function. Volume commit sau lỗi giữ log/telemetry để CPU finalizer gửi sau khi GPU đã trả.

## Kiểm chứng và giới hạn

`TESTS10.txt` giữ lượt kiểm cuối. Các ca mới kiểm hai attempt không ghi đè hoặc thay request GPU, normalization producer/consumer, metadata failure/empty log/unknown files, publication idempotent và phiên bản mới, monitor sample/timeout/query-error/kill bằng process giả. Không khởi chạy process GPU thực. Vì vậy chưa có số đo utilization, tốc độ hoặc bằng chứng cleanup provider thực từ lượt code này. Root cần image preflight mới và nghiệm thu lần chạy actual sau khi đóng SHA scripts.

Wrapper chưa tự resume fit đang dở. Retry CPU chạy lại join/fit từ numeric đã lưu bằng tranche mới, có thể tốn thêm CPU. Với raw đã đủ và muốn giảm việc lặp, root vẫn có thể gọi fit_volume_calibration riêng sau kiểm pin. Không tự chọn checkpoint hoặc thay tham số V1.
