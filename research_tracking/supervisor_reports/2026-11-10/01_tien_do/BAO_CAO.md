# Báo cáo tiến độ khóa luận — 10/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương và Hồ Nguyễn Minh Sang.

[Báo cáo chi tiết: diễn tiến nghiên cứu, số liệu và biểu đồ](BAO_CAO_NGHIEN_CUU.html).

## Điểm xuất phát và tiến độ hiện tại

Paper 1 được kế thừa theo bản PDF phát triển dùng để nộp, là nguồn chuẩn về thiết kế và kết quả, còn notebook trong repository là bản tiền kỳ. Theo PDF, tính liên tục của lộ trình chịu ảnh hưởng của cách chọn bài, trong khi đồ thị mở rộng chưa cải thiện ổn định mức thành thạo. Paper 2 quan sát cải thiện dự báo nhỏ ở một số nhóm mô phỏng nhưng chưa phát hiện lợi ích rõ ở kết quả học tập chính. Khóa luận đi tiếp từ khoảng trống này: vì sao đồ thị chưa giúp ổn định, khi nào nó có ích và liệu CG-AKT sử dụng độ tin cậy cạnh có cải thiện được không?

**Đã có bằng chứng chẩn đoán mới cho RQ1–RQ2, gồm phép đo trực tiếp hai điều kiện xét thành thạo; RQ3 đã có dữ liệu, bước ước lượng cạnh, lõi CG-AKT được kiểm tính toán và quy trình chọn checkpoint AKT không đồ thị chạy thành công trên corpus nhỏ. Chưa RQ nào hoàn tất; chưa có kết quả CG-AKT đã huấn luyện để kết luận mô hình này tốt hơn.**

**Mốc chẩn đoán thành thạo trước đó.** Đã giải thích đủ 30 thời điểm nhãn thành thạo khác nhau nhưng tập sẵn sàng ban đầu giống nhau, với phần trùng nhau giữa các điều kiện được kiểm riêng.

**Đã giải thích vì sao hai đường đi khác nhau cùng dừng ở 172 lượt trong ví dụ Paper 1. Khi giữ cùng trạng thái ban đầu và cùng số ngẫu nhiên ở từng lần luyện của mỗi khái niệm, nếu cả hai nhánh đều hoàn tất, tổng lượt và trạng thái cuối bằng nhau dù thứ tự chương có thể khác. Sáu tình huống dựng tay đã kiểm cả điều kiện này và giới hạn khi dừng sớm hoặc chạm trần trạng thái.**

**Mốc mới cho RQ2.** Đã mở rộng đối chứng sang đồ thị học từ dữ liệu. Cả 18 cặp đổi chuỗi bài. Ở nhóm năng lực cao có cơ chế thiếu tiên quyết bất hoạt, đổi nguồn đồ thị vẫn làm kết quả học khác nhau, còn bật mức phạt giữ nguyên lịch sử và trạng thái cuối. Điều này tách được một chênh lệch ngoài cơ chế phạt thiếu nền tảng; khả năng khái quát và thứ hạng đồ thị còn phải kiểm tiếp.

Ở mốc kiểm trước, AKT đạt 299 kiểm hợp đồng và 18 kiểm checkpoint thật trên CPU. Bộ nghiệm thu tích hợp tại mốc trước đã đạt 1.913 ca, bao gồm nhiều kiểm đã chạy riêng trước đó. Mốc này kiểm sự phối hợp của các thành phần trước khi dùng tài nguyên huấn luyện lớn. GKT đã đạt 11 kiểm mô hình và 8 kiểm trainer trên dữ liệu dựng sẵn. Phần lưu và nạp trạng thái cuối vòng huấn luyện cũng đã qua 28 kiểm trên CPU, vòng học kế tiếp khớp đối chứng trong phạm vi đã kiểm. Đã kiểm thêm dừng chủ động AKT sau epoch 5 rồi chạy tiếp đến epoch 7 qua pipeline thật. Checkpoint tốt nhất ở epoch 4 được giữ riêng với trạng thái mới nhất ở epoch 5. Cả lịch sử huấn luyện và 84 dự báo xuất cuối khớp lượt chạy liền mạch. Các mốc này kiểm độ tin cậy của quy trình trên CPU, còn phục hồi khi lỗi bất ngờ, CUDA và so sánh nghiên cứu vẫn cần thực hiện. Phần xem lại minh chứng trong demo đã cho đổi khối mô phỏng, mức khởi tạo và cơ chế phạt để đọc số liệu tương ứng. Các mô hình đã huấn luyện và luồng chọn bài cho người học mới vẫn còn cần được nối.

**Mốc cập nhật ngày 10/11, phép đối chứng nguồn đồ thị đã hoàn tất 120 ca trên mười khối mô phỏng mới. Kết quả cho thấy phần thay đổi do bật cơ chế phạt còn đổi dấu giữa các khối ở mức khởi tạo thấp và trung bình. Đối chứng năng lực cao tiếp tục tách được tác động ngoài riêng cơ chế phạt. Đây là bằng chứng chẩn đoán mới, chưa là kết luận mô hình nào tốt hơn một cách ổn định.**

**Cập nhật phân tích bất định.** Đã kiểm ba so sánh trên cùng mười khối. Khoảng thăm dò ở mức 1150 nằm phía dương, nhưng chênh lệch tác động giữa mức 1150 và 1000 vẫn chưa phân biệt rõ với 0. Kết quả bổ sung sau khi xem dữ liệu được giữ ở mức thăm dò.

