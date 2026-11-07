# AKT Task 14 — Báo cáo mức sẵn sàng instrumentation

Cập nhật: 04/11/2026  
Phạm vi ban đầu là hoàn thiện instrumentation; cập nhật 04/11 ghi nhận một preflight bị dừng vì RAM và một lần chạy Task 14 được ủy quyền. **Lần chạy mới đã nạp bounded Development cohort và cập nhật 32 optimizer steps, rồi gặp lỗi khi thay thế file progress trên Windows. Không chạy Task 13/15, outer fold, CV hoặc Holdout.**

## A. Kết luận

**INCONCLUSIVE. Lần chạy duy nhất đã huấn luyện một phần và đo được tốc độ/RAM sơ bộ, nhưng thất bại khi ghi progress trước validation/checkpoint/export. Gate 4 chưa PASS.**

Instrumentation và synthetic tests sẵn sàng, nhưng lần pilot chưa hoàn tất chu trình train → validation → checkpoint save/load → prediction export. Synthetic tests không chứng minh toàn bộ lifecycle trên cohort Junyi. Lần chạy dừng ở lỗi I/O; không tự retry. Bất kỳ lần chạy tiếp theo nào cũng cần authorization mới, build/runtime/data/config/run ID/caps khớp chính xác.

## B. Nguyên nhân và sửa đổi

Trước remediation, pilot chỉ báo cáo training/validation loss và epoch được chọn. Nó không chạy lại checkpoint/export cycle của smoke và thiếu phép đo batch/window/tokens, substep timing cùng phân loại partial run. Ngoài ra, nếu RSS vượt ngưỡng ngay sau optimizer update, guard có thể ném lỗi trước khi ghi nhận update vừa hoàn tất.

Đã hoàn thiện instrumentation tối thiểu trong:

- `src/knowledge_tracing/akt/model.py`: đo riêng forward, backward, gradient clipping và optimizer update tại adapter hiện có.
- `src/knowledge_tracing/akt/training.py`: đếm windows, batches, độ dài chuỗi và batch shapes thực tế; target/context/padding/valid tokens; target đã xử lý/đã tối ưu; loss, gradient norm, clipping, update, thời gian và resource snapshots. Epoch không đầy đủ không tạo selection checkpoint. Nếu RSS guard dừng sau optimizer update, progress của bước đã hoàn tất được lưu trước khi dừng.
- `src/knowledge_tracing/akt/data.py`: đo thời gian truy vấn DuckDB theo timeline, sort và materialization/fetch, cùng số learner-event rows thực tế trả về.
- `src/knowledge_tracing/akt/runner.py`: phân biệt số learner/target được chọn và thực sự nạp; lưu progress/partial evidence; chu trình pilot đầy đủ tải lại checkpoint, so trạng thái model chính xác, dự đoán và export cohort inner-validation, rồi xác minh coverage/phân phối. Không tính outer-fold metric.
- `src/knowledge_tracing/akt/watchdog.py`: lưu snapshot RSS của parent và RAM khả dụng toàn hệ thống quanh vòng đời subprocess, cùng worker PID, elapsed time, return code và trạng thái.
- `tests/akt/test_pilot.py`, `tests/akt/test_data.py`, `tests/akt/test_runner.py`: bao phủ chu trình pilot tổng hợp, partial/resource stop và phép đo loader; test cap được cô lập khỏi output sản phẩm.

Không đổi source AKT upstream, model dimensions, loss, optimizer, batch/window protocol, cohort caps hay resource limits. Không sửa BKT/GAM-KT hoặc frozen artifacts.

