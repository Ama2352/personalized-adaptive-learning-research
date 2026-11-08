# RQ1/RQ2 — kế hoạch history-stratified cached contrast, chưa tính số

## Câu hỏi mới và duplicate search

Full−empty trong cùng enabled Graph-GAM package có ΔLL/ΔBrier và tỷ lệ **full preview** đổi khác nhau theo (a) số events đã cập nhật trước target và (b) số lần concept của target đã được quan sát trong cùng learner không? Hai trục giúp phân biệt sequence dài nhưng target concept vẫn ít quan sát với target concept đã lặp nhiều; không chứng minh cơ chế, causal moderation hay ability effect.

Đã tìm trong các reports `rq1*`/`rq2*`: transition, score-vector, query-observability, closed-loop reconstruction, conditions và fixed-edge-set contrast mới. Chúng chưa chia direct full−empty theo hai biến này. Junyi common-population/prefix-support và factorial ability là estimands/inputs khác, không được dùng thay. Protocol21 line58 ghi history1–10/11–50/>50; matrix05 E06 ghi history và sparse **train support**. Biến concept-prior dưới đây là **within-learner observed concept history**, không train support/vocabulary coverage, nên chưa hoàn thành chiều sparse-train-support của E06.

## Source validation: Hpast thật sự đếm gì?

Archived `rq1-query-observability-reproduction-20261108-01/historical_runner.py`, SHA `402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45`:

- Lines55–68: learner/profile mới, policy constructors mới; RNG reset cùng seed, cùng item list.
- Lines69–75: `step=0…119`, timestamp=`2026-01-01 + 6*(step+1) hours`; current query được predict.
- Lines83–89: stored `event_id=str(step)` trước `policy.update`; mỗi variant update đúng một lần/event. Lines90–93 bookkeeping gắn cùng logged query, preview ở deepcopy lines77–78 không trở thành lịch sử thật.
- Do đó **Hpast=int(event_id)** là số prior labeled policy updates trên toàn sequence. `event_id=0` là cold zero-policy-history, không đưa vào bin1–10. Dù environment.interact đã sinh current y tại line73, current label chưa được đưa vào policy cho tới line89; không diễn giải Hpast là số environment calls đã xảy ra tại thời điểm predict.
- **concept_prior_count(t)=sum_{j<t} I(query_concept_j=query_concept_t)** trong cùng `(seed,profile)`; tính trước khi tăng counter với current query. Không dùng current/future y, preview CID, mastery, oracle hoặc model score để gán bin. Đây là observed exposure count, không đo toàn bộ effective information vì graph có thể truyền parent evidence.

## Inputs và joins, không đổi population

Chỉ dùng immutable bundle `rq1-fixed-edge-set-contrast-20261108-01`: `event_flags.json`, `summary.json`, `run.json`, `plan.json`, `observed_query_sidecar.jsonl.gz`, `observed_legacy.jsonl.gz`, `observer.py`, `historical_runner.py`, `C13_manifest.json` và manifest hiện hành. Verify SHA trước/sau, không execute native/runner/observer classes. Exact equality/rowsha helper chỉ pure stdlib definitions nếu cần.

1. Verify completed manifest + outputs; existing summary1080/16groups và all36historical checks. Primary flags đúng1.080 unique keys `(seed,profile,event_id)`.
2. Sidecar/legacy join `(variant,learner_id,event_id)` bằng `legacy_row_sha256`; đủ3.240 rows, đủ3variants/key. Enforce actual query tuple+label cùng1080keys, canonical step0…119 và learner_id. Full/empty histories có cùng observed items/y; GF chỉ identity negative check, không thêm GF metrics.
3. LL/Brier/full-preview changed **reuse nguyên flags**, không re-score model/calibration, không derive lại M/S/R. Verify flags khớp source tuple equality; không đổi exact comparator hoặc LL clip1e−15 đã freeze.
4. Duyệt sorted events mỗi learner; assert counter trước target bằng actual prior prefix count, cập nhật sau gán bin. Mỗi target vào đúng1history bin và1concept bin; tổng pooled partition và mỗi profile/seed/trajectory phải recover đủ1080, không intersection/filter/drop.

## Bins, aggregations và coverage đã định trước

| Trục | Bins cố định | Ý nghĩa |
|---|---|---|
| Hpast |0;1–10;11–50;>50|Prior policy updates; zero báo riêng|
| Concept prior |0;1–5;≥6|Prior logged observations của target concept, không train support|

Từ schedule source, **expected, chưa xác nhận bằng actual row analysis**: history counts pooled9/90/360/621; mỗi profile hoặc seed block3/30/120/207; mỗi trajectory1/10/40/69. Concept-bin và joint-cell coverage **chưa đọc/tính**, không giả đủ; ≥6 là exposure category, không adoption mastery threshold.

Giữ các context như analysis trước: pooled,3profiles,3seed blocks,9seed×profile trajectories (16contexts). Mỗi context xuất đủ4history marginal +3concept marginal +12joint cells;304summary cells kể cả rỗng. Mỗi cell chỉ có n query-pairs, meanΔLL, meanΔBrier và preview-change count/n; cell0: means/rate=null, count0. Không threshold minimum, merging, smoothing, favourable-bin selection hoặc kiểm định. Event flag table1080rows thêm Hpast/concept_prior/bin để trace từng membership.

Pooled mean là equal-weight query targets trong cell, không equal-weight learner mới hoặc causal population estimator. Báo denominator1080total/360profile/120trajectory; cell denominator theo actual coverage. Có thể kiểm weighted reconstruction từ cells về existing pooled/profile metrics ở tolerance1e−12, không đổi giá trị đã lưu. Báo số nonempty seed/profile trajectories trong mỗi bin và các empty cells; không tính CI.

## Control overlap và confounds bắt buộc nêu

- Full/empty phải100% đồng bin/actual query+y trên1080targets: cùng-exposure overlap, không propensity/statistical overlap. Các contexts/bins tái dùng events; không cộng n thành samples mới.
- Source reset RNG từng profile cùng seed, nên queries và concept counts dự kiến lặp giữa profiles của một seed family; validate không tự suy independent exposure. Labels/initial state/dynamics vẫn khác. Shared query schedule không làm profile contrast thành causal ability intervention.
- Hpast gắn chính xác timestamp/sequence position và accumulated practice; các bins không randomize history length, forgetting/time hay graph. Own-concept count phụ thuộc random item frequencies và sequence position, có thể confound với concept identity/difficulty/parent exposure. Joint cells chỉ mô tả, không adjustment/mediation hay causal sparsity effect.
- Full−empty là conditional estimator-edge-set package contrast gồm downstream updates; không direct-logit-only/edge quality. Preview chưa served, không learning benefit. Historical H120 diagnostic không thay H_dev30/final H500 coverage; không claim RQ2 complete hay final generalization.

## Proposed bounded next action — chưa được dispatch

Sau root plan review: chuẩn bị/freeze một stdlib analyzer chỉ đọc cached files, source/plan pins trước quantities; ONE cached arithmetic≤10s cumulative, exclusive outputs, source/input SHA trước=sau, log+receipt. Không model/teacher/RNG/replay/realdata/GPU, new independent N=0. Thiếu keys, mismatched history/query/label, sai partition hoặc metric-reconstruction thì STOP giữ failure; không relax, retry hoặc đổi bins. Bước hiện tại chỉ DESIGN, chưa chạy hay xuất coverage/contrast theo bins.
