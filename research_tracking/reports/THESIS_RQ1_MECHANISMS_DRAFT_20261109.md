# Bản thảo kết quả RQ1: từ thay đổi trạng thái đến thay đổi lựa chọn

**Trạng thái:** bản thảo chương kết quả ngày 09/11/2026, bổ sung hai phần bằng chứng mới vào bốn bộ chẩn đoán đã đóng gói. Các số đếm dưới đây mô tả những lịch sử mô phỏng đã có; chưa phải kết luận cuối của RQ1 hoặc kết quả đánh giá CG-AKT. Bản thảo RQ1–RQ2 ngày 08/11 được giữ nguyên để truy vết. Đặc biệt, các bảng full–empty dưới đây không dùng chung định nghĩa đối chứng với mọi bảng full-package–graph-free trước đó.

## 1. Vấn đề tiếp nối từ hai nghiên cứu trước

Đề tài kế thừa hai hướng nghiên cứu: tách ảnh hưởng của đồ thị và chính sách chọn bài trong Paper1, đồng thời kiểm tra prerequisite context trong dự đoán và mô phỏng vòng kín của Paper2. Câu hỏi của RQ1 không dừng ở việc mô hình có dùng thêm cạnh tiên quyết hay không. Điều cần giải thích là thông tin bổ sung đã thay đổi điều gì trong hệ thống, và thay đổi ấy có đi đến quyết định chọn bài hay không.

Một mô hình có thể thay đổi xác suất dự đoán nhưng vẫn giữ nguyên phân loại thành thạo. Ngay cả khi phân loại thay đổi, tập bài được phép chọn hoặc bài đứng đầu tập ứng viên cũng có thể giữ nguyên. Vì vậy, nghiên cứu cần quan sát từng đầu ra tại cùng thời điểm, thay vì đồng nhất cải thiện dự đoán với cải thiện trình tự học.

Điều này không thay thế cách đánh giá xác suất bằng AUC, Log Loss, Brier Score và phân tích hiệu chuẩn đã dùng trong các baseline. Các thước đo đó trả lời xác suất dự đoán có phù hợp với câu trả lời hay không. Các phép đo trong phần này trả lời câu hỏi khác: với quy tắc của hệ thống đang có, khác biệt ở trạng thái được sử dụng như thế nào khi đưa ra quyết định. Chưa có bằng chứng trong phân tích này để gọi phân loại thành thạo nào là đúng hơn.

## 2. Thiết kế đối chiếu trạng thái và đơn vị quan sát

Ba phát hiện về trạng thái và preview ở các mục 3–5 dùng lại chín chuỗi tương tác, tạo bởi ba khối seed và ba hồ sơ PG, PY, PYH; mỗi chuỗi có 120 thời điểm. Đây là các mã hồ sơ được giữ nguyên từ nguồn, không được tự xem là ba mức năng lực chung. Tại mỗi thời điểm, hai nhánh full và empty nhận cùng câu hỏi và đáp án đã lưu. Cả hai nhánh giữ graph package hoạt động và dùng cùng đồ thị cho controller; điều thay đổi là tập cạnh đưa vào bộ ước lượng trạng thái. Empty vì thế là đối chứng cạnh rỗng trong package, không được đổi tên thành mô hình hoàn toàn graph-free. [E1]

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

Sau phân loại thành thạo, controller tính tập sẵn sàng ban đầu R theo quy tắc tiên quyết. Nguồn tiếp tục xử lý tránh lặp/thoát bế tắc để được C, rồi lọc theo số lượt đã luyện để được B. Riêng nhánh `escape_all_nodes` có thể thay tập ứng viên bằng toàn bộ khái niệm; vì vậy C không được giả định luôn là tập con của R, và R không phải ràng buộc cứng cho mọi lựa chọn trong mọi tình huống. Cuối cùng controller chọn khái niệm theo score native và các khóa phân xử của nguồn. Chỉ quan sát R sẽ bỏ qua những phép biến đổi tập và xếp hạng này. [E2]

Các số đếm đã tái dựng cho thấy:

- Có 30 snapshot M-set khác nhau nhưng R, C, B và khái niệm được chọn đều giữ nguyên.
- Có bốn snapshot R và C khác nhau, nhưng bộ lọc cân bằng số lượt luyện tạo cùng B, rồi chọn cùng khái niệm.
- Có 51 snapshot B khác nhau nhưng cùng một khái niệm vẫn thắng trong cả hai tập.
- Có năm snapshot khác nhau ở cả M, R, C, B và khái niệm thắng.
- Có 17 snapshot M/R/C/B giống nhau nhưng khái niệm thắng khác nhau; khóa xếp hạng native trên score đã lưu phục hồi chính xác lựa chọn này.

Cùng với 973 snapshot giữ nguyên cả năm đầu ra boolean trên, các tình huống này bao phủ đủ 1.080 cặp. “Giữ nguyên năm đầu ra” không có nghĩa xác suất hoặc mọi score số đều giống nhau. Các nhóm cũng không tạo thành một phễu nhân quả: chúng là các chữ ký đồng thời của hai điều kiện tại cùng snapshot.

Với bốn trường hợp bị lọc khỏi B, nguồn xác định được phép xử lý tập cụ thể làm mất khác biệt membership. Với 51 trường hợp cùng người thắng, thay đổi tập cuối chưa đủ thay đổi native minimum. Cả hai là lời giải thích cơ học về lựa chọn CID trong implementation đang xét; chưa phải ước lượng tác động giáo dục của bộ lọc. [E2]

## 5. Phát hiện thứ ba: hai tổng bằng nhau có thể nói về những snapshot khác nhau

Chẩn đoán trạng thái còn đo một tiêu chí tham chiếu của khái niệm đang được hỏi. Vì xác suất trả lời phụ thuộc độ khó câu hỏi, dùng cùng bộ ba câu giúp đối chiếu các cấu hình trên cùng mốc tham chiếu. Phép đo lấy trung bình xác suất raw trên ba độ khó 1.050, 1.200 và 1.350 Elo, rồi đối chiếu ngưỡng V1 là 0,5637150147511514. Đây chưa phải xác suất đã qua temperature calibration và cũng không thay đổi controller native. “Thay đổi” trong bảng dưới là bất đồng của hai cờ phân loại full–empty tại cùng snapshot; không có nghĩa chỉ một thay đổi số bất kỳ của xác suất.

Tiêu chí này khác nhau ở 22 cặp full–empty. Khái niệm được preview đề xuất cũng khác nhau ở 22 cặp. Phép ghép một-một theo seed, hồ sơ, thời điểm và query cho thấy hai tập chỉ trùng hai cặp. [E3]

| Tiêu chí xác suất tham chiếu | Khái niệm đề xuất giữ nguyên | Khái niệm đề xuất khác |
|---|---:|---:|
| Giữ nguyên | 1.038 | 20 |
| Khác nhau | 20 | 2 |

Vì vậy, không thể diễn giải hai con số 22 thành 22 lần thay đổi xác suất đã dẫn đến 22 lần đổi bài. Có 20 snapshot ở mỗi phía không trùng nhau. Tất cả năm bất đồng nativeM của **khái niệm đang được hỏi** cũng không trùng bất đồng CID trong mẫu này.

Điểm cuối không mâu thuẫn với 90 snapshot có bất đồng M-set: Query-M chỉ xem một khái niệm của câu đã ghi, còn M-set xét cả 28 khái niệm và controller có thể đề xuất một khái niệm khác. Phân tích giữ đầy đủ 16 nhóm pooled/hồ sơ/seed/quỹ đạo và các ô bằng không; không chỉ chọn trường hợp có lợi cho đồ thị. [E3]

## 6. Phát hiện thứ tư về ECE gộp có thể che sai lệch dự báo trái dấu giữa các hồ sơ

### Vì sao quay lại kiểm tra độ tin cậy của xác suất?

Ba phát hiện trước giải thích hệ thống đã sử dụng trạng thái như thế nào. Một câu hỏi cần đặt song song là chính xác suất dự báo đáp án có đáng tin trên quần thể mà hệ thống đã phục vụ hay không. AUC đánh giá thứ hạng, còn Log Loss và Brier Score đánh giá sai số xác suất tổng thể. Reliability đặt câu hỏi cụ thể hơn khi gom những lần có forecast gần nhau lại, tỷ lệ đúng quan sát được có gần forecast đó không. Các kết quả baseline AUC/Log Loss/Brier vẫn được giữ, phép phân rã này bổ sung cách đọc calibration theo nhóm. [E4]

Phân tích dùng lại 14.400 served events của CPU09, gồm 10 seed 21000–21009, ba hồ sơ PG/PY/PYH và bốn arms. Mỗi world có 120 bước, tổng 120 worlds. Mỗi persona-arm có 1.200 dòng và mỗi arm gộp có 3.600 dòng. Đây là mười seed clusters đã dùng lại, không phải120 người học độc lập hoặc14.400 quan sát độc lập mới. Quần thể này khác chín fixed streams và 1.080 preview pairs của các mục 3–5, nên hai nhóm số đếm không được cộng hoặc ghép như cùng một phép đối chiếu.

Bốn arms kết hợp λ=0 hoặc 0,55 với gOFF/gON. gOFF tắt parent signal và parent adaptation, gON bật cả hai. Local pathway tắt ở cả hai, graph môi trường và controller giữ nguyên. Sau phân kỳ action hoặc feedback, mỗi arm có thể phục vụ các query/history riêng. Vì vậy các bảng dưới là mô tả reliability trên served population của từng arm. Chúng chưa ước lượng tác động policy trên cùng query/history, chưa tách từng pathway hoặc từng cạnh. PG/PY/PYH là profile được kế thừa từ nguồn, không phải các mức scalar ability được can thiệp độc lập.

