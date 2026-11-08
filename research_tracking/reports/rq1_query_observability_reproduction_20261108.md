# RQ1: tái lập fixed-stream với query và full item preview — 08/11/2026

**Tái lập có observer đã giữ exact toàn bộ P/S/M/R/A/labels của pilot lịch sử, đồng thời ghi được query thật và item preview đầy đủ.** Trong reproduction mới,22/1.080 full-preview tuple differences của full graph package đúng bằng22concept differences đã biết; không phát hiện thêm item changes ẩn khi concept giữ. Đây là kiểm quan sát trên cùng pilot, **không thêm independentN**, không backfill metadata lịch sử hoặc chứng minh causal learning benefit.

Bằng chứng theo [bundle observability](../runs/rq1-query-observability-reproduction-20261108-01/README.md). [Báo cáo transition trước](rq1_transition_evidence_20261108.md) và [score-vector analysis](rq1_score_vector_diagnostic_20261108.md) vẫn mô tả trace cũ thiếu item/time; chúng không được sửa thành dữ liệu đã log metadata. Report này phân biệt rõ source reproduction mới với historical observation.

## 1. Đã tái lập chính xác điều gì?

Pilot `cpu-rq12-20261107-03` dùng seeds20000,20001,20002 × profilesPG/PY/PYH ×120steps. Có **1.080logical seed-profile-step keys**, mỗi key có3variants (`graph_free`, `graph_package`, `empty_graph_package`), tức **3.240rows/pass**. Không coi3.240rows là independent samples hoặc9seed-profile configurations là9independent seeds.

