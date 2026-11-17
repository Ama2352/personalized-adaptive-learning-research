# Rà phạm vi và tính đúng của kết quả · 18/11/2026

## Kết luận vận hành

Mục tiêu nghiệm thu là có phép so sánh hợp lệ, đủ bằng chứng trả lời ba RQ và báo cáo được giới hạn. Kết quả âm hoặc bất định là đầu ra nghiên cứu được chấp nhận. Chỉ thị mới của người dùng xác nhận ưu tiên này. A0–A3 và ba bẫy đánh giá vẫn gắn trực tiếp với đề cương. Chặng tối ưu tài nguyên, phục hồi và quản lý file đã chiếm nhiều đầu việc trong khi bằng chứng quyết định/vòng kín còn thiếu; cần chuyển ưu tiên sang khép những phép kiểm đó.

Người dùng làm rõ thêm rằng kết luận RQ dựa trên mức độ bằng chứng có độ tin cậy và giới hạn cụ thể. Các mức kết luận có thể là hỗ trợ trong một điều kiện, hỗ trợ một phần, chưa phát hiện khác biệt rõ hoặc thiếu bằng chứng để phân biệt các giải thích. Độ lớn hiệu ứng, bất định, cơ chế và đối chứng được trình bày cùng nhau. Tránh quy RQ thành một nhãn nhị phân hoặc lấy p-value riêng lẻ làm toàn bộ kết luận.

Hiện tại đang kiểm kê, sao lưu và bàn giao đầu ra đã có. Lượt này chưa fit lại, thay siêu tham số, chọn seed mới hoặc chạy GPU. Hai tiến trình truyền/kiểm Drive chỉ xử lý artifact nguyên byte.

## Căn cứ phạm vi

- Đề cương, trang2–5, bản trích `docs/thesis_recovery/evidence/proposal.txt`. Các yêu cầu gồm AKT/CG-AKT và đối chứng SAKT/GKT/GAM/Graph-GAM/BKT, hai môi trường Junyi/Grade10, đồ thị chuyên gia/học/nhiễu, dự báo–calibration–quyết định–vòng kín, thống kê và demo.
- Góp ý GVHD do người dùng cung cấp nguyên văn. RQ1/RQ2 tập trung ba bẫy; RQ3 tối giản và đánh giá chủ yếu trong mô phỏng biết cạnh thật/nhiễu. Gate tắt vẫn là kết quả hợp lệ.
- Protocol21 và Recipe26 là lựa chọn triển khai đã adopt của nhóm. Đề cương chưa ấn định tích đầy đủ mọi model×graph×environment, sốepoch hoặc CV5 cho mọi model. Ma trận21phase còn lại thuộc protocol nhóm hiện hành; số này cần được đọc cùng quyền điều chỉnh phạm vi phương pháp, và chưa phải định lượng khối lượng bắt buộc nguyên văn trong đề cương.
- Hồ sơ `TRAINING_SCOPE_RECONCILIATION_20261115.md` đã đề xuất cân nhắc hoãn6phase learnedJunyi. Đề xuất chưa được áp dụng. Lượt kiểm này giữ đầy đủ chúng trong danh mục, đồng thời ghi đúng địa vị của quyết định triển khai.

## Kiểm lại từng nhóm việc

| Nhóm việc | Vai trò đối với KLTN | Xử lý ưu tiên |
|---|---|---|
| Bảo toàn model, cấu hình, prediction, figure và chỉ mục bàn giao | Tái lập và hoàn thành báo cáo | Hoàn tất gói đang truyền; giữ archive lịch sử đã có trên Drive bằng liên kết |
| Junyi expert A0–A3 fit/refit/calibration/outer đã nghiệm thu | Bằng chứng dự báo cho RQ1/RQ3 | Giữ nguyên kết quả và checkpoint hiện tại để phân tích/báo cáo |
| Grade10 model/adapter/controller/calibration và vòng kín có ghép cặp | Trực tiếp trả lời RQ1/RQ3 về quyết định và kết quả học | Critical path nghiên cứu tiếp theo; khóa đối chứng, metrics và quy tắc dừng trước xem outcome |
| Khép ba bẫy với dữ liệu đã lưu và bổ sung control còn thiếu | Trực tiếp trả lời RQ1/RQ2 | Tái dùng artifact, chỉ bổ sung phép kiểm có câu hỏi còn mở cụ thể |
| SAKT/GKT và matched GAM/Graph-GAM | Đối chứng có trong đề cương | Giữ nhiệm vụ; lượt engineering nhỏ chưa thay được model nghiên cứu |
| Sáu phase Junyi learned A1–A3 | Kiểm phụ thuộc nguồn đồ thị trong ma trận đã adopt | Theo dõi riêng, chưa tự bỏ. Trước phân bổ GPU tiếp cần chốt giá trị bổ sung so với learned/noise Grade10 và phạm vi kết luận |
| Tối ưu GPU thêm sau khi pipeline đã chạy và giữ đúng semantics | Giảm chi phí trong giới hạn ngân sách | Chỉ mở khi dự toán lượt cần thiết vượt ngân sách/thời gian. Ngưỡng utilization tùy ý chưa là tiêu chí nghiệm thu nghiên cứu |
| Thêm dataset, model, seed sweep, full nested CV hoặc sản phẩm LMS | Mở rộng vượt gói cốt lõi hiện hành | Đưa vào đề xuất riêng nếu có câu hỏi/budget được duyệt; ưu tiên hiện tại là báo cáo KLTN |

