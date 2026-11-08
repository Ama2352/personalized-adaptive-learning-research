# Sổ cái thí nghiệm

## Hiện hành08/11 — vận hành Linux CPU, không thí nghiệm efficacy

Đã kiểm124output SHA của hai bundle mới. Các mục Gate21/pending archive hoặc resolution-only phía sau là snapshot lịch sử; giữ nguyên các hàng baseline/thí nghiệm đã ghi.

| Hồ sơ/sự kiện | Trạng thái và bằng chứng | Giới hạn |
|---|---|---|
| [Linux install/audit80outputs](runs/akt-linux-isolated-install-20261108-01/README.md) | Install01 **FAILED** trước pip-install;02 **FAILED**, dù pip-install/report44selected và pip-check exit0. [Report](reports/akt_linux_isolated_install_20261108.md). | Không đổi controller verdict hoặc fake số44 từ failed result field. |
| Audit riêng, alias audit03/directory `post-install-audit01` | **EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY**,23.361956656s≤90s/1child;44versions/all RECORD origins/8CPUimports/1CPUscalar;Torch2.7.1+cu126, không CUDA initialize. |0pip/install/network/model/optimizer/Modal trong audit. Không relabel02; không full binary-byte/image/CUDA/worker/cost acceptance. |
| [Tooling44outputs](runs/linux-gate-tooling-engineering-20261108-01/README.md), commit `7b07d61` |118targeted PASS, RED107PASS/11FAIL giữ lại; parent raw44Git verified. [Report](reports/akt_linux_gate_tooling_readiness_20261108.md). | Selectedlock/publicpackaging/defaultWindows parity;0optimizer, chưa actual Linux fullGate. |
| Windows Gate22 | [Report](../artifacts/akt/preflight/gate2-evidence-20261108-linux-tooling-22.json) **768PASS**,477.7091635s≤540s/0fail/error/skip; report/log/XML/currentpointer trong bundle80. | Windows CPU software only. Gate21 là source trước tooling; Gate20 vẫn resourceREJECTED dù724functional PASS. |

[Source kit local](../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/README.md)980252bytes/161payload chưa remote execution; không tính là model/Gate run. Bridge98978 expired, startup kỹ thuật mới pending, không là user connection failure. Actual Linux fullGate/main-worker/CUDA/image/throughput-cost và S04/S05 chưa nghiệm thu.

Ngày là ngày ghi trong manifest/artifact hoặc run ID; không đồng nhất file timestamp với quyết định nghiên cứu. COMPLETED không đồng nghĩa scientific validity.

