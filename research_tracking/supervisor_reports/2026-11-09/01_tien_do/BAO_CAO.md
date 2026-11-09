# Báo cáo tiến độ khóa luận — 09/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương và Hồ Nguyễn Minh Sang.

[Báo cáo chi tiết: diễn tiến nghiên cứu, số liệu và biểu đồ](BAO_CAO_NGHIEN_CUU.html).

## Điểm xuất phát và tiến độ hiện tại

Paper 1 cho thấy tính liên tục của lộ trình chịu ảnh hưởng của cách chọn bài, trong khi đồ thị mở rộng chưa cải thiện ổn định mức thành thạo. Paper 2 quan sát cải thiện dự báo nhỏ ở một số nhóm mô phỏng nhưng chưa phát hiện lợi ích rõ ở kết quả học tập chính. Khóa luận đi tiếp từ khoảng trống này: vì sao đồ thị chưa giúp ổn định, khi nào nó có ích và liệu CG-AKT sử dụng độ tin cậy cạnh có cải thiện được không?

**Đã có bằng chứng chẩn đoán mới cho RQ1–RQ2, gồm phép đo trực tiếp hai điều kiện xét thành thạo; RQ3 đã có dữ liệu, bước ước lượng cạnh và lõi CG-AKT được kiểm tính toán. Chưa RQ nào hoàn tất; chưa có kết quả CG-AKT đã huấn luyện để kết luận mô hình này tốt hơn.**

## Quá trình đã thực hiện

**Trước hết, nhóm kiểm lại nền thí nghiệm.** Đã dựng phản ví dụ quay lại chương trên mã Paper 1 hiện có, nhưng chưa xác minh đó là đúng phiên bản tạo PDF nên không dùng để bác bỏ paper. Đã làm rõ khi tiến bộ ròng sau 14 ngày chỉ tỷ lệ với tiến bộ cuối lịch; điều này không chứng minh hai kết quả chính của Paper 2 dư thừa. Trên Junyi, đã lượng hóa trường hợp tỷ lệ khớp thứ tự tăng dù số trường hợp phù hợp giảm, do mẫu số thay đổi. Những kiểm tra này giúp tránh coi giả định mô phỏng hoặc thứ tự luyện là bằng chứng đồ thị dạy tốt.

**Sau đó, nhóm tách riêng đầu vào cạnh trên cùng tình huống.** Trong 1.080 câu hỏi/nhãn được giữ chung, 963 dự báo thay đổi nhưng 943 trong số đó giữ đề xuất khái niệm xem trước; chỉ 22 đề xuất thử đầy đủ thay đổi. Tác động dự báo khác chiều giữa các hồ sơ. Phân tích bản tái dựng quỹ đạo còn cho thấy 2.041/2.740 lượt chọn khái niệm có tiên quyết cần ngoại lệ đã luyện đủ lần, thay vì mọi kiến thức nền được đánh dấu thành thạo. Đã xác định được cơ chế cụ thể trong quyết định cho phép học; chưa chứng minh cơ chế này gây lợi, gây hại hoặc che khuất bao nhiêu tác động của đồ thị.

**Trở lại 1.080 tình huống giữ chung câu hỏi, nhóm kiểm nơi quyết định được giữ lại.** Có 55 lần tập cho phép thay đổi nhưng đề xuất thử giữ nguyên; 17 lần đề xuất thử đổi dù cả tập thành thạo và tập cho phép giữ nguyên. Trong 5 lần cả ba đầu ra cùng đổi, khái niệm full chọn nằm ngoài tập cho phép đã ghi của empty. Đây là đề xuất thử, chưa là bài giao cho người học; tập ghi lại chưa phản ánh mọi bước lọc của bộ chọn bài và không cho phép quy riêng cho điểm xếp hạng. Phân tích đọc lại mẫu cũ, không tăng số người học hay mẫu độc lập.

**Tái dựng các bước lọc giúp giải thích cụ thể hơn.** Trong 55 lần tập cho phép đổi nhưng đề xuất giữ nguyên, 4 lần khác biệt bị loại khỏi tập cuối sau cân bằng số lượt; 51 lần tập cuối vẫn khác nhưng cùng khái niệm thắng. 17 lần đổi khái niệm trong cùng tập cuối khớp khóa xếp hạng của nguồn. Đây là giải thích quyết định thử từ dữ liệu đã lưu, không phải các tập ứng viên ghi trực tiếp, thành thạo đã hiệu chuẩn hoặc lợi ích học tập; không thêm mẫu độc lập.

