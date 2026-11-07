# Tiến độ nghiên cứu

**Vòng tiếp theo đang làm:** SAKT03 và SIMTRAIN01 chỉ dùng dữ liệu giả để kiểm kỹ thuật. Module/test AKT mới cần Gate19 sau freeze; Gate18 bên dưới là snapshot nguồn đã kiểm trước batch mới, không tự áp dụng cho nguồn đang sửa. Colab CPU chờ xác nhận frontend, chưa remote call/GPU/Modal.

## Snapshot engineering08/11 — xem giới hạn từng bằng chứng

Gate18 WindowsCPU661PASS; real-guard watchdog toy lifecycle48targets/2updates/8predictions đã kiểm. **Actual new-worker Linux/CUDA và GPU08fullhashlock/image vẫn thiếu**, chưa Gate4/fulltraining. GKT43PASS purekernel vẫn incomplete; demo53PASS+visualQA là storedsynthetic replay/partialE11; bản thảo phương phápRQ12 đã cósourcesmap. RQ1/RQ2 chỉ pilot/descriptive, RQ3 chưa fittedcomparisons. [Context report](reports/akt_worker_context_readiness_20261108.md), [demo](reports/demo_readiness_20261108.md), [GKT](reports/gkt_core_readiness_20261108.md), [thesisdraft](reports/THESIS_METHODS_RQ12_DRAFT_20261108.md). No Modal credit used by batch, no Holdout or external sending. Các snapshot cũ dưới đây là lịch sử, không thay current verdict.


**Trạng thái hiện tại — 07/11/2026:** đọc dashboard này trước các snapshots lịch sử bên dưới. Đề cương và Paper1/2 đã tìm được; lịch sử04/11 “chưa thấy” không còn mô tả inventory hiện tại. Không dùng các số test/version của snapshot cũ thay nghiệm thu mới.

| Phạm vi | Trạng thái dựa bằng chứng hiện tại | Việc còn thiếu |
|---|---|---|
| RQ1/RQ2 | PARTIALLY VERIFIED: source diagnosis, fixed-stream/closed-loop pilots, factorial và Junyi controls; đã tổng hợp với giới hạn | Final estimands, đủ mechanism exposure, controlled inference và S04/S05; không causal graph-benefit claim |
| Paper1 | Audit PDF/source/Git/archives hoàn tất trong phạm vi local; exact submitted revision vẫn thiếu | Source+inputs+actual seed list+per-seed outputs và xác nhận tác giả/advisor |
| AKT graph-free | Actual Colab T4 bounded CUDA lifecycle/recovery PASS; local Gate15462pass, Colab CPU505pass/2declared exclusions | Linux/CUDA mainworker contract, representative pilot/throughput, full Development protocol; Gate4false |
| Graph residual/gate | Kernel độc lập42tests pass, reuse causal context guards, graph-off parity | Chưa native AKT integration, learned gate/confidence training hoặc CG-AKT result |
| SAKT | Paper-equation core37CPUtests pass,0optimizersteps | Adapter/trainer/export/resume/final protocol; không full baseline benchmark |
| GKT và required comparisons | Yêu cầu đề cương giữ nguyên | GKT và các evaluation pipelines còn phải triển khai/kiểm; không tự loại baseline |
| Modal | 30USD free credits do user báo,0USD trả thêm; **chưa dùng compute/credits** | Runtime/image/Volume/budget controls và exact approved run allocation |

Đọc [nghiệm thu CUDA](reports/colab_cuda_acceptance_20261107.md), [phản biện](reports/colab_cuda_adversarial_review_20261107.md), [RQ1/RQ2 synthesis](reports/rq12_evidence_synthesis_20261107.md) và [mục lục bằng chứng](EVIDENCE_INDEX.md). Heavy artifacts giữ tại `experiments/akt/results/colab-actual-cuda-20261107-01/`; không nhầm software acceptance với hoàn thành RQ. Next task làGPU06 trong backlog, chưa launch training/Modal.

