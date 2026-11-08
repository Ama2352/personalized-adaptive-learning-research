# RQ1 next contrast — read-only source review trước tính số mới

## Verdict

**Có thể dùng fixed-stream đã lưu để tính full graph_package − empty_graph_package, với estimand có điều kiện rõ ràng:** thay **estimator edge set** từ rỗng sang source graph trong **cùng enabled Graph-GAM package**, trên cùng observed history/query/label. Không có thay đổi độc lập về nonedge parameters, item-feature construction, initialization hoặc package flags. Các local pathway realizations có thể đổi như downstream consequence của graph-dependent state updates; vì vậy không gọi đây là direct-logit-only, individual edge-quality hoặc closed-loop learning-benefit effect.

Chưa có contrast metrics mới được tính trong review này. Chỉ đọc source, archived schemas/provenance/headers và kết quả đã công bố. C13/C14/bundles/draft giữ nguyên.

## Đã tìm duplicate ở đâu?

- `rq1_transition_evidence_20261108.md`, `rq1_score_vector_diagnostic_20261108.md` và `rq1_query_observability_reproduction_20261108.md`: các bảng candidate đều full−graph_free hoặc empty−graph_free; chưa có joint full−empty P/S/M/R/full-preview contrast.
- CPU09 factorial signal/parent-adaptation on/off, local off, seeds21000… là intervention/stream khác; không thay cho contrast package-enabled ở pilot20000… này.
- C14 closed-loop trajectory histories có thể diverge; không lấy ordinal rows của nó để tính paired prediction losses. Đây chỉ dùng fixed stream.

## Source facts: đâu thật sự thay đổi?

| Thành phần | Full / empty trong source | Evidence |
|---|---|---|
| Constructor |Cùng `GAMKTPolicy(True)`; cùng graph/name/parameter flags |Archived `historical_runner.py` fixed-profile block; parity headers |
| Class/initial state |Cùng class definitionSHA `99d10d26d5c3eee9bf48c6530c8a7ed5ea885d1585750316dd6d0db41f8925f1`; full/empty initial state fingerprint `c80ce36865fce461a66603587649295d2d1b6638cdf97cef932f9a70a9bf443d` |C13 `parity.json`, `control/observed.policy_headers` và state fingerprints; cell13 deterministic MemoryState/__init__ |
| Estimator graph |Full source edges / empty edges; cả hai giữ28node IDs/order, không drop isolated nodes |`load_reference(estimator_edges=[])`, ConceptDAG cell5; header graph hashes |
| Environment/controller graph |Giữ source graph. Loader rebind `CoverageAwareSelectorMixin` từ **controller scope**, không empty estimator scope |`paper2_reference.py`87–92; env/controller/full estimator hash `2466c94b49de0ccbf4aa4bbfbdaddfbc7835c7cb301e7f4d0b5342676a44f40f`; empty estimator `c1bedcd65d0be9b6323bd3ea85d0ee68ceeb6345039b7ad7df6181b4cd13115a` |
| Item/concept features |Cùng node/chapter/level/difficulty encoding, normalization/FEATURE_DIM; `item_feature` không đọc edges |Cell7 item_feature; namespace construction giữ CSVs/node order/chapter maps; concept probes cùngMASTERY_ELO |
| Parent input pathways |Edges đổi parent signal/uncertainty/deficit; q_task và decay dùng summary đó |Cell13 `_graph_summary`, `_context`, `_decayed_pi`, predict/update/mastery_score |
| Nonedge local code |Đều active vì use_graph_context=True. Struggling dựa attempts/recent outcomes nên cùng fixed observed history; times_forgotten có thể khác do state đã graph-dependent |Cell13 `_context`/update. Không giả rằng realized local decay luôn giống nhau |
| Preview/tie bookkeeping |Preview trên deepcopy, không thay actual next logged item. Native counters/recent/current_chapter sau update gắn cùng logged cid/qid ở mọi variant |Fixed-profile runner after-update assignments; C13 observer |

`graph_free` là `GAMKTPolicy(False)`: không chỉ empty edge input, vì còn tắt local branches. Do đó full−GF cũ là package contrast; full−empty mới mới là graph-edge-information **conditional on package enabled**. Nó vẫn tổng hợp signal, parent adaptation và propagated internal-state differences, không nhận diện từng pathway riêng.