### Cùng 15 bins của baseline, hai loại đối chiếu đáp án

Phép chia bin giữ evaluator BKT/GAM-KT hiện hành `bin=min(int(15P),14)`, với khoảng `[k/15,(k+1)/15)` và bin cuối chứa P=1. Ordinary ECE15 bằng `Σ_b (n_b/N)|mean(P)_b−mean(Y)_b|`. Bin rỗng được giữ với count 0 và mean null. ECE thấp hơn mô tả gap theo bins nhỏ hơn trên đúng population được tính. Không được dùng nó để thay thứ hạng baseline hoặc kết luận về học tập. [E4]

Trong simulator còn có `p_true`, xác suất tạo đáp án tại đúng bài, timestamp và trạng thái thế giới đã phục vụ. Chỉ evaluator hậu nghiệm đọc giá trị này. Oracle-response ECE15 thayY bằng `p_true`, giúp đối chiếu bias của forecast với xác suất sinh đáp án mà không đồng nhất một đáp án hữu hạn với xác suất đó. Trong mỗi bin, `mean(P−Y)=mean(P−p_true)+mean(p_true−Y)`. Sau trị tuyệt đối và cộng bins, ordinary ECE và oracle-response ECE phải tính riêng. Không cộng hai scalar ECE theo đẳng thức có dấu.

Bảng giữ đủ bốn arms, làm tròn sáu chữ số. Mỗi persona row dùng 1.200 events, mỗi pooled row dùng 3.600 events.

| λ | Policy | Nhóm | Ordinary ECE15 | Oracle-response ECE15 |
|---|---|---|---:|---:|
| 0 | gOFF | PG | 0,200792 | 0,215098 |
| 0 | gOFF | PY | 0,171412 | 0,160990 |
| 0 | gOFF | PYH | 0,094043 | 0,087773 |
| 0 | gOFF | Gộp | 0,030269 | 0,032524 |
| 0 | gON | PG | 0,197034 | 0,212556 |
| 0 | gON | PY | 0,152721 | 0,150017 |
| 0 | gON | PYH | 0,089085 | 0,074047 |
| 0 | gON | Gộp | 0,040044 | 0,039275 |
| 0,55 | gOFF | PG | 0,200792 | 0,215098 |
| 0,55 | gOFF | PY | 0,171412 | 0,162006 |
| 0,55 | gOFF | PYH | 0,094876 | 0,088478 |
| 0,55 | gOFF | Gộp | 0,030547 | 0,032927 |
| 0,55 | gON | PG | 0,197034 | 0,212556 |
| 0,55 | gON | PY | 0,152529 | 0,150806 |
| 0,55 | gON | PYH | 0,089085 | 0,074731 |
| 0,55 | gON | Gộp | 0,040606 | 0,039902 |

### Vì sao thứ hạng descriptive đảo khi gộp?

Ở λ=0,55, ordinary ECE15 của gON thấp hơn gOFF trong từng PG/PY/PYH. Khi gộp cả ba, ordinary ECE15 lại là 0,040606 của gON so với 0,030547 của gOFF. Bảng λ=0 cũng có hiện tượng này. Số gộp không phải trung bình các ECE theo hồ sơ vì signed gaps được gộp trong từng bin rồi mới lấy trị tuyệt đối.

Hướng lệch ở λ=0,55 cho thấy PG bị dự báo thấp hơn xác suất trả lời đúng của simulator, còn PY và PYH bị dự báo cao hơn. Mean(P−`p_true`) của PG là −0,215098/gOFF và−0,212556/gON. PY là +0,162006 và+0,150806. PYH là +0,088478 và+0,074731. Những số này nói về response bias của các served populations, chưa phải sai số ước lượng mastery hoặc ability.

Cơ chế bù trừ thấy trực tiếp ở gOFF/λ=0,55 trong bin `[7/15,8/15)`. Signed empirical gap mean(P−Y) lần lượt là −0,234774 của 341 PG events, +0,187376 của 430 PY events và+0,088164 của 436 PYH events. Khi gộp 1.207 events trong bin này, gap còn +0,032273. Dấu trái nhau làm gap gộp nhỏ đi trước trị tuyệt đối. Đây là minh chứng số học cho việc một ECE gộp nhỏ có thể che lệch lớn theo hồ sơ. Nó chưa xác định nguyên nhân của lệch hoặc calibration method nào sẽ sửa được lệch. [E4]

### Giới hạn bổ sung cho RQ1

Đóng góp ở đây là phép phân rã response reliability theo hồ sơ và kiểm tra bù trừ theo bins trên cache đã có. Nguồn giữ đủ 120 world groups, 12 persona-arm groups, 4 pooled arms và 2.040 bins, kể cả bins rỗng. Các group views biểu diễn lại cùng 14.400 events, tương ứng 43.200 lượt sử dụng dòng. Chúng không tạo thêm N. Không có simulation, model fit hoặc temperature fit mới, CI hay p-value.

`p_true` chỉ là truth của đáp án đã phục vụ trong simulator. Native mastery M còn dựa vào theta_est và pi. Pi không phải xác suất trả lời đúng. Criterion reference-mixture tại τ lại dùng một population query khác. Vì vậy response reliability chưa cho biết M hoặc quyết định tại τ đúng hơn, chưa chứng minh gating accuracy, ability accuracy hoặc learning benefit. Các failure replay native mastery hiện tại được giữ trong hồ sơ kiểm phần mềm riêng và không dùng làm phát hiện RQ1.

Bundle E4 đã đóng gói, và bảng tổng hợp 16 nhóm đã được đối chiếu với các bins được nghiệm thu. Báo cáo chuyên đề là snapshot viết trước khi đóng gói nên còn câu mô tả archiver đang chuẩn bị. Bản thảo này dùng manifest đã hoàn tất để xác định trạng thái bằng chứng, giữ nguyên báo cáo cũ và không gán ngược thời điểm lưu recipe tổng hợp.

## 7. Kiểm tiếp trên cùng lịch sử và cùng câu hỏi

Phát hiện về reliability ở mục 6 còn một giới hạn quan trọng. Các cấu hình chọn bài khác nhau có thể phục vụ những câu hỏi và lịch sử khác nhau. Để kiểm hiện tượng gộp nhóm che sai lệch trong điều kiện giữ chung đầu vào, nghiên cứu trở lại chín chuỗi cố định ở các mục 3–5. Hai cấu hình nhận cùng lịch sử, câu hỏi và đáp án. Điểm được đọc là trung bình ba xác suất raw của ba câu tham chiếu cho khái niệm đang hỏi. [E5]

Nguồn sinh dòng dữ liệu lấy câu hỏi ngẫu nhiên đều từ bộ 84 câu, mỗi khái niệm có ba câu. Trong thiết kế này, trung bình ba xác suất có thể được đánh giá như dự báo cho đáp án của một câu lấy ngẫu nhiên trong khái niệm đó. Mỗi đáp án đã quan sát được dùng một lần cho mỗi cấu hình. Có 1.080 tình huống chung, tương ứng 2.160 dòng cấu hình. Ba xác suất trong một điểm trung bình không làm tăng số đáp án lên ba lần.

Điểm trung bình giúp đối chiếu các cấu hình trên một mốc câu hỏi chung. Việc đánh giá nó với đáp án trước hết kiểm mức phù hợp của xác suất trả lời. Độ đúng của quyết định thành thạo cần được kiểm riêng bằng trạng thái kiến thức thật. Cách phân biệt này giữ cùng mục đích của Log Loss, Brier Score và reliability trong các baseline.

| Nhóm | Số tình huống chung | ECE15 khi nhận đủ cạnh | ECE15 khi cạnh rỗng |
|---|---:|---:|---:|
| Gộp | 1.080 | 0,043185 | 0,042526 |
| PG | 360 | 0,263534 | 0,261267 |
| PY | 360 | 0,131945 | 0,137415 |
| PYH | 360 | 0,069198 | 0,075091 |

Phép chia 15 khoảng và công thức ECE giữ như mục 6. Tại PG, dự báo trung bình thấp hơn tỷ lệ đúng. Tại PY và PYH, dự báo cao hơn tỷ lệ đúng. Sai lệch gộp khoảng 4,3 điểm phần trăm có thể đi cùng sai lệch khoảng 26 điểm phần trăm tại PG. Hiện tượng gộp nhóm che sai lệch vì vậy còn xuất hiện ở phép đọc ba câu tham chiếu khi hai cấu hình nhận chung dòng dữ liệu.

Hai cấu hình trong bảng là đủ cạnh và cạnh rỗng bên trong cùng graph package. Nhận đủ cạnh cho ECE thấp hơn ở PY/PYH và cao hơn ở PG. Theo ba khối seed đã dùng lại, ECE của đủ cạnh thấp hơn cạnh rỗng ở khối 20000, cao hơn ở 20001 và 20002. Hướng chênh lệch cần được giữ đầy đủ khi diễn giải kết quả.

Ở vùng điểm trên ngưỡng raw tham chiếu, hai cấu hình lần lượt có 195 và 217 tình huống. Chúng có thể gồm những tình huống khác nhau vì chính điểm dự báo quyết định membership của từng vùng. So sánh trong vùng này cần ghi đúng tập điều kiện của mỗi cấu hình. Ngưỡng raw giữ nguyên 0,5637150147511514, chưa được fit lại từ dữ liệu này.