## Có đang chọn số liệu để đạt kết quả đẹp?

Hồ sơ đã đọc cho thấy selected-fit chọn epoch trên selection, refit khóa9epoch cho cả bốn điều kiện expert, confidence giữ TRAIN80 xuyên refit, calibration dùng calibration10 riêng. `epoch-plan.json` ghi `system_winner_selected=false`. Các mốc này có cơ sở để phân biệt lựa chọn model theo development hợp lệ với lựa chọn theo kết quả outer đã xem. Đây là rà các hồ sơ nghiệm thu chính; chưa phải chứng nhận đầy đủ mọi thao tác ở toàn bộ lịch sử repository.

Outer hiện đã xem. Mọi sửa thiết kế sau mốc này cần ghi là hậu kiểm/thăm dò và nêu lý do. Sửa lỗi kỹ thuật cần giữ bản cũ, định vị tác động và áp dụng nhất quán cho các điều kiện bị ảnh hưởng. Ngưỡng mastery, graph/confidence, seed và outcome cần khóa trước phép đánh giá tiếp theo. Một kết quả mới đẹp hơn chưa tự cung cấp lý do thay kết quả cũ.

Nghiệm thu một thí nghiệm dựa vào population/split đúng, dự đoán trước cập nhật, artifact đủ, metric đã chỉ định, bất định/đối chứng phù hợp và diễn giải tương xứng. Dấu của hiệu ứng và p-value quan sát được là kết quả cần báo cáo.

## Kết luận hiện tại được phép viết

Junyi outerfold4, một trainingseed, cùng39.616người học và4.137.050target mỗi model,144OOV giữ null. A3 soA0 sau calibration có ΔLogLoss≈−0,000020, CI95%≈[−0,000044;+0,0000047]. So sánh LogLoss/Brier của ba graph variants vớiA0 chưa có ý nghĩa sau Holm. Bằng chứng hiện tại cho thấy mức chênh lệch dự báo nhỏ và chưa phát hiện ưu thế rõ sau calibration trong điều kiện đã kiểm.

Chưa đủ để kết luận các model tương đương, đồ thị luôn vô ích, gate cải thiện học tập hoặc xác suất chưa calibration là nguyên nhân duy nhất. Calibration toàn cục cũng chưa thay phép đo riêng quanh ngưỡng mastery. Phần quyết định/vòng kín còn cần phép kiểm trực tiếp. Đây là các câu hỏi nghiên cứu còn mở, có thể trả lời bằng hiệu ứng dương, âm hoặc bất định.

## Giới hạn cần hiện rõ trong bàn giao và báo cáo

1. Family thống kê24phép được khóa sau inference nhưng trước xem metric outer. `STATISTICAL_PLAN_TIMING01.json` ghi chưa có metrics tại thời điểm khóa. Báo exploratory có điều kiện; chưa gọi đây là thiết kế tiền đăng ký.
2. A0 selection dùng validation batch1 lịch sử; đã replay bestepoch9 bằng batch128, chưa kiểm lại ranking toàn12epoch. Chênh lệch rất nhỏ cần diễn giải cùng giới hạn này. Giữ model đã chọn khi báo cáo hiện tại.
3. A3 refit đã nối nhiều loạiGPU; artifact/progress được kiểm, chưa chứng minh bitwise-equivalence xuyên phần cứng. Ghi mixed hardware trong tái lập.
4. BKT/GAM CV5 lịch sử có protocol/trainpopulation khác bảng AKTouter hiện hành. Bảng tham chiếu phải tách rõ, matched comparison cần cùng giới hạn thông tin.
5. Pilot chọn num_fits BKT đã sử dụng fold0 rồi fold0 được dùng lại trong CV. Giữ kết quả lịch sử với giới hạn selectionbias.
6. ConfidenceTRAIN80 là predictive-stability score của surrogate; oracle edge truth chỉ hợp lệ ở control mô phỏng có nhãn rõ. LogJunyi có thứ tự luyện liên quan knowledge map, nên lợi ích dự báo quan sát chưa xác lập hiệu quả dạy học nhân quả.

## Quyết định sau kiểm

Giữ kết quả outer hiện hành và công bố kết luận âm/bất định cùng giới hạn. Hoàn tất bàn giao đã được yêu cầu, sau đó ưu tiên bộ bằng chứng tối thiểu cho ngưỡng/mastery, lựa chọn và vòng kín cùng các đối chứng đề cương. Mỗi lượt training bổ sung cần chỉ rõ câu hỏi còn thiếu và đầu ra sẽ sử dụng trong luận văn. Phạm vi21phase hiện hành được bảo toàn trong backlog; gói hiện tại chưa cấp quyền tự chạy toàn bộ hoặc tự lược bỏ các nhánh đó.

Nguồn kiểm trực tiếp gồm `junyi-outer-real-20261117-01/OUTER_COMPARISON01.json`, `STATISTICAL_PLAN_TIMING01.json`, `STATE.json`; `junyi-refit-pipeline-20261114-01/epoch-plan.json`; `TRAINING_RQ_SCOPE_REVIEW_20261116.md`; `TRAINING_SCOPE_RECONCILIATION_20261115.md` và các MODEL_INDEX trong inventory bàn giao.