**Phát hiện mới về cách đo thành thạo.** Trên ba lịch sử cùng một khối, quan sát toàn bộ 28 khái niệm cho thấy nhật ký chỉ gồm câu đang giao bỏ ngoài 215 công nhận đúng và 5 công nhận nhầm ở những khái niệm khác tại cùng thời điểm. Đã kiểm độc lập trạng thái dựng lại ở mọi bước. Các con số là lần đo lặp, chưa là bằng chứng khái quát qua nhiều người học.

### Chuẩn bị mô hình cho thí nghiệm tiếp theo

SAKT đã hoàn tất một vòng đời kiểm kỹ thuật CPU trên bộ dữ liệu mô phỏng nhỏ gồm 8 người học huấn luyện, 1 người học chọn vòng và 1 người học dành riêng cho hiệu chỉnh. Lượt kiểm chạy 6 vòng học, chọn checkpoint vòng 1, nạp lại checkpoint và xuất đủ 84 dự báo của tập chọn vòng. Tập hiệu chỉnh chưa được dùng để tối ưu hoặc đánh giá mô hình. Đây là bằng chứng pipeline hoạt động trên bộ dữ liệu kiểm kỹ thuật, chưa là kết quả so sánh SAKT trong thí nghiệm chính.

Đường chạy AKT có đồ thị cố định cũng đã hoàn tất kiểm kỹ thuật trên cùng bộ dữ liệu mô phỏng nhỏ. Nhóm giữ cùng dữ liệu và cấu hình học với AKT không đồ thị, kiểm phần AKT gốc có cùng trạng thái khởi tạo, rồi chạy đủ quy trình huấn luyện, chọn checkpoint, nạp lại và xuất 84 dự báo. Kết quả này xác nhận thêm một đường so sánh đã hoạt động bằng mô hình thật. GKT được kiểm tiếp bằng cấu hình riêng đã cố định. Lượt kiểm hoàn tất 11 vòng học, chọn vòng 6, nạp lại checkpoint và xuất đủ 84 dự báo. Thí nghiệm chính, độ tin cậy cạnh và cơ chế điều tiết ảnh hưởng đồ thị, huấn luyện lại, hiệu chỉnh xác suất và đánh giá học tập vòng kín vẫn còn phải thực hiện.

Để chuẩn bị thí nghiệm chính, nhóm đã kiểm cách ghép đầu ra của chín điều kiện so sánh trên dữ liệu giả ở quy mô 1.260 lượt trả lời. Bước này kiểm việc đối chiếu đúng người học, câu hỏi, lịch sử và nhãn, để kết quả sau huấn luyện có thể so sánh trên cùng quần thể. Bộ kiểm tổng thể cần chạy lại trên nguồn mới trước lượt GPU. Huấn luyện GPU chính thức, kiểm phục hồi khi lỗi bất ngờ và các so sánh neural trên corpus nghiên cứu vẫn còn phải thực hiện.

## Quá trình đã thực hiện

**Trước hết, nhóm kiểm lại nền thí nghiệm.** Đã dựng phản ví dụ quay lại chương trên notebook tiền kỳ của Paper 1 và chỉ dùng kết quả để mô tả quy tắc của bản tiền kỳ đó. Thiết kế và kết quả kế thừa lấy theo PDF chuẩn. Các mô phỏng mới tiếp nối Paper 1 cần bám PDF, ghi rõ phiên bản và tiêu chí đối chiếu hành vi. Cần kiểm chứng riêng trước khi gọi là tái lập chính xác thí nghiệm gốc. Đã làm rõ khi tiến bộ ròng sau 14 ngày chỉ tỷ lệ với tiến bộ cuối lịch; điều này không chứng minh hai kết quả chính của Paper 2 dư thừa. Trên Junyi, đã lượng hóa trường hợp tỷ lệ khớp thứ tự tăng dù số trường hợp phù hợp giảm, do mẫu số thay đổi. Những kiểm tra này giúp tránh coi giả định mô phỏng hoặc thứ tự luyện là bằng chứng đồ thị dạy tốt.

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

**Chuẩn bị huấn luyện AKT đã tiến thêm một mốc kiểm phần mềm.** Sau khi bổ sung khả năng tiếp tục ở cuối một vòng huấn luyện, bộ kiểm hợp đồng hiện hành đã đạt 299/299 ca. Kiểm checkpoint thật theo nguồn hiện hành cũng đã đạt 18/18 ca. Các bước còn lại gồm kiểm đầy đủ khả năng tiếp tục ở cấp pipeline và kiểm CUDA. Kết quả này tăng độ tin cậy của pipeline, chưa bổ sung kết quả so sánh các mô hình cho RQ3.

**Mốc tích hợp mới nhất, AKT đã đi qua quy trình chọn checkpoint thực tế.** Nhóm đã chạy thành công quy trình AKT không đồ thị trên corpus kiểm tích hợp riêng gồm 10 người học ×84 lượt. Tám người dùng để huấn luyện, một người chọn số vòng học và một người được giữ riêng cho hiệu chỉnh. Lượt kiểm hoàn tất 7 vòng học với 14 bước cập nhật, chọn checkpoint ở vòng 4, nạp lại vào mô hình mới và xuất đủ 84 dự báo trên người học chọn vòng. Kết quả sau nạp lại khớp checkpoint đã chọn. Toàn bộ lượt kiểm chạy trên CPU local, chưa dùng credit Modal.

Mốc này xác nhận đường đi dữ liệu → huấn luyện → chọn checkpoint → nạp lại → xuất dự báo của AKT không đồ thị trên corpus nhỏ. Huấn luyện lại, hiệu chỉnh xác suất, khôi phục toàn bộ quy trình, kiểm Linux/CUDA và các so sánh CG-AKT trên corpus nghiên cứu còn phải thực hiện. Bộ kiểm chỉ có một người học chọn vòng, nên chưa cung cấp bằng chứng so sánh chất lượng mô hình cho RQ3.

