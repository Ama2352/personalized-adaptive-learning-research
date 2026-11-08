# GKT recurrent candidate: engineering convention, chưa final baseline — 08/11/2026

**Full registered recurrent network theo recipe engineering đã duyệt đạt88 CPU tests; GKT baseline nghiên cứu vẫn chưa hoàn thành.** Có43 kernel cases đã có và45 cases mới, 0 failures/errors/skips, JUnit5,177giây/controller6,553361giây. Ba actual targeted invocations dùng tổng21,444325giây trong cumulative budget120giây, **0 optimizer steps**. Không dataset/Holdout, trainer, graph fitting, GPU/cloud hoặc cài dependencies.

Parent chỉ cho phép **concrete engineering candidate**, không adoption làm S05/final baseline hoặc exact author reproduction. [Đặc tả đã review](gkt_recurrence_specification_20261108.md) và [source map](gkt_recurrence_specification_20261108.sources.json) giữ nguyên bytes; recipe ID `gkt_static_recurrent_convention_v1`. Đây là bước sau [Batch A43cases](gkt_core_readiness_20261108.md), không sửa lại mức bằng chứng của bundle kernel trước.

## Source/API và phạm vi đã implement

Chỉ hai source/test mới: [recurrent.py](../../src/knowledge_tracing/gkt/recurrent.py) và [test_recurrent.py](../../tests/gkt/test_recurrent.py). Existing GKT core/config/package exports, root/shared/native AKT/protocol không sửa. Import candidate qua module `knowledge_tracing.gkt.recurrent`, không thay root exports.

Network đăng ký **26 parameter paths** trong PyTorch: concept/interaction embeddings; ba MLP self/out/in độc lập Linear→ELU→Linear→ELU; hai erase/add affines; sáu bias-free ChoGRU affines; common readout vector và per-node bias. Fixed adjacency là registered buffer, đồng thời đi qua fixed `StaticGKTKernel` hiện có; actual buffer/kernel digest được kiểm khi gọi.

Constructor bắt buộc config/binding/A và explicit recipe ID, MLP hidden width, `normalization='none'`, dropout0, zero-initial-state policy và `cho2014_reset_before_bias_free`. Message width phải bằng state width. Không tự chọn32hidden, optimizer, fit seeds hoặc learning rate. Dropout0/normnone là fixture recipe đã khai báo, **omission so với journal-BN training**, không faithful training reproduction.

- **Erase–add:** `m*(1−sigmoid(W_e*m+b_e))+tanh(W_a*m+b_a)`; mapping DKVMN `M_old=v=m,w=1` là repo convention đã được cho phép để thử kỹ thuật, không công thức tác giả GKT đã xác nhận.
- **GRU:** reset-before candidate `tanh(W_n*u+U_n*(r*h))`, không PyTorch reset-after. Bias-free là recipe literal Cho đã chọn, không tuyên bố journal implementation có cùng bias/reset.
- **Sparse update:** support answered OR incoming/outgoing nonzero, áp `where` **sau GRU**; disconnected state giữ nguyên dù biased add/gate có thể làm zero-message node đổi state. Empty graph chỉ update answered node.
- **State/API:** caller-owned hidden tensors/history counters, domain/vocab/node-order/graph/recipe binding; `initial_state`, `predict`, `observe`, `sequence` và registered-module `forward`. Không implicit learner cache hoặc learner-ID embedding.
- **Chronology:** sequence lấy score query_t từ H_t rồi mới observe đúng cặp `(i_t,r_t)`. Current answer không là input của predict. Padding có finite0 score placeholder, maskFalse, không update state/counter; không tính nó là eligible prediction. Unknown active IDs/multi-concept inputs bị reject, chưa có OOV/fitted coverage policy.

First target từ zero h0 có finite0,5 khi node bias ban đầu0; đó là random engineering network prior, không fitted correctness/calibrated mastery. History counts cho caller biết lượng prefix; candidate không chọn cold-target denominator hoặc calibration rule.

## Bằng chứng numerical/causal có thật

| Kiểm | Kết quả và giới hạn |
|---|---|
| Unary EA known answer | Gate weights0, biases xác định; khớp phép tính FP64 độc lập đến1e−12 |
| Cho reset geometry | Scalar reference2dimensions với non-diagonal hidden matrix; đúng reset-before và khác reset-after positive control |
| Full-network asymmetric direction | Hook tại erase input xác nhận messages `[27,5,34,0]` trên4nodes; self/out/in đều qua registered MLPs |
| Disconnected positive control | Node cô lập giữ byte-value trước update; tính trực tiếp cùng biased gate/GRU sẽ drift, chứng minh mask sauGRU có tác dụng |
| Sequence/continuation | FP32 và FP64 khớp manual predict→observe; prefix state nối suffix khớp full sequence |
| Label causality | B2/T12: đổi response hiện tại và mọi response tương lai không đổi score đến current timestep; đổi response trước có thể đổi future scores |
| Learner isolation | Batch so với từng learner, đổi response peer, permutation và fresh states độc lập; không BN/dropout peers |
| Padding/empty | Interleaved sentinel IDs/responses được ignore đúng mask; all-padding và zero-time sequence finite/no-op; history counts rõ |
| Immutability | Graph/IDs/labels/mask/caller hidden/counters không mutate; caller graph sau constructor thay đổi không đổi internal copy |
| Binding/guards | Domain/vocab/node order/unit, state/graph/recipe mismatch, internal buffer/kernel drift, invalid active IDs/response/mask/dtype/nonfinite đều reject |
| Full gradient paths | Backward qua **mọi26named parameter paths**, gradient hữu hạn/nonzero theo từng path; fixed A không requires-grad; không optimizer |
| CPU default-device trap | Constructor/helpers vẫn CPU với cả Static và Dense khi caller đặt default device meta; constructor và kernel calls có CPU context |
| Counter overflow | Caller-provided active max-int64 history counter bị reject trước update; padded max counter không thay đổi |

