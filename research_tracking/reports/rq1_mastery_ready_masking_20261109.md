# RQ1 — vì sao mastery khác nhau nhưng tập readiness có thể giữ nguyên?

Trên1.080cặp snapshot full–empty đã lưu,90snapshot có khác biệt native mastery nhưng chỉ60snapshot có tập readiness R khác nhau. Phân tích cached mới giải thích30snapshot còn lại bằng quy tắc controller và cấu trúc đồ thị tại đúng trạng thái đó. **Exposure và trạng thái child-mastered có thể cùng thỏa, nên không được gọi chúng là các nguyên nhân loại trừ nhau.** Không chạy lại policy hoặc simulator, không thêm người học hay nhãn, không đánh giá mastery nào đúng hơn.

Nguồn số là [summary](../runs/rq1-mastery-ready-masking-20261109-01/summary.json), [event flags](../runs/rq1-mastery-ready-masking-20261109-01/event_flags.json) và [đếm lại độc lập từ native snapshots](../runs/rq1-mastery-ready-masking-20261109-01/masking_independent_native_recount02.json). Manifest của [bundle](../runs/rq1-mastery-ready-masking-20261109-01/manifest.json) xác nhận closure thực tế. Báo cáo được freeze trước closure, còn các verdict phân tích dưới đây đã có trong actual receipts.

## 1. Từ câu hỏi RQ1 đến quy tắc đang được kiểm

RQ1 cần phân biệt dự đoán, quyết định thành thạo và cơ chế chọn nội dung. [Chẩn đoán E4](rq1_native_mastery_reference_diagnostic_20261109.md) đã cho thấy native GAM dùng `M=(theta_est>=1250) AND (pi_task<=.55)`. Đây là boolean từ state ước lượng, chưa là latent mastery truth hoặc xác suất đã calibrated. [Tái dựng controller](rq1_fixed_controller_candidates_20261109.md) đã kiểm chính xác R/C/B và khóa chọn concept. Phần còn thiếu ở giữa là điều kiện nào làm khác biệt M không đổi initial readiness.

Source controller dùng bốn predicate tại mỗi snapshot trước current update:

- `I(c)=NOT M(c)` giữ concept chưa được đánh dấu mastered.
- `E(p)=M(p) OR visits(p)>=6` cho mỗi parent. Visits đếm lượt concept đã được hỏi trong logged prefix, không đếm câu đúng hoặc item duy nhất.
- `A(c)=ALL parent E(p)` đòi mọi parent đủ điều kiện. Với root, tập parent rỗng khiến A tự đúng.
- `F(c)=I(c) AND A(c)` là membership trong frontier.

Khi frontier không rỗng, R là frontier. Hai fallback all-mastered/minimum-unresolved vẫn được kiểm theo source. R ở đây là **tập ban đầu trước anti-repeat/escape tạo C và lọc cân bằng tạo B**, không phải quyền chọn bài phổ quát hoặc hành động đã phục vụ. Các hành động fixed-stream đã ghi chỉ là preview trên bản sao. [Source controller đã ghim](../runs/rq1-fixed-controller-candidates-20261109-01/analyze_fixed_controller_candidates02.py).

## 2. Population và bảo toàn hành vi

Giữ nguyên9lịch sử20000–20002×PG/PY/PYH, mỗi lịch sử120queries và hai enabled graph-package arms full/empty. Controller dùng cùng full31edges; chỉ estimator-edge input khác. Các hậu quả update/state nằm trong contrast này, không là direct-logit-only hoặc individual-edge quality.

Admission kiểm18gzip đủCRC/120rows mỗi file,2.160arm states trước current label,28native predicates, query/P/full-preview/legacy identity, node order và toàn2.160R/C/B/CID/khóa chọn/branch. Past visits/recent/chapter được dựng chỉ từ logged-query prefix và đối chiếu từng snapshot. Original fixed runner đã phục hồi từGit e4e6a262…, không mang provenance-gap của nhánh closed-loop khác. [Validation](../runs/rq1-mastery-ready-masking-20261109-01/validation.json), [fixed-stream nguồn](../runs/rq1-fixed-edge-set-contrast-20261108-01/manifest.json).