Rà soát `model.py` cho run này: các thay đổi đo thời gian quanh native forward/backward, gradient clipping và optimizer step, đồng thời trả thêm telemetry. Công thức `mean_loss = native_sum_loss / n`, thứ tự backward → clip → optimizer step và mask đưa vào native model không đổi; attention/masks được giữ bởi upstream model và causal window adapter. Test parity/causality/model hiện hành pass 21/21. Probe khởi tạo intended config đã gọi thành công `build_native`, nhưng phần in cấu trúc cuối bị lỗi do `out` là `Sequential`, không có thuộc tính `.in_features`; không dùng lỗi introspection này làm bằng chứng model sai, nhưng cũng không ghi nhận được bản dump kích thước cuối trước khi dừng vì RAM.

## C. Tái sử dụng smoke và partial run

Pilot gọi chung `load_checkpoint`, `restore_checkpoint`, `_checkpoint_state_matches`, `iter_predictions` và `export_predictions` đã dùng trong pipeline smoke. Kiểm tra export gồm `source_row` duy nhất, đủ identity/key và coverage expected/prediction/fitted/unseen; prediction chỉ hợp lệ nếu là xác suất hữu hạn và thuộc nhóm đã fit hoặc unseen/null tương ứng.

Nếu epoch bị chặn bởi step/time/target cap, selection trả trạng thái `bounded`, `complete_epoch=false`, giữ counts/loss/gradient/resource đã tích lũy, không validation epoch đó, không tạo checkpoint cho epoch dở dang và không chạy export. Nếu tài nguyên vượt ngưỡng hoặc watchdog timeout, lifecycle là `incomplete` với stop reason resource/timeout; lỗi số học/lỗi triển khai là `failed`. Không trạng thái nào trong số đó được ghi thành completed fit. Khi guard phát hiện RSS vượt ngay sau update, bước vừa chạy cùng loss/gradient được flush vào progress trước khi exception thoát.

## D. Gate 2 và bằng chứng

Suite synthetic cuối cùng:

```powershell
$env:PYTHONPATH='src;third_party'; .venv\Scripts\python.exe -B -m pytest tests/akt tests/shared_kt -q -p no:cacheprovider
```

Kết quả xác nhận: **155 passed in 66.20s**. Log: `artifacts/akt/preflight/gate2-tests.log`. Báo cáo Gate 2 được cập nhật ở `artifacts/akt/preflight/gate2.json`; trạng thái `PASS`, 40 SHA-256 mã nguồn/test gắn với build hiện tại. Hash log: `55200622772dca06a859a86d3d301640502e0f6cc4db2e0510842fabeadc870b`. Gate 2 report SHA-256: `3b7ec3c55829d969ab4a2f4a1cfa0e02136b9faa2c71d9d805c8a2579ba269df`.

