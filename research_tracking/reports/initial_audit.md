# Báo cáo kiểm toán nghiên cứu ban đầu

**Ngày kiểm toán:** 2026-11-04  
**Project root:** D:\Dev\KLTN  
**Vai trò:** auditor độc lập; chỉ đọc workspace và tạo tài liệu trong research_tracking/.

## A. Tình trạng nghiên cứu điều hành

- **Đã triển khai:** BKT standard, GAM-KT graph-free và AKT graph-free. Chỉ BKT/GAM-KT có benchmark Junyi Development hoàn tất. AKT source/config/tests tồn tại nhưng đang Git-untracked; run evidence nằm trong ignored paths.
- **Đã xác minh kỹ thuật:** BKT/GAM artifacts có manifests. GAM parity được ghi trong protocol/test. AKT Gate 2 ghi 155 passed in 66.20s; smoke run smoke-task13-20261101-03 hoàn tất train/checkpoint/validation/export ở cohort nhỏ.
- **Đã xác minh thực nghiệm:** BKT có 5-fold Development CV, final Development refit và holdout Test evaluation. GAM-KT có pilot, 5-fold Development CV common-row và paired learner bootstrap.
- **Đang tiến hành:** AKT integration/pilot work là mục tiêu của implementation agent. Pilot mới nhất quan sát được đã terminal failed; chưa có AKT full benchmark. Audit không xác định process nào còn chạy hiện tại.
- **Chưa xác minh/chưa thấy:** Graph-GAM-KT, SAKT, GKT, fixed-graph AKT, CG-AKT, graph perturbation/quality/history subgroup, mastery decision/policy analysis và closed-loop simulator results.

## B. Phạm vi bằng chứng workspace

Filesystem discovery bao phủ roots dataset/, artifacts/, experiments/, reports/, drive-download-20261018T084013Z-1-001/, papers/, _context/, src/, scripts/, tests/, docs/, cùng metadata .wsl/, venv/, .venv/. Đã đọc .gitignore, .gitignore lồng tìm thấy, .git/info/exclude, git status, tracked/untracked/ignored path listings và git check-ignore cho các vùng trọng yếu.

Các vùng ignored có evidence nghiên cứu:

- dataset/: raw Junyi, exercise table, relationship annotations và profiling HTML.
- artifacts/bkt_baseline/ và experiments/bkt_baseline/results/: CV, final refit, Test, split/derived data; Git listing có khoảng 9,765 files trong BKT result tree.
- artifacts/gam_kt/ và experiments/gam_kt/results/: sidecar/source-map/integrity, pilot/CV, fallback/common-row artifacts.
- artifacts/akt/ và experiments/akt/results/: Gate/preflight, temp, smoke outputs, partial pilot.
- papers/ và drive-download-.../: local survey/PDF/RIVF source artifact; không sao chép nội dung.

Git status đồng thời cho thấy AKT source/config/test/docs untracked và .gitignore/AKT plan modified. Audit không sửa file ngoài research_tracking/.

Không đọc toàn bộ 2,668,566,436-byte ProblemLog, tất cả prediction shards, toàn bộ BKT tree, WSL VHDX/cache/môi trường ảo. Global Git exclude tại C:\Users\AmaDev\.config\git\ignore bị từ chối quyền; repo-local exclusions vẫn kiểm tra được. Pilot 14-02 chỉ đọc sau khi metadata cho thấy last write 17:28 và manifest terminal failed; không poll/re-read. Chi tiết E-001…E-028 trong EVIDENCE_INDEX.md.

## C. Tiến độ theo mô hình

### BKT

- **Implementation/protocol:** standard CAHLR/pyBKT 1.4.3 C++, một model/exercise, target correct, seed/config frozen; manifest lưu runtime/hashes.
- **Execution:** Development 5-fold CV complete; final refit 720 exercise models; holdout Test evaluated once.
- **Kết quả VERIFIED:** CV AUC 0.7834134107927653 ± 0.0011584741219760302; Log Loss 0.3756074974398662 ± 0.0015747963998997052; Brier 0.11510534239887318 ± 0.0005760560410811493; ECE 0.0022408926425045916 ± 0.0007188307862958956; Accuracy 0.8474159098322505 ± 0.000748281088585296. Test AUC 0.7853401389315783, Log Loss 0.37411719753644507, Brier 0.11467086826208853, ECE 0.002303197682958907, Accuracy 0.8476443448639567.
- **Coverage:** CV 20,706,014/20,706,208; Test 5,218,336/5,218,345. Mười một final exercise fits chạm maxiter=100.
- **Giới hạn:** Test đã xem nên giữ làm frozen record; không chọn cấu hình bằng Test. Audit không chạy lại pipeline.
- **Mốc tiếp:** giữ làm baseline fixed; báo convergence warning và denominator/unseen policy.

### GAM-KT