Song song, nhóm đã nối hồ sơ người học, world, ước lượng Elo và bộ chọn bài thành một lượt mô phỏng riêng theo PDF Paper 1. Bộ kiểm hiện có 85 trường hợp đã đạt, gồm 13 ca mới cho việc sinh dữ liệu theo seed. Bộ đầu vào ứng viên đã nạp thành công, gồm 28 khái niệm, 84 câu và hai đồ thị 25/31 cạnh. Nhóm đã nối bộ sinh riêng theo từng người học, khái niệm và lần luyện với lượt mô phỏng. Hai nhánh có thể dùng lại cùng trạng thái ban đầu và cùng số ngẫu nhiên ở lần luyện tương ứng của khái niệm. Các kiểm tra trên bộ câu dựng tay xác nhận tái tạo được lượt chạy và giữ thứ tự dự đoán–phản hồi–cập nhật. Đã kiểm thêm một lượt trên miền 28 khái niệm và 84 câu, giữ cùng hồ sơ US và bộ số ngẫu nhiên theo lần luyện của từng khái niệm. Trong đúng lượt seed 42 này, hai nhánh đều dừng sau 172 tương tác khi bộ ước lượng đánh dấu đủ 28 khái niệm thành thạo. Đồ thị 25 cạnh có 0 lần quay lại chương, còn đồ thị 31 cạnh có 2 lần. Trạng thái kiến thức ẩn cuối của hai nhánh giống nhau. Ví dụ này nối được lập luận về quy tắc chương với một lượt chạy có đầy đủ dấu vết. Một cặp lượt chạy chưa xác định được thứ hạng đồ thị hoặc lợi ích học tập. Còn phải hoàn thiện các chính sách so sánh và kiểm các điều kiện làm thay đổi kết quả trước thí nghiệm đầy đủ.

**Kiểm tiếp điểm tổng hợp trên cùng lịch sử.** Ở các chặng trước, nhóm đã đọc xác suất trung bình của ba câu tham chiếu để theo dõi một tiêu chí gắn với quyết định. Trước khi dùng điểm này để đánh giá thành thạo, cần biết nó có phù hợp với đáp án hay không. Nhóm kiểm lại trên 1.080 tình huống cũ, nơi câu hỏi được lấy ngẫu nhiên đều từ bộ câu cố định và hai cấu hình nhận cùng lịch sử, câu hỏi, đáp án. Mỗi khái niệm có ba câu tham chiếu, nên trung bình ba dự báo có thể được đánh giá như dự báo cho một câu lấy ngẫu nhiên trong nhóm đó.

Điểm tổng hợp vẫn thấp hơn tỷ lệ đúng ở PG và cao hơn ở PY/PYH. Để kiểm độ phù hợp của xác suất, nhóm gom dự báo vào 15 khoảng cố định, so dự báo trung bình với tỷ lệ đúng trong từng khoảng và tổng hợp độ lệch theo số lượt. Độ lệch tính gộp khoảng 4,3 điểm phần trăm, trong khi ở PG khoảng 26 điểm phần trăm. Như vậy, hiện tượng gộp nhóm che sai lệch còn xuất hiện ở điểm đọc từ ba câu tham chiếu, trên phép so đã giữ chung dòng dữ liệu. Nhận đủ cạnh làm sai lệch nhỏ hơn ở PY/PYH nhưng lớn hơn ở PG; chưa có một chiều cải thiện ổn định.

Phép kiểm dùng lại ba khối ngẫu nhiên với chín lịch sử hồ sơ, không thêm người học hoặc mẫu độc lập. Mỗi đáp án được dùng một lần cho mỗi cấu hình. Kết quả mới đánh giá sự phù hợp với đáp án của điểm tổng hợp; độ đúng của đánh giá thành thạo so với trạng thái thật và tác động lên học tập còn phải kiểm riêng.

**Bổ sung lời giải thích cho kết quả không quay lại chương trong Paper 1.** Từ quy tắc ready và giữ chương, nhóm đã chứng minh một điều kiện đủ. Khi đồ thị chỉ có cạnh nội chương, khái niệm đã đạt ngưỡng được giữ nguyên và chương còn khái niệm chưa đạt luôn có bài được phép học. Bộ chọn vì vậy chỉ rời chương sau khi hoàn tất chương đó. Dưới những giả thiết này, không quay lại chương là hệ quả của quy tắc. Nhóm đã kiểm bốn tình huống nhỏ, gồm cả đáp án sai. Với cạnh liên chương, một phản ví dụ cho chuỗi A → B → A dù bộ chọn vẫn giữ đúng quy tắc. Phần bổ sung xác định ranh giới của cơ chế; hiệu quả học tập còn cần đối chiếu trạng thái kiến thức thật và kết quả cuối.

**Giải thích bước từ thành thạo đến tập sẵn sàng ban đầu.** Trên cùng 1.080 thời điểm, hai cấu hình Graph-GAM-KT nhận 31 và 0 cạnh có 90 thời điểm khác nhãn thành thạo ở một khái niệm. Tập sẵn sàng ban đầu R khác nhau ở 60 thời điểm và giống nhau ở 30 thời điểm. R là đầu vào cho các bước lọc và mở rộng ứng viên tiếp theo của bộ chọn bài. Trong cả 90 thời điểm, chính khái niệm mang nhãn khác nhau đều còn bị điều kiện tiên quyết chặn khỏi R.

