# Ma trận claim–evidence

## Bổ sung09/11 — điều kiện đủ của zero re-entry

CLM-RQ1-REENTRY-20261109. Với DAG chỉ có cạnh nội chương, ready loại node đã đạt ngưỡng, update chỉ node được chọn và continuity giữ chương còn ready, tập đạt ngưỡng hấp thụ và mỗi chương xuất hiện tối đa một khối liên tiếp. Chứng minh áp dụng dưới giả thiết không forgetting/reset hoặc đổi graph. Phản ví dụ dựng tay có một cạnh B→A cho A→B→A dù chapter quotient không chu trình. Bốn test đã đạt trong0,2165947giây. [Chứng minh và giới hạn](reports/paper1_reentry_mechanism_20261109.md), [output kiểm](runs/paper1-reentry-mechanism-20261109-01/result.json). Còn phải đo tác động học tập và tần suất trong thí nghiệm theo PDF.

## Bổ sung09/11 — raw reference-mixture trên cùng logged stream

CLM-RQ1-REFMIX-20261109. Sai lệch khác chiều theo PG/PY/PYH còn xuất hiện khi kiểm raw mean của ba câu tham chiếu trên cùng lịch sử, câu hỏi và đáp án. ECE15 pooled full/empty0,043185/0,042526, PG0,263534/0,261267, PY0,131945/0,137415 vàPYH0,069198/0,075091. Mỗi arm dùng một Y cho một mean3forecast dưới source-design logger uniform84items. [Báo cáo](reports/rq1_reference_mixture_reliability_20261109.md), [manifest42outputs](runs/rq1-reference-mixture-reliability-20261109-01/manifest.json).

Phạm vi gồm1080query–Y từ9paired trajectories/3seedfamilies cũ,2160arm rows và0newindependentN. Decimal50digits đã kiểm mọi480bins/64strata. Chỉ response-mixture reliability hậu nghiệm, chưa masterytruth/calibrator hoặc causal learning benefit.


## Nhận định được cập nhật08/11 — tách diagnostic, corpus và trình bày

Các câu “chưa có result” trong snapshot cũ phía sau phải đọc theo thời điểm ghi; bảng mới này bổ sung kết quả hữu hạn, **không đóng RQ1/RQ2/RQ3 hoặc thay C01–C14**. [Báo cáo GVHD theo ngày](supervisor_reports/2026-11-08/01_tien_do/BAO_CAO.md) là bản đọc; số liệu gốc vẫn ở các bundles.

