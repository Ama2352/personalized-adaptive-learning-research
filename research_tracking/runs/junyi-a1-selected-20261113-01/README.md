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

## Chốt lượt source cũ và lưu checkpoint

Run04 đã học 1.000 bước/7.365.262 target tại checkpoint được công bố, alpha khoảng0,020778. `checkpoint1000-inspection.json` xác nhận model, optimizer và cả bốn RNG, sampler consumed128.000window. File .pt28.914.671byte trên D, SHA khớp metadata/Volume. Đây là checkpoint giữa epoch, chưa có validation A1 hoặc selected model.

Watchdog tính cả thời gian chờ cấp GPU đã kết thúc App lúc14:53:43. Đã xác nhận0container. Lần lấy live logs qua CLI bị cắt stdout, nhưng sau đó phục hồi archive26.639.508byte đủ19file từ Volume. `archive-verification04.json` xác nhận SHA receipt, ZIP CRC và từng file, gồm cả logs. Trạng thái remote FAILED thuộc đợt bị giới hạn thời gian, không coi đó là full epoch đã hoàn tất. Checkpoint1000 vẫn dùng được với source cũ.

## Source2 tối ưu đã nghiệm thu trong phạm vi kiểm

`research_graph_model.py` copy mask về CPU một lần khi bind và vector hóa residual A1. Giữ mọi kiểm integrity, alpha gradient ở0, graph-off và nhánh A2/A3 cũ. Có snapshot source2 tại `research_graph_model_source2.py`, không hotpatch run04.

56kiểm CPU đạt, tiếp đó Linux Gate source02 đạt2.336ca,0fail/error/skip. Hồ sơ native ở `experiments/akt/results/modal-junyi-a1-selected-cpu-20261113-02/`, source tại `artifacts/akt/modal/junyi-a1-selected-20261113-01/source02.zip`.

`vector-gpu-probe03.log` chứa nguyên stdout của phép đối chiếu H1009,02giây, gồm JSON kết quả đầy đủ. `vector-gpu-result03-from-stdout.json` được trích từ dòng JSON này, không coi đó là bản sao byte của file JSON remote. Phép kiểm dùng nguồn ngoài cây đang train, tiến trình riêng trên GPU hiện có, không sửa code hoặc trọng số run04. Batch128×200,12.800target,717exercise, alpha0 và0,75. Loss/prob/parameters sau1Adamstep khớp trong cả2điều kiện, gradient drift tối đa6,52e-9, Adam moment drift tối đa3,49e-10, RNG/dropout khớp. Chưa chứng minh bitwise toàn trajectory.

Giữ hai lượt probe trước bị guard RAM chặn ngay khi import Torch. Torch CUDA trong VM này cần khoảng3,4GiB RSS trước fixture. Lượt3 đặt baseline sau import, giới hạn thêm2GiB private và tổng6GiB RSS. Hai lượt lỗi chưa thực hiện phép đối chiếu CUDA. Lỗi upload đầu do giới hạn chiều dài argv Windows được sửa bằng nén nguồn. Chưa cài thêm thư viện global. CLI có trường hợp trả0dù child lỗi, nên nghiệm thu dựa status và nội dung JSON.

Figure `a1-vector-h100-v1.svg/.png/.pdf`, dữ liệu `a1-vector-h100-data.csv`, dựng bằng `build_vector_figure.py`. Đã kiểm trực quan. Giữ rõ đây là một cặp mỗi alpha, thứ tự đảo, GPU chia sẻ với training, có warm-up khác nhau giữa cặp và chưa phải tốc độ toàn Junyi. Quy ước bảng màu từ figures4papers, provenance cùng giấy phép đã lưu ở bundle nguồn được dẫn trong script.

## Run05 dùng source2 từ seed42

Root chọn khởi tạo lại A1 từ seed42 để fit bằng source2 đã kiểm, giữ riêng trajectory/checkpoint source cũ. Quyết định vận hành này chưa do người dùng chỉ định riêng. Không cộng1.000bước run04 vào run05. Không thay split, vocabulary, công thức model, optimizer hoặc quy tắc chọn epoch. `request05.json` ghi rõ lựa chọn và cap3USD mới trong30USD toànKLTN. `gpu_worker_attempt04.py` giữ bản vận hành trước sửa timer.

100bước đầu run05 trên cùng761.969target mất77,33giây, so127,53giây của run04.500bước mới mất366,71giây, so603,11giây của bản cũ. Đây là số đo thực hai lượt H100, không phải benchmark lặp có ghép cặp. Còn phải đo epoch đầy đủ, validation, checkpoint/reload/export và mức chi sau lượt mới.

Worker mới giới hạn thời gian còn lại theo deadline cả lượt, chừa khoảng lưu artifact. Giữ source2 của run05 để tiếp tục cùng trajectory sau checkpoint, không tự restart theo mỗi thay đổi tối ưu.

Prototype projector evidence được DEFER. Benchmark CPUstdlib1,81giây cho1,067lần ởfixture sparse,1,325lần ởfixture dense. Chưa đủ bằng chứng lợi ích trên payload Junyi thực để mở một source/trajectory mới. `evidence-projector-benchmark.json` giữ dữ liệu và hash tương đương trong fixture, chưa áp dụng vào production.
