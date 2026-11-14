# Kiểm thực tế ranh giới CPU–GPU và cache A2/A3 trên T4 — 14/11/2026

## Mục tiêu và phạm vi

Chuẩn bị cache đồ thị và selection trên CPU local trước khi thuê GPU, sau đó kiểm tính tương đương và phục hồi checkpoint trên T4 miễn phí qua MCP. Đây là kiểm kỹ thuật, chưa phải kết quả nghiên cứu trả lời RQ3. Confidence dùng fixture cố định để kích hoạt các nhánh tính toán, chưa phải confidence fit từ TRAIN80.

## Diễn tiến đã xác nhận

1. CPU local tạo bốn cache A2/A3 train/selection trong 13,305 giây trên cohort kỹ thuật đã được duyệt chuyển lên Colab. Cohort gồm 256 cửa sổ train và 88 cửa sổ selection, không có Holdout/calibration.
2. Source mới nối cache selection và admission CPU vào luồng staged. GPU dispatch bị chặn nếu thiếu một trong năm đầu vào cache/admission. Selection SQLite có chỉ mục thứ tự được tạo trên CPU. Byte SHA và định danh dữ liệu vẫn được kiểm khi nhận cache.
3. Colab MCP kết nối qua Edge. Môi trường Python cô lập ở project `.venv`, Torch 2.7.1+cu126, Tesla T4 15 GiB. Không cài package vào Python global. Khóa môi trường ở `runtime-lock-pin.json`.
4. Lượt 01 kiểm A2 cached/direct khớp nhưng dừng ở so sánh optimizer sau resume. Bộ đếm Adam được map sang CUDA khi đọc checkpoint. Nhánh Adam non-capturable/non-fused của PyTorch giữ nguyên thiết bị bộ đếm khi load. Model weights sau resume đã khớp. Giữ nguyên lỗi và output lượt 01.
5. Sửa restore để đưa riêng bộ đếm Adam/AdamW non-capturable/non-fused về CPU, giữ momentum và các chế độ fused/capturable. Bộ kiểm cuối local đạt 102 ca, 0 lỗi, 0 skip trong 49,747 giây. Xem `tests06.log` và `tests06.xml`. Bộ hợp đồng cache mở rộng sau đó đạt 39 ca, gồm 10 ca mới; xem `tests07.log/xml`.
6. Lượt 02 chạy source delta đã ghim, tái dùng cache CPU bất biến. A2/A3 đều khớp loss, dự đoán, gradient, cập nhật model/Adam. Sai lệch xác suất lớn nhất bằng 0. Resume khớp model/optimizer và tổng 14.270 target, 2 bước optimizer cho mỗi biến thể. Supervisor xác nhận process thoát mã 0 sau 95,493 giây. Xem `attempt02-status.json` và `source-delta02.json`.

## Hiệu năng đo được và giới hạn

Mỗi ô thời gian cộng hai block AB/BA, mỗi block đo 4 bước sau warmup, batch 128 và FP32. Mỗi chế độ xử lý 61.024 target. Thời gian GPU được đồng bộ trước/sau đoạn đo.

| Biến thể | Tính trực tiếp | Cache CPU chuẩn bị sẵn | Diễn giải |
|---|---|---|---|
| A2 | 3,5995 giây | 3,4304 giây | Giảm khoảng 4,7% trên mẫu này |
| A3 | 3,4646 giây | 3,4667 giây | Chênh khoảng 0,06%, gần như ngang nhau |

Lượt 01 cho mức tăng tốc A2 lớn hơn nhưng không hoàn tất resume. Giữ số liệu lượt 01 riêng. Hai block ngắn còn dao động nên chưa suy rộng thành thời gian toàn epoch hoặc mức tiết kiệm H100.

Đỉnh VRAM allocated khoảng 4,70 GiB, reserved khoảng 4,94 GiB. Mẫu nvidia-smi cách khoảng 1 giây bao gồm setup/warmup trong mỗi phase. Trung bình phase A2 cached 32,3%, A3 cached 43,1%, không phải mức sử dụng riêng các bước được bấm giờ. Chưa xác nhận mục tiêu GPU trên 50% hay triệt tiêu thời gian chờ CPU.

## Bằng chứng và cách kiểm lại

- `attempt01-status.json`, `attempt02-status.json` giữ kết quả và telemetry gốc.
- `remote-setup.py`, `remote-materialize.py`, `remote-probe-supervisor.py`, `remote-probe02-supervisor.py` giữ lệnh thực thi đã dùng.
- `transfer-inventory-before.json`, `upload-plan.json`, `mcp-verified-progress.json` giữ inventory truyền vào. Không chứa token.
- `source-delta02.json` ghi SHA trước/sau sửa checkpoint và probe.
- Đã nhận 45 file, gồm 12 checkpoint, về `experiments/akt/results/gpu-boundary-t4-20261114-01/`, `experiments/akt/results/gpu-boundary-t4-20261114-02/` và hồ sơ vận chuyển cùng vùng results. `download-verification.json` đối chiếu SHA từng file. T4 trả `RELEASE_ACCEPTED`, chưa kiểm độc lập cloud list; xem `runtime-release.json`.
- Entry point tái dựng là `scripts/akt/probe_junyi_gpu_boundary.py`, dùng `--prepare-only` cho CPU rồi `--prepared-receipts` và `--cache-id` cho lượt GPU. Cần runtime/source/data đúng inventory và output mới, không ghi đè lượt cũ.

## Việc còn thiếu trước training chính

Confidence TRAIN80 thật còn chưa hoàn tất. Cần cache đầy đủ từ confidence đó, Gate Linux của source cuối và xác minh stop barrier trên Modal thật. Đọc batch, chuyển tensor, kiểm danh tính và checkpoint vẫn có phần CPU trong function GPU. Phải dự toán từ đo toàn lifecycle, không lấy phép đo bốn bước làm thời gian epoch. A0 lịch sử validation batch 1, mới replay checkpoint 9 batch 128, giới hạn so sánh vẫn giữ.

Đợt này dùng Colab T4 miễn phí, chi Modal bằng 0 USD. Các checkpoint ở đây là model kiểm kỹ thuật, không thay model nghiên cứu A0/A1.

## Lưu ý vận hành MCP

Đợt truyền chunk 1 MiB bị timeout và ngắt cầu nối. Sau kết nối lại qua Edge, Colab vẫn giữ archive và runtime cũ. Đã chuyển sang 537 chunk tối đa 200.000 byte, kiểm SHA từng chunk và toàn archive 107.242.140 byte, sau đó kiểm CRC ZIP và SHA toàn bộ output. Giữ archive, các phần nhận và receipt trong `artifacts/akt/colab/gpu-boundary-download-20261114-01/`. Chưa dọn file vì còn phục vụ truy vết. Sau nhận đủ mới trả runtime qua MCP.