| Claim mới | Evidence/commit | Diễn giải được phép | Không được suy |
|---|---|---|---|
| CLM-HISTORY-AVAIL-20261108: available input history có thể đổi predictive/preview behavior | [Report](reports/rq1_history_availability_replay_20261108.md), [45output manifest](runs/rq1-history-availability-20261108-02/manifest.json), `8f95fd6`.27targets/108arms/54exact full-prefix controls;H100/L50 preview graph2/9 so full0/9. | Whole-policy input intervention gồm controller bookkeeping; ΔLLgraph không đơn điệu theo window; đủ profiles/negative cases và aliases. | Không causal practice/learning, KT-only history, general ability effect hoặc independent81nominal samples. P/S28/M/R/preview endpoint parity không full hidden-state historical proof. |
| CLM-DEV-WORKER-20261108: orchestration guard hoạt động trong scoped stubs | [27output manifest](runs/development-corpus-worker-engineering-20261108-01/manifest.json), [report](reports/development_corpus_worker_readiness_20261108.md), `509c955`;19PASS02,19setupERROR01 giữ nguyên. | Source/owner/RAM/input/publication-readback branches được kiểm bằng fake dependencies. | Không actual12.600teacher calls/corpus hoặc research efficacy từ manufactured counters. |
| CLM-DEV-CORPUS-20261108: corpus observable Development đã thực sinh và publish/readback | [48output manifest](runs/development-corpus-native-20261108-01/manifest.json), [report](reports/simulator_development_corpus_20261108.md), `1990d4c`;48/6/6learners×210events=12.600attempts/returns,17canonical files. | Có actual Development inputs tách roles; mỗi role84items/hai lớp. Train minima38learners/item,47/concept,45strict-prior learners trên756ordered pairs là coverage. | Không learned graph/OOF confidence/calibration/model fit hoặc final150evaluation. Oracle đã mở để hash opaque, không parse/modelinput; không giữ diễn đạt sai “chưa mở” của flag QA gốc. |
| CLM-CONTROLLED-ABILITY-20261108: graph×world-penalty interaction không nhất quán dương trong finite controlled design | [70output manifest](runs/rq2-controlled-ability-prerequisite-20261108-01/manifest.json), [all36Y/18Δ/9Ψ/6Ω](reports/rq2_controlled_ability_prerequisite_results_20261108.md), `8b6487c`. MeanΨ−0,007631/−0,035867/0 ởa1000/1150/1300. | Cùng residual/U, scalarability/estimator full–empty/λ0–.55; S1P1L0. Đơn vị mean NET theta/Elo28concepts/T41ngày. HighΨ0knownD0 nhưng highgraphΔλ0positive cả3blocks; không quy lợi ích graph chỉ cho true prerequisite mechanism. | Không observational profile DiD/external causal ability law/practical significance/CI/p-value. Δâm chỉ ít gain hơnempty, không necessarily dưới base. Các actions/labels có thể phân kỳ dù U step-coupled. |
| CLM-GVHD-NOTEBOOK-20261108: bản đọc theo ngày và notebook tự chứa | Current chỉ2file: [báo cáo](supervisor_reports/2026-11-08/01_tien_do/BAO_CAO.md), [notebook nghiên cứu](supervisor_reports/2026-11-08/01_tien_do/KET_QUA_NGHIEN_CUU.ipynb). **LỊCH SỬ2e63cd9** giữ26artifacts/8code cells/4SVG/22sources/40pointers và SHA0f2130…67620. | Bản hiện hành theo yêu cầu user là summary+fullresearch notebook; đã kiểm current notebook local16code cells/6SVG/73sources/58pointers, SHA `d7a7cbd61b242bf1434a19fbb0e24b28ec466bd317c41f90a31204bef53ae506`. Các phép so sánh vẫn lấy frozen evidence, không phát sinh researchN. | Không dùng cached-output acceptance/pins của2e63cd9 chứng nhận nội dung mới; không actual Colab/kernel/visualQA hoặc fittedmodel/RQcomplete từ presentation. |

Bốn bundles mới có190outputs đã hash lại; packet lịch sử2e63cd9 có26artifacts=25snapshotfiles+1chỉ mục; currentlayout chỉ2file, không26run outputs. Các accepted batches không thay failure/verdict lịch sử và không tự duyệt current full Gate/CUDA hay paid/fullCV/Holdout.


**RQ2/trap retention mới:** [readout separation](reports/rq2_retention_metric_separation_20261108.md), commit746c374, chứng minh khả năng soft-ranking reversal ở fixed constructed states; C08 net-theta identity giữ nguyên. Không reachablepolicy/graphbenefit/RQcomplete.

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

## CPU-RQ2-COMMON — Coverage và learner weighting

`runs/cpu-junyi-common-20261107-01/common_population.json` kiểm fixed-denominator learner/child diagnostic và identity negative control0. Chỉ1–7/239eligible learners có prior score đổi dưới mỗi control. Low exposure làm null comparison yếu; không suy graph neutral hoặc instructional benefit. `reports/cpu_common_population_20261107.md` ghi scope/estimand/attrition.

## CPU-SIM-KT-INTERFACE — Causal query/probe plumbing

Native AKT online/offline/geometry/OOV và session isolation được kiểm bằng synthetic fixtures và Paper2 bank metadata. Không là CG-AKT efficacy. Delayed-query invariance cho thấy native model không biết elapsed calendar time, không chứng minh latent retention bất biến. Source/export bug H3/T2 được tái hiện/sửa; historical predictions giữ nguyên. Xem simulator_kt_interface_20261107.md và runs/cpu-sim-kt-interface-20261107-01/02.