## Batch tiếp theo: runtime và worker đã được kiểm trên CPU

- **Gate17:513pass,0fail/error/skip**,269,98s; tách với Gate16failed512pass1fail và giữ bằng chứng đường dẫn. Không actualLinux/CUDAworker pass từ mocks.
- [Runtime report](reports/akt_linux_runtime_contract_20261107.md) và [worker report](reports/akt_main_worker_lifecycle_20261107.md): platform-aware strictvenv metadata; actualsyntheticParquet→8train targets→validation/checkpoint/export4rows. Chưa Junyi pilot hoặc fulltraining.
- [SAKT adapter](reports/sakt_adapter_readiness_20261107.md):89CPUtests gồm payloadregressions; random/unverified weights không fitted baseline, trainer/completebridge còn thiếu.
- Current backlog chuyển GPU07→GPU08→GPU09. Không dùng creditModal hoặc GPU trongbatch; kết quảT4trước đó thuộc frozenkitv12.

## Thành quả báo cáo GVHD08/11

[Báo cáo tiến độ](reports/BAO_CAO_TIEN_DO_GVHD_20261108.md) đã có claim/source/limitations và S01/S04/S05. RQ1 mới xác minh944/964 scalar-probability-changed snapshots giữ concept preview; RQ2 mới cho thấy PYH−PY không robust dưới LOO và Junyi pooled-rate sensitivity do denominator. Đây là descriptive/exploratory diagnosis, chưa hoàn thành RQs. Hai analyzer có25+27synthetic tests đạt, stored-input SHA/reproduction checks đã lưu. Nhánh AKT đang triển khai immutable worker context và bounded CUDA phase; chưa có actualCUDA-mainworker hoặc creditModal run mới.

## Snapshot ngày04/11 và nhật ký cập nhật tiếp theo


**Cập nhật:** 2026-11-04. Trạng thái theo evidence workspace và RQ/sprint từ yêu cầu người dùng; repo không có proposal/advisor feedback để xác minh wording chính thức.

## Dashboard

| Phạm vi | Trạng thái công việc | Xác minh | Bằng chứng và giới hạn |
|---|---|---|---|
| Junyi/BKT baseline | EXPERIMENTALLY VALIDATED | VERIFIED | BKT CV/refit/Test; Test dùng một lần, không tuning. |
| GAM-KT graph-free | EXPERIMENTALLY VALIDATED | VERIFIED | Pilot, 5-fold CV, common-row và learner bootstrap; Development only. |
| AKT graph-free | TECHNICALLY VALIDATED; pilot FAILED | VERIFIED | Gate 2 155 tests pass và bounded smoke; pilot 14-02 failed trước validation/export. Không có benchmark. |
| Graph-GAM-KT, SAKT, GKT | NOT STARTED trong scope tìm thấy | MISSING | Không thấy implementation/run trong source, experiments và reports đã kiểm tra. |
| Fixed-graph AKT, CG-AKT | NOT STARTED trong scope tìm thấy | MISSING | Chưa thấy graph-aware AKT implementation/result. |
| Grade 10 simulator/policy loop | NEEDS REVIEW | MISSING | Không thấy simulator/output; Junyi prerequisite catalog không thay thế simulator. |

## RQ coverage

| RQ | Coverage | Đã hỗ trợ | Còn thiếu |
|---|---|---|---|
| RQ1 — vì sao prerequisite graph không ổn định | Chưa trả lời | BKT/GAM predictive baselines; Junyi catalog metadata sơ bộ. | Graph on/off, threshold calibration, decision transitions, policy effects. |
| RQ2 — điều kiện graph có ích/trung tính/có hại | Chưa trả lời | Metadata/sparsity mô tả, không phải controlled experiment. | Graph perturbation/quality, history/cold-start/profile strata, edge confidence. |
| RQ3 — CG-AKT | Chưa trả lời | AKT source, Gate 2 và bounded smoke kỹ thuật. | Full AKT benchmark, fixed graph, CG-AKT, ablations, robustness, closed loop. |

