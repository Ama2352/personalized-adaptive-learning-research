# RQ1/RQ2: history-stratified full–empty contrast trên fixed stream — 08/11/2026

## Phát hiện và giới hạn chính

Đã chia **đủ1.080 cached target pairs** của [full–empty contrast](rq1_fixed_edge_set_contrast_20261108.md) theo số prior policy updates và số lần target concept đã được quan sát trước target. Pooled LL/Brier nhỏ hơn với full trong từng history bin; nhưng cả ba profile không cùng chiều: PG có LL/Brier lớn hơn ở tất cả history bins. Concept-prior1–5 pooled có ΔLL dương nhỏ trong khi ΔBrier âm; do đó không nói graph nhất quán có lợi hoặc có một quy luật sparse/history đơn điệu.

Đây là mô tả **conditional enabled-package estimator-edge-set contrast** trên exposures cũ. Không chạy native/model/teacher/RNG/replay, không thêm learner/seed, new independent N=0. Không CI/p-value/calibrator/bin search. **Hpast bị confound chính xác với thời gian/vị trí chuỗi; concept-prior là own-concept exposure, không train support/vocabulary hoặc toàn bộ parent information.** Preview chưa là served action; kết quả chưa đo learning benefit hay causal history/ability moderation.

## Source và định nghĩa trước tính

[Design freeze](../runs/rq1-history-edge-contrast-20261108-01/design.md), [kế hoạch SHA](../runs/rq1-history-edge-contrast-20261108-01/plan.json) và [analyzer](../runs/rq1-history-edge-contrast-20261108-01/analyze_history_contrast.py) có trước quantities. Runner fixed gốc lines69–89: step0…119; timestamp=2026-01-01+6×(step+1) giờ; `event_id=str(step)` được lưu trước `policy.update`. Vì thế **Hpast=event_id** đếm prior labeled updates của policy. Environment sinh current y trước predict nhưng label chỉ vào policy ở update sau lưu row; không đánh đồng Hpast với environment-call count tại thời điểm predict. [Runner nguồn](../runs/rq1-history-edge-contrast-20261108-01/historical_runner.py).

`Cprior(t)=sum(j<t)[query_concept(j)=query_concept(t)]` trong cùng learner; tăng counter **sau** gán bin. Current/future y, preview, S/M/R và oracle không tham gia gán bin. Lịch sử item/y đã cùng nhau ở full/empty; flags tái dùng LL/Brier với clip1e−15/rawP và full-preview tuple equality đã freeze, không gọi model lại.

| Trục | Bins | Đơn vị |
|---|---|---|
| Hpast |0;1–10;11–50;>50|Prior policy updates toàn sequence; cold0 tách riêng|
| Cprior |0;1–5;≥6|Prior logged target-concept observations trong learner|

Giữ16contexts (pooled,3profiles,3seed blocks,9seed×profile trajectories), mỗi context4H+3C+12joint=19cells; tổng**304cells**, kể cả empty/null. Strict3.240sidecar↔legacy rowSHA và1.080flag keys; actual query+label exact cả3variants; overlap full/empty cùngbin đủ1.080/1.080. Queries giống nhau across profiles trong từng seed đã verified, nhưng outcomes/initialization/dynamics khác. Three seed families reused, không9independent-seed hoặc1.080independent-target claims.

ONE cached run PASS **0.4277682000s≤10**, RC0;14source/plan/input hashes trước=sau; all304cells; all16contexts×3partitions recover n/preview exact và96weightedLL/Brier checks residual≤1e−12. [Receipt](../runs/rq1-history-edge-contrast-20261108-01/run.json), [all304cells/coverage/checks](../runs/rq1-history-edge-contrast-20261108-01/summary.json), [all1.080event bins](../runs/rq1-history-edge-contrast-20261108-01/event_bins.json). Empty cells: n=0,count=0,mean/rate=null; không drop/merge/smoothing. Không tính thêm metrics ngoài LL/Brier+full-preview count/rate.

## Pooled và toàn bộ profile marginal bins

Δ=full−empty; âm nghĩa metricfull thấp hơn. A là số full `(concept,question,difficulty)` preview đổi/n của cell, không phải served action. n là same-query/label pairs, không independent N. Các profiles dùng cùng exposure-bin counts trong seed family; label differences vẫn tồn tại.