- **Implementation:** graph-free Junyi model từ RIVF notebook cell 11 cùng adapter/protocol; source parity có tài liệu/test.
- **Execution:** pilot 2,000 users và 5-fold Development CV complete; không dùng holdout.
- **Matched common rows:** 20,706,014. GAM AUC 0.7748662971439921; Log Loss 0.3948808855161685; Brier 0.12037155187421189; ECE 0.05554197784523786; Accuracy 0.8414529934200823. BKT có mean tốt hơn ở cả năm metric trong benchmark được ghi.
- **Coverage:** native predictions 20,706,208, có 194 global-difficulty fallback; native metrics không cùng fitted population với common comparison.
- **Bootstrap:** 1,000 learner-clustered draws/seed 20261030 cho LL/Brier/ECE/Accuracy có CI loại 0; chưa có paired AUC CI hoặc Holm trong JSON.
- **Giới hạn:** chỉ predictive Development benchmark; không bật graph/policy; không giải thích nguyên nhân.
- **Mốc tiếp:** dùng làm graph-free comparator với common-row/supported metrics.

### AKT graph-free

- Source integrated; provenance ghi upstream commit 01b7e8d7d7c862cabc9467108e3e7f2555653a88; Gate 2 PASS với hash-bound source/lock/test evidence.
- Smoke smoke-task13-20261101-03 COMPLETED: 11 train learners/4,096 targets; 16 validation learners/549 targets; 12 steps/48 windows; export đủ 549 rows, 441 fitted/108 unseen; checkpoint reload state exact. Đây là technical smoke.
- Pilot pilot-task14-20261104-02 FAILED sau 32 batches/7,346 targets optimized; PermissionError [WinError 5] khi replace progress. complete_epoch=false; không validation, checkpoint, prediction export hay metric.
- Pilot 14-01 bị chặn trước launch bởi RAM preflight. Smoke 10-31-01 incomplete do export; smoke 10-31-02 bị RAM floor; smoke 11-01-03 pass.
- **Mốc tiếp:** điều tra lỗi progress persistence; run mới chỉ theo authorization/config mới. Sau đó cần full Development benchmark/comparison.

### Các model còn lại

Không tìm thấy Graph-GAM-KT, SAKT, GKT, fixed-graph AKT hoặc CG-AKT source/run/output phù hợp trong project roots đã kiểm tra. Phân loại MISSING trong scope này, không kết luận không tồn tại ngoài workspace.

## D. Thí nghiệm đã xác minh

1. **BKT Development CV:** năm fold learner-disjoint, 20,706,208 validation interactions. Metric exact như mục C; manifest complete/frozen. Hỗ trợ baseline predictive trên Junyi Development; không trả lời graph/policy RQ.
2. **BKT refit + Test:** 720 models trên Development; Test 49,522 learners/5,218,345 rows, 9 unseen. Test metrics như mục C; frozen holdout, không dùng tuning.
3. **GAM-KT pilot/CV:** pilot 216,677 rows; full CV 20,706,208 rows. Native fallback 194; common rows 20,706,014. BKT common-row mean tốt hơn ở 5 metrics trong benchmark này.
4. **GAM−BKT bootstrap:** estimand unweighted mean fold-level difference; resample learner trong fold; 1,000 reps, seed 20261030. Log Loss diff +0.01927338807630231 (CI [0.01877985121496039, 0.019729975709771537]); Brier +0.005266209475338718 ([0.005095943691713719, 0.005412828935142605]); ECE +0.0533010852027333 ([0.052169595268879654, 0.05382637666200834]); Accuracy −0.0059629164121681785 ([−0.0062013687903859525, −0.005701726892075646]). Dấu là GAM−BKT; GAM có LL/Brier/ECE cao và accuracy thấp ở estimand này. Không có AUC CI.
5. **AKT Gate 2/smoke:** xác nhận kỹ thuật ở snapshot và bounded cohort nhỏ, không tạo predictive comparison. Pilot AKT không hoàn tất và không có metric benchmark hợp lệ.

## E. So sánh và validity

- **Matched:** BKT–GAM Development common-row, frozen assignments/folds, target correct, source_row alignment, 20,706,014 fitted/common rows. 194 GAM fallback rows tách khỏi common. CV JSON ghi no holdout.
- **Không matched/không gộp:** GAM native có fallback; BKT Test không so với GAM Test; AKT smoke/partial pilot không so với BKT/GAM benchmark.
- **Protocol:** BKT/GAM docs/manifests ghi learner-disjoint, sequential predict-before-update, chronology; auditor chưa replay predictions hoặc kiểm hết parquet joins. AKT causal/OOV/masking có synthetic Gate 2 evidence, chưa full benchmark.
- **Thống kê:** fold mean±SD là mô tả, không phải CI. Learner bootstrap có điều kiện trên năm folds/fits; thiếu paired AUC CI, Holm và retraining variability. Không claim equivalence/causal effect.
- **Leakage:** chưa thấy leakage được xác nhận trong manifests đã mở; không phải proof độc lập toàn pipeline. Graph/policy semantics chưa đánh giá.

