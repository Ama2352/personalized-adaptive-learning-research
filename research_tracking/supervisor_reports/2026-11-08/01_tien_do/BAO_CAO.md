# Báo cáo tiến độ khóa luận — 08/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương và Hồ Nguyễn Minh Sang.

## Từ hai nghiên cứu trước đến câu hỏi của khóa luận

Một hệ thống học tập thích ứng phải trả lời câu hỏi: **với những gì người học đã làm, nên giao bài nào tiếp theo?** Để trả lời, hệ thống cần ước lượng người học đang biết gì, xác định kiến thức nền cần có và chọn một hoạt động phù hợp. Đồ thị tiên quyết là bản mô tả những quan hệ kiến thức nền ấy. Tuy nhiên, có một bản đồ tốt chưa bảo đảm hệ thống sẽ chọn được bài tốt, cũng chưa bảo đảm người học sẽ học tốt hơn.

**Paper 1** đã làm rõ sự khác nhau giữa bản đồ kiến thức và cách chọn đường đi. Đồ thị giới hạn những nội dung được phép chọn, còn quy tắc lựa chọn quyết định nội dung thực sự xuất hiện tiếp theo. Nghiên cứu cho thấy ưu tiên học liên tục trong một chương giúp giảm chuyển chương và quay lại chương; nhưng đồ thị mở rộng chưa cải thiện ổn định mức thành thạo so với đồ thị nội chương. Kết quả này đặt ra vấn đề: một lộ trình liền mạch hơn có thể do cách chọn bài, chứ chưa phải bằng chứng các quan hệ tiên quyết bổ sung giúp học tốt hơn.

**Paper 2** đi tiếp vào mô hình ước lượng người học. Nghiên cứu trước hết cho các mô hình dự báo trên cùng luồng câu hỏi, sau đó kiểm tra kết quả khi từng mô hình được tích hợp vào hệ thống chọn bài. Thông tin đồ thị giúp dự báo nhỉnh hơn ở một số nhóm mô phỏng, nhưng chưa phát hiện cải thiện rõ ở các kết quả học tập chính sau hiệu chỉnh thống kê. Trên Junyi, bước chọn cấu hình theo dữ liệu phát triển lại ưu tiên phương án tắt thông tin đồ thị. Paper cũng đã thừa nhận rằng thành phần được bật/tắt còn gồm nhiều cơ chế ngoài riêng các cạnh tiên quyết.

Khóa luận kế thừa những kết quả này, không coi chúng là phát hiện mới. Theo đề cương, phần nghiên cứu tiếp nối phải giải thích **vì sao đồ thị chưa giúp ổn định, trong điều kiện nào nó có thể giúp và liệu có thể sử dụng nó thận trọng hơn hay không**. Ba RQ bên dưới là câu hỏi của KLTN; cách đánh số RQ riêng trong mỗi paper không tương ứng trực tiếp với chúng.

## Cách đọc các kết quả

Đánh giá cần trả lời ba câu hỏi khác nhau. Trước hết, mô hình có dự báo đúng hơn từ bài làm trước đó không? Phần này giữ bộ thước đo như baseline BKT: AUC và Accuracy kiểm khả năng dự báo, Log Loss và Brier kiểm chất lượng xác suất, ECE kiểm sự phù hợp giữa mức tự tin và tần suất đúng. Sau đó mới hỏi thay đổi ước lượng có làm hệ thống quyết định hoặc chọn bài khác đi không. Cuối cùng, mô phỏng kiểm người học có tiến bộ và giữ lại kiến thức tốt hơn không. Các số đếm về quyết định bổ sung lời giải thích cho hai tầng sau; chúng không thay bảng so sánh chất lượng dự báo.

## RQ1 — Vì sao thông tin đồ thị chưa chuyển thành cải thiện học tập?

Vấn đề còn mở sau hai paper là khoảng cách giữa “ước lượng tốt hơn” và “chọn bài tốt hơn”. Nếu việc thêm đồ thị làm thay đổi dự báo nhưng hệ thống vẫn nhận định người học đủ hoặc chưa đủ kiến thức như trước, các bài được phép học có thể không đổi. Ngay cả khi tập bài được phép thay đổi, quy tắc chọn bài vẫn có thể đưa ra cùng một đề xuất. Vì thế, khóa luận cần quan sát các tầng này riêng, thay vì chỉ so một điểm dự báo cuối cùng.

Nhóm đã bắt đầu bằng các phép so sánh giữ cùng câu hỏi và lịch sử người học, rồi xem việc thay tập quan hệ tiên quyết đưa vào mô hình có đi cùng thay đổi ở trạng thái ước lượng và đề xuất tiếp theo hay không. Việc so trên cùng đầu vào giúp hạn chế trường hợp hai mô hình trông khác nhau chỉ vì đã được hỏi các bài khác nhau. Nhóm cũng giữ các cơ chế ngoài cạnh giống nhau trong một phép so sánh riêng, nhằm tiến gần hơn tới phần tác động của đầu vào đồ thị mà Paper 2 chưa tách được.

