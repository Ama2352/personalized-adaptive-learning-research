# A1 Junyi trên H100, batch128 cho train và validation

Ngày 13/11/2026. Bundle đang mở. Mục tiêu là fit A1 expert trên cùng TRAIN80/selection10 của A0, chỉ thêm thông tin đồ thị. Chưa refit, calibration hoặc đánh giá độc lập. Không truy cập Holdout.

## Quyết định thực thi

Người dùng chọn batch128 cho cả train và validation, ưu tiên triển khai A1. Giữ cùng seed42, backbone, vocabulary717, split, optimizer và quy tắc chọn epoch max20/patience3/min_delta0,0001. A1 chọn epoch riêng theo quy tắc đó. Tham chiếu A0 và graph được pin SHA, producer kiểm dữ liệu, cấu hình và khởi tạo trước optimizer, kiểm target population mỗi lần validation.

A0 lịch sử train batch128 nhưng validation từng cửa sổ. Không train lại A0. Chỉ dự đoán lại checkpoint đã chọn epoch9 bằng batch128. Không kiểm lại lựa chọn epoch trên đủ12checkpoint, không khẳng định lịch sử chọn epoch đã được tái lập hoàn toàn.

## Bằng chứng đã đạt

- Linux CPU Gate đạt 2.328 ca, 0 fail/error/skip, nguồn giữ nguyên. Receipt ở `experiments/akt/results/modal-junyi-a1-selected-cpu-20261113-01/receipt.json`. Archive đã tải về D và kiểm inventory. App CPU đã stopped, 0 task.
- `a0-validation-replay03.json` giữ kiểm A0 epoch9 trên H100 với đủ1.600.343selection target/15.847learner, 0OOV. Target population khớp A0. Log Loss batch128 bằng giá trị lịch sử0,35358017683029175 trong độ chính xác lưu, chênh lệch0. Thời gian dự đoán25,11giây. Hash xác suất khác, không tuyên bố từng xác suất bằng bit.
- `a0-batched-comparison-reference03.json` dẫn về tham chiếu gốc và bằng chứng replay. Worker hiện tái dùng hai artifact đã kiểm SHA, không chạy lại phép đối chiếu này.

## Lịch sử lỗi được giữ

1. Request01 dừng trước dispatch do gọi tên Volume theo execution thay vì logical run. Đã sửa tham chiếu Volume A0 thực tế. App dừng có acknowledgment.
2. Request02 lỗi import launcher vì đường dẫn remote ngắn hơn giả định. Đã sửa phép tìm root không dùng chỉ số vượt độ sâu. App lỗi được dừng riêng trước lượt tiếp.
3. Request03 đã thực hiện replay A0 thành công nhưng A1 chưa train vì gọi wrapper riêng A0 với tham số đồ thị. Đã đổi sang `run_junyi_selected` có sẵn. Giữ `gpu_worker_attempt03.py`, log và archive lỗi. Lỗi thuộc worker vận hành, không đổi kiến trúc hoặc kết quả A0.
4. Request04 tái dùng replay A0, gọi entrypoint chung, batch128 train/validation. Đọc dispatch/receipt/monitor để xác định trạng thái thực, không suy training từ việc đã tạo App.

## Tài nguyên và lưu trữ

Trần đợt CPU0,15USD và H1003USD trong tổng30USD free credits toàn KLTN. Một GPU, không auto retry của hàm, có watchdog và timeout. Các lỗi thiết lập được giữ để đối soát tổng chi, không cấp một ngân sách mới cho mỗi request. Mức dự phòng lịch sử trong ledger bảo thủ hơn meter trước đợt này. Cần đối soát lại khi hết đợt.

Checkpoint được công bố có COMPLETE marker rồi sync sang Volume theo run. Artifact lớn giữ tại `experiments/akt/results/modal-junyi-a1-b128-h100-20261113-*/`, source/runtime/cache tại `artifacts/akt/`. Không chuyển model vào ổ C hoặc commit model lớn. Khi hết thời gian phải giữ partial checkpoint để resume, không khởi động lại từ đầu.

`monitor_once.py` chỉ đọc container của App hiện hành, giữ tiến độ và thông số GPU. `gpu_controller.py`, `gpu_worker.py` tái dùng controller/producer hiện có với nguồn đã qua Gate. Các request và source pins ghi rõ dữ liệu gốc và giới hạn. Mọi kết luận đối chứng BKT/GAM phải chờ đánh giá độc lập theo cùng biên thông tin.
