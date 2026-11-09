# Vì sao không quay lại chương có thể là hệ quả của quy tắc chọn bài?

Bản nháp cơ chế RQ1/RQ2, ngày09/11/2026. Có chứng minh từ định nghĩa và bốn fixture nguồn đang chờ Root chạy. Chưa có output kiểm thử mới, simulation mới hoặc kết quả tái lập số liệu PDF.

## Câu hỏi xuất phát từ Paper1

Paper1 phân biệt graph xác định khái niệm nào được phép học và controller chọn khái niệm nào trong tập đó. PDF bản nộp là tài liệu có thẩm quyền theo D37. Trang2 Eq.(3) chỉ đưa một khái niệm vào ready khi estimate của nó dưới1250 và estimate của mọi parent đạt ít nhất1250. Trang3 Eq.(8)–(9) ưu tiên tuyệt đối chương vừa chọn nếu chương đó còn khái niệm ready. Cùng paper báo cáo continuity cho zero re-entry trong các run đã thử. Câu hỏi cơ chế tiếp theo là phần nào của hiện tượng này đã được bảo đảm bởi chính quy tắc, và phần nào còn phụ thuộc graph hoặc đường chạy. [PDF Paper1](../../../../paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf)

Một lần re-entry là chuyển vào chương từng được chọn trước đó. Chuỗi A,A,B,B,C có hai lần chuyển chương và không re-entry. Chuỗi A,B,A có hai lần chuyển chương và một re-entry. Đây là thuộc tính của đường đi chọn bài, chưa đo người học có tiến bộ hay không. [Định nghĩa và bộ đếm nguồn](../../../../src/knowledge_tracing/paper1_pdf/simulator.py)

## Điều kiện đủ cho graph chỉ có cạnh nội chương

Xét graph hữu hạn không cycle, mọi cạnh nội chương, ready và continuity đúng các phương trình trên. Chỉ estimate của khái niệm được chọn mới cập nhật. Không có forgetting, reset, thay graph hoặc thay chapter map giữa run.

Gọi tập đã mastered theo estimate là M. Một node thuộc M không còn nằm trong ready, nên không thể được chọn để cập nhật tiếp. Vì vậy M chỉ giữ nguyên hoặc tăng. Điều này vẫn đúng khi đáp án sai làm estimate của một node chưa mastered giảm. Không cần giả sử mọi estimate tăng đơn điệu.

Nếu chương C còn node chưa mastered, DAG cảm sinh trên các node đó có một source v. Mọi parent của v đều đã mastered, vì không có parent chưa mastered trong DAG cảm sinh và không có cạnh từ chương khác. Do đó C còn ít nhất một node ready. Continuity buộc giữ C cho đến khi toàn bộ C mastered. Sau khi rời C, không node nào của C có thể trở lại ready. Mỗi chương xuất hiện trong nhiều nhất một khối liên tiếp, nên re-entry bằng0 với mọi chuỗi đáp án và mọi tiền tố ngân sách hữu hạn.

Đây là điều kiện đủ cho B1 gồm25cạnh nội chương theo PDF. Nó không yêu cầu mọi chương được hoàn tất. Run có thể hết ngân sách ngay trong chương đầu và vẫn có zero re-entry. Chứng minh không phụ thuộc tie order, phân bố persona hoặc chất lượng dự đoán đáp án. [Ghi chú chứng minh đầy đủ](PAPER1_ZERO_REENTRY_ANALYTIC01.md)

## Graph liên chương một chiều vẫn có thể buộc quay lại

Xét ba khái niệm tự tạo a1 và a2 thuộc chương A, b thuộc chương B. Chỉ có cạnh b→a2. Graph khái niệm là DAG và graph giữa các chương chỉ có B→A, cũng là DAG. Ban đầu a1=1248, b=1249 và a2=1200. Không có latent state hoặc world trong ví dụ này.

| Thời điểm chọn | Ready và quy tắc | Khái niệm chọn | Chương |
|---|---|---|---|
| 1 | a1 và b ready, a1 có Elo thấp hơn | a1 | A |
| 2, sau đáp án đúng ở a1 | a1 vượt1250, a2 còn bị b chặn, chỉ b ready | b | B |
| 3, sau đáp án đúng ở b | b vượt1250, a2 vừa được mở | a2 | A |

Theo công thức Elo và K=40 ở lần đầu của mỗi khái niệm, hai đáp án đúng đầu đủ đưa a1 và b qua ngưỡng. Chuỗi chương suy ra là A→B→A. Continuity vẫn được tuân thủ ở cả ba lần chọn. Cạnh liên chương đi một chiều không ngăn việc bắt đầu A quá sớm rồi phải tạm rời A. Bảng là phép suy luận làm việc trên input fixture đã khai báo, chưa là output test. Nó không mô tả GA31 hoặc một run lịch sử trong PDF. [Fixture phản ví dụ](../../../../tests/paper1_pdf/test_reentry_mechanism.py)