| Context | Trục | Bin | n | ΔLL | ΔBrier | A đổi/n |
|---|---|---|---:|---:|---:|---:|
|pooled|history|0|9|-0.002543028549|-0.001271457293|0/9|
|pooled|history|1-10|90|-0.001495280692|-0.0007305063806|0/90|
|pooled|history|11-50|360|-0.001420362601|-0.0007327702966|17/360|
|pooled|history|>50|621|-3.081955365e-05|-3.990934836e-05|5/621|
|pooled|concept|0|246|-0.001553834326|-0.000761199729|7/246|
|pooled|concept|1-5|762|1.154017421e-05|-4.320066025e-05|15/762|
|pooled|concept|>=6|72|-0.004367810653|-0.002022162022|0/72|
|profile:PG|history|0|3|0.00780995501|0.003904800427|0/3|
|profile:PG|history|1-10|30|0.004172375787|0.002023398102|0/30|
|profile:PG|history|11-50|120|0.004244826333|0.001956077744|15/120|
|profile:PG|history|>50|207|0.001167570913|0.0005012554433|5/207|
|profile:PG|concept|0|82|0.004158026889|0.0020300999|7/82|
|profile:PG|concept|1-5|254|0.002391839932|0.001055970891|13/254|
|profile:PG|concept|>=6|24|-0.002034086246|-0.0009908019849|0/24|
|profile:PY|history|0|3|-0.007719520328|-0.003859586153|0/3|
|profile:PY|history|1-10|30|-0.00413949459|-0.002009876996|0/30|
|profile:PY|history|11-50|120|-0.005466400548|-0.002660499333|2/120|
|profile:PY|history|>50|207|-0.001084549929|-0.0005217422712|0/207|
|profile:PY|concept|0|82|-0.005432062965|-0.002661774314|0/82|
|profile:PY|concept|1-5|254|-0.001729085669|-0.0008497200357|2/254|
|profile:PY|concept|>=6|24|-0.005966515696|-0.002710052318|0/24|
|profile:PYH|history|0|3|-0.007719520328|-0.003859586153|0/3|
|profile:PYH|history|1-10|30|-0.004518723272|-0.002205040247|0/30|
|profile:PYH|history|11-50|120|-0.003039513588|-0.001493889301|0/120|
|profile:PYH|history|>50|207|-0.0001754796452|-9.924121724e-05|0/207|
|profile:PYH|concept|0|82|-0.0033874669|-0.001651924773|0/82|
|profile:PYH|concept|1-5|254|-0.0006281337402|-0.0003358528359|0/254|
|profile:PYH|concept|>=6|24|-0.005102830016|-0.002365631762|0/24|

Không diễn giải pooled H>50 gần0 là graph-neutral/equivalent. PG vẫn dương ở cả4Hbins; PG C≥6 âm trong khi C0/C1–5 dương. PY/PYH mọi marginal bin âm, nhưng marginal pooling có thể che các joint cells ngược chiều. H0 có9queries/9trajectories nhưng chỉ3shared seed schedules, không9independent cold-world replicates.

## Joint coverage: đủ cả pooled và ba profiles

Các bảng giữ mọi joint cell, gồm null và kết quả bất lợi. Support là số seed families có ≥1target, không training support. n mỗi cell thay đổi theo source exposure và position; không dùng n như inference weight ngoài same-target arithmetic.