**Kết quả hiện có cho thấy thay đổi dự báo thường không đi cùng thay đổi đề xuất.** Trong 1.080 tình huống so sánh, có 963 tình huống thay đổi xác suất dự báo; 943 trong số đó vẫn giữ đề xuất khái niệm xem trước. Đồng thời, tác động lên chất lượng dự báo khác chiều giữa các hồ sơ người học mô phỏng. Để đánh giá chất lượng dự báo, nhóm kiểm tra xác suất có phù hợp với đáp án quan sát được hay không; các thước đo chi tiết trong notebook phục vụ câu hỏi đó, không đo trực tiếp việc người học đã học được thêm bao nhiêu.

Một phép kiểm tiếp theo cho thấy **quyết định cho phép học tiếp không chỉ dựa vào thành thạo**. Paper 2 cho phép một kiến thức nền đáp ứng điều kiện nếu mô hình đánh dấu đã thành thạo, hoặc nếu nội dung đó đã được chọn ít nhất sáu lần. Trong 3.240 lượt chọn đã lưu, 500 lượt không có kiến thức tiên quyết. Trong 2.740 lượt còn lại, 699 lượt có mọi kiến thức nền được đánh dấu thành thạo; 2.041 lượt cần ngoại lệ đủ số lần luyện. Như vậy, ngoại lệ này thực sự được sử dụng trong các quỹ đạo đã xét. Chưa thể từ đó kết luận ngoại lệ gây lợi hay hại, hoặc xác định bao nhiêu thay đổi dự báo đã bị che khuất. Đây là phân tích lại các quỹ đạo có sẵn, không phải 3.240 người học độc lập.

Phần bổ sung so với hai paper là các đối chiếu cụ thể giữa những đầu ra trung gian, không phải phát hiện lần đầu rằng dự báo và kết quả học tập có thể khác nhau. Hiện chưa xác định đầy đủ nguyên nhân nằm ở mức tự tin của dự báo, cách quyết định thành thạo hay quy tắc chọn bài. Các đề xuất trên mới được kiểm tra thử trên bản sao trạng thái, chưa phải bài đã giao cho người học và chưa chứng minh lợi ích học tập.

## RQ2 — Trong điều kiện nào đồ thị hữu ích, trung tính hoặc bất lợi?

Kết quả chưa tích cực ở hai paper không đủ để kết luận đồ thị vô ích trong mọi trường hợp. Một quan hệ tiên quyết có thể hữu ích với người học thiếu nền tảng nhưng ít tạo khác biệt khi nền tảng đã vững. Tương tự, hệ thống có thể sử dụng thông tin quan hệ khác nhau khi chỉ quan sát được ít bài làm. Đề cương vì thế yêu cầu xét chất lượng đồ thị, lượng lịch sử và đặc điểm người học, thay vì tìm một kết luận chung “có đồ thị tốt hơn hay không”.

**Về lịch sử tương tác,** nhóm giữ cùng tình huống cần dự báo nhưng thay lượng quá khứ mà hệ thống được xem. Trước khi rút ngắn lịch sử, các trường hợp dùng đầy đủ lịch sử được kiểm để bảo đảm khớp đầu ra gốc. Kết quả cho thấy tác động của đồ thị không tăng hoặc giảm đều theo lượng lịch sử. Đây là một đối chứng bổ sung cho RQ2, nhưng việc rút ngắn còn thay bộ ghi nhớ của phần chọn bài, nên chưa thể quy toàn bộ khác biệt cho riêng mô hình ước lượng tri thức.

**Về đặc điểm người học,** nhóm xây dựng phép so sánh giữ cùng cấu trúc mạnh/yếu giữa các khái niệm và cùng chuỗi ngẫu nhiên, rồi thay mức năng lực chung và mức tác động của thiếu kiến thức nền. Mục đích là tránh nhìn thấy một nhóm học tốt hơn rồi quy ngay cho đồ thị. Trong các điều kiện đã thử, việc tăng tác động của quan hệ tiên quyết không luôn làm lợi thế tương đối của cấu hình dùng đồ thị lớn hơn. Đồ thị còn tạo khác biệt ở trường hợp cơ chế thiếu nền tảng không tác động. Vì vậy, chưa thể giải thích mọi lợi thế của đồ thị chỉ bằng cơ chế tiên quyết. Đây mới là kết quả hữu hạn trong mô phỏng, chưa phải quy luật về học sinh thật.