Đã giải thích đủ 30 thời điểm có cùng R. Có 18 trường hợp ở khái niệm không có con trực tiếp trong đồ thị của bộ điều khiển, còn 12 trường hợp có khái niệm con đã mang nhãn thành thạo ở cả hai cấu hình. Trong 12 trường hợp sau có 4 trường hợp đồng thời đủ 6 lần luyện ở tiên quyết, nên cần ghi rõ phần trùng nhau khi giải thích. Tất cả 30 trường hợp thuộc hồ sơ PG. Kết quả đã được tính lại trực tiếp từ 18 trace gốc của cùng chín lịch sử. Phần đánh giá độ đúng của nhãn so với kiến thức thật và tác động lên học tập vẫn cần làm tiếp.

## Chặng 12. Vì sao hai đường đi khác nhau cùng dừng ở 172 lượt?

Paper1 tách vai trò của đồ thị và chính sách trong đường đi học. Paper2 còn cho thấy cần phân biệt dự báo, quyết định và kết quả học. Sau ví dụ hai đồ thị cùng dừng ở 172 tương tác nhưng quay lại chương khác nhau, nhóm đặt câu hỏi số lượt bằng nhau có phản ánh hiệu quả tương đương, hay đến từ quy tắc mô phỏng.

Nhóm kiểm lại quy tắc trạng thái của từng khái niệm trong phiên bản Paper1 đang triển khai. Hai nhánh giữ cùng trạng thái ban đầu, bộ câu, quy tắc chọn độ khó và dòng số ngẫu nhiên theo số lần luyện riêng của mỗi khái niệm. Trạng thái chỉ cập nhật ở khái niệm được chọn, không quên theo thời gian hoặc nhận tác động học từ khái niệm khác. Bởi vậy, lần luyện thứ n của một khái niệm có cùng câu hỏi, dự báo, đáp án và cập nhật ở hai nhánh, dù lần luyện đó xuất hiện ở những vị trí khác nhau trên toàn đường đi.

Từ đó có một kết luận có điều kiện. Nếu cả hai lượt đều hoàn tất mọi khái niệm theo ngưỡng của bộ ước lượng, mỗi khái niệm cần cùng số lần luyện để chạm ngưỡng lần đầu. Tổng số tương tác và trạng thái cuối vì vậy bằng nhau, trong khi thứ tự chương và số lần quay lại vẫn có thể khác. Điều này giải thích sự bằng nhau ở 172 trong ví dụ đã chạy dưới các giả thiết được giữ cố định, chưa chứng minh hai đồ thị đem lại kết quả học tương đương ở mọi điều kiện. Các tình huống dựng tay đã kiểm cả đáp án sai, đổi độ khó câu hỏi và mức cập nhật thay đổi theo số lần luyện.

Điều kiện hoàn tất không thể bị bỏ qua. Khi dừng vì hết ngân sách trước lúc hoàn tất, hai đường đi có thể dành số lượt khác nhau cho từng khái niệm. Những đoạn luyện chung của từng khái niệm vẫn giống nhau, nhưng trạng thái cuối của cả bộ khái niệm có thể khác. Một trường hợp nhỏ còn cho thấy vai trò của trần trạng thái 1500. Nếu chỉ có một lượt phản hồi, luyện khái niệm đang ở 1498 làm trạng thái thật tăng 2, còn luyện khái niệm đang ở 1200 làm nó tăng 12. Với cùng số lượt mà mọi cập nhật đều tăng đủ 12, tổng mức tăng bằng 12 nhân số phản hồi, ngay cả khi đáp án và phân bổ lượt luyện khác nhau.

Phần bổ sung làm rõ chỉ tiêu nào có thể đã bị quy tắc của mô phỏng ràng buộc. Nó không biến toàn bộ hai lịch sử thành giống nhau, không xếp hạng đồ thị và không xác nhận lợi ích trên người học thật. Còn phải đối chiếu phân bổ dưới ngân sách hữu hạn, các chính sách so sánh và những cơ chế học khác trước khi kết luận về hiệu quả học.

## Chặng 13. Đổi nguồn đồ thị khi cơ chế thiếu nền tảng bất hoạt

Các chặng trước đã cho thấy kết quả học có thể chịu ảnh hưởng của cơ chế mô phỏng và cách mô hình sử dụng thông tin cha. Từ đây, nhóm đặt câu hỏi tiếp theo cho RQ2. Khi thay đồ thị chuyên gia bằng đồ thị được ước lượng từ dữ liệu, chênh lệch học tập có thực sự đi qua cơ chế thiếu kiến thức nền, hay còn xuất hiện qua những đường khác của hệ thống?

Nhóm dùng đồ thị 31 cạnh đã ước lượng từ phần huấn luyện, chỉ thay đầu vào đồ thị của mô hình GAM. Đồ thị mô tả thế giới và đồ thị của bộ điều khiển giữ nguyên theo chuyên gia. Các cơ chế dùng tín hiệu cha và điều chỉnh theo cha được giữ bật, điều chỉnh cục bộ giữ tắt. Mỗi cặp giữ cùng trạng thái kiến thức thật ban đầu, lịch thời gian và dòng số ngẫu nhiên. Lượt mở rộng có 18 ca mới, tương ứng ba khối ngẫu nhiên, ba mức năng lực và hai mức phạt thiếu nền tảng. Trước đó, một ca đối chứng cũ được chạy lại và khớp đủ 120 lượt cùng trạng thái cuối.

Để đánh giá học thêm được bao nhiêu, nhóm đo mức tăng ròng của kiến thức ẩn trung bình trên 28 khái niệm ở cuối lịch 41 ngày, trên thang Elo của simulator. Đây là đầu ra học tập của thế giới mô phỏng. Các thước đo dự báo đáp án như Log Loss vẫn có vai trò riêng ở bước đánh giá mô hình ước lượng.

