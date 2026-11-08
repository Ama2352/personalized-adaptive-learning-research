# RQ1 — khi nào bài được mở vì thành thạo, khi nào vì đã được chọn đủ lần?

Ngày08/11/2026. **Kết quả hậu kiểm cache đã được outer nghiệm thu; báo cáo chờ ROOT review.** Không chạy lại policy, simulator, mô hình hoặc test trong bước đọc/viết báo cáo này. Bằng chứng làm việc chưa được đóng thành bundle riêng; các đường dẫn bên dưới chỉ đúng với checkout có artifacts local.

## 1. Vì sao cần phép kiểm này?

Đề cương KLTN hỏi vì sao thông tin đồ thị chưa chuyển thành cải thiện học tập: dự báo chưa đủ tốt, mức tự tin chưa phù hợp hay ảnh hưởng bị quy tắc chọn bài che khuất? Để trả lời, không thể chỉ nhìn xác suất dự báo. Cần kiểm tra hệ thống thực sự dùng quyết định “đã thành thạo” như thế nào khi cho phép học một nội dung tiếp theo.

[Paper2, trang3, Algorithm1](../../paper2/Paper2_RIVF_2026_Prerequisite_Aware_Knowledge_Tracing.pdf) đã định nghĩa một ngoại lệ quan trọng: một parent được coi là đủ điều kiện nếu **mô hình đánh dấu mastered HOẶC concept đó đã được chọn ít nhất6lần trước bước hiện tại**. Sáu lần được chọn không có nghĩa sáu câu trả lời đúng, sáu bài khác nhau hoặc latent knowledge đã đạt chuẩn. Đây là quy tắc controller, khác ngưỡng1150 của cơ chế học trong môi trường.

Rule này đã có trong paper, không phải phát hiện mới của KLTN. Phần bổ sung ở đây là **định lượng footprint của hai cách thỏa điều kiện trong các hành động thực sự đã phục vụ**, từ trace đã có. [Kế hoạch hậu kiểm](rq1_ready_set_exposure_plan_20261108.md) và analyzer được freeze trước khi ROOT chạy một lần phân tích.

## 2. Kết quả chính: phải tách các bài không có tiên quyết

Trong3.240lượt chọn đã lưu,1.199lượt thuộc lớp `strict_mastery` và2.041lượt thuộc lớp `exposure_exception`. Tuy nhiên, **500/1.199lượt strict là concept gốc không có parent**: điều kiện “mọi parent mastered” tự thỏa với tập parent rỗng. Không dùng các lượt này làm bằng chứng người học đã thành thạo tiên quyết.

Sau khi loại roots, quần thể cần xét điều kiện tiên quyết còn **2.740lượt =699strict +2.041exposure**:

| Điều kiện của concept đã phục vụ | Số lượt | Cách đọc |
|---|---:|---|
| Không có parent (root) |500|Tách khỏi mẫu số đánh giá tiên quyết.|
| Có parent và tất cả parent được mô hình đánh dấu mastered |699|Thỏa điều kiện strict mastery tại snapshot trước selection.|
| Có ít nhất một parent chưa mastered, nhưng mọi parent chưa mastered đều đã được chọn≥6lần |2.041|Eligibility sử dụng ngoại lệ exposure. Không đồng nghĩa parent thực sự đã biết hoặc chưa biết.|
| Concept đã mastered hoặc còn parent không thỏa cả hai điều kiện |0|Không quan sát served concept thuộc hai lớp này trong quần thể đã phân tích.|
| **Tổng** |**3.240**|Các lượt lặp trong27quỹ đạo, không phải3.240người học độc lập.|

Ở2.041lượt exposure có tổng **2.245parent-opportunities chưa mastered**; tất cả2.245đều thỏa visits≥6. Đây là số parent xuất hiện theo lượt chọn: một lượt có thể có nhiều parent, nên2.245không là số lượt, số parent duy nhất hoặc số người học.

**Ý nghĩa đối với RQ1:** quyết định cho phép học tiếp trong controller này không chỉ phụ thuộc mastery. Khi một parent đã thỏa điều kiện exposure, việc đổi boolean mastery của parent đó có thể không đổi riêng điều kiện readiness của nó. Footprint trên chứng minh ngoại lệ được sử dụng trong trace, nhưng chưa xác định bao nhiêu khác biệt dự báo bị “che khuất”, chưa chứng minh calibration sai và chưa cho biết bỏ ngoại lệ sẽ chọn bài nào.

## 3. Giữ đủ hồ sơ và các cấu hình, không suy effect sau phân kỳ

Mỗi hàng có360lượt trên ba seed blocks. “Strict có parent” bằng stored strict trừ roots; mọi roots đã phục vụ trong trace này đều thuộc stored strict. Bảng là mô tả từng quỹ đạo đã diễn ra, **không lấy các hàng khác variant làm paired causal contrasts**: histories/items/outcomes có thể đã phân kỳ.

