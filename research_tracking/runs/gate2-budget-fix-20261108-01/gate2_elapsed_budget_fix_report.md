# Sửa chốt ngân sách thời gian Gate2 — 08/11/2026

Gate20 có **724 kiểm tra chức năng PASS nhưng không đạt ngân sách đã khai báo**: controller ghi `1083.9951060999883s`, trong khi `timeout_seconds=540`. Script cũ chỉ dựa vào `subprocess.run(timeout=...)`, rồi công bố PASS mà không so sánh lại elapsed. Bản sửa buộc cả nơi phát hành lẫn nơi đọc Gate từ chối báo cáo quá giờ hoặc thiếu/sai trường ngân sách. Không sửa báo cáo Gate20 lịch sử, model, hyperparameters, split, dữ liệu hay quyền chạy thí nghiệm.

## Chẩn đoán từ bằng chứng thực tế

| Lượt | Tổng controller | Tổng JUnit | Đúng testcase refit recovery | Kết luận được phép |
|---|---:|---:|---:|---|
| [Gate18](../../artifacts/akt/preflight/gate2-evidence-20261108-context-18.json) | 179.084513s | 177.045s | 1.682s | Chức năng và thời gian dưới cap540s |
| [Gate19](../../artifacts/akt/preflight/gate2-evidence-20261108-sim-trainer-19.json) | 372.052467s | 368.079s | 3.087s | Chức năng và thời gian dưới cap540s |
| [Gate20](../../artifacts/akt/preflight/gate2-evidence-20261108-graph-prototype-20.json) | 1083.995106s | 1081.972s | 922.520s | 724 chức năng PASS; chấp nhận ngân sách bị lỗi |
| [Chạy cô lập đúng testcase](../../artifacts/akt/local-tests/gate20-refit-diagnostic-20261108-01/run.json) | 12.055534s | 8.452s | 7.896s | 1PASS, không timeout45s; không tái hiện mức922s |

Testcase là `tests/akt/test_refit_recovery.py::test_refit_recovery_matches_uninterrupted_weights_adam_rng`. SHA của testcase và ba nguồn `training.py`, `resumable.py`, `runner.py` giống nhau trong cả Gate18/19/20. Phần JUnit còn lại của Gate20 là159.452s. Điều này khoanh vùng bất thường ở thời gian của một testcase; chưa xác định được nguyên nhân của nó. [Bảng đối chiếu và SHA sáu report/XML](../../artifacts/akt/local-tests/gate20-refit-diagnostic-20261108-01/comparison_and_findings.json).

Lượt cô lập chỉ dùng synthetic fixture của testcase, `.venv`, CUDA ẩn, OMP/MKL/OpenBLAS mỗi biến bằng2 và timeout45s; source/lock/upstream trước–sau không đổi. Metadata thực tế: PyTorch2.7.1+cpu, intra-op2, inter-op12, CPU count16, CUDA unavailable/uninitialized. Một process chỉ import Torch với môi trường hiện tại không giới hạn cho12/12 threads. Các Gate cũ không ghi số thread thực tế, vì vậy không được quy922s cho oversubscription. [Metadata chuẩn hóa, có ghi phép chuẩn hóa](../../artifacts/akt/local-tests/gate20-refit-diagnostic-20261108-01/process_metadata.normalized.json).

Một lần đọc tối đa10 timestamps System/Kernel-Power42/107 bị từ chối với `System.UnauthorizedAccessException`; không nâng quyền và không thử đọc rộng hơn. **Host suspend: UNKNOWN.** Khoảng cách UTC giữa các lượt làm việc cũng không xác nhận suspend hoặc thời gian tính toán.

## Cơ chế có thể giải thích timeout không tương đương elapsed

