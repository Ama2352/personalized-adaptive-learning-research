# Báo cáo chẩn đoán và retry AKT Task 13 — 2026-11-01

Phạm vi: sửa lỗi export của bounded smoke trên Development, xác minh Gate 2, và thực hiện tối đa một retry được ủy quyền. Không chạy pilot, outer fold, CV hoặc Holdout.

## A. Nguyên nhân

`runner._select_inner_cohort` xếp hạng cohort bằng SHA-256 để quyết định membership. `_capped_learners` giữ thứ tự cohort đó khi nạp Development; do vậy tuple validation tiếp tục theo thứ tự hash. `runner._run_phase` trước đây truyền tuple đó thẳng vào `prediction.iter_predictions`, trong khi `iter_predictions` yêu cầu `user_id` tăng dần từ điển. Đây là chỗ producer và consumer bất đồng: cohort selection đúng membership, loader giữ đúng chronology từng learner, nhưng adapter prediction chưa đổi thứ tự learner groups.

Exporter ghi shard theo learner và hoàn tất một learner khi gặp learner kế tiếp. Hai learner đầu của thứ tự cohort tình cờ không vi phạm thứ tự từ điển. Khi bắt đầu learner thứ hai, exporter đã promote shard của learner đầu (`user_id=12448`, 205 rows). Inversion xuất hiện ở learner thứ ba; `iter_predictions` ném `ValueError` trước khi phát record của learner đó. Expected-population audit chỉ chạy sau khi đọc xong prediction stream nên chưa bắt đầu. Manifest cũ vì vậy là `incomplete`, ghi một learner/205 rows; đây không phải coverage hoàn tất.

Vị trí chính: `src/knowledge_tracing/akt/runner.py` gọi producer ở bước export; `src/knowledge_tracing/akt/prediction.py` giữ kiểm tra thứ tự và quản lý manifest/shard nguyên tử. Resume không gây lỗi: run ID cũ không được tái sử dụng; CLI từ chối output đã tồn tại.

## B. Sửa và kiểm thử

`order_prediction_learners` sắp xếp tuple learner đã bị giới hạn theo `user_id` ngay tại prediction boundary. Membership hash-selected không đổi; event tuple bên trong từng learner không bị sửa và vẫn theo `(time_done, source_row)`. Expected-population iterator vẫn nhận thứ tự cohort gốc. Không sửa assertion, shared KT contract, baseline hay upstream AKT.

Regression tests kiểm tra cohort không theo lexical order và reopen tất định; event chronology không đổi; prediction và expected iterator có thứ tự khác nhau; một learner 201 rows đi qua nhiều Parquet shard; known và OOV null xen kẽ; từng `source_row` xuất hiện đúng một lần; và export lỗi vẫn incomplete, không thể bị nhận là complete. Test budget training xác nhận counter phân biệt windows/targets đã xử lý với targets thực sự tối ưu.

Kết quả:

- Test tập trung prediction + budget: `12 passed`.
- Lệnh Gate 2: `$env:PYTHONPATH='src;third_party'; .venv\Scripts\python.exe -B -m pytest tests/akt tests/shared_kt -q -p no:cacheprovider`.
- Kết quả cuối: `141 passed in 37.72s`, exit code 0.
- Gate 2 report: `artifacts/akt/preflight/gate2.json`; test log: `artifacts/akt/preflight/gate2-tests.log`.
- Upstream AKT commit: `01b7e8d7d7c862cabc9467108e3e7f2555653a88`; lock SHA-256: `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`.
- Gate 2 ghi 35 source/test hashes. Test log SHA-256: `58941a339e94bc8e0cb45fc0c29e751dbc2c700fbec1ba373715371bcaeda503`. Report SHA-256 sau khi ghi: `0f2e5e39cd7227f068f8e318865eb378ebe71931aa5e143f22d8d02473f5a2f6`.
- `_require_gate2_evidence` và CLI `preflight` xác nhận source/runtime/lock/build/test log còn khớp. CLI `--help` hoạt động.

## C. Accounting của run ban đầu

