# GPU07: phản biện độc lập source đã freeze — 08/11/2026

## Kết luận và phạm vi

**Chưa tìm thấy P1 hoặc authorization bypass trong các đường CLI đã đọc.** Không có static blocker mới cho bước main-worker **CPU synthetic có authorization riêng và inputs giữ bất biến**. Đây là kết luận review mã, không nghiệm thu một execution. Gate18 đang chạy khi review; không đọc/khẳng định kết quả Gate18, không tự cấp quyền CPU/GPU hoặc đánh dấu actual Linux/CUDA thành công.

Đã so diff workspace với Git revision **`e4a44e9`** cho `config.py`, `authorization.py`, `watchdog.py`, `runner.py`; đọc trực tiếp các tệp mới `context.py`, `device_budget.py`, builder và tests vì untracked files không xuất hiện trong `git diff`. Đọc thêm recovery/data/training call sites liên quan. Không sửa source/tests/config/build/gate inputs, không rerun tests/model, không raw Junyi/Holdout/GPU/cloud. Chỉ tạo báo cáo này; parent quản indices/state/Git.

## Findings theo mức ưu tiên

### P2 — Hash input qua paths chưa bind nguyên tử với actual DuckDB read

**Evidence:** [context.py:18](../../src/knowledge_tracing/akt/context.py#L18), [revalidate:60](../../src/knowledge_tracing/akt/context.py#L60), [input hashing:151](../../src/knowledge_tracing/akt/context.py#L151) kiểm bytes theo từng lần mở path. [Runner:221](../../src/knowledge_tracing/akt/runner.py#L221) đọc assignments sau preflight; [data.py:17](../../src/knowledge_tracing/akt/data.py#L17) và [data.py:69](../../src/knowledge_tracing/akt/data.py#L69) để DuckDB mở các paths/glob riêng. [Runner:387](../../src/knowledge_tracing/akt/runner.py#L387) và [runner:624](../../src/knowledge_tracing/akt/runner.py#L624) revalidate sau đó.

Một writer đồng thời có thể đổi file/tree **A→B→A** giữa các lần hash và DuckDB query: pre/post hashes vẫn A nhưng loader đã materialize B. Thêm Parquet ngắn hạn giữa inventory/query rồi xóa cũng thuộc cùng giới hạn. Source hiện tại chưa có stable opened-file handles hoặc immutable staging snapshot bind với loader. Đây là **static race reasoning**, chưa exploit, fault injection hoặc execution được thực hiện trong review; không gọi là đã chứng minh bypass trên run thực tế.

**Implication:** `input_hashes` chứng minh integrity ở thời điểm kiểm, chưa là atomic attestation của mọi byte DuckDB đã đọc. Với inputs builder mới tạo và không có writer đồng thời, không có bằng chứng race đã xảy ra; finding không tự chặn CPU2-step dummy với vùng input được giữ bất biến.

**Đề nghị batch sau:** tài liệu/run contract nói rõ immutability; trước claim adversarial concurrent-write protection cần immutable staging/copy có manifest, cùng actual materialized-data binding và deterministic fault-injection regression. Không sửa loader hoặc Gate18 trong review này. Không tự làm snapshot raw realdata chỉ để xử lý finding.

### P3 — Lỗi CUDA smoke giữ exception gốc nhưng stop-reason phân loại quá rộng

**Evidence:** [runner.py:644](../../src/knowledge_tracing/akt/runner.py#L644) đặt mọi exception khi `pilot=False` thành `incomplete`; [runner.py:655](../../src/knowledge_tracing/akt/runner.py#L655) suy `stop_reason=resource_or_timeout`. Vì `cuda-smoke` đi `pilot=False`, `ValueError` của context/CUDA setup hoặc numerical/implementation failure cũng có thể mang nhãn này. `error_type`/`error` vẫn được ghi và exception được re-raise, nên **không mất root exception**. [Test setup failure](../../tests/akt/test_cuda_budget.py#L69) kiểm đúng original error và incomplete manifest bằng mocked CUDA setup.

**Đề nghị:** consumer phải ưu tiên exact `error_type/error`, không dùng `incomplete` làm bằng chứng chỉ thiếu tài nguyên hoặc retryable. Batch sau có thể phân loại resource/implementation riêng cho CUDA mà giữ historical smoke verdict; không cần sửa giữa Gate18. Đây là giới hạn diagnostic classification, không một đường execution tiếp tục sau failure.

## Các nhánh đã kiểm và không thấy bypass

| Vấn đề cần phản biện | Evidence source | Nhận định có giới hạn |
|---|---|---|
|Missing context gây default real-data fallback CUDA?|[context.py:187](../../src/knowledge_tracing/akt/context.py#L187), [watchdog.py:110](../../src/knowledge_tracing/akt/watchdog.py#L110), [runner.py:318](../../src/knowledge_tracing/akt/runner.py#L318)|`cuda-smoke` thiếu sidecar bị từ chối trước Torch/runner import ở `_execute`; runner CUDA entry cũng yêu cầu context. CPU không sidecar giữ historical default path có authorization riêng; không diễn giải “mọi CPU command đều synthetic”.|
|Context là approval ngầm?|[authorization.py:225](../../src/knowledge_tracing/akt/authorization.py#L225), [context auth identity:169](../../src/knowledge_tracing/akt/context.py#L169)|Vẫn cần `execution_enabled`, approved/run/phase/config hash/reference/caps và exact identity. CUDA identity cần synthetic scope, context SHA, nonempty input hashes, limits hợp lệ; equality với freshly calculated identity mới quyết định. Gate PASS không cấp quyền chạy.|
|Unknown phase bị rơi vào pilot?|[config.py:88](../../src/knowledge_tracing/akt/config.py#L88), [runner.py:99](../../src/knowledge_tracing/akt/runner.py#L99), [runner.py:239](../../src/knowledge_tracing/akt/runner.py#L239), [runner.py:811](../../src/knowledge_tracing/akt/runner.py#L811)|Whitelist config/CLI; cohort tags và loader có explicit unknown-phase reject; worker dictionary dispatch cho3bounded phases. `_run_phase` còn kiểm expected phase trước loader.|
|Context paths/input membership?|[context.py:103](../../src/knowledge_tracing/akt/context.py#L103)|Relative paths phải trong trusted root, chặn traversal/glob/Windows syntax/protected/private paths; runtime/Gate2/lock có vùng riêng, inputs phải chung dataset root dưới AKT. Exact input hash membership,1..64Parquets,128MiB actual hash budget và synthetic marker được kiểm. Chưa atomic read như P2.|
|Marker có chứng minh data origin không?|[builder marker](../../scripts/akt/prepare_synthetic_context.py#L166), [context marker check](../../src/knowledge_tracing/akt/context.py#L151)|Marker là declaration, không certificate chống caller cố ý chép realdata rồi gắn nhãn dummy. Builder cụ thể tạo dummy bits/8users/64rows với readback; không cấp auth/import model. Không biến arbitrary valid sidecar thành chứng minh nguồn synthetic.|
|CPU historical hash drift?|[config.py:34](../../src/knowledge_tracing/akt/config.py#L34), [authorization.py:186](../../src/knowledge_tracing/akt/authorization.py#L186)|Đối chiếu AST bằng standard library cho thấy `AKTConfig` và `config_hash` **không đổi** so `e4a44e9`; context sidecar không thêm dataclass field. Chưa xác minh lại mọi authorization artifact lịch sử. Validation mới ép inner fraction0,1; stored configs có khai field đã kiểm đều0,1.|
|CPU→CUDA resume hoặc thay data/budget?|[recovery.py:28](../../src/knowledge_tracing/akt/recovery.py#L28), [stable_inputs:71](../../src/knowledge_tracing/akt/recovery.py#L71), [validate_source:122](../../src/knowledge_tracing/akt/recovery.py#L122)|Semantic hash giữ phase/device/config resources; stable identity giữ context SHA/input hashes/CUDA limits/build/runtime/lock. Cumulative wall được kiểm. Tests certificate có CPU→CUDA/change-data/change-limits negatives; không phải actual CUDA optimizer/RNG resume proof mới.|
|CUDA unavailable có silently chạy CPU không?|[device_budget.py:4](../../src/knowledge_tracing/akt/device_budget.py#L4), [config.py:133](../../src/knowledge_tracing/akt/config.py#L133)|CUDA phase yêu cầu device CUDA; availability, đúng1visible device và memory tối thiểu được kiểm; không có CPU fallback trong budget setup. Hardware behavior hiện chỉ được mocked tests của batch mới mô tả.|
|Early setup failure bị resource-summary error che?|[runner.py:365](../../src/knowledge_tracing/akt/runner.py#L365), [runner.py:372](../../src/knowledge_tracing/akt/runner.py#L372), [test_cuda_budget.py](../../tests/akt/test_cuda_budget.py)|Context run reserve incomplete manifest trước setup trong try; non-pilot exception không gọi summary của empty samples. Original exception được re-raise; source test inject setup failure giữ error. Không chứng minh mọi filesystem failure lúc ghi manifest không thể che exception.|

## VRAM, runtime và actual execution còn thiếu

`configure_cuda_budget` gọi `set_per_process_memory_fraction` và reset peak stats; snapshots kiểm allocated/reserved/max counters với cap64MiB..2GiB. Code trả scope **PyTorch allocator only**, không total driver/process GPU memory hoặc cloud billing limit. Đó là framing phù hợp. Không nâng thành driver hard cap, isolation với process khác, spend cap, OOM-proof, hoặc representative training throughput. Local CPU `FakeCuda` không đo CUDA allocator thực.

Runner wiring có context paths cho preflight/Gate2/identity/loader và truyền context file+SHA sang child. Tuy nhiên **chưa có actual main-worker Linux/CUDA execution được review này nghiệm thu**: cần isolated Linux `.venv`/origin/lock và runtime report đúng device; current Gate2 source/lock phù hợp; actual bounded CUDA setup→loader→train/validation→reload/export; failure negatives/VRAM telemetry; cùng-context fresh-process recovery nếu muốn claim đó. Old Colab kitv12 synthetic proof không tự chứng minh source GPU07 hiện tại hoặc Modal Volume/hard-kill durability.

Public CLI kiểm auth/context trước spawn và `_execute` kiểm lại trước import heavy runner. Direct Python import `runner` đã import Torch từ đầu; vì vậy câu “reject trước Torch import” chỉ áp dụng lightweight CLI path được nêu, không mọi Python API.

Builder tạo config `execution_enabled=false`, không authorization và không đọc nội dung runtime/Gate2/lock. Các reports được tham chiếu có thể chưa tồn tại ở preparation stage; authorization/preflight thật phải kiểm sau. Trần preparation2steps nhỏ hơn config CUDA smoke tối đa20steps; preparation inventory không phải approval tăng lên20. Allocation thực phải ghi exact configured/approved caps, không suy từ schema maxima.

## Negative constraints và cách dùng review

- Không xác nhận Gate18 PASS, actual CPU2-step hoặc actual CUDA chỉ từ code/tests đang đọc. Không test rerun trong review.
- Không có đầy đủ end-to-end test context parent→child→actual Parquet CUDA của source mới trong evidence đã đọc ở lượt này; JSON/byte certificate và mocks phải giữ nhãn.
- Không approve realdata, full CV, Modal compute, training hyperparameters, S04/S05 hoặc scientific claims. CPU2-step dummy và CUDA là hai nghiệm thu khác nhau.
- Giữ inputs bất biến trong bounded smoke, record exact source/context/config/auth/input/output hashes; không dùng report này thay authorization. Các findings P2/P3 được báo parent trong khi Gate18 chạy; không có source/build edit để làm gate stale trong review.

## Source snapshot và kiểm read-only

Đã đọc các vùng liên quan trong14tệp chính dưới đây, cùng targeted baseline diff/AST và các stored config lines. AST check không import AKT/Torch hoặc model; chỉ đọc Git blob và parse source. Đây không phải chạy tests hoặc thực nghiệm mới.

| File | SHA-256 tại snapshot review |
|---|---|
|`akt/context.py`|`73455648b43212c23282f6fa2f417329f5d9f81b831f88aa8bbbfc546fffca39`|
|`akt/device_budget.py`|`79d6dff68f0cc36ec94c5f92097f5bdfe94f4f367386e989c03543d9a8dc4906`|
|`akt/config.py`|`6f972accc31a20a95cd2964042632ac39a8c89d08768d4c9932cac5fa7c59185`|
|`akt/authorization.py`|`e95c7928330d7353b4d52a7e59abe011c2cb8cc0e774c15f2baaa41aac9312e2`|
|`akt/watchdog.py`|`b94fd1c6468a440138b26be4cdcdefecfb1087805db9eac4d419be9b3663ac2e`|
|`akt/runner.py`|`a79dbcd8b5341eeddaf8a5606ed984209ef7786fdb8d70804f6619faf7ce2852`|
|`akt/recovery.py`|`93eed09fa9962a1c54bccda2ce9985317c20faeb7397758b652eb0a48709f900`|
|`akt/data.py`|`0f898de8edb17c188364839d9f44952071ec5c2c5bd507a13a4da99971242a94`|
|`akt/training.py`|`8eff1265e9fccb6488c6bfc0c6af9cda8c8ea68966a2b001752991de0db5805a`|
|`scripts/akt/prepare_synthetic_context.py`|`075d4f02857af1b6fdebd03338705b1ae071e013350fafe8d81692c4fb614915`|
|`tests/akt/test_context.py`|`82aa113e10ec029e70e423fbd0cb977aa4267d1956f8a8fc7e7d262d5e14a4da`|
|`tests/akt/test_context_recovery.py`|`daa989ab60308cb8d26356a119abc66e264e3deb3be1df0dcc4e7d5be6386842`|
|`tests/akt/test_cuda_budget.py`|`1210c26cdee9d9183a81ff643dfc278793a2d034623e5b1378055e4e93f13a5e`|
|`tests/akt/test_synthetic_context_builder.py`|`6b60ac89090aac3ab09bcfb3cf9565a998ce99b0ef0be026357f47713839dada`|

Các hàng `akt/...` là dưới `src/knowledge_tracing/`. Line anchors chỉ định vị source snapshot, không là khẳng định code host đã render GitHub anchors. Các path/JSON/link checks cho báo cáo chỉ xác nhận locator và bytes, không scientific validity.