| ID | Thời điểm | Model/mục tiêu | Dataset/protocol | Run status / verification | Kết quả/diễn giải | Evidence |
|---|---|---|---|---|---|---|
| EXP-BKT-CV-20261015 | 2026-10-15 | BKT standard Development CV | Junyi; 20,706,208 validation rows; 5-fold student-disjoint; correct; seed 42; one-step-ahead | COMPLETED / VERIFIED | AUC 0.7834134107927653 ± 0.0011584741219760302; Log Loss 0.3756074974398662 ± 0.0015747963998997052; Brier 0.11510534239887318 ± 0.0005760560410811493; ECE 0.0022408926425045916 ± 0.0007188307862958956; Accuracy 0.8474159098322505 ± 0.000748281088585296. Coverage 20,706,014/20,706,208. | E-002, E-003, E-006 |
| EXP-BKT-REFIT-20261015 | 2026-10-15 | Final BKT refit on Development | 198,084 learners; 20,706,208 interactions; 720 exercises; no Test | COMPLETED / VERIFIED | 709 reached tolerance; 11 hit maxiter 100. Refit is not metric evaluation. | E-004, E-006 |
| EXP-BKT-TEST-20261015 | 2026-10-15 | One-time holdout | 49,522 learners; 5,218,345 rows; 9 unseen excluded | COMPLETED / VERIFIED | AUC 0.7853401389315783; LL 0.37411719753644507; Brier 0.11467086826208853; ECE 0.002303197682958907; Acc 0.8476443448639567. Not for tuning. | E-005, E-006 |
| EXP-GAM-PILOT-20261018 | 2026-10-18 | GAM-KT throughput pilot | Fold 0 Development, 2,000 users | COMPLETED / VERIFIED | 216,677 events; AUC 0.7721864534211456; Brier 0.11702559330062247; not full CV. | E-007, E-008 |
| EXP-GAM-CV-20261018 | 2026-10-18 | Graph-free GAM-KT 5-fold and matched BKT | Same frozen Dev assignments/folds; 20,706,208 native rows; common comparison 20,706,014 rows | COMPLETED / VERIFIED | Common GAM: AUC 0.7748662971439921, LL 0.3948808855161685, Brier 0.12037155187421189, ECE 0.05554197784523786, Acc 0.8414529934200823. BKT better on five mean metrics here only. | E-007–E-009 |
| EXP-GAM-BKT-BOOT-20261030 | 2026-10-30 | Paired learner bootstrap for GAM−BKT | 1,000 replicates, seed 20261030, percentile 95%; sample learners within fold | COMPLETED / VERIFIED | CI excludes 0 for LL/Brier/ECE/Accuracy; no paired AUC CI; JSON has no Holm correction. Conditional on stored five folds/fits. | E-010, E-011 |
| EXP-AKT-GATE2-20261104 | 2026-11-04 | Synthetic technical suite and Gate 2 | tests/akt + tests/shared_kt; not Junyi benchmark | COMPLETED / VERIFIED from Gate report | 155 passed in 66.20s; technical validation only. | E-012 |
| EXP-AKT-SMOKE-20261031-01 | 2026-10-31 | First bounded smoke | Development capped cohort | FAILED/incomplete / VERIFIED | Partial training/checkpoint; export failed learner-order check; not a smoke pass. | E-015, E-016 |
| EXP-AKT-SMOKE-20261031-02 | 2026-10-31 | Smoke retry | Stopped at RAM floor before loading cohort | FAILED/blocked / REPORTED | No cohort, checkpoint or prediction. | E-016, E-017 |
| EXP-AKT-SMOKE-20261101-03 | 2026-11-01 | Bounded end-to-end AKT smoke | 11 train learners/4,096 targets; 16 validation learners/549 targets; Development only | COMPLETED / VERIFIED | 12 steps, 48 windows; 549/549 export, 441 fitted and 108 unseen/null; checkpoint reload exact. Not CV/benchmark. | E-013, E-014, E-016 |
| EXP-AKT-PILOT-20261104-01 | 2026-11-04 | Pilot readiness attempt | Preflight only, Development | BLOCKED before launch / REPORTED | Available-RAM preflight failed; no training pilot. | E-018 |
| EXP-AKT-PILOT-20261104-02 | 2026-11-04 | Bounded AKT pilot | 417 train learners/50,000 targets; 256 validation/29,199; 79,199 targets kept | FAILED / VERIFIED | 32 batches/7,346 optimized targets; PermissionError replacing progress file. Epoch incomplete; no validation/export/checkpoint/predictive metric. | E-018, E-019 |

## Chưa có run đủ điều kiện

Không thấy qualifying run cho Graph-GAM-KT, SAKT, GKT, fixed-graph AKT hoặc CG-AKT. Source tree hoặc config không tự chứng minh experiment complete.

## Cập nhật CPU07/11/2026

Năm bounded runs trong runs/, gồm1run superseded và1replay check. Xem reports/cpu_rq12_20261107.md về thiết kế, outputs và giới hạn.

## Pilot CPU09/10 và refit07/11/2026

User chấp thuận bounded pilot trước execution. Xem reports/cpu_pilots_20261107.md về factorial và Junyi order, gồm cơ chế PG không hoạt động trong cohort và cycle witness của catalog thô. Engineering snapshot ở runs/cpu-readiness-pathways-20261107-01, không đồng nghĩa GPU/full-training acceptance.

## Matched-control exposure07/11/2026

Run32learner và run mở rộng256learner có notes/manifests riêng. Xem reports/cpu_matched_controls_20261107.md. Source controls giữ degree/topic/area/prefix-support-bin counts, còn learner-level co-observation thay đổi. Không suy graph neutral từ controls thiếu exposure. Mở rộng256×300/180s do user giao lựa chọn sau proposal cụ thể.

## Portable-kit và Gate2 cuối batch07/11

Kitv6 có113source/fixture files, source-only notebook copies và project venv. Manifest comparison chỉ ra AKT/shared v6 giống v5 đã kiểm240passed1deselected; GAMv6 đạt31passed1deselected. Hai local integration exclusions được ghi rõ. Actual Colab/CUDA chưa chạy. Main Gate2 đạt241test khôngskip. Tất cả log thành công/thất bại của batch ở runs/cpu-controls-portability-20261107-01.

