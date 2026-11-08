# RQ1: ready set đổi có luôn làm lựa chọn xem trước đổi không?

Bản hậu kiểm ngày09/11/2026, đã có kết quả cache được ROOT nghiệm thu; bundle dự kiến `rq1-cross-ready-membership-20261109-01` **chưa đóng tại lúc viết**. Không chạy lại mô hình hoặc simulator. Đây là phân tích post-hoc mô tả trên cùng1080snapshot/query/đáp án đã lưu, không phải thí nghiệm học tập mới hay kết luận hoàn tất RQ1.

## Câu hỏi và đơn vị so sánh

Kết quả [full–empty trước đây](rq1_fixed_edge_set_contrast_20261108.md) cho biết graph package có thể đổi prediction, mastery, ready set hoặc preview với tần suất khác nhau. Bản này xét **sự xuất hiện đồng thời** của các thay đổi và hỏi: concept do full package chọn có nằm trong ready set đã ghi của empty package hay không, và ngược lại?

Hai nhánh đều bật cùng graph package; full và empty khác edge set cùng các hệ quả của nó trong graph features/update. So sánh là conditional edge-set ablation trong package đang bật, không chỉ can thiệp trực tiếp vào một logit hoặc chứng minh chất lượng từng cạnh. Một dòng là một snapshot fixed-stream chung seed/profile/event;1080=3seedblocks×3profiles×120events. Các dòng phụ thuộc trong quỹ đạo và giữa profile tái dùng seed; **new independent N=0**, không1080người học độc lập.

`M` là tập concept được native `is_mastered` đánh dấu; `R` là native ready set ghi trên policy gốc; `A` dưới đây là **toàn bộ tuple preview** concept/question/difficulty trên bản sao, chưa được phục vụ cho người học. R không đồng nghĩa calibrated mastery hoặc tập candidate/balanced thực tế bên trong selector.

## Kết quả: giữ cả các trường hợp không đổi

| M đổi | R đổi | Full preview đổi | Số cặp snapshot |
|---|---|---|---:|
| Không | Không | Không |973|
| Không | Không | Có |17|
| Không | Có | Không |0|
| Không | Có | Có |0|
| Có | Không | Không |30|
| Có | Không | Có |0|
| Có | Có | Không |55|
| Có | Có | Có |5|
| **Tổng** | | |**1080**|

R thay đổi ở60cặp, nhưng55trong số đó giữ nguyên full preview. Ngược lại,17cặp preview đổi trong khi cả M và R giữ nguyên. Vì vậy, sự thay đổi membership của R không phải điều kiện cần hoặc đủ cho preview đổi trong các snapshot này. Đây là quan hệ mô tả trên trạng thái đồng thời; không phải causal mediation hoặc bằng chứng “chỉ score gây đổi lựa chọn”.

| Profile, mỗi nhóm360cặp |000|001|100|110|111|
|---|---:|---:|---:|---:|---:|
|PG|259|15|30|51|5|
|PY|358|2|0|0|0|
|PYH|356|0|0|4|0|

Cột là chữ ký M/R/A theo thứ tự trên; ba chữ ký010/011/101 đều0. Tất cả seedblocks và9quỹ đạo được giữ trong summary16groups.5jointchanges đều ở seed20002/profilePG;17preview-only changes ở seed20001 (PG15,PY2). Không suy hiệu ứng ability từ các profile này.

## Cross-ready membership thu hẹp được điều gì?

Ở1075cặp, cả hai preview concept nằm trong cả hai recorded ready sets.5cặp còn lại: full preview concept nằm ngoài empty R, trong khi empty preview concept vẫn nằm trong full R.5cặp này trùng toàn bộ chữ ký111; không có trường hợp cả hai concept cùng nằm ngoài R của nhánh kia.

Mỗi nhánh đều có preview concept thuộc R riêng trong toàn bộ1080cặp. Tuy nhiên, runner tạo dữ liệu cũ đã có assertion `action in ready` và dừng khi vi phạm; **đây là giới hạn admission của artifact**, không phải chứng minh mọi trạng thái/policy đều có tính chất đó. Analyzer mới không ép điều kiện này và giữ riêng tất cả ô own/cross membership, kể cả0.