## Sáu sprint

| Sprint | Trạng thái | Bằng chứng | Còn thiếu |
|---|---|---|---|
| 1. Nền tảng/tái lập | NEEDS REVIEW | Research notes, protocol, data audit, RIVF source artifact | Literature protocol, proposal/advisor text, simulator reproduction. |
| 2. Dữ liệu/baselines | IN PROGRESS | Junyi, splits/eval, BKT, GAM; AKT technical work | AKT benchmark, Graph-GAM, SAKT, GKT; simulator chưa thấy. |
| 3. RQ1 diagnosis | NOT STARTED | Predictive BKT/GAM differences | Threshold, decision/policy decomposition, graph ablations. |
| 4. RQ3 method | NOT STARTED | AKT graph-free technical integration | Fixed graph, confidence/gating/fallback, CG-AKT, ablations. |
| 5. RQ2/RQ3 evaluation | NOT STARTED | Bootstrap cho baseline pair, không thay graph study | Perturbation, strata, closed loop, retention/mastery, planned inference. |
| 6. Consolidation | NOT STARTED | Baseline report | Thesis claims, final tables, demo, reproducibility/publication package. |

## Ưu tiên

1. Điều tra lỗi lưu progress AKT; không diễn giải pilot hiện tại thành epoch hoàn tất.
2. Chốt benchmark AKT graph-free, Development-only checkpoint selection và comparability trên 5 folds.
3. Xác minh simulator Grade 10 và graph source.
4. Đăng ký trước graph variants, history/profile strata, mastery thresholds và statistical plan.

## Cập nhật CPU07/11/2026

Adapter nguồn Paper2, explicit mastery trace, matched graph và integrity verifier đã được kiểm. RQ1/RQ2 còn thiếu controlled factorial, Junyi order analysis và inference.

## Pilot CPU09/10 và refit07/11/2026

User chấp thuận bounded pilot trước execution. Xem reports/cpu_pilots_20261107.md về factorial và Junyi order, gồm cơ chế PG không hoạt động trong cohort và cycle witness của catalog thô. Engineering snapshot ở runs/cpu-readiness-pathways-20261107-01, không đồng nghĩa GPU/full-training acceptance.

## Matched-control exposure07/11/2026

Run32learner và run mở rộng256learner có notes/manifests riêng. Xem reports/cpu_matched_controls_20261107.md. Source controls giữ degree/topic/area/prefix-support-bin counts, còn learner-level co-observation thay đổi. Không suy graph neutral từ controls thiếu exposure. Mở rộng256×300/180s do user giao lựa chọn sau proposal cụ thể.

## Portable-kit và Gate2 cuối batch07/11

Kitv6 có113source/fixture files, source-only notebook copies và project venv. Manifest comparison chỉ ra AKT/shared v6 giống v5 đã kiểm240passed1deselected; GAMv6 đạt31passed1deselected. Hai local integration exclusions được ghi rõ. Actual Colab/CUDA chưa chạy. Main Gate2 đạt241test khôngskip. Tất cả log thành công/thất bại của batch ở runs/cpu-controls-portability-20261107-01.

## Recovery CLI và common-population07/11, cập nhật mới

AKT public smoke/pilot recovery đã nối và kiểm trên actual CPU model/parent-worker synthetic fixture; chưa real-data/GPU. Xem `docs/thesis_recovery/17_AKT_RECOVERY_ENGINEERING_LOG.md`. RQ2 có descriptive learner/common-opportunity analysis tái dùng3controls, chưa confirmatory protocol; xem `reports/cpu_common_population_20261107.md`. RQ1/RQ2 còn PARTIAL, RQ3 chưa trained/evaluated. Các Gate2 số test ở mục trước là snapshot lịch sử, build mới cần refresh.

