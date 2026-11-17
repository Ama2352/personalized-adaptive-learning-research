# Tài nguyên bốn lượt suy luận calibration

Mỗi phiên bản A0–A3 xử lý cùng 1.621.484 target và 28.653 window calibration, không có target OOV. Telemetry A1/A2/A3 được lấy riêng từ Drive sau khi đối chiếu SHA/byte/parent với publication đã nghiệm thu. Tổng tải thêm 12.837 byte. A0 telemetry gốc giữ nguyên.

| Phiên bản | GPU worker, giây | Mẫu NVML | GPU trung bình mẫu | GPU cao nhất | VRAM cao nhất, MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| A0 | 57,913 | 55 | 6,236% | 43% | 1.835 |
| A1 | 42,056 | 39 | 10,026% | 34% | 1.835 |
| A2 | 41,881 | 40 | 8,650% | 33% | 1.836 |
| A3 | 47,978 | 45 | 8,667% | 24% | 1.835 |

Tổng thời gian outer GPU worker là khoảng 189,828 giây, tương đương 3,164 phút. Con số này chưa cộng CPU preparation, truyền dữ liệu, startup hoặc quy tắc tính phí. Nguồn thời gian là trường worker_seconds ngoài cùng trong A<i>_GPU_RESULT01.json. Các trường numeric_worker_seconds và thời gian quan sát telemetry được giữ riêng trong CSV.

GPU trung bình là trung bình số học các mẫu NVML lấy gần mỗi giây, bao gồm nạp model và I/O trong khoảng được đo. Mức sử dụng còn thấp. Không thể dùng số liệu này để tuyên bố đã tận dụng GPU trên 50%. Mỗi model có một lượt trên H100, chưa có benchmark lặp kiểm soát để kết luận khác biệt tốc độ do kiến trúc. Các lượt này là suy luận calibration, không phải training thêm hoặc đánh giá độc lập.

## Figure và cách dựng

`GPU_USAGE_COMPARISON01.svg` là figure độc lập, PNG giữ bản kiểm bố cục. Cả ba biểu đồ dùng `GPU_USAGE_COMPARISON01.csv`, nguồn từ telemetry gốc cùng metadata/result đã ghim. Đã xem PNG và kiểm nhãn không chồng nhau. `GPU_USAGE_ACCEPTANCE01.json` giữ source/output SHA và số liệu từng phiên bản.

`build_gpu_usage_figure01.py` dùng Matplotlib và đặt cache font tại artifacts/akt/runtime/figure-cache trên D. Script kiểm tất cả source pins trước khi dựng. Các output dùng chế độ tạo mới, không ghi đè artifact đã có. Khi dựng bản figure khác, đổi tên phiên bản trong bản sao source để giữ bản gốc.

```powershell
.\.venv\Scripts\python.exe -B research_tracking/runs/junyi-calibration-real-20261117-01/build_gpu_usage_figure01.py
```

`fetch_gpu_telemetry01.py` chỉ cho phép A1/A2/A3 và tối đa 16 KiB/file. Script đọc OAuth local đã được duyệt, kiểm đúng tài khoản Sang, pin metadata và content, không tải model hoặc prediction. Mã không in token hay nội dung ngoại lệ mạng.
