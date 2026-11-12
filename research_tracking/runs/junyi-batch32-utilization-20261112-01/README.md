# Batch32 trên T4 — đo tài nguyên trực tiếp ngày12/11

## Kết quả đã nghiệm thu

Một T4 đã hoàn tất kiểm kỹ thuật. Có115mẫu nvidia-smi trong khoảng64,98giây training ổn định, sau lượt làm nóng.

| Đại lượng | Kết quả |
|---|---|
| GPU-Util | Trung bình87,51%, min76%, max90% |
| VRAM theo nvidia-smi | 1.541/15.360MiB, khoảng10,03% |
| Công suất GPU | Trung bình67,724W |
| Xung SM | Trung bình1.477MHz |
| Thông lượng sau làm nóng | 19.792,43target/giây |
| CUDA tensor peak allocated | 1.301,38MiB |
| Worker / remote cả đóng gói | 81,74 /85,06giây |
| Checkpoint nạp lại và cập nhật tiếp | Model, Adam, RNG, metric và dự báo khớp chính xác |

Đạt mục tiêu GPU-Util trên50% trong khoảng đo. Chưa đánh giá chất lượng selection hoặc thời gian đạt cùng chất lượng trên toàn Junyi. Main A0 source04/batch4 được giữ nguyên.

## Workload và giới hạn

Tái sử dụng đúng packet đã được phép chuyển, gồm755learner TRAIN80,1.024window,56.332target duy nhất và100.032token hợp lệ. Lặp24lượt packet để có khoảng quan sát ổn định. Tổng1.351.968lượt target/768updates cho phần đo. Kiểm resume thêm2updates, tổng770updates/1.354.738lượt target, dưới trần1.358.368đã định. Các lượt packet không đại diện24epoch toàn Junyi.

Giữ source04, encoding717exercise, FP32, seed42, Adam và các kiểm target/mask. Config nghiên cứu tham chiếu batch4, trường actual_benchmark_batch_size ghi32. Đây là sử dụng primitive training để kiểm phần cứng, chưa tiếp nhận cấu hình nghiên cứu mới. Loss trên packet lặp chỉ xác nhận hữu hạn và khả năng tối ưu kỹ thuật. Không suy thành cải thiện dự báo độc lập.

## Ngân sách và dừng

Người dùng duyệt lượt test tiết kiệm, hạn mức0,10USD nằm trong trần30USD toàn KLTN. Một GPU, deadline client400giây, timeout function420giây và không retry. Cận tính T4/2core/8GiB trong420giây khoảng0,0874USD. App đã dừng, snapshot `containers-after.json` rỗng.

Snapshot sau lượt ghi metered3,23858233USD, credits3,23USD, billed0USD. So snapshot ngay trước lượt, tổng tăng khoảng0,02USD. Đây là delta giữa các snapshot, có thể có điều chỉnh từ nhà cung cấp. Giữ `billing-after.json` và billing-before ở native output. API có điều chỉnh giảm tổng trước lượt so snapshot cũ20giờ07 nên không lấy hiệu giữa hai snapshot khác đợt làm chi phí riêng lượt này.

## Truy cập trên web Modal

[App của lượt đo](https://modal.com/apps/honguyenminhsang2005/main/ap-WxcyTqtF4fNfQRj62Yxh1N), function `remote_probe`, container `ta-01M780C6MSQZJSCA3S8S7QX4JR`. Chọn khoảng20giờ50–20giờ53 ngày12/11, giờ Việt Nam. Modal cung cấp biểu đồ GPU, GPU memory, CPU và RAM ở dashboard function/container. [Tài liệu GPU Metrics](https://modal.com/docs/guide/gpu-metrics).

## Artifact và dựng lại

- Native output ở `experiments/akt/results/modal-junyi-batch-utilization-t4-20261112-01/`. Archive26.173.953byte đã kiểm SHA/CRC/inventory. Checkpoint ở member `checkpoints/batch-032/state.pt`, đồng thời được giữ tại Volume `kltn-akt-modal-junyi-batch-utilization-t4-20261112-01`.
- `gpu_worker.py`, `request.json` và `reservation.json` giữ code, nguồn pin và giới hạn thực chạy. Controller hiện có là `experiments/akt/modal_junyi_batch_probe.py`. File đầu vào được mount lúc startup theo API Modal, giữ kiểm SHA phía remote.
- `analyze.py` đọc archive, đối chiếu resume, dựng `usage-summary.json` và `resource-data.csv`. Dùng Python trong `.venv`.
- `gpu-telemetry.jsonl` giữ mẫu gốc. `build_figure.py` dựng `gpu-usage.svg`, PDF và PNG. Phong cách tiếp tục quy ước figures4papers của các bundle trước.
- `live-observer.log` và `live-resources.jsonl` giữ lần lấy CPU/RAM trực tiếp bị lỡ vì task đã kết thúc. Không có số CPU/RAM process đáng tin cậy cho lượt này. `provider-metrics-query.log` giữ lỗi lookup function ephemeral khi thử lấy lại số liệu qua CLI. Hai thất bại này tách khỏi telemetry GPU trong worker đã lưu đầy đủ.

So tốc độ với batch4 cũ là tham khảo lịch sử, khác thời điểm và số lượt packet, chưa phải đối chứng đồng thời. Lựa chọn GPU mạnh hơn cần đo cùng workload và tính cả CPU/RAM, startup, checkpoint. Chưa chạy L4 hoặc H100 trong bundle này.
