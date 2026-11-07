# EXPLORATORY POST-HOC uncertainty của factorial pilot — 07/11/2026

## Kết quả và phạm vi

Phân tích lại aggregates đã lưu giữ nguyên mean interaction: PG0, PY+0,034017258 và PYH+0,053528587. Hai profile PY/PYH đều có7seed interaction dương và3seed âm. Mean khi bỏ lần lượt từng seed vẫn dương, nhưng dấu từng seed biến thiên. Đây là sensitivity sau khi đã xem kết quả pilot, **không phải preregistered inference, final efficacy, equivalence hoặc kết luận nhân quả trên người học thật**.

[JSON đầy đủ](factorial_pilot_uncertainty_20261107.json) lưu30paired aggregates, mọi leave-one-seed-out(LOO), resampling settings, source hashes và kiểm arithmetic. Không query/sinh simulator, không mở outcomes/traces/raw dataset/Holdout, không fit model hoặc dùng GPU. Không sửa phương pháp confirmatory, core source/tests, Gate15 hoặc kitv12.

## Estimand và đơn vị

Nguồn là `research_tracking/runs/cpu-factorial-20261107-01/{contrasts,summary}.json`, bổ sung diễn giải từ README run, `cpu_pilots_20261107.md`, mechanism coverage/followup và `rq12_evidence_synthesis_20261107.{md,json}`. Inventory7tệp và SHA-256 nằm trong JSON. Hai aggregate hashes hiện tại khớp các giá trị mà synthesis đã đối chiếu manifest nguồn; lần này không audit lại toàn bộ bundle hoặc latent/random identity4cells.

Giữ đúng estimand nguồn:

`I_seed,profile = (edge-on − edge-off)|λ0,55 − (edge-on − edge-off)|λ0`.

Treatment “edge-on” bật **parent signal và parent adaptation cùng nhau**, control tắt cả hai; local pathway off ở cả hai. G_env/G_controller giữ graph lịch sử. Mỗi nhóm4cells dùng cùng base realization và step-indexed uniforms theo hồ sơ nguồn. Outcome là net mean theta gain, Elo-scale trung bình trên28concept sau120steps. Không đổi thành raw graph gain, hiệu ứng riêng từng pathway hoặc time-DiD. Initial abilities vẫn được sinh có graph correlation của nguồn.

Đơn vị phân tích là **10seed blocks21000–21009**, mỗi block chứa đủ3profiles và interaction paired4cells.30profile–seed rows không được xem là30blocks độc lập;14.400events của pilot không phải14.400independent learners. Chỉ dùng contrasts đã paired, không resample riêng cells hoặc hai graph-effect components. Vì không mở outcomes, pairing4cells được kế thừa từ aggregate/hồ sơ nguồn, chưa được kiểm lại từ cell outcomes trong gói này.

## Descriptive sensitivity trên tất cả seeds

Không loại/chọn seed theo kết quả. Tất cả10LOO means/profile và toàn bộ seed interactions được xuất trong JSON; range dưới đây không dùng làm formal CI.

| Profile | Mean interaction | Min–max interaction từng seed | Dương/âm/zero | Min–max mean bỏ1seed |
|---|---:|---:|---:|---:|
|PG|0,000000000|[0;0]|0/0/10|[0;0]|
|PY|+0,034017258|[−0,149211020;+0,176815592]|7/3/0|[+0,018150776;+0,054375956]|
|PYH|+0,053528587|[−0,076758152;+0,214224963]|7/3/0|[+0,035673435;+0,068004892]|

LOO cho biết mean quan sát không đổi dấu khi bỏ riêng một block trong10blocks này. Nó không đánh giá bỏ nhiều blocks, tails chưa thấy, population effect hoặc độ ổn định trên simulator/seed families khác. Không dùng LOO để loại seed bất lợi hoặc chọn profile thuận lợi.

Hai components mô tả được giữ để tránh đọc interaction thành graph gain:

| Profile | Mean(edge-on−off), λ0,55 | Mean(edge-on−off), λ0 |
|---|---:|---:|
|PG|+0,110853316|+0,110853316|
|PY|+0,051485897|+0,017468639|
|PYH|+0,378081797|+0,324553209|

PG có interaction0 nhưng graph-effect component không bằng0: penalty bất hoạt không làm package/controller mất mọi ảnh hưởng khác. Không dùng structural zero của interaction để nói “graph không có tác dụng”.

## Khoảng resampling exploratory và giả thiết

Script lấy mẫu lại có hoàn lại10seed blocks/draw,10.000draws, fixed seed42 với `random.Random`(MT19937). Mỗi draw dùng **cùng10indices cho cả3profiles**, giữ phụ thuộc giữa profiles trong block và các contrasts paired nguồn. JSON ghi SHA-256 của toàn bộ chuỗi indices, quantile convention tuyến tính tại rank(n−1)p và chính xác source script.

| Profile | Percentile2,5%–97,5% của resampled mean interaction |
|---|---:|
|PG|[0;0]|
|PY|[−0,021574110;+0,088162708]|
|PYH|[+0,003053027;+0,105689082]|

