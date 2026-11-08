# Hợp đồng quan sát closed-loop Paper2 — chỉ đọc nguồn, 08/11/2026

**Chưa chạy test, model, simulator hoặc replay.** Có thể ghi M/R và full served tuple vốn đã được tính bằng read-only call/return frames của native methods, không gọi lại predictor/selector/mastery/ready/RNG. Đây là đề xuất instrumentation cho cùng pilot, không nghiên cứu xác nhận mới. Parent cần review exact source/caps/parity trước quyết định chạy; authorization safe bounded local engineering không tự đổi thành approval methodology hoặc mặc định cần thêm human approval.

## Nguồn và giới hạn revision

Historical run `cpu-closedloop-20261107-01` có3seeds20000–20002,PG/PY/PYH,3variants,120steps;8output SHA đã kiểm. Notebook353f487a…/14definition SHA và4simulator-input byte SHA khớp provenance. Không parse prediction traces hoặc execute notebook trong bước chuẩn bị.

**Chưa recover exact whole runner a585d5f3… mà manifest lịch sử ghi.** Git `04c36169` và current physical file đều d8892fc3…; function `closed_loop_pilot` lines31–65 có AST giống nhau. Git e4e6… là fixed-only402d…, chưa có function này. Hash lookup trong tracking/docs chỉ tìm a585… trong manifest, không tìm snapshot bytes. Vì vậy chỉ đề xuất **candidate function pinned current d889/04c361**, không tự gọi exact historical source/revision. Nếu replay được parent cho phép, full legacy parity là gate bắt buộc; parity không thay source identity. Inventory/excerpts/line anchors ở [hồ sơ nguồn](CLOSED_LOOP_OBSERVABILITY_CONTRACT.sources.json).

## Thời điểm thật của nguồn

Native loop: tăng timestamp → `policy.select()` → `policy.predict(actual tuple,timestamp)` → `environment.interact` với uniforms đã có → ghi legacy event → `policy.update(y,prediction)` → append concept. `select` mutate counters/recent/current_chapter trước predict; do đó M/R trước selection và P sau bookkeeping phải có phase labels riêng, không gộp thành cùng instant policy snapshot hoặc mediation funnel. Selector không nhận timestamp; context time không phải selector time argument.

Cell11 `ready_set` gọi `is_mastered` cho đủ28nodes để tạo unmastered, rồi kiểm parents. `select` gọi ready_set đúng một lần, có thể thay candidates bằng anti-drill escape; R returned ban đầu không nhất thiết là final eligible candidates. Sau đó selector chỉ gọi `mastery_score` trên balanced candidates và trả actual `(concept,question,difficulty)`. Đây là item đã phục vụ trong simulator, không preview trên deepcopy. Cell13 `is_mastered` dùng theta và pi_task theo source; không threshold P/S hoặc dùng cached/oracle state thay quyết định.

## Instrumentation tối thiểu đề nghị

Dùng scoped `sys.setprofile` call/return callback trong child, lọc exact native function code objects/module binding. Không thay source code, class, method globals hoặc policy state. Nếu child đã có profiler thì STOP, không overwrite callback có sẵn. Callback chỉ serialize primitive values/array bytes; không invoke native scoring, selector, environment snapshot hoặc RNG methods. Không build framework mới.

| Hook nguồn đã có | Ghi từ frame/return value | Guard |
|---|---|---|
| `select` call | Raw policy state trước selection; timestamp context từ enclosing loop, event/variant keys | Không đọc/ghi oracle để định nghĩa M/R; phase trước bookkeeping |
| `is_mastered` return trong `ready_set` | `(cid,bool)` của các calls có sẵn; đủ28nodes ở đầu ready_set | Preserve ordered/repeated returns; không gọi thêm để fill missing |
| `ready_set` return | Ordered R do nguồn trả | Giữ riêng R và candidates/anti-drill |
| `select` return | Full actual tuple; locals final `candidates`,`balanced`; policy state sau bookkeeping | Không gọi select lần2; missing locals/code drift → STOP |
| `mastery_score` returns đã có | Chỉ scores của candidates thực sự evaluated | **Không có full S28** nếu nguồn không tính; không fill bằng new calls |
| `predict` call/return | Actual query tuple/time và P, đúng một native call | Trước interact/update current y |
| `update` call/return | Actual y/P args và policy state sau native update | Một native update; legacy outcome/current y không bị reorder |
| `closed_loop_pilot` return | Uniform array bytes/hash; existing final snapshots/aggregates | Không gọi thêm snapshot/RNG; không claim final Generator state |

