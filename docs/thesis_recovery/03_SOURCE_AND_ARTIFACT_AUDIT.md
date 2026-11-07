# Kiểm toán mã nguồn và artifact

Mốc kiểm toán 06/11/2026, HEAD `30d63c6`. Trạng thái VERIFIED ở đây chỉ áp dụng phạm vi evidence ghi kèm. Source inspection khác runtime reproduction. Đã inventory SHA-256 trong `evidence/source_inventory.json`, không di chuyển artifact. Dataset và Holdout rows không được mở trong phiên. Source notebook được trích thành text có đánh số CELL, chưa execute. Git có nhiều nguồn untracked, cần snapshot để tái lập.

Gọi P2 là `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/`.

| Thành phần | Trạng thái | Vị trí, chức năng và evidence | Còn lại/rủi ro, quyết định, critical path |
|---|---|---|---|
| Paper1 | PARTIALLY VERIFIED | `paper1/AdaptiveEngineSimulation_Enhanced.ipynb`, PDF 5 trang. Source CELL3,5,11,13 khác PDF continuity/latent/seeds | Tìm revision chính thức, inputs chỉ có thể dùng P2 sau hash/provenance confirmation. REUSE tham chiếu, MODIFY qua variant riêng. Critical |
| Paper2 | PARTIALLY VERIFIED | P2/source notebooks, `SIMULATOR_SPEC.md`, `SELECTOR_SPEC.md`, `CONTEXT_ADAPTATION_SPEC.md`, frozen/simulation | Có frozen results và fixture, chưa rerun. REUSE adapters, giữ historical. Critical |
| Junyi preprocessing | PARTIALLY VERIFIED | `src/knowledge_tracing/bkt_baseline/preprocess.py`, `docs/bkt-data-readiness-audit.md`, GAM cv.json canonical identity | Chronology time_done/source_row, correct hint semantics, dedup 1.174 theo report. Raw chưa audit lại. REUSE |
| Junyi graph | PARTIALLY VERIFIED | Catalog audit `docs/research/bkt-gam-kt-baseline-benchmark-report.md` §9, shared_kt graph | 835 catalog IDs, 979 edges sau self-removal theo audit lịch sử, 720 Dev exercise. Chưa gold/KC map. REUSE metadata, MODIFY validation. Critical |
| Learner split | PARTIALLY VERIFIED | `bkt_baseline/splits.py`, `akt/splits.py`, `_context/evaluation_protocol.md`, GAM CV hashes | Frozen 80/20 learner, Dev5 folds, 198.084/49.522 theo report. Chưa reread assignments. REUSE |
| Shared evaluation | PARTIALLY VERIFIED | shared_kt.py, paired_bootstrap.py, tests/shared_kt | Identity/source_row/masks/OOV contracts có test, chưa multi-model integration. MODIFY trace |
| BKT | PARTIALLY VERIFIED hiện runtime, VERIFIED tồn tại lịch sử | `bkt_baseline/adapter.py`, `pipeline.py`, experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json completed, final_cpp, test_cpp marker. Không mở Test predictions/metrics | CV và refit/Test documented. Pilot fold0 selection limitation. .venv hiện thiếu pyBKT.models, collection lỗi 4 modules. KEEP frozen, supporting reference, không critical training |
| GAM-KT | PARTIALLY VERIFIED | src/knowledge_tracing/gam_kt, experiments/gam_kt/results/wsl_cpp/cv/cv.json completed, báo common rows/paired bootstrap | Graph-free decay off, train-fold difficulty, no verified KLTN Holdout. REUSE, không cần Holdout hiện tại |
| Graph-GAM | IMPLEMENTED BUT UNVALIDATED trong tích hợp KLTN | P2 simulator CELL13 và Junyi CELL11 có implementation. src/gam_kt benchmark chỉ graph-free | Tracking cũ NOT STARTED chỉ đúng adapter mới. Cần package ablations và parity. REUSE/MODIFY. Critical RQ1 |
| AKT NonRasch | PARTIALLY VERIFIED | src/knowledge_tracing/akt, upstream `01b7e8d7d7c862cabc9467108e3e7f2555653a88`, smoke-task13-20261101-03 manifest, tests | Gate2 164 theo 05/11 log, toàn build hashes khớp audit_checks.json. Pilot14-02 failed 32 steps, chưa complete Dev CV. KEEP/MODIFY lifecycle. Critical |
| Fixed graph AKT | NOT STARTED | Config validate cấm graph, chưa source/result tương ứng trong src/tests/experiments | Cần residual branch và graph contract. KEEP required. Critical |
| CG-AKT | NOT STARTED | Chưa source/checkpoint/evidence trong phạm vi tìm | Edge confidence/gate/fallback chưa triển khai. KEEP required. Critical |
| SAKT | NOT STARTED trong repo sources đã tìm | Chưa model/tests/experiment | Comparator proposal required. KEEP, chạy budget nhỏ hơn CG sensitivity, bỏ cần duyệt |
| GKT | NOT STARTED trong repo sources đã tìm | Chưa model/tests/experiment | Chốt variant graph/message semantics, upstream provenance. KEEP required |
| Simulator integration | INCOMPLETE | P2 có BKT/GAM/Elo policies, AKT dùng Junyi LearnerEvents | Vocabulary và mastery adapter chưa tương thích. MODIFY, hai môi trường train riêng. Critical |
| Statistics | PARTIALLY VERIFIED | P2 STATISTICAL_PROTOCOL, frozen CSV, reports/paired_cluster_bootstrap_bkt_gam.json | Historical paired learner CI 1.000 reps, chưa AUC CI, chưa new RQ families. REUSE/MODIFY |
| Demo | NOT STARTED trong phạm vi tìm | Proposal trang4 và5 yêu cầu rõ | Build sau contract, viewer có thể sớm dùng fixture. KEEP. Critical delivery |
| Thesis/docs | INCOMPLETE | research_tracking và docs/research baseline report, proposal và papers có | Chưa tìm thesis manuscript, advisor feedback riêng. KEEP viết từ tuần1, thêm article draft |