Các đơn vị được giữ riêng gồm1.080paired event snapshots,30.240paired concept snapshots và33.480parent→child opportunities trên toàn đồ thị. Trong số cuối có148opportunities mà parent M khác giữa hai arms. Ba roots tạo3.240root-concept snapshots và không được dùng làm bằng chứng đã biết prerequisite. Đây đều là trạng thái lặp của9lịch sử cũ, new independentN=0.

## 3. Khác biệt frontier và khác biệt mastery không cùng đơn vị

Mã dưới là `(I_full≠I_empty,A_full≠A_empty,F_full≠F_empty)`. Đây là bất đồng hai điều kiện cùng thời điểm, không phải lần người học vượt ngưỡng theo thời gian.

| Mã | Cặp concept–thời điểm | Diễn giải |
|---|---:|---|
|000|30.026|Ba predicate giữ, không có nghĩa numeric state giữ|
|001|0|Không thể có nếu F là AND của I và A|
|010|44|A đổi nhưng F giữ, concept đã mastered ở cả hai arms|
|011|80|A và F đổi, I giữ concept chưa mastered|
|100|90|I đổi nhưng F giữ, A false ở cả hai arms|
|101|0|Không quan sát|
|110|0|Không quan sát|
|111|0|Không quan sát|
|**Tổng**|**30.240**|Giữ cả các ô0|

Đếm raw độc lập xác nhận cả90changed concepts đều có prerequisite A=false ở hai arms. Vì vậy, khác biệt mastery của chính concept đó không tự làm nó vào/ra R trong những snapshot này. Tuy nhiên, M của concept còn được dùng khi xét các direct children.80frontier membership disagreements bên trên không phải80event R differences; một snapshot có thể có nhiều concept memberships khác nhau.

Trên148changed-parent opportunities, bảng predicate đầy đủ có bốn ô khác0:

| Exposure che khác biệt E? | A của child đổi? | I của child đổi? | F của child đổi? | Opportunities |
|---|---|---|---|---:|
|Không|Không|Không|Không|20|
|Không|Có|Không|Không|44|
|Không|Có|Không|Có|80|
|Có|Không|Không|Không|4|
|**Tổng**||||**148**|

Ở20opportunities, parent E khác nhưng conjunction A vẫn bị prerequisite khác chặn. Ở44opportunities, A khác nhưng child đã mastered nên F giữ. Ở80opportunities, A khác chuyển thành F khác. Ở4opportunities, visits≥6 khiến parent E đúng ở cả hai arms. Đây là các chữ ký predicate, **không là phân bổ tác dụng nhân quả duy nhất**. Đặc biệt,4opportunities exposure còn đồng thời có child mastered, như kiểm riêng dưới đây xác nhận.

## 4. Ba mươi snapshot M khác nhưng R giữ — điều kiện chồng lấp phải được giữ

Raw verifier đọc lại18native streams và toàn prefix, không import analyzer hoặc helper của nó. Kết quả cho30snapshot, tất cả thuộcPG:

| Điều kiện tại snapshot | Events |
|---|---:|
|Changed concept không có direct child, đồng thời chính nó bị prerequisite chặn|18|
|Có direct child đã mastered ở cả hai arms, chưa thỏa exposure tại changed parent|8|
|Có direct child đã mastered ở cả hai arms và đồng thời thỏa exposure|4|
|Chỉ exposure, không có child-mastered|0|
|**Tổng**|**30**|

Đếm không loại trừ nhau là12events có child mastered,4events thỏa exposure, giao bằng4. Vì vậy không diễn giải “18 do topology,8 do child mastery,4 chỉ do exposure”. Với4events cuối, hai điều kiện cùng đúng. Chưa có intervention để gán một nguyên nhân riêng. “Không có direct child” cũng chỉ giải thích immediate readiness tại snapshot, không chứng minh concept hoặc graph không ảnh hưởng state/quyết định tương lai.

