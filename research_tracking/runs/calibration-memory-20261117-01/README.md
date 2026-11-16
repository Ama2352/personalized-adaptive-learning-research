# RAM fitter V1 — đo tổng hợp và quyết định triển khai

Ngày 17/11/2026. Đã đo ba cỡ mẫu tổng hợp bằng đúng `response_calibration.fit_temperature` hiện hành. Chưa fit Junyi hoặc dùng model/GPU/cloud trong lượt đo.

## Kết quả đo

| Targets tổng hợp | Peak RSS | Thời gian gọi fit | Tổng thời gian worker | Objective evaluations |
|---|---:|---:|---:|---:|
| 25.000 | 58,26 MiB | 2,42 giây | 4,94 giây | 4 |
| 50.000 | 92,69 MiB | 2,60 giây | 6,40 giây | 4 |
| 100.000 | 159,83 MiB | 4,51 giây | 10,86 giây | 4 |

Mỗi cỡ chạy ở process mới, tuần tự, có cap RSS512MiB và120giây. Cap được hạ từ mức tối đa640MiB cho phép do máy thiếu RAM. Controller kiểm RAM trước mỗi lượt và chừa128MiB ngoài cap. Mẫu có event ID và history SHA riêng cho từng target, giữ list targets cùng list expected keys như caller V1. Object learner/item được chia sẻ theo cấu trúc tổng hợp đã khai báo. Watchdog lấy mẫu10ms, peak working set OS cũng được lấy khi có. Đây là kiểm tài nguyên được giám sát, không là kernel hard limit.

Lượt admission đầu thấy khoảng487MiB trống, đã dừng trước khi tạo child. `BENCHMARK.json` và `V1_025000_ADMISSION.json` giữ lượt này. Khi RAM đủ hơn, `BENCHMARK02.json` hoàn tất ba cỡ mẫu. Không xóa log deferred hoặc ghi đè kết quả trước.

## Ngoại suy có giới hạn

Hồi quy tuyến tính trên ba peak cho độ dốc khoảng1.418byte/target và baseline khoảng25,9MB. Với1.621.484targets của calibration thật, điểm ngoại suy là khoảng2,17GiB cho footprint fitter theo cấu trúc mẫu. Đây chưa là peak đo trên full cohort và chưa gồm reader Parquet, vật liệu population của producer, allocator khác hoặc khả năng chia sẻ identifier khác.

Ước lượng cũ4KiB/target tương ứng khoảng6,19GiB. Với điều kiện chỉ dùng60%RAM available trong guard hiện hành, nó đòi hơn10,30GiB available. Phép đo cho thấy đó là heuristic bảo thủ hơn footprint mẫu, không phải yêu cầu RAM đã đo của phương pháp.

Max4objective evaluations chỉ phục vụ benchmark tài nguyên. Quy trình khoa học vẫn giữ budget/điều kiện dừng V1. Chưa đo runtime full200evaluation, chưa suy thời gian hoàn tất calibration thật từ cột thời gian trên.

## Quyết định đã thống nhất với root

Giữ fitter V1 và optimization hiện hành. Root chọn cloudCPU12GiB/1core cho lượt thực đầu, kèm watchdog RSS/time và ghi peak thực tế. Cấp RAM này là quyết định vận hành cho lượt đầu và guard hiện có, không phải giới hạn cứng của mô hình hay yêu cầu rằng mọi lượt luôn cần12GiB.

Theo yêu cầu cloud-first mới, full calibration chạy trên cloudCPU, đầu ra lớn giữ Drive làm nơi lưu chính. PC chỉ chạy probes tổng hợp nhỏ. Không triển khai thêm optimizer hoặc backend bounded mới khi chưa có nhu cầu thực tế vượt trần cloudCPU đã chọn. Lựa chọn này giảm rủi ro sai khác số học/provenance do viết lại fitter và giữ shared source đang đóng băng cho producer.

Trên cloud, guard dùng `psutil.virtual_memory().available` cần được đọc cùng trần RAM đã khai báo của function và watchdog RSS. Giá trị available không tự thay cho trần bộ nhớ của process/function. Lượt full phải đo RSS của toàn CPU worker gồm reader và upload, giữ timeout để giới hạn chi phí.

## Tái kiểm và provenance

- `benchmark_v1.py` là source chạy thực tế, không nạp Torch hoặc dataset thật.
- `V1_*.json` và `V1_*.txt` giữ số đo từng worker. `BENCHMARK02.json` giữ admission và thứ tự ba lượt.
- `EXTRAPOLATION.json` giữ công thức/slope/intercept cùng giới hạn, không là confidence interval.
- `SOURCE_PINS.json` ghi SHA shared source và worker sau đo. Source V1 được giữ freeze qua phối hợp nhánh, các shared file kiểm bằng git diff sạch. Worker chưa có hash trước/sau riêng trong phép đo, nên không khai báo phép kiểm đó đã chạy.
- `ACCEPTANCE.json` xác nhận các lượt đều dưới cap và không có full Junyi fit hoặc cloud call.

Các JSON digest là bằng chứng dữ liệu tổng hợp. Nhiệt độ hoặc loss của mẫu này không được dùng để chọn model, chọn cấu hình hoặc trình bày như kết quả RQ3.
