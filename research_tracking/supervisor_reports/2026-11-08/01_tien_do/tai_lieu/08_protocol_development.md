> Bản đọc kèm gói ngày08/11. Nội dung giữ nguyên; chỉ chỉnh đường dẫn tương đối. Nguồn gốc và SHA xem NGUON.json.

# Protocol V1 đã chọn: S04-A và S05-Plan B cho development

**Ngày08/11/2026 · ADOPTED_GROUP_METHOD_V1 · chưa cấp quyền thực thi run.**

Nguồn quyền chọn phương pháp là chỉ thị mới của user, do root chuyển tiếp: **“Phương pháp nào an toàn và tiết kiệm tiền thì chọn, ko chờ chốt”.** Root chọn S04-A và S05-Plan B; H_dev30 được root xác nhận là giới hạn development. Đây là lựa chọn phương pháp của nhóm theo quyền user giao, **không phải phê duyệt của GVHD**, không xóa yêu cầu đề cương, không cho phép paid run/full CV/Holdout từ câu trả lời này. Không tiếp tục coi routine method engineering là đang chờ advisor. Source review/run config/resource/data authorization vẫn phải thỏa trước execution.

Bản [DRY đã review](../../../../reports/s04_s05_decision_options_DRY_20261108.md) và [source map](../../../../reports/s04_s05_decision_options_DRY_20261108.sources.json) giữ nguyên byte: SHA report `38b22244a0e396c44433fdf12d13c90ecdbf0c972e10bae1d7169b700e280fca`, source map `530d09636dc8b9477d073337c78550f61540b8bc2824ea02c967626444145d1c`. Các chữ “chưa adopt” ở đó là trạng thái **trước quyết định mới**; tài liệu này ghi đúng phạm vi adoption hiện hành. Các thiết kế05/06/09 không bị sửa lịch sử bởi V1.

## 1. Phạm vi đã adopt, các mức chưa được nghiệm thu

| Phần | V1 hiện hành |
|---|---|
| S04-A | Reference ba item thật, common reference criterion, response temperature calibration độc lập, controller version mới với target success0,70 |
| S05-B staged | Một training seed; Junyi outer fold4 đã frozen; đủ required models, hai environments, expert/learned graph; không full-Cartesian |
| Interpretation | Development evidence có giới hạn; không5fold modern performance, training-seed variance, causal learning benefit ngoài simulator hoặc RQ completion |
| H_dev | **30 interactions/trajectory** cho development closed loop. Không đủ để kiểm history>50 hoặc long-horizon RQ2 |
| Final horizon | **H_final500 là đề xuất alignment lịch sử**, chưa final execution freeze/budget acceptance. Không âm thầm lấyH30 hoặcQUICK120 làm final |
| Execution | Chưa chạy corpus/fit/calibration/Junyi/GPU trong task lập protocol; mỗi run phải có config/source/inputs/caps/output directory riêng và authority tương ứng |

Notebook Paper2 cell3 thực tế có `REPLAY_STEPS = 120 if QUICK_MODE else 300` (dòng29) và `CLOSED_LOOP_STEPS = 120 if QUICK_MODE else 500` (dòng30). Source identity nằm trong source map đi kèm; không xem QUICK120 là full historical horizon. ChọnH30 vì resource development, không vì outcome đã quan sát. Mọi thay đổi horizon/coverage sau này phải version/reason trước execution; không chọn horizon theo hiệu ứng đẹp.

## 2. S04: reference, calibration và controller hữu hạn

**Reference bank:** mỗi28concept có đúng item1050/1200/1350, trọng số1/3, tổng84item responses ở một full probe. Dùng đúng item IDs từ bank đã ghim SHA, không tạo exercise1250 giả. Tại history trước t, `S_c=mean_d Cal_m(p_m(c,d|history))`; `M_c=(S_c≥tau_ref)`.

**Threshold:** `p_true(theta,d)=1/(1+10^((d−theta)/400))`; `tau_ref=mean_d p_true(1250,d)=0.5637150147511514`. Đây là mapping dựa vào thiết kế simulator, **không P(K), không chứng minh calibrated mastery**. Tau0,5 trên ba difficulty này tương ứngtheta1200. True state chỉ ở evaluator để so với `theta_c(t)≥1250`; không vào features/selector/gate. `PREREQUISITE_READY_ELO=1150` là ngưỡng environment learning-deficit/violation; khác controller readiness dùng `is_mastered(parent)` hoặc visits≥6. Giữ outcome net latent gain/retention14 theo source, không thay bằng S.