## Collector/adapter simulator07/11 — engineering, không confirmatory experiments

| Run | Trạng thái | Bằng chứng | Giới hạn |
|---|---|---|---|
|cpu-sim-collector-20261107-01|FAILED|Collector proof24targets; pytest collection error do test module trùng basename|Không coi failed suite làPASS; bundle giữ nguyên|
|cpu-sim-collector-20261107-02|COMPLETED|60targeted tests, v1 exact source replay/repeat;24targets12windows|Train-only2×12fixture,0NN/optimizer,22/84items|
|cpu-sim-collector-trials-20261107-01|COMPLETED archive|12outputs gồm lỗi Windows path, source snapshots, log14/34tests và static domain defect|Archive hoàn tất không biến các trial failed thànhpassed|
|cpu-sim-collector-20261107-03-semantic|COMPLETED|64tests, collectorv2 semantic domain, RNG namespacev1|KhôngactualLinux/CUDA|
|cpu-sim-collector-20261107-04-portable|COMPLETED|65tests gồm already-stripped checkout; v1/v2oracle/queries/labels exact|Khôngfullcorpus/trainer/calibration/refit/final runner|

Gate2-12 nguồn v1 đạt396tests374.84s; sau semantic fix cần source-bound gate mới. Gate counts là kiểm phần mềm, không số thí nghiệm RQ. Xem reports/simulator_collection_runner_20261107.md và investigation state cho current gate sau nghiệm thu.

## RQ1 score-vector08/11 — phân tích lại cùng pilot

rq1-score-vector-20261108-01 COMPLETED/7outputs verified. Đọc lại traces vàcomparisons của cpu-rq12-20261107-03, khôngnewlearner/events/model/simulator. Fullpackage1080S-change/90M-change/22A-preview-change, empty267S-change/0MRA;18legacygroups×2lossmetrics match1e-12. PG predictive losses dương ở3/3seed-profile rows trong khi pooleddelta âm; khôngclaimgraphhelpsmọiprofile/causality/mediation. 1080events khôngindependentn, chỉ3seedblocks. Bundle mới không được tính thành additional experiment samples.

## Sổ bổ sung kỹ thuật08/11 — không cộng thành thí nghiệm efficacy

Đã kiểm472/472output SHA của sáu bundle dưới đây. Mốc commit là locator tích hợp; tests, native state updates và training/fitted research là các loại bằng chứng khác nhau. Parent đã xác minh raw Git27/68/196outputs ở các commit Graph-GAM/budgetfix/graph prototype tương ứng; không chạy Git trong cập nhật này. Các hàng thí nghiệm lịch sử phía trên giữ nguyên.

| Hồ sơ | Trạng thái và kết quả được kiểm | Bằng chứng/giới hạn |
|---|---|---|
| SAKT synthetic trainer, `9952bc7` | ĐÃ ĐÓNG/139PASS/51outputs | [Bundle](runs/sakt-training-engineering-20261108-01/README.md), [report](reports/sakt_training_readiness_20261108.md). Partial CPU training-ready; chưa selected-fit/refit/resume/calibration hoặc complete simulator bridge. |
| AKT toy role trainer, `000ea22` | ĐÃ ĐÓNG/40targeted PASS/93outputs; Gate19 lịch sử701PASS | [Bundle](runs/akt-simulator-engineering-20261108-01/README.md), [report](reports/akt_simulator_engineering_readiness_20261108.md). Mechanical one-epoch toy lifecycle/intentional incomplete proof, chưa full scientific trainer/corpus hoặc benchmark. |
| Graph-GAM variant factory, `96004e2` | ĐÃ ĐÓNG/38PASS/27outputs;97native state updates,0optimizer/global fit | [Bundle](runs/graph-gam-variant-engineering-20261108-01/README.md), [report](reports/graph_gam_variant_readiness_20261108.md). Coupled parent/local adaptation; không edge-only causal effect hoặc fitted CV. |
| Gate2 elapsed bugfix, `4af8f85` | ĐÃ ĐÓNG/47targeted PASS/68outputs; RED19PASS/25FAIL giữ nguyên | [Bundle](runs/gate2-budget-fix-20261108-01/README.md), [report](reports/gate2_elapsed_budget_fix_20261108.md). Operational acceptance fix,0optimizer ở targeted suite; archive snapshot chưa cấp full Gate. |
| Native A0/A1 graph prototype, `6377265` | ĐÃ ĐÓNG/23targeted PASS/196outputs/0optimizer; Gate21 accepted757PASS | [Bundle](runs/akt-graph-prototype-engineering-20261108-01/README.md), [report targeted](reports/akt_graph_prototype_readiness_20261108.md). Same-backbone residual/fallback/causal-input engineering; chưa A2/A3/trainer/fitted CG-AKT. |
| Actual Linux dependency resolution | ĐÃ ĐÓNG/37outputs;44packages/14NVIDIA;0install | [Bundle](runs/akt-linux-dependency-resolution-20261108-01/README.md), [report](reports/akt_linux_dependency_resolution_20261108.md).14raw files/SHA verified;46active constraints kiểm offline. Chưa wheel-byte/install/image/CUDA acceptance. |