Historical runner raw Git LF blob tại commit `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a` khớp manifest SHA `402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45`. Native notebook SHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`,14definition hashes, loader/diagnostics và4simulator-input CSV hashes khớp lịch sử. Current runner có thêm closed-loop code nhưng fixed-profile AST body identical. Driver chỉ compile fixed-profile body từ historical blob đã kiểm hash; **không chạy whole notebook hoặc tail retention/counterexample/matched-graph generation**.

Hai passes cùng source/inputs/seeds: control dùng native policy objects, observed dùng transparent observer. Mỗi pass có3.240legacy rows và18comparisons **exact bằng historical JSON values**, gồm binary64 float identity, không tolerance fallback. Control/observed còn có cùng9initial/final policy-state, environment, uniforms và final local-RNG fingerprints. Initial policy flags/parameters được bind bằng native class/selector source hashes và state hashes. Không monkeypatch native method code/globals, đổi graph/package flags hoặc RNG draws.

**Execution thực tế:**12spy tests PASS,0fail/error/skip, rồi cả control/observed PASS ngay attempt đầu. Reproduction child63,256971giây; toàn controller gồm tests/imports71,995901giây trong cap120. Có6.480native prediction/update calls và2.160environment interactions của **hai lần chạy cùng pilot**, 0optimizer steps. Không failed attempt hoặc fake RED. Logs/JUnit/source snapshots được giữ. Analysis tiếp theo chỉ đọc artifacts, không gọi lại model/RNG.

## 2. Metadata lấy trực tiếp ở đâu?

Native `predict(self,cid,qid,difficulty,timestamp)` được proxy ghi nguyên arguments **trước delegate call**. `copy.deepcopy(policy)` vẫn copy native delegate đúng một lần. Native `select(self)` trên copy trả tuple `(concept,question,difficulty)`; observer ghi chính tuple đó, trả lại nguyên tuple và không select lần thứ hai. Native ready/mastery/score calls giữ nguyên; non-observer attribute assignment như `current_chapter` delegate về native object.

Sidecar3.240rows lưu actual query concept/question/difficulty/timestampISO+ns, preview concept/question/difficulty và capture phases. Query/update arguments, y và p_pred được kiểm pairing trước native update. Legacy row được chụp trước update; sidecar được hoàn tất sau update thành công, không đổi thời điểm các giá trị đã capture.

**Select không nhận timestamp.** `preview_timestamp_argument=null`, `preview_is_served=false`. Không gán context query time thành time input của selector, không tạo questionID từ concept/seed, không coi preview là item đã phục vụ. Random fixed-stream query và policy preview là hai item identities khác nhau. Source-order `environment.interact` trước vòng policy predictions vẫn giữ nguyên; current y chỉ vào policy khi update như nguồn.

P là scalar correctness của actual current query. S là source mastery-score vector28concepts; M là source boolean `is_mastered`; R là ready membership; A là concept preview ở legacy trace. S không được nâng thành calibrated/latent mastery, không fit calibrator mới. Full item preview ở đây được định nghĩa đúng tuple mà `select` trả: **(concept,question,difficulty)**.

## 3. Kết quả item-level, toàn bộ paired population

Mỗi comparison có1.080pairs; mỗi profile360pairs. P_same/P_changed dùng exact parsed binary64 equality, không near-equality. Denominator trong cột cuối là **số P_same rows** của profile, không toàn360.

| Candidate vs graph_free | Profile | P_changed | Concept changed | Full tuple changed | Question changed | Difficulty changed | P_same/full tuple changed |
|---|---|---:|---:|---:|---:|---:|---:|
| graph_package | PG |322/360|20/360|20/360|20/360|0/360|1/38|
| graph_package | PY |321/360|2/360|2/360|2/360|0/360|1/39|
| graph_package | PYH |321/360|0/360|0/360|0/360|0/360|0/39|
| graph_package | pooled |964/1.080|22/1.080|22/1.080|22/1.080|0/1.080|2/116|
| empty_graph_package | PG |10/360|0/360|0/360|0/360|0/360|0/350|
| empty_graph_package | PY |13/360|0/360|0/360|0/360|0/360|0/360|0/347|
| empty_graph_package | PYH |14/360|0/360|0/360|0/360|0/360|0/360|0/346|
| empty_graph_package | pooled |37/1.080|0/1.080|0/1.080|0/1.080|0/1.080|0/1.043|

Full package có **944/964 P_changed rows giữ nguyên toàn preview tuple**, mạnh hơn phát biểu chỉ giữ concept trong **reproduction này**. Hai P_same/full-action-changed rows vẫn tồn tại, một PG và một PY; không coi scalar P của current query là toàn bộ policy scoring state hoặc nguyên nhân đủ của action preview.

Trong cả hai comparisons, **same concept nhưng different full tuple =0**. Difficulty giữ ngay cả ở22rows chọn concept/question khác; cùng numeric difficulty không làm chúng thành cùng item. Kết quả0additional item changes là quan sát của bank/selector/histories này, không equivalence proof cho mọi scenario. Empty package có37P changes nhưng0full tuple changes; nó vẫn bật adaptation local nên không tự là edge-only effect hoặc proof graph neutral.

`sidecar_event_flags.csv` giữ đủ **2.160comparison rows**, full/reference preview tuples và exact flags; `sidecar_analysis.json` giữ pooled, cả3profiles và9seed-profile breakdowns, cùng first examples deterministic. Không chọn positive subset, không CI/p-value hoặc inference nhân quả.

## 4. Shared queries đã được kiểm trong reproduction

Tại mỗi1.080logical keys, cả3variants có **cùng actual query tuple và label**. Đây là kiểm trực tiếp từ trước-predict captures, không suy từ learner/event keys. Hai passes giữ mọi legacy observable như lịch sử và cùng RNG/native-state fingerprints trong runtime mới.

Cross-profile query identity cũng được kiểm: PG–PY, PG–PYH, PY–PYH mỗi pair **360/360** query tuples exact giống nhau, phù hợp source reset local rng theo cùng seed. Labels/histories/profile initialization vẫn có thể khác; không coi profiles là controlled causal-ability intervention hoặc independent replicates. Đây là paired descriptive pilot với3seed families đã dùng trước.

Historical trace không có query/time/full preview fields; không thể đọc lại những trường chưa được log. New sidecar **chỉ thuộc reproduction mới**, dù legacy projection exact. Không sửa historical gzip, không append new fields vào bundle cũ, không gọi metadata mới là historical direct measurement. Gzip hashes mới khác do file headers/mtime/name; so parity ở canonical parsed values, không giả compressed-byte identity.

## 5. Preservation và giới hạn

Historical8outputs được kiểm SHA trước/sau model phase bằng source-bound assertions và đối chiếu lại khi archive. Snapshot historical runner giữ402d… đúng bytes. Codeobserver/driver/tests/plan có before/after SHA và snapshot trước execution; native definitions/input bytes không thay đổi. Bundle giữ control/observed legacy streams, actual query sidecar, parity/state/RNG hashes,12spy tests, logs/JUnit, analyzer/flags/counts và copy inventories trước/sau.

Không real Junyi/Holdout, no new graph generation, optimizer/GPU/cloud/install hoặc sửa gated scripts/root models/current AKT kit. Không thêm learner/seed family độc lập, không tái lập bảng paper hay closed-loop served actions, không dùng oracle confidence/calibration hoặc suy learning benefit. Giá trị mới là **quan sát được shared queries và full returned preview tuple trong same-source reproduction**, với biên giới thống kê và lịch sử giữ nguyên.
