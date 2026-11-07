# RQ2: điều kiện exposure, profile và graph controls từ bằng chứng đã lưu

Ngày 08/11/2026. **Phân tích mới cho thấy thứ tự mean giữa PYH/PY không bền trong leave-one-seed-out, còn dấu contrast Junyi có thể đổi theo mẫu số/quần thể.** Đây là descriptive/exploratory reanalysis của pilot đã xem, chưa là kết luận điều kiện hiệu quả cuối hoặc causal ability effect.

Run mới [rq2-conditions-evidence-20261108-01](../runs/rq2-conditions-evidence-20261108-01/README.md) chỉ đọc selected aggregates và manifests. [conditions.json](../runs/rq2-conditions-evidence-20261108-01/conditions.json) giữ các bảng, toàn bộ 30 leave-one-seed-out values cho ba profile pairs, edge decomposition, denominator checks và 13 input SHA. Không query Junyi interactions/correctness/Holdout, mở outcomes/traces gốc, chạy model/simulator hoặc sinh graph mới.

## Phép tính mới và nguồn

Script tái dùng [factorial contrasts/summary](../runs/cpu-factorial-20261107-01/contrasts.json), manifest/README cùng run; [mechanism followup](cpu_pilot_followup_20261107.json); [corrected graph, order và ba controls](../runs/cpu-junyi-controls-20261107-02-expanded/README.md); [common-population aggregates](../runs/cpu-junyi-common-20261107-01/common_population.json). Selected outputs được kiểm SHA với manifest nguồn; followup khớp archived `input_mechanism_followup.json` trong [parallel-graph-diagnostics](../runs/parallel-graph-diagnostics-20261107-01/manifest.json). Source `practice_order.py` được hash/đối chiếu bản dùng cho common-population để diễn giải đúng hai estimands order. Không verify toàn bộ bundle bằng cách mở thêm raw outputs.

Khác bản [factorial uncertainty cũ](factorial_pilot_uncertainty_20261107.md), gói này tính **paired profile-difference và LOO của profile-difference**, không chỉ LOO riêng từng profile. Với Junyi, gói tính lại corrected-base từ stored edge summaries, phân rã removed/added/shared edges, phân biệt global endpoint exposure với same-learner co-observation, rồi đối chiếu hai hệ trọng số/quần thể. Mọi seed/profile/control nguồn đều được giữ, không chọn subset theo kết quả thuận lợi.

## Simulator: exposure không phải sample size độc lập

Giữ đúng estimand nguồn:

`I(s,p) = (edge-on − edge-off)|λ0,55 − (edge-on − edge-off)|λ0`.

Outcome là net mean theta gain, Elo-scale trung bình qua 28 concepts sau 120 steps. Edge treatment bật **parent signal và parent adaptation cùng nhau**; control tắt cả hai, local pathway tắt ở cả hai. Environment/controller giữ historical graph, initialization vẫn có graph correlation. Không đổi tên I thành raw graph gain, riêng một pathway hoặc time-DiD.

| Profile | Min ability ban đầu nguồn | Deficit-exposed events / denominator | Exposure pooled | Mean edge effect λ0,55 | Mean edge effect λ0 | Mean I |
|---|---:|---:|---:|---:|---:|---:|
|PG|1269,311781|0/2400|0%|+0,110853316|+0,110853316|0|
|PY|911,469549|1919/2400|79,9583%|+0,051485897|+0,017468639|+0,034017258|
|PYH|929,632974|1197/2400|49,8750%|+0,378081797|+0,324553209|+0,053528587|

Minimum ability là aggregate đã lưu trong followup, không dựng lại latent vectors ở lần này. Exposure ratios và các effect components/I được tính lại bằng arithmetic. 2400 là pooled diagnostic events/profile của followup, **không phải 2400 learners độc lập**; không dùng event denominator để tính binomial CI hoặc tăng n cho contrasts. Đơn vị contrasts là 10 seed blocks 21000–21009; 30 profile–seed rows không phải 30 independent blocks.