Đã đối chiếu đủ 32 bảng nhóm, 480 khoảng và 64 vùng ngưỡng bằng phép tính Decimal độc lập. Các bảng nhóm dùng lại cùng chín lịch sử và ba khối ngẫu nhiên. Việc bổ sung cách tổng hợp không tạo thêm mẫu độc lập. Bước tiếp theo là kiểm độ đúng của quyết định thành thạo và hiệu chỉnh trên dữ liệu tách riêng. [E5]

## 8. Xác định điều kiện mà controller bảo đảm không quay lại chương

Paper1 đã tách đồ thị xác định tính khả thi với chính sách quyết định bài nào được chọn. Để giải thích thêm kết quả zero re-entry, nghiên cứu xét trực tiếp các quy tắc ready, cập nhật Elo và giữ chương của PDF bản nộp. Đây là một phân tích cấu trúc có giả thiết rõ ràng. [E6]

Xét đồ thị hữu hạn không chu trình, mọi cạnh nằm trong chương, chỉ khái niệm được chọn được cập nhật, không có quên, reset hoặc thay đồ thị giữa lượt. Ready chỉ chứa khái niệm chưa đạt ngưỡng có mọi tiên quyết đã đạt. Controller giữ chương hiện tại nếu chương đó còn ready.

Khái niệm đã đạt ngưỡng bị loại khỏi ready nên điểm của nó được giữ nguyên. Tập đã đạt ngưỡng vì thế chỉ giữ nguyên hoặc tăng, kể cả khi đáp án sai làm giảm điểm của một khái niệm chưa đạt. Nếu một chương còn khái niệm chưa đạt, đồ thị cảm sinh của chúng có một source. Mọi parent của source đã đạt ngưỡng, nên chương còn khái niệm ready. Controller chỉ rời chương sau khi hoàn tất chương đó. Sau lúc rời, chương không mở lại. Suy ra mỗi chương có tối đa một khối liên tiếp và số lần quay lại bằng 0 dưới các giả thiết này.

Điều kiện trên áp dụng cho dạng B1 với các cạnh nội chương. Một lượt hết ngân sách trong chương đầu vẫn thỏa kết luận. Do đó, khi đọc chỉ tiêu zero re-entry cần đặt nó cạnh quy tắc controller và topology. Kết quả học cần được đối chiếu thêm với trạng thái kiến thức thật và kết quả cuối.

Để xác định ranh giới của lập luận, dựng hai khái niệm a1, a2 thuộc A và một khái niệm b thuộc B, chỉ có cạnh b→a2. Điểm đầu a1=1248, b=1249, a2=1200. Lần đầu chọn a1 vì điểm thấp hơn b. Đáp án đúng đưa a1 qua ngưỡng, còn a2 bị b chặn nên controller sang B. Đáp án đúng ở b mở a2, controller trở lại A. Chuỗi A→B→A được tạo dù mọi lựa chọn tuân thủ continuity và đồ thị giữa chương chỉ có B→A, không chu trình.

Bốn kiểm dựng tay đã đạt qua controller được cài theo PDF. Chúng gồm đồ thị nội chương có nhiều nhánh và đáp án sai, parent ngoại chương đã đạt trước entry, phản ví dụ một cạnh liên chương và đối chứng selector global lowest-Elo nhỏ. Chứng minh cung cấp kết luận với toàn bộ chuỗi đáp án dưới giả thiết đã nêu, còn các kiểm dựng tay xác nhận những trường hợp cụ thể của implementation. Tần suất trên đồ thị liên chương, các hồ sơ người học và ngân sách nghiên cứu vẫn cần được đo. [E6]


## 9. Kết luận có thể bảo vệ và phần nghiên cứu còn thiếu

Ba kết quả về trạng thái và preview bổ sung một lời giải thích có thể truy vết cho RQ1: khác biệt trạng thái có thể bị điều kiện phân loại còn lại giữ lại; khác biệt tập ứng viên có thể mất sau lọc hoặc vẫn giữ cùng người thắng; và readout của câu đang hỏi không đại diện cho toàn bộ trạng thái mà bộ chọn sử dụng. Mỗi kết luận gắn với phép đối chiếu từng snapshot và quy tắc nguồn cụ thể. Phát hiện thứ tư bổ sung rằng response reliability cần được đọc theo nhóm và theo served population, vì phép gộp signed gaps trước trị tuyệt đối có thể đảo thứ hạng descriptive của ECE.

Phần này chưa chứng minh graph có lợi, trung tính hoặc có hại về kết quả học tập; chưa đo đúng/sai của mastery bằng latent truth; chưa tách nhân quả mọi pathway của graph package. Phân rã reliability trên cache mới bổ sung bằng chứng mô tả cho correctness, còn kiểm tra calibration trên mô hình fitted, các đối chứng simulator có kiểm soát và đánh giá closed-loop vẫn là các phần còn lại của kế hoạch RQ1–RQ3. Bằng chứng phần mềm của AKT/CG-AKT không được dùng thay kết quả nghiên cứu đó.

Phép kiểm trên cùng dòng dữ liệu ở mục 7 thu hẹp giới hạn về quần thể câu hỏi của phân tích reliability trước đó. Phân tích cấu trúc ở mục 8 xác định điều kiện controller tự bảo đảm kết quả không quay lại chương. Hai phần bổ sung giữ riêng vai trò của xác suất, quyết định, đường đi và trạng thái thật khi diễn giải RQ1.

### Nguồn dùng trong bản thảo

- **E1:** [phân tích trạng thái và hai điều kiện mastery](rq1_native_mastery_reference_diagnostic_20261109.md); [bundle trace gốc](../runs/rq1-prediction-mastery-trace-20261109-01/README.md), có raw traces, parity, summary và đối chiếu boolean độc lập.
- **E2:** [tái dựng C/B và khóa chọn CID](rq1_fixed_controller_candidates_20261109.md); [bundle kết quả và failure lịch sử](../runs/rq1-fixed-controller-candidates-20261109-01/README.md).
- **E3:** [phép ghép Query-M/tiêu chí tham chiếu/CID](rq1_query_decision_overlap_20261109.md); [bundle đủ 1.080 cặp và kiểm chéo](../runs/rq1-query-decision-overlap-20261109-01/README.md).

- **E4:** [response reliability và bù trừ sai lệch theo hồ sơ](rq1_response_reliability_diagnostic_20261109.md); [bundle đã đóng với bins, synthesis và receipts](../runs/rq1-response-reliability-diagnostic-20261109-01/README.md).

- **E5:** [raw reference-mixture trên dòng dữ liệu chung](rq1_reference_mixture_reliability_20261109.md); [bundle có kiểm số học độc lập](../runs/rq1-reference-mixture-reliability-20261109-01/README.md).
- **E6:** [chứng minh cơ chế chương và phản ví dụ](paper1_reentry_mechanism_20261109.md); [bốn tình huống đã kiểm](../runs/paper1-reentry-mechanism-20261109-01/README.md).

Các nguồn trên gồm chẩn đoán phát triển từ implementation kế thừa và phân tích cấu trúc theo PDF, không thay thế PDF của hai paper hoặc đề cương đã duyệt. Bản thảo giữ riêng bằng chứng quan sát, giải thích cơ học theo nguồn và các kết luận thực nghiệm chưa có.

## 10. Bổ sung E7 về nơi bất đồng thành thạo được giữ lại trước bước chọn bài

### Vì sao cần kiểm riêng bước dựng tập sẵn sàng?

Mục4 đã ghi nhận30 snapshot mà hai cấu hình có tập thành thạo khác nhau nhưng vẫn giữ cùng tập sẵn sàng R, cùng các tập ứng viên sau đó và cùng khái niệm thắng. Để giải thích rõ hơn quan sát này, nghiên cứu kiểm từng điều kiện cấu thành R. Đây là phân tích tiếp trên cùng chín lịch sử, không tạo một thí nghiệm mô phỏng hoặc dòng phản hồi mới. [E7]

Đối chiếu giữ1.080 cặp thời điểm của ba seed20000–20002 và ba hồ sơ PG/PY/PYH, mỗi lịch sử120 bước. Mỗi cặp có trạng thái pre-update của28 khái niệm, tương ứng30.240 cặp khái niệm–thời điểm. Hai cấu hình Graph-GAM-KT nhận lần lượt31 và0 cạnh ở bộ ước lượng, đồng thời giữ cùng controller với31 cạnh. Empty vẫn nằm trong cùng graph package. Phép so này không thay bằng đối chứng graph-free hoặc thí nghiệm tách riêng từng pathway.

R là tập sẵn sàng ban đầu trước các bước lọc, cân bằng và mở rộng ứng viên C/B đã mô tả ở mục4. Nhánh escape của nguồn có thể đưa khái niệm ngoài R vào ứng viên tiếp theo. Vì vậy, bị loại khỏi R chưa có nghĩa bị cấm ở mọi bước chọn sau hoặc chưa từng được phục vụ.

### Tách điều kiện của chính khái niệm và điều kiện của tiên quyết

Tại cùng snapshot, nguồn đưa khái niệm c vào frontier khi c chưa được đánh dấu thành thạo và mọi tiên quyết của c đều đã thành thạo hoặc được luyện ít nhất6 lần. Gọi I(c) là điều kiện chưa thành thạo, E(p) là điều kiện tiên quyết p đã thành thạo hoặc đủ6 lần luyện, A(c) là phép AND của mọi E(p), thì frontier F(c)=I(c) AND A(c). Với khái niệm không có parent, A bằng true. Phân tích vẫn giữ riêng fallback của nguồn khi frontier rỗng. Trong toàn bộ cohort được đối chiếu, cả hai nhánh đều đang ở nhánh frontier. [E7]

