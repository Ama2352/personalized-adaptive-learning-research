# A1 — context gọn đã nối adapter và kiểm T4

## Kết quả ngày 13/11/2026

Đã đưa context A1 dạng bytes bất biến vào `JunyiGraphAKTAdapter` và `ResearchGraphNative`, giữ đường reference để đối chiếu. Producer selected-fit A1 đã được nối với tùy chọn compact. Chưa khởi chạy training nghiên cứu hoặc dùng Modal trong đợt này.

| Phép đo | Reference | Compact |
|---|---:|---:|
| CPU dựng context và bốn checksum trên 128 window Junyi thật | 0,838357 giây | 0,065225 giây |
| T4 chuẩn bị batch và 8 bước học trên dữ liệu tổng hợp | 13,787333 giây | 3,391457 giây |
| Target/giây trong đoạn đo T4 | 7.427 | 30.194 |
| GPU-Util trung bình theo mẫu T4 | 14,98% | 76,00% |
| Số mẫu GPU | 44 | 12 |
| VRAM sử dụng đỉnh theo nvidia-smi | 5.305 MiB | 5.305 MiB |

Tăng tốc 12,85 lần cho riêng thành phần CPU và 4,065 lần cho đoạn chuẩn bị batch + training step trên T4. GPU probe mất tổng 34,03 giây. Mỗi backend có hai block bốn bước theo thứ tự reference, compact, compact, reference. Mỗi block khôi phục cùng khởi tạo, alpha 0,75, Adam và RNG trước khi đo. Có 12.800 target mỗi bước, batch128 × 200, vocabulary 717.

## Thay đổi thực thi

- `research_junyi_compact.py` tính đúng message A1 từ shifted responses của native window, cùng mặt nạ active và metadata source rows/phase/encoding/condition. Payload dùng bytes bất biến. Checksum được tính lại mỗi lần sử dụng.
- Kiểm phase/support ở hai đầu batch, kiểm geometry từng window. Chuyển các kiểm phase lặp từng window về biên batch trong builder đồng bộ. Có ca kiểm thay đổi encoding giữa batch để xác nhận bị phát hiện.
- Native nhận cả evidence reference và compact. Giữ thứ tự các target active theo hàng/vị trí, cùng phép nhân alpha, residual, backbone, loss và optimizer. Alpha vẫn nằm trong forward, kể cả khi alpha bằng 0. Target có message 0 vẫn giữ active nếu có prerequisite được quan sát.
- `compact_context=False` giữ đường reference cho caller dùng adapter trực tiếp. Factory selected-fit A1 chọn `True`; A0 giữ nhánh AKTAdapter hiện hành. Recovery signature có backend để tránh nối checkpoint sang đường thực thi khác một cách ngầm định.

