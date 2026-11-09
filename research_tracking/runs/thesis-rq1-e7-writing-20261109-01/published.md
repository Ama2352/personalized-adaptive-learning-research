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
