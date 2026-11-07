# Kiểm toán validity/comparability

Verdict áp dụng cho scope evidence đã kiểm tra. Thiếu evidence là NOT VERIFIED/CONDITIONAL PASS, không tự động là scientific failure.

| Finding | Phạm vi | Verdict | Evidence/lý do | Impact | Khuyến nghị |
|---|---|---|---|---|---|
| VAL-01 | BKT learner-disjoint split | CONDITIONAL PASS | Protocol/manifest ghi frozen global split; 5 Dev folds, 198,084 Dev/49,522 Test. | Trung bình; không tái tạo assignments từ raw. | Giữ assignment fingerprint, chỉ compare cùng folds. |
| VAL-02 | BKT predict-before-update | CONDITIONAL PASS | Protocol/report/manifest ghi time_done, source_row, one-step-ahead. | Cao nếu sai; chưa replay độc lập. | Trích protocol trong thesis; code review độc lập trước mở rộng. |
| VAL-03 | BKT frozen fit | PASS theo artifact | Manifest: pyBKT 1.4.3 C++, num_fits=1, tol=.005, maxiter=100, seed/split seed 42, forgets off; hashes/runtime. | 11 final fits hit maxiter. | Báo convergence warning riêng, không thay historical artifacts. |
| VAL-04 | BKT metric integrity | PASS cho giá trị ghi nhận | CV/Test JSON có denominator, coverage, metrics, unseen policy; khớp report. | Pipeline không rerun. | Giữ metric path/denominator trong bảng. |
| VAL-05 | BKT holdout isolation | CONDITIONAL PASS | Test JSON ghi không dùng fit/tuning; protocol đánh giá một lần. | Holdout đã xem; không còn untouched. | Không chọn config bằng Test. |
| VAL-06 | GAM source parity | CONDITIONAL PASS | Integration note/test path và CV source hash trỏ notebook cell 11. | Test không rerun; source archive local/ignored. | Giữ hashes trong benchmark snapshot. |
| VAL-07 | GAM mapping/split/causality | CONDITIONAL PASS | CV JSON ghi 20,706,208 canonical rows; sidecar 20,707,382 raw, 1,174 duplicates verified; identity fields; frozen folds; no Test. | Không re-read mọi prediction join. | Tách fallback và supported metrics. |
| VAL-08 | BKT–GAM comparability | CONDITIONAL PASS, matched Development | Same frozen folds/target/population; 20,706,014 common rows; 194 fallback loại khỏi common; BKT common aggregate khớp. | Không đại diện graph, policy hay model family khác. | Ghi rõ matched Development common-row benchmark. |
| VAL-09 | GAM bootstrap inference | CONDITIONAL PASS | JSON gốc: 1,000 learner resamples/fold, seed 20261030, percentile CI. LL/Brier/ECE/accuracy loại 0. | Không đo refit/split variance; thiếu AUC paired CI/Holm. | Diễn giải trên 5 stored folds; đăng ký multiplicity cho nghiên cứu mới. |
| VAL-10 | AKT provenance | CONDITIONAL PASS | Provenance doc, Gate2 source commit 01b7e8d7d7c862cabc9467108e3e7f2555653a88, lock hash, synthetic tests. | Snapshot untracked/in development; không là benchmark. | Manifest provenance cho mỗi future run. |
| VAL-11 | AKT Gate 2 | PASS cho recorded snapshot | gate2.json: PASS, 155 passed/66.20s, log/build hashes. | Technical/synthetic only. | Không nâng thành scientific validation. |
| VAL-12 | AKT smoke | PASS bounded pipeline | Manifest completed; 549/549 export, 441 fitted/108 unseen, exact checkpoint reload. | Small cohort/12 steps; không benchmark. | Giữ milestone smoke riêng. |
| VAL-13 | AKT pilot | FAIL execution | Manifest/pilot terminal failed PermissionError replace; complete_epoch=false; no validation/export/checkpoint. | Không có predictive result. | Điều tra persistence rồi run mới với authorization riêng. |
| VAL-14 | Graph semantics/quality | NOT VERIFIED | Junyi prerequisite metadata; report ghi thiếu explicit KC map/gold validation; không ablation. | Cao với RQ1–RQ3. | Xác minh provenance/node/edge direction/confidence trước claim. |
| VAL-15 | Decision/policy/closed-loop | NOT VERIFIED | Không thấy threshold/policy run, Grade 10 simulator outputs, retention/mastery evidence. | RQ còn mở; predictive score không thay outcome. | Xác minh simulator, đăng ký outcome và policy protocol. |
| VAL-16 | Portable reproducibility | CONDITIONAL PASS/local-only | Manifests/source/dependency hashes/relocation summary; data/results/RIVF source ignored local. | Auditor khác không nhất thiết truy cập được; global ignore unread. | Duy trì safe provenance/fingerprint; không phát tán private data. |

## Leakage/comparability check

- BKT: manifest/docs ghi learner split, fold, causal one-step prediction rồi update; chưa independently replay sequence.
- GAM: CV ghi fold-specific difficulty từ train folds, chronological replay, no holdout, mapping audit/fallback. Prediction joins không mở hết; xác minh dựa trên raw summary/report.
- AKT: Gate2 ghi synthetic tests causal/mask/OOV/checkpoint/export; bounded smoke. Pilot failed trước validation. Chưa có full-data leakage audit.
- BKT–GAM: common-row/source_row join và 194 fallback tách rõ. Native GAM có fallback nên không hoàn toàn cùng fitted population.
- Statistics: fold mean±SD là mô tả; bootstrap learner CI có điều kiện trên stored fits; thiếu paired AUC CI/Holm/multi-seed retraining. Không claim equivalence/causality.
