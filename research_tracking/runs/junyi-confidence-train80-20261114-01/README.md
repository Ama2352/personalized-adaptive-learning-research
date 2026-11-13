# Confidence TRAIN80 Junyi cho A2/A3

Đợt ngày 14/11/2026, tạm dừng theo yêu cầu người dùng. Chưa training AKT A2/A3. Gate Linux CPU-only có reservation tối đa 0,15 USD, đã dừng và tải artifact. Chi phí riêng của lượt này chưa tách được từ billing tổng, ledger giữ nguyên cận bảo thủ 0,15 USD.

## Mục tiêu

Tạo một artifact confidence dùng chung A2/A3 từ TRAIN80 frozen của A0/A1. Điểm đo mức ổn định của cải thiện dự báo khi bổ sung thống kê quá khứ của một parent vào baseline đã có thống kê child và mức đúng chung. Điểm này phục vụ trọng số cạnh, chưa là xác suất cạnh tiên quyết thật hoặc bằng chứng cải thiện vòng kín.

## Phương pháp giữ nguyên

- Tái dùng `research_junyi_confidence.py` và solver/bootstrap trong `edge_confidence.py`. Crossfit ba nhóm người học TRAIN80, seed42, logistic lbfgs và 200 bootstrap người học theo Method24.
- Dựng feature trước khi dùng đáp án hiện tại, trong prefix native window giống AKT. Lịch sử rollover/OOV giữ cùng semantics đã kiểm. Tập selection/calibration/outer validation và Holdout không tham gia fit confidence.
- Duyệt đủ 13.347.331 target TRAIN80 trong 232.662 record. Chỉ lưu feature cho child có cạnh vào. Graph có 976 cạnh và 736 child. Child ngoài vocabulary TRAIN80 giữ lý do không hỗ trợ, trọng số vận hành bằng 0.
- A2 dùng confidence cố định, A3 dùng cùng artifact và học thêm cổng trong lúc train AKT. Phải đánh giá độc lập và mô phỏng sau đó để trả lời hiệu quả nghiên cứu.

## Cài đặt và kiểm

`src/knowledge_tracing/akt/research_junyi_confidence_run.py` spool SQLite trên D, commit dữ liệu cùng offset đọc và checkpoint riêng từng child. `scripts/akt/fit_junyi_confidence.py` điều phối CPU theo tranche, lưu RAM/thời gian và tạo process mới cho từng child. SQLite đã đóng được ghim SHA. Child có summary, OOF nén và marker COMPLETE với SHA. Finalize chỉ công bố confidence khi đủ mọi child và lineage/byte khớp.

`tests03.log`/`tests03.xml` ghi 40 ca đạt trên source hiện hành, gồm spool/resume so toàn row với feature tham chiếu, fitter CPU thật trên dữ liệu giả, finalize khi đủ child, corruption, child rỗng, resource cap và hồi quy staged IO. Các lượt kiểm có overlap, không cộng thành số lượng ca độc lập. `confidence-bulk01.log` giữ lỗi serialization tuple/list của fixture, đã sửa và kiểm lại.

## Vị trí chạy và phục hồi

- Lượt đầu tại `artifacts/akt/confidence/full-train80-20261114-01/` được dừng có chủ đích khi phát hiện bộ đo RSS mới chỉ đo venv launcher. `guard-correction.json` ghi lý do. SQLite/nhật ký được giữ.
- Lượt hiện hành tại `artifacts/akt/confidence/full-train80-20261114-02/` có source identity mới sau sửa bộ đo toàn cây process. Không sửa identity của lượt trước. Log `spool02.log`, tài nguyên trong `controller-*.jsonl` của output.
- Theo request đã ghim trong `request.json`. Runtime và source identity trong output. Chỉ dùng `.venv` local, giới hạn worker RSS448MiB và tranche900giây. Khi hết tranche, tiếp tục cùng output và cùng source. Lỗi tài nguyên không được gán thành cạnh không hỗ trợ về mặt thống kê.

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/fit_junyi_confidence.py --request research_tracking/runs/junyi-confidence-train80-20261114-01/request.json --output artifacts/akt/confidence/full-train80-20261114-02 --action spool --max-seconds 900 --max-rss-mib 448
.\.venv\Scripts\python.exe -B scripts/akt/fit_junyi_confidence.py --request research_tracking/runs/junyi-confidence-train80-20261114-01/request.json --output artifacts/akt/confidence/full-train80-20261114-02 --action fit-all --max-seconds 3600 --max-rss-mib 448
.\.venv\Scripts\python.exe -B scripts/akt/fit_junyi_confidence.py --request research_tracking/runs/junyi-confidence-train80-20261114-01/request.json --output artifacts/akt/confidence/full-train80-20261114-02 --action finalize --max-seconds 300 --max-rss-mib 448
```

Sau confidence còn cần Gate Linux mới, CUDA parity/resume ngắn, snapshot và allocation đúng cận ngân sách trước training A2/A3. Checkpoint A0/A1 đã lưu giữ nguyên. `STATE.json` được cập nhật theo tiến độ thật, chưa công bố confidence COMPLETE khi còn thiếu child.

## Bàn giao khi tạm dừng

Đã dừng cây process local đang chạy, danh sách trong `pause-processes.json`, không còn process thuộc lượt đó. `STATE.json` giữ số record/target đã commit và SHA SQLite trước/sau phục hồi transaction dở. Khi tiếp tục, dùng cùng output02 và source confidence đã ghim, không tạo lại corpus từ đầu. Chưa có child fit hoặc confidence COMPLETE.

Tại lúc dừng, SQLite đã commit đủ232.662record và13.347.331target, lưu11.807.185row của các child có cạnh vào. **Chưa có SPOOL_COMPLETE.json**, nên còn bước kiểm/niêm phong trước fit. Dữ liệu không bị coi là confidence đã fit. Lệnh spool cùng source sẽ tiếp tục bước kết thúc còn thiếu.

Gate Linux tại [hồ sơ riêng](../junyi-a2-a3-linux-gate-20261114-01/README.md) đạt 2.590 ca trong 139,59 giây CPU, đã tải ZIP và xác nhận App dừng. Sau Gate này có thay đổi cache, vì vậy cần Gate mới trên source cuối trước chạy GPU.

Theo yêu cầu tách CPU/GPU kỹ hơn, đã mở rộng cache graph A2/A3 chứa weighted messages và gate features. `cache-tests01.log` ghi 38 ca đạt, gồm cached/direct khớp feature, dự đoán và hai bước Adam, cùng hồi quy A1. Tiếp đó đã sửa API selection admission và producer để nhận cache selection/graph. **Phần sửa selection mới chưa được kiểm**, chưa nối đầy đủ vào `prepare_junyi_gpu_stage.py` và `run_junyi_gpu_stage.py`.

Thứ tự tiếp tục gồm hoàn thiện wiring và tests selection receipt, tiếp tục spool/fit confidence, build các cache CPU thật cho train và selection, đóng source/Gate cuối, kiểm ngắn Modal thật có thời gian từng stage và checkpoint/resume. Training chính A2/A3 bị giữ đến khi các điều kiện đó đạt. Các thao tác đọc batch, chuyển tensor và lưu checkpoint trong numerical worker vẫn cần được đo, chưa có kết quả xác nhận mức tiết kiệm của thiết kế mới.
