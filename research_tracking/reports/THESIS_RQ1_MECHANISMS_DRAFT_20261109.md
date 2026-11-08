# Bản thảo kết quả RQ1: từ thay đổi trạng thái đến thay đổi lựa chọn

**Trạng thái:** bản thảo chương kết quả ngày 09/11/2026, dựa trên ba bộ chẩn đoán đã đóng gói. Các số đếm dưới đây mô tả những lịch sử mô phỏng đã có; chưa phải kết luận cuối của RQ1 hoặc kết quả đánh giá CG-AKT. Bản thảo RQ1–RQ2 ngày 08/11 được giữ nguyên để truy vết. Đặc biệt, các bảng full–empty dưới đây không dùng chung định nghĩa đối chứng với mọi bảng full-package–graph-free trước đó.

## 1. Vấn đề tiếp nối từ hai nghiên cứu trước

Đề tài kế thừa hai hướng nghiên cứu: tách ảnh hưởng của đồ thị và chính sách chọn bài trong Paper1, đồng thời kiểm tra prerequisite context trong dự đoán và mô phỏng vòng kín của Paper2. Câu hỏi của RQ1 không dừng ở việc mô hình có dùng thêm cạnh tiên quyết hay không. Điều cần giải thích là thông tin bổ sung đã thay đổi điều gì trong hệ thống, và thay đổi ấy có đi đến quyết định chọn bài hay không.

Một mô hình có thể thay đổi xác suất dự đoán nhưng vẫn giữ nguyên phân loại thành thạo. Ngay cả khi phân loại thay đổi, tập bài được phép chọn hoặc bài đứng đầu tập ứng viên cũng có thể giữ nguyên. Vì vậy, nghiên cứu cần quan sát từng đầu ra tại cùng thời điểm, thay vì đồng nhất cải thiện dự đoán với cải thiện trình tự học.

Điều này không thay thế cách đánh giá xác suất bằng AUC, Log Loss, Brier Score và phân tích hiệu chuẩn đã dùng trong các baseline. Các thước đo đó trả lời xác suất dự đoán có phù hợp với câu trả lời hay không. Các phép đo trong phần này trả lời câu hỏi khác: với quy tắc của hệ thống đang có, khác biệt ở trạng thái được sử dụng như thế nào khi đưa ra quyết định. Chưa có bằng chứng trong phân tích này để gọi phân loại thành thạo nào là đúng hơn.

## 2. Thiết kế đối chiếu và đơn vị quan sát

Phân tích dùng lại chín chuỗi tương tác, tạo bởi ba khối seed và ba hồ sơ PG, PY, PYH; mỗi chuỗi có 120 thời điểm. Tại mỗi thời điểm, hai nhánh full và empty nhận cùng câu hỏi và đáp án đã lưu. Cả hai nhánh giữ graph package hoạt động và dùng cùng đồ thị cho controller; điều thay đổi là tập cạnh đưa vào bộ ước lượng trạng thái. Empty vì thế là đối chứng cạnh rỗng trong package, không được đổi tên thành mô hình hoàn toàn graph-free. [E1]

Có 1.080 cặp thời điểm full–empty. Mỗi cặp cho phép đối chiếu trạng thái của 28 khái niệm, tương ứng 30.240 cặp khái niệm–thời điểm. Đây là các quan sát lặp theo thời gian; không phải 30.240 khái niệm khác nhau hoặc người học độc lập. Ba khối seed và các hồ sơ cũ được tái sử dụng, nên phần này không báo thêm cỡ mẫu độc lập, p-value hay khoảng tin cậy.

Các trace trạng thái được nghiệm thu sau khi kiểm đủ 2.160 snapshot của hai nhánh với hành vi gốc và đối chiếu các fingerprint đầu/cuối. Các tập ứng viên trung gian C/B được tái dựng từ đúng nguồn controller và lịch sử đã ghi, rồi kiểm khớp toàn bộ ready membership và khái niệm thắng. Không gọi thêm model hoặc sinh đáp án khi phân tích C/B và khi ghép các bảng readout. [E1–E3]

Một giới hạn cần giữ khi diễn giải là các lựa chọn trong phép đối chiếu này là **preview**: bài mà controller sẽ đề xuất tại trạng thái đang xét. Chúng không được dùng để thay đổi lịch sử đã ghi và tạo kết quả học tập mới. Do đó, các số đếm dưới đây không đo mức tăng kiến thức do phục vụ một trình tự khác.