[Gate21](../artifacts/akt/preflight/gate2-evidence-20261108-elapsed-guard-21.json) có elapsed467.1361735s≤540s,0fail/error/skip; current pointer/source/lock đã xác minh bằng reader. **Gate20:724functional PASS nhưng ngân sách REJECTED1083.995106s>540s**; [audit](../artifacts/akt/preflight/gate2-resource-audit-20261108-graph-prototype-20.json) và original bytes giữ nguyên. Không cộng hai gate hoặc hai targeted rerun thành các thí nghiệm nghiên cứu độc lập, không suy throughput/GPU readiness từ thời gian suite.

**Linux future install chưa chạy:** theo [addendum acceptance](reports/akt_linux_dependency_resolution_20261108_addendum.md), có thể cài trực tiếp44URLs của [candidate lock](runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt) bằng pip `--require-hashes` trong isolated target theo stage/budget riêng; wheelhouse là tùy chọn lưu riêng. Archive resolution và wording future-step trong report không là installation, GPU hoặc thí nghiệm model mới. Site unchanged chỉ có probe/danh sách tên theo source, không full filesystem byte attestation.

**Errata demo93outputs:** số12/120“nodes” trong [report visualQA](reports/demo_readiness_20261108.md) là timeline entries `#route li`; domain28concepts. [Bundle đã đóng](runs/demo-readonly-engineering-20261108-01/README.md) không sửa; không diễn giải preview timeline thành graph-node count hoặc served actions.

## GKT02 recurrent candidate08/11 — chỉ engineering recipe

| Hồ sơ | Trạng thái và kiểm đã có | Evidence/source và giới hạn |
|---|---|---|
| `gkt-recurrent-candidate-engineering-20261108-01`, commit `6035262` | ĐÃ ĐÓNG, **88finalCPUtests/47outputs**,0optimizer; cumulative controller **21,4443s** cho ba actual trials86/87/88. | [Bundle](runs/gkt-recurrent-candidate-engineering-20261108-01/README.md), [manifest](runs/gkt-recurrent-candidate-engineering-20261108-01/manifest.json) SHA `b00ca32d5c4385da9a84d3442b82638ec344a64cb191b91b1b02c5ab513d09ac`, [report](reports/gkt_recurrent_candidate_readiness_20261108.md). Recipe `gkt_static_recurrent_convention_v1`, engineering convention/unfitted. |

Mốc này bổ sung kernel GKT01; giữ các trial/source versions riêng, không cộng chúng thành samples/thí nghiệm efficacy độc lập. Chưa exact author parity/final S05 adoption, trainer/fitted adapter/learned graph hoặc full required baseline; không RQ completion/GPU/realdata/Holdout. WRITE02 không thêm registry/ledger entry vì là bản thảo viết từ bằng chứng đã lưu, không experiment mới.

## RQDIAG04 observability08/11 — reproduction cùng pilot

`rq1-query-observability-reproduction-20261108-01`, commit `7dd8338`: **12spyPASS/40outputs**, controller71,9959014s≤120s,0optimizer, **new independentN=0**. [Report](reports/rq1_query_observability_reproduction_20261108.md); manifest SHA `112cd15f69b63fec730a4b4a67acf98650986adc58138f68ef4a5105adbf81d7`. Parent review độc lập kiểm1.080sharedquery keys và flags: fullpackage22full-preview-tuple differences, empty0; không additionalitemchange khi conceptgiữ trong reproduction này. Hai passes giữ exactlegacyobservables/comparisons/state-RNG identity; đây không additionalresearchsample, historicalmetadata backfill, served-action/closedloop hoặc causalefficacy/RQcompletion.