PG có I=0 ở cả 10 seeds và mechanism không exposed trong followup, nhưng hai graph-effect components đều khác 0. Đây không phải equivalence hoặc graph neutrality. PYH có pooled exposure thấp hơn PY nhưng I mean cao hơn; không thể suy dose–response hay mediation vì selected inputs không có exposure theo seed/cell để ghép với seed effects. Các profiles cũng khác initialization/dynamics, không là can thiệp chỉ thay ability.

## Paired profile moderation: thứ tự PYH/PY nhạy với seed

Với mỗi seed s, tính `D_s=I(s,profile thứ hai)−I(s,profile thứ nhất)`, rồi giữ cả 10 D_s và 10 means khi bỏ đúng một seed. Đây là numerical pairing theo seed identifier nguồn; không tự xác lập causal ability intervention hoặc population sampling model.

| Contrast mô tả | Mean D | Số seed dương / âm / zero | Min–max D từng seed | Min–max mean LOO |
|---|---:|---:|---:|---:|
|I(PY)−I(PG)|+0,034017258|7/3/0|[−0,149211020; +0,176815592]|[+0,018150776; +0,054375956]|
|I(PYH)−I(PG)|+0,053528587|7/3/0|[−0,076758152; +0,214224963]|[+0,035673435; +0,068004892]|
|I(PYH)−I(PY)|+0,019511329|5/5/0|[−0,200356474; +0,363435984]|[−0,018702521; +0,043941085]|

Bỏ seed 21004 làm mean PYH−PY thành −0,018702521; bỏ seed 21002 làm mean +0,043941085. Seed 21004 tự có D=+0,363435984. Vì vậy thứ tự sample means PYH>PY không giữ dấu dưới mọi one-seed deletion, dù LOO của hai contrasts so PG vẫn dương.

LOO range **không là CI**, không có p-value/significance hoặc test heterogeneity cuối. Zero ở bảng dùng tolerance arithmetic 1e−12, không là scientific equivalence margin. Giữ all-seed means làm kết quả mô tả; không bỏ seed 21004 hay các seed bất lợi để chọn kết luận.

## Junyi: corrected 976 edges, không trộn raw denominator

Cohort nguồn: 256 inner-train learners, outer-fold0, tối đa 300 events/learner, 12.575 events. Catalog graph sau bỏ self-loop có **979 edges**; frozen correction còn **976**. Không sinh lại graph hoặc thay control seeds/swaps.

| Graph/reference | Supported edges / toàn bộ edges | Parent-first / co-observed edge–learner pairs | Pair-weighted alignment | Equal-weight supported-edge mean |
|---|---:|---:|---:|---:|
|Raw reference, đã bỏ self-loop|199/979|576/650|0,886153846|0,806715515|
|Corrected base|198/976|575/649|0,885978428|0,805739331|
|Control0|198/976|576/650|0,886153846|0,805739331|
|Control1|198/976|568/644|0,881987578|0,794459870|
|Control2|194/976|574/645|0,889922481|0,817197874|

Supported edge nghĩa là hai endpoints đã co-observed trong ít nhất một learner prefix. Pair-weighted alignment lấy tổng parent-first pairs chia tổng co-observed pairs; edge được nhiều learners quan sát có trọng số lớn hơn. Equal-edge mean lấy trung bình tỷ lệ riêng mỗi supported edge, với denominator supported edges của từng graph. Hai số đo khác estimand, không phải hai estimates của cùng quantity. Riêng corrected base đã có 0,88598 so với 0,80574 do thay cách cân trọng số; không coi đó là sai số thống kê.

Order summaries so first exposure theo tuple `(timestamp,source_row)`. Common-population estimator phía dưới chỉ dùng timestamp để tách before/later/tie và giữ missing parent riêng. Không đồng nhất hai định nghĩa khi gặp ties.

## Perturbation exposure và removed/added decomposition

