# RQ2 — controlled ability × prerequisite world: protocol đề xuất

08/11/2026. **SOURCE-LEVEL DESIGN ONLY, chưa implementation/run/new data.** Đây là focused native-GAM diagnostic tiếp theo để tách ability khỏi latent residual/profile thay đổi đồng thời; không sửa Protocol21, simulator lịch sử hoặc kết quả cũ. Root cần review exact inputs/source/caps trước mọi bounded native plan. Không cần mở thêm toy tests để thay bằng chứng khoa học, không neural fit/Junyi/Holdout/cloud.

## 1. Vì sao pilot cũ chưa trả lời ability effect?

[Factorial cũ](../runs/cpu-factorial-20261107-01/README.md) có10seed blocks21000–21009 ×3profiles ×4cells ×120steps. Đã kiểm metadata120outcomes/30four-cell groups: mỗi group có cùng latent/random identity giữa4conditions; cùng seed giữa profiles có cùng uniform-array identity **nhưng ba latent identities khác nhau**. Vì vậy profile-interaction differences chưa là controlled mean-ability intervention. [Phân tích conditions](rq2_conditions_evidence_20261108.md) giữ limits này, kể cả LOO/profile ordering không bền.

Notebook cell9 `persona_base_abilities` dùng khác global mean1400/1050/1175, khác persona-index seed offset, chapter/noise draws và riêng PYH shift−150 tại chapter Hàm số; parent smoothing0,72/0,28 và clamp850…1500 cũng tham gia. Source **không có behavior-parameter vector riêng theo persona**; persona chủ yếu đi vào initial latent vector. Không gọi giữ tên profile là đã giữ mọi residual/behavior giống nhau.

Đã truy được exact runner bytes trong Git `43d5b1ff38686fad2e3f99406c477096e9471bd5`, SHA `aea2ff2462411ac5aa5ae52fe91b325e78b8640047e23f0aa05acd0f3c9ac157`, khớp manifest cũ. Current file SHA `55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e` khác, nhưng AST function `factorial` giống hệt (SHA `2941ea8ac850a658fc36eea43400c670309f92ad145f7dcc2b3093e85ebaf600`); không giả toàn current file là exact historical revision. Cơ chế/pathway helpers hiện tại khớp archived source SHA. [Source pins](rq2_controlled_ability_prerequisite_protocol_DRAFT_20261108.sources.json).

## 2. Một finite matrix được khuyến nghị

**Đề xuất freeze trước execution:** reuse ba diagnostic blocks đầu21000/21001/21002 theo thứ tự số, không chọn theo outcome. Đây là reuse exploratory blocks đã xem, **0new independent seed blocks**, không untouched final. Mỗi block tạo **một** residual vector và **một** step-indexed two-channel uniform array, dùng chung mọi ability/graph/mechanism conditions.

### Controlled initial state — recipe mới có version

Với block b, dùng một source anchor `u_b=persona_base_abilities('PY',b)` đúng một lần, rồi:

`z_b,c = u_b,c − mean_c(u_b,c)`;

`r_b,c = 60 z_b,c / max(1, max_c |z_b,c|)`;

`base_b,c(a) = a + r_b,c`, với **a∈{1000,1150,1300}**.

Mean residual≈0 (numeric check1e−10), |r|≤60; residual bytes/node order/hash giữ nguyên giữa mọi cells của block. Không regenerate theo ability, estimator graph hoặc λ; không clip/resample/reselect theo outcomes. Nếu residual degenerate thì giữ/ghi coverage, không tìm seed thuận lợi. Base ranges lần lượt940…1060,1090…1210,1240…1360, đều trong source850…1500 và dưới ceiling1600 mà không cần clamp. Alpha là mức mean ability được điều khiển, **không** oracle model feature; model vẫn init native theta1200 ở mọi levels.

