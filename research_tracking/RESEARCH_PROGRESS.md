# Tiến độ nghiên cứu

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