**Calibrator:** một positive temperature/checkpoint, fit observed response Log Loss, không đổi neural weights. Recipe numerical tiết kiệm cho implementation là bounded scalar fit trên `T∈[0,05;20]`, tối đa200 objective evaluations; logit dùng common clip1e−6. Những giới hạn này là method-engineering V1, không hyperparameter search theo final labels. Calibrator ID gắn checkpoint/vocab/split/reference-bank/source. Không đủ valid labels/two-class support hoặc nonfinite thì STOP calibrated evaluation và báo unsupported; không tự gọiT1 là calibration thành công. Raw predictive diagnostics có thể báo riêng đúng tên.

**Data lifecycle bắt buộc:** fit80% / epoch-selection10% / response-calibration10% bên trong Junyi outer-train; simulator dùng cùng role separation theo learner/seed families. Chọn epoch và system selector bằng **raw best-epoch predictions trên selection trước refit**. Refit fit+selection90% tại epoch đã chọn; không dùng lại selection đã thành train để đổi winner. Fit temperature bằng calibration10% sau refit; final/audit không tham gia bất kỳ bước chọn nào. Đây là thay đổi versioned so với draft “refit100%”, không chỉnh historical BKT folds hoặc lách native validator10%.

**Controller `reference-controller-v1`:** probe counterfactual references từ cùng prehistory, không observe/RNG/practice; tính S/M → R theo prerequisite/count≥6 → C theo anti-drill/escape hiện hành → B có visits≤min_visits+1 → `min(S_c, chapter_tie, previous_visits, cid)` → item gần calibrated expected success0,70 nhất, tie ít dùng rồi item ID → bookkeeping → predict served query → interact → observe. Recent-concept limit3; giữ exact ordering/ties bằng source-pinned contract. Trong controller mới, **preselect reference P vector** đi vào choice; **postselect served-item P** có phase/query identity khác. Không suy DAG mới từ linear funnel Pserved→M→A hoặc gọi đây là exact historical reproduction.

G_env và G_controller chuyên gia cố định giữa model conditions; thay expert/learned/noisy G_estimator không thay world/latent initialization/controller. Policy graph on/off là diagnostic contrast riêng. Known-item cold query-only là convention V1; OOV/unsupported vẫnnull+reason, không0,5/fitted giả. Thiếu bất kỳ reference item nào thì concept score null, không renormalize. Preflight phải chứng minh đủ support để trajectory đủ điều kiện; không drop trajectory bất lợi sau khi thấy outcome. GKT concept-level repeated item predictions có thể reuse **nếu exact contract/parity** cho phép; không xem ba item đó là ba quan sát độc lập.

**System fallback bảo thủ:** so checkpointA1/A3 với **A0 riêng** trên selection common-supported targets, kèm full-population coverage. Chỉ eligible graph khi upper95% learner-bootstrap bound của `LL_graph−LL_A0`<0; chọn eligible model có meanLL nhỏ nhất; còn lạiA0. Đây là rule lựa chọn Dev, không final significance hay bằng chứng practical benefit. Disable graph trongA3 chỉ tái hiện backbone củaA3, không independentA0 fallback. Không đổi raw/calibrated selector hoặc threshold bằng final outcomes.

## 3. S05-B: model×environment được giữ, allocation development được thu nhỏ

Grade10 và Junyi là hai domain train riêng; không chuyển numeric embedding/checkpoint giữa84items và Junyi exercises. Một algorithm training seed được ghi trong từng run manifest, không dùng repeat như nhiều training seeds. Không thay frozen AKT hyperparameters trong protocol này.

| Model/condition | Simulator development | Junyi development |
|---|---|---|
| BKT | Paper2-native sequential reference, đúng variant label; không giả là pyBKT offline fitted | Frozen5fold BKT giữ historical reference, không rerunEM |
| GAM | Native graph-free online reference, same scenario/controllerV1 khi adapter accepted | Một matched fit outerfold4 theo partitionV1; frozen5fold giữ historical reference |
| Graph-GAM | Expert + learned; local adaptation matched khi isolate graph | Outerfold4 expert + learned, cùng matched partition với GAM |
| A0 AKT | Một fit, reuse khi G đổi | Fold4 một selection/refit pair |
| A1 fixed | Một fit/expert và một fit/learned | Fold4 expert + learned |
| A2 confidence | Một fit/expert và một fit/learned | Fold4 expert + learned |
| A3 gated | Một fit/expert và một fit/learned | Fold4 expert + learned |
| SAKT | Một fit comparator | Fold4 một selection/refit pair |
| GKT | Một fit static expert; concept28, disclosed full-prefix memory | Fold4 một selection/refit pair; exercise-tag graph, exact map bound |

Tổng modern: simulator **9 neural fits**; Junyi9conditions×selection/refit = **18 phases**. GAM/Graph-GAM, graph/confidence estimator, calibration, learning curve và inference chưa nằm trong hai số đó. BKT cũ full outer-train khác90% của comparison mới: chỉ historical reference, không information-matched control cho graph contrast. GKT là explicit primary-equation candidate variant, không tự gán author-code parity; fixed graph khác learned GKT graph module. Chưa làm GKT-learned không có nghĩa bỏ learned graph: Graph-GAM/A1–A3 vẫn có learned condition trên cả hai environments.