Không được gọi1075cặp đầu là “score-only”: source selector lấy R rồi có anti-drill escape, lọc candidates và cân bằng visits trước khi xếp hạng. Cache này không ghi C/B của lần preview. Một concept thuộc R bên kia chưa chứng minh nó thuộc B bên kia hoặc được cùng tie context.5cặp ngoài empty R cũng chỉ xác nhận khác biệt membership ở recorded snapshot, không phải hypothetical served action hoặc lợi ích học tập.

## Timing và kiểm tra hợp lệ

Theo `historical_runner.py`, thứ tự là predict trên policy gốc → deepcopy → preview.select → ready_set/S/M trên policy gốc → update bằng đáp án hiện tại → bookkeeping theo item của fixed stream. Selector được đọc từ source snapshot, không thực thi lại trong hậu kiểm. Preview có thể thay bookkeeping của bản sao; R được ghi không phải tập B đã dùng trong bản sao. Không dùng phân tích này cho paired closed-loop comparisons sau khi lịch sử hai nhánh phân kỳ.

ROOT đã chạy một lần analyzer stdlib: terminal quan sát1.1549765s trong cap10s; `owned__final.json` lưu elapsed trước ghi receipt1.1536037921905518s. Owned receipt chấp nhận cleanup, Job active0, không model/solver/teacher hoặc newdata.1080keys/query/y chung cả3nhánh được nối exact, hai rawstreams có3240dòng mỗi stream;11flags cũ được tái lập từng dòng và oldmarginals khớp. Các số full–empty vẫn là P963/M90/R60/A22; không thay full–GF964/944 của báo cáo cũ.

Fixed-stream historical runner gốc đã truy được Git `e4e6a262bddcdd3b6b6de8c1115ef0eb54b3240a`; hồ sơ [C13](rq1_query_observability_reproduction_20261108.md) xác nhận exact legacy parity giữa observed/control/historical. Hạn chế original-source-missing của nhánh closed-loop khác không áp dụng cho fixed-stream này. Không thêm calibrator/threshold, p-value/CI, seed, trajectory hoặc independent N.60purecases trước đó (51loader+9join/set arithmetic) là bằng chứng kỹ thuật riêng, không kết quả nghiên cứu hay60mẫu thực nghiệm.

## Nguồn đối chiếu và phạm vi lưu giữ

- [Manifest cache nguồn](../runs/rq1-fixed-edge-set-contrast-20261108-01/manifest.json), SHA `906d1698482b78708cf16ce9453a8ed866e7dc0ef47cf0b8dca81c2d89b7b044`; gzip legacy/query, parity và oldflags được pin trong plan5inputs, không nhân đôi gzip khi đóng bundle mới.
- Kế hoạch đã freeze: `artifacts/akt/local-tests/akt-research-runner-20261108-01/rq1_cross_ready_plan01.json`, SHA `f54f99fa4cf098ae28bc4488bd827b9bca1b05663472189364618228e4b43fc8`; analyzer `scripts/research/analyze_rq1_cross_ready.py`, SHA `423968f864c84c8fc66a6678bf9351b195cc3ce47d38eb8696ddbab0ee830398`.
- Actual outputs: cùngprep, `rq1-cross-ready-attempt01/summary.json` SHA `a6860a4f01ea650292bd9c7d237e21048aa0e219e85144c299f3e0e3d1abd3c4`; `event_flags.json` SHA `b789c3a686d1b36e6f3b4d4a602128557f3db6bc3b0f33542047f91ac9e0f446`; `validation.json` SHA `deb84f6d340507f9a7c4377faebc6b4894fd186ebb1f044cb6c5c12c95c24789`; `result.json` SHA `0b0df3911de5fe15f3d15e8327674c63b36b3a21d8a66e1c4a966aedef8741d5`.
- Root controller `run_rq1_cross_ready01.py`, terminal/owned metadata và logs tại `rq1-cross-ready01-owned/` sẽ được copy nguyên bytes cùng outputs, source/plan và report snapshot khi ROOT phê duyệt đóng gói. Báo cáo này chưa tuyên bố manifest mới đã tồn tại.

Kết quả bổ sung cho RQ1 là vị trí các thay đổi có thể bị giữ lại hoặc bộc lộ ở preview trong package hiện tại. Vẫn thiếu đánh giá mastery đã hiệu chuẩn và served-action/outcome của mô hình nghiên cứu fitted; membership hậu kiểm không thay thế các phép đo đó.