Kết quả cho thấy cả 18 cặp chuyên gia–đồ thị học đều có chuỗi câu hỏi khác nhau. Tổng cộng 1.409 trong 2.160 vị trí thứ tự dùng câu hỏi khác, trong đó nhóm năng lực 1300 có 600 trong 720 vị trí. Sau khi đường đi phân kỳ, cùng vị trí thứ tự có thể là hai bài khác nhau, nên cần đọc chênh lệch học tập trong bối cảnh hai lộ trình đã khác.

Ở nhóm năng lực 1300, mô phỏng xác nhận thiếu hụt tiên quyết bằng 0 trong toàn bộ các lượt mới. Với từng đồ thị, bật mức phạt từ 0 lên 0,55 giữ nguyên cả lịch sử và trạng thái cuối. Tuy vậy, khi đổi nguồn đồ thị, mức tăng kiến thức vẫn khác. Chênh lệch giữa hai đồ thị ở ba khối lần lượt là −0,197266, +0,181461 và +0,076440 Elo, và giữ nguyên khi bật mức phạt. Như vậy, chênh lệch tổng thể còn có thể xuất hiện qua đường ước lượng và chọn bài khi cơ chế phạt thiếu nền tảng đang bất hoạt.

Nhóm lấy mức tăng của cấu hình chuyên gia trừ cấu hình đồ thị học, rồi kiểm chênh lệch đó thay đổi bao nhiêu khi bật mức phạt. Bảng dưới giữ đầy đủ ba khối. Ở mức năng lực 1150, cả ba thay đổi đều âm. Ở mức 1000, dấu thay đổi trái chiều giữa các khối. Ở mức 1300, cả ba bằng 0 theo đối chứng bất hoạt đã kiểm. Các mức năng lực này là can thiệp vào trạng thái ban đầu trong mô phỏng.

| Khối | Chuyên gia − đồ thị học ở năng lực 1300 | Thay đổi khi bật phạt, năng lực 1000 | Thay đổi khi bật phạt, năng lực 1150 | Thay đổi khi bật phạt, năng lực 1300 |
| --- | --- | --- | --- | --- |
| 1 | -0.197266 | -0.017810 | -0.035150 | +0.000000 |
| 2 | +0.181461 | -0.016087 | -0.038274 | +0.000000 |
| 3 | +0.076440 | +0.029300 | -0.036009 | +0.000000 |

Giá trị âm ở cột chênh lệch nghĩa là cấu hình đồ thị học có mức tăng lớn hơn. Ba cột cuối là chênh lệch tại mức phạt 0,55 trừ chênh lệch tại mức phạt 0. Các giá trị chỉ mô tả những trường hợp đã khảo sát.

Phần mở rộng đã tách thêm được nguồn đồ thị của bộ ước lượng khỏi đồ thị thế giới và bộ điều khiển, đồng thời xác định một chênh lệch vẫn tồn tại khi cơ chế thiếu tiên quyết bất hoạt. Ba khối được dùng lại từ chẩn đoán trước, nên chưa tăng số khối độc lập. Điều kiện cũ được tái dựng từ nguồn và kiểm khớp qua một ca đối chứng đầy đủ. Khả năng khái quát sang người học mới, mức nhiễu khác và chất lượng đồ thị tiên quyết còn cần đánh giá tiếp. Kết quả hiện tại chưa xác lập thứ hạng chung giữa đồ thị chuyên gia và đồ thị học.


## Chặng 14. Đối chiếu thành thạo cần kiểm soát cả cách chọn bài

Paper2 dùng dự báo đáp án để cập nhật trạng thái kiến thức, rồi dựa vào trạng thái đó để quyết định khái niệm nào đã thành thạo. Sau các phép kiểm đường đi, nhóm quay lại câu hỏi nền của RQ1. Quyết định thành thạo có phản ánh trạng thái thật trong simulator tại các câu đang được giao hay không?

Nhóm dùng lại nhật ký đã kiểm của một lịch sử thuộc hồ sơ năng lực cao PG, gồm 120 lượt hỏi trước khi cập nhật bằng đáp án hiện tại. Hai đường đưa tín hiệu và điều chỉnh theo cha vào bộ ước lượng được tắt, điều chỉnh cục bộ được tắt. Bộ chọn bài vẫn giữ đồ thị tiên quyết. Cơ chế phạt do thiếu tiên quyết trong thế giới mô phỏng được tắt. Các bản ghi được ghép chính xác theo câu hỏi, khái niệm, dự báo và lịch thời gian với trạng thái thật đã lưu của simulator.

Theo quy tắc Paper2, mô hình công nhận thành thạo khi điểm kiến thức ước lượng đạt 1250 và điều kiện về bất định cùng đạt. Phép đối chiếu dùng tiêu chí latent của simulator tại cùng ngưỡng 1250. Trong cả 120 lượt hỏi trên 22 khái niệm riêng biệt, khái niệm đang hỏi đều đạt tiêu chí latent, trong khi điểm ước lượng ở những thời điểm đó đều dưới ngưỡng. Số lượt có điểm ước lượng đạt để xét vai trò chặn bổ sung của điều kiện bất định bằng 0.

| Đánh giá của mô hình tại câu được hỏi | Simulator chưa đạt ngưỡng | Simulator đạt ngưỡng |
|---|---:|---:|
| Chưa công nhận thành thạo | 0 | 120 |
| Công nhận thành thạo | 0 | 0 |

