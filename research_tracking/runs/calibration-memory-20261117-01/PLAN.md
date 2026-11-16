# Đo tài nguyên fitter V1 trước quyết định tối ưu

Ngày 17/11/2026. Root giao đo tổng hợp để thay ước lượng RAM chưa đo. Hướng triển khai hiện hành dùng cloudCPU cho full calibration, PC chỉ chạy các probes nhỏ.

## Thiết kế

Chạy tuần tự ba process độc lập với25.000,50.000,100.000CalibrationTarget. Mỗi target có event ID riêng, prehistory SHA64ký tự riêng, learner ID10ký tự với100event/learner và item ID tổng hợp dài28ký tự. Giữ cả list targets và list expected keys như producer V1, gọi đúng `fit_temperature` với4objective evaluations. Dữ liệu xác suất/nhãn đều dựng xác định, không lấy Junyi hoặc model thật.

Mỗi process có watchdog RSS640MiB/120giây, lấy mẫu10ms, dùng thêm peak working set OS nếu được trả. Đây là cap được giám sát, không là kernel hard limit. Controller chừa thêm128MiB ngoài cap khi xét RAM trước từng lượt. Không chạy cùng probe native model khi RAM thấp. Parent có timeout dự phòng và chỉ dừng cây process do chính nó tạo.

## Đo và diễn giải

Ghi baseline sau import, RSS sau dựng inputs, peak/end RSS, thời gian import/dựng targets/fit, objective count và digest. Peak bao gồm các key tuples, sorting, asdict, JSON và logits bên trong V1. Cấu trúc này gần footprint fitter nhưng chưa có reader Parquet, model hoặc full producer population.

Dùng chênh lệch peak giữa các cỡ mẫu để ước lượng slopebyte/target và baseline, ngoại suy tới1.621.484targets chỉ làm dự toán. Nêu giới hạn do độ dài identifier, allocator và IO/payload khác, không gọi đó là benchmark full cohort. Budget4evaluation giữ phạm vi phép đo tài nguyên, chưa đo toàn runtime max200evaluation.

Nếu bằng chứng cho thấy cloudCPU có thể dùng V1 trong trần RAM rõ ràng, ưu tiên giữ V1. Chỉ triển khai fitter bounded mới ở module riêng sau đo, và cần parity vềtemperature/loss/digest/counts/error cases. Không sửa `response_calibration.py` hoặc producer/source đang đóng băng của nhánh GPU.

## Output

Script `benchmark_v1.py`, mỗi lượtJSON/log nhỏ và `BENCHMARK.json` trong bundle này. Chưa ghi file model/checkpoint/calibration thật. Không dùng GPU, cloud hoặc fullJunyi fit trong phép đo.