| Hồ sơ | Estimator variant | Roots | Strict có parent | Exposure có parent | Tổng có parent |
|---|---|---:|---:|---:|---:|
|PG|graph_free|50|186|124|310|
|PG|graph_package|49|181|130|311|
|PG|empty_graph_package|50|186|124|310|
|PY|graph_free|58|5|297|302|
|PY|graph_package|58|27|275|302|
|PY|empty_graph_package|58|5|297|302|
|PYH|graph_free|59|35|266|301|
|PYH|graph_package|59|39|262|301|
|PYH|empty_graph_package|59|35|266|301|

Theo variant, tổng **roots / strict có parent / exposure** lần lượt là graph_free **167/226/687**, graph_package **166/247/667**, empty_graph_package **167/226/687**. Không diễn giải khác biệt số đếm giữa các variant thành mức tăng mastery hay hiệu quả cạnh: đây là quỹ đạo và exposure đã khác nhau. `empty_graph_package` chỉ rỗng estimator edges; controller và environment graph vẫn giữ chung.

Để không chỉ trình bày kết quả gộp, bảng sau giữ đủ9seed×profile và cả ba variants. Mỗi ô có dạng **roots / strict có parent / exposure**, tổng mỗi ô120lượt:

| Seed | Profile | graph_free | graph_package | empty_graph_package |
|---|---|---|---|---|
|20000|PG|18/50/52|17/62/41|18/50/52|
|20000|PY|21/0/99|21/0/99|21/0/99|
|20000|PYH|19/0/101|19/0/101|19/0/101|
|20001|PG|16/52/52|17/46/57|16/52/52|
|20001|PY|19/0/101|17/12/91|19/0/101|
|20001|PYH|20/20/80|20/21/79|20/20/80|
|20002|PG|16/84/20|15/73/32|16/84/20|
|20002|PY|18/5/97|20/15/85|18/5/97|
|20002|PYH|20/15/85|20/18/82|20/15/85|

## 4. Fallback và escape: kiểm đúng nguồn nhưng không gọi nhánh chưa thấy là kết quả

Analyzer reconstruct nguyên `ready_set`, giữ native order: ưu tiên frontier thỏa mastery/exposure; nếu tất cả đã mastered thì trả toàn nodes; nếu còn unmastered nhưng frontier rỗng thì chọn nhóm có ít parent chưa mastered nhất. Nhánh cuối đếm unresolved parents theo M, **không trừ exposure**. Không chạy một policy strict-only thay thế.

**Actual3.240/3.240rows đều dùng frontier; hai nhánh fallback có0rows.** Mọi served concept nằm trong B⊆C và cũng nằm trong returned R;0served outside R,0served already-mastered,0served blocked. Vì thế trong quần thể này không có hành động phục vụ từ nhánh spaced-review mở rộng ra ngoài R. Không được viết rằng fallback hoặc hành động ngoài R giải thích các số exposure trên.

Điều này cũng **không** có nghĩa mọi bộ lọc chọn bài đều không tác động. [Phân tích closed-loop trước](rq1_closed_loop_reconstruction_20261108.md) đã đo thay đổi R→C do anti-repeat và C→B do cân bằng số lượt. Bộ lọc bỏ concept vừa lặp trong chính R khác với escape tìm thêm concept ngoài R. Không suy “không vi phạm tiên quyết thật” từ việc thỏa controller rule; chưa sử dụng latent truth để đánh giá điều đó.

## 5. Dữ liệu, kiểm hợp lệ và execution đã được nghiệm thu

Nguồn là [accepted reconstruction02](../runs/rq1-closed-loop-reconstruction-20261108-02/README.md):27trajectories =3seeds20000–20002×PG/PY/PYH×3variants,120steps mỗi trajectory. M28/R được native observer ghi trước selector bookkeeping; served tuple là hành động thật trong mô phỏng đã lưu. Visits khởi tạo0 riêng mỗi trajectory, dựng từ toàn bộ served prefix và chỉ tăng sau snapshot hiện tại; không dùng current/future outcome.

Đây vẫn là **current-source diagnostic reconstruction** với original runner a585 chưa tìm lại. Stored legacy parity không khôi phục provenance source gốc. Ba seed families được tái sử dụng, **new independentN=0**; không27learners độc lập hoặc thí nghiệm mới sinh3.240outcomes.

