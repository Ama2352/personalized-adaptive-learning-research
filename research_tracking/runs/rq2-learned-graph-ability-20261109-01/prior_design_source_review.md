# Bước bằng chứng RQ2 tiếp theo — audit nguồn và hợp đồng triển khai

Ngày 09/11/2026. SOURCE-ONLY. Đã đọc nguồn, metadata, báo cáo và tính SHA bằng công cụ hệ thống. Không import/chạy Python, test, simulator, mô hình, Git hoặc dữ liệu Holdout. Không sửa production, protocol, tracking hay artifact đã đóng.

## 1. Quyết định đề nghị

Ưu tiên ngay **RQDIAG26 — điều kiện bất biến quỹ đạo cục bộ của Paper1 và ranh giới finite horizon/cap**. Đây là câu hỏi cơ chế mới, có thể giải thích vì sao hai graph cho cùng172lượt và cùng latent cuối dù re-entry0/2. Cần chứng minh điều kiện và vài phản ví dụ xác định qua public core hiện có. Graph agent đang sở hữu candidate tests riêng theo phân công ROOT. Note này sở hữu phần khoa học, không tạo test trùng.

Bước native có giá trị tiếp theo cho factorial RQ2 là **expert31 so learned31 × scalar ability × world prerequisite λ**, dùng graph Method24 đã fitted và loader đã kiểm với artifact thật. Có thể bổ sung18worlds vào36worlds controlled-ability cũ nếu kiểm tái lập đầu vào/nguồn đạt. Đây là đề xuất riêng chờ ROOT chọn allocation. Không chạy đồng thời hai hướng hoặc tự mở matrix lớn.

Điểm thiếu của RQ2 hiện tại không được lấp chỉ bằng thêm cached bins. Proposal tr.3 yêu cầu điều kiện chất lượng graph, history và đặc điểm người học. `05_EXPERIMENT_MATRIX.md` E04/E06 đặt factorial và expert/learned/noise riêng. Kết quả hiện có cho finite conditions, chưa đáp ứng toàn bộ mô hình, hai môi trường, mức noise, seed coverage và phép suy luận cuối.

## 2. Những gì đã được kiểm, những gì chưa có

| Bằng chứng | Phạm vi đã có | Khoảng trống thực sự |
|---|---|---|
| CPU09 `cpu-factorial-20261107-01` | 10seed×3persona×S/P on-off×λ0/.55,120worlds/14.400interactions | Persona thay cả latent/residual; graph flag bật/tắt hai pathways, không thao tác quality của cùng enabled package |
| `rq2-controlled-ability-prerequisite-20261108-01` | 3block21000–21002×a1000/1150/1300×full/empty edges×λ0/.55;36worlds/4.320returns; chung residual/U; high-ability null controls | Chưa learned hoặc graph sai cấu trúc trong ability factorial; ba block tái sử dụng, không independent validation sample mới |
| Matched graph `cpu-rq12-20261107-04-replay/matched_graph.json` | 31edges, một double-edge swap, giữ degree/chapter-pair counts | Script tạo graph sau các outcome loops, chưa dùng graph đó trong controlled-ability outcomes. Một swap không đại diện các mức delete/add/reverse0/20/50% |
| Method24 + typed consumer | TRAIN48×210,2.352solver calls lịch sử; learned DAG31 và31typed scores được consumer thực nhận | Chưa có outcome ability×learned graph. Predictive-stability score không phải xác suất cạnh đúng |
| Paper1 US42 engineering | B1/GA đều172returns,28estimated-mastered, cùng final-latent SHA; re-entry0/2 | Một witness và test local coupling chưa phải chứng minh bất biến all-completion hay phủ ranh giới finite H/cap |

Các controlled-ability means Ψ đã báo âm nhỏ ở a1000/a1150 và0 theo thiết kế ở a1300. Đơn vị Y/Δ/Ψ/Ω là mean **net latent theta/Elo points trên28concepts tại T41ngày**. Không thay bằng phần trăm mastery hoặc gross learning gain. Δgraph tại λ0 có thể khác0, kể cả high ability. Chỉ loại prerequisite multiplier không loại estimator/controller/challenge/initial-residual paths.

