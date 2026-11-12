# Kiểm mức sử dụng GPU của AKT ngày 12/11/2026

## Kết luận hiện tại

Cách gọi trước đây rằng GPU đã được tối ưu là quá sớm. Cache, dự báo theo batch và phục hồi checkpoint đã có kiểm kỹ thuật. Mức khai thác GPU trong training chính cần được đo riêng. Đợt đo này xác nhận cấu hình batch4 còn dư VRAM và còn thời gian GPU không chạy kernel. Chưa xác định nguyên nhân nghẽn hoặc chứng minh chi phí thấp nhất để đạt chất lượng yêu cầu.

## Quan sát trực tiếp trong training

Lấy 30 mẫu cách nhau khoảng hai giây, từ 18 giờ 52 phút 30 giây đến 18 giờ 53 phút 29 giây ngày 12/11. Cùng process, cùng epoch5 của execution06, không chuyển sang validation hoặc đóng gói trong khoảng đo.

| Đại lượng | Giá trị đo |
|---|---|
| GPU | NVIDIA T4 |
| GPU-Util trung bình | 43,9%, thấp nhất39%, cao nhất49% |
| VRAM cấp cho context | 459/15.360MiB, khoảng2,99% |
| Điện năng trung bình | 50,95W, giới hạn70W |
| CPU process training | Trung bình tương đương1,28core |
| RAM thường trú process training | Trung bình4,34GiB |
| Tiến độ giữa hai mốc ghi nhận | 2.100 bước optimizer, 496.651target |
| Thông lượng giữa hai mốc | 8.519target/giây trong58,30giây |
| Padding trong phần cửa sổ vừa xử lý | 42,50% số token |

GPU-Util phản ánh phần thời gian có kernel đang thực thi. Chỉ số này chưa mô tả mức sử dụng FLOPS hoặc mức chiếm dụng từng SM. VRAM được cấp và mức hoạt động bộ nhớ là hai đại lượng khác nhau. [Định nghĩa NVIDIA](https://nvidia.custhelp.com/app/answers/detail/a_id/3751/~/useful-nvidia-smi-queries).

Đây là một khoảng quan sát gần một phút. Số CPU/RAM thuộc process training, chưa phải toàn container. Chưa đọc được cgroup quota. Chưa đo toàn epoch hoặc chi phí để đạt cùng chất lượng dự báo.

## Phân biệt các pha thực thi

Mẫu cuối execution04 gồm bốn thời điểm còn worker và26thời điểm worker đã kết thúc, GPU về0% khi đóng gói. Gộp các mẫu này sẽ làm sai trung bình mức sử dụng trong training. Giữ nguyên cả hai bộ log để kiểm chứng.

Batch lớn hơn đã cho thông lượng cao hơn trong benchmark trước, nhưng số bước Adam mỗi epoch cũng thay đổi. Chưa có bằng chứng thời gian đạt cùng chất lượng hoặc tổng chi phí thấp hơn. Cấu hình chính hiện hành tiếp tục batch4 với cùng checkpoint. Các giả thuyết cần kiểm tiếp gồm chi phí đồng bộ CPU–GPU, nhiều kernel nhỏ và kích thước batch. Tăng GPU-Util đơn thuần chưa đủ làm tiêu chí chọn cấu hình.

## Phục hồi lỗi startup

Execution05 hết35giây khi kiểm runtime, trước mọi bước training. Archive lỗi đã tải về và kiểm inventory, App đã dừng. Giữ bản worker cũ, tăng riêng thời gian chờ kiểm runtime lên120giây, kiểm AST xác nhận phần khác giữ nguyên. Execution06 tiếp tục từ checkpoint đã kiểm của execution04 tại epoch5 bước39.488. Khoảng đo trên xác nhận training đã tiến đến bước43.800. Chưa xác định nguyên nhân sâu hơn của sự chậm startup.

## Tiến độ mô hình đã đối chiếu

Execution04 đã hoàn tất epoch4. Log Loss selection lần lượt là0,359648,0,356651,0,355651 và0,356488. Epoch4 kém epoch3. Checkpoint tốt nhất tạm thời ở epoch3. Chưa chốt epoch cuối, refit, calibration hoặc đánh giá độc lập.

## Bằng chứng và cách dựng lại

Các file nằm trong [bundle A0 đang mở](../runs/junyi-main-selected-20261112-01/README.md).

- `gpu-telemetry06.log` giữ mẫu nvidia-smi, process và tiến độ gốc.
- `gpu-telemetry06-data.csv` giữ dữ liệu dạng bảng.
- `gpu-telemetry06-summary.json` giữ thống kê và giới hạn.
- `collect_gpu_telemetry06.py` và `observe_stable_gpu06.py` giữ cách lấy mẫu trên container hiện có.
- `summarize_gpu_telemetry.py` dựng lại CSV và JSON bằng Python trong `.venv`, không cần Torch.
- `gpu-telemetry04.log` giữ pha chuyển từ training sang đóng gói.
- `execution04-verification.json` và `verify_execution04.py` kiểm archive và bốn epoch.
- `runtime-timeout05-remediation.json` giữ đối chiếu sửa startup cùng nguồn checkpoint.

Việc quan sát dùng container training đang chạy. Không cấp thêm GPU cho bộ lấy mẫu. Đợt đo không tăng bằng chứng trả lời RQ hoặc xác lập mô hình cuối cùng.
