> Bản đọc kèm gói ngày08/11. Nội dung giữ nguyên; chỉ chỉnh đường dẫn tương đối. Nguồn gốc và SHA xem NGUON.json.

# RQ1/RQ2: native whole-policy available-history replay — 08/11/2026

## Kết quả chính và estimand

Trên **27cached targets** được chọn trước tại Hpast10/50/100 của3seed families×3profiles, đã dựng lại native Graph-GAM với last10/last50/full prior records, giữ current query/label/time. Mọi54full-prefix arm endpoints khớp **exact P/S28/M/R/full-preview** với trace gốc trước khi bất kỳ truncated case nào được chạy. Toàn108fresh policies và4.140native state updates đã hoàn tất; không teacher/world/RNG draw/NNoptimizer hoặc learner outcome mới.

Intervention thay **available observed history của toàn native policy, gồm controller bookkeeping**, không KT-only history. G_estimator full/empty đều enabled package; G_controller/G_env source không đổi. Cả estimator state và visits/question_counts/recent/chapter được dựng từ retained records. Timestamp tuyệt đối giữ nguyên; first retained observation dùng native initial state/last_timestampNone, không mô phỏng một student đã quên khác đi.

Trong pooled H100, full−empty ΔLL tại availableL10/L50/full lần lượt+0,00640588/+0,00757339/+0,00578026: không đơn điệu theo lượng input history. Graph full-preview khác empty chỉ ở H100/L50,2/9targets trong các cells này; rút ngắn lịch sử đổi preview của **cả hai arms**6–8/9 so full history. Đây là finite algorithmic response, **không causal practice/learning benefit hoặc kết luận ability**. Không so H10 vớiH100 như can thiệp một target cố định: hai H chọn targets/labels khác nhau.

## Population, aliases và source controls

[Thiết kế gốc](../../../../runs/rq1-history-availability-20261108-02/source__RQ1_CONTROLLED_HISTORY_REPLAY_DESIGN.md), [native plan](../../../../runs/rq1-history-availability-20261108-02/source__history_availability_plan02.json) và [nguồn worker](../../../../runs/rq1-history-availability-20261108-02/source__history_availability_worker02.py) được root review trước native dispatch. [Analysis recipe](../../../../runs/rq1-history-availability-20261108-02/analysis__recipe.md)/[plan](../../../../runs/rq1-history-availability-20261108-02/analysis__plan.json)/[analyzer](../../../../runs/rq1-history-availability-20261108-02/analysis__analyzer.py) freeze sau raw-validity audit nhưng **trước effect estimates**; không gọi đó là confirmatory/preregistered population study. Full−empty là estimator edge-set input contribution trong enabled native package gồm downstream state effects, không individual edge quality.

Unique native lengths: H10:{10}; H50:{10,50}; H100:{10,50,100}. Có54unique target-window pairs/108arms. Nhãn k10/k50/full tạo81nominal pairs do aliases, **không81new native observations**. 16contexts×9H/nominal cells=144summary rows; pooled9target pairs/cell, mỗi profile3 và mỗi trajectory1. Giữ mọi seed/profile/trajectory và mọi signs trong [JSON144cells](../../../../runs/rq1-history-availability-20261108-02/analysis__summary.json)/[54unique pairs](../../../../runs/rq1-history-availability-20261108-02/analysis__unique_pairs.json)/[81alias rows](../../../../runs/rq1-history-availability-20261108-02/analysis__nominal_aliases.json); không grandmean qua windows/aliases, không CI/p-value/calibrator hay favorable subset. **New independent seed N=0**, reused seed families20000–20002.

| Hpast | Nominal k | Actual L | Aliasing |
|---|---|---:|---|
|10|10|10|Cùng native case với full|
|10|50|10|Cùng native case với full|
|10|full|10|Canonical full-history endpoint|
|50|10|10|Truncated native case|
|50|50|50|Cùng native case với full|
|50|full|50|Canonical full-history endpoint|
|100|10|10|Truncated native case|
|100|50|50|Truncated native case|
|100|full|100|Canonical full-history endpoint|

