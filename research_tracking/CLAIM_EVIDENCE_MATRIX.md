# Ma trận claim–evidence

| Claim | Claim/RQ | Experiment | Evidence | Scope/verification | Diễn giải được phép | Không được kết luận |
|---|---|---|---|---|---|---|
| CLM-001 | BKT predictive baseline trên Junyi Dev | EXP-BKT-CV-20261015 | E-002, E-003, E-006 | 5-fold Development; VERIFIED | Mean-of-fold AUC .7834134107927653, LL .3756074974398662, Brier .11510534239887318, ECE .0022408926425045916, Acc .8474159098322505. | Không suy ra mastery/policy effect hoặc ngoài protocol. |
| CLM-002 | Holdout BKT metrics được ghi nhận | EXP-BKT-TEST-20261015 | E-005, E-006 | 49,522 Test users; VERIFIED | Raw JSON metrics giữ làm frozen record. | Không dùng Test chọn config hoặc gọi untouched. |
| CLM-003 | BKT outperformed GAM graph-free trên common Development rows | EXP-GAM-CV-20261018 | E-002, E-007, E-008, E-011 | 20,706,014 rows; VERIFIED | BKT hơn về mean AUC/LL/Brier/ECE/accuracy trong benchmark này. | Không nói BKT luôn hơn mọi GAM/neural model; không kết luận graph effect. |
| CLM-004 | Bootstrap hỗ trợ GAM−BKT khác biệt ở bốn metrics | EXP-GAM-BKT-BOOT-20261030 | E-010, E-011 | 1,000 resamples/fold; VERIFIED | LL/Brier/ECE/accuracy CI95 loại 0 conditional trên 5 folds/fits. | Không claim paired AUC significance; lưu ý Holm/training variability. |
| CLM-005 | AKT bounded smoke hoàn tất technical path | EXP-AKT-SMOKE-20261101-03 | E-013, E-014, E-016 | 11 train + 16 validation learners; VERIFIED | 549 export, 441 fitted/108 unseen, exact checkpoint reload. | Không phải AKT benchmark/CV; không ngoại suy unseen rate. |
| CLM-006 | AKT Gate2 pass tại snapshot hash-bound | EXP-AKT-GATE2-20261104 | E-012 | 155 synthetic tests; VERIFIED theo Gate evidence | Technical checks của snapshot được ghi nhận. | Không chứng minh full Junyi predictive quality. |
| CLM-007 | AKT pilot14-02 không tạo validation/prediction result | EXP-AKT-PILOT-20261104-02 | E-018, E-019 | Terminal failed; VERIFIED | Partial telemetry rồi persistence error; không epoch complete/validation/export. | Không dùng partial loss/throughput như benchmark. |
| CLM-008 | Chưa có evidence graph benefit/harm trong scope | No qualifying experiment | E-011, E-025 | MISSING; absence không phải zero effect | RQ1/RQ2/RQ3 còn mở về graph. | Không kết luận graph vô ích từ thiếu run. |
| CLM-009 | Chưa có CG-AKT/fixed-graph AKT evidence | No qualifying experiment | E-025, E-027 | MISSING trong source/run scope | RQ3 chưa kiểm tra. | Không coi planned method/upstream paper là repo result. |

## Truy vết hai chiều

- RQ1 → graph-on/off, calibration/threshold, decision/policy → chưa có qualifying run; CLM-001/003 là nền tảng graph-free.
- RQ2 → graph quality/perturbation/history/profile → chưa có result.
- RQ3 → AKT Dev benchmark → fixed graph → CG-AKT/ablations → hiện chỉ Gate2/smoke và pilot failure.
- E-002…E-006 → BKT CV/refit/Test → CLM-001/002.
- E-007…E-011 → GAM CV/bootstrap → CLM-003/004.
- E-012…E-019 → AKT technical/smoke/pilot attempts → CLM-005/006/007.

## Cập nhật CPU07/11/2026

CPU-RQ1-CHAIN, CPU-RQ1-PACKAGE, CPU-RQ2-RETENTION, CPU-RQ2-REENTRY, CPU-RQ2-NULL và CPU-REPRO được định nghĩa tại reports/cpu_rq12_20261107.md. Chưa là final instructional benefit.

## Pilot CPU09/10 và refit07/11/2026

User chấp thuận bounded pilot trước execution. Xem reports/cpu_pilots_20261107.md về factorial và Junyi order, gồm cơ chế PG không hoạt động trong cohort và cycle witness của catalog thô. Engineering snapshot ở runs/cpu-readiness-pathways-20261107-01, không đồng nghĩa GPU/full-training acceptance.

## Matched-control exposure07/11/2026

Run32learner và run mở rộng256learner có notes/manifests riêng. Xem reports/cpu_matched_controls_20261107.md. Source controls giữ degree/topic/area/prefix-support-bin counts, còn learner-level co-observation thay đổi. Không suy graph neutral từ controls thiếu exposure. Mở rộng256×300/180s do user giao lựa chọn sau proposal cụ thể.
