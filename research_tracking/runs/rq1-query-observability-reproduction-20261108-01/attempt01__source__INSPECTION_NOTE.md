# RQ1: phương án tái lập fixed-stream có quan sát query/item — 08/11/2026

**PLAN ONLY, chưa wrapper code hoặc model execution.** Có thể thu actual query identity trước `predict` mà không cần đổi phương trình/native source. Preview item được lấy từ **lần select trên bản sao vốn đã có**, sau predict; không gọi select thêm, không gán timestamp đầu vào cho select vì signature không có timestamp.

## Bằng chứng đã kiểm bằng static reads

- Run gốc: `research_tracking/runs/cpu-rq12-20261107-03/`; manifest completed, seeds20000..20002, steps120; 8output SHA khớp, gz trace SHA `22b065e8e0206403d2bcd41d175eeb1d686ed8bbf204c64f74d0e93d2aca0497`.
- Đếm trực tiếp stored JSONL: **3.240variant rows = 1.080logical (learner_id,event_id) keys ×3variants**, mỗi variant1.080rows; mastery vector28. Keys thực tế chỉ variant/event/learner/label/P/S/M/R/A, **không query qid/difficulty/timestamp hay preview item**.
- Historical runner SHA `402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45` khớp **nguyên bytes Git LF blob** `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a:scripts/research/run_cpu_diagnostics.py`. Đây là recover source, không recover metadata đã quan sát trong lịch sử.
- Current runner SHA `d8892fc3ce8d9c6f03c99a807c0efbd80844b292c77c835d0dceaa3a7a95657e` có thêm closed-loop mode. AST toàn fixed-profile body, bỏ riêng branch closed-loop mới, **identical** historical blob. `graph_controls.py` hiện đã đổi SHA; không chạy nguyên `run()` tail vì sẽ tạo lại matched graph không liên quan.
- Notebook `paper2/.../source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb` SHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`, `paper2_reference.py` SHA `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1`, diagnostics SHA `651da44e7f8e2ce94fc5733f8a962d6fb1a5776d08c8224fb86aab879ac24d95` và4simulator-input CSV hashes khớp run gốc. Không load/execute notebook definitions trong investigation này.

## Native signatures và call order

| API thực tế | Anchor source | Điều có thể ghi |
|---|---|---|
| `load_reference(*, estimator_edges=None, controller_edges=None)` | `src/knowledge_tracing/paper2_reference.py` | Chỉ AST definitions allowlist; source estimator/environment/controller riêng; không full notebook preprocessing |
| `persona_base_abilities(persona: str, seed: int) -> dict[str,float]` | Notebook cell9 | Giữ nguyên latent starts và RNG seed-offset; không sửa profile thành controlled ability intervention |
| `LatentStudentEnvironment.interact(self,cid,difficulty,timestamp,outcome_uniform,learning_uniform)` | cell9 | Gọi **một lần trước predict vòng variants**, như nguồn. Không reorder để tạo chronology mới; y chung cho3variants |
| `GAMKTPolicy.__init__(self,use_graph_context: bool)` | cell13 | False/True/full/empty packages giữ nguyên; empty vẫn có local adaptation |
| `GAMKTPolicy.predict(self,cid,qid,difficulty,timestamp)` | cell13 | Capture nguyên4args **trước delegate predict**, return probability không đổi |
| `CoverageAwareSelectorMixin.select(self)` | cell11 | Return đúng `(cid,qid,float(elo_difficulty))`; mutate selector counters/history trên **copy** |
| `mastery_score(self,cid)`, `is_mastered(self,cid)`, `ready_set(self)` | cells13/11 | Giữ đúng các calls nguồn để tạo S/M/R; observer không gọi thêm |
| `GAMKTPolicy.update(self,cid,qid,difficulty,timestamp,y,p_pred)` | cell13 | Delegate đúng một lần; sau đó original manual selector bookkeeping giữ đúng như loop |

Fixed loop thực tế: chọn qid bằng local seeded rng → environment.interact → từng policy predict → `copy.deepcopy(policy)` → `preview.select()[0]` → native ready/S/M/DecisionTrace/write → update → manual counters/recent_concepts/current_chapter. Predict/_context/_decayed_pi đọc existing states, không lazy state creation ở Paper2 simulator policy này; không nhầm với original Junyi API khác.

## Một API observer đề nghị, không sửa gated source

New isolated reproduction driver chỉ chạy **verified historical fixed-profile AST block**, không gọi whole `run()`/retention/counterexample/rewire tail. Snapshot historical LF blob và kiểm402d… trước compile; không sửa source file, notebook hoặc historical bundle. Native `load_reference` giữ nguyên.

1. Control pass: execute block với original native policy factories, same seeds/profiles/steps; fresh namespaces/environment/policies. Thu legacy trace projection,18comparisons, final policy/environment state fingerprints, local RNG state/uniform byte hashes sau mỗi profile. Không native predict/select calls thêm.
2. Observed pass: cùng block/same input bytes/same starts, chỉ policy factory của **shallow copied namespace mapping** trả transparent `PolicyObserver(delegate,variant,context,sink)`. Native class/method functions và `__globals__` không bị sửa.
3. `predict` proxy chụp actual `(cid,qid,difficulty,timestamp)` trước khi gọi native method đúng một lần. `__deepcopy__` thực hiện native delegate deepcopy đúng một lần, observer copy đánh dấu preview và dùng cùng event key. `preview.select` delegate đúng một lần, lưu nguyên tuple trả về rồi trả lại chính tuple; không chọn lại question từ guessed concept/ability.
4. `__getattr__` delegate attributes/methods; `__setattr__` phải delegate non-observer attributes để manual `current_chapter` bookkeeping cập nhật native object, không shadow trên proxy. Mutable Counter/deque references vẫn là native object. Observer chỉ serialize/copy primitive metadata, không gọi RNG/model scoring.
5. Trace sink giữ nguyên legacy line và ghép sidecar theo existing key `(seed/profile,event_id,variant)`; checksum canonical legacy row bind P/S/M/R/A/y. Missing/duplicate/order mismatch phải fail, không repair/drop row.

**Sidecar schema tối thiểu:** event key/variant; query concept/qid/difficulty, actual timestamp ISO+ns, capture phase `before_delegate_predict`; preview concept/qid/difficulty, phase `after_native_preview_select`; explicit `preview_is_served=false`, `preview_timestamp_argument=null`; context query timestamp có thể ghi riêng với nhãn context. Không invented IDs, calibrated/mastery probability, oracle confidence hoặc timestamp đưa vào select. Không đọc oracle outcome fields ngoài y đã có trong legacy trace.

Header bind policy identity/parameters: native `GAMKTPolicy` definition SHA, selector definition SHA, original parameter values/flags và estimator/controller/environment graph identities; preview delegate phải cùng native class/parameters với original ngay lúc deepcopy. `select(self)` không nhận qid/difficulty/timestamp từ caller: bộ query args của `predict` và tuple item **do selector trả về** là hai identity riêng. Không truyền current query vào selector để ép parity. Wrapper không sửa namespace globals hoặc chọn lại question.

## Parity/acceptance trước khi gọi đây là evidence mới

- Unit spy/dummy checks: delegates đúng một predict/select/update/deepcopy; wrapper callback không đổi delegate state/RNG; preview count mutations không vào original; non-observer attribute assignment không bị shadow; mismatched/duplicate queries và missing preview bị reject. Không cần chạy paper để test wrapper plumbing.
- **Exact legacy value parity**, không tolerance nới: control và observed đủ3.240rows, đầy đủ keys/labels/P/S28/M/R/A, bằng stored historical JSON values; set fields canonicalized đúng native serialization, finite floats so exact float value/bit representation khi cần.18comparisons phải khớp. Gzip mới không cần cùng compressed bytes/header/mtime; không gọi khác gzipSHA là trace divergence.
- Control vs observed final native state/environment snapshots và local RNG state/uniform hashes khớp từng9seed-profile runs. Chỉ instrumentation mới, không thêm RNG draws hoặc model calls. Historical RNG/state không được lưu nên không claim đối chiếu directly với lịch sử những trường đó.
- Trong **observed reproduction**,3variants có exact same query tuple/y tại từng1.080logical events; đủ3.240actual query captures và3.240preview tuples. Nếu source/dependency drift khiến legacy parity fail thì giữ failed attempt, STOP/no interpretation/no tolerant fallback.
- Runtime/source/input hashes trước/sau, method-definition provenance, exclusive output/log/JUnit; cumulative CPU budget<=120s, 0optimizer, CUDAhidden/.venv. Hai replay passes tối đa6.480variant predictions/updates nhưng chỉ là lặp lại cùng1.080keys; **không tăng independentN**. Chưa chạy pass nào.

**Đơn vị và giới hạn:**3seed families ×3profiles ×120steps =1.080keys, không3.240independent samples. RNG item stream reset cùng seed giữa profiles nên cross-profile inputs có thể chung; không coi9profiles là9independent seeds hoặc causal ability effect. New query metadata chỉ là quan sát của reproduction mới. Dù legacy projection khớp, không chép ngược metadata vào historical trace hoặc tuyên bố trace cũ đã independently log full identity. A vẫn preview, không served action; không closed-loop learning efficacy, calibration fit, CI hay final RQ completion. Không real Junyi/Holdout, no new graph generation/model methodology.

**Quyết định cần parent review trước code:** cho phép isolated AST-block replay + transparent observer/control parity như trên. Bản này chỉ là inspect note/source inventory trong ignored workdir; chưa implementation, model/simulator rerun hoặc archive mới.