**Tiếp theo, nhóm kiểm điều kiện người học.** Đối chứng thay lượng lịch sử không cho một chiều tác động đều. Đối chứng năng lực chung và mức phạt thiếu nền tảng không cho lợi thế đồ thị tăng nhất quán khi bật mức phạt. Đây là kết quả hữu hạn trong mô phỏng với ba khối ngẫu nhiên dùng lại, chưa phải quy luật về học sinh thật hoặc đánh giá đầy đủ các mức nhiễu đồ thị.

**Từ đó, nhóm chuẩn bị phép kiểm CG-AKT.** Đã tạo corpus mô phỏng riêng gồm 60 người học ×210 lượt, phân vai 48 huấn luyện /6 chọn số vòng học /6 hiệu chỉnh xác suất. Bước ước lượng cạnh từ TRAIN đã hoàn tất 2.352 lần khớp mô hình CPU và tạo đồ thị ứng viên 31 cạnh theo quy tắc định trước. Điểm cạnh phản ánh mức ổn định của lợi ích dự báo, không phải xác suất tiên quyết đúng; chưa chứng minh khôi phục đúng đồ thị hoặc cải thiện CG-AKT. Điểm của 31 cạnh đã được đọc lại theo đúng hợp đồng dữ liệu; cầu tính toán SAKT cũng đã được kiểm tra trên dữ liệu nhỏ. Đây là chuẩn bị phần mềm, chưa là kết quả SAKT hoặc CG-AKT đã huấn luyện trên corpus nghiên cứu.

**Cuối cùng, nhóm quay lại đo trực tiếp quyết định thành thạo.** Đã phát lại đủ 18 lượt trên chín lịch sử cũ, khớp toàn bộ 2.160 thời điểm với kết quả đã lưu. Trên 30.240 cặp khái niệm–thời điểm, có 3.428 cặp khác điều kiện bất định nhưng vẫn cùng đánh giá chưa thành thạo, vì điểm kiến thức ước lượng của cả hai dưới ngưỡng. Cả 90 cặp khác quyết định thành thạo đều khác điều kiện kiến thức, khi hai phía cùng đạt điều kiện bất định. Đây là bất đồng giữa cấu hình ở cùng thời điểm, không phải 90 lần học vượt ngưỡng. Đã xác định thêm nơi tác động bị giữ lại; chưa nói được đánh giá nào đúng hơn hay giúp học tốt hơn.

**Ghép tiếp với khái niệm đang được hỏi cho thấy hai con số 22 không ứng với cùng một nhóm tình huống.** Trong cùng 1.080 cặp full–empty, tiêu chí dựa trên xác suất trung bình của ba câu tham chiếu và khái niệm được đề xuất thử đều khác nhau ở 22 tình huống, nhưng chỉ trùng 2 tình huống. Cả 5 bất đồng đánh giá thành thạo riêng của khái niệm đang được hỏi đều không đi kèm đổi khái niệm đề xuất. Điều này không mâu thuẫn với 90 bất đồng tập thành thạo ở trên: câu đang hỏi chỉ gắn với một khái niệm, còn tập thành thạo xét cả 28 và bộ chọn có thể đề xuất khái niệm khác. Tiêu chí xác suất chưa được hiệu chỉnh; đề xuất xem trước chưa là bài thực giao. Đây là đọc lại cùng mẫu cũ, không thêm người học hay chứng minh xác suất thay đổi gây đổi bài.

**Lõi CG-AKT đầu tiên cũng đã được kiểm bằng tính toán và gradient thật trên CPU.** Có confidence theo cạnh, gate điều chỉnh ảnh hưởng và đường tắt graph; dữ liệu kiểm được dựng sẵn. Chưa huấn luyện trên corpus nghiên cứu, chưa chứng minh các biến thể hoặc hệ thống chọn bài tốt hơn. Phần lưu và nạp lại trạng thái huấn luyện đã được kiểm qua hai tiến trình độc lập trên CPU. Chạy lại trọn vòng dữ liệu kế tiếp cho cùng thứ tự mẫu và cùng trạng thái mô hình. Đây là kiểm khả năng khôi phục ở cuối một vòng huấn luyện trên dữ liệu dựng sẵn; workflow huấn luyện trên corpus nghiên cứu, lựa chọn mô hình, đánh giá vòng kín và CUDA vẫn còn phải hoàn thiện.