A0–A3 dùng cùng backbone initialization, observable corpus, optimizer budget và **effective causal history**; không full-cache advantage riêng cho graph. SAKT/GKT có native memory/capacity khác được disclose, không gọi deltaGKT−AKT là edge-only effect. Unseen/cold/common-supported/full-target population đều báo; không chấm unknown như fitted.

**Noise development:** delete/add/reverse ở0/20/50%, expert/learned; frozen-checkpoint inference sensitivity trước, không gọi noisy-training robustness. Confidence trên added edges cũng phải derive từ train-only recipe, không mặc định biết cạnh giả. History bins1–10/11–50/>50 và support/intra-cross giữ definitions; H30 làm bin>50 **not covered**, không missing-bin imputation hoặc suy kết luận RQ2. Final coverage thiếu phải ghi rõ, không waive requirement.

## 4. Confidence, learned graph và evaluation estimands

Chọn hướng train-only lagged surrogate + cross-fitting theo learner, không per-edge neural refits. Features chỉ past target/parent correctness/support và learner past-mean proxy; không current/future y, learner-ID embedding hoặc theta. Learned graph rank positive paired OOF response-loss reductions, deterministic tie/cycle handling, edge budget bằng expert graph với endpoints train-supported hoặc dừng và báo thiếu support. **Trước estimator fit** phải pin candidate pool, regularization/features/solver/cross-fit assignments trong config; đây là routine finite engineering freeze theo quyền user, không cần chờ advisor hay được chọn bằng audit labels.

Reliability V1: tối thiểu20 co-observed train learners;200 learner-bootstrap resamples của **paired frozen OOF loss deltas**; `c_e=fraction(DeltaLL_e>0)`. Đó là predictive-stability score conditional on fitted surrogate, khôngP(edge true)/causal confidence. Mỗi delta có cùng eligible edge population giữa hai terms; ghi full child denominator và attrition. Unsupported có flag riêng; operational residualzero không là chứng minh cạnh sai. Structural toy0,25/0,75 không được promotion thành estimated score. c=1 baseline/shuffledwithin-strata là controls; true-edge labels/noise-generator knowledge chỉ privileged simulator upper-reference, không main/Junyi deployment.

Không gọi c calibrated edge probability nếu chưa có **graph-realization** train/calibration/audit split và unseen-realization evaluation; learner split trên một graph chưa đủ. Gate train bằng response loss, low gate không chứng minh cạnh sai. E05 order-only và degree/chapter/support-matched graph controls vẫn cần vì learned graph có thể proxy logged order; Junyi effects chỉ predictive association.

**Estimands/units:** F1 primaryLL/Brier trên full coverage và common-supported targets, AUC/ECE15/near-threshold bands báo thêm. F2 primary net latent gain, retention14/time-to-mastery/censoring/violations/chapter changes/reentry báo đúng definitions; homogeneous no-practice retention proportional final gain phải ghi redundancy. F3 noise-degradationLL/net gain với same frozen checkpoint. Paired learner bootstrap Junyi, paired seed-block bootstrap simulator,2.000replicates; Holm theo family contrasts×conditions×primary endpoints freeze trước run. Không reset family theo persona. Simulator proposed evaluation gồm50fresh seed blocks×3personas; pair worlds bằng same base/uniform channels, không150independent seeds hoặc event-as-N. Một training seed chỉ cho conditional results, không training-seed variance claim. Raw selected P/action differences sau divergent histories không paired target contrasts; optional source-local common-prefix explanation giữ đúng nhãn.

## 5. H_dev30, horizon lịch sử và resource stops

H_dev30 là first-development closed-loop target đã chọn để giảm workload; **không final horizon**, không evidence history>50 hay long-term benefits. H_final500 chỉ là historical-alignment proposal. Trước bất kỳ final execution cần pin final horizon/coverage trong manifest dựa measured resource budget, không dùng outcome để chọn hoặc tự claim yêu cầu đề cương đã đủ. Có thể đổi phương án rẻ trong phạm vi quyền user, nhưng mọi thay đổi phải version/reason và giữ prior evidence; không xin lại advisor cho routine engineering.

Logical reference workload: `Q=W×50×3×H×84`. PlanB W9: **113.400H**, nên **H_dev30→3.402.000 responses**. H120 chỉ ví dụ13.608.000; **proposed finalH500→56.700.000**, chưa runtime/cost authorization. Q không là independent observations hoặc sequential kernel calls: independent batching/GKT exact reuse có thể giảm calls. Legacy/noise/calibration/servedP/export/Junyi add work. Chỉ benchmark dataset training targets/s không đủ; phải đo reference/controller workload trước forecast.

