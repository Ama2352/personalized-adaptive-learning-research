# A1 — đọc dữ liệu, selection và nối checkpoint epoch1

## Trạng thái trước H100

Nguồn đã đóng băng để chạy, Linux CPU Gate đạt **2.528 ca**, không fail/error/skip. Archive Gate đã tải về D và kiểm SHA/inventory. VM CPU đã dừng có acknowledgment. Dự phòng CPU tối đa0,15USD theo ledger toàn dự án30USD. Số chi thực cần đối soát meter sau lượt GPU.

## Đã làm và bằng chứng

- Tách preparation khỏi scoring trong `prediction_batch.py`, dùng chung logic prediction/OOV. Selection có thể chuẩn bị trước một chunk hữu hạn trên một thread trong khi GPU chấm batch hiện tại. Reader được đóng khi model lỗi. Giữ thứ tự window, batch, các RNG và target identity.
- Train window reader có tùy chọn đọc trước đúng một shard. Không đổi shuffle, record hay vị trí commit của sampler. Tests kiểm lặp hai epoch và lỗi ở thread đọc.
- Đã thử cache selection trên đĩa với window nhân quả và đáp án riêng trong sidecar. CPU build hoàn tất1.600.343target trong226,55giây, không Holdout. Toàn28.449window và metadata khớp tuyệt đối với đường raw,0OOV, target population khớp A0.
- Cache lookup ban đầu có phần đọc/kiểm113,44giây so raw62,61giây. Đổi metadata sang stream giảm còn94,03giây, nhưng raw cùng lượt60,85giây. Đây là thời gian CPU có kiểm geometry/digest, chưa là inference GPU. **Cache selection trên đĩa tắt trong cấu hình H100.** Cache graph cũng tắt theo bằng chứng đợt trước. Giữ hai cache là tùy chọn đã kiểm, không mặc định áp dụng một phương án chậm hơn.
- Từ checkpoint source2 epoch1 thật, hai window TRAIN80 có200target/152target có thông tin đồ thị, alpha0,0401386, reference frozen và compact khớp probability/loss/gradient/model/Adam/Python–NumPy–Torch RNG sau một bước CPU tạm. Probe thành công13,51giây, không sửa checkpoint nghiên cứu. `actual-checkpoint-parity.json` và log03 giữ kết quả. Hai lỗi thiết lập trước được giữ ở log01/02, lần đầu chọn window không có tín hiệu đồ thị và lần hai guard yêu cầu root vật lý khi nạp module frozen từZIP.
- Đã thêm validator chuyển identity có schema đóng và receipt ngoài ghim SHA. Producer nhận transition cho **epoch1 đầy đủ, trước validation**, xuất lineage vào output mới và giữ checkpoint cũ. Kiểm state machine xác nhận không học lại epoch1 hoặc cộng counters hai lần. `transition-tests04` có186ca đạt, các suite trước có112và174ca, có overlap nên không cộng làm tổng.

## Nguồn và trạng thái model

Checkpoint gốc tại `experiments/akt/results/modal-junyi-a1-b128-h100-20261113-05/checkpoints/train-epoch-001/state.pt`,28.914.223byte. Epoch1 đã học13.347.331target/1.818step, validation còn chờ. Source02ZIP khớp build identity của checkpoint, có kiểm AST các module số học chưa đổi và reference frozen chạy trong namespace riêng. `source2-static-review.json` giữ truy vết.

Gói source mới tại `artifacts/akt/modal/junyi-a1-selection-cache-20261113-01/source.zip`. `source-gate-preparation.json` giữ inventory và biến đổi notebook. `experiments/akt/results/modal-junyi-a1-selection-cpu-20261113-01/receipt.json` giữ Gate Linux, archive và xác nhận nguồn không đổi.

## Lượt H100 dự kiến

`h100-request.json`, `h100-preparation.json`, `gpu_worker.py` và `gpu_controller.py` chuẩn bị một H100, cap3USD, watchdog2000giây, function timeout2100giây, không auto retry, scaledown2giây. Thời gian native1500/1600giây được giữ từ checkpoint, không tính lại theo thời gian chờ cấpGPU. Dùng đọc trước train/selection, giữ FP32/batch128 cùng split/optimizer/early stopping. Tái dùng bằng chứng A0 đã kiểm, không chạy lại A0 replay.

Worker phải kiểm CUDA bằng checkpoint thật trước khi tạo receipt transition. Khi đạt, producer nạp nguyên model/Adam/RNG source2, xử lý validation epoch1, rồi học tiếp epoch2. Khi lỗi canary thì dừng, giữ diagnostics. Khi hết thời gian thì giữ checkpoint đã công bố, không restart seed42. Lượt này chưa là refit/calibration/fullCV hoặc đánh giá độc lập.

Giá H100 chính thức kiểm ngày13/11 là0,001097USD/giây. Trần tính bảo thủ2,883USD gồm cả CPU/RAM mức3× và thời gian dự phòng, dưới allocation3USD. Guard còn kiểm cận chi phí lịch sử, allocation khác và dự phòng3USD trong tổng30USD. [Giá Modal](https://modal.com/pricing)

## Các entrypoint có giới hạn

- `prepare_junyi_selection_cache.py --request ...` chỉ chuẩn bị CPU vào `artifacts/akt/window-cache/`. Cache thử nghiệm đã tạo ở `full-selection10-20261113-01` được giữ để truy vết kết quả âm.
- `verify_full_selection.py --label stream` kiểm toàn input/metadata, không gọi model.
- `check_actual_checkpoint.py --device cpu|cuda --output-name <tên-mới>.json` kiểm hai window thật và một bước Adam tạm. CPU bypass admission CUDA trong process probe. CUDA phải qua profile/guard thật.
- `cpu_controller.py` và `gpu_controller.py` mặc định chỉ admission, cần `--run` để dispatch. Lượt GPU còn phải kiểm ledger/source pins và trạng thái App trước khi gọi.

Bundle đang mở trong khi H100 được chuẩn bị. Kết quả GPU, checkpoint, figure và báo cáo được cập nhật theo kết quả thực, không suy từ exit code hoặc App đã tạo.