Provenance/runtime trong Gate 2 còn giữ source commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88` và lock SHA-256 `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`. `require_gate2_evidence` được gọi sau khi cập nhật và chấp nhận report/log/build hashes hiện tại. Gate 1/source không bị thay đổi.

Task 13 evidence vẫn tồn tại: `experiments/akt/results/smoke-task13-20261101-03/manifest.json` ghi `completed`; SHA-256 hiện tại `be9529ef218ff3d48b192ee1241a478dac53a4dbe5ab8c3594508f18ac901cec`. Không ghi vào run đó.

Các test tổng hợp trong suite xác minh authorization theo phase/build/config, cấm full-fold/CV tự động, checkpoint mismatch, export identity/coverage, giới hạn runner và không đổi cấu hình/mô hình. Trong pilot `-02`, chỉ learner thuộc cohort Development đã chọn được nạp; không đọc Holdout.

## E. Cấu hình và điều kiện cho lần chạy được duyệt

Template `experiments/akt/configs/pilot.json` vẫn khóa intended architecture `d_model=256`, `heads=8`, `blocks=1`, `d_ff=1024`, `final_fc=512`; CPU/FP32, batch 4, context `H=100`, target block `T=100`. Caps giữ tối đa 1024 learner train và 256 inner-validation, 100000 target rows tổng, một epoch hoặc 900 giây training, 1200 giây toàn subprocess, RSS worker 2 GiB và RAM khả dụng toàn hệ thống floor 1 GiB. Pilot `-02` chỉ đo được một phần epoch.

Lần preflight đầu đã chọn 1024 learner train và 256 learner inner-validation từ assignments Development; hai nhóm rời nhau và ngoài outer fold 0, nhưng dừng trước launch vì RAM chỉ còn `1,536,565,248` byte. Sau khi RAM hồi phục, sáu snapshot mới nằm trong `5,050,019,840–5,467,385,856` byte; độ dao động `417,366,016` byte trong 25 giây. Run ID mới `pilot-task14-20261104-02` dùng config/auth mới, checks parent/worker pass, và CLI được gọi đúng một lần.

Run `-02` giữ đúng CPU FP32, d=256, 8 heads, 1 block, d_ff=1024, final FC=512, H/T=100, batch=4, 1 epoch/900s train, 1200s subprocess, 2 GiB RSS ceiling, 1 GiB available-RAM floor. Pre-spawn watchdog thấy RAM `4,647,559,168` byte; sau worker import `4,341,276,672` byte. Output dir là mới. Cohort được chọn 1024/256 và rời nhau ngoài fold 0; actual loader giữ 417 train learners/50.000 targets và 256 validation learners/29.199 targets. Hai query trả lần lượt 100.000 và 29.199 event rows do loader đọc trọn learner trước khi giữ target cap; combined targets được giữ là 79.199.

Config SHA-256 `3e6e39dc08ef5e9acdc51fd123a8bdbfd54c42201665a4cf763cbff4e98e8649`; config identity SHA-256 `ed8cf880fee6f246dac6fe44e3535a1da30a63c41c9bf19c9c3efe5e12ab8e8b`; authorization SHA-256 `6ba68b3ebfcac46e89954c25a28b6413a2b70984a834f5deb4e0a4d47b53006c`. CLI log ở `artifacts/akt/preflight/pilot-task14-20261104-02-cli.log`; SHA-256 `9722568bcd12e96aa1c6c4ae2b64e41f01e64710cd086c0f28d589f49b8243f8`.

## F. Giới hạn độ chính xác phép đo

- Thời gian `chronological_query_sort_and_materialize_seconds` là wall time gộp của query có `ORDER BY`, DuckDB fetch và materialization qua loader; chưa tách riêng chi phí sort khỏi fetch.
- Training substep durations được đo bằng đồng hồ đơn điệu quanh các lệnh của PyTorch; chúng không bao gồm toàn bộ Python/loader/shuffle/resource-check overhead. `windows_per_second` và `scored_targets_per_second` dùng training wall time nên thể hiện throughput end-to-end của epoch.
- Worker current RSS và system available RAM được lấy ở các điểm resource-check/progress và lifecycle phases; peak RSS dùng peak working-set của hệ điều hành nếu nền tảng cung cấp. Snapshot không thể loại trừ spike ngắn giữa hai lần đo. Giá trị parent RSS là các snapshot của watchdog, không phải tổng RAM hệ thống.
- Nếu tiến trình bị kill cứng hoặc máy mất điện, file progress cuối cùng chỉ phản ánh snapshot đã flush gần nhất; nó không thể chứng minh trạng thái chưa ghi.
- Synthetic results không cho biết kích thước cohort thực, tỷ lệ OOV, throughput, peak memory, thời gian hoàn thành hay khả năng thực hiện inner selection/refit trên Junyi.

## G. Bước kế tiếp

Run `pilot-task14-20261104-02` kết thúc `failed` sau 30,19 giây, worker exit code 1. Lỗi cụ thể là `PermissionError: [WinError 5] Access is denied` tại `runner._write_json` khi `os.replace(pilot-progress.json.tmp, pilot-progress.json)` trong lần ghi progress sau một batch. File đích tồn tại, file `.tmp` đã được ghi; nguồn tiến trình/handle làm hệ điều hành từ chối replace chưa xác định. Runner ghi được `pilot.json` và manifest trạng thái `failed`; không retry. `pilot-progress.json` trên đĩa dừng ở 31 steps, file `.tmp` và `pilot.json.partial_progress` ghi đủ 32 steps. Progress có `complete_epoch=false`, nhưng trường `stop_reason` vẫn là `epoch_complete` do exception xảy ra giữa epoch trước khi train loop cập nhật nguyên nhân; status tổng thể `failed` là kết quả đúng.

Training đã tối ưu 7.346 targets qua 128 windows/32 batches trong 10,868 giây training wall time: **675,9 scored targets/s** và 11,78 windows/s. `loss_sum=3697,035`; mean loss tính từ tổng/count là `0,50327`. Cả 32 steps có gradient khác 0 và cập nhật tham số; clipping xảy ra 4/32 steps (12,5%), max norm trước clip 1,4217 và sau clip 1,0. Có 53/128 windows dài 200; batch shapes gồm 29 `4×200`, một `4×180`, một `4×100`, một `4×42`. Đây là prefix/partial sample, không phải epoch hoàn tất.

Worker RSS peak là `732.065.792` byte (0,682 GiB), current khi progress flush là `731.271.168` byte; system available RAM thấp nhất trong worker là `3.861.966.848` byte (3,597 GiB), cao hơn floor 1 GiB. Watchdog parent peak RSS `25.997.312` byte; system available RAM thấp nhất ở ba parent snapshots là `4.545.531.904` byte. Không có checkpoint Task 14, validation, checkpoint reload/parity hoặc prediction export; `predictions/` không tồn tại. Không có bằng chứng Task 14 về source_row alignment/fitted-unseen coverage. Task 13 manifest/checkpoint/export đã được xác minh trước launch và vẫn nguyên trong run directory riêng.

## H. Ngoại suy sơ bộ khối lượng và thời gian

Benchmark Development đã audit 20.706.208 validation rows qua năm fold. Outer-train mỗi fold là 16.507.559–16.644.953 targets; inner-train gần 14,86–14,98 triệu/epoch chỉ nếu số rows gần tỷ lệ learner 90/10. Từ pilot partial, ngoại suy có điều kiện theo 675,9 targets/s:

- Outer-train một epoch: khoảng 6,78–6,84 giờ.
- Inner selection train: khoảng 6,11–6,16 giờ/epoch; validation thêm khoảng 10% rows nhưng throughput validation chưa đo. Nếu tạm áp cùng tốc độ cho train+validation thì khoảng 6,78–6,84 giờ/epoch, giả định này chưa được kiểm chứng.
- Inner selection 1–20 epochs: train-only khoảng 6,1–123 giờ; kèm validation theo proxy cùng tốc độ khoảng 6,8–137 giờ.
- Fresh refit 1–20 epochs: khoảng 6,8–137 giờ/fold.
- Outer validation có 4,06–4,20 triệu rows/fold; proxy cùng target rate là 1,67–1,73 giờ/fold, nhưng inference throughput chưa đo.
- Năm folds, giả sử selection và refit cùng E epochs, có khoảng 186,4 triệu target/validation presentations ở E=1 và 3,334 tỷ ở E=20. Proxy thời gian lần lượt khoảng 76,6 giờ và 1.370 giờ (57,1 ngày), chưa kể overhead loader/sort/export và biến thiên do validation/window shapes.

Đây là ngoại suy từ 7.346 targets/128 windows, không phải benchmark full epoch; mẫu chỉ 32 batches và 53 windows L=200. Data distribution, validation speed, đầu/cuối epoch và I/O có thể làm sai lệch đáng kể. Kết quả cho thấy protocol selection + refit có nguy cơ tốn nhiều ngày đến nhiều tuần trên CPU ở E cao, nhưng chưa đủ để kết luận go/no-go. Gate 4 **INCONCLUSIVE**; Task 15 chưa được biện minh. Không chuyển sang fixed E=3 nếu chưa có phê duyệt riêng.