## 3. Paper1 — kết luận điều kiện có thể chứng minh từ source

### Mệnh đề cần ROOT review

Giữ cùng bank/tie rule, initial estimate/latent cho từng concept, chapter mapping, và cùng tape `u[c,n]` theo concept và số lần đã observe. Cho phép thay DAG/traversal order nhưng giữ literal controller/world. Giả sử cả hai branch đều thực sự hoàn thành mọi concept trong trần hiện có.

Khi đó, mỗi concept có cùng chuỗi cục bộ theo local-visit index, cùng số lượt đầu tiên đạt ngưỡng `N_c`, cùng terminal estimate/latent/item exposure và tổng số feedback `ΣN_c`. Global interleaving, chapter switches và re-entry vẫn có thể khác.

### Chứng minh nguồn

1. `simulator.py:144–158` dùng graph/chapter/global order để chọn concept. Sau khi concept được chọn, item key chỉ dùng estimate của chính concept, exposure từng item trong chính bank của concept và item ID. Global order không đổi local item tie.
2. `simulator.py:173–186` chỉ update estimate, attempt count và exposure của concept/item được chọn. `dynamic_k` ở52–59 dùng local count. Không transfer, forgetting hoặc elapsed-time state trong các phép cập nhật này.
3. `simulator.py:238–248` tính đáp án từ chính latent và difficulty hiện tại. Latent chỉ của concept đó được đổi thành `min(1500,before+12)`, bất kể đáp án. `episode.py:159` lấy đúng `tape[concept][previous_interactions]`. Induction theo local n cho cùng item, p, y và mọi local state trước/sau. Bước global và chapter history được loại khỏi phép so local prefix.
4. Một concept estimate≥1250 bị loại khỏi ready. Không có cập nhật ngoài concept đang chọn, nên trạng thái đạt ngưỡng hấp thụ. Đặt `N_c=0` nếu initial estimate đã đạt, còn lại là first hitting index của chuỗi cục bộ.
5. Với finite DAG, nếu còn node chưa đạt thì induced subgraph của các node chưa đạt có root, mọi parent còn lại đã đạt, nên node ấy ready. Bởi vậy `ready=∅` thực sự tương đương mọi node đã đạt dưới các giả thiết hiện tại. Điều này không bảo đảm first hitting hữu hạn cho mọi supplied tape.
6. Nếu cả hai branch hoàn thành, mỗi branch phải dùng đúng prefix dài `N_c` cho từng concept. Terminal local states và tổng lượt vì vậy trùng nhau. Latent cap không phá kết luận này khi cùng số lượt, kể cả supplied initial>1500. Riêng phát biểu “mỗi lượt tăng12” phải loại các lượt bị cap hoặc initial>1500.

`seeded_episode.py:60–66,102–120,133–146` khai báo coupling prospective. Graph/policy/global step không vào event key. Đây là chứng minh pathwise có điều kiện trên tape chung, không phải bằng chứng statistical independence của SHA-seeded streams, historical random draws hay mọi cách coupling khác.

### Giới hạn và phép phân biệt cần thêm

- Finite horizon có thể cho allocation theo concept khác nhau, một branch chưa hoàn thành, nên total/final-state equality không suy ra. Trên phần local prefix chung, equality vẫn phải giữ.
- Không có cap và mọi lượt thực sự tăng12 thì cùng H feedback cho cùng tổng net gain12H dù allocation khác. Vì vậy “finite H” riêng lẻ chưa đủ tạo khác biệt tổng net gain. Có cap thì allocation có thể đổi tổng net gain.
- Dùng global-step tape chung thay local tape có thể đổi responses pathwise khi graph đổi order. Điều đó không tự chứng minh thay đổi marginal distribution nếu vẫn lấy iid uniforms theo cùng transition law. Không được đổi coupling để tìm effect rồi gọi tái lập lịch sử.
- Prerequisite-dependent learning, forgetting/spacing, shared learner fatigue, item selection/update phụ thuộc global counts hoặc graph-specific estimate transfer sẽ phá một số giả thiết. Chúng cần source/world version khác. Không thêm chúng vào phiên bản này để buộc graph có hiệu quả.
- Mệnh đề chỉ áp dụng implementation prospective hiện tại. Không suy ra PDF sai, graph vô hiệu trong Paper2/thực tế hoặc full RQ2 đã trả lời.