Các số dưới đây là run `-01` đã chạy trước bản sửa; chúng không mô tả retry `-02`:

| Bộ đếm | Giá trị | Diễn giải |
|---|---:|---|
| Train target được chọn | 4.096 | Chạm target cap đã duyệt; đây là giới hạn loader, không phải số hyperparameter được chọn theo metric. |
| Train target đã xử lý | 4.096 | Đã đi qua 48 training windows trong kiểm tra read-only run trước. |
| Train target tối ưu | 4.096 | Checkpoint ghi 4.096 valid targets đóng góp vào loss/gradient. |
| Optimizer steps | 12 | 12/12 có gradient khác 0 và cập nhật tham số. |
| Learner train thực nạp | 11 | Cohort tối đa là 32; target cap đạt trước khi cần hết cohort. |
| Learner validation | 16 | 549 target validation. |
| Validation fitted / unseen | 441 / 108 | Unseen 19,67%; xuất phát từ vocabulary train nhỏ trong smoke và không đại diện cho toàn Development CV. |

Train loss mean là `0.659937`; validation loss mean-known là `0.647450`. Checkpoint save/load state khớp chính xác; training phase RSS đo được là `458,420,224` bytes, train epoch `0.702s`. Các số loss/checkpoint này không biến run `-01` thành smoke thành công vì export chưa hoàn tất. Bản sửa hiện ghi rõ `selected_targets`, `windows_processed`, `processed_target_rows`, và `optimized_target_rows` cho một run tương lai; retry `-02` dừng trước khi các counter cohort/training đó được tạo.

## D. Retry duy nhất và resource

- Run ID mới: `smoke-task13-20261031-02`.
- Config: `experiments/akt/configs/smoke-task13-20261031-02.json`; SHA-256: `7b63416eb8094a1d3797d5feaebe9dfb64ce942a1d2629ab85c6b87eb47b6f55`.
- Authorization: `experiments/akt/authorizations/smoke-task13-20261031-02.json`; được kiểm bằng `_require_authorization`, bind config, Gate 2, source/runtime/data identity và giữ nguyên các cap đã duyệt.
- Lệnh đã gọi đúng một lần qua CLI watchdog: `& .\.venv\Scripts\python.exe -B -m knowledge_tracing.akt.cli smoke --config experiments/akt/configs/smoke-task13-20261031-02.json --authorization experiments/akt/authorizations/smoke-task13-20261031-02.json`.
- Trước CLI, RAM khả dụng là `2,168,180,736` bytes và đĩa trống `64,891,527,168` bytes; output `-02` chưa tồn tại. Trong child process, lần kiểm tra bắt buộc trước khi nạp cohort thấy RAM khả dụng dưới `1,073,741,824` bytes và dừng với `MemoryError`. Không có cohort Development được đọc, không có checkpoint hoặc prediction cho `-02`.
- CLI log: `artifacts/akt/preflight/task13-run02-cli.log`. Output directory `experiments/akt/results/smoke-task13-20261031-02` không được tạo. Run `-01` và artifacts incomplete của nó vẫn được giữ nguyên.
- Peak RSS và minimum available RAM chính xác tại thời điểm guard fail không được ghi bởi guard hiện tại; không suy diễn các giá trị đó. Retry không đạt tới training, validation, export hoặc Gate 3 resource summary. Không thử retry lần hai.

## E. Gate verdict và bước kế

Gate 2: **PASS** với 141 test và hash evidence hiện hành. Gate 3: **BLOCKED** cho yêu cầu smoke hoàn chỉnh: run `-01` **FAIL** tại export; retry duy nhất `-02` **BLOCKED** trước khi đọc dữ liệu do RAM floor. Do không có bounded train/validation/export cycle hoàn chỉnh, chưa thể kết luận prediction distribution, exact coverage sau sửa, nguồn hàng alignment thực trên run mới, hay resource summary toàn subprocess.

Task 14 chưa đủ điều kiện. Cần một phê duyệt riêng sau khi có điều kiện RAM ổn định và một kế hoạch smoke hợp lệ mới; báo cáo này không cho phép chạy pilot.
