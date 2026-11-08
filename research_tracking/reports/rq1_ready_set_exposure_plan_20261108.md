# RQ1 — kế hoạch hậu kiểm ngoại lệ exposure trong ready set

**PROSPECTIVE POST-HOC / CHỈ CHUẨN BỊ NGUỒN — chưa execution, chưa có quantities mới.** Ngày08/11/2026. ROOT review source/pins trước một lần phân tích stdlib có owned-process. Không sửa hai file báo cáo GVHD, C13/C14, raw/history hoặc bundle đã đóng.

## Câu hỏi và giá trị bổ sung

Đề cương trang2–3 yêu cầu phân biệt dự báo, calibration, quyết định thành thạo và lựa chọn hoạt động. Paper2 trang3 đã mô tả ready rule cho parent: **mastered HOẶC đã được chọn ít nhất6lần**. Ta chưa định lượng riêng vai trò ngoại lệ exposure trong các served actions đã log. Phân tích này hỏi: trong đúng những quỹ đạo đã có, những concept nào được mở vì parent mastered, những concept nào cần ngoại lệ exposure, và served concept thuộc loại nào?

Đây là kiểm cách controller sử dụng M, **không calibration fit, policy intervention, causal mediation hoặc learning-effect estimate**. Source rule không mới; phần mới dự kiến là all-event quantitative footprint. Có thể kết quả bằng0, vẫn giữ đủ groups/zero cells. Không chọn threshold/bin sau quantities.

## Inputs cố định, không đọc dataset hoặc chạy code lịch sử

Chỉ đọc bốn file trong bundle [accepted02](../runs/rq1-closed-loop-reconstruction-20261108-02/README.md):

| File | SHA-256 |
|---|---|
|manifest.json|c8bd8f387e5101fca641098257dd5a99d67d2f838cefc3b53b7d9d55248bcb16|
|accepted_fast__observed_metadata.jsonl.gz|1ab8dcd5c5521c1f4055887f8d53032592a74e71949e9caaed83898c6efeb5ce|
|simulator_input__edges.csv|ecd910d8df52f8790997391de657ea0f9e8357446212c168b73e500d0facc2fb|
|prep__closed_loop_native_source_snapshot.json|a080cd079742d83dfef6a78f807d17c62f58dcdff9f8b36e38cc13f4ca428ec8|

Metadata gzip848.299B, dùng M28/call order/R/C/B/served concept/keys/phases. Record chứa nhãn/prediction nhưng analyzer không dùng các trường đó. Controller edges chung cho cả ba variants; **empty estimator không là empty controller**. Không lấy oracle, current/future outcome hoặc served-item P để suy M. Source snapshot selector cell11 SHA `fc616cb9d5067419950cfc4a5e0ae0c2a02afc0d78b6ae86dd72f87224f42310`; parse AST chỉ kiểm source, không exec/eval/import. MIN6 là recipe đã cố định theo Paper2 trang3/sourceaudit, không được tìm giá trị để fit ready trace. Exact R parity không chứng minh6là constant duy nhất có thể khớp dữ liệu.

Node order lấy từ28native `is_mastered` calls đầu có direct caller `ready_set`: chính list comprehension native quét nodes. Phải cùng order/set trên cả3.240rows và M28; không giả JSON object order là native node order. Trước rowt, visits=Counter của toàn bộ served concepts ở steps0..t−1 riêng trajectory; sum(visits)=t. Chỉ tăng sau khi xử lý row hiện tại.

## Phân loại và reconstructed ready rule

Phân hoạch mỗi concept×event thành đúng một trong bốn lớp:

1. `already_mastered`: M[c]=true.
2. `strict_mastery`: M[c]=false và mọi parent có M=true. Roots thỏa vacuous condition, nên xuất root counters riêng.
3. `exposure_exception`: M[c]=false, có parent M=false nhưng mọi parent thỏa M=true hoặc visits≥6.
4. `blocked`: M[c]=false và còn parent M=false/visits<6.

Reconstruct nguyên native `ready_set`, **giữ thứ tự**:

- Nếu frontier có phần tử: returned R là strict_mastery+exposure_exception theo native node order.
- Nếu không còn unmastered: returned R là toàn nodes, branch `all_mastered_fallback`.
- Nếu frontier rỗng nhưng còn unmastered: chọn unmastered có ít parent M=false nhất, theo native order. **Fallback này không trừ parents thỏa exposure exception.** Branch `minimum_unresolved_fallback`.

Không chạy selector strict-mastery thay thế. Không suy hành động giả định nếu bỏ ngoại lệ. C/B giữ nguyên metadata; kiểm served∈B⊆C. Served nằm ngoài returned R có thể do escape; class blocked/mastered trong fallback/escape không tự là prerequisite violation. Không gán controller criterion bằng latent-world threshold1150.

## Population, outputs và acceptance đã định trước

- Toàn3seeds20000–20002×PG/PY/PYH×graph_free/graph_package/empty_graph_package×120steps=3.240unique rows/27trajectories; không intersection/drop/subset.
- Exact M types, phase trước bookkeeping, node order, full step grid. Gzip EOF/CRC, compressed≤2MiB/file, decompressed≤64MiB và≤64KiB/line; max3.240lines.
- Returned R membership **và order exact3.240/3.240**. Một mismatch → STOP; không sửa recipe/relax fallback/filter để cứu claim.
- Concept partition90.720concept-events; bốn served classes và ba ready branches đều partition đúng event denominator. Parent-opportunity counts là edge occurrences của served concepts, không unique parents/learners.
- Xuất40groups:27trajectories+9profile×variant+3variant+pooled. Mọi bốn class/ba branch có zeros explicit;40×28×4=4.480concept cells kể cả0.
- `summary.json`, `event_membership_flags.csv`3.240rows, `validation.json`, `result.json` pending outer. Source/input/plan SHA trước và sau cả publication; output exclusive≤2MiB/file. Trước khi toàn3.240R khớp, analyzer chưa tạo output directory: failure được giữ bằng owned stderr/receipt, không có bảng quantities partial để dùng. Failure sau tạo directory có thêm `failure.json`; marker pending không được nghiệm thu nếu late guard/owned outer fail. Không retry/resume hoặc dùng group aggregates như mẫu độc lập.

Analyzer: `artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/analyze_ready_set_exposure.py`. Không thêm production module/test framework. Source/plan pins truyền explicit trên CLI; chỉ cho fresh output basename trong chính prep. Imports khoa học/native, Popen và network bị audit-deny sau `worker_gate()`; helper stdlib gọi trước scientific imports. Owned helper source/root/prefix/Job kiểm riêng; child không tự gọi process. Không CI/p-value, calibrator, mới model/seed/teacher/graph/RNG.

**Đề xuất một allocation mới tối đa10s gồm owned launch/cleanup/final checks, worker7s/cleanup2s. ROOT duyệt trước dispatch; chưa được chạy.** Không cộng/trừ/reset cap các native reconstruction/failed attempts cũ. Native/model/optimizer calls mới=0. ROOT phải kiểm cumulative outer clock sau persistence và source hashes/cleanup trước acceptance; inner result không tự là nghiệm thu.

## Câu có thể viết sau khi đạt acceptance và có actual quantities

“Trong current-source diagnostic reconstruction, X/3.240served events cần ngoại lệ exposure để thỏa frontier; Y events thỏa strict-mastered parents. Các trường hợp fallback/escape giữ riêng.” Nếu X=0 phải báo0; không đặt mục tiêu kết quả thuận lợi.

Không viết rằng calibration sai, exposure gây học kém/tốt, đổi rule sẽ đổi actual action, hay RQ1 hoàn tất. Đây là footprint source-local; current runner là reconstruction, original a585 còn missing; new independentN=0. Calibration→mastery vẫn thiếu held-role/reference predictions đúng contract. Paper2/source đã công bố rule; bài này không nhận rule là đóng góp mới. Không paired effect sau histories diverge hoặc individual-edge truth/benefit.