### Nghiệm thu engineering cuối07/11

REC01–REC06 và CPU11 completed **CPU synthetic only**. Source-bound Gate2-08 đạt274pass, pointerverified; GAM riêng45pass. HaiCLI cases có artifact-level exact model/Adam/RNG/prediction proof,85targets/3steps/9predictions/case. Source Paper1/2 và historical results giữ nguyên. RQ1/RQ2 vẫn PARTIAL; fixed/CG-AKT, required comparators và controlled final experiments chưa được hoàn tất từ software tests. Kitv7 mới chỉ ZIP integrity, chưaactualColab/CUDA.

## Interface simulator–KT và batching, cuối07/11

SIM01–SIM05 completed CPU engineering: source bank28concept/84item,168synthetic train targets/1update cho fixture, predict-before-update/session/reset/snapshot/domain guards, fixed duplicate-window export và independent batching84→42calls. Gate2-10 296pass/no fail/error/skip. Xem reports/simulator_kt_interface_20261107.md và runs/cpu-sim-kt-batch-gate-20261107-01. Raw correctness score chưa là mastery, native AKT không nhận elapsed time; research/CG-AKT/GPU readiness không nâng theo software pass. V9 kit ZIP-only, khôngremoteexecution.

## DATA01–04: split/schema và graph-context boundaries, cập nhật cuối07/11

Completed CPU engineering,70targeted tests và Gate2-11 mới361pass0fail/error/skip152.84giây. Có4-role split với explicit namespaces/RNG, observable schema/oracle guards và role-shard coverage; graph context reuse AKT effective-window/OOV, full-history sensitivity riêng, confidence provenance/off/empty/zero controls. Bundles cpu-sim-data-context-20261107-01/02/03 và cpu-sim-data-context-gate-20261107-01 giữ logs/proofs/hashes. Source-only finding: Paper2 latent base parent-smoothed và replay item chọn theo theta thật; collector phải giữ base realization và tách oracle sidecar. Xem report simulator_data_graph_boundaries_20261107.md và contract19. Chưa generate research cohort/train CG-AKT hoặc đo GPU; S04/S05 vẫn pending. V9 không chứa source mới.

## DATA05–07: collector/adapter và domain portability, current software gate07/11

Completed CPU engineering: train-only collector≤2×12fixture, source-environment replay và oracle separation, role-aware KT windows/collator khôngfoldJunyi, versionedsemantic domain đểstripnotebookoutputs không đổi môi trường. Giữ RNGnamespacev1, v1/v2oracle/RNG/query/labels exact.65targeted tests và finalGate2-13 **401pass/no fail/error/skip374.53s**; prior396 là snapshotv1. Archive cpu-sim-collector-gate-20261107-01 và report simulator_collection_runner_20261107.md. V10sourcekit135files ZIP/sourceparity-only, chưaactualLinux/Colab/CUDA.24targets chỉ22/84items, không fullcorpus/T10/fulltrainer hoặc graphmodels/RQbenefit. S04/S05 vẫnpending; các comparator/model/confirmatory deliverables chưa được bỏ.

## COLAB01 — current software gate và recovery,07/11

Gate2-14 **407passed,0fail/error/skip169.05s**, thay401current sau sửa CPU-normalization CUDA RNG state. Probe production train_epoch chạy CPU3processes5vs2+3updates/17targets: model/Adam/RNG/sampler/predictions exact, khôngskip/duplicate.19notebookguardcases giả lập đạt,kitv11 137files cóSHA/CRC/sourceparity. Xem [báo cáo](reports/colab_recovery_readiness_20261107.md), bundles cpu-colab-recovery-20261107-01 và cpu-colab-recovery-gate-20261107-01. Không actualColab/CUDA/Modal compute hoặc credits; chưa hard-kill/Volume durability/Gate4/RQefficacy. RQ1/2 vẫnPARTIAL,RQ3model/evaluation chưahoàn tất.