New fixtures tối đa2learners×12steps/4nodes, state/embedding/MLP widths nhỏ; không artificial research trajectories, simulator truth, metrics hoặc model global fit. Existing43cases giữ nguyên, bao gồm pure Dense kernel cases theo fixture lịch sử. Source/test giữ SHA trước/sau từng invocation. Numerical agreement trong fixture không author-code/checkpoint/metric parity hoặc CUDA validation.

## Ba actual trials, không dựng failure

| Trial | Actual outcome | Controller / source version |
|---|---|---|
| `parallel-gkt-recurrent-20261108-01` |86pass,0fail/error/skip; first suite invocation PASS |8,708018giây; recurrent `bff11350…`, tests `f2483fdf…` |
| `parallel-gkt-recurrent-20261108-02` |87pass,0fail/error/skip; thêm active history overflow guard/regression |6,182946giây; recurrent `eba87c2b…`, tests `24f1210d…` |
| `parallel-gkt-recurrent-20261108-03` |88pass,0fail/error/skip; thêm Dense/default-meta regression và CPU context ở kernel constructor mới |6,553361giây; recurrent `510195d7…`, tests `bb173f7d…` |

Giữa01/02, static self-review phát hiện extreme caller history counter có thể overflow; thêm guard và case rồi chạy lại. Sau02, independent reviewer phát hiện Dense constructor trong frozen kernel dùng ambient factory default, còn regression02 chỉ kiểm Static; candidate mới bọc kernel construction bằng CPU context và thêm Dense/meta positive case. Không sửa frozen kernel/config. Cả hai phát hiện đều từ static review, **không có fail-before invocation**, không mô tả chúng như actual RED. Không có failed targeted trial trong batch. Các bản86/87pass/source snapshots/log/XML được giữ nguyên, không ghi đè bằng source88pass.

Exact commands và snapshots ở `artifacts/akt/local-tests/parallel-gkt-recurrent-20261108-{01,02,03}/run.json`. Controller dùng project `.venv\Scripts\python.exe -B -m pytest tests/gkt -q -p no:cacheprovider`, exclusive basetemp/JUnit; env `CUDA_VISIBLE_DEVICES=''`, OMP/MKL/OpenBLAS2. Invocations02/03 nhận remaining timeouts111/105giây; cumulative controller21,444325/120. Implementation interface/recipe note được ghi trước code ở `artifacts/akt/local-tests/parallel-gkt-recurrent-20261108-preparation/implementation_note.json`.

Final frozen source SHA:

| Tệp | SHA-256 |
|---|---|
| `src/knowledge_tracing/gkt/recurrent.py` | `510195d71c1ddb743f747e78d7d874c04bb809931c5ec24ae6fe907fe53ec072` |
| `tests/gkt/test_recurrent.py` | `bb173f7dd9b7b8cf14dbe00dd5fc75097dc87c9f5a794d90e29fd670d26afdce` |

## Những việc chưa có

Đây là recurrent core cho documented recipe, **chưa required GKT comparator done**. Chưa trainer/epoch selection/selected-fit, fitted inference adapter, checkpoint/export/resume contract hoặc shared OnlineSession bridge. State binding kiểm identity/consistency, không attest caller graph/vocab train-only, label origin hoặc model đã fit. Không serialize random parameters thành fitted artifact.

S05 vẫn chờ node/item/multi-tag semantics, Dense/Transition/expert/learned graph, graph training provenance, capacity/history information matching, optimizer/seeds/splits/refit và allocation. S04 vẫn chờ score calibration/mastery/first-target/OOV/controller. BN omission và unary EA specialization chưa được adopt làm scientific method; muốn exact author recurrence vẫn cần nguồn đủ hơn. Engineering acceptance không chứng minh predictive efficacy, RQ completed, causal prerequisite graph hoặc learning benefit.

Independent read-only reviewer đã kiểm final source/fix và actual03 receipts: **PASS trong phạm vi engineering recipe**, không blocker còn lại ở phạm vi đó; reviewer không execute hoặc edit. Hồ sơ theo [bundle candidate](../runs/gkt-recurrent-candidate-engineering-20261108-01/README.md), giữ24source snapshots của ba trials, logs/JUnit, source/spec/provenance JSON và inventories trước-sau. Archiver chỉ đóng sau reviewPASS, không rerun model/test. Parent xử lý index/state/Git. Không fullGate/shared regression suite mới được chạy trong batch này.