**Về cách đánh giá,** nhóm kiểm tra xem thí nghiệm có vô tình tạo sẵn một phần kết luận hay không. Chẳng hạn, trong các trạng thái đã xét, phần tiến bộ ròng so với mức nền cố định không âm và giảm theo cùng một tốc độ quên. Nếu không luyện thêm sau khi kết thúc, lượng tiến bộ còn giữ sau 14 ngày chỉ là một tỷ lệ cố định của lượng tiến bộ ròng tại thời điểm kết thúc. Hai con số đó không cung cấp hai bằng chứng độc lập. Tuy nhiên, chỉ số học thêm tức thời của Paper 2 là đại lượng khác; kết quả này không chứng minh hai chỉ số chính của paper trùng lặp. Một cách đọc mức thành thạo khác cũng đã cho phản ví dụ đổi thứ hạng, nên không thể loại bỏ mọi phép đo duy trì kiến thức.

Trên **Junyi**, nhóm kiểm tra thêm một nguy cơ: người học vốn có thể làm bài theo thứ tự chịu ảnh hưởng của bản đồ kiến thức. Một đồ thị khớp thứ tự đã ghi chưa chắc là đồ thị giúp dạy tốt hơn. Các phép kiểm hiện có cho thấy cách xếp hạng theo thứ tự luyện có thể đổi khi thay tập trường hợp được quan sát hoặc cách tính tỷ lệ. Vì vậy, chúng được dùng để cảnh báo và kiểm soát phép so sánh, chưa được diễn giải thành lợi ích giảng dạy.

Những kết quả này bổ sung các điều kiện và giới hạn cần kiểm soát. Chúng chưa thay thế việc đánh giá đầy đủ đồ thị chuyên gia, đồ thị học từ dữ liệu và đồ thị bị gây nhiễu như đề cương yêu cầu. Việc đối chiếu đúng phiên bản mã tạo ra kết quả Paper 1 cũng còn thiếu; các phản ví dụ trên mã đang có không được dùng để bác bỏ kết quả của PDF.

## RQ3 — Có thể sử dụng đồ thị thận trọng hơn theo độ tin cậy không?

RQ1 và RQ2 dẫn tới một hướng giải quyết cần kiểm chứng: hệ thống không nên buộc phải tin mọi quan hệ tiên quyết với cùng mức độ. Đề cương đề xuất CG-AKT trên nền AKT, một mô hình học từ lịch sử bài làm. Phần bổ sung sẽ điều chỉnh ảnh hưởng của từng quan hệ dựa trên bằng chứng hỗ trợ và cho phép quay về phương án không dùng đồ thị khi dữ liệu phát triển chưa cho thấy lợi ích đủ rõ.

Để kiểm tra giả thuyết này, cần so các phương án trên cùng dữ liệu và giới hạn thông tin, rồi đánh giá riêng dự báo, đề xuất bài và kết quả học trong mô phỏng. Nhóm đã chuẩn bị bộ dữ liệu mô phỏng có phân vai cho huấn luyện, lựa chọn và điều chỉnh mức tự tin, cùng các thành phần phần mềm phục vụ quy trình đó. **Chưa có kết quả nghiên cứu đầy đủ để khẳng định CG-AKT tốt hơn đồ thị cố định hoặc không dùng đồ thị.** Để tránh chỉ so với các mô hình cũ, phần đánh giá tiếp theo vẫn phải giữ AKT, SAKT, GKT, GAM-KT, Graph-GAM-KT và BKT tham chiếu, cùng phương án AKT dùng đồ thị cố định và CG-AKT. Việc thử đồ thị chuyên gia, đồ thị học từ dữ liệu, đồ thị gây nhiễu và demo nghiên cứu cũng chưa được bỏ khỏi phạm vi đề cương.

## Tiến độ hiện tại và phần làm tiếp

Đến thời điểm này, nhóm đã có bằng chứng chẩn đoán cho từng phần của RQ1 và RQ2, thay vì chỉ có công việc cài đặt. Tuy vậy, chưa RQ nào được đánh dấu hoàn tất; RQ3 vẫn cần các mô hình đã huấn luyện và phép so sánh nghiên cứu đầy đủ.

Bước tiếp theo là hoàn tất quy trình chạy có thể kiểm chứng, thực hiện các đối chứng còn thiếu về mức tự tin và lựa chọn bài, rồi nối các mô hình bắt buộc vào phép so sánh chung. Việc viết kết quả và chuẩn bị demo tiếp tục dựa trên bằng chứng đã lưu, giữ cả kết quả bất lợi hoặc chưa kết luận được.

[Báo cáo nghiên cứu có minh họa](BAO_CAO_NGHIEN_CUU.html) trình bày đầy đủ bối cảnh, thiết kế so sánh, bảng dự báo BKT/GAM-KT trên Junyi, các kết quả chẩn đoán cho từng RQ, biểu đồ và nguồn kiểm chứng.

**Tài liệu nền:** Đề cương KLTN đã duyệt (2026), tr. 1–4; Paper 1 về đồ thị và chính sách lựa chọn, tr. 1 và 4–5; Paper 2 về theo dõi tri thức có tiên quyết, tr. 1 và 3–6. Tên đầy đủ và phạm vi kế thừa được trình bày trong báo cáo HTML.