Đây là **new initialization recipe** `paper2-centered-bounded-residual-v1`, không exact source persona reproduction. Nó giữ một morphology residual có graph correlation từ fixed expert anchor; không làm latent residual/graph trở thành độc lập trong quần thể. Native response/learning/forgetting equations giữ nguyên, chỉ input base và coefficient variant được gắn version rõ.

### Các trục can thiệp độc lập

| Trục | Conditions đề xuất | Giữ nguyên |
|---|---|---|
| Mean ability a |1000/1150/1300|Cùng r_b, uniforms, item bank, schedule, model initialization/parameters|
| Estimator edge input g |source full E / empty E|Cùng `build_pathway_policy(..., signal=True, parent_adaptation=True, local_adaptation=False)` ở cả hai; controller G expert cố định|
| World prerequisite strength m |λ0 / λ0,55|`build_mechanism_environment` sẵn có; G_env expert cố định, mọi phương trình khác giống nhau|

**12cells/block ×3blocks =36trajectories; H120 =4.320interact attempts**, tối đa cùng số select/predict/update calls;36policy/env constructors, ba anchor draws/ba uniform arrays. Pure oracle readout thêm tối đa4.320`theta_at`+response-curve probes, không thêm world transition. Không Cartesian noise/more profiles/learned graph/NN allocation trong diagnostic này. Required baselines/learned graph/Junyi của toàn KLTN vẫn giữ, không được miễn bởi matrix nhỏ này.

L=off ở mọi cells để giữ scope factorial cũ; g **là edge-set input**, không bật/tắt nonedge code. Empty dùng `load_reference(estimator_edges=[])`, giữ28nodes/features/order và controller namespace full. World classes luôn dựng từ full reference; không dùng empty estimator graph làm world/controller graph. Source cũ dùng S/P off/on trên full G, mới dùng cùng S/P enabled với Efull/∅; phải ghi thay đổi operationalization, không nhập chung như same-run replication. Không tách parent signal khỏi parent adaptation hoặc suy chất lượng từng cạnh.

World threshold1150 là learning-deficit threshold; khác native model mastery theta≥1250 vàpi_task≤0,55, và controller readiness còn có parent visits≥6. Không tráo chúng với tau_ref/calibrated response trong Protocol21; diagnostic này giữ native controller, chưa là shared research-calibration evaluation.

## 3. Native equations, stochastic coupling và chronology

World source cell9:

`p_true = 1/(1+10^((difficulty−theta_at)/400))`, `y=I(U_outcome < p_true)`;

`D = mean_parent clip((1150−theta_parent_at)/300,0,1)`; no parents→D0;

`gain = TRUE_GAIN_SCALE × exp(−0,5((p_true−0,65)/0,22)^2) × (1,15 nếu y0, ngược lại0,85) × [1+0,20 min(gap_days,7)/7] × (1−λD) × (0,85+0,30U_learning)`;

`theta[cid] = min(1600, theta_before+gain)`; forgetting về **own base** với rate0,06/ngày.

Không sửa notebook/teacher: existing `simulator_mechanisms.py` kiểm AST exact `1−0.55×prerequisite_deficit` và chỉ thay coefficient trong class riêng. λ0,55 parity với source đã có test implementation; source/test không thay bằng toy test mới trong note này. λ ảnh hưởng immediate learning gain, **không immediate response ở cùng pre-state/item**; tương lai theta/y/actions vẫn có thể đổi.

U_b dùng exact existing recipe `default_rng(b).random((120,2))`, column0outcome/column1learning; cùng array hash giữa a/g/λ. Residual anchor RNG có native namespace khác, draw một lần rồi giữ. “Behavior giữ nguyên” nghĩa là cùng deterministic policy/controller equations, action space, clock và exogenous draws; **không ép actual actions hoặc y bằng nhau** sau intervention. Actions là endogenous outputs.