## AKT implementation audit

Window H=100,T=100,L≤200, target anchors không overlap, OOV tạo barrier và null target. Không có warmup target bị bỏ âm thầm trong thiết kế hiện tại. BKT history không hạn chế, AKT truncated history, phải báo effective-history và coverage, cùng current target population. Train vocabulary từ train learners, refit có vocabulary mới thì không reuse inner embeddings bằng ID ngầm.

`tensors.py` tái tạo QA của quá khứ, native strict mask ngăn current answer vào prediction. Đây là chủ ý của causal adapter, cần perturb-current/future-label tests cả GPU. `training.py` shuffle buffer có seed theo epoch, inner select và outer refit separate. `model.py` mean loss theo scored targets, finite gradients, clip. CUDA timings hiện đo perf_counter chưa synchronize, cần end-to-end synchronized benchmark. Many .item()/CPU checks gây sync overhead, chưa đo hiệu năng GPU.

`checkpoint.py` chứa model/optimizer/Python/NumPy/Torch/CUDA RNG, encoding và identity, complete epoch only. Thiếu mid-epoch sampler cursor/buffer, stopper/history phục hồi đầy đủ và resume CLI lifecycle đã chứng minh. os.link publish cần test filesystem Volume. `runner.py` đã unique temp/retry Windows errors 5/32/33, progress remediation có synthetic tests, chưa successful Task14 rerun. Watchdog evidence ghi PID parent/child mismatch, cần remote cancellation verification.

Runtime-v2 là torch 2.7.1+cpu, CUDA false. Config cho device cuda ở schema nhưng smoke/pilot khóa CPU. GPU ladder cần phase/authorization hợp lệ và Linux image lock mới, không sửa JSON device để bypass caps. Gate4 vẫn INCONCLUSIVE. New gate2 evidence đã reconciliation hashes, không tiếp tục coi 155/163 là hiện hành.

## Comparability

BKT/GAM common fitted rows 20.706.014, 194 GAM fallback tách theo report. BKT thắng trên metrics báo cáo, bootstrap learner conditional on stored fits. GAM native 20.706.208 rows không đồng nhất denominator common. ECE Junyi benchmark 15 bins, Paper2 replay10 và per-user5, phải recompute canonical metrics trên predictions mới hoặc báo riêng. Simulator BKT chọn global parameters theo simulated Dev, khác per-exercise EM Junyi, không đồng nhất checkpoint/model fit.

No verified complete GAM Holdout trong experiments/gam_kt inventory. Paper2 frozen Junyi confirmation có protocol riêng, không được gọi là KLTN Holdout GAM. Không có successful Task14 mới trong results inventory, prepared config/auth request không chứng minh execution.

## Pass 4 — kiểm chứng runtime hiện tại

Phiên06/11 thử combined suite bị4 collection errors do .venv thiếu pyBKT.models. AKT/shared/GAM lần đầu61passed,34failed,81errors do temp ACL, Git dubious ownership và notebook path. Retry dùng basetemp mới trong workspace và per-process safe.directory đúng upstream (không đổi Git global), kết quả **161 passed,15 failed in65.89s**. Log `evidence/synthetic_tests_retry.log`. Lỗi hard-link tại checkpoint.py/prediction.py và GAM parity test hardcoded path `drive-download-20261018T084013Z-1-001` đã không còn. Chưa kết luận hard-link lỗi do sandbox hay OS filesystem chung. Đây là blocker reproducibility hiện tại, không xóa evidence164pass ngày05/11. Không tiếp tục retry vô hạn, không sửa source trong planning.

PDF extraction MiKTeX failed do setup/registry, fallback bundled pypdf thành công đề cương5trang, Paper1 5trang, Paper2 6trang. pip fallback bị DNS, không cài dependency vào venv. Text extraction đọc toàn trang, chưa visual verification chữ ký/figures.

Kiểm chứng cuối Q09 đã giải quyết. `evidence/planning_validation.json` xác nhận map36ID duy nhất, đủ28nodes,8extraIDs, không missing/duplicate. Advanced31edges=28intra+3cross, baseline25intra, không missing endpoints/isolated nodes trong inputs P2. Không suy provenance Paper1 từ việc graph counts giống PDF.
