# Cơ chế không quay lại chương trong Paper1

Ngày 09/11/2026. RQ1 tìm nguyên nhân tác động của đồ thị không chuyển thành cải thiện học tập. Phản hồi GVHD yêu cầu kiểm xem một số kết quả có được bảo đảm bởi bộ mô phỏng hay bộ điều khiển hay không. Phần này kế thừa PDF Paper1 theo D37, chứng minh điều kiện đủ và kiểm ranh giới của điều kiện đó bằng bốn tình huống dựng tay.

## Từ kết quả Paper1 đến câu hỏi cơ chế

Paper1 báo cáo controller giữ chương không quay lại chương cũ trong các lượt đã thử. Ready chỉ chứa khái niệm có điểm ước lượng dưới 1250 và mọi tiên quyết đã đạt ngưỡng. Khi chương vừa chọn còn khái niệm ready, controller tiếp tục chọn trong chương đó. Chỉ điểm của khái niệm được chọn được cập nhật. Các quy tắc này cho phép hỏi liệu zero re-entry có thể suy ra từ cấu trúc trước khi xem số liệu hay không. Nguồn là Eq.(3), Eq.(6), Eq.(8)–(9) và định nghĩa re-entry trong PDF. [Paper1](../../paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf).

## Điều kiện đủ và chứng minh

Giả sử đồ thị hữu hạn không có chu trình, mọi cạnh nằm trong cùng chương, ready và continuity theo các quy tắc trên, không forgetting/reset hoặc đổi đồ thị trong lượt chạy.

1. Khái niệm đã đạt ngưỡng không còn trong ready, nên không được chọn để cập nhật tiếp. Tập khái niệm đạt ngưỡng vì vậy chỉ giữ nguyên hoặc tăng. Đáp án sai vẫn có thể làm giảm điểm của khái niệm chưa đạt ngưỡng.
2. Nếu một chương còn khái niệm chưa đạt ngưỡng, xét đồ thị cảm sinh trên các khái niệm đó. Nó có một node không còn parent trong tập chưa đạt ngưỡng. Vì không có parent ngoài chương, node ấy ready.
3. Do đó controller chỉ rời chương sau khi mọi khái niệm của chương đạt ngưỡng. Sau lúc rời, chương không có node ready trở lại. Mỗi chương xuất hiện trong tối đa một khối liên tiếp.

Suy ra re-entry bằng 0 cho mọi chuỗi đáp án và mọi tiền tố hữu hạn dưới các giả thiết này. Điều kiện áp dụng cho dạng đồ thị B1 gồm các cạnh nội chương. Một lượt có thể hết ngân sách ngay trong chương đầu và vẫn thỏa kết luận. Chứng minh cũng cho thấy chất lượng dự báo đáp án không phải điều kiện cần để nhận zero re-entry trong trường hợp này. [Định nghĩa đã cài theo PDF](../../src/knowledge_tracing/paper1_pdf/simulator.py), [chứng minh chi tiết lưu cùng bundle](../runs/paper1-reentry-mechanism-20261109-01/analytic_note.md).

## Phản ví dụ xác định ranh giới

Dựng a1, a2 thuộc chương A và b thuộc chương B. Chỉ có cạnh b→a2. Điểm đầu lần lượt là 1248, 1200 và 1249. Đồ thị giữa chương chỉ có B→A, cũng không có chu trình.

| Bước | Điều kiện trước khi chọn | Lựa chọn | Sau đáp án đúng |
|---|---|---|---|
| 1 | a1 và b ready, a1 có điểm thấp hơn | a1 ở A | a1 đạt ngưỡng, a2 vẫn bị b chặn |
| 2 | Chương A tạm hết ready, b còn ready | b ở B | b đạt ngưỡng, a2 được mở |
| 3 | a2 vừa được mở | a2 ở A | Đã quay lại A |

Chuỗi A→B→A đã được kiểm qua entrypoint controller. Cả ba lần chọn đều tuân thủ continuity. Điều kiện rộng hơn vẫn đủ nếu mọi parent ngoài chương của tất cả node trong chương đã đạt ngưỡng trước khi vào chương đó. Chỉ yêu cầu đồ thị giữa chương không có chu trình là chưa đủ. [Bốn tình huống kiểm cơ chế](../../tests/paper1_pdf/test_reentry_mechanism.py).

## Kết quả kiểm local

Root chạy bốn test trên `.venv`, hoàn tất trong 0,2165947 giây theo wrapper, dưới trần 30 giây. Cả bốn đạt, nguồn trước/sau trùng nhau.

| Tình huống | Kết quả được kiểm |
|---|---|
| Đồ thị nội chương nhiều nhánh, có node đã đạt ngưỡng và hai đáp án sai đầu lượt | Tập đạt ngưỡng hấp thụ, điểm node đã đạt giữ nguyên, mỗi chương một khối |
| Parent ngoại chương đã đạt ngưỡng trước entry | Chương A được xử lý liên tiếp |
| Một cạnh B→A và node a1 độc lập | A→B→A, một lần re-entry |
| Hai root và ba đáp án đúng | Selector global lowest-Elo nhỏ cho A→B→A, controller continuity cho A→A→A |

Đối chứng cuối dùng selector nhỏ trong test để phân biệt vai trò của bộ lọc chương. Bộ kiểm dùng trạng thái khai báo và đáp án cố định. Tần suất re-entry trên toàn bộ người học, đồ thị GA và ngân sách nghiên cứu vẫn cần được đánh giá riêng. [Raw kết quả](../runs/paper1-reentry-mechanism-20261109-01/result.json), [log đầy đủ](../runs/paper1-reentry-mechanism-20261109-01/stderr.log).

## Đóng góp cho RQ1 và RQ2

Đã xác định một tập điều kiện trong đó kết quả zero re-entry là hệ quả cấu trúc. Khi diễn giải Paper1, cần đặt chỉ tiêu này cạnh điều kiện controller và topology. Nó mô tả đường đi chọn bài. Để kết luận lợi ích học tập còn cần trạng thái kiến thức thật và kết quả học sau cùng. Cạnh liên chương có thể làm mất bảo đảm đó, như phản ví dụ đã kiểm.

Phần tiếp theo là kiểm trên phiên bản mô phỏng theo PDF với hồ sơ và nguồn ngẫu nhiên được khai báo rõ, đối chiếu kết quả học với đường đi quyết định. Các kết quả PDF tiếp tục được kế thừa theo phạm vi đã công bố.
