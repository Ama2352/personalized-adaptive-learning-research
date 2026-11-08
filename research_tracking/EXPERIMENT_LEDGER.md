# Sổ cái thí nghiệm


## Mốc mới08/11 — graph lifecycle, GPU-host preparation và demo closed-loop

- **GRAPH04 — `f8e9ab0`:** [toy graph lifecycle](reports/akt_graph_training_readiness_20261108.md), [bundle](runs/akt-graph-training-engineering-20261108-01/README.md), 89 outputs. Actual02 giữ **45 PASS/1 FAIL**; sáu graph tests PASS; inventory expectation kiểm riêng một corrected function trên stored artifact/0fit, không rerun toàn suite hoặc relabel failure. **4 optimizer reservations/body returns**, cumulative **46,6888821s ≤ 60s**; graph complete1update/8targets, selection4=3scored+1OOV, reload delta0; partial graph1update không checkpoint/export/COMPLETE. Chưa research fitted/calibration/S04/S05/context100/resume/full Gate/CUDA.
- **GPU09HOST — `c1d93ec`:** [source preparation](reports/akt_gpu_host_preparation_20261108.md), [bundle102outputs](runs/akt-gpu-host-preparation-20261108-01/README.md). Final warm20/generic9/cold24/packet41 methods là **bốn scopes local mock/AST/metadata**, không tổng fullGate. Historical CPU marker/tag engineering không actual GPU-host discovery/startup/hidden audit/install hoặc wheel-byte/CUDA proof.0model/optimizer/hardwarechange/remote trong batch. Report snapshot còn chữ proposed/pre-closure; mốc này chỉ xác nhận archive closure bằng manifest.
- **DEMO02 — source `22b3522`, bundle `b9eaaab`:** [viewer closed-loop](reports/demo_closed_loop_readiness_20261108.md), [bundle66outputs](runs/demo-closed-loop-engineering-20261108-01/README.md). **83 PASS**, cumulative36,1590131s ≤ 60s; giữ47PASS/36HTTPfailures trial01, không sourcefix giữa trials. Cùng trang chọn trajectory/common-prefix/first-break, giữ bảy negatives; actual mobile390×844, console0error, QA tab/server đã đóng. Post-hoc source-local CID/newN0/native Bscore noncalibrated/Pafterselect/package≠edges; không paired ΔP sau divergence hoặc live fitted personalization. T21 vẫn IN_PROGRESS/partial E11.

**Trạng thái vận hành hiện tại:** Linux Gate24 771 PASS và CPUdummy48train/8val/2updates/durable9files là **bằng chứng lịch sử source trước Graph03/04**. Không dùng Gate24 hoặc targeted tests/mocks mới để chứng nhận current full Gate, actual CUDA/GPU ready, hiệu quả CG-AKT hay hoàn thành RQ. Windows Gate22 đã stale. Các snapshot hiện hành cũ phía dưới giữ nguyên thời điểm/verdict.

**Mốc mới08/11:** [A2/A3 confidence/gate](reports/akt_graph_confidence_gate_readiness_20261108.md) commit `4a256a4`:43targeted CPU PASS/0optimizer,37outputs rawGitverified; chưa graph-aware trainer/fit/calibration hoặc GPU. Gate24 trước thay đổi này **không chứng nhận current source**. [Bản thảo C14](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) commit `4edf1f8`:14claims/104pointers/28inputs/24links đã kiểm; C01–C13 giữ nguyên, C14 post-hoc source-local/newN0, không finalRQ.

**RQDIAG05 đã đóng (`850f5ab`):** [closed-loop và concept ranking](reports/rq1_closed_loop_reconstruction_20261108.md) giữ exact legacy 3.240events/pass,27statepairs và9uniformpairs. Native ranking key khớp3.240/3.240 CID; trong common-prefix first breaks,8full+2empty cases có cùng M/R/C/B membership nhưng khác score chọn khác concept. Đây là **post-hoc source-local explanation**, không edge-only/causal/learning-benefit hoặc hoàn tất RQ1. Served-item P được tính sau selection trong source này. Accepted-02 có125outputs; failed archiver-01 có116outputs giữ nguyên; cả241raw Git blobs đã kiểm. Report snapshot còn chữ PROPOSED vì được freeze trước closure; mốc chỉ mục này xác nhận actual closure bằng manifest.

