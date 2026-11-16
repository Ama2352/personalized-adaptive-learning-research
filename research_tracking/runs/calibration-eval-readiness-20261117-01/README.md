# Khép ranh giới phần mềm cho đánh giá Junyi độc lập

## Đã hoàn thiện

Thêm phase `outer_evaluation` cho đúng learner outer fold 4 trong các role đã đóng băng. Phase này chỉ tạo prediction windows. Encoding phải có lineage refit90; encoding TRAIN80 bị từ chối. Ba graph adapter A1/A2/A3 đã refit nhận phase mới và tiếp tục từ chối optimizer batch ở phase đó. Các phase train, selection và calibration giữ tập learner/fold như trước.

Reader chọn `allowed_folds=(4,)` cho outer, `(0,1,2,3)` cho các phase nội bộ. Kiểm role/content identity trước mở reader và sau khi kết thúc stream. Cache cohort kỹ thuật cũ được từ chối rõ ràng khi dùng cho outer. Các view là ranh giới phần mềm, quyền chạy một lượt dữ liệu thật được xác định ở entrypoint cùng manifest/grant hiện hành.

## Kiểm metadata của kết quả đã train

`audit_roles.py` chỉ đọc JSON role, cache manifest, encoding và export index. Đã hash roles.json khớp pin trong stage-inputs của cả A0–A3, tái tính role identity/epoch-plan identity, selected-input identity và refit-input identity. Refit-input identity tái tính khớp bốn export. Encoding90 được đọc và kiểm SHA/identity với receipt, fit view và bốn export.

| Nhóm | Người học |
|---|---:|
| TRAIN80 | 126.774 |
| Selection10 | 15.847 |
| Refit90 = train + selection | 142.621 |
| Calibration10 | 15.847 |
| Outer fold4 | 39.616 |

Mọi giao đôi của train/selection/calibration/outer bằng 0. Refit90 không giao calibration hoặc outer. Cache manifest train/selection ghi rõ calibration, outer và Holdout events không nằm trong cache. Tổng target train + selection theo metadata là 14.947.674 mỗi epoch. `ROLE_LINEAGE.json` giữ hashes và các binding đối chiếu, chỉ xuất counts/identity vào hồ sơ này.

Đây là kiểm lineage metadata. Chưa đọc từng assignment, event, prediction hoặc checkpoint, nên không kết luận từ kiểm này rằng mọi event đã train đều tuân thủ metadata. Export index của bốn model vẫn ghi `calibration_completed=false` và `independent_evaluation_completed=false`.

## Kiểm thử đã chạy

Lượt cuối `tests04.txt` và `tests04.xml` đạt **66 passed in 85.79s**. Bao gồm phase data cũ/mới, cache, encoding lineage, calibration consumer và ba graph adapter trên native backbone CPU rất nhỏ với dữ liệu tổng hợp. CUDA admission bị mock trong fixture hiện hữu, không dùng GPU.

Các hồi quy mới kiểm cross-role, fold inner trong outer reader, event có fold khác learner, stream thiếu/ngoại lai, cache kỹ thuật dùng nhầm outer, encoding TRAIN80 dùng cho outer, role/content drift trước reader access, optimizer bị chặn khi graph adapter đã chuyển outer, cùng dự đoán ba biến thể trên toy sequence.

Giữ các failure trước để truy vết. `tests01.txt` thiếu `PYTHONPATH=src`, nên collection dừng. `tests02.txt` gặp Git dubious ownership của dependency upstream. Lượt sau dùng duy nhất cấu hình Git per-process cho thư mục upstream đã biết, không đổi cấu hình global. `tests03.txt` có một test báo source drift trong khi source đang được sửa giữa lượt. Lượt cuối được chạy sau khi freeze source và đạt toàn bộ. Các lỗi đó là kiểm môi trường/engineering, không phải kết quả nghiên cứu.

## Cách kiểm lại

PowerShell tại `D:\Dev\KLTN`, dùng `.venv`.

```powershell
$env:PYTHONPATH = 'D:\Dev\KLTN\src'
.\.venv\Scripts\python.exe -B research_tracking\runs\calibration-eval-readiness-20261117-01\audit_roles.py
```

Lệnh test đã nghiệm thu được giữ trong `COMMANDS.json`. Khi chạy mới, chọn output/basetemp mới và giữ env changes trong phạm vi process. Kiểm Git ownership chỉ áp dụng path `D:/Dev/KLTN/artifacts/akt/dependencies/upstream`, các kiểm source commit/hash vẫn được thực hiện bởi loader cũ.

## Phần còn lại để có số liệu nghiên cứu

1. Entry point nạp refit export bằng config/vocab/mapping đúng, kiểm model/source/checkpoint identity và ghi lineage train-source so với inference-source hiện hành. Thay đổi source ranh giới này cần current-source Gate/runtime receipt phù hợp trước thực thi thật.
2. Chuẩn bị calibration phase đầy đủ từ dữ liệu Development đúng learner role. Cache selected/refit90 đang giữ không chứa calibration hoặc outer labels, nên phải có nguồn/manifest riêng cho các phase đó.
3. Producer tạo raw calibration prediction đầy đủ và `CalibrationTarget` cùng exact population keys đã tính độc lập. Phải gắn event/source-row, learner, item và history-prefix identity đúng nghĩa. `window_id` chưa đủ để tự khẳng định history-prefix provenance. OOV/null tiếp tục có mặt trong coverage.
4. Fit temperature riêng cho từng final checkpoint bằng calibration10. Producer phải dự toán RAM của `fit_temperature` hiện hữu vì hàm materialize targets và logits. Chưa có benchmark RAM/thời gian cho calibration Junyi đầy đủ trong lượt này.
5. Entry point outer evaluation tiếp tục cần grant/config/source/output/budget, exact target population và predictor/export wiring. Phase reader mới chỉ khép phần cấp view và fold routing. Không lấy metadata audit hoặc unit tests làm quyền truy cập outer tự động.
6. Xuất raw/calibrated prediction, coverage/OOV và LL/Brier/AUC/ECE, paired learner statistics theo family đã chốt. Protocol21 phân loại BKT5fold cũ là historical reference vì training population khác refit90 của ma trận mới. Graph contrasts cần các điều kiện information-matched đã khai báo, matched GAM/Graph-GAM vẫn là phần việc riêng.

Không chạy calibration thật, outer prediction thật, training, GPU hoặc cloud trong lượt này. Các checkpoint, split, hyperparameter, artifact cũ và nguyên tắc predict-before-update giữ nguồn hiện hữu. Bổ sung này chưa tạo kết quả thực nghiệm mới cho RQ3.