Để giữ final state fingerprints cả27variant trajectories mà control không cần profiling model methods, cả hai passes có thể dùng **cùng constructor-factory registry** trong shallow copied scope maps: factory gọi chính native constructor một lần, giữ reference của object, trả nguyên native instance. Không subclass/override method/code/globals; function AST và native code giữ nguyên. Sau function returns, chỉ serialize `vars`/dataclass primitives/arrays đã có của retained native policy/environment. Environment state fingerprint chỉ kiểm instrumentation không đổi dynamics; không dùng latent theta làm reference mastery/calibration mới. Confirm factory registry không đổi constructor arguments/identity/return count trước model phase.

Control không observer profile; observed có callback. Function được compile một AST node, globals chỉ dependencies cần thiết; không execute whole `run`, retention/counterexample/matched-graph tail hoặc full notebook preprocessing. Source/input/method hashes phải exact trước/sau. Existing fixed-stream wrapper không tự dùng lại vì closed selector chạy trên actual policy và native self-internal calls không đi qua fixed proxy.

## Parity và nguồn lực trước khi diễn giải

- Giữ nguyên seeds/profiles/variants/120steps, dynamics/graph packages/controller/72h gaps và same step-indexed uniforms. Không graph generation, new seed/model, corrected simulator, CI hoặc hyper selection.
- Mỗi pass phải exact đủ3.240legacy events và27outcome aggregate rows so với historical parsed values, bao gồm outcomes/labels/P/actions/timestamps/net/retained gain/coverage; không tolerance, drop/repair rows hoặc compressed-gzip byte parity claim.
- Control vs observed phải khớp final policy/environment primitive-state fingerprints cho27trajectories và9uniform-array byte hashes. Source dùng temporary `default_rng(seed).random`; Generator không được giữ, nên không có final local RNG state để đọc/claim. Không thêm RNG calls/draws. Native predict/update/interact counts mỗi loại6.480 tối đa cho hai passes; new independent N=0.
- Sidecar observed có3.240rows, explicit28M decisions và raw R đã return, final candidates, full served tuple, phase-tagged P/state/y; mismatch/missing decision/node/key hoặc code identity phải fail, không gọi bù. Post-update `currently_mastered` cache không thay preselection M.
- Đề xuất bounded child cumulative120s gồm spy checks/control/observed;0optimizer,CPU/.venv,CUDAhidden,OMP/MKL/OpenBLAS2,exclusive attempt logs/JUnit/source before-after. Parent review cap trước run. Nếu legacy parity/source guard fail, giữ failure và STOP; không rút ngắn pilot, chọn seed tốt hoặc nới comparator để pass.

## Claim được phép và còn thiếu

Nếu accepted, new metadata chỉ thuộc reproduction; không backfill historical trace. Các graph variants có thể phục vụ items khác nhau nên histories/labels không còn same-target; không áp fixed-stream paired prediction estimator lên closed loop. R/candidates/served tuple được quan sát sẽ cho phép mô tả đường đi nguồn, chưa calibration, causal mediation hoặc learning benefit. Full S28 chưa được native closed loop tính nên vẫn thiếu; reference mastery/calibration/interventions và independent evaluation vẫn là protocol decisions riêng. Không mở CPU09/10 confirmatory matrix bằng hợp đồng observer này.
