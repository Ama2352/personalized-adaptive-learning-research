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