Bảng cần được đọc cùng cách chọn bài. Bộ chọn ưu tiên khái niệm mà mô hình đang đánh giá chưa thành thạo, rồi ưu tiên điểm thành thạo thấp trong các ứng viên. Vì vậy những trạng thái xuất hiện ở câu được giao đã chịu ảnh hưởng của chính mô hình và chính sách. Bộ chọn còn có nhánh ôn tập và nhánh khi mọi khái niệm đã thành thạo, nên kết quả điểm ước lượng dưới ngưỡng ở cả 120 lượt vẫn là một quan sát của lịch sử này.

Kiểm lần thực hành đầu tiên cho thấy cả 22 khái niệm được phục vụ đã đạt tiêu chí latent ngay từ lần đầu xuất hiện. Mô hình bắt đầu với điểm ước lượng 1200. Trong cơ chế hiện tại, trạng thái thật chỉ nhận mức tăng không âm và quên dần về mức nền, nên các khái niệm có mức nền đã đạt ngưỡng tiếp tục thuộc lớp đạt ngưỡng. Phép kiểm này vì thế chưa quan sát một lần chuyển từ chưa đạt sang đạt của thế giới mô phỏng. Trạng thái của sáu khái niệm còn lại cần bằng chứng riêng.

Phát hiện bổ sung cho RQ1 là cần kiểm soát quần thể khi đánh giá trạng thái kiến thức. Một bảng chỉ gồm các câu do chính hệ thống chọn chưa đủ để đánh giá chất lượng toàn bộ trạng thái. Vai trò riêng của điều kiện bất định cũng còn cần các trường hợp điểm kiến thức đã đạt. Bước kiểm tiếp theo được đề xuất là một tập khái niệm và thời điểm định trước, độc lập với quyết định chọn bài, có cả trạng thái mô hình lẫn trạng thái thật tương ứng. Thiết kế đó còn cần được chốt trong hợp đồng thực nghiệm chính.

Kết quả hiện tại là một lịch sử dùng lại, với 120 thời điểm có tương quan. Nó bổ sung chẩn đoán về cách đo và ảnh hưởng của năng lực ban đầu. So sánh giữa các đồ thị, hiệu chỉnh xác suất, thay đổi kết quả học và khả năng khái quát sang nhiều người học vẫn là những phần còn thiếu.


## Chặng 15. Kiểm lại đối chứng đồ thị trên mười khối mô phỏng mới

Ba khối trước cho thấy thay đồ thị trong bộ ước lượng có thể đổi đường đi ngay cả khi cơ chế phạt thiếu tiên quyết không hoạt động. Tuy nhiên, ba trường hợp còn ít và dùng lại trạng thái cũ. Nhóm tiếp tục một phép kiểm với mười khối khởi tạo mới đã định trước, giữ cùng trạng thái ban đầu và cùng chuỗi số ngẫu nhiên trong từng cặp so sánh.

Mỗi khối có ba mức khởi tạo 1000, 1150, 1300, hai nguồn đồ thị và hai mức cơ chế phạt. Tổng cộng 120 ca, mỗi ca 120 lượt, đã hoàn tất. Đồ thị trong môi trường và bộ chọn bài giữ nguyên. Chỉ nguồn đồ thị trong bộ ước lượng thay giữa đồ thị chuyên gia và một đồ thị 31 cạnh được ước lượng từ dữ liệu huấn luyện. Hai đường tín hiệu và điều chỉnh theo cha cùng bật, điều chỉnh cục bộ tắt. Đây là một đồ thị học được cố định, chưa đại diện cho mọi đồ thị học từ dữ liệu.

Để biết chênh lệch giữa hai đồ thị có thực sự đi qua cơ chế phạt hay không, trước hết lấy mức tăng kiến thức trung bình của đồ thị chuyên gia trừ đồ thị học được. Sau đó đối chiếu chênh lệch này giữa lúc bật và lúc tắt cơ chế phạt. Đại lượng thu được diễn tả phần thay đổi của chênh lệch khi cơ chế được bật, theo thang Elo của simulator.

| Mức khởi tạo | Trung bình | Khoảng quan sát | Số block dương / âm / bằng 0 |
|---|---:|---|---|
| 1000 | +0.004496 | -0.069250 đến +0.095294 | 6 / 4 / 0 |
| 1150 | +0.024530 | -0.004716 đến +0.079790 | 8 / 2 / 0 |
| 1300 | +0.000000 | +0.000000 đến +0.000000 | 0 / 0 / 10 |

Ở mức 1000 và 1150, phần thay đổi có cả dấu dương lẫn âm giữa các khối. Trung bình dương vẫn cần được đọc cùng những trường hợp âm và độ phân tán. Chặng này ghi thống kê mô tả trên mười khối. Phần tiếp theo bổ sung khoảng thăm dò theo khối và các giới hạn của cách diễn giải.

Ở mức 1300, phần thay đổi bằng 0 trong cả mười khối. Đây là đối chứng bất hoạt đã được dự kiến từ điều kiện của simulator. Đồng thời, chênh lệch trực tiếp giữa hai đồ thị vẫn khác 0 và có cả hai dấu. Vì vậy, khác biệt do đổi nguồn đồ thị còn có thể đi qua các đường khác ngoài riêng cơ chế phạt thiếu tiên quyết. Kết quả chưa tách riêng vai trò của tín hiệu đồ thị, điều chỉnh theo cha và mức thử thách của câu được chọn.

Cả 60 cặp so sánh đổi chuỗi câu hỏi, với 4936/7200 vị trí khác câu. Sau khi đường đi phân kỳ, cùng số thứ tự không bảo đảm cùng câu và cùng lịch sử, nên chưa dùng những vị trí này để so sai số dự báo trên cùng targets.