Trần user vẫn **30USD free credits/net trả thêm0USD**, local→Colabfree→Modal; không auto paid fallback/hardware allocation. Source/runtime Gate và actual device/resource/durability acceptance là prerequisite; oldCUDA/mocks không currentGPUready. Reserve training **và inference** theo actual quotas/cost projection; exhausted cap/partial epoch/source mismatch/coverage error→STOP giữ ledger, không tự retry/reset cap. Không dùng protocol adoption này thay execution authorization data/Holdout/fullCV/paid jobs.

## 6. Công việc tiếp theo: research-mode wiring, không thêm toy-only milestones

| Module/input | Deliverable hữu hạn trước first research-mode fit |
|---|---|
| Data/split (`simulator_data`, `simulator_collection`, native contexts) | Role-aware corpus manifest: exact learner/count/clock/RNG/behavior/vocab hashes, train80/selection10/calibration10 và audit disjoint;84item/28concept support. Collector hiện train-only fixture nên phải nối đúng roles, không giả Junyi fold hoặc dùng oracle replay logging policy |
| Training lifecycle (AKT/shared, SAKT/GKT pipelines) | Versioned accepted research config/attestation, actual corpus budgets/complete epoch/epochselection/refit/coverage/export; giữ frozen native hyperparams. Không sửa role checkpoint toy hoặc nới cap bằng wrapper |
| Calibration/reference | Fitted temperature bound đúng final checkpoint+calibration partition, three-item aggregation/null handling, raw/calibrated metrics tách rõ; response calibration không là latent mastery calibration |
| Controller + system selector | ControllerV1 pure probes/ties/predict-before-observe, same-bank action eligibility, independentA0 selector trước refit, no extra RNG/teacher calls |
| Learned graph/confidence | Train-only OOF ledger/coverage, frozen estimator configuration và graph realizations/perturbation provenance; no label oracle trong main |
| Runtime/resource | Current source Gate, bounded real CPU/CUDA lifecycle nếu phase đó được phép, durable outputs và representative query throughput; không thêm mô hình/NN module ngoài A0–A3 đã có |

**Numerical execution profile chưa được chọn trong adoption này:** first corpus learner/event counts, neural dimensions/lr/dropout/batch/epochs/optimizer-step/time/RAM/VRAM caps phải là **exact pinned config trước run**, do root chọn an toàn/tiết kiệm theo authority đã có; không suy chúng từ toy≤12events/d32 hoặc âm thầm đổi frozen AKT settings. H_dev30 giới hạn evaluation, không tự là train-data horizon. Không launch khi các trường này null hoặc lấy production defaults/data paths. Đây là readiness/config task cụ thể, không open-ended wait-for-advisor.

First substantive run sau wiring là **một simulator A0 research-mode lifecycle trên corpus đã freeze**: train→epochselect→refit90%→temperaturecalibration10%→full-targetexport; weights frozen khi evaluation. Chỉ mở các fit tiếp theo trong staged matrix sau acceptance corpus/coverage/resource, không đòi metric tăng để qua engineering acceptance. Sau đó SAKT/GKT/A1–A3/Junyi theo allocation; không coi first A0 hoặc một fold là final RQ completion.

## 7. Audit đề cương còn phải giữ

Required models/two environments/learned graphs/noise types/demo/article/thesis vẫn còn nguyên. PlanB không chứng minh đủ fivefold modern generalization, training-seed stability, long history hoặc full finalhorizon; audit requirement coverage trước khi báo hoàn tất. Paper1 original revision vẫn thiếu; current-source diagnostic không tự thành exact historical reproduction. Holdout đã có access history phải giữ S06 separation; không mở Test để chọn model/threshold/graph. Nếu final scope không đủ nguồn lực, ghi limitation và trình deliverable reconciliation trung thực, không tự gọi GVHD đã duyệt waiver.

**Nguồn:** [đề cương](../../../../../docs/thesis_recovery/evidence/proposal.txt) trang2–4; [05](../../../../../docs/thesis_recovery/05_EXPERIMENT_MATRIX.md), [06](../../../../../docs/thesis_recovery/06_AKT_CGAKT_ARCHITECTURE_PLAN.md), [09](../../../../../docs/thesis_recovery/09_DECISION_REGISTER.md), [18](../../../../../docs/thesis_recovery/18_SIMULATOR_KT_INTERFACE.md), [19](../../../../../docs/thesis_recovery/19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md), [20](../../../../../docs/thesis_recovery/20_LINUX_CUDA_WORKER_CONTRACT.md); immutable DRY/source-map ở đầu. User authorization không là outcome evidence. Companion `21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.sources.json` ghi source SHA, root-relayed instruction và phân loại adopted/config-before-run/proposed-final, không fabricate signed approval.
