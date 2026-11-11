# Hoàn thiện setup AKT trên Modal — 12/11/2026

## Trạng thái hiện hành

Gói nguồn sửa đóng gói đã qua Gate CPU đầy đủ1.994/1.994ca trên VM8GiB. GPU pilot11 đã thực hiện6Adam updates/144target giả trên TeslaT4 nhưng chưa lưu/phục hồi checkpoint thành công. Kiểm storage bằng vài byte đã đạt trên native filesystem và Volumev2. Pilot12 đã đạt đủ6process/16updates/384lượt target giả,4checkpoint và parity A0/A3. Đã đọc lại12file/106.888.132bytes của bốn checkpoint trực tiếp từ Volumev2, khớp archive native. Actual A0 GPU lifecycle đã đạt7epochs/best4/14updates/4.704lượt train-target/84dự báo và4checkpoint. Đã kiểm độc lập artifact. Actual Main60 A0 selected đang chạy tiếp, allocation riêng giữ aggregate dự toán0,437USD dưới grant0,50USD.

Người dùng yêu cầu các lượt training tiếp theo dùng GPU Modal. Nhánh CPU training engineering đã dừng sau lượt02, lỗi và artifact được giữ. Chưa Main60, Junyi, Holdout, full CV hoặc kết quả so sánh chất lượng A0–A3 mới từ bundle này.

## Chuỗi điều tra

1. Log server lượt07 xác nhận chờ cấp phát và đang bổ sung GPU capacity. Lượt08 tiếp tục hết hạn, thống kê có1input chờ/0container. Đường SandboxT4 lượt09 cũng hết hạn tạo sau180giây và đã cleanup.
2. Gate CPU trên gVisor bị giới hạn RSS cũ chặn. Probe không train cho thấy riêng importTorch2.7.1+cu126 báo khoảng3,5GiB RSS. VM thử đầu chỉ có khoảng2,4GiB thực do request2GiB nên còn lỗi floor RAM. VM request8GiB đã đạt đủ1.993ca với nguồn/test cũ. Một sai khác loss nhỏ trong lượt VM lỗi trước được giữ trong JUnit, lượt Gate đủ sau đó đạt nguyên kiểm exact.
3. Actual selected A0 engineering01 dừng trước model do bộ đóng gói viết lại notebook vốn đã sạch, làm lệch danh tính nguồn của corpus. Đã sửa ở `scripts/akt/build_colab_bundle.py`, thêm hồi quy, đạt14ca local. Không sửa corpus hoặc notebook gốc. Gate04 đạt đủ1.994ca trên gói mới.
4. Actual selected A0 engineering02 đã train tới bước lưu checkpoint rồi bị `os.link` từ chối trên Volumev1. GPU11 cũng train được6updates trước khi guard từ chối alias ở thư mục mount. Hai lỗi này xác nhận cấu hình storage của runner cần sửa.
5. Tài liệu Modal xác nhận Volumev2 hỗ trợ hard-links. Đã kiểm helper thật `publish_new_file` trên native filesystem và Volumev2, gồm chống ghi đè và tải lại đối chiếu SHA. Source helper giữ nguyên.
6. Runner hiện ghi checkpoint ở filesystem cục bộ của container. Sau mỗi pha, copy kết quả sang Volumev2 dưới `/durable`, kiểm SHA rồi `sync`. Archive cuối được kiểm trước commit/tải về. Model và hyperparameter giữ nguyên.

## Bằng chứng và phạm vi

- Source/command của từng phép kiểm có trong bundle. Các file có hậu tố attempt01/02/03 giữ đúng launcher/worker trước sửa.
- `cpu03__*` giữ log, JUnit, Gate trên gói trước. Gate04 và archive/checkpoint lớn giữ ở `experiments/akt/results/<run-id>/`.
- `source-package-correction.json` và `SOURCE_PACKAGE_FIX.md` mô tả sửa packaging. Commit riêng `d2f06cc`.
- `storage-probe-result.json`, `storage-fix-plan.json` ghi nghiệm thu file và thiết kế pilot12.
- `billing-*.json` là tổng kỳ tại thời điểm đọc, có thể trễ. Đến01:32ngày12/11 tổng API ghi0,05055687USD, net billed0USD. Grant pilot tổng0,50USD vẫn là giới hạn vận hành hiện hành.
- `verify_checkpoint.py` là phép đối chiếu archive CUDA độc lập, chỉ chạy nghiệm thu sau khi receipt đạt. Không importTorch local.

## Điều kiện hoàn tất tiếp theo

Pilot12 đã đạt sáu tiến trình A0/A3, bốn checkpoint, model/Adam/RNG/counters/predictions liên tục–phục hồi khớp, bản durable và archive tải về đều được kiểm độc lập. Bước hiện hành là lifecycle A0 GPU trên cohort engineering10x84, đo chi phí rồi lập allocation nghiên cứu. Main60 và Junyi cần danh tính dữ liệu/training riêng.

## Nguồn bên ngoài

[GPU và fallback](https://modal.com/docs/guide/gpu), [Volumev2 và hard-link/sync](https://modal.com/docs/guide/volumes), [Runtime VM/gVisor](https://modal.com/docs/guide/sandboxes#runtimes). Không suy nguyên nhân quota/payment từ trạng thái chờ.


## Mốc tiếp theo đã đạt — Main60 A0 trên GPU

Ngày 12/11 — đã huấn luyện baseline AKT không đồ thị trên GPU Modal. Sau khi kiểm trọn quy trình trên nhóm nhỏ, đã chạy corpus nghiên cứu Grade 10 gồm 60 học viên, với 48 người huấn luyện, 6 người chọn epoch và 6 người dành riêng cho hiệu chỉnh. Lượt A0 hoàn tất 8 epoch và 288 bước cập nhật, chọn checkpoint epoch 5, nạp lại rồi xuất đủ 1.260 dự báo trên 6 người của tập selection. Năm checkpoint cùng log và archive khoảng 124 MB đã được giữ; file kết quả, mã kiểm toàn vẹn, danh tính dự báo và hai phép tính Log Loss/Brier đã được đối chiếu độc lập sau khi tải về. Tổng chi phí sử dụng của workspace tại lần đọc sau lượt này khoảng 0,171 USD, được bù bằng credits/allowance; số liệu có thể cập nhật trễ. Tập selection đã dùng chọn epoch, vì vậy cần tiếp tục các bản đồ thị, bước refit/hiệu chỉnh và đánh giá độc lập trước khi kết luận về lợi ích của CG-AKT. Chưa có kết quả Junyi từ lượt này.

Bằng chứng độc lập `main60-a0-verification.json`, mã dựng lại `verify_main60_a0.py`, lịch sử `main60-a0__fit80__epochs.json` và `main60-a0__events.jsonl`. Artifact lớn tại `experiments/akt/results/modal-main60-a0-selected-20261112-01/`. Phần còn thiếu là A1/A2/A3, refit/calibration, so sánh độc lập và Junyi. Full workflow resume trên GPU vẫn chưa được nghiệm thu.