Có90 thời điểm mà hai cấu hình bất đồng native M tại đúng một khái niệm. R khác nhau ở60 thời điểm và giống nhau ở30 thời điểm. Đây là90 so sánh giữa cấu hình tại cùng thời điểm, không phải90 lần một người học vượt ngưỡng theo thời gian.

Trong cả90 so sánh, A của chính khái niệm mang nhãn khác nhau đều false ở cả hai cấu hình. Bất đồng I của nó vì vậy đi cùng F=false ở cả hai. Đường còn lại cần kiểm là các khái niệm nhận nó làm tiên quyết. Cùng một parent có thể tác động vào nhiều child tại cùng snapshot, nên148 parent→child opportunities có bất đồng parent M được giữ như một đơn vị riêng. Không quy chúng thành148 thời điểm hoặc cộng trực tiếp với90 so sánh M-set.

### Phân loại đủ30 thời điểm có cùng R

Tính lại trực tiếp từ18 trace trạng thái gốc cho phân loại sau. Cả30 thời điểm thuộc hồ sơ PG. Đây là các trạng thái lặp lại trong chín lịch sử đã có, không phải30 người học mới. [E7]

| Điều kiện tại snapshot có M khác nhau nhưng R giống nhau | Số thời điểm |
|---|---:|
| Khái niệm mang nhãn khác nhau không có child trực tiếp trong controller graph | 18 |
| Child liên quan đã thành thạo ở cả hai cấu hình, parent chưa đủ6 lần luyện | 8 |
| Child liên quan đã thành thạo ở cả hai cấu hình, đồng thời parent đủ6 lần luyện | 4 |
| Tổng | 30 |

Ở18 thời điểm đầu, khác biệt không có child trực tiếp để đi tiếp qua điều kiện tiên quyết. Chính khái niệm đó đã bị A=false giữ ngoài R. Ở12 thời điểm còn lại, child liên quan có I=false vì đã thành thạo ở cả hai cấu hình, nên nó cũng nằm ngoài R ở bước này.

Trong12 thời điểm có child đã thành thạo,4 thời điểm còn đồng thời thỏa ngoại lệ đủ6 lần luyện ở parent. Khi đó E của parent bằng true ở cả hai cấu hình dù M của parent khác nhau. Hai điều kiện cùng hiện diện. Phân loại ghi8 và4 để bộc lộ phần chồng lấp, không quy4 thời điểm cho exposure như một nguyên nhân độc lập duy nhất.

Kết quả bổ sung định vị được hai bước của phép dựng R trong những snapshot này. Bất đồng ở chính khái niệm chưa làm nó đủ tiên quyết để vào frontier, còn đường qua child bị giới hạn bởi topology hoặc điều kiện của child. Đó là lời giải thích Boolean theo implementation và trạng thái đã lưu. Nó không phải phép can thiệp thay từng điều kiện trong khi giữ mọi điều kiện khác cố định, cũng không phải ước lượng trung gian nhân quả.

### Phạm vi kết luận của E7

Đã kiểm đầy đủ SHA và CRC của18 trace,2.160 snapshot hai nhánh, cùng query/P/preview/legacy identity và trạng thái28 khái niệm. Lịch sử visits, recent và chapter chỉ được dựng từ logged-query prefix. Các R/C/B/CID và khóa chọn của nguồn được đối chiếu trước khi nghiệm thu thống kê. Mười sáu nhóm pooled/hồ sơ/seed/quỹ đạo và toàn bộ ô0 được giữ trong outputs. Bản đếm lại độc lập xác nhận phân loại30 thời điểm và phần giao4 thời điểm. [E7]

Phần mới giải thích bước dựng R trước quyết định thử. Nó không tự chứng minh preview hoặc bài thực phục vụ giữ nguyên vì riêng các điều kiện trên. Phân tích không đánh giá native M có đúng với trạng thái kiến thức thật, không coi pi_task là xác suất thành thạo đã hiệu chuẩn và không kết luận đồ thị cải thiện hay không cải thiện học tập. Không thêm seed độc lập, CI hoặc p-value. Các profile và lịch sử cũ tiếp tục được giữ đúng phạm vi của chúng.

### Nguồn bổ sung E7

**E7** dùng summary, event flags và validation của phép cached mastery–readiness đã nghiệm thu, cùng bản tính lại độc lập từ18 native traces. Source map đi kèm ghi40 input SHA của phép tính lại, nguồn analyzer/controller và các JSON pointers của từng số đếm. Bằng chứng E7 đã được đóng trong [bundle masking](../runs/rq1-mastery-ready-masking-20261109-01/README.md). Có thể đối chiếu [báo cáo chuyên đề](rq1_mastery_ready_masking_20261109.md) và [bản đếm lại độc lập](../runs/rq1-mastery-ready-masking-20261109-01/masking_independent_native_recount02.json). Manifest hoàn tất và SHA của các file này được ghi trong source map. Các mục1–9 và toàn bộ nguồn E1–E6 phía trên giữ nguyên byte so với bản canonical trước khi nối E7.


## 11. Bổ sung E8 về trường hợp đồ thị đổi đường đi nhưng giữ kết quả cuối

### Từ cùng 172 lượt đến câu hỏi về cấu trúc bộ mô phỏng

Phần 8 đã xác định điều kiện mà controller tự bảo đảm không quay lại chương. Cần kiểm tiếp liệu sự bằng nhau về số lượt và trạng thái cuối, khi hai đồ thị cho đường đi khác nhau, có thể suy ra từ phương trình đang dùng hay phải đo lại trên từng nhóm người học.

Một lượt kiểm tích hợp Paper1 đã lưu cung cấp tình huống cụ thể. Trên cùng một hồ sơ US với seed 42 và cùng profile/tape phản hồi, B1 và GA đều dừng sau 172 phản hồi với 28/28 khái niệm được controller đánh dấu thành thạo. B1 không quay lại chương, còn GA quay lại 2 lần. Latent cuối của từng khái niệm có cùng identity giữa hai nhánh. Đây là một witness engineering của phiên bản prospective, không phải kết quả matrix hoặc khôi phục random draws lịch sử của PDF. Hai nhánh cũng khác cả các cạnh bổ sung và traversal order, nên quan sát này chưa tách riêng cross-edge effect. [E8a]

### Mệnh đề có điều kiện về quỹ đạo của từng khái niệm

Trong source Paper1 đang xét, graph và chapter continuity quyết định khái niệm nào được chọn. Khi khái niệm đã được chọn, item gần estimate nhất được lấy theo estimate và số lần dùng item của chính khái niệm đó. Controller chỉ cập nhật estimate của khái niệm vừa hỏi. Hệ số K phụ thuộc số lượt đã luyện khái niệm ấy. World cũng chỉ đổi latent của khái niệm vừa hỏi, theo quy tắc tăng 12 và cap 1500. Đáp án được sinh từ latent của khái niệm và difficulty item, không từ việc khái niệm khác vừa được học. [E8b]

Giữ cùng bank, trạng thái ban đầu, item tie rule và tape phản hồi theo cặp **khái niệm–số lượt luyện cục bộ**. Không thêm forgetting, thời gian chờ, transfer hoặc cập nhật xuyên khái niệm. Cho phép DAG và thứ tự duyệt khác nhau. Khi đó, tại lần luyện thứ n của một khái niệm, hai nhánh có cùng item, xác suất, đáp án và local state trước/sau. Lập luận đi theo quy nạp. State ban đầu giống nhau. Cùng local state xác định cùng item. Cùng item và uniform cục bộ xác định cùng đáp án và update, nên local state kế tiếp tiếp tục giống nhau.

Nếu cả hai nhánh hoàn thành mọi khái niệm, mỗi khái niệm dừng tại cùng lần đầu estimate đạt 1250. Gọi số lần đó là N_c, bằng 0 nếu đã đạt từ đầu. Khái niệm đạt ngưỡng bị loại khỏi ready và không được cập nhật tiếp. Do đó, tổng số phản hồi của mỗi nhánh bằng Σ_c N_c, và terminal estimate, latent, local item exposures giống nhau. Global interleaving, chapter switches và re-entry vẫn có thể khác. Với finite DAG, ready rỗng tương đương mọi khái niệm đã đạt ngưỡng dưới các quy tắc này. Mệnh đề không giả định mọi tape/horizon đều đủ để hoàn thành. [E8b]

Sự bằng nhau ở witness 172 lượt vì vậy phù hợp với một hệ quả cấu trúc có điều kiện. Thứ tự và re-entry có thể đổi trong khi các quỹ đạo cục bộ hoàn tất vẫn được bảo toàn.

### Finite horizon và cap xác định ranh giới của kết luận

Sáu fixture xác định đã kiểm qua public core, gồm hai DAG complete có đường A→B và A→B→A, trường hợp có đáp án sai, history dài đi qua các mức K và đổi difficulty, cùng các đối chứng finite horizon. Cặp complete giữ exact local prefixes, stopping counts, exposures và final states dù thứ tự khác. Các fixture finite horizon giữ local prefixes chung nhưng có allocation và final states khác khi dừng trước completion. [E8c]