Phép kiểm mới củng cố chẩn đoán cần tách nguồn đồ thị, năng lực khởi tạo và cơ chế môi trường. Nó cũng cho thấy dấu hiệu ở ba khối cũ chưa đủ để khái quát. Phần còn thiếu là thống kê theo đơn vị khối, khảo sát thêm chất lượng đồ thị và các so sánh chính của mô hình mới. Chưa RQ nào hoàn tất.


## Tiếp theo, kiểm độ bất định của xu hướng giữa các khối mô phỏng

Sau khi hoàn tất mười khối mới, câu hỏi tiếp theo là trung bình dương có còn đủ rõ khi xét sự biến động giữa các khối hay không. Nhóm dùng lại đúng dữ liệu của Chặng 15, lấy mẫu lại toàn bộ khối để giữ các điều kiện so sánh đi cùng nhau. Có 10.000 lần lấy mẫu lại, nhưng số khối độc lập vẫn là mười và không có lượt mô phỏng mới.

Ba so sánh được xét cùng nhau gồm phần thay đổi khi bật cơ chế phạt ở mức khởi tạo 1000, ở mức 1150, và hiệu của hai phần thay đổi trong cùng khối. So sánh thứ ba là bước cần thiết để hỏi tác động có khác giữa hai mức khởi tạo hay không. Việc một khoảng chứa 0 còn khoảng kia không chứa 0 tự nó chưa trả lời được câu hỏi này.

| So sánh | Trung bình | Khoảng thăm dò đã điều chỉnh |
|---|---:|---|
| Mức khởi tạo 1000 | +0.004496 | -0.024649 đến +0.035327 |
| Mức khởi tạo 1150 | +0.024530 | +0.005767 đến +0.047248 |
| Chênh lệch 1150 trừ 1000 trong cùng khối | +0.020034 | -0.021413 đến +0.058529 |

Ở mức 1000, khoảng thăm dò còn chứa cả giá trị âm và dương. Ở mức 1150, khoảng nằm phía dương trong phép phân tích này. Tuy nhiên, khoảng của chênh lệch giữa hai mức vẫn chứa 0. Vì vậy dữ liệu hiện có chưa phân biệt rõ tác động giữa hai mức khởi tạo, dù các trung bình khác nhau.

Phân tích được bổ sung sau khi đã xem kết quả nên giữ nhãn thăm dò. Các khoảng đã điều chỉnh cho ba so sánh, với mức danh nghĩa 98,33% cho từng khoảng và mức đồng thời danh nghĩa 95%. Đây là xấp xỉ bootstrap trên mười khối, không bảo đảm mức bao phủ chính xác. Lấy mẫu lại nhiều lần không khắc phục được số khối còn ít.

Đã lượng hóa thêm độ bất định và kiểm độc lập các phép tính. Phạm vi vẫn là một đồ thị học được cố định và các giả định của simulator. Đối chứng 1300 bằng 0 theo cơ chế tiếp tục được giữ riêng, không dùng làm bằng chứng thống kê về năng lực. Còn phải khảo sát đồ thị nhiễu, độ ổn định qua các nguồn đồ thị khác và các so sánh CG-AKT đã huấn luyện.


## Tiếp theo, quan sát toàn bộ trạng thái để thấy điều nhật ký câu hỏi bỏ sót

Chặng 14 đã đặt ra giới hạn của việc chỉ đối chiếu khái niệm đang được giao bài. Một câu hỏi tiếp theo là mô hình có công nhận thành thạo ở những khái niệm không được hỏi lúc đó hay không, và các công nhận ấy có đúng với trạng thái thật của simulator hay không. Nếu thiếu phần quan sát này, nhật ký bài làm có thể che cả đánh giá đúng lẫn đánh giá sai của hệ thống.

Nhóm giữ cùng một cấu hình GAM kế thừa và đồ thị chuyên gia, tắt cơ chế phạt thiếu tiên quyết trong thế giới mô phỏng, rồi kiểm ba mức kiến thức nền 1000, 1150 và 1300 trong cùng một khối khởi tạo. Các lịch sử này khác quần thể của Chặng 14. Tại mỗi thời điểm trong 120 bước, nhóm ghi đủ 28 khái niệm từ các lần đọc trạng thái vốn có của bộ chọn bài. Lựa chọn, dự báo và trạng thái cuối phải khớp lịch sử gốc trước khi đối chiếu với trạng thái thật được dựng lại từ trạng thái khởi tạo và các cập nhật đã lưu.

Mỗi mức có 3360 lần đo khái niệm–thời điểm, trong đó 120 lần thuộc khái niệm đang được hỏi và 3240 lần thuộc các khái niệm còn lại. Ba lịch sử cùng thuộc một khối ngẫu nhiên. Số lần đo lặp không được xem là số người học hoặc số khối độc lập. Bảng dưới đối chiếu quyết định thành thạo với tiêu chí trạng thái ẩn ở ngưỡng 1250 của simulator.

| Mức nền | Trạng thái thật đạt ngưỡng | Mô hình công nhận | Công nhận tại câu đang hỏi |
|---|---|---|---|
| 1000 | 0 | 0 | 0 |
| 1150 | 1 | 5 | 0 |
| 1300 | 3023 | 215 | 0 |

Ở mức 1300, mô hình công nhận đúng 215 lần đo trạng thái, toàn bộ ở các khái niệm không được hỏi lúc đó. Nhật ký chỉ gồm khái niệm đang được giao bài sẽ không cho thấy những công nhận đúng này. Ở mức 1150, năm lần công nhận thành thạo đều là công nhận nhầm và cũng nằm ngoài khái niệm đang được hỏi. Chỉ nhìn 120 lần hỏi của mức này sẽ thấy toàn trường hợp chưa đạt được đánh giá chưa đạt, nhưng bỏ sót cả năm công nhận nhầm trong trạng thái còn lại.