Mỗi control giữ 976 edges và thay 20 edges bằng 20 edges: **20/976=2,04918%** bị thay, shared edge identities còn 956. Symmetric difference có 40 entries vì tính cả removed và added, không phải 40/976 edges gốc bị thay. In/out-degree được đối chiếu trực tiếp từ frozen edge sets và đều giữ nguyên.

| Control | Changed entries có child được thấy /40 | Có cả endpoints được thấy toàn cohort /40 | Thực sự co-observed cùng learner /40 | Removed: prior / pairs | Added: prior / pairs | Δprior count / Δpair denominator |
|---|---:|---:|---:|---:|---:|---:|
|0|14/40|8/40|2/40 (5%)|1/1|2/2|+1/+1|
|1|20/40|18/40|10/40 (25%)|11/14|4/9|−7/−5|
|2|14/40|12/40|6/40 (15%)|2/5|1/1|−1/−4|

Hai endpoints xuất hiện ở đâu đó trong cohort không đảm bảo cùng learner đã thấy cả hai. Số 8/18/12 của field nguồn `changed_entries_with_both_endpoints_observed` là global endpoint coverage; phép tính mới cho same-learner co-observation chỉ là 2/10/6. Không dùng global counts để phóng đại exposure thực sự của control.

Shared edge identities có counts giống hệt giữa base/control, được kiểm trực tiếp; mọi thay đổi pooled numerator/denominator được giải thích đúng bởi added−removed. **Control2 giảm parent-first count từ 575 xuống 574 nhưng denominator giảm từ 649 xuống 645**, nên pooled rate lại tăng `574/645−575/649=+0,003944052`. Đây là denominator composition, không chứng minh graph tốt hơn hoặc probability-of-benefit. Removed/added subsets nhỏ và selected theo perturbation/co-observation; không dùng tỷ lệ 1/1 để chứng minh edge validity.

## Common-population sensitivity: attrition và thay estimand

Giữ 239/256 eligible learners và 1361 observed learner–child opportunities cố định; mỗi child dùng toàn bộ incoming degree làm denominator, sau đó mean qua child trong learner và equal learner weights. Base prior fraction là 0,165861732; unobserved-parent fraction 0,820852360 là **hierarchical mean** trong prefix, không phải 82% toàn bộ graph Junyi sai hoặc thiếu mastery.

| Control | Parent-set changed opportunities /1361 | Learners đổi prior /239 | Δprior all-fixed, control−base | Common opportunities /1361 | Common learners /239 | Δprior common subset |
|---|---:|---:|---:|---:|---:|---:|
|0|43/1361 (3,1594%)|1/239|+0,000697350|569/1361 (41,8075%)|96/239 (40,1674%)|0|
|1|42/1361 (3,0860%)|7/239|−0,001179045|564/1361 (41,4401%)|96/239 (40,1674%)|−0,003082618|
|2|12/1361 (0,8817%)|1/239|−0,000836820|566/1361 (41,5871%)|95/239 (39,7490%)|0|

Common subset giữ learner–child có ít nhất một parent co-observed ở cả hai graph. Base prior fractions trên subsets lần lượt 0,817391781 / 0,818822664 / 0,816200584: mức tăng so all-fixed 0,16586 đi cùng **thay quần thể/điều kiện quan sát**, không phải cải thiện learner. Ba controls có intersections khác nhau; không pool chúng như cùng target population hoặc chọn subset có contrast đẹp.

Control2 cho pooled pair contrast dương, all-fixed learner-weighted contrast âm và common contrast 0. Đây là ba estimands/quần thể khác nhau, không phải arithmetic contradiction. Identity negative control bằng 0 trên mọi categories đã được đối chiếu. Selected common JSON chỉ có means/ranges/sign counts; **không có learner-level rows để tính lại learner LOO/bootstrap/precision**. Không dựng các rows giả từ mean hoặc dùng edge–learner pairs làm n độc lập.

## Điều có thể trình bày với GVHD