## 3. Phát hiện thứ nhất: điều kiện còn lại có thể giữ nguyên phân loại thành thạo

Nguồn GAM-KT xác định thành thạo bằng đồng thời hai điều kiện: điểm kiến thức ước lượng đạt ít nhất 1.250 trên thang Elo, và tham số bất định không vượt quá 0,55. Ký hiệu hai điều kiện lần lượt là T và U thì quyết định M bằng T AND U. Tham số bất định này không phải một xác suất thành thạo đã hiệu chuẩn. [E1]

Trong khi đó, xác suất của câu hỏi hiện tại còn phụ thuộc vào câu cụ thể, độ khó và thời gian. Xác suất, score khái niệm và M là các phép đọc từ cùng trạng thái trước cập nhật; M không trực tiếp lấy xác suất của câu hỏi hiện tại rồi so với một ngưỡng. Vì vậy không mô tả P→M như một phép biến đổi trực tiếp tại cùng bước trong implementation này.

| Tình huống tại cùng khái niệm–thời điểm | Số cặp | Điều giải thích được từ nguồn và trace |
|---|---:|---|
| Cả hai điều kiện T/U giữ nguyên | 26.722 | Phân loại M giữ nguyên, dù giá trị số bên trong có thể đã thay đổi. |
| Chỉ điều kiện bất định U khác nhau | 3.428 | Điểm kiến thức ở cả hai nhánh còn dưới 1.250, nên M vẫn false ở cả hai. |
| Chỉ điều kiện điểm kiến thức T khác nhau | 90 | Cả hai nhánh đã qua điều kiện bất định; full qua điều kiện điểm kiến thức còn empty chưa qua, nên M khác nhau. |

Kết quả định vị được một cơ chế cụ thể: trong 3.428 cặp, khác biệt ở bất định bị điều kiện điểm kiến thức chưa đạt giữ lại tại phép AND. Kết quả không cho biết bất định của nhánh nào đúng hơn; nó giải thích vì sao khác biệt đó không đổi phân loại ở những snapshot này.

Ngược lại, 90 cặp có bất đồng M không phải 90 lần người học vượt ngưỡng theo thời gian. Một khái niệm có thể bất đồng liên tiếp qua nhiều thời điểm. Trong cohort này, 90 cặp khái niệm–thời điểm cũng nằm ở 90 snapshot có M-set khác nhau, nhưng hai đơn vị được đếm riêng và không được coi là đồng nhất trong mọi thí nghiệm. [E1]

## 4. Phát hiện thứ hai: tập ứng viên thay đổi chưa đủ làm đổi khái niệm thắng

Sau phân loại thành thạo, controller tính tập khái niệm được phép chọn R. Nguồn còn áp dụng các điều kiện tránh lặp/thoát bế tắc để được C, rồi lọc theo số lượt đã luyện để được B. Cuối cùng controller chọn khái niệm theo score native và các khóa phân xử của nguồn. Chỉ quan sát R sẽ bỏ qua những bước lọc và xếp hạng này. [E2]

Các số đếm đã tái dựng cho thấy:

- Có 30 snapshot M-set khác nhau nhưng R, C, B và khái niệm được chọn đều giữ nguyên.
- Có bốn snapshot R và C khác nhau, nhưng bộ lọc cân bằng số lượt luyện tạo cùng B, rồi chọn cùng khái niệm.
- Có 51 snapshot B khác nhau nhưng cùng một khái niệm vẫn thắng trong cả hai tập.
- Có năm snapshot khác nhau ở cả M, R, C, B và khái niệm thắng.
- Có 17 snapshot M/R/C/B giống nhau nhưng khái niệm thắng khác nhau; khóa xếp hạng native trên score đã lưu phục hồi chính xác lựa chọn này.

Cùng với 973 snapshot giữ nguyên cả năm đầu ra boolean trên, các tình huống này bao phủ đủ 1.080 cặp. “Giữ nguyên năm đầu ra” không có nghĩa xác suất hoặc mọi score số đều giống nhau. Các nhóm cũng không tạo thành một phễu nhân quả: chúng là các chữ ký đồng thời của hai điều kiện tại cùng snapshot.