Mỗi prior record native predict→cached y update rồi literal fixed-runner bookkeeping; không reuse full-history p_pred trong truncated updates. Target y không vào target predict/select, chỉ dùng proper-loss evaluation. Full-prefix control không chứng minh toàn hidden state ở từng endpoint giống historical state vì không có historical state dumps tại cácH này; nó xác nhận đúng observed endpoint fields đã nêu. [Raw verification](../../../../runs/rq1-history-availability-20261108-02/verification__raw.json) kiểm độc lập54endpoint projections/stream-prefix hash,25native source/input pins,216reservation/terminal rows/call counts và owned cleanup.

Readonly probes: native source assert actual policy fingerprint trước=sau target predict/deepcopy-preview/control probes,108cases đã đi qua. Raw chỉ lưu **một shared fingerprint**, không hai hidden-state dumps để independent reconstruct. Không nâng source-assert+receipt thành external attestation.

## Proper-loss và full-preview contrasts — pooled, đầy đủ nominal cells

Δgraph =full_estimator−empty_estimator trên cùng query/y. LL natural-log clip1e−15 (nats/target), Brier squared probability; Δp là probability points, không mastery. Âm LL/Brier nghĩa full thấp hơn theo metric đó. Preview=(concept,question,difficulty) trên deepcopy, **không actual served action**; P là current-query scalar, không reference-calibrated mastery.

| H | k | L | n | MeanΔp | ΔLLgraph | ΔBriergraph | Graph preview đổi/n |
|---|---|---:|---:|---:|---:|---:|---:|
|10|10|10|9|-0.006564293669|-0.00651630521|-0.003315535075|0/9|
|10|50|10|9|-0.006564293669|-0.00651630521|-0.003315535075|0/9|
|10|full|10|9|-0.006564293669|-0.00651630521|-0.003315535075|0/9|
|50|10|10|9|-0.002594370931|0.002666141911|0.001274556557|0/9|
|50|50|50|9|-0.004882669857|0.00528442581|0.002575484059|0/9|
|50|full|50|9|-0.004882669857|0.00528442581|0.002575484059|0/9|
|100|10|10|9|-0.004928798693|0.006405883948|0.003132230237|0/9|
|100|50|50|9|-0.005047472443|0.00757338507|0.003692362592|2/9|
|100|full|100|9|-0.002461020735|0.005780257997|0.002671292076|0/9|

## Window−full history trong từng estimator — cùng exact target

Các delta này thay input của **toàn policy**. Zero ở full/aliases là design negative control, không effect-size estimate độc lập. Dương LL/Brier nghĩa window k có metric lớn hơn full history trên các targets này. Không kết luận từ pooled rằng mọi profile luôn được lợi bởi full history.

| H | k | Arm | MeanΔp(window−full) | ΔLL | ΔBrier | Preview window khácfull/n |
|---|---|---|---:|---:|---:|---:|
|10|10|full E|0|0|0|0/9|
|10|10|empty E|0|0|0|0/9|
|10|50|full E|0|0|0|0/9|
|10|50|empty E|0|0|0|0/9|
|10|full|full E|0|0|0|0/9|
|10|full|empty E|0|0|0|0/9|
|50|10|full E|0.01046415164|0.0434366154|0.02062025195|6/9|
|50|10|empty E|0.00817585271|0.0460548993|0.02192117945|6/9|
|50|50|full E|0|0|0|0/9|
|50|50|empty E|0|0|0|0/9|
|50|full|full E|0|0|0|0/9|
|50|full|empty E|0|0|0|0/9|
|100|10|full E|0.008811827124|0.05780442966|0.027334343|8/9|
|100|10|empty E|0.01127960508|0.05717880371|0.02687340484|8/9|
|100|50|full E|0.01308768962|0.04730766418|0.0222054403|6/9|
|100|50|empty E|0.01567414133|0.04551453711|0.02118436978|8/9|
|100|full|full E|0|0|0|0/9|
|100|full|empty E|0|0|0|0/9|