Một phản ví dụ dựng tay dùng hai khái niệm có latent đầu 1498 và 1200, cùng một phản hồi. Nhánh hỏi khái niệm đầu chỉ tăng 2 vì chạm cap. Nhánh bị prerequisite chặn khái niệm đó và hỏi khái niệm còn lại tăng 12. Đây là **tổng latent gain** của fixture, không phải mean mastery, phần trăm học tập hoặc kết quả trên học sinh thật. Nó cho thấy allocation tại finite horizon cùng cap có thể làm endpoint khác nhau. [E8c]

Đối chứng bổ sung kiểm trường hợp không update nào bị cap. Dù allocation và số đáp án đúng khác nhau, mỗi phản hồi vẫn tăng latent đúng 12, nên cùng N phản hồi cho cùng tổng net gain 12N. Như vậy, finite horizon riêng lẻ chưa đủ để suy ra khác biệt tổng gain. Cap cũng không phá mệnh đề complete nếu mỗi khái niệm vẫn nhận cùng N_c. Đây là hai ranh giới khác nhau của cùng implementation.

Sáu fixture mới nằm trong lượt 91 tests đã đạt, gồm cả 85 hồi quy trước đó. Các con số này là đơn vị kiểm implementation, không phải người học hoặc replicate nghiên cứu. Trần 13 episode calls/464 feedback suy từ horizon của fixture không được đổi thành measured interaction ledger. Việc nối E8 không chạy thêm mô hình, sinh đáp án hay tăng cỡ mẫu độc lập. [E8c]

### Phạm vi đóng góp cho RQ1 và RQ2

E8 bổ sung một lời giải thích cho khoảng cách giữa thay đổi lựa chọn và thay đổi kết quả cuối. Trong một simulator có cập nhật độc lập theo khái niệm và được học đến cùng local stopping rule, graph có thể chỉ đổi interleaving. Số lượt hoặc terminal gain bằng nhau trong phạm vi đó không tự đo chất lượng dự báo, độ đúng của mastery hoặc hiệu quả của graph ở môi trường có dynamics khác.

Coupling theo concept/local count là lựa chọn prospective đã được khai báo. Đổi sang tape gắn global step có thể làm responses khác pathwise khi thứ tự đổi, nhưng chưa tự chứng minh marginal-distribution effect nếu transition law và iid noise giữ nguyên. Các world có prerequisite-dependent learning, forgetting/spacing, cross-concept transfer hoặc finite-budget allocation cần được kiểm riêng. Không thêm các cơ chế đó chỉ để tạo effect, không suy Paper1 PDF mâu thuẫn, và không quy các kết luận này sang Paper2 hoặc người học thật. [E8b]

Phần này thu hẹp cách diễn giải một equality đã quan sát. Nó chưa trả lời toàn bộ graph-quality×ability matrix, chưa là kết quả fitted CG-AKT và chưa hoàn tất RQ1/RQ2.

### Nguồn bổ sung E8

- **E8a** dùng [witness domain28](paper1_seeded_domain_smoke_readiness_20261109.md) và [result của hai episode đã lưu](../runs/paper1-seeded-domain-smoke-engineering-20261109-01/scientific__result.json).
- **E8b** dùng [chứng minh điều kiện](paper1_concept_local_invariance_20261109.md), [source primitives đã đóng](../runs/paper1-pdf-primitives-engineering-20261109-01/simulator.py), [supplied episode](../runs/paper1-supplied-episode-engineering-20261109-01/episode.py) và [recipe coupling](../runs/paper1-seeded-episode-engineering-20261109-01/seeded_episode.py).
- **E8c** dùng [sáu fixture đã chạy](../runs/paper1-concept-local-invariance-20261109-01/test_concept_local_invariance.py) và [receipt91tests](../runs/paper1-concept-local-invariance-20261109-01/result.json). Source map phân biệt JSON pointers của measurements, expected values trong assertion đã đạt và các lập luận có điều kiện từ source.


## 12. Bổ sung E9 về nguồn đồ thị và điều kiện năng lực trong world Paper2

### Từ cơ chế của controller đến kết quả học trong simulator

E7 xác định những điều kiện có thể giữ bất đồng thành thạo ngoài tập sẵn sàng. E8 chỉ ra một trường hợp mà graph đổi thứ tự học nhưng vẫn giữ kết quả cuối do cấu trúc cập nhật cục bộ của world Paper1. Câu hỏi tiếp theo là khi world có learning dynamics phụ thuộc trạng thái và mức thiếu tiên quyết, đổi nguồn graph của bộ ước lượng có làm endpoint thay đổi theo cùng một chiều hay không.

Phép kiểm mới dùng world Paper2, giữ graph chuyên gia của môi trường G_env và controller G_controller, mỗi graph31cạnh. G_estimator đổi từ expert31 sang learned31 đã được học trên48 learners TRAIN rồi giữ cố định. Cùng một GAM variant vẫn bật signal và parent adaptation, tắt local adaptation. Điểm confidence của learned edges không được dùng làm trọng số GAM. Thiết kế giữ số cạnh bằng nhau nhưng chưa xác lập một graph là đúng hoặc chất lượng cao hơn graph kia. [E9a]

### Thiết kế ghép hữu hạn và giả thiết về trạng thái đầu

Ba blocks21000–21002 được dùng lại với cùng residual vector năng lực và cùng cặp uniforms cho response/learning theo step. Mỗi residual được đặt quanh scalar ability1000,1150 hoặc1300. Các mức này thuộc thiết kế world, khác các persona PG/PY/PYH trong những pilot trước. World prerequisite strength nhận λ=0 hoặc0,55. Mỗi trajectory có120phản hồi theo cùng lịch kết thúc ở ngày41. Outcome Y là trung bình trên28khái niệm của latent theta cuối trừ latent ban đầu, đơn vị theta/Elo points. [E9a]

Có18worlds learned mới và một expert sentinel, tổng19worlds với2.280native online policy updates. Đối chứng expert gồm18outcomes đã có trong study controlled-ability trước, không chạy lại. Sentinel tái hiện cell expert ở block21000, ability1150, λ0,55. Toàn120observable rows,120oracle rows và endpoint/state phải khớp exact trước khi chạy learned cells. Việc dùng lại ba seed blocks không bổ sung seed family độc lập. [E9a, E9b]

Study cũ có assertion về cùng nonedge initial policy state và theta ban đầu1200, nhưng không lưu raw initial-policy hash. Vì vậy, phép ghép dựa trên giả thiết initial state được tái dựng từ nguồn đã ghim, cùng sentinel exact. Hash của19initial states mới được lưu riêng, không điền ngược vào trường lịch sử còn thiếu. Một sentinel không chứng minh tương đương cho mọi arm, runtime hoặc phần cứng. Các contrasts dưới đây giữ điều kiện provenance này. [E9b]

### Khoảng cách giữa hai nguồn graph không có một dấu chung

Đặt Q_b(a,λ)=Y_expert−Y_learned tại block b và ability a. Q dương nghĩa net latent gain của expert cao hơn trong cell ấy. Đặt K_b(a)=Q_b(a,0,55)−Q_b(a,0), là thay đổi của khoảng cách graph-source khi đổi world prerequisite penalty. Đây là contrasts potential outcomes hữu hạn trong world và coupling đã quy định. Không dùng K làm human difference-in-differences hoặc causal mediation. [E9c]

| Ability | Block | Q tại λ0 | Q tại λ0,55 | K |
|---|---|---:|---:|---:|
|1000|21000|−0,055965|−0,073775|−0,017810|
|1000|21001|−0,022627|−0,038715|−0,016087|
|1000|21002|+0,056961|+0,086262|+0,029300|
|1150|21000|−0,743541|−0,778692|−0,035150|
|1150|21001|+0,333994|+0,295720|−0,038274|
|1150|21002|−0,620649|−0,656658|−0,036009|
|1300|21000|−0,197266|−0,197266|0|
|1300|21001|+0,181461|+0,181461|0|
|1300|21002|+0,076440|+0,076440|0|

Bảng giữ đủ18components và9contrasts, làm tròn6chữ số, cùng đơn vị theta/Elo points. Q âm là expert có net gain thấp hơn learned trong phép so ấy, chưa có nghĩa kiến thức giảm dưới baseline. Ở1000 và1150, expert thấp hơn trong hai blocks và cao hơn ở block còn lại. Ở1300, expert thấp hơn một block và cao hơn hai. K1150 âm trong cả ba blocks, còn K1000 có hai âm và một dương. Dấu và độ lớn hữu hạn này chưa cho phép xếp hạng graph nguồn nào tốt hơn nói chung hoặc xác lập ý nghĩa thực tiễn. [E9c]

Đối chứng ability1300 làm rõ một giới hạn đặc biệt. Hai λ có semantic trace và endpoint giống exact trong từng block vì prerequisite deficit bằng0 theo thiết kế. Ba K1300 do đó bằng0 là kết quả phù hợp negative control đã biết trước. Tuy vậy, ba Q1300 đều khác0 và mang cả hai dấu. Khác biệt nguồn graph vẫn có thể đi cùng endpoint khác khi world penalty này không hoạt động. Chưa thể quy toàn bộ graph-source advantage cho cơ chế thiếu tiên quyết, cũng chưa tách riêng signal, parent adaptation, chọn bài hoặc challenge/response dynamics. [E9c]

### Đường đi khác nhau chưa chỉ định một mediator

Trong cả18cặp expert–learned, có ít nhất một câu hỏi được chọn khác nhau. Tổng1.409/2.160vị trí ordinal khác question ID. Mẫu số này là18cặp trajectory×120steps, không phải2.160independent observations. Đáp án trước lần phân kỳ câu hỏi đầu tiên vẫn trùng trong từng cặp. Sau đó, cùng ordinal step có thể thuộc query và history khác, nên không dùng các vị trí ấy để tính paired response loss hoặc giải thích matched-query probability changes. [E9d]