Hướng tổ chức lại phần CPU phù hợp nguyên tắc giữ hàng đợi tính toán cho GPU và giảm các điểm chờ trong hướng dẫn PyTorch. Đợt này giữ FP32, batch, learner splits và quy tắc tối ưu hiện hành. [Hướng dẫn PyTorch](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html#avoid-unnecessary-cpu-gpu-synchronization)

## Đúng số học và biên dữ liệu

69 ca local đạt qua ba lượt có log riêng. Lượt đầu gồm 65 ca về compact/reference, adapter Junyi, vector A1 và native Grade10. Lượt bổ sung có ba ca về encoding đổi giữa batch, message 0 và đổi backend. Một ca kiểm factory xác nhận selected-fit A1 bật compact. Kiểm model gồm hai bước Adam, hai mức alpha, graph-on/off, thiếu support, dự đoán, source/ticket mutation và chạy ngắt rồi phục hồi checkpoint cùng backend. Lượt 65 ca có trần 240 giây/1 GiB RSS, thực tế khoảng 95 giây và đỉnh 814 MiB.

T4 kiểm riêng alpha 0 và 0,75 với cùng khởi tạo/RNG. Loss, gradient sau clip, tham số sau một bước Adam, trạng thái optimizer và RNG khớp hoàn toàn trong các đại lượng đã lưu. Dự đoán được đối chiếu ở bộ kiểm CPU. T4 probe dùng Torch 2.14.1+cu130, CUDA 13.0, venv dự án kế thừa runtime có sẵn.

CPU component dùng đúng 128 window seed43 của shard đầu TRAIN80, 102 learner, 5.527 target, graph976 cạnh và vocabulary717. Message FP32 và mask khớp hoàn toàn. Có kiểm pins của roles, encoding, graph, shard và source. Không đọc sự kiện calibration/Holdout. Gói upload Colab chỉ chứa source và fixture tổng hợp, không có log Junyi, token hoặc checkpoint nghiên cứu.

## Giới hạn và quyết định tiếp theo

GPU 76% được quan sát trong đoạn đo ngắn, với cửa sổ nvidia-smi tương quan và ranh giới phase xấp xỉ. Đây chưa là mức GPU trung bình toàn epoch. Fixture T4 có lịch sử lặp A/B/C và graph hai cạnh, khác phân bố Junyi thật. Chưa gồm SQL/cache I/O, checkpoint, validation hoặc khởi động cloud. Chưa đo source mới trên H100. Không quy đổi 22 phút thành 2 phút từ các số đo này.

Đã nối producer ở local sau phép đo T4 và kiểm factory bằng CPU. Probe GPU dùng adapter trực tiếp. Full producer và Gate Linux cho toàn source cuối vẫn cần nghiệm thu trước lượt nghiên cứu tiếp theo.

Checkpoint A1 source2 epoch1 trước validation được giữ nguyên tại `experiments/akt/results/modal-junyi-a1-b128-h100-20261113-05/checkpoints/train-epoch-001/state.pt`. Đợt này chưa chuyển checkpoint này sang backend/source mới. Cần kiểm migration có manifest riêng, giữ model/optimizer/RNG/counters/population và nghiệm thu validation từ checkpoint thật. Kiểm resume synthetic cùng backend đã đạt, chưa đủ để tự động cho phép migration source2.

Ưu tiên tiếp là kiểm full producer và checkpoint thật bằng workload giới hạn, rồi đo lượt đại diện để dự toán training. Cache message trên đĩa được tạm hoãn, chỉ thêm khi số đo lượt đại diện cho thấy còn cần. Kết quả hiện tại đủ cơ sở tiếp tục hướng compact trong khi giữ số lượng thành phần vận hành ở mức nhỏ. RQ3 vẫn cần selected fit, refit, calibration, đánh giá độc lập và so sánh các model nghiên cứu.

## Bằng chứng được lưu

- `summary.json`, các CSV CPU/GPU và `compact-adapter-cpu-t4-v1.svg/.png/.pdf` giữ số liệu, telemetry và hình độc lập đã kiểm trực quan. `build_figure.py` dựng lại hình, giữ provenance quy ước màu figures4papers.
- `local-regression.json/.log`, `extra-tests.json/.log`, `factory-test.json/.log` giữ ba lượt kiểm. `verify_local.py` chạy lượt đầu có resource watchdog. Không cộng lại các ca trùng từ bundle cũ.
- `benchmark_context.py` giữ CPU comparison trên một shard, `context-component.json` giữ kết quả và input pins.
- `probe_t4.py` giữ script đã chạy trên Colab. `transfer-manifest.json` ghi SHA gói nguồn và từng file trước upload. `source-pins.json` là source của lượt CPU component. `final-source-pins.json` ghi source cuối sau nối factory và bổ sung tests.
- `download-receipt.json` ghi kiểm SHA archive, CRC và SHA từng member sau tải về D. Raw result/log/ZIP ở `experiments/akt/results/colab-a1-compact-adapter-20261113-01/`.
- `runtime-release.json` xác nhận probe đã thoát, không còn compute process của lượt kiểm, cell gọi `runtime.unassign()` đã trả về và bridge đã đóng. Đợt này dùng 0 USD Modal.
- `manifest-final.json` đóng inventory bundle. Khi đo lại dùng run ID mới. Dùng `.venv` trong repository cho Python local, giữ nguyên artifacts đã đóng.