Numeric interaction định trước: `E(H,L)−E(H,H)`, với E là full−empty proper-loss/probability contrast. Nó bằng full-arm window delta trừ empty-arm window delta (residual≤1e−12), không time-DiD hoặc causal mediation. ỞH50/k10, interactionLL−0,00261828 trong khi ởH100/k10/k50 là+0,000625626/+0,00179313. Mọi p/LL/Brier interactions cho144cells nằm trong JSON; không chia thành “phần trăm graph contribution”.

## Cả ba profiles, mọi nominal cells và kết quả ngược chiều

n=3same-target pairs/cell; cùng seed families có shared query schedule nhưng labels/states khác. Profile không là randomized ability level. Hai cột windowΔLL riêng giữ cả beneficial/harmful outcomes của việc giữ ít records hơn; A_F/A_E là window preview khácfull history.

| Profile | H | k | ΔLLgraph | ΔBriergraph | Graph A/n | WindowΔLLfull E | WindowΔLLempty E | A_F/n;A_E/n |
|---|---|---|---:|---:|---:|---:|---:|---:|
|PG|10|10|0.003946634849|0.00155906733|0/3|0|0|0/3;0/3|
|PG|10|50|0.003946634849|0.00155906733|0/3|0|0|0/3;0/3|
|PG|10|full|0.003946634849|0.00155906733|0/3|0|0|0/3;0/3|
|PG|50|10|0.005266200361|0.002562113625|0/3|0.08628849516|0.0857584501|2/3;2/3|
|PG|50|50|0.004736155304|0.002144655503|0/3|0|0|0/3;0/3|
|PG|50|full|0.004736155304|0.002144655503|0/3|0|0|0/3;0/3|
|PG|100|10|0.009086411439|0.004383014024|0/3|0.210286996|0.1995363966|2/3;2/3|
|PG|100|50|0.007692907826|0.003679648282|0/3|0.1534264767|0.144069381|2/3;2/3|
|PG|100|full|-0.001664187912|-0.0008729727753|0/3|0|0|0/3;0/3|
|PY|10|10|-0.01326352975|-0.006411061714|0/3|0|0|0/3;0/3|
|PY|10|50|-0.01326352975|-0.006411061714|0/3|0|0|0/3;0/3|
|PY|10|full|-0.01326352975|-0.006411061714|0/3|0|0|0/3;0/3|
|PY|50|10|0.001366112685|0.000630778023|0/3|0.02201737452|0.0262031239|2/3;2/3|
|PY|50|50|0.005551862068|0.002787598559|0/3|0|0|0/3;0/3|
|PY|50|full|0.005551862068|0.002787598559|0/3|0|0|0/3;0/3|
|PY|100|10|0.002039888218|0.001167437357|0/3|0.01171108413|0.01389041937|3/3;3/3|
|PY|100|50|0.002274944524|0.001410265831|1/3|0.02218324838|0.0241275273|2/3;3/3|
|PY|100|full|0.00421922345|0.002288010152|0/3|0|0|0/3;0/3|
|PYH|10|10|-0.01023202073|-0.005094610841|0/3|0|0|0/3;0/3|
|PYH|10|50|-0.01023202073|-0.005094610841|0/3|0|0|0/3;0/3|
|PYH|10|full|-0.01023202073|-0.005094610841|0/3|0|0|0/3;0/3|
|PYH|50|10|0.001366112685|0.000630778023|0/3|0.02200397653|0.0262031239|2/3;2/3|
|PYH|50|50|0.005565260059|0.002794198117|0/3|0|0|0/3;0/3|
|PYH|50|full|0.005565260059|0.002794198117|0/3|0|0|0/3;0/3|
|PYH|100|10|0.008091352188|0.003846239328|0/3|-0.04858479115|-0.04189040488|3/3;3/3|
|PYH|100|50|0.01275230286|0.005987173663|1/3|-0.03368673254|-0.03165329695|2/3;3/3|
|PYH|100|full|0.01478573845|0.006598838852|0/3|0|0|0/3;0/3|

PG H100/full graphΔLL âm nhưng k10/k50 dương; PYH H100 window−full LL âm ở cả hai arms, dù pooled delta tương ứng dương. Vì thế không kết luận graph benefit/history benefit ổn định từ pooled means. Không chọn một favourable seed/profile/window;3seed-block và9trajectory-level contexts đủ trong JSON, cùng per-target records để đối chiếu.