| Mức nền | Công nhận đúng ngoài câu đang hỏi | Công nhận nhầm ngoài câu đang hỏi |
|---|---|---|
| 1000 | 0 | 0 |
| 1150 | 0 | 5 |
| 1300 | 215 | 0 |

Phát hiện mới là phạm vi quan sát làm thay đổi điều có thể kết luận về mô hình. Không thể từ việc chưa thấy công nhận thành thạo ở câu được giao suy ra mô hình chưa công nhận bất kỳ khái niệm nào. Đồng thời, một bảng chỉ có các trường hợp chưa đạt cũng chưa kiểm được khả năng nhận diện trạng thái đã đạt. Kết quả phù hợp với quy tắc ưu tiên các khái niệm chưa được mô hình công nhận trong bộ chọn bài, nhưng chưa định lượng tác động của quy tắc đó lên kết quả học.

Nhóm còn kiểm được điều kiện bất định ở những thời điểm điểm kiến thức ước lượng đã đạt ngưỡng. Có 220 cơ hội như vậy trong cả ba lịch sử, nhưng điều kiện bất định không chặn công nhận thành thạo lần nào. Đây là quan sát có điều kiện trong cửa sổ 120 bước của cấu hình đang kiểm. Chưa thể suy điều kiện bất định luôn dư thừa ở mọi hồ sơ hoặc thời gian học.

Mô hình bắt đầu với điểm ước lượng 1200, còn trạng thái nền của simulator được thay giữa ba mức. Vì vậy, khởi tạo và độ dài lịch sử phải được đọc cùng các chênh lệch thành thạo. Phép kiểm mới tạo được phản ví dụ rõ về giới hạn của nhật ký câu hỏi và nối RQ1 với điều kiện người học trong RQ2. Nó chưa là so sánh đồ thị, bằng chứng CG-AKT cải thiện hoặc kết luận trên người học thật. Phần tiếp theo cần kiểm nhiều khối độc lập và nối các chẩn đoán với so sánh mô hình đã huấn luyện.

## Còn phải chứng minh

- **RQ1** đã có đối chiếu đủ 28 khái niệm tại mỗi bước trên ba lịch sử cùng một khối. Cần kiểm độ phổ biến qua nhiều khối độc lập, hiệu chỉnh xác suất và nối với kết quả học tập trong các so sánh mô hình.
- **RQ2:** kiểm khả năng khái quát qua đồ thị nhiễu, nhóm khái niệm và người học mới, với đối chứng đúng quần thể.
- **RQ3:** mở rộng từ quy trình chọn checkpoint AKT đã kiểm sang Linux/CUDA và corpus nghiên cứu, hoàn thiện huấn luyện lại và hiệu chỉnh; so sánh không đồ thị / đồ thị cố định / confidence / gate cùng các baseline bắt buộc, rồi đánh giá chọn bài và kết quả học vòng kín.

Các mô hình và demo trong đề cương vẫn được giữ. Kết quả không cải thiện hoặc cổng chọn tắt đồ thị vẫn được báo cáo nếu bằng chứng hỗ trợ; chưa có kết luận ưu thế của CG-AKT hoặc hiệu quả giáo dục trên người học thật.

## Cập nhật kỹ thuật ngày 10/11 — AKT chạy được trên Colab CPU

Đã chuyển các lượt kiểm AKT tốn RAM sang Colab CPU. Bảy nhóm kiểm baseline đạt 67 ca và bốn nhóm kiểm phần đồ thị đạt 113 ca, không lỗi hoặc bỏ qua. Đã lưu log cùng kết quả từng ca về repository. Mốc này xác nhận mã hiện hành chạy được trên môi trường Linux CPU đã ghi nhận, còn bộ kiểm toàn nguồn, CUDA và huấn luyện nghiên cứu vẫn cần hoàn tất.

## Cập nhật tích hợp AKT ngày 10/11

Đã nối thêm checkpoint nghiên cứu của AKT không đồ thị vào luồng dự báo tuần tự. Lượt kiểm trên Colab đạt 22 ca, gồm 12 ca mới và 10 ca hồi quy. Trên dữ liệu giả nhỏ, sáu dự báo khớp bản nghiên cứu trong sai số đã đặt và việc nạp mô hình giữ nguyên luồng ngẫu nhiên của mô phỏng. Lượt đầu dùng fixture thu nhỏ sai cấu hình đã chốt nên bị chặn; đã sửa fixture và giữ log lỗi. Mốc này hoàn thiện một phần tích hợp AKT, còn mô hình cuối sau refit, hiệu chỉnh và kết quả vòng kín chính cần tiếp tục.

## Cập nhật kiểm tích hợp AKT ngày 10/11

Bộ kiểm tích hợp AKT trên Colab CPU đã đạt 1.992 ca qua ba tiến trình độc lập, không lỗi hoặc bỏ qua. Các lượt kiểm đã tìm và xử lý phần đóng gói thiếu cấu hình, phụ thuộc một snapshot cũ chưa được Git lưu và giả định timestamp của filesystem. Có một ca yêu cầu môi trường thư viện cô lập được tách riêng vì phiên này kế thừa thư viện Colab. Đã lưu cả log lỗi và JUnit lượt đạt. Mốc này tăng độ tin cậy trước khi dùng GPU; môi trường đúng phiên bản, CUDA, phục hồi và đo chi phí vẫn cần hoàn tất. Lượt điều phối thứ hai thiếu thư mục cha vùng tạm; đã sửa và giữ log.