## F. Research Question coverage

- **RQ1:** chưa trả lời. Có baseline predictive differences; chưa graph on/off, threshold calibration, decision flips hoặc policy decomposition.
- **RQ2:** chưa trả lời. Có candidate prerequisite metadata, không có controlled graph-quality/noise/history/cold-start/profile experiment.
- **RQ3:** chưa trả lời. AKT kỹ thuật chưa benchmark; fixed graph/CG-AKT/ablation/closed loop chưa thấy. Smoke không phải predictive result.

## G. Sprint matrix

| Sprint | Trạng thái | Bằng chứng | Thiếu |
|---|---|---|---|
| 1 Foundation/reproduction | NEEDS REVIEW | _context, data readiness audit, survey report, RIVF GAM source | Proposal/advisor, literature protocol, simulator reproduction. |
| 2 Data/baselines | IN PROGRESS | Junyi, frozen split/eval, BKT, GAM; AKT gate/smoke | AKT full benchmark, Graph-GAM, SAKT, GKT; Grade10 simulator. |
| 3 RQ1 diagnosis | NOT STARTED | BKT/GAM predictive benchmark | Threshold/decision/policy breakdown, graph effect. |
| 4 RQ3 method | NOT STARTED | AKT graph-free technical integration | Fixed graph, confidence/gating/fallback, CG-AKT, ablations. |
| 5 RQ2/RQ3 evaluation | NOT STARTED | Baseline bootstrap | Perturbation/history/profile/cold-start, closed loop, retention/mastery. |
| 6 Consolidation | NOT STARTED | Baseline report | Thesis claims, final tables/demo/reproducibility/publication package. |

## H. Khoảng trống trọng yếu

1. Không có graph-on/off/quality experiment: thiếu bằng chứng trực tiếp cho mọi claim về graph.
2. AKT pilot lỗi lưu progress; chưa có epoch hoàn chỉnh/validation/export.
3. Chưa tìm thấy simulator Grade 10/graph và closed-loop outputs.
4. Thiếu threshold-to-decision/policy analyses; predictive score không giải thích mastery outcome.
5. Graph prerequisite chưa được xác nhận gold/edge reliability/KC mapping.
6. BKT có 11 fits chạm maxiter; bootstrap chưa có training randomness/AUC interval/multiplicity correction.
7. Dataset/results local-only/ignored; global Git exclude không truy cập được, làm giới hạn portability/discovery.

## I. Tracking files

- README.md: vai trò, evidence levels, lifecycle và update rules.
- KE_HOACH_KIEM_TOAN.md: scope và các bước audit.
- RESEARCH_PROGRESS.md: dashboard RQ/model/sprint.
- EXPERIMENT_LEDGER.md: chronology run.
- EVIDENCE_INDEX.md: inventory và Git classification.
- VALIDITY_AUDIT.md: verdict/remediation.
- RESEARCH_GAPS.md: gap ưu tiên.
- DECISION_LOG.md: quyết định có nguồn.
- CLAIM_EVIDENCE_MATRIX.md: claim→experiment→artifact.
- experiment_registry.json: schema 1.0.0 registry.
- reports/initial_audit.md: báo cáo này; future reports tạo file riêng.

## J. Hành động tiếp theo

### Agent 1

1. Điều tra PermissionError ở atomic progress replace, giữ nguyên run cũ và chỉ chạy ID/config/auth mới khi hợp lệ.
2. Tách technical smoke/pilot khỏi benchmark; benchmark phải có complete prediction/export/metric provenance.
3. Manifest run mới cần source/config/data identity, split, train/validation counts, checkpoint selection, seed, command và metrics.

### Nhóm nghiên cứu

1. Xác nhận proposal chính thức, simulator Grade 10 và graph provenance/permission.
2. Định nghĩa node/edge/ground truth, confidence/noise variants và graph comparisons trước khi chạy.
3. Đăng ký mastery thresholds, decision/policy metrics, history/proficiency strata, seeds/paired analysis và multiplicity plan.
4. Dùng common Development folds/population/target/timing; tách predictive, decision, closed-loop claims.

### Auditor Agent 2

1. Đọc registry/report cũ; rà artifacts mới khi manifest terminal và ổn định.
2. Đối chiếu run AKT mới với authorization, Gate hashes, config, coverage, checkpoint và metric refs.
3. Chỉ nâng milestone khi evidence đủ; giữ records failed/incomplete và cập nhật claims liên quan.

## Giới hạn kết luận

Audit không chạy training, benchmark, evaluation hay test; không sửa code/dataset/experiment artifact. Discovery giới hạn bởi artifacts không exhaustive-read, ignored local storage, VHDX/env/cache không mở và quyền đọc global exclude bị từ chối. Mỗi claim có path/status trong EVIDENCE_INDEX.md; registry trong experiment_registry.json.