## Thời gian, failure history và acceptance

| Hoạt động riêng | Kết quả thực tế | Thời gian/giới hạn |
|---|---|---|
| Attempt01 pre-native |PPID guard reject trước native imports,0nativecalls; không sửa receipt |0,389369199984s|
| Pure launch probe |Venv shim chain được xác nhận; overallUNKNOWN do instant conhost snapshot, không persistent-leak claim |0,456024499959s|
| Owned Job helper |6pure tests; actual normal/descendant/timeout, không native |Controller2,1453567s; bảo thủ charge toolwall2,6589773s|
| Revision02 native |108cases/54controls exact; actualworker in exact Job trướcGO; owned cleanup accepted/Jobactive0/handlesclosed |Worker2,1586598s; outer2,593270301819s; toolwall3,1005861s riêng|
| Cumulative native objective |Giữ prior3,504370999943s; không reset cap |6,097641301762/60s accepted|
| ONEcached analysis |RC0, no native; root tool capture **không raw stdout bytes** |Toolwall0,5720696s; observedouter0,747s≤10s|

[Original failure/probe bundle](../../../../runs/rq1-history-availability-20261108-01/README.md) giữ nguyên. [Native receipt](../../../../runs/rq1-history-availability-20261108-02/native__run.json), [owned launch receipt](../../../../runs/rq1-history-availability-20261108-02/native__owned_launch_receipt.json), [budget](../../../../runs/rq1-history-availability-20261108-02/source__history_availability_budget02.json), [root analysis capture](../../../../runs/rq1-history-availability-20261108-02/analysis__root_tool_capture.json) tách mức bằng chứng. Không chế analysis.stdout/stderr log khi root chỉ có tool-capture JSON. Archival/root verification không rerun native hoặc analysis.

Counter direct driver calls:108constructors/4.140priorpredict/4.140updates/108targetpredict/108preview; full controls có54ready/1.512S/1.512is_mastered explicit reads. Nested source calls không được tuyên bố đã instrument toàn bộ; fixed28nodes/84items và pinned native code giữ bound.0world interactions/teacher/generated labels/scientific RNG draws/NNoptimizer; helper nonce entropy chỉ vận hành.

[Independent numeric verifier](../../../../runs/rq1-history-availability-20261108-02/verification__numeric.json) dùng raw endpoints và log1p cho cùng LL formula, không import analyzer/native:54unique pairs×13numeric fields702checks,144rows×13means1.872checks,576boolean-count checks và81alias mappings, toàn bộ PASS. 40analysis input pins+source+plan42 được kiểm lại. Không thêm effect search/CI hoặc chọn bins sau quantities.

## Điều được hỗ trợ và còn thiếu

Kết quả cô lập **algorithmic available-history input** tại target cố định rõ hơn observational history bins: current query/y/time không đổi khi đổi retained length trong cùngH. Nó cho thấy both native policies có thể nhạy với thiếu records/controller bookkeeping, graph preview contrast có thể chỉ lộ ra ở một availability condition; không chứng minh graph ổn định làm policy tốt hơn.

Không đổi actual world/learner histories hoặc thực serve preview, nên chưa là instructional causal history effect/net gain/retention benefit. Comparisons giữa H khác nhau vẫn đổi target/position/time; no causal ability interpretation. Model initialization/uncertainty/last_seen được reset theo native recipe chứ không phải chỉ xóa một attention context; không gọi KT-only/full-history advantage của CG-AKT đã được kiểm. Native S chưa calibrated/mastery proxy V1, chưa fitted research neural model, independent final seeds, required model/noise/learned-graph/Junyi comparisons hoặc RQcompletion.

[Accepted bundle02](../../../../runs/rq1-history-availability-20261108-02/README.md) lưu raw/source/plan/hash/copyinventory; old C13/C14/full-empty/history-bin outputs không bị đổi. Báo cáo này là finite simulator-source algorithmic diagnostic, không final efficacy study.