### Acceptance cho candidate stdlib đang do graph agent chuẩn bị

Reuse public `Paper1PdfController`/`Paper1PdfLearner` và supplied episode khi profile hợp lệ. Không giả `InitialProfile` khác initializer để lách admission. Local projection giữ item/difficulty/p/y/estimate/latent/count/exposure, loại riêng global step/order. Cần có wrong-Y case, complete two-DAG case, finite-prefix case, cap case và uncapped fixed-H control. `test_seeded_episode.py:142–159` đã kiểm reverse-order shared prefixes với zero-RNG fixture, nên chỉ lặp test đó không thêm bằng chứng mới.

Một known-answer candidate nhỏ dùng a1,a2 thuộc A, b thuộc B, order(a1,a2,b), baseline không cạnh và graph có b→a2. Native initial estimates1249 và supplied uniforms0 cho mỗi node cho phép một correct response là đủ đạt. Khi complete, AAB/ABA có cùng local endpoints nhưng khác re-entry. Khi H2, baseline ghé a1/a2 còn graph ghé a1/b. Nếu latent đều không bị cap thì net sum đều24. Nếu latent_a2=1499, latent_b=1000, latent_a1=1000 thì source arithmetic cho net sum13/24. Các giá trị này là expected fixture, chưa được chạy trong audit này.

Đề nghị ≤6finite cases, total≤100feedback, ≤12controller/world pairs, 0RNG draws/NN/optimizer/teacher-Paper2, whole≤5s owned allocation riêng. Candidate owner phải tính exact actual workload từ final test trước ROOT dispatch, giữ cả failure. Không chạy lại US42 hoặc matrix50seed để kiểm mệnh đề. Kết quả sẽ là condition proof + deterministic boundary witnesses, không population effect estimate.

Recommended task ID `RQDIAG26`, chưa có trong TASKS160 lúc audit. Dependencies hiện có `RQDIAG17`, `RQDIAG19`, `RQDIAG21`, `RQDIAG22`, `RQDIAG24` bao phủ primitives/domain/re-entry/supplied/seeded. ROOT chọn các direct dependencies cần thiết khi thêm task. Factorial learned extension sau đó dùng `CPU09`, `EDGEFIT01`, `EDGELOAD01`, không tự nhận đã được chạy từ task status.

## 4. Factorial evidence kế tiếp — learned31 đối với expert31

Đề xuất hữu hạn, chưa cấp execution. Giữ nguyên recipe controlled-ability ngày08, thêm đúng **một graph-source condition learned31**, trước khi xem outcomes. Dùng `edge_confidence_artifact.load_method24_scores` trả `LoadedMethod24Scores.declared_edges` qua genuine producer/read bindings đã accepted. Truyền edge set vào `load_reference(estimator_edges=...,controller_edges=None)`. Không đưa c_e vào GAM, không chuyển c_e thành `EdgeConfidence` hoặc đổi S/P/L. G_env và G_controller tiếp tục native expert31. Full/empty historical branches vẫn cùng enabled S=P1,L0.

Phải admit exact28nodes/31DAG, khác expert ít nhất một cạnh, giữ bank/features/node order/initial model state. Graph được học từ TRAIN48, không từ world oracle. Chỉ đọc/check source metadata và graph trước outcomes. Nếu graph trùng expert, thiếu provenance hoặc không xác nhận role/seed-family lineage thì STOP hoặc ghi giới hạn thiết kế trước dispatch. Không tự chọn graph khác. Ba controlled blocks được tái sử dụng, không tuyên bố unseen-world hoặc independent training/test validation chỉ vì learner IDs khác.