E9 bổ sung một bước giữa câu hỏi cơ học của RQ1 và kiểm tra endpoint của RQ2. Đổi nguồn graph có thể đổi đường đi và net latent endpoint, nhưng chiều endpoint phụ thuộc block và world condition. Dữ liệu này chưa xác định việc đổi native mastery, readiness hay một rank score nào đã trung gian hóa effect. Nó cũng chưa đánh giá mastery accuracy hoặc response calibration. Các analyses E1–E7 và contrasts E9 vì vậy cần được đọc theo đúng population và intervention của từng phần.

### Những điều còn chưa biết

Kết quả chỉ dùng một learned graph, một native GAM variant và ba blocks đã có. Graph học có thể phản ánh support hoặc logged order của corpus TRAIN, chưa là recovery của prerequisite truth. Confidence không phải xác suất edge đúng. Same-step uniforms là coupling đã khai báo, còn ability là scalar cộng residual trong simulator, chưa đại diện cho nguyên nhân năng lực ở người học thật.

Cần tiếp tục kiểm các graph conditions và worlds độc lập theo thiết kế đã freeze, đánh giá calibrated controller cùng neural comparators bắt buộc, và giữ nguồn gốc mọi state/role. Pilot này không thay main matrix hai environments hoặc fitted AKT/SAKT/GKT/CG-AKT results. Việc viết E9 không sinh thêm world, model fit, CI hoặc p-value, và chưa hoàn tất RQ1/RQ2/RQ3.

### Nguồn bổ sung E9

- **E9a** dùng plan, admission, summary và worker receipt của pilot learned19, cùng [báo cáo chuyên đề đã lưu trong bundle](../runs/rq2-learned-graph-ability-20261109-01/report_draft.md).
- **E9b** dùng sentinel, initial-state scope và [bản kiểm độc lập trong bundle](../runs/rq2-learned-graph-ability-20261109-01/independent_verification.json).
- **E9c** dùng đủ [18graph-source components](../runs/rq2-learned-graph-ability-20261109-01/native__graph_source_contrasts.json), [9conditional contrasts](../runs/rq2-learned-graph-ability-20261109-01/native__conditional_lambda_contrasts.json) và high controls.
- **E9d** dùng đủ18trajectory joins trong independent verification, source chronology và raw-output hashes. Source map ghi phép cộng18question-ID counts cho1.409/2.160, không tạo thêm phép chạy hoặc metric population mới.

Pilot E9 đã đóng bằng chứng trong [bundle learned19](../runs/rq2-learned-graph-ability-20261109-01/README.md). Manifest và SHA của sources được ghi trong source map. Root đã đối chiếu 18 nguồn cùng 66 giá trị theo đường dẫn JSON và hai phép cộng từ dữ liệu đã lưu trước xuất bản. Các mục 1–11 cùng toàn bộ nguồn E1–E8 được giữ nguyên.


## 13. Bổ sung E10 về trạng thái thành thạo tại các câu được chọn

### Vì sao cần đối chiếu quyết định với trạng thái mô phỏng

Paper2 đã đặt dự báo đáp án vào một hệ thống chọn bài. Để giải thích vì sao thay đổi dự báo có thể chưa dẫn đến thay đổi kết quả học, cần biết quyết định thành thạo có phản ánh trạng thái mà simulator đang mô phỏng hay không. Câu hỏi này bổ sung cho việc đo sai số dự báo. Dự báo đáp án và trạng thái thành thạo là hai đại lượng phục vụ hai bước khác nhau của cùng hệ thống.

Nhóm đối chiếu lại một lịch sử PG đã lưu, gồm120 lượt hỏi trước khi cập nhật bằng đáp án hiện tại. Lịch sử dùng seed21000, cơ chế phạt do thiếu tiên quyết trong world được tắt, tương ứng λ=0. Hai đường tín hiệu và điều chỉnh theo cha trong bộ ước lượng được tắt, điều chỉnh cục bộ cũng tắt. Bộ chọn bài vẫn dùng đồ thị tiên quyết. Vì vậy, cấu hình này chỉ tắt các đường đã nêu của bộ ước lượng. Các bản ghi được ghép theo đúng câu hỏi, khái niệm, thời điểm và giá trị dự báo với trạng thái thật đã lưu của simulator. Đây là phân tích dữ liệu cũ, không thêm người học hoặc lượt tương tác mới. [E10a]

### Kết quả đối chiếu và lý do cần đọc cùng cách lấy mẫu

Quy tắc Paper2 xét cả điểm kiến thức ước lượng đạt1250 và chỉ số bất định không vượt0,55. Phép đối chiếu dùng trạng thái latent của simulator tại cùng ngưỡng1250. Trong120 lượt hỏi được quan sát, khái niệm đang hỏi luôn đạt tiêu chí latent, trong khi điểm kiến thức ước lượng luôn dưới ngưỡng. Kết quả gồm120 quan sát trên22 khái niệm riêng biệt của một lịch sử. [E10a]

| Quyết định tại khái niệm được hỏi | Latent chưa đạt | Latent đã đạt |
|---|---:|---:|
| Mô hình chưa công nhận thành thạo | 0 | 120 |
| Mô hình công nhận thành thạo | 0 | 0 |

Điểm kiến thức ước lượng chưa đạt ở cả120 lượt nên điều kiện bất định chưa có cơ hội chặn thêm một trường hợp đã vượt ngưỡng điểm. Quan sát này chưa đo được vai trò tăng thêm của điều kiện bất định khi điểm kiến thức đã đạt. Nó cũng chưa đo ảnh hưởng của bất định đối với dự báo, cập nhật trạng thái hoặc cách xếp hạng ứng viên.

Bảng chỉ gồm những câu do hệ thống quyết định giao. Trong source Paper2, bộ chọn ưu tiên các khái niệm được đánh giá chưa thành thạo và ưu tiên điểm thành thạo thấp trong nhóm ứng viên. Do đó, quần thể được quan sát đã chịu ảnh hưởng của mô hình và chính sách. Bộ chọn còn có nhánh ôn tập cùng nhánh xử lý khi mọi khái niệm đã thành thạo, nên việc toàn bộ120 điểm ước lượng dưới ngưỡng vẫn là kết quả riêng của lịch sử này. Bảng chưa đánh giá trạng thái của toàn bộ28 khái niệm tại cùng những thời điểm. [E10b]

### Năng lực ban đầu giới hạn điều có thể kết luận về học tập

Kiểm lần xuất hiện đầu cho thấy cả22 khái niệm đã được phục vụ đều đạt tiêu chí latent ngay từ lần thực hành đầu tiên, trong khi điểm ước lượng khởi tạo bằng1200. Phân tích phương trình của phiên bản này cho thấy mức tăng latent không âm và forgetting kéo về mức nền ban đầu. Với các khái niệm có mức nền đã vượt ngưỡng, trạng thái tiếp tục nằm trên ngưỡng. Phát hiện về lần xuất hiện đầu là kiểm cơ chế hậu nghiệm trên lịch sử đã chọn. [E10c]

Vì vậy, lịch sử này chưa cung cấp một lần chuyển latent từ chưa đạt sang đạt tại các khái niệm đã được phục vụ. Khác biệt giữa quyết định và latent cần được đọc cùng khởi tạo năng lực cao và cách chọn câu. Sáu khái niệm chưa xuất hiện cần bằng chứng riêng. Không gán kết quả của22 khái niệm này cho mọi hồ sơ PG, mọi seed hoặc toàn bộ28 khái niệm.

### Đóng góp chẩn đoán và phần thực nghiệm còn thiếu

E10 chỉ ra rằng đánh giá quyết định thành thạo cần kiểm soát cách chọn quần thể. Phép đánh giá chỉ lấy các câu hệ thống đang giao dễ tập trung vào những trạng thái mà chính mô hình đang coi là chưa đạt. Điều này có thể che khuất khả năng đánh giá những khái niệm khác và làm khó việc tách tác dụng của từng điều kiện trong quyết định.

Bước tiếp theo được đề xuất là đối chiếu một tập khái niệm và thời điểm định trước, độc lập với câu được chọn, đồng thời giữ cả trạng thái ước lượng và latent tương ứng. Thiết kế đó cần được chốt trong hợp đồng thực nghiệm trước khi dùng làm đánh giá chính. Trong phép đối chiếu quyết định thành thạo với latent này, so sánh giữa các đồ thị, hiệu chỉnh xác suất, trạng thái khởi đầu thấp hơn và đánh giá kết quả học trên nhiều người học vẫn còn thiếu. Các đối chứng nguồn đồ thị ở E9 có phạm vi riêng. Một lịch sử với120 thời điểm tương quan chưa hoàn tất RQ1 hoặc RQ2 và chưa chứng minh lợi ích của graph.

### Nguồn bổ sung E10

- **E10a** dùng [summary của witness](../runs/rq1-observer03-cached-truth-20261109-01/cached02_child__summary.json), [120 bản ghi đã ghép](../runs/rq1-observer03-cached-truth-20261109-01/cached02_child__joined120.json) và [kiểm độc lập](../runs/rq1-observer03-cached-truth-20261109-01/observer03_truth120_independent_crosscheck01.json).
- **E10b** dùng [review source và cách diễn giải mẫu](../runs/rq1-observer03-cached-truth-20261109-01/OBSERVER03_CACHED120_SELECTION_INTERPRETATION_REVIEW01.md), cùng [báo cáo chuyên đề](rq1_on_policy_mastery_witness_20261109.md).
- **E10c** dùng first_visit_analysis trong kiểm độc lập và phương trình source được truy vết trong review. Phép kiểm đã đọc đủ14.400 hàng cache và CRC trước khi lấy120 hàng. Không cộng120 lượt hỏi vào số mẫu độc lập.