| Context | Hpast | Cprior | n | Seed families | ΔLL | ΔBrier | A đổi/n |
|---|---|---|---:|---:|---:|---:|---:|
|pooled|0|0|9|3|-0.002543028549|-0.001271457293|0/9|
|pooled|0|1-5|0|0|null|null|0/0;rate=null|
|pooled|0|>=6|0|0|null|null|0/0;rate=null|
|pooled|1-10|0|72|3|-0.001109192101|-0.0005398855239|0/72|
|pooled|1-10|1-5|18|3|-0.003039635052|-0.001492989808|0/18|
|pooled|1-10|>=6|0|0|null|null|0/0;rate=null|
|pooled|11-50|0|132|3|-0.001301063903|-0.0006354855566|6/132|
|pooled|11-50|1-5|225|3|-0.00143059662|-0.0007610663943|11/225|
|pooled|11-50|>=6|3|1|-0.005901953927|-0.002891091531|0/3|
|pooled|>50|0|33|3|-0.003265264263|-0.001607762621|1/33|
|pooled|>50|1-5|519|3|0.0007425650927|0.0003182945128|4/519|
|pooled|>50|>=6|69|3|-0.004301108771|-0.001984382478|0/69|
|profile:PG|0|0|3|3|0.00780995501|0.003904800427|0/3|
|profile:PG|0|1-5|0|0|null|null|0/0;rate=null|
|profile:PG|0|>=6|0|0|null|null|0/0;rate=null|
|profile:PG|1-10|0|24|3|0.004739968488|0.002328992496|0/24|
|profile:PG|1-10|1-5|6|3|0.001902004981|0.0008010205253|0/6|
|profile:PG|1-10|>=6|0|0|null|null|0/0;rate=null|
|profile:PG|11-50|0|44|3|0.003911310142|0.001889146702|6/44|
|profile:PG|11-50|1-5|75|3|0.004565176504|0.002054295298|9/75|
|profile:PG|11-50|>=6|1|1|-0.005106724107|-0.00246527296|0/1|
|profile:PG|>50|0|11|3|0.002879222716|0.001430501429|1/11|
|profile:PG|>50|1-5|173|3|0.001466630491|0.0006320135013|4/173|
|profile:PG|>50|>=6|23|3|-0.001900493296|-0.0009266945511|0/23|
|profile:PY|0|0|3|3|-0.007719520328|-0.003859586153|0/3|
|profile:PY|0|1-5|0|0|null|null|0/0;rate=null|
|profile:PY|0|>=6|0|0|null|null|0/0;rate=null|
|profile:PY|1-10|0|24|3|-0.003498598907|-0.001716335246|0/24|
|profile:PY|1-10|1-5|6|3|-0.006703077319|-0.003184043997|0/6|
|profile:PY|1-10|>=6|0|0|null|null|0/0;rate=null|
|profile:PY|11-50|0|44|3|-0.006472692471|-0.003152748329|0/44|
|profile:PY|11-50|1-5|75|3|-0.004848635355|-0.002357093293|2/75|
|profile:PY|11-50|>=6|1|1|-0.007521945423|-0.003756996494|0/1|
|profile:PY|>50|0|11|3|-0.00486415997|-0.002433978447|0/11|
|profile:PY|>50|1-5|173|3|-0.0002041713545|-0.0001152753068|0/173|
|profile:PY|>50|>=6|23|3|-0.005898888317|-0.002664533006|0/23|
|profile:PYH|0|0|3|3|-0.007719520328|-0.003859586153|0/3|
|profile:PYH|0|1-5|0|0|null|null|0/0;rate=null|
|profile:PYH|0|>=6|0|0|null|null|0/0;rate=null|
|profile:PYH|1-10|0|24|3|-0.004568945885|-0.002232313821|0/24|
|profile:PYH|1-10|1-5|6|3|-0.004317832818|-0.002095945952|0/6|
|profile:PYH|1-10|>=6|0|0|null|null|0/0;rate=null|
|profile:PYH|11-50|0|44|3|-0.001341809379|-0.0006428550425|0/44|
|profile:PYH|11-50|1-5|75|3|-0.004008331008|-0.001980401188|0/75|
|profile:PYH|11-50|>=6|1|1|-0.005077192252|-0.00245100514|0/1|
|profile:PYH|>50|0|11|3|-0.007810855536|-0.003819810846|0/11|
|profile:PYH|>50|1-5|173|3|0.0009652361416|0.0004381453438|0/173|
|profile:PYH|>50|>=6|23|3|-0.005103944702|-0.002361919876|0/23|

Pooled H11–50/C≥6 chỉ**3targets từ1seed family**, mỗi profile1target. Đây là coverage hẹp, không thể dùng để xác lập sparse effect. H0/C>0 và H1–10/C≥6 rỗng; null không được thay bằng zero effect. H>50/C1–5 pooled LL/Brier dương; riêng PYH ở cell này cũng dương dù mọi PYH marginal bin âm. Bảng đầy đủ ngăn chọn riêng signs/nhóm có lợi; seed/profile/trajectory cells còn lại đều có trong JSON304cells.

## Những gì dữ liệu chưa trả lời

Source schedule làm Hpast tăng cùng elapsed time, forgetting opportunities và accumulated practice. Cprior phụ thuộc concept identity/frequency, difficulty mix, sequence position và lịch sử trước đó; graph có thể truyền parent evidence dù Cprior=0. Joint stratification không loại các confounds đó. Vì thế chưa thể nói graph hữu ích **do** sparse history hoặc thay đổi H khiến benefit tăng/giảm.

E06 yêu cầu sparse theo **train support**; bài này không có training-corpus support variable và không thay yêu cầu đó. Cũng không thay development H30/final horizon500 bằng historical H120, không claim RQ2 complete, robustness theo noise hoặc learned graph. Full/empty vẫn khác estimator edges trong cùng package gồm downstream state-update effects; controller/environment graph vẫn full. Preview là probe trên deepcopy; không instruction/retention/outcome claim.

Đây là bước định vị điều kiện mô tả từ cached evidence. Controlled availability replay sẽ là **thí nghiệm thuật toán mới**, cần source/caps/negative controls được review riêng trước thực hiện; hiện chưa chạy. Không biến binning này thành thử nghiệm randomize lượng lịch sử. [Bundle và provenance](../runs/rq1-history-edge-contrast-20261108-01/README.md) giữ nguồn, inputs, hashes/copy trước-sau; C13/C14 và contrast trước giữ nguyên.