Existing matched graph là control cấu trúc đã có thể dùng về sau. Audit này không đề nghị thêm nó cùng learned condition trong allocation đầu. Nó chỉ thay2cạnh gốc bằng2cạnh khác, giữ degree/chapter; không tự là scalar “quality” chuẩn. Tương tự learned-versus-expert là graph-source intervention. Không xếp chất lượng tốt/xấu từ outcome rồi giải thích effect.

### Đơn vị và estimand khóa trước

Với block b, ability a và mechanism λ, giữ nguyên `Y_b(a,g,λ)` là mean28 final-minus-base theta tại T41ngày. Đặt `Q_b(a,λ)=Y_b(a,expert,λ)−Y_b(a,learned,λ)` và `K_b(a)=Q_b(a,.55)−Q_b(a,0)`. Báo đủ9K và18Q cùng components, thêm adjacent ability contrasts theo đúng ba levels nếu khóa trước. Đây là finite paired potential-outcome contrast của simulator trên U/residual chung. Không mechanical DiD, mediation, graph-only causal effect bên ngoài world hoặc causal ability generalization.

Sau action histories tách, cùng ordinal step không còn cùng item/y. Không tính paired LL như thể shared query. Counterfactual coupling là U[step,outcome-or-learning], shared latent residual và clock, không ép cùng served actions. Output y được world thực tạo, predict trước interact/update. Oracle chỉ evaluator, không vào policy/features hoặc graph fitting.

### Native workload đề nghị cho lần triển khai sau

| Phase | Worlds | Interact ceiling | Mục đích |
|---|---:|---:|---|
| Expert sentinel b21000,a1150,λ.55 | 1 | 120 | Exact replay đối với source/runtime/shared inputs/semantic trace/endstate cũ trước ghép36Y |
| Learned high a1300,3blocks×2λ | 6 | 720 | Ba paired high controls,360paired semantic rows; D0 do a+r≥1240>1150 |
| Learned a1000/a1150,3blocks×2λ | 12 | 1440 | 12potential outcomes còn lại |
| Tổng | 19 | 2280 | 18new cells, sentinel duplicate không thêm N |

Mỗi world một environment và một top-level policy factory. Select/predict/interact/update mỗi loại≤2280; hai evaluator probability/theta probes mỗi loại≤2280 nếu giữ literal old worker. 0solver/NN/optimizer/teacher ngoài các interact trên. Ctor lồng nhau phải ghi đúng phạm vi riêng trong packet sau. Reuse saved residual/bases/U từ `native__shared_inputs.json`, reconstitute float64/C-order rồi kiểm exact byte identity, không redraw hoặc đổi normalizer.19cells phải có durable reservation120 trước world work, attempted/returned và terminal percell; hardkillactualUNKNOWN≤reserved, không reset/retry.

Expert sentinel mismatch làm STOP trước18new cells. Một sentinel chỉ kiểm một arm, không chứng minh universal runtime equivalence. Source/library/profile identities còn phải khớp đầy đủ. Chưa xác định current runtime có đủ exact historical library bindings, nên không coi old36Y đã tự động admit vào một grid mới. Nếu không khớp, ROOT quyết định thiết kế mới riêng, không âm thầm rerun36 hoặc ghép tolerances.

Đề nghị protective allocation whole60s/worker50/owned55 gồm cleanup3, RSS512MiB/free1536MiB, output≤16MiB, exact prelaunch remeasure; chưa đo throughput của condition mới. Native raw theo `experiments/gam_kt/results/rq2-learned-graph-ability-20261109-01/`, một bundle nhỏ sau review, reference old70 và Method24 thay duplicate exports. Không thuê GPU hoặc thay main lifecycle.

