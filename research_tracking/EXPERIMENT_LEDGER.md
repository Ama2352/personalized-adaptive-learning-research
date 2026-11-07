# Sổ cái thí nghiệm

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