## CPU-SIM-DATA — Observable/oracle và role boundaries

`runs/cpu-sim-data-context-20261107-03` và `runs/cpu-sim-collector-20261107-04-portable`: schema chặn oracle fields, train-only vocabulary, current/future input-prefix guard, role-disjoint allocation, OOV/global-window/collator accounting. Đây là evidence phần mềm hỗ trợ tính hợp lệ cho RQ1/RQ3, không là predictive/learning benefit. Collector fixture24targets chỉ phủ22/84items; full corpus T10, mastery calibration và complete trainer vẫn mở. Không suy learner independence từ seed namespaces.

## CPU-SIM-DOMAIN — Checkpoint environment identity khi strip notebook output

`runs/cpu-sim-collector-trials-20261107-01/collector-domain-audit-01.json` xác nhận full storageSHA làm domainv1 khác dù mọi cellsource identical. Collectorv2 đã tách semantic definitions/constants/input/clock khỏi storage integrity;65targeted tests kiểm actual bundler, already-stripped copy và scientific-change negative controls. V1/v2oracle/RNG/query/label parity giữ nguyên trong fixture. Không là actual Linux/CUDA/Modal checkpoint handoff proof; runtime/Volume ladder vẫn bắt buộc. Đọc report simulator_collection_runner_20261107.md trước khi trích nhận định này.


## Phạm vi nhận định08/11 — conditional edges, history bins và research IO

- **RQDIAG07**, commit `9efd5be`, 29outputs đã kiểm raw Git: [rq1_fixed_edge_set_contrast_20261108.md](reports/rq1_fixed_edge_set_contrast_20261108.md), [manifest](runs/rq1-fixed-edge-set-contrast-20261108-01/manifest.json). Conditional full–empty edge-set contrast: 1080 paired targets; ΔLL−0.000636974; PG bất lợi cả3seed,22preview changes; không causal learning effect.
- **RQDIAG08**, commit `ec88970`, 28outputs đã kiểm raw Git: [rq1_history_stratified_edge_contrast_20261108.md](reports/rq1_history_stratified_edge_contrast_20261108.md), [manifest](runs/rq1-history-edge-contrast-20261108-01/manifest.json). 304 descriptive cells từ1080 cached pairs; Hpast confounded time/order; concept-prior không train support; new independent N=0.
- **RESAUTH01**, commit `750921a`, 50outputs đã kiểm raw Git: [akt_research_execution_readiness_20261108.md](reports/akt_research_execution_readiness_20261108.md), [manifest](runs/akt-research-execution-engineering-20261108-01/manifest.json). 85 final pure guard tests; runtime/Gate mocked, chưa actual authorization/training/CUDA.
- **CORPUSIO01**, commit `47323e9`, 30outputs đã kiểm raw Git: [simulator_corpus_publisher_readiness_20261108.md](reports/simulator_corpus_publisher_readiness_20261108.md), [manifest](runs/simulator-corpus-publisher-engineering-20261108-01/manifest.json). 31 publisher tests với handmade temporary corpus; chưa actual research corpus; DONE-last không OS crash transaction.

Không cộng repeated targets/tests thành independent samples hoặc phần trăm hoàn tất. Reader timeout chưa JUnit và replay PID guard fail trước native được giữ riêng; không gắn PASS.


### RQ1 — readiness không chỉ phụ thuộc boolean mastered

[Phân tích exposure](reports/rq1_ready_set_exposure_results_20261108.md), [bundle](runs/rq1-ready-set-exposure-20261108-01/README.md): trên3240current-source served actions,500roots táchriêng;2740nonroots gồm2041cần ngoại lệ đã chọn≥6lần và699thỏa mastery của mọi parent. ExactreturnedR/order3240; không observedfallback/outsideR. Rule đã công bố Paper2; đóng góp là footprint từcache, không phát hiện rule mới, causal masking fraction, calibration sai, hypothetical strict-only action hoặc learning benefit.