## 5. Thay đổi tối thiểu và ranh giới quyền

- Paper1 trước mắt chỉ thêm candidate theorem/finite fixtures trong P do graph agent sở hữu, không production patch.
- Factorial tương lai chỉ cần derivative worker/owned outer/plan trong P, tiny explicit graph-condition outcome key và keyed contrast arithmetic. `experimental_controls.FactorialOutcome.graph_on` là bool, không overload để chứa expert/empty/learned. Giữ old API và old runner nguyên trạng.
- `run_approved_cpu_pilots.factorial` không phải drop-in. Source đó bật/tắt S/P và dùng persona initialization, còn controlled worker973a mới là base cho same-residual scalar-ability design.
- User đã ủy quyền routine safe/cost-saving Development choices trong protocol21. Chuẩn bị code, validation và versioned finite recipe không cần mặc định đợi GVHD. ROOT vẫn review concrete sources/data roles/caps và dispatch operation riêng. Completed CPU09/Method24 không là grant cho lượt mới.
- Current AKT Gate stale sau MainC changes. Không dùng fabricated AKT PASS hoặc thay Main/CUDA guards làm quyền cho GAM diagnostic. Independent GAM source/runtime/owned checks phải genuine. Không tự gộp full CPU09 mastery/truth lane đang stopped vào task này.
- Final study vẫn cần learned/noise levels, required AKT/SAKT/GKT/CG variants, independent validation design, horizon/replicate coverage và hai environments. Diagnostic legacy native mastery/controller không được trình bày như main S04-A calibrated controller. Không final RQ completion, CI/p-value hoặc paid/fullCV authorization từ note.

## 6. Nguồn đã đọc và SHA khóa tại audit

Các line refs áp dụng bytes dưới đây. Snapshot state/TASKS là thời điểm audit, không sửa chúng.