Nguồn notebookSHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`; loaderSHA `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1`. Fixed branch gốc đã tìm lại ở Git `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a`, runner rawSHA `402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45`; C13 đã exact-reproduce legacy values. Không mang limitation missing-original-runner của **closed-loop** sang fixed branch đã recover.

## Chính xác saved rows và target identity

Primary bundle: `research_tracking/runs/rq1-query-observability-reproduction-20261108-01/`.

1. `observed_legacy.jsonl.gz`: P (`probability`), S (`mastery`28scores), M (`mastered`boolean set), R (`ready`), A concept (`action`), y (`correct`).
2. `observed_query_sidecar.jsonl.gz`: actual before-predict `query` và actual full item `preview`; join legacy bằng `(variant,learner_id,event_id)` và `legacy_row_sha256`.
3. `parity.json` và `historical__manifest.json`/`historical__source_provenance.json`: source/state/RNG/query equality certificates. `control_legacy.jsonl.gz` và `historical__traces.jsonl.gz` có thể dùng exact-value validation, **không append như samples mới**.
4. `historical__comparisons.json`: hai contrasts cũ để consistency-check metric formula; không lấy changed-count subtraction để suy full−empty.

Pair key không gồm model: `(seed,profile,event_id)`, với `learner_id=f'{seed}-{profile}'`; `event_id` là string step0…119, không invented source_row. Expected complete population đã ghi **1.080keys =3seed families×3profiles×120steps**, mỗi variant đúng một row/key. Dùng full và empty rows, GF chỉ làm reference/decomposition/negative checks.

Trước tính metrics, phải verify **tất cả keys**, không intersection/drop rows: actual query `(concept,question,difficulty,timestamp_iso,timestamp_ns)` và y exact bằng nhau giữa cả ba variants; complete steps/order bảo đảm observed prehistory common. Join new metadata với exact historical legacy projection, không backfill original gzip. C13 đã certified cùng query+y ở1.080keys; analyzer vẫn phải enforce contract.

Full preview tuple là `(concept,question,difficulty)`, `preview_is_served=False`, `preview_timestamp_argument=None`. Không dùng current query như preview item, hoặc timestamp query như argument của select. S/M/R/A là observations trước update sau current prediction; M dùng stored boolean, không S≥0,5. Query/y/profile history khác nhau giữa personas không là controlled ability effect.

## Cached analysis đã được root cho chuẩn bị; chưa được dispatch trong review

- Metrics frozen: paired P changes/absolute delta; LL/Brier theo existing diagnostic clip1e−15; S-vector event/concept changes; stored M event-change và concept symmetric-difference crossings; R set-change/Jaccard; full/concept/question/difficulty preview changes. Units riêng: snapshot pairs1.080, score/concept decisions30.240, preview tuples1.080; không event-as-independent-N.
- Giữ pooled, cả3profiles, cả3seed blocks và9seed-profile trajectories; report mọi positive/negative delta. Không p/CI/calibrator mới/threshold search, không favorable metric or group selection. Three seed families reused, new independent N=0.
- Trên **cùng supported rows** và giống aggregation: `DeltaLL(full−GF)=DeltaLL(full−empty)+DeltaLL(empty−GF)`; tương tự Brier. Đây là exact algebra, floating arithmetic chỉ check residual ở tolerance1e−12 đã freeze. Baseline cancellation không là unique attribution/causal mediation; decomposition phụ thuộc thứ tự control.
- Không trừ P/S/M/R changed counts; event sets có overlap. Preview equality của empty−GF đã lưu có thể làm transitivity check sau joint validation, không cần gọi model lại.
- Nếu missing/duplicate/mismatched query-label/source/provenance: STOP toàn analysis, không đổi common population. Nếu GF certification không đủ: bỏ decomposition, ghi coverage reason; không đổi full−empty target population để cứu kết quả.

Không thiếu counterfactual mới để tính **total edge-set contribution within this package**. Nhưng signal-only/path-specific attribution cần thêm matching pathway variants hoặc full-state probes chưa nằm trong saved rows; graph-quality inference cần matched nonempty graph controls. Những mục đó không được thực hiện trong read-only task này. Next chỉ là bounded cached arithmetic≤10s sau source/plan pin gửi root, không rerun model/teacher/seeds hoặc sửa historical artifacts.