Một verifier01 ban đầu đã dừng ở assertion kỳ vọng phân hoạch18/8/4 theo thứ tự ưu tiên nhãn. Khi ưu tiên child-mastered,4events exposure bị gộp vào nhóm child-mastered, làm lộ overlap. Analyzer,9fixtures và cached verdict không đổi. Bản02 đo riêng hai flags và xác nhận bảng trên. Giữ [source verifier01](../runs/rq1-mastery-ready-masking-20261109-01/recount_before02__verify_masking_from_native_snapshots01.py), [inventory](../runs/rq1-mastery-ready-masking-20261109-01/recount_before02__inventory-before.json) và [failure note](../runs/rq1-mastery-ready-masking-20261109-01/recount_before02__failure-note.json). Failure được ghi từ ROOT tool output, không có raw subprocess log riêng và không dựng thêm log thay thế.

## 5. Toàn16nhóm, bao gồm nhóm bằng0

“Parent opps” chỉ đếm changed-M parent trong một child prerequisite set. Những nhóm dưới lồng nhau, không cộng pooled/profile/seed như thêm mẫu.

| Nhóm | Events | M-set khác | R khác | M khác/R giữ | Parent opps |
|---|---:|---:|---:|---:|---:|
|Gộp|1080|90|60|30|148|
|PG|360|86|56|30|144|
|PY|360|0|0|0|0|
|PYH|360|4|4|0|4|
|Seed20000|360|0|0|0|0|
|Seed20001|360|18|0|18|0|
|Seed20002|360|72|60|12|148|
|20000/PG|120|0|0|0|0|
|20000/PY|120|0|0|0|0|
|20000/PYH|120|0|0|0|0|
|20001/PG|120|18|0|18|0|
|20001/PY|120|0|0|0|0|
|20001/PYH|120|0|0|0|0|
|20002/PG|120|68|56|12|144|
|20002/PY|120|0|0|0|0|
|20002/PYH|120|4|4|0|4|

Actual paired snapshots đều ở frontier branch của hai arms. Fallback vẫn được giữ trong source và mọi9branch-pair cells/nhóm, không gọi fallback là cơ chế đã quan sát trong mẫu này. Việc30events đềuPG không xác định causal ability effect; profiles và histories ở đây không phải controlled scalar-ability intervention.

## 6. Nghiệm thu, giới hạn và lưu bằng chứng

ROOT đã chạy pure9 một lần,9PASS/0failure/error/skip. Stored outer trước finalwrite là1.3689911s, ROOT terminal sau finalwrite1.3707195s trong cap20. Cached một lần đạt toàn bộ population, worker2.7010548s, stored outer5.0726772s và ROOT terminal5.0790765s trong allocation mới12/owned10/worker7/cleanup2. Không cộng các thời gian lồng nhau. [Pure raw](../runs/rq1-mastery-ready-masking-20261109-01/pure__unittest.log), [pure outer](../runs/rq1-mastery-ready-masking-20261109-01/pure_outer__final.json), [cached outer](../runs/rq1-mastery-ready-masking-20261109-01/cached_outer__final.json).

Outer đọc lại4actual outputs/SHA/bytes, kiểm38inputs và6current sources trước–sau, đếm độc lập toàn16groups/128concept cells/256parent cells/144branch cells, cùng clean exit/Job0/environment restored. Không có postwrite rejection. Source chỉ kiểm RAM trống trước launch512MiB, không có continuous RSS peak certificate. Independent verifier02 kiểm lại18CRC/2.160states/30.240predicate codes/148opportunities trực tiếp từ native snapshots trong0.4968897s/cap15, giữ source40SHA không đổi. [Verifier02](../runs/rq1-mastery-ready-masking-20261109-01/verify_masking_from_native_snapshots02.py), [proof](../runs/rq1-mastery-ready-masking-20261109-01/masking_independent_native_recount02.json).

Đóng góp choRQ1 là nối rõ **native mastery với initial readiness** bằng các predicate thực sự của controller, đồng thời loại cách gán exposure là nguyên nhân độc lập khi điều kiện chồng lấp. Chưa xác nhận latent mastery, calibration, giả thuyết giảng dạy, hiệu quả từng cạnh hoặc learning benefit. Không CI/p-value, fit, oracle read hoặc newN. Không thay thế full native-M/truth CPU09 bị dừng, không dùng partial failures, không hoàn thànhRQ1. Bundle giữ raw nhỏ, nguồn, review và cả lỗi kỳ vọng verifier01;18gzip và các bundles trước chỉ tham chiếu SHA tại vị trí cũ. ROOT quản lý cập nhật chỉ mục và báo cáo người đọc riêng.