| Nguồn | SHA-256 |
|---|---|
| `docs/thesis_recovery/TASKS.json` | `c10d305b67da023398d7f59a096b4093e25e90bd1b4475dcb44a05cd5c9831a5` |
| `docs/thesis_recovery/INVESTIGATION_STATE.json` | `7d067dc647080fce99b6f45f30e2e356556687068c1246c244c25ed12f074efd` |
| `docs/thesis_recovery/evidence/user_documents_20261108_proposal.txt` | `69568a3669b70dc17976555d752b2aaf34122e07f8f586e194d95f4d7e894878` |
| `docs/thesis_recovery/05_EXPERIMENT_MATRIX.md` | `635f5ea0ea8e069bdd3f9c2fa51763587c594d54ff4ae344612a595b1059dd0d` |
| `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md` | `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6` |
| `src/knowledge_tracing/paper1_pdf/simulator.py` | `b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f` |
| `src/knowledge_tracing/paper1_pdf/episode.py` | `e01fc94656e206101a6ab6dfc960eb24ac331a677f3711c2b4561fbcd840b471` |
| `src/knowledge_tracing/paper1_pdf/seeded_episode.py` | `7c7ac305cd49fd79f5768173198705be7fa32586114acf5871950c7540dda1b2` |
| `tests/paper1_pdf/test_seeded_episode.py` | `f97674bc764988271c091a00560bf31f2afba2f951b72819a150ae64a83b48e2` |
| `tests/paper1_pdf/test_reentry_mechanism.py` | `365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074` |
| `research_tracking/runs/paper1-seeded-domain-smoke-engineering-20261109-01/manifest.json` | `a12e409be45a3c900154b2f7f1d1118bd2e3cda59a66476d6cb32b886da85131` |
| Cùng bundle `scientific__result.json` | `cbe892e42cdcf969b4c1c7e8ef5b7f8462d66f0a72d39ed9c07b990c01704e0b` |
| `research_tracking/reports/rq2_controlled_ability_prerequisite_results_20261108.md` | `5bd3f075bf3a352ad84ce3cf259a4420ba1d7194bf39cf1895fc5e2197da8e23` |
| `research_tracking/runs/rq2-controlled-ability-prerequisite-20261108-01/manifest.json` | `a910612fdb0b3c728a715a3f5250eb9736016fdd9e691bc8fd29cdc89a146f57` |
| Cùng bundle `worker.py`, lines83–219 | `973a1973da7982aac9a44b4112786915a127447ac57c6bce07f51c06e381f119` |
| Cùng bundle `native__shared_inputs.json` | `11caeb463d6f7f4d686f3b969d43e15f971a27813179d333fc34e0a0ef22ab6e` |
| Cùng bundle `native__outcomes.json` | `76ddbdff68fb0ea592762c4feaaf4d39b112df35ac834fa576da7219c861d88d` |
| `src/knowledge_tracing/paper2_reference.py`, load_reference28/86–104 | `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1` |
| `src/knowledge_tracing/gam_kt/simulator_mechanisms.py`, build_mechanism_environment11 | `0cbfaf1b4735c188e04ed822197121118dcb65849b582af7413e157fd8d847fa` |
| `src/knowledge_tracing/gam_kt/simulator_pathways.py`, build_pathway_policy6 | `33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560` |
| `src/knowledge_tracing/experimental_controls.py`, FactorialOutcome9/paired_mechanism_contrasts19 | `099a02e9182d2357f0abcd1fc25816c7cc4b5425ec16106245a738d028631aa4` |
| `scripts/research/run_approved_cpu_pilots.py`, factorial34 | `55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e` |
| `src/knowledge_tracing/graph_controls.py`, perturb_graph48/rewire_matched_graph86 | `3c66f5d98938906f467f02fb3b82f76146d60fb546408492b4967582f3394d5c` |
| `research_tracking/runs/cpu-rq12-20261107-04-replay/matched_graph.json` | `8f5290c7be3fa5111c422f07cf5c0301e2ff250e071d20d9f0f66365c49d764f` |
| `src/knowledge_tracing/edge_confidence_artifact.py`, typed declarations91–183/load_method24_scores355 | `ecc313c5a52c3fbb56e06e84bbd1c0808191b956a35bad1ffced200728e01746` |
| `P/method24-native01/graph.json` | `6b31728f0f2bd1714cfe0b37b9dae85e10aedcb06a16b639a4d53e607f17972a` |
| `research_tracking/runs/edge-confidence-artifact-integration-20261109-01/manifest.json` | `f19c2243a663f07c48ee45f5d5b21e71cd2248c5ce1fe115e10b19d0d094bc9d` |
| Cùng bundle `edge_artifact_native03_expectation.json` | `fe968b7c87aa868e7d98fc29dcacc5fa6ddd5ec20fd21d517eda4ac75e35ce20` |
| `scripts/research/windows_owned_worker.py` | `0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1` |

Graph file SHA, graph semantic fingerprint và native namespace identity là ba định dạng khác nhau. Native namespace giữ CSV node order, còn matched-control fingerprint sort nodes/edges và có direction. Future admission phải dựng lại đúng từng scheme, không so chúng như một loại hash.

Truy vết thêm các báo cáo đã đọc `paper1_seeded_episode_readiness_20261109.md`, `paper1_reentry_mechanism_20261109.md`, `edge_confidence_native_results_20261108.md`, `edge_confidence_artifact_readiness_20261109.md`, và note P `RQ2_CACHE_MECHANISM_PROPOSAL01.md`. State đã được ROOT cập nhật đồng thời từ hash `d30a091472395c38199df57abbf9c3ea128be5728b51bdaf3f755e55821d3827` lúc mở audit sang hash ở bảng lúc chốt note. Đã đọc lại current-next-step, vẫn ghi Gate stale/MainC applied-tests-pending/no automatic retry. State là nguồn quản lý có thể tiếp tục đổi, không phải input grant của một run. Các giới hạn lịch sử trong các báo cáo giữ nguyên. Note hiện tại không chuyển pending result thành actual PASS.