Các khoảng trên là **envelope của mean khi resample từ empirical distribution10blocks đã thấy**, không formal population95%CI. Việc tính envelope là hợp lệ như phép mô tả arithmetic trên distribution hữu hạn này. Nếu muốn suy rộng thành inference về simulator seed law, cần giả thiết blocks độc lập/exchangeable và đại diện cho seed law cố định; pilot chưa xác lập các giả thiết đó. Initial graph/ability construction, finite profile set và seed selection của pilot không tự xác lập population sampling model.

N=10giới hạn tails và calibration/coverage của bootstrap. Resampling không sinh information mới hoặc khắc phục post-hoc selection.10.000draws chỉ giảm nhiễu Monte Carlo của phép resampling này; không tăng số seed nghiên cứu. Đầu mút trình bày nhiều chữ số chỉ để truy vết arithmetic, không thể hiện độ chính xác khoa học tương ứng.

Family ở đây gồm **3mean interaction** theo PG/PY/PYH. Các khoảng marginal exploratory không được hiệu chỉnh multiple comparison và không có simultaneous coverage; giữ draws chung không tạo phép hiệu chỉnh. Không có p-values, confirmatory rejection, test heterogeneity/profile differences hoặc probability-of-benefit. Việc envelope PYH nằm trên0 không đủ để tuyên bố significance/efficacy, chọn PYH là nhóm có lợi hoặc xác nhận RQ2; dấu điểm ước lượng và profile khác nhau cũng không tự chứng minh interaction heterogeneity.

## Mechanism coverage và PG structural zero

Followup đã lưu báo deficit tại λ0,55: PG0/2.400events, PY1.919/2.400(79,9583%), PYH1.197/2.400(49,8750%). Đây là pooled event coverage của mechanism trong hai treatment cells, không phải independent-sample sizes cho uncertainty. Không dùng tỷ lệ này làm causal mediation estimate hoặc điều chỉnh interaction post-hoc.

Minimum initial PG ability1269,3117807694116 cao hơn readiness1150; dynamics được nguồn kiểm giữ theta_at≥base. Vì vậy zero interaction phù hợp với penalty không exposed trong pilot PG. Envelope[0,0] chỉ phản ánh10observed zeros trong empirical resampling; **không phải proof of equivalence, upper bound cho mọi PG learner hoặc bằng chứng graph neutral**. Không tự mở rộng kết luận sang graph-independent initialization, abilities thấp hơn, readiness khác hoặc dynamics mới.

## Kiểm tra, tái lập và failure giữ lại

Script tại `artifacts/akt/local-tests/parallel-factorial-analysis-20261107-01/analyze_factorial_uncertainty.py`; chỉ Python standard library trong project `.venv`, không cài package. Script chặn ghi đè output cũ và có budget60s. Chạy từ root:

```powershell
& .venv\Scripts\python.exe artifacts/akt/local-tests/parallel-factorial-analysis-20261107-01/analyze_factorial_uncertainty.py --root D:\Dev\KLTN --output <duong-dan-JSON-moi>
```

| Kiểm | Output xác nhận |
|---|---|
|Grid/pairing aggregate|30rows, đúng10seed×3profiles, không duplicate/missing; không independently sample component/cell|
|Arithmetic nguồn|Mỗi stored interaction bằng graph-effect-on−off với tolerance1e−12|
|Summary nguồn|Means tính lại khớp cả3source means với absolute error bằng0|
|Negative controls|Known4cell answer, identity theo λ, identity theo treatment và constant-zero arithmetic đềuPASS|
|Identity nguồn|2aggregate SHA khớp synthesis recorded manifest verification;7input hashes ghi trong JSON|
|Run thành công02|`analysis-02.log`:PASS,10.000draws,0,050074s|
|Tái lập|`reproduce.log`:PASS,0,067714s; `reproduced.json` có cùng raw-byte SHA với JSON chính|

JSON chính và reproduced cùng SHA-256:

`9cbc08bfe19b23d7cef4709dccbd35b6a6f5780cf7a9f68d42eebcd15c729502`.

Lượt đầu `analysis.log` fail trước ghi JSON do dùng sai tên metadata key synthesis(`hash_checks` thay vì `selected_output_hash_checks`). Giữ source snapshot `analyze_factorial_uncertainty_failed01.py` và failure log. Sửa key lookup, không sửa input/result nguồn. Các logs/source/reproduced nói trên cùng thư mục `parallel-factorial-analysis-20261107-01/`; parent sẽ archive inventory trước mọi chuyển/copy. Không sửa immutable manifests/state/tasks/index và không Git stage/commit trong gói này.

## Cách dùng khi viết KLTN

Câu có thể trích: “Exploratory post-hoc trên10paired seed blocks/profile cho mean λ×edge interaction PY+0,0340 và PYH+0,0535Elo-scale; từng seed có cả dấu dương và âm. Leave-one-seed-out means giữ dấu dương trong sample này, nhưng số seed nhỏ, cơ chế/initialization conditional và giả thiết seed-population inference chưa được xác lập; chưa đủ kết luận graph-benefit.”

Gói này cập nhật uncertainty/sensitivity của pilot đã có, không biến nó thành final independent evaluation. Kế hoạch confirmatory cần freeze estimand/family/seed handling/precision trước seeds mới theo methodology được duyệt; báo cáo này không tự thông qua kế hoạch đó.
