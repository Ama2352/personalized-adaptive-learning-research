> Bản đọc kèm gói ngày08/11. Nội dung giữ nguyên; chỉ chỉnh đường dẫn tương đối. Nguồn gốc và SHA xem NGUON.json.

# RQ1: full–empty estimator edge-set contrast trên fixed stream — 08/11/2026

## Kết luận và phạm vi

Trên đúng **1.080 query/label pairs chung** đã lưu, full Graph-GAM có log loss và Brier trung bình thấp hơn empty Graph-GAM một lượng nhỏ. Chiều chênh lệch **không đồng đều theo profile**: cả ba trajectory PG đều kém hơn empty; PY và PYH đều tốt hơn. Đây là chẩn đoán có điều kiện trên enabled package và fixed observed history, không phải lợi ích học tập, chất lượng từng cạnh hay bằng chứng nhân quả.

Full và empty cùng `GAMKTPolicy(True)`, cùng item features, parameters và initial state; chỉ estimator edge set khác nhau. Environment/controller graph vẫn full ở cả hai. Edges đi qua parent signal, uncertainty/deficit, q_task/decay và update, rồi có thể làm local state khác nhau. Vì vậy contrast bao gồm tổng hệ quả của edge input trong thuật toán hiện tại, **không chỉ direct logit**. `graph_free=False` tắt cả nonedge local branches nên là control package khác. [Review nguồn](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/source_review.md), [selected notebook cells5/7/13](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/source_excerpts.json), [loader](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/source__paper2_reference.py), [fixed runner GitLF](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/historical_runner.py).

Fixed runner gốc đã truy được Git `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a`; C13 exact legacy parity đã được tái kiểm cho observed/control/historical. Hạn chế original-source-missing của reconstruction closed-loop khác không được gán sang fixed branch này. [Hồ sơ C13](../../../../reports/rq1_query_observability_reproduction_20261108.md).

## Population, kiểm tra và đơn vị

3 seed families20000–20002 ×3 profilesPG/PY/PYH ×120 steps =1.080 keys `(seed,profile,event_id)`; mỗi variant có một row/key. Cả actual query `(concept,question,difficulty,timestamp_iso,timestamp_ns)` và y exact bằng nhau; history observations/bookkeeping dùng cùng logged items. Không intersection, row drop, seed mới hoặc replay; **new independent N=0**. Profiles trong cùng seed family không là replicate độc lập mới, và persona contrast không cô lập ability effect.

P là scalar của current logged query. S là28 native concept scores chưa được hiệu chuẩn; M là stored mastered boolean, không suy từ S≥0,5. R là stored ready set. A là full `(concept,question,difficulty)` preview trên deepcopy, **không phải served action**. Đơn vị riêng:1.080 snapshot pairs,30.240 concept-score/mastery-decision pairs,1.080 preview tuples. Preview timestamp argument làNone; query timestamp không bị gán làm timestamp select.

ONE stdlib cached analysis PASS trong0.6813872000s≤10s,0model/teacher/RNG/replay calls. All40 C13 outputs hash exact;14 source/plan/input hashes trước=sau; all1080 keys; all36 LL/Brier historical checks và16 nhóm giữ đủ. LL dùng clip1e−15, Brier dùng rawP như `diagnostics.py`; không calibration fit, p-value, CI, threshold search hoặc lựa chọn metric hậu nghiệm. [Kế hoạch trước tính](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/plan.json), [mã](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/analyze_full_empty_fixed.py), [receipt](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/run.json), [summary](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/summary.json), [event flags](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/event_flags.json).

## Chênh lệch dự đoán và quyết định

| Đại lượng full−empty | Kết quả | Đơn vị/giới hạn |
|---|---:|---|
| Mean LL delta |−0.0006369740725551903|1.080 supported query targets; âm nghĩa LLfull thấp hơn|
| Mean Brier delta |−0.000338675650001518|Cùng1.080 targets; âm nghĩa Brierfull thấp hơn|
| P thay đổi exact |963/1.080|Current-query scalar, không toàn vector|
| S thay đổi |1.080 snapshots;27.000/30.240 concept pairs|Mean absΔS0.005251146328046196; không calibrated mastery|
| M thay đổi |90 snapshots;90 concept symmetric-difference crossings|Hai đơn vị được tính riêng|
| R thay đổi |60 snapshots;80 membership symmetric-difference entries|Mean Jaccard0.9876675485008819|
| Full preview đổi |22/1.080|cid22;qid22;difficulty0; không served action|

| P exact | Preview giữ | Preview đổi | Mẫu số có điều kiện |
|---|---:|---:|---:|
| P giữ |115|2|117|
| P đổi |943|20|963|

Đây là **NEW full−empty**:963P đổi và943trong số đó giữ preview. **Historical full−GF** của C13 vẫn là964P đổi/944giữ preview; không thay thế hay sửa các số cũ. Cả hai contrasts có22full-preview changes nhưng không được suy ra bằng trừ các changed-count.