Các mục trước E10 giữ nguyên byte. [Bundle viết E10](../runs/thesis-rq1-e10-writing-20261110-01/README.md) giữ before/after, kiểm các số liệu đã trích và nguồn bằng chứng. Việc viết không thực hiện thêm model/world call hoặc thay thiết kế thực nghiệm.


## 14. Bổ sung E11 về tái kiểm nguồn đồ thị trên mười khối mô phỏng mới

### Từ dấu hiệu ở ba khối đến một phép kiểm mới

E9 đã cho thấy đồ thị trong bộ ước lượng có thể đổi đường đi ngay cả khi cơ chế phạt thiếu tiên quyết của world không hoạt động. Ba khối cũ vẫn còn ít, dùng lại trạng thái đã lưu và có giới hạn về chứng minh trạng thái khởi đầu. Vì vậy, bước tiếp theo giữ cùng câu hỏi nhưng dùng mười khối khởi tạo mới đã định trước, đồng thời lưu trạng thái ban đầu thực tế của từng ca. Không chọn lại seed theo dấu của kết quả. [E11a]

Thiết kế gồm các block21010–21019. Mỗi block có ba mức khởi tạo1000,1150,1300, hai nguồn đồ thị trong bộ ước lượng và hai mức cơ chế phạt0/0,55. Đồ thị của môi trường và bộ chọn bài cùng giữ expert31. Chỉ đồ thị trong bộ ước lượng thay giữa expert31 và một learned31 đã có từ TRAIN. Hai đường tín hiệu và điều chỉnh theo cha cùng bật, điều chỉnh cục bộ tắt. Đây là mười block dùng một learned artifact cố định, chưa có mười đồ thị học độc lập. [E11a]

### Đại lượng được đối chiếu trả lời câu hỏi nào

Gọi Y là trung bình trên28 khái niệm của latent cuối trừ mức nền ban đầu. Trước hết lấy Y của expert trừ Y của learned tại cùng block, mức khởi tạo và mức cơ chế, được chênh lệch Q. Sau đó lấy Q khi bật cơ chế trừ Q khi tắt, được K. Phép trừ thứ hai giúp nhận diện sự tương tác giữa đổi nguồn đồ thị và cơ chế phạt trong chính simulator đang kiểm. Nó chưa tách riêng mọi mediator của đường đi. [E11b]

Không dùng nhóm năng lực cao làm một nhóm người học đối chứng giả định có parallel trends. Các mức khởi tạo là can thiệp được dựng trong mô phỏng. Các trạng thái và chuỗi uniform được ghép trong từng block. Diễn giải chính dựa vào các can thiệp đã kiểm soát và phương trình simulator. Thiết kế chưa cung cấp tác động nhân quả của prerequisite instruction trên người học thật.

| Mức khởi tạo | K trung bình | K nhỏ nhất đến lớn nhất | Block dương / âm / bằng0 |
|---|---:|---|---|
|1000|+0,004496|−0,069250 đến+0,095294|6 /4 /0|
|1150|+0,024530|−0,004716 đến+0,079790|8 /2 /0|
|1300|0|0 đến0|0 /0 /10|

Các giá trị dùng thang điểm latent Elo của world. Ở hai mức thấp hơn, K đổi dấu giữa các block. Trung bình dương cần được đọc cùng các trường hợp âm. Đây là thống kê mô tả, chưa có CI hoặc kiểm định xác lập ưu thế ổn định. Đơn vị độc lập được dự kiến là block, không phải120 world hoặc14.400 lần trả lời. [E11b]

### Đối chứng bất hoạt và thay đổi đường đi

Ở mức1300, K bằng0 ở cả mười block, phù hợp với20 cặp high-control đã khớp semantic trace và endpoint giữa hai mức cơ chế. Zero này là hành vi được dự kiến từ điều kiện bất hoạt của penalty. Nó chưa phải mười bằng chứng độc lập rằng mọi tác dụng của graph đều biến mất khi năng lực cao. Chênh lệch Q ở mức1300 vẫn khác0 tại cả20 điều kiện, có cả dấu dương lẫn âm. Như vậy, tác động của đổi nguồn đồ thị còn đi qua các đường ngoài riêng penalty. Phép kiểm hiện tại chưa phân rã signal, parent adaptation và challenge thành các tác động riêng. [E11c]

Cả60 cặp expert–learned có ít nhất một câu hỏi khác nhau, tổng cộng4936/7200 vị trí ordinal khác question ID. Nhãn trước lần phân kỳ đầu khớp trong từng cặp. Sau phân kỳ, cùng ordinal chưa bảo đảm cùng câu và cùng history. Vì vậy, các vị trí đó chưa là shared-target population để đối chiếu Log Loss của hai model. Thay đổi hành động đã được quan sát, còn chất lượng dự báo trên cùng dòng cần một phép kiểm riêng. [E11c]

### Điều được củng cố và điều cần giữ mở

Mười block mới duy trì chẩn đoán rằng khác biệt giữa đồ thị có thể tồn tại khi đường penalty bất hoạt. Dấu hiệu theo mức khởi tạo cũng cần kiểm lại. Chẳng hạn, K ở mức1150 có tám block dương và hai âm, còn cả ba block cũ của E9 đều âm. Sự khác nhau về dấu chưa là một kết luận đảo chiều có ý nghĩa thống kê. Hai tập block có population và bằng chứng initial state khác nhau, nên chưa pooling thành một mẫu13block. [E11d]

E11 bổ sung đối chứng có trạng thái khởi đầu được lưu thực và khả năng lặp lại trên các block mới. RQ1 vẫn cần đo chuỗi dự báo, hiệu chỉnh, quyết định và hành động trên quần thể phù hợp. RQ2 vẫn còn graph noise/quality conditions cùng thống kê theo block. RQ3 tiếp tục cần các biến thể neural đã huấn luyện, so sánh công bằng và closed-loop outcomes. Các kết quả mô tả hiện tại chưa hoàn tất một RQ.

### Nguồn bổ sung E11

- **E11a** dùng [acceptance recovery](../runs/rq2-fresh-graph-recovery-20261110-01/acceptance.json), public plan và initial-state hashes. Logical120/14.400 được tách khỏi physical121/14.430 có30lượt replay, giữ parent failure.
- **E11b** dùng [thống kê mô tả đã lưu](../runs/rq2-fresh-graph-source-analysis-20261110-01/descriptive_statistics.json), đủ60 Q và30 K đã kiểm số học. Công thức Y nằm trong source worker được đóng cùng recovery bundle.
- **E11c** dùng20highcontrols,60trajectory pairs và [review độc lập](../runs/rq2-fresh-graph-source-analysis-20261110-01/independent_review.md), có exact pointers để kiểm lại từng giá trị.
- **E11d** đối chiếu nguồn E9 đã nghiệm thu với [báo cáo fresh120](rq2_fresh_graph_source_replication_20261110.md). Việc viết E11 không thực hiện thêm tương tác hoặc tăng cỡ mẫu của bất kỳ phép kiểm nào.

[Bundle viết E11](../runs/thesis-rq2-e11-writing-20261110-01/README.md) giữ before/after và source map. Toàn bộ phần trước E11 được bảo toàn byte.


## 15. E12 — Bất định giữa các khối và giới hạn của so sánh năng lực

Phần E11 cho thấy trung bình của tương tác nguồn đồ thị với cơ chế phạt có thể khác nhau giữa hai mức khởi tạo. Câu hỏi tiếp theo là sự khác nhau ấy có đủ rõ so với biến động giữa các khối mô phỏng hay không. Đơn vị độc lập tiếp tục là mười khối21010–21019. Các120worlds và14.400tương tác bên trong không được xem là các quan sát độc lập. Ba khối E9 không được gộp vào phép tính mới.

Gọi K(a) là phần thay đổi của chênh lệch expert–learned khi bật cơ chế phạt tại mức khởi tạo a, với định nghĩa Y và Q giữ như E11. Phân tích bổ sung xét ba trung bình gồm K(1000), K(1150) và K(1150)−K(1000) được trừ trong cùng khối. Đại lượng thứ ba trả lời trực tiếp câu hỏi tác động có khác giữa hai mức khởi tạo hay không. Việc hai khoảng riêng lẻ có quan hệ khác nhau với0 chưa tự chứng minh chênh lệch giữa hai tác động.

Nhóm dùng paired-block bootstrap với10.000lần lấy mẫu lại mười khối có hoàn lại, private seed42. Các điều kiện trong cùng khối luôn đi cùng nhau. Ba khoảng percentile loại7 dùng điều chỉnh Bonferroni, mỗi khoảng có mức danh nghĩa98,333333%, tương ứng mức đồng thời danh nghĩa95% của gia đình ba so sánh. Đây là mức xấp xỉ của bootstrap, không bảo đảm bao phủ chính xác với n=10. Các estimands và thuật toán được đóng băng trước phép tính bổ sung, nhưng kết quả mô tả đã được xem trước, nên toàn bộ phân tích mang tính thăm dò sau kết quả.