**Tiếp đó, nhóm kiểm tra vì sao thay cơ chế học trong mô phỏng chưa chắc làm đổi lịch sử bài làm.** Nhóm đọc lại đủ 14.400 lượt của pilot cũ, gồm 10 khối ngẫu nhiên ×3 hồ sơ ×4 điều kiện. Khi giữ cùng cấu hình mô hình và bật/tắt mức phạt thiếu kiến thức nền, 58/60 cặp giữ nguyên toàn bộ đáp án quan sát và 59/60 cặp giữ nguyên chuỗi bài. Khi đổi hai cơ chế dùng thông tin cha của GAM, cả 60/60 cặp có chuỗi bài khác. Mỗi cặp so hai quỹ đạo dùng chung điều kiện ban đầu; các cặp lặp bên trong 10 khối, không phải 60 người học độc lập.

Phát hiện này phân biệt **kiến thức thật thay đổi trong simulator** với **phản hồi mà mô hình nhận được**. Mức học liên tục có thể thay đổi dù người học vẫn trả lời giống nhau trên cùng bài. Bởi vậy, chỉ thấy chuỗi bài gần như giữ nguyên chưa đủ để kết luận cơ chế thiếu nền tảng không ảnh hưởng học tập. Nhóm đã nối từng quỹ đạo với các kết quả cuối cũ và giữ cả trường hợp bất lợi; chưa tách được tác động riêng của năng lực chung hoặc chứng minh lợi ích của đồ thị trên người học thật. Đây là phân tích bổ sung trên dữ liệu đã xem, không phải thí nghiệm xác nhận mới.

**Từ lịch sử quan sát ấy, nhóm kiểm tiếp mức tự tin của dự báo theo từng hồ sơ.** Trên cùng 14.400 lượt đã lưu, mô hình GAM tắt hai cơ chế dùng thông tin cha dự báo trung bình khoảng 55% cho hồ sơ PG, trong khi tỷ lệ đúng quan sát gần 75% và xác suất từ simulator gần 77%. Với hồ sơ PY, ba giá trị tương ứng khoảng 47%, 30% và 31%. Những sai lệch trái chiều có thể bù trừ khi gộp các hồ sơ vào cùng khoảng dự báo. Đã kiểm và lưu đủ các khoảng xác suất cho bốn điều kiện của pilot.

Phân tích mới cho thấy **chỉ số phù hợp xác suất tính gộp có thể che sai lệch lớn ở từng hồ sơ và đảo thứ hạng mô tả giữa cấu hình**. Đây là một lời giải thích cụ thể cần kiểm trong RQ1, bổ sung cho các bảng dự báo tổng hợp của Paper 2. Các cấu hình có thể phục vụ những bài và lịch sử khác nhau, nên kết quả hiện tại chưa xác định cấu hình nào hiệu chỉnh tốt hơn trên cùng tình huống. Bước tiếp theo là đối chiếu trực tiếp quyết định thành thạo với trạng thái thật đã lưu, rồi kiểm một biện pháp hiệu chỉnh trên dữ liệu tách riêng.

## Còn phải chứng minh

- **RQ1:** đánh giá độ đúng của quyết định thành thạo, hiệu chỉnh xác suất và vai trò chính sách; nối chẩn đoán nội bộ đã có với kết quả học tập.
- **RQ2:** kiểm khả năng khái quát qua đồ thị nhiễu, nhóm khái niệm và người học mới, với đối chứng đúng quần thể.
- **RQ3:** hoàn thiện workflow huấn luyện/checkpoint từ lõi đã kiểm; so sánh không đồ thị / đồ thị cố định / confidence / gate cùng các baseline bắt buộc, rồi đánh giá chọn bài và kết quả học vòng kín.

Các mô hình và demo trong đề cương vẫn được giữ. Kết quả không cải thiện hoặc cổng chọn tắt đồ thị vẫn được báo cáo nếu bằng chứng hỗ trợ; chưa có kết luận ưu thế của CG-AKT hoặc hiệu quả giáo dục trên người học thật.
