# Kiểm CUDA hiện hành của bốn biến thể AKT — 10/11/2026

## Đã nghiệm thu

Đã xác nhận T4 miễn phí và thực thi mã A0–A3 trên CUDA. Đây là smoke kỹ thuật trên dữ liệu dựng sẵn, chưa là kết quả nghiên cứu fitted hoặc bằng chứng cải thiện học tập. Modal sử dụng 0 USD.

| Hạng mục | Kết quả |
|---|---|
| GPU | Tesla T4, 15.360 MiB theo nvidia-smi, driver 580.82.07 |
| Runtime | Python 3.13.16, Torch 2.7.1+cu126, venv không kế thừa package hệ thống |
| Dependencies | 44 wheel khớp lock/URL/SHA, base pip trước–sau nguyên |
| A0 | Không đồ thị, 2 Adam updates, 48 target giả, 6 dự báo |
| A1 | Đồ thị cố định, 2 Adam updates, 48 target giả, 6 dự báo |
| A2 | Confidence dựng sẵn, 2 Adam updates, 48 target giả, 6 dự báo |
| A3 | Confidence và gate, 2 Adam updates, 48 target giả, 6 dự báo |
| Tổng | 8 updates, 192 target exposures, 24 dự báo |
| Thời gian | Worker 8,636 giây, watchdog bao ngoài 9,464 giây |
| Peak allocator | 104.003.072 byte lũy kế, dưới cap 2 GiB |

Backbone khởi tạo cùng SHA cho cả bốn biến thể. Trọng số backbone thực sự thay đổi sau cập nhật. Loss, tham số, Adam state và dự báo đều hữu hạn. Chế độ CUDA tuân thủ recipe28 FP32, seed42, deterministic, tắt TF32, explicit Adam foreach=False/fused=False. Kích thước mô hình giữ 256d/8heads/1block; chuỗi fixture chỉ dài sáu tương tác. Không suy VRAM hoặc throughput corpus chính từ số đo này.

## Diễn tiến và lỗi đã giữ

1. Người dùng chuyển runtime sang T4 và xác nhận MCP. `device-discovery.json` xác nhận thiết bị, Python và root trống. Runtime CPU trước đã được tải về đầy đủ trong bundle riêng.
2. Chuyển lại cùng 279 thành viên nguồn, kiểm từng phần và SHA/CRC trước giải nén. Không chuyển Junyi, credentials hoặc checkpoint lịch sử.
3. Lượt cài đầu dừng trước pip vì helper còn ghim Python 3.13.18 của runtime CPU, trong khi T4 dùng 3.13.16. `setup-attempt01-diagnostic.json` và `remote/install01-error.log` giữ lỗi thực tế.
4. Lượt hai chỉ chỉnh pin nhận diện Python sang 3.13.16 và dùng output/input riêng. Giữ lock 44 wheel cùng toàn bộ model recipe và resource caps. Venv vẫn rỗng trước cài, package hệ thống không đổi. Cài thành công trong 173,916 giây.
5. Chạy `cuda_smoke.py` qua watchdog tối đa 180 giây. Mỗi biến thể giới hạn hai updates, không tự nối sang Main. Kết quả đã tải về và kiểm độc lập.

Helper và installer được nhúng sau chuẩn hóa xuống dòng LF. `attempt02-inputs.json` ghim byte payload thực sự chuyển. Mã mô hình và tests giữ byte theo manifest source, không áp dụng phép biến đổi helper lên mã model. Confidence của fixture được dựng sẵn, không giả thành artifact Method24 đã fit.

## Tìm bằng chứng

- `cuda_smoke.py`, `smoke_watchdog.py`, `smoke_launch.py` mô tả workload và giới hạn đã chạy. Source inventory của model được kiểm trước–sau; launcher kiểm toàn bộ source kit trước chạy.
- `remote/smoke-result.json` giữ loss, bước cập nhật, initial/final backbone hashes, alpha/gate và 24 xác suất dự báo. `remote/smoke-worker.log` và `remote/watchdog-result.json` giữ log cùng trạng thái tiến trình.
- `remote/install02-result.json` và `remote/origins.stdout` giữ package origins và các giới hạn thực tế. Lượt đầu được giữ riêng.
- `experiments/akt/results/colab-t4-current-20261110-01/logs.zip` giữ trọn 41 thành viên bằng chứng, gồm pip report và log hai lượt cài. `archive-inventory.json`, `export-metadata.json` và `verification.json` nối SHA/CRC với archive đã nhận.
- `receive_verify.py` kiểm độc lập archive, 44 wheel identities, nguồn hiện hành, tám updates, 192 targets, 24 dự báo và SHA của worker được khởi chạy. Không import Torch trên máy local.

## Phần còn thiếu

Smoke này không lưu checkpoint mô hình. Cần nghiệm thu checkpoint/optimizer/RNG/counters và restore bằng pipeline nghiên cứu hiện hành trên CUDA, sau đó complete lifecycle, xuất dự báo có danh tính target, benchmark đại diện và lập allocation riêng cho training chính. Chưa chứng minh khả năng phục hồi lỗi bất ngờ, durability Modal Volume, Main matrix hoặc hiệu quả CG-AKT. CPU Gate 1.993 ca thuộc profile Linux CPU đã lưu riêng, không được gộp thành 1.993 ca CUDA.

Ưu tiên tiếp tục A0–A3 và phép so sánh cốt lõi. Không mở rộng demo, simulator hoặc quét cấu hình rộng trong gói này.