| Đại lượng | Trung bình, Elo | Khoảng bootstrap đã điều chỉnh, Elo |
|---|---:|---|
| K(1000) | +0.004496 | -0.024649 đến +0.035327 |
| K(1150) | +0.024530 | +0.005767 đến +0.047248 |
| K(1150) − K(1000), trong cùng khối | +0.020034 | -0.021413 đến +0.058529 |

Khoảng của K(1000) chứa cả giá trị âm và dương. Khoảng của K(1150) nằm phía dương trong phép thăm dò này. Tuy nhiên, khoảng của hiệu K(1150)−K(1000) còn chứa0, nên dữ liệu hiện tại chưa phân biệt rõ tác động giữa hai mức khởi tạo. Kết quả không được diễn giải thành bằng chứng khẳng định đồ thị có ích hơn cho một nhóm năng lực của người học thật.

K(1300)=0 vẫn là đối chứng bất hoạt theo điều kiện của simulator. Nhóm không lập khoảng hoặc kiểm định cho đại lượng này. Đổi nguồn đồ thị vẫn tạo Q khác0 ở mức khởi tạo1300, như E11 đã ghi, nên không được dùng K bằng0 để suy mọi đường tác động của đồ thị đã biến mất.

Độ bất định đã được lượng hóa thêm trên đúng quần thể và giữ các kết quả âm. Tăng số lần bootstrap chỉ giảm nhiễu Monte Carlo, không tạo thêm khối độc lập. Khoảng hiện có chưa bao gồm biến động do nhiều đồ thị học độc lập, nhiều seed huấn luyện, môi trường khác hoặc người học thật. RQ2 còn cần khảo sát đồ thị nhiễu và khả năng khái quát. Phần này chưa đóng RQ2 và chưa là bằng chứng ưu thế của CG-AKT.

Các phép tính đã được kiểm độc lập từ30K và10.000vector đã lưu bằng số thập phân độ chính xác60chữ số. Không lấy mẫu lại hoặc chạy mô phỏng mới trong kiểm này. Sai khác lớn nhất do số thực nhỏ hơn1,14e−16, trong ngưỡng kiểm số1e−12 đã công bố. Ngưỡng này kiểm tái lập số học, không là biên hiệu quả nghiên cứu. Bảng làm tròn sáu chữ số thập phân, JSON giữ độ chính xác đầy đủ.

[Báo cáo kỹ thuật](rq2_fresh_block_uncertainty_20261110.md). [Bằng chứng và giới hạn](../runs/rq2-fresh-block-uncertainty-20261110-01/README.md).


## 16. E13 — Câu hỏi được chọn chưa đại diện cho trạng thái thành thạo toàn miền

### Từ witness câu hỏi đến bảng khái niệm và thời điểm cố định

E10 đã nêu giới hạn khi chỉ đối chiếu trạng thái của khái niệm đang được hỏi. Câu hỏi tiếp theo là phần còn lại của miền có chứa những trạng thái mà cách quan sát đó bỏ qua hay không. Phép kiểm bổ sung ghi đủ 28 khái niệm trước mỗi bước, rồi tách khái niệm của câu hỏi được chọn khỏi 27 khái niệm còn lại. Quần thể đánh giá vì vậy được mở rộng theo khái niệm tại cùng thời điểm, thay vì chỉ theo câu hệ thống đang giao. [E13a]

Ba lịch sử cùng block 21010 có mức khởi tạo latent 1000, 1150 và 1300. Cả ba giữ đồ thị đầy đủ, λ bằng 0, bật signal và parent adaptation, tắt local adaptation. F041 ở mức 1000 đã nghiệm thu và chỉ được tham chiếu. Hai ô F081 ở mức 1150 và F001 ở mức 1300 được cố định trước khi chạy các đối chứng mới. Các lịch sử có thể chọn câu khác nhau, nên không ghép cùng ordinal giữa các mức khởi tạo như thể đó là cùng history và câu hỏi. Ba lịch sử này cũng chưa tạo ba block độc lập. [E13a]

Native M dùng đúng điều kiện θ ước lượng ≥ 1250 và π_task lưu trong trạng thái ≤ 0,55. Bên đối chiếu dùng θ_at ≥ 1250 của simulator tại cùng khái niệm và thời điểm. Đây là criterion latent do phương trình simulator định nghĩa. Criterion này chưa là nhãn thành thạo người thật, xác suất trả lời đúng hoặc mastery đã hiệu chỉnh theo S04. [E13b]

### Kết quả toàn miền và phần bị bỏ ngoài câu hỏi

Mỗi lịch sử có 120 bước, tạo 3360 cặp khái niệm–thời điểm. Bảng toàn miền giữ cả trạng thái âm và dương. TP, FP, FN và TN là các ô đối chiếu native M với criterion latent ở trên, không phải số người học độc lập. [E13c]

| Mức khởi tạo | TP | FP | FN | TN |
|---|---:|---:|---:|---:|
| 1000 · F041 | 0 | 0 | 0 | 3360 |
| 1150 · F081 | 0 | 5 | 1 | 3354 |
| 1300 · F001 | 215 | 0 | 2808 | 337 |

Ở mức 1300, cả 215 cặp được native M nhận diện dương đúng đều nằm ngoài khái niệm của câu hỏi đang được chọn. Trong 120 cặp thuộc câu hỏi, native M luôn âm, gồm 117 FN và 3 TN. Bảng toàn miền cho thấy thêm các dương đúng, đồng thời vẫn giữ 2808 FN. Kết quả làm rõ sự khác nhau giữa hai quần thể quan sát và chưa xác nhận chất lượng phân loại chung. [E13c]

Ở mức 1150, cả 120 cặp thuộc câu hỏi đều là TN. Tuy nhiên, ngoài các câu hỏi ấy có 5 FP và 1 FN. Vì vậy, nếu chỉ trình bày hàng queried thì một bảng toàn âm dễ che mất các sai lệch ở khái niệm khác. Không diễn giải 120 TN thành bộ phân loại chính xác 100%. Ở mức 1000, cả 3360 cặp chỉ có lớp latent âm, giữ nguyên giới hạn của kết quả F041. [E13c]

### Tác dụng của cổng bất định còn chưa được phân biệt

Số cặp có θ ước lượng đạt ngưỡng lần lượt là 0, 5 và 215 tại ba mức khởi tạo. Trong tổng số 220 cơ hội này, không có cặp nào bị cổng π_task chặn. Quan sát 0/220 chỉ áp dụng cho ba lịch sử 120 bước, một block và cấu hình S1P1L0 đang kiểm. Chưa thể từ đó kết luận π luôn dư thừa hoặc không có tác dụng trong lịch sử khác. [E13d]

Recorder lấy lại 28 lời gọi is_mastered đầu tiên vốn có trong ready_set, không thêm getter hoặc thay phương trình policy. Cả 120 action, P và cập nhật cùng endpoint policy phải khớp lịch sử gốc trước khi đóng native panel và ghép latent. Phía latent dùng trạng thái ban đầu thực đã lưu và chuyển trạng thái theo phương trình nguồn, không tạo world, đáp án hoặc số ngẫu nhiên mới. Kiểm độc lập từ cache khớp 3360 phương trình latent, 120 fullvars SHA và endpoint 28 khái niệm cho mỗi ô mới. [E13b]

E13 bổ sung bằng chứng trực tiếp cho giới hạn chọn quần thể đánh giá ở RQ1. Bảng đủ miền tìm thấy các trạng thái mà bảng câu hỏi bỏ ngoài, nhưng chưa đo calibration hoặc giải thích nhân quả vì sao hệ thống chọn câu. Cũng chưa đối chiếu đồ thị, người học thật hay các trạng thái đạt ngưỡng bị π chặn. Quần thể này khác witness PG120 của E10 và được giữ riêng. RQ1, RQ2 và phép replay truth toàn bộ CPU09 vẫn còn các phần thực nghiệm chưa hoàn tất.

### Nguồn bổ sung E13

- **E13a** dùng [báo cáo tổng hợp ba lịch sử](rq1_fixed_time_ability_native_panels_20261110.md) và whitelist trước hai đối chứng trong [bundle F001](../runs/rq1-ability-native-panel-f001-20261110-01/rq1_ability_panel_case_whitelist02.json). F041 được giữ làm tham chiếu đã nghiệm thu.
- **E13b** dùng parity, lineage và kiểm độc lập trong [F001](../runs/rq1-ability-native-panel-f001-20261110-01/independent_cached_review.json), [F081](../runs/rq1-ability-native-panel-f081-20261110-01/independent_cached_review.json) cùng [F041](../runs/rq1-f041-native-panel-20261110-01/independent_cached_review.json). Hai scientific JSONL của mỗi ô giữ tại experiments theo inventory, không nhân đôi trong bundle.
- **E13c** dùng các nhóm all28, queried và not_queried trong [summary F001](../runs/rq1-ability-native-panel-f001-20261110-01/native__summary.json), [summary F081](../runs/rq1-ability-native-panel-f081-20261110-01/native__summary.json) và [summary F041](../runs/rq1-f041-native-panel-20261110-01/native__summary.json). Giữ đủ chín hàng trong bảng nguồn, kể cả ô bằng không.
- **E13d** dùng theta_gate_true và uncertainty_suppression của ba nhóm all28, cộng đúng các cơ hội đã quan sát. Không coi các cặp lặp theo thời gian là cỡ mẫu độc lập.

Phần E1–E12 được giữ nguyên 70408 byte. Việc viết E13 không thực hiện thêm model hoặc world call và không tăng số block độc lập.