Các tập đổi không tạo thành causal funnel:2sameP vẫn đổi preview, và943changedP vẫn giữ preview. Native selector dùng concept score/tie/candidate logic, không chỉ scalarP. Ở fixed runner, preview được gọi sau current prediction; đây là thứ tự instrumentation, không xác lập DAG P→M→R→A. Không trừ changed-count của hai contrasts cũ để suy contrast mới.

## Tất cả nhóm đã định trước

Δ luôn full−empty; số âm LL/Brier thuận cho full theo metric này. Cột M/R/A là số snapshot đổi; S là số concept-score pairs đổi. Không suy độc lập thống kê từ1.080 rows.

| Nhóm | Target pairs | ΔLL | ΔBrier | P đổi | S pairs đổi | M đổi | R đổi | Full preview đổi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|pooled|1080|-0.000636974072555|-0.000338675650002|963|27000|90|60|22|
|profile:PG|360|0.00249907632664|0.0011414043067|321|9000|86|56|20|
|profile:PY|360|-0.00285503694368|-0.00138648788466|321|9000|0|0|2|
|profile:PYH|360|-0.00155496160062|-0.000770943372041|321|9000|4|4|0|
|seed:20000|360|-0.000932008857347|-0.000462798049804|312|9000|0|0|0|
|seed:20001|360|-0.000550758359332|-0.000283797527256|324|9000|18|0|17|
|seed:20002|360|-0.000428155000986|-0.000269431372945|327|9000|72|60|5|
|trajectory:20000:PG|120|0.0020656464103|0.000954399309109|104|3000|0|0|0|
|trajectory:20000:PY|120|-0.00355404769755|-0.00170213657343|104|3000|0|0|0|
|trajectory:20000:PYH|120|-0.00130762528479|-0.000640656885087|104|3000|0|0|0|
|trajectory:20001:PG|120|0.00198032848619|0.000903981160576|108|3000|18|0|15|
|trajectory:20001:PY|120|-0.00303571648967|-0.00145545715006|108|3000|0|0|2|
|trajectory:20001:PYH|120|-0.000596887074512|-0.000299916592284|108|3000|0|0|0|
|trajectory:20002:PG|120|0.00345125408343|0.0015658324504|109|3000|68|56|5|
|trajectory:20002:PY|120|-0.00197534664382|-0.00100186993048|109|3000|0|0|0|
|trajectory:20002:PYH|120|-0.00276037244257|-0.00137225663875|109|3000|4|4|0|

Cả3seed-level means đều âm nhưng mỗi seed gộp ba profiles; điều đó không xóa kết quả PG dương. Các trajectory có M/R đổi mà preview giữ, hoặc S đổi không M/R đổi, là negative results cần giữ; đây không chứng minh graph vô dụng.

## Phép tách đại số trên cùng rows

GF đã certified cùng1080 query+y; không đổi common population. Các mean đều dùng cùng mẫu số:

- ΔLL(full−GF)=−0.0006935695974777178 = **−0.0006369740725551903** (full−empty) + **−0.00005659552492252744** (empty−GF).
- ΔBrier(full−GF)=−0.0003647062784812577 = **−0.000338675650001518** + **−0.00002603062847973973**.

Pooled residual LL−1.0842×10⁻¹⁹/Brier0; tất cả16groups residual≤1e−12. Đây là baseline cancellation theo control order, không causal mediation, path-specific effect hoặc unique attribution. Không tính phần trăm “đóng góp graph” từ các số nhỏ này. Empty−GF phản ánh nonedge enabled-package difference trong cách sắp control này; full−empty gồm edge-state update propagation.

## Điều thật sự hỗ trợ RQ1 và còn thiếu

Bổ sung direct full−empty comparator có cùng enabled package làm rõ edge-information input có thể thay đổi predictions/native scores và một số previews trên cố định exposures; mức LL/Brier và preview khác nhau giữa profiles. Nó thu hẹp cách diễn giải full−GF trước đây, không sửa C13/C14 và không đủ đóng toàn RQ1.

Chưa có calibration/mastery reference contract thực thi cho dữ liệu này, matched nonempty graph-quality controls, path-specific attribution hay closed-loop learning benefit. Preview equality không thay bằng served-action equality; lịch sử cố định không ước lượng can thiệp dạy học. Các kết quả này không chọn hyperparameters/model/graph hoặc final methodology, không thêm estimator hay independent observations. Source/units/negative groups phải đi cùng khi trích luận văn.

[Bundle và giới hạn](../../../../runs/rq1-fixed-edge-set-contrast-20261108-01/README.md); original manifests giữ nguyên đường dẫn lịch sử, copy inventory ánh xạ tên archive. Notebook gốc chỉ hash và selected source cells để tránh nhân đôi toàn notebook; report không dựa vào raw realdata/Holdout.
