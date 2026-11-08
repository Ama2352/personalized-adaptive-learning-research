# Controller reference V1: công cụ đo quyết định đã kiểm local

**Phạm vi:** engineering cho RQ1–RQ3, không kết quả về hiệu quả graph. Theo [protocol đã chọn](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), không sửa selector hoặc kết quả Paper2 lịch sử.

## Đã cài đặt và kiểm chứng

[`reference_controller.py`](../../src/knowledge_tracing/reference_controller.py) nhận reference correctness đã calibrate từ cùng prehistory, dùng ngưỡng0,5637150147511514; giữ readiness/exposure6, anti-drill3/spaced-review escape, balanced set và chapter tie. Item chọn gần expected success0,70; tie theo ít dùng rồi ID, tolerance probability-distance1e-12 được ghi rõ. Trace lưu graph/chapter/state/prehistory/calibration identities, M/R/C/B, keys và action. Served probability đểnull vì phải predict bằng ticket riêng sau selection.

`select_from_reference_snapshot` nối output calibration/reference vào controller; yêu cầu đủ28concept và84item support từ producer. Hàm kernel còn cho phép graph nhỏ để kiểm cơ chế; không tự xác nhận graph là expert hay dict snapshot đến từ fitted model. Missing/null/nonfinite, history/bank mismatch, inconsistent means, cyclic graph, sai bookkeeping hoặc recent/count/chapter mâu thuẫn đều bị từ chối.

**Final trial05:36 PASS**, gồm24 kiểm controller và12 kiểm bridge có sẵn; log pytest0,27s. Không fit model, không môi trường tương tác, không mở Junyi/Holdout, không network/cloud. [Bundle14outputs](../runs/reference-controller-engineering-20261108-01/README.md), [manifest](../runs/reference-controller-engineering-20261108-01/manifest.json), SHA `78debea6db6cbc006a10249f3338b983a5bc7b9a8c173ff722af4b78f9c4016c`. Giữ năm trials; chỉ trial05 gắn source cuối, không gán source cuối cho intermediate trials.

Review độc lập phát hiện sai tie do float quanh0,60/0,80 và hạn chế state phục hồi. Đã sửa nearest-pool, thêm regression đối xứng, kiểm recent/count/chapter và hai negative cases. Các kiểm còn xác nhận: đổi P không đổi action, threshold crossing đổi ready/action, và escape có thể chọn ngoài raw-ready. Đây là tính năng đo cần cho RQ1, **không phải bằng chứng tần suất xảy ra trên nghiên cứu thật**.

## Phần chưa hoàn tất

Outer runner còn phải giữ G_controller expert cố định giữa model conditions, tạo snapshot bằng đúng fitted checkpoint/calibrator/partition, predict served item trước interact/observe, commit state đúng sau interaction hoặc dừng khi lỗi. Không suy hợp lệ provenance từ hash do caller tự khai. Cần corpus thật theo role80/10/10, selected refit90, calibration10 và mô hình research-fitted trước controlled closed-loop; kết quả thử tổng hợp này không hoàn tất S04/S05 hoặc RQ.