Một điều kiện đủ rộng hơn là mọi parent ngoài C của tất cả node thuộc C đã mastered trước khi vào C. Những parent ấy giữ mastered, nên chứng minh DAG cảm sinh lại áp dụng. Ngược lại, gateway nằm giữa chương có thể chưa được mở lúc chương bắt đầu. GA31 ứng viên có các cạnh liên chương vào những node giữa hoặc cuối chương, nên không áp dụng máy móc mệnh đề nội chương cho mọi đường chạy GA. Điều này không yêu cầu biết historical exact traversal order để công nhận kết quả finite-run được PDF báo cáo.

## Bốn kiểm tra nguồn đang chờ thực thi

| Fixture | Điều được kiểm tra | Điều chưa suy ra |
|---|---|---|
| DAG nội chương nhiều nhánh, một node đã mastered, hai đáp án sai rồi đáp án đúng | Node đã mastered giữ nguyên estimate, tập M tăng, mỗi chương một khối, hoàn tất fixture trong giới hạn40response đã khai báo | Tính đúng trên toàn bộ graph hoặc persona lịch sử |
| Các parent ngoại chương đã mastered lúc entry | Có cạnh ngoài nhưng chương A vẫn hoàn tất liên tiếp | Mọi graph liên chương đều có zero re-entry |
| Một cạnh B→A với node a1 độc lập | A→B→A dù graph giữa chương không cycle | Tần suất re-entry hoặc kết quả GA31 |
| Hai root độc lập, selector global lowest-Elo cục bộ | Ba đáp án đúng có thể cho A→B→A, trong khi controller continuity trên cùng trạng thái đầu cho A→A→A | Một policy ablation đầy đủ hoặc lợi ích giáo dục |

Đối chứng cuối dùng selector nhỏ ngay trong test, tái sử dụng công thức probability và dynamic K public. Nó không sửa, subclass hoặc bypass controller production. Mỗi concept có ba item ở đúng mức1050/1200/1350. Các lựa chọn trong ba bước không gặp tie khó giữa item, nên không thay quy tắc item selection của đối chứng. Bank mang nhãn `paper1-pdf-unverified-mechanism-fixture`; không đọc CSV nghiên cứu, tạo persona/RNG, world response hoặc chạy full matrix.

## Kết luận được phép dùng sau khi có output

Chứng minh cho biết zero re-entry có thể là một invariant cấu trúc của hợp đồng ready–continuity, thay vì một bằng chứng độc lập rằng graph giàu cạnh hơn cải thiện học tập. Fixture liên chương phân định ranh giới của invariant đó. Kiểm thử nếu được chấp nhận sẽ xác nhận implementation ở các tình huống dựng tay nêu trên, không nâng chúng thành dữ liệu người học hoặc bằng chứng instructional benefit.

Phát hiện này bổ sung giải thích cơ chế cho RQ1/RQ2. Nó không chứng minh estimate mastery trùng mastery thật, không xác định chính sách tối ưu và không hoàn tất hai RQ. Các kết quả Paper1 được kế thừa phải tiếp tục ghi đúng phạm vi simulator và finite runs đã báo cáo.

## Nguồn và trạng thái freeze

- PDF SHA256 `984e2f825968c212ca7e76db23a4c9501659ed880ecff6dce437590ad49167f4`, tr.2 Eq.(3)/(6), tr.3 Eq.(8)/(9) và định nghĩa re-entry, tr.3–4 kết quả và giới hạn.
- Extract `docs/thesis_recovery/evidence/paper1.txt` SHA256 `b6d2d4a518a0b40f27c695bdde3ca624ce16ee976cb59151b15b85cee11eda85`.
- Primitives `src/knowledge_tracing/paper1_pdf/simulator.py` SHA256 `b73057bc0523742fe9f8d84f543e305652c032973facbd327437331affb3d37f`, ready144–146, continuity153–156, selected-only update181–186.
- Test mới `tests/paper1_pdf/test_reentry_mechanism.py` SHA256 `365b062098ea2edcb5ac320b469d593024fd577a7801c7a4b9fd35eff7b86074`,116dòng,4 unittest methods theo inspection nguồn. Chưa import, collection hoặc chạy.
- Ghi chú chứng minh `PAPER1_ZERO_REENTRY_ANALYTIC01.md` SHA256 `f296133c4b40eddaa0c0fff22ade830d92d78b6cd4f3fe4ee2a2d58e6701e847`, đã được Root đọc và nhận xét proof sound dưới các giả thiết liệt kê. Đây là source review, không execution evidence.

Lệnh hữu hạn đề xuất cho Root là `.venv/Scripts/python.exe -B -m unittest discover -s tests/paper1_pdf -p test_reentry_mechanism.py -v`, qua controller riêng có cap30giây và lưu stdout/stderr cùng SHA trước/sau. Báo cáo này vẫn là draft source-only cho đến khi có output xác nhận.