Với bốn trường hợp bị lọc khỏi B, nguồn xác định được phép xử lý tập cụ thể làm mất khác biệt membership. Với 51 trường hợp cùng người thắng, thay đổi tập cuối chưa đủ thay đổi native minimum. Cả hai là lời giải thích cơ học về lựa chọn CID trong implementation đang xét; chưa phải ước lượng tác động giáo dục của bộ lọc. [E2]

## 5. Phát hiện thứ ba: hai tổng bằng nhau có thể nói về những snapshot khác nhau

Chẩn đoán trạng thái còn đo một tiêu chí tham chiếu của khái niệm đang được hỏi: lấy trung bình xác suất raw trên ba câu có độ khó đã định nghĩa trong ngân hàng tham chiếu V1, rồi đối chiếu ngưỡng tham chiếu. Đây chưa phải xác suất đã qua temperature calibration và cũng không thay đổi controller native.

Tiêu chí này khác nhau ở 22 cặp full–empty. Khái niệm được preview đề xuất cũng khác nhau ở 22 cặp. Phép ghép một-một theo seed, hồ sơ, thời điểm và query cho thấy hai tập chỉ trùng hai cặp. [E3]

| Tiêu chí xác suất tham chiếu | Khái niệm đề xuất giữ nguyên | Khái niệm đề xuất khác |
|---|---:|---:|
| Giữ nguyên | 1.038 | 20 |
| Khác nhau | 20 | 2 |

Vì vậy, không thể diễn giải hai con số 22 thành 22 lần thay đổi xác suất đã dẫn đến 22 lần đổi bài. Có 20 snapshot ở mỗi phía không trùng nhau. Tất cả năm bất đồng nativeM của **khái niệm đang được hỏi** cũng không trùng bất đồng CID trong mẫu này.

Điểm cuối không mâu thuẫn với 90 snapshot có bất đồng M-set: Query-M chỉ xem một khái niệm của câu đã ghi, còn M-set xét cả 28 khái niệm và controller có thể đề xuất một khái niệm khác. Phân tích giữ đầy đủ 16 nhóm pooled/hồ sơ/seed/quỹ đạo và các ô bằng không; không chỉ chọn trường hợp có lợi cho đồ thị. [E3]

## 6. Kết luận có thể bảo vệ và phần nghiên cứu còn thiếu

Ba kết quả bổ sung một lời giải thích có thể truy vết cho RQ1: khác biệt trạng thái có thể bị điều kiện phân loại còn lại giữ lại; khác biệt tập ứng viên có thể mất sau lọc hoặc vẫn giữ cùng người thắng; và readout của câu đang hỏi không đại diện cho toàn bộ trạng thái mà bộ chọn sử dụng. Mỗi kết luận gắn với phép đối chiếu từng snapshot và quy tắc nguồn cụ thể.

Phần này chưa chứng minh graph có lợi, trung tính hoặc có hại về kết quả học tập; chưa đo đúng/sai của mastery bằng latent truth; chưa tách nhân quả mọi pathway của graph package. Các kiểm tra dự đoán và hiệu chuẩn chuẩn hóa, các đối chứng simulator có kiểm soát, cùng đánh giá closed-loop trên mô hình fitted vẫn là các phần còn lại của kế hoạch RQ1–RQ3. Bằng chứng phần mềm của AKT/CG-AKT không được dùng thay kết quả nghiên cứu đó.

### Nguồn dùng trong bản thảo

- **E1:** [phân tích trạng thái và hai điều kiện mastery](rq1_native_mastery_reference_diagnostic_20261109.md); [bundle trace gốc](../runs/rq1-prediction-mastery-trace-20261109-01/README.md), có raw traces, parity, summary và đối chiếu boolean độc lập.
- **E2:** [tái dựng C/B và khóa chọn CID](rq1_fixed_controller_candidates_20261109.md); [bundle kết quả và failure lịch sử](../runs/rq1-fixed-controller-candidates-20261109-01/README.md).
- **E3:** [phép ghép Query-M/tiêu chí tham chiếu/CID](rq1_query_decision_overlap_20261109.md); [bundle đủ 1.080 cặp và kiểm chéo](../runs/rq1-query-decision-overlap-20261109-01/README.md).

Các nguồn trên là chẩn đoán phát triển từ implementation kế thừa, không thay thế PDF của hai paper hoặc đề cương đã duyệt. Bản thảo giữ riêng bằng chứng quan sát, giải thích cơ học theo nguồn và các kết luận thực nghiệm chưa có.