Clock reuse factorial cũ: start2026-01-01UTC; trước mỗi step+6h, riêng step>0 và step%28=0 thì+72h. Đây khác fixed-stream six-hour-only bins trước: H120 tương ứng41ngày theo source schedule. Không nén/reorder time hoặc sinh gaps theo treatment. World/estimator fresh cho từng condition; select→predict(query)→interact→update, current y chỉ vào policy ở update. Không feed alpha, true theta/D hoặc evaluator oracle vào selector/KT inputs.

Common-random-number **step coupling** giữ cùng U index, không đảm bảo cùng item/loss opportunity sau action divergence. Nó định nghĩa một coupling hợp lệ của potential trajectories, không làm events thành same-target paired predictions. G/λ/a đều có thể thay selected concept/difficulty, feedback và spacing; đó là tổng closed-loop response. Báo first served tuple/y prefix break và actual exposures, không ghép ordinal ΔP/loss sau phân kỳ. Không suy thay order là confound có thể “adjust away” bằng post-treatment matching; order/action là một phần policy-mediated path.

## 4. Estimands và negative controls có thể bác bỏ implementation

Với residual/noise block b đã freeze, định nghĩa potential trajectory outcome:

`Y_b(a,g,m) = mean_c[theta_b,c(T;a,g,m) − base_b,c(a)]`.

T cố định theo clock; không dùng learned-gain field trước cap làm net theta outcome. Giá trị y trong oracle/proper-loss fields không được đổi thành latent learning gain. Primary contrasts:

`Δ_b(a,m) = Y_b(a,full,m) − Y_b(a,empty,m)`;

`Ψ_b(a) = Δ_b(a,0.55) − Δ_b(a,0)`;

`Ω_b(a₂,a₁) = Ψ_b(a₂) − Ψ_b(a₁)` cho adjacent1000→1150 và1150→1300 (giữ cả hai, không chọn cặp theo sign).

Đây là finite-block factorial interaction và controlled ability moderation **trong versioned simulator đã chỉ định**, không mechanical time-DiD hoặc High là untreated control cho Low; không parallel-trends argument. Có thể gọi algorithm/world intervention khi đủ implementation assumptions, nhưng chưa external learner causal effect. Report từng block và equal-block mean, signs/zeros; không CI/p-value hoặc tăng n bằng4.320events. Không đòi Ω monotonic hoặc Ψlow>0 để pass.

| Negative/control | Expectation và phạm vi |
|---|---|
| Mechanism-null λ0 |D vẫn có thể dương nhưng multiplier=1, learning equation không phụ thuộc D ở pre-state cố định. **Không** đòi Δ(a,0)=0: estimator graph, controller G, global/latent correlation và exposure vẫn có thể giúp/hại.|
| Inactive high-ability world |a1300, |r|≤60 ⇒ every base≥1240>1150. Positive gains, cap1600 và source decay về base giữ theta_at≥base bằng induction. Do đó D=0 mọi event: với từng b/g, λ0 vàλ0,55 phải exact cùng full trace/final state/Y; Ψ_b(1300)=0 là **design-known negative**, không discovery “high ability không cần graph”.|
| Oracle readout/label negative |Trước mỗi interact, evaluator tính `elo_probability(env.theta_at(cid,t),difficulty)`; env state hash trước=sau pure probe phải giữ. So exact với returned p_true và `y=I(U_out<p_oracle)`; không dùng current answer để tạo oracle probability. Cùng state/action/time, oracle probability không nhận g/λ. Sau divergence không đòi oracle LL giữa trajectories bằng nhau.|
| No oracle leakage |Không tìm thấy native OraclePolicy trong source đã đọc; **không invent một existing oracle model/baseline**. Oracle chỉ evaluator sidecar; không cấp raw theta/base/D/a vào native policy or graph confidence. Không gọi oracle labels là fitted/calibrated KT.|

Latent truth chỉ dùng evaluator/exposure negatives. Outcome net-theta14d là common-factor redundant theo C08 ở cùng no-practice/rate; không thêm nó như independent confirmation. Soft/hard retention khác readout và đã có [counterexample](rq2_retention_metric_separation_20261108.md), nhưng không mở thêm secondary matrix trong focused diagnostic này.

