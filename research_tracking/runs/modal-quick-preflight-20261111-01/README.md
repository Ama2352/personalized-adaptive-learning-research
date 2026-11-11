# Chẩn đoán và pilot AKT trên Modal — 11–12/11/2026

## Mục đích và phạm vi

Kiểm môi trường CUDA, lưu checkpoint và phục hồi model/Adam/RNG qua tiến trình mới trước huấn luyện nghiên cứu. Người dùng duyệt tổng tối đa 0,50 USD từ free credits. Dữ liệu dựng sẵn, tối đa 16 cập nhật optimizer và 384 lượt target vật lý trong một lượt đủ sáu pha. Chưa có huấn luyện Junyi, Holdout hoặc kết luận hiệu quả CG-AKT từ pilot này.

## Diễn tiến

1. Hai lượt đầu yêu cầu riêng T4/L4 nằm chờ, không có container. Đã dừng và giữ logs. Ảnh gốc `modal-overview-original.png` được giữ nguyên byte, có inventory riêng.
2. Canary CPU chạy được. Hai canary L4 riêng hết thời hạn chờ. Canary cho phép A10/L4/T4 nhận NVIDIA L4 thành công. Chưa xác định được riêng nguyên nhân cấp phát chậm.
3. Lượt 03 lỗi đường dẫn khi Modal mount entrypoint vào `/root`. Đã dừng vòng startup và sửa tính đường dẫn.
4. Lượt 04 thực thi được nhưng còn tham chiếu tệp cài đặt Colab. Archive lỗi đã tải và kiểm đầy đủ.
5. Lượt 05 kiểm runtime CUDA và lock đạt, sau đó bị validator chặn vị trí output. Archive lỗi đã tải và kiểm.
6. Lượt 06 qua validator, bị giới hạn RSS 2 GiB chặn trước batch đầu. Đo được 4.089.319.424 byte trong container 8 GiB. Đã ghi thay đổi giới hạn tiến trình lên 6 GiB, giữ cấu hình model và thuật toán.
7. Lượt 07 dùng giới hạn mới. Trạng thái cuối và kết quả nghiệm thu được lưu trong `current-run.json` và tệp verification khi có kết quả.

Các lỗi chuyển runner từ Colab sang Modal ở bước 3–5 thuộc phần triển khai của agent. Việc sửa chúng chưa tạo bằng chứng trả lời RQ.

## Nguồn và output

- Entrypoint `experiments/akt/modal_checkpoint_pilot.py`.
- Fixture gốc được giữ nguyên trong `research_tracking/runs/akt-t4-checkpoint-recovery-20261110-01/`.
- Gói nguồn từng lượt tại `artifacts/akt/modal/<run-id>/source.zip`, có manifest SHA-256 bên trong. Không chứa dataset Junyi hoặc credentials.
- Archive, checkpoint và execution log tại `experiments/akt/results/<run-id>/`. Không đưa checkpoint lớn vào Git.
- `billing-*.json` là số tổng kỳ tính phí đọc tại thời điểm ghi, có thể cập nhật chậm. Không dùng chúng để suy chính xác chi phí riêng từng App.
- Các probe và log thất bại nhỏ nằm trong bundle hiện tại. `current-run.json` chỉ trạng thái tiếp tục, các hồ sơ cũ giữ lịch sử.

## Điều kiện nghiệm thu

Sáu tiến trình A0/A3 × continuous/interrupted/resumed hoàn tất. So sánh chính xác weights, Adam, RNG, counters, target participation và predictions giữa chạy liên tục với phục hồi cuối epoch. Bốn checkpoint có metadata/COMPLETE và SHA đúng. Archive tải về phải đạt CRC, kích thước và SHA từng thành viên. App phải dừng sau kiểm.

Ngay cả khi đạt, pilot chỉ xác nhận phục hồi cuối epoch trong fixture. Phục hồi sau preemption bất ngờ, sampler/early stopping toàn lifecycle, throughput đại diện và Main fit còn phải kiểm riêng.

## Kết thúc lượt 07

Lượt 07 hết hạn client 600 giây. Lần đọc trạng thái gần cuối ghi 0 container; chưa có receipt hoặc checkpoint tải về. App đã dừng lúc 00:49:46 ngày12/11 giờ Việt Nam. Toàn bộ 11 App thuộc lượt kiểm đã dừng và có 0 tasks tại lần đọc cuối. Bản sửa RSS chưa được nghiệm thu.

API billing lúc 00:50:06 ngày12/11 ghi tổng kỳ 0,02055687 USD, credits áp dụng 0,02 USD, net billed 0 USD. Số tổng có thể cập nhật chậm. Chưa khẳng định chi phí cuối riêng từng lượt. Tổng còn dưới grant0,50USD tại thời điểm đọc.

Bước tiếp theo là chẩn đoán cấp phát cho đúng image/Volume/function hiện hành. Chưa đủ bằng chứng quy nguyên nhân cho quota, payment, Volume hoặc image. Không chạy lặp lại cùng yêu cầu khi chưa có giả thuyết mới.