CPython3.13.5 local trên Windows gọi `WaitForSingleObject` trong `Popen._wait`; [trích đúng stdlib đã đọc và SHA](../../artifacts/akt/local-tests/gate20-refit-diagnostic-20261108-01/local_cpython_wait_excerpt.json), đối chiếu [nguồn CPython v3.13.5](https://github.com/python/cpython/blob/v3.13.5/Lib/subprocess.py#L1596-L1613). Microsoft ghi rõ countdown của [WaitForSingleObject trên Windows8+](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject) không tính thời gian low-power, còn [QPC](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps) tính cả standby/hibernate/connected standby. Python3.13 dùng cùng clock monotonic/QPC cho [perf_counter](https://docs.python.org/3.13/library/time.html#time.perf_counter).

Đây là **cơ chế tương thích với triệu chứng**, chưa phải nguyên nhân đã chứng minh trên máy này. [Tài liệu subprocess](https://docs.python.org/3.13/library/subprocess.html) cũng không bảo đảm ngắt ngay thời gian tạo process. Dù nguyên nhân922s là gì, elapsed1084s vẫn vượt cap540s và không được phát hành PASS.

## Thay đổi đã kiểm

- [authorization.py](../../src/knowledge_tracing/akt/authorization.py): thêm `validate_gate2_elapsed_budget`; timeout phải là exact `int` trong1..600, elapsed phải là exact `int`/`float`, hữu hạn, không âm và không vượt timeout. Reader bắt buộc hai trường hiện có ngay cả khi status vẫnPASS, tests không rỗng và pointer SHA đã được tính lại. Thiếu trường, bool, string, NaN/Infinity, số âm, integer cực lớn và timeout ngoài miền đều bị từ chối.
- [refresh_gate2.py](../../scripts/akt/refresh_gate2.py): đo elapsed sau subprocess thành công, parse JUnit và xác minh nguồn; kiểm ngân sách trước khi ghi PASS hoặc thay pointer. Khi vi phạm, ghi độc quyền report `REJECTED_RESOURCE_BOUND` chứa counts, nguồn/build/lock, SHA log/XML, observed/allowed; dùng JSON chuẩn rồi ném `TimeoutError`. Pointer và backup pointer không được chạm vào trong nhánh này. Không ghi đè run ID cũ.
- Child software suite được đặt `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=2` trước import Torch; CUDA tiếp tục bị ẩn. Đây là giới hạn vận hành kiểm thử CPU, không là lựa chọn tối ưu model hoặc methodology nghiên cứu.
- Giữ schema1, timeout mặc định300s và trần600s. [tests/akt/test_runner.py](../../tests/akt/test_runner.py) chỉ bổ sung `elapsed_seconds=1.0`, `timeout_seconds=30` cho fixture Gate dương tính; không sửa neural tests hoặc production config.

## Kiểm tra trước–sau

| Bằng chứng | Kết quả thực tế | Giới hạn |
|---|---|---|
| [Snapshot trước sửa](../../artifacts/akt/local-tests/gate2-budget-fix-pretest-20261108-01/source_inventory.json) | 4 input copies, SHA trước–sau copy khớp | Chưa chạy test tại thời điểm snapshot |
| [Trial01 RED](../../artifacts/akt/local-tests/gate2-budget-fix-trial-20261108-01/run.json) | 44tests:19PASS/25FAIL; controller10.797052s | Lỗi thực tế với source cũ, giữ log/XML/source snapshots |
| [Trial02 PASS](../../artifacts/akt/local-tests/gate2-budget-fix-trial-20261108-02/run.json) | 47PASS/0fail/error/skip; controller9.366551s, JUnit7.493s | Thêm3 tình huống clock âm/NaN/Infinity sau lượt RED |
| [Kiểm lại receipt/nguồn/reader](../../artifacts/akt/local-tests/gate2-budget-fix-trial-20261108-02/final_verification.json) | 4 nguồn cuối khớp SHA trial02; reader thật từ chối pointer đã revoke tại thời điểm kiểm | Không thay pointer, không phát hành Gate mới |

Hai lượt targeted mất tổng20.163603s, dưới ngân sách60s; **0 optimizer steps, 0 model fit**. Chỉ chạy `test_gate2_refresh.py` và hai node Gate2 cụ thể trong `test_runner.py`, không chạy các neural runner cases. Fake child exit0/JUnit3PASS cùng clock1084s/cap540s phải bị từ chối, giữ nguyên pointer byte-for-byte; chỉ clock của script được thay thế, không mock `time` toàn process. Reader bị thử với báo cáo đã rehash để phân biệt kiểm ngân sách với lỗi digest. Trường hợp trong ngân sách và đúng biên vẫnPASS. `git diff --check` cho4 files sửa không có lỗi whitespace; có cảnh báo chuyển LF→CRLF theo cấu hình repository.

## Trạng thái và giới hạn

Source/tests đã freeze sau trial02. Các Gate18/19/20 gắn source cũ không chấp thuận source đã sửa; cần Gate mới trên đúng source/lock hiện hành. Tại receipt kiểm cuối, current pointer trỏ audit revoke Gate20 SHA`e6a53ade40d01ee4229fcc3fe5b8d3e7364c984e3c37a632e4e49810b4c1a9c7` và reader thực tế từ chối. Parent quản lý pointer/Gate21; báo cáo này không tự thay pointer hoặc tăng ngân sách.

Chốt mới chặn **chấp nhận sau khi hoàn tất** nếu vượt elapsed; không chứng minh hard interrupt trong khi host suspend hoặc đang ở một lệnh hệ điều hành không thể ngắt. Không trừ elapsed bằng thời gian sleep suy đoán. Không có full suite, dữ liệu thật, GPU, cloud, thay OS power settings hoặc Git mutation trong batch sửa này. Software PASS không là bằng chứng efficacy của AKT/CG-AKT hay hoàn thành RQ.

Ghi chú truy vết nhỏ: file metadata raw của lượt refit cô lập có trailer literal `\\n`; giữ nguyên bản và ghi companion chuẩn hóa bỏ đúng2 ký tự, không chạy lại model. Một inline verification helper ban đầu thiếu `src` trong import path, được ghi trong receipt kiểm cuối; sửa import path cho kiểm metadata, không thêm lượt test hay thay implementation.