## 5. Implementation-ready output và acceptance trước root dispatch

Không sửa `run_approved_cpu_pilots.py`, `simulator_mechanisms.py`, pathway helpers hay notebook. Nếu root chọn proposal: một driver riêng trong existing purposefulprep gọi existing builders; serialize r/alpha-base/U identities **trước firstinteract**, source/bank/G_env/G_controller/G_estimator/recipe/clock hashes trước=sau. Cùng node order và allcells/source counts phải được kiểm; không dùng params sau outcome để tune.

Mỗi cell lưu observable served query/time/y/prediction riêng với evaluator oracle sidecar: true state snapshot, deficit, challenge/gap/gross gain, actual cap exposure. Lưu endpoints/raw36trajectories, **9Ψ =3blocks×3abilities**,18graph-effect components và6adjacentΩ; kiểm đủ toàn population trước tổng hợp. Không loại root concepts/no-deficit/negative signs, không retain chỉ common-prefix như population thay thế. Existing `paired_mechanism_contrasts` dùng4base/random-identicalcells cho từng `(b,a)` được reuse bằng labelA1000/A1150/A1300; thêm residual identity cho across-ability moderation, không dùng old profile labels giả.

Acceptance:36fresh worlds/policies,4.320reserved/attempted/returnedinteracts nếu globalCOMPLETE; same r/U across all12cells/block, same base across g/λ ở từng a; strict source/graph/parameter boundaries; current-label chronology; all oracle equation checks; high-world λ-pair exact trace/state equality; no teacher calls ngoài registeredcases; no NN optimizer/fits. Cell không active prerequisite vẫn giữ và báo **coverage**, không bắt sampling cho đến khi effect xuất hiện.

**Resource proposal, chưa authority:** ONE outerCPU allocation60s, RSS512MiB/freeRAM≥1GiB, method counts và finalfiniteelapsedcheck; no retry/partial acceptance. Trước **mọi world work của mỗi cell**, reserve **toàn bộ120interact attempts** bằng ledger entry ghi/flush/fsync durable, kèm exact condition/plan/source/U/base identities và cumulative reserved count. Chỉ reserve nếu tổng mới≤4.320;36cell reservations là finite toàn batch. Live attempted counter tăng ngay trước mỗi native interact, returned counter tăng ngay sau return; cellterminal được persist với số thực tế nếu process còn sống. Không fsync mỗi method hoặc giả rằng batched end-of-cell logs là durable per-call.

Nếu hardkill sau reservation nhưng trước terminalreceipt: actual attempts/returns của cell là **UNKNOWN trong [0,120]**, ≤reserved, không ghi0 hoặc suy hoàn thành từ missinglog. Conservative allocation charge đủ120 cho cell đã reserve; không reclaim/reset/retry/resume bằng residual tokens. Traces partial giữ riêng, batchkhôngCOMPLETE thì không accepted inference hoặc partial subset claim. Outer/helper cleanup elapsed vẫn vào wall ledger, không bỏ spent khi sửa launcher.

Historical14.400events62,05s không là throughput forecast cho design mới với extra instrumentation. Nếu không đủ cap phải STOP và review measured failure trước revision, không tự tăng. Native plan/call caps/cleanup dùng helper launch đã review; không chạy trong source-level task này. Allocation60s ở đây là **đề xuất cho objective RQ2 mới**, không gia hạn/reset availability-replay ledger cũ hoặc cấp execution authority.

Trước execution còn phải root chọn exact recipe/a/blocks/H/caps và đọc driver/sourcepins; không đòi advisor xử lý routine safe engineering. Đây chưa final confirmatory design, fitted research corpus, RQcompletion, publication-quality uncertainty hoặc thay required models/two environments/learned graph/Junyi. Các hiện vật cũ và protocol lịch sử giữ byte-identical.