| Kiểm | Kết quả actual |
|---|---|
|Population/grid|3.240unique rows,27×120; không drop/intersection.|
|Ready reconstruction|3.240/3.240khớp cả membership và thứ tự; full fallback rule giữ nguyên.|
|Concept partition|90.720concept-events, bốn lớp tách biệt và đầy đủ.|
|Coverage xuất|40groups;4.480concept cells kể cả0; CSV3.240event flags.|
|Selection membership|3.240/3.240served∈B⊆C;0served outside returned R.|
|Input/source|Bốn input SHA và analyzer/plan trước=sau; gzip EOF/CRC và byte/line bounds.|
|Inner worker|2,3425914s trong7s; result ghi pending outer, không tự nghiệm thu.|
|Owned process|RC0, cleanup accepted, Job active0, Popen handle closed; elapsed2,9119983s.|
|Caller terminal|`ACCEPTED_CACHED_SOURCE_LOCAL_DESCRIPTION`,2,9229504s≤10s; không retry.|
|Lời gọi mới|0policy/model/simulator/optimizer/network/child-process calls trong analyzer; owned launcher là tiến trình vận hành riêng.|

Execution một lần do ROOT dispatch. Bước viết báo cáo chỉ đọc các outputs/receipt đã có; không chạy lại analyzer hoặc mở nguyên trace gzip để thực hiện một lượt phân tích khác. Báo cáo không tuyên bố đã nghiệm thu phép kiểm raw độc lập khác mà ROOT đang thực hiện.

## 6. Cách trích dẫn và phần còn thiếu

Có thể viết: **“Trong3.240hành động của current-source reconstruction,500là roots; trong2.740hành động có tiên quyết,2.041cần ngoại lệ exposure để thỏa frontier và699thỏa strict mastery. Điều kiện readiness của controller vì thế không đồng nhất với quyết định mastered của mô hình.”**

Không viết rằng ngoại lệ gây lợi/hại học tập, graph bị vô hiệu hóa, calibration sai, estimator nào tốt hơn hoặc bỏ ngoại lệ sẽ đổi một served action cụ thể. Không chia các số này cho22fixed-stream preview changes để quy phần trăm nguyên nhân: hai modes khác lịch sử, population và đơn vị. Không paired ΔP/loss sau divergence, CI/p-value, edge-only attribution hay RQ completion.

Calibration→mastery vẫn cần reference predictions và dữ liệu phân vai đúng contract. Native M boolean, B-score và served-item P không thay thế nhau; P được tính sau selection. Kết quả này bổ sung một mắt xích controller cho RQ1, không hoàn tất giả thuyết calibration hoặc đánh giá lợi ích closed-loop.

Nguồn làm việc, có thể kiểm trong checkout local:

- [Kế hoạch prospective post-hoc](rq1_ready_set_exposure_plan_20261108.md); [analyzer](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/analyze_ready_set_exposure.py); [freeze/invocation](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready_set_exposure_freeze01.json).
- [Summary40groups/4.480cells](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready-exposure-attempt01/summary.json); [event flags](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready-exposure-attempt01/event_membership_flags.csv); [validation](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready-exposure-attempt01/validation.json).
- [Inner result](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready-exposure-attempt01/result.json); [owned receipt](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready-exposure-owned-attempt01/receipt.json); [caller final](../../artifacts/akt/local-tests/rq1-observability-preparation-20261108-01/ready-exposure-owned-attempt01/final.json).
- [Original metadata gzip](../runs/rq1-closed-loop-reconstruction-20261108-02/accepted_fast__observed_metadata.jsonl.gz), [native selector snapshot](../runs/rq1-closed-loop-reconstruction-20261108-02/prep__closed_loop_native_source_snapshot.json), [controller edges](../runs/rq1-closed-loop-reconstruction-20261108-02/simulator_input__edges.csv).

Exact SHA của lần đọc:

| Artifact | SHA-256 |
|---|---|
|analyzer|2eb46e0a2e35fa95c796c11150fa1fe66dc98e1d107b6e41fe5435a8c667c11b|
|plan|53414badb767d26608c3387386998b66fe2e12eb3efa901dd2fe660f198cb774|
|summary|730b7b572213179a2d6db49190494569c478d753b057d5a147abf863de3e9846|
|event flags|d23005485c8d0f118f6371c88083eb2334093c1c5193ef2bad224355a8818f31|
|validation|8dd1b576b1a9894664970e7199cf09c0dafc090edd2e16dec764eb14215d7a21|
|inner result|3b38cfc83e43eaee7bcf7510942c4fccabe3d40d47b29f1ad345352960a7da7a|
|owned receipt|084e25ffcdd0819b3d1eecc4215a926ec2d4703c1acea0c87785526b6a1ee57e|
|caller final|c3d59699eac92d9d81a92e8352ce74b441c7d7a966c3b20dacf3f553ac83fb20|

Không sửa artifacts/manifest/source/protocol hoặc báo cáo GVHD hiện hành. Cần bundle nhỏ immutable và liên kết durable trước khi dùng working-artifact links như bằng chứng có thể mở từ một clone sạch.