**GKT06 đã nghiệm thu (`f204f69`):** [epoch pipeline](reports/gkt_epoch_pipeline_readiness_20261108.md) có38purePASS và actual2epochs/2Adamreturns;6train targets mỗi epoch, selection đủ4=2scored+2unsupported/0research_fitted.95outputs raw Git verified. Đây là lifecycle engineering, chưa full corpus/final GKT baseline/refit/resume hoặc S04/S05 adoption.

## Bổ sung08/11 — GKT05 và discovery CPU đã nghiệm thu

- [GKT05 adapter](reports/gkt_adapter_readiness_20261108.md), commit `4a64525`:32portable tests và1actual stored checkpoint load;6targets=2scored+4unsupported,0research_fitted/optimizer.69outputs đã kiểm raw Git; chưa epoch/corpus/fitted OnlineSession hoặc training-attested item mapping.
- [Discovery CPU trước T4](reports/akt_t4_discovery_readiness_20261108.md), commit `04b8ac1`:165source/lock hashes,44versions, cả hai cleanup accepted; **warm candidate, chưa CUDA/GPU ready**.53outputs raw Git verified; giữ timeout, failed discovery01 và scheme correction. Không cài lại venv/đổi hardware/Modal.

## Hiện hành08/11 — Linux CPU worker đã đóng (`1c52043`)

Mốc vận hành hiện tại là **Linux Gate24 771 PASS, 0 fail/error/skip** và **native CPU dummy 48 train targets / 8 validation predictions / 2 optimizer updates thật**, với **9 file đã lưu bền vững và khớp SHA**. [báo cáo](reports/akt_linux_worker_readiness_20261108.md), [bundle đã đóng](runs/akt-linux-worker-readiness-20261108-01/README.md), [manifest](runs/akt-linux-worker-readiness-20261108-01/manifest.json). Đã kiểm lại toàn bộ **194 output SHA** của bundle và 9 bản sao artifact. GKT03 (`b67eba0`) và các kết quả nghiên cứu phía dưới giữ nguyên phạm vi.

| Bằng chứng hiện tại | Kết quả đã xác minh | Phạm vi |
|---|---|---|
| Linux native Gate24 | 268.092342194s ≤ 600s; 771 PASS; Linux lock `60dad3de…35cc45a` | Software/source gate trên Linux CPU, không CUDA readiness. |
| Native CPU dummy | Phase 26.110794024s; 48 train targets/6 windows; 8/8 validation predictions, 0 unseen; 2 nonzero-gradient và 2 parameter-update steps; reload exact | Synthetic engineering, không research fitted efficacy, model selection/refit/resume hoặc RQ completion. |
| [Durable copy inventory](../experiments/akt/results/ctx-linux-20261108-01/transfer-copy-inventory.json) | 4 binary (448378 B) + 5 native text = 9 file khớp SHA/size trước–sau; checkpoint `f77b39c6…de8cc6` | Artifact Colab CPU đã hoàn tất, không local fit hoặc model/Parquet load. Binary giữ ngoài Git. |

**Lịch sử giữ nguyên:** Windows Gate22 768 PASS là **STALE sau test-only `dd80006`**; Gate23 763 PASS/5 FAIL và các failure loader/transport vẫn giữ verdict gốc. Các dòng “current”, “pending archive”, “chưa Linux Gate/mainworker” trong snapshot cũ phía dưới mô tả thời điểm trước mốc này. GPU09 còn **actual CUDA pending**; immutable image, CUDA lifecycle/resume và protocol S01/S04/S05 chưa được đóng bằng CPU proof. Không đánh dấu RQ hoàn tất hoặc GPU ready.

## Bổ sung08/11 — GKT04 và bản thảo C13 đã đóng