| Câu hỏi | Bằng chứng hiện có | Loại giới hạn |
|---|---|---|
|Profiles có response khác với λ×edge package không?|Means và signs khác theo source profile; PYH−PY ordering đổi dấu trong LOO.|Kết quả mô tả chưa kết luận ordering/heterogeneity suy rộng; profiles không là ability-only intervention.|
|PG zero nghĩa là graph vô ích?|Không: I=0 đi cùng zero measured mechanism exposure, trong khi graph-effect components khác0.|Cơ chế không được exposed trong pilot; weak identification, không equivalence.|
|Matched Junyi controls có chứng minh graph neutral/quality không?|Không: chỉ thay2,05%edges, same-learner changed-entry exposure5–25%, chỉ1–7learners đổi prior score.|Perturbation/overlap yếu; outcome order không trực tiếp đo predictive hoặc instructional efficacy.|
|Có thể xếp graph theo aggregate order alignment không?|Control2 cho dấu khác giữa pooled/fixed/common estimands và attrition lớn.|Denominator/selection sensitivity; không causal graph effect hoặc counterfactual learning gain.|

RQ2 có thêm evidence về **điều kiện nhận diện** và sự không bền của một profile ordering, chưa hoàn tất confirmatory condition-of-effectiveness. Không loại required baselines, tự adopt protocol/threshold/graph null, đổi seed family hoặc coi các diagnostic controls là mẫu đều của toàn bộ DAG null population.

## Kiểm tra và tái lập

Implementation: [analyze_rq2_controls.py](../../scripts/research/analyze_rq2_controls.py), [27 synthetic tests](../../tests/shared_kt/test_rq2_controls.py). Tests có known-answer paired profile LOO, numerator-vs-denominator sign reversal, unsupported edge None, mismatched degree/counts, common attrition/category arithmetic, source-hash tampering và allowlisted reads không chạm outcomes/traces/dataset/parquet.

| Kiểm có output xác nhận | Kết quả |
|---|---|
|Targeted synthetic suite|27 passed, 0,37s; controller timeout60s, source SHA trước/sau không đổi.|
|Primary stored analysis|0,129116s; `verify_evidence_bundle` verified6outputs; 13 input hashes checked theo selected manifests.|
|Deterministic reproduction|`PYTHONHASHSEED=17`; JSON tái lập giống raw bytes/SHA của primary. Không model/simulator events mới.|

Lệnh chính, từ repository root và chỉ dùng project `.venv`; phải chọn run ID mới vì output không ghi đè:

```powershell
.\.venv\Scripts\python.exe -B scripts/research/analyze_rq2_controls.py --run-id <run-id-moi>
```

Lệnh đã chạy dùng run ID `rq2-conditions-evidence-20261108-01`; wrapper standard-library `subprocess.run(...,timeout=60)` ghi stdout/stderr vào [analysis-01.log](../../artifacts/akt/local-tests/parallel-rq2-controls-20261108-01/analysis-01.log). Test arguments/timeout/source hashes ở [run.json](../../artifacts/akt/local-tests/parallel-rq2-controls-20261108-01/run.json), [JUnit](../../artifacts/akt/local-tests/parallel-rq2-controls-20261108-01/pytest.xml); reproduction command/receipt ở [reproduce-run.json](../../artifacts/akt/local-tests/parallel-rq2-controls-20261108-01/reproduce-run.json), [log](../../artifacts/akt/local-tests/parallel-rq2-controls-20261108-01/reproduce.log). Primary analysis và reproduction không có failure; không sửa các inputs/manifests/bundles cũ.

Primary và reproduced JSON cùng SHA-256 `5bbc381f8f5bc7b86f6035c6502a05e50728f7ee7202546eee46048b6bd2d6a1`. Run mới giữ source/test snapshots với SHA trước/sau copy và closure manifest. Đây là một phép reanalysis/reproduction, không hai thí nghiệm độc lập. Không sửa root index/state/tasks hoặc Git; parent quản lý tích hợp và báo cáo GVHD.