- **GKT04 — `2d8aaf8`:** [weights-only checkpoint report](reports/gkt_checkpoint_readiness_20261108.md), [bundle60outputs](runs/gkt-checkpoint-engineering-20261108-01/README.md), [manifest](runs/gkt-checkpoint-engineering-20261108-01/manifest.json). Final **40 PASS/0 fail/error/skip**; **2 actual Adam updates tổng hai trials** (1/trial), conservative **24,609858s ≤ 60s**, toàn bộ60outputSHA và source/test SHA đã kiểm lại. Trial01 vẫn **1PASS/39fixtureERROR** do quyền hard-link `WinError5`; trial02 cùng source/test được chạy trong bounded process đã được phép. Không đổi failure thành PASS hoặc gọi đây là source bugfix.
- **Phạm vi GKT:** GKT03 (`b67eba0`) vẫn là one train-batch/45tests/4updates/32outputs. GKT04 là followup hoàn tất weights-only save/load riêng, không thay giới hạn lịch sử của GKT03. Không optimizer/RNG/hidden-state restoration, resume, epoch/corpus, refit/selection hoặc fitted inference; scientific S04/S05 và baseline nghiên cứu đầy đủ vẫn pending.
- **WRITE02 hiện tại — `1b3d3f9`:** [bản thảo RQ1–RQ2](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) và [source map](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json) có **13 claims/80 JSON pointers/21 inputs** được kiểm. C13 chỉ tích hợp observability reproduction: **944/964 P changes giữ full preview**, **2/116 P-same rows đổi preview**, **22/1.080 full-preview changes**, actual shared queries1.080keys; ba seed families, **new independent N=0**. C01–C12/16inputs cũ và snapshot `d30dafe` giữ nguyên lịch sử; không backfill trace, causal/served-action/calibration claim hoặc RQ completion. Mốc Linux Gate24/CPU worker phía trên giữ nguyên.

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

## GKT03 train-batch08/11 — engineering, chưa epoch/corpus

`gkt-training-engineering-20261108-01`, commit `b67eba0`: **45CPUtests/32outputs/4actual Adam updates**, controller9,8446043s; conservative cumulative10,8446043s≤60 gồm1s dự trữ cho controller-only pre-import SyntaxError (0updates, retained). [Report](reports/gkt_training_readiness_20261108.md), [bundle](runs/gkt-training-engineering-20261108-01/README.md); manifest SHA `c1194df13f6f8f6efa41469264e6ced6447135bf389c2d03729a755d1ed14e0f`. Parent actual review, không independent reviewer agent. Source training `6def666d82cf02dfefcf8980c2670ac24f3a137a86e9093e66cb87bc2cabc4e5`, tests `1d4a9869d6b167e972c719df637b593171343e6d93fd55395925c7e0268392e0`. One explicit Adam batch/caller masks/preupdate-state binding; cooperative identities không nonresettable authorization; exception sau step không rollback/checkpoint. Chưa checkpoint/resume, epoch/corpus runner, fitted adapter/selection/refit/scientific S04/S05; không realdata/Holdout/GPU hoặc research efficacy/RQ completion. Không rerun model trong cập nhật chỉ mục.


## Sổ cập nhật08/11 — conditional edges, history bins và research IO

- **RQDIAG07**, commit `9efd5be`, 29outputs đã kiểm raw Git: [rq1_fixed_edge_set_contrast_20261108.md](reports/rq1_fixed_edge_set_contrast_20261108.md), [manifest](runs/rq1-fixed-edge-set-contrast-20261108-01/manifest.json). Conditional full–empty edge-set contrast: 1080 paired targets; ΔLL−0.000636974; PG bất lợi cả3seed,22preview changes; không causal learning effect.
- **RQDIAG08**, commit `ec88970`, 28outputs đã kiểm raw Git: [rq1_history_stratified_edge_contrast_20261108.md](reports/rq1_history_stratified_edge_contrast_20261108.md), [manifest](runs/rq1-history-edge-contrast-20261108-01/manifest.json). 304 descriptive cells từ1080 cached pairs; Hpast confounded time/order; concept-prior không train support; new independent N=0.
- **RESAUTH01**, commit `750921a`, 50outputs đã kiểm raw Git: [akt_research_execution_readiness_20261108.md](reports/akt_research_execution_readiness_20261108.md), [manifest](runs/akt-research-execution-engineering-20261108-01/manifest.json). 85 final pure guard tests; runtime/Gate mocked, chưa actual authorization/training/CUDA.
- **CORPUSIO01**, commit `47323e9`, 30outputs đã kiểm raw Git: [simulator_corpus_publisher_readiness_20261108.md](reports/simulator_corpus_publisher_readiness_20261108.md), [manifest](runs/simulator-corpus-publisher-engineering-20261108-01/manifest.json). 31 publisher tests với handmade temporary corpus; chưa actual research corpus; DONE-last không OS crash transaction.

Không cộng repeated targets/tests thành independent samples hoặc phần trăm hoàn tất. Reader timeout chưa JUnit và replay PID guard fail trước native được giữ riêng; không gắn PASS.
