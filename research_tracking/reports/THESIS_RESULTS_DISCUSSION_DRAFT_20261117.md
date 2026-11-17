# Kết quả và thảo luận về vai trò của đồ thị tiên quyết

Bản thảo ngày 17/11/2026, tổng hợp kết quả lịch sử, chẩn đoán và đánh giá mô hình. [Đề cương, trang 2–5](../../paper2/DC%20KLTN0127%2023520355%2623521338_LeVanTuan.pdf)

## 1. Từ hai nghiên cứu trước đến vấn đề của khóa luận

Hệ thống học thích ứng ước lượng tri thức, xác định nội dung đủ điều kiện và chọn hoạt động tiếp theo. Khóa luận theo dõi ảnh hưởng của đồ thị qua dự báo, quyết định thành thạo, tập đủ điều kiện, lựa chọn và kết quả học. Mỗi tầng cần bằng chứng riêng. [Đề cương, trang 2–4](../../paper2/DC%20KLTN0127%2023520355%2623521338_LeVanTuan.pdf)

Paper1 nghiên cứu mô phỏng Toán lớp 10 với 28 khái niệm. Ở hồ sơ năng lực thấp và yếu hàm số, các cấu hình đồ thị giảm số lần chuyển chương trung bình từ 11 xuống 2, số lần quay lại chương từ 9 xuống 0. Tuy nhiên, đồ thị mở rộng chưa tạo ưu thế thành thạo nhất quán so với đồ thị nội chương. Phân tích loại bỏ thành phần cho thấy chính sách giữ tính liên tục có vai trò quan trọng. PDF Paper1 cung cấp nền kết quả lịch sử cho phần thảo luận này. [Paper1](../../paper1/Paper1_RIVF_2026_Graph_vs_Policy_Adaptive_Sequencing.pdf)

Paper2 so mô hình trên cùng luồng rồi xét vòng kín. Nhóm đã chạy lại hàm thống kê gốc trên outcome theo seed, gồm trung bình, chênh lệch, Wilcoxon, bootstrap 3.000 lần và Holm; cả 117 phép so sánh khớp số lịch sử. Môi trường hiện hành tái lập chính xác số liệu; phiên bản thư viện lịch sử còn thiếu hồ sơ xác nhận. [Kết quả tái lập thống kê](../runs/paper2-statistical-reproduction-20261117-02/attempt01/RESULT.json)

Để biết dự báo có đáng tin hơn hay không, Paper2 dùng Log Loss, chỉ tiêu phạt xác suất tự tin nhưng dự báo sai. Gói Graph-GAM-KT giảm Log Loss so với GAM-KT khoảng 0,003195 ở hồ sơ thấp và 0,001692 ở hồ sơ yếu hàm số, đạt tiêu chí Holm của nhóm so sánh dự báo. Hai chỉ tiêu học tập chính, gồm tăng kiến thức mỗi bước và tăng kiến thức giữ lại sau 14 ngày, vẫn chưa đạt tiêu chí Holm ở cả ba hồ sơ. Sự tách rời ấy là động cơ trực tiếp của RQ1. [Bảng contrast đã đối chiếu](../runs/paper2-statistical-reproduction-20261117-01/PRIMARY_PACKAGE_CONTRAST.csv)

*Hình 1. Chênh lệch dự báo và kết quả học trong Paper2. Đọc ba phần cùng nhau để thấy cải thiện dự báo ở một số hồ sơ còn thiếu bằng chứng tương ứng ở kết quả vòng kín. Đơn vị và độ bất định giữ theo nghiên cứu lịch sử.* [SVG và nguồn dựng lại](../runs/paper2-statistical-reproduction-20261117-01/paper2-prediction-outcome-v01.svg)

## 2. RQ1 — ảnh hưởng của đồ thị bị suy giảm ở đâu?

### 2.1. Phân biệt ảnh hưởng của đồ thị và quy tắc điều khiển

Nhóm kiểm trực tiếp điều kiện để kết quả quay lại chương bằng không xuất hiện. Khi quan hệ chỉ nằm trong chương, đồ thị không có chu trình, mastery đã đạt được giữ nguyên và controller tiếp tục chương hiện tại khi còn hoạt động hợp lệ, mỗi chương tạo thành một đoạn liên tiếp. Bốn tình huống dựng tay kiểm đúng cơ chế và cho phản ví dụ quay lại chương khi có quan hệ liên chương. Kết quả trả lời một phần RQ1 bằng cách xác định chỉ tiêu lộ trình có thể được quy tắc bảo đảm trước khi xét chất lượng dự báo. [Chứng minh, giả thiết và phản ví dụ](paper1_reentry_mechanism_20261109.md)

Một phân tích khác cho thấy, dưới chuyển trạng thái chỉ phụ thuộc khái niệm đang luyện và cùng nguồn ngẫu nhiên ghép theo khái niệm, các nhánh cùng hoàn tất có thể đạt trạng thái cuối giống nhau dù đổi thứ tự. Phạm vi kết luận phụ thuộc điều kiện hoàn tất và cấu trúc chuyển trạng thái. Thời hạn hữu hạn hoặc tương tác giữa khái niệm cần được xét riêng khi diễn giải ảnh hưởng của lộ trình. [Phân tích bất biến concept-local](paper1_concept_local_invariance_20261109.md)

### 2.2. Dự báo thay đổi có dẫn đến gợi ý khác?

Nhóm dùng pilot cùng lịch sử để quan sát xác suất, nhãn thành thạo, tập chủ đề đủ điều kiện và gợi ý tại từng trạng thái. Mục tiêu của các số đếm là tìm bước ảnh hưởng bị giữ lại bởi controller. Trong 1.080 cặp trạng thái, gói đồ thị làm thay đổi xác suất câu đang xét ở 964 cặp, nhãn thành thạo ở 90 cặp, tập đủ điều kiện ở 60 cặp và gợi ý ở 22 cặp. Các tập thay đổi được đối chiếu từng dòng. [Kiểm số đếm và giới hạn pilot](RQ12_EXISTING_EVIDENCE_20261117.md)

| Tập chủ đề đủ điều kiện | Gợi ý thay đổi | Gợi ý giữ nguyên | Tổng |
|---|---:|---:|---:|
| Có thay đổi | 5 | 55 | 60 |
| Giữ nguyên | 17 | 1.003 | 1.020 |

Trong 60 trường hợp tập đủ điều kiện thay đổi, 55 trường hợp vẫn giữ gợi ý. Đồng thời, 17 trường hợp thay gợi ý giữ nguyên tập đủ điều kiện. Điều này phù hợp với việc bộ chọn bài còn sử dụng điểm số và các quy tắc xếp hạng khác. Bảng chéo cho thấy quan hệ đồng biến trong pilot, còn phần tác động nhân quả của từng thành phần vẫn cần đối chứng. [Dữ liệu bảng chéo](../runs/rq12-existing-evidence-20261117-01/rq1_conditionals.csv)

*Hình 2. Bảng chéo tập đủ điều kiện và gợi ý preview. Pilot có ba họ seed và ba hồ sơ; các bước cùng quỹ đạo phụ thuộc nhau.* [SVG độc lập](../runs/rq12-existing-evidence-20261117-01/rq1-ready-preview-v01.svg)

RQ1 hiện có bằng chứng rằng controller có thể giữ cùng hoạt động dù thông tin đầu vào đổi. Phần còn mở là nối checkpoint fitted với xác suất tham chiếu, hiệu chỉnh quanh ngưỡng, quyết định mastery và hành động trên cùng trace. Xác suất trả lời đúng một câu và mức thành thạo khái niệm cần được định nghĩa riêng trước phép nối này. [Ma trận nghiệm thu RQ1–RQ2](RQ12_CLOSURE_MATRIX_20261112.md)

## 3. RQ2 — điều kiện nào làm đồ thị có lợi, trung tính hoặc bất lợi?

### 3.1. Cơ chế quên quyết định ý nghĩa của phép đo duy trì

Để đánh giá tác dụng của thứ tự luyện sau một khoảng nghỉ, cần biết chỉ tiêu duy trì có mang thông tin khác trạng thái kết thúc hay không. Với luật quên đồng nhất 0,06/ngày trong Paper2, phần tăng kiến thức trung bình giữ lại sau 14 ngày bằng khoảng 43,17% mức tăng ở cuối buổi. Phép đo này giữ thứ tự xếp hạng final gain. Tuy nhiên, một phép tổng hợp mastery phi tuyến có thể đổi thứ tự giữa các trạng thái. Fixture đã kiểm cho thấy khả năng đổi hạng ấy, với phạm vi là các trạng thái dựng để kiểm phép đo. [Phân biệt các phép đo duy trì](rq2_retention_metric_separation_20261108.md)

### 3.2. Tách điều kiện môi trường khỏi phản ứng của hệ thống

Nhóm bổ sung núm bật/tắt phạt thiếu tiên quyết trong phương trình học của simulator. Thí nghiệm giữ đồ thị môi trường và controller, ghép trạng thái ban đầu cùng ngẫu nhiên theo block, rồi so đồ thị chuyên gia với một đồ thị học cố định. Hiệu giữa chênh lệch hai đồ thị khi bật và khi tắt phạt đo tương tác có kiểm soát giữa graph và cơ chế môi trường. Đơn vị phân tích là 10 block ghép cặp, mỗi block chứa các điều kiện năng lực, đồ thị và mức phạt. [Thiết kế và bất định theo block](rq2_fresh_block_uncertainty_20261110.md)

Kiểm chuỗi đã lưu cho thấy 58/60 cặp bật/tắt phạt giữ nguyên cả chuỗi câu hỏi, đáp án và xác suất KT trong 120 bước. Riêng mức khởi tạo 1150, cả 20 cặp giữ nguyên quan sát, trong khi tăng kiến thức ẩn giảm ở cả 20 cặp khi bật phạt. Ở mức 1300, cả quan sát lẫn tăng kiến thức giữ nguyên trong các ca đã chạy. Như vậy, simulator có thể thay kết quả ẩn qua phương trình học trong lúc hệ thống nhận cùng lịch sử. [Kiểm chuỗi độc lập](../runs/rq12-existing-evidence-20261117-01/SECONDARY_CHECK.json)

Ở mức 1150, tương tác trung bình giữa hai đồ thị và núm phạt bằng khoảng +0,024530 Elo, dương ở 8/10 block. Phát hiện về chuỗi quan sát giới hạn cách đọc dấu dương ấy vào tương tác của thiết kế mô phỏng. Bằng chứng phản ứng thích ứng của KT/controller còn cần trace và đối chứng bổ sung. Khảo sát hiện tại dùng một đồ thị học cố định và thời hạn 120 bước. [Bảng kết quả và diễn giải cơ chế](RQ12_EXISTING_EVIDENCE_20261117.md)

### 3.3. Thứ tự luyện giới hạn sức mạnh của đối chứng Junyi

Trên Junyi, người học đã luyện theo một trình tự chịu ảnh hưởng của bản đồ kiến thức. Vì vậy, một quan hệ cha–con có thể trùng với thứ tự sẵn có trong log. Nhóm trước hết đo liệu thay đồ thị có thực sự thay thông tin quá khứ mà mô hình nhận. Pilot cùng quần thể 239 người học cho thấy ba đối chứng chỉ thay exposure ở lần lượt 1, 7 và 1 người. Đây là dấu hiệu đối chứng topology có thể yếu khi áp vào lịch sử cụ thể. [Nguồn pilot cùng quần thể](../runs/cpu-junyi-common-20261107-01/common_population.json)

Phân tích toàn TRAIN80 tiếp tục kiểm theo đúng cửa sổ AKT. Trong 976 cạnh, 876 cạnh có cha xuất hiện trước ít nhất một target con; 58 cạnh thiếu con trong từ vựng TRAIN, 28 cạnh thiếu cha và 14 cạnh có đủ endpoint nhưng chưa có kiểu quan sát cha-trước-con đang xét. Phân loại này giúp chọn đối chứng có thay đổi thông tin thực tế và ghi rõ thiếu hỗ trợ. [Kết quả và kiểm độc lập](../runs/rq2-junyi-window-exposure-preflight-20261112-01/FINDINGS.md)

*Hình 3. Khả năng quan sát thông tin tiên quyết trong cửa sổ TRAIN80 Junyi. Một trăm cạnh thiếu dạng exposure đang xét được tách theo nguyên nhân, cung cấp giới hạn support cho phép so sánh tiếp theo.* [SVG và dữ liệu cạnh](../runs/rq2-junyi-window-exposure-preflight-20261112-01/junyi-native-window-edge-coverage.svg)

RQ2 đã làm rõ ba nguồn điều kiện gồm phương trình môi trường, mức năng lực và khả năng quan sát cạnh. Thí nghiệm xác nhận còn cần đối chứng thứ tự Junyi, mức nhiễu xóa/thêm/đảo cạnh, phân nhóm độ dài lịch sử, khái niệm thưa dữ liệu và quan hệ nội/liên chương theo protocol. Các kết quả Junyi cung cấp bằng chứng dự báo trên log; kết quả giáo dục được giới hạn vào simulator đã khai báo. [Phạm vi còn thiếu](RQ12_COMPLETION_REVIEW_20261116.md)

## 4. RQ3 — CG-AKT đã tạo được bằng chứng đến đâu?

CG-AKT tối giản bổ sung một tín hiệu tiên quyết vào logit AKT. A0 là AKT không đồ thị. A1 dùng trọng số cạnh cố định. A2 dùng trọng số độ tin cậy ước lượng từ TRAIN. A3 bổ sung cổng học được điều tiết ảnh hưởng của graph. Confidence hiện hành biểu diễn độ ổn định dự báo của bộ ước lượng TRAIN. Nhãn cạnh thật/nhiễu trong simulator được dành cho đánh giá và đối chứng oracle được khai báo riêng. [Thiết kế đã chốt](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md)

Selected-fit chọn vòng bằng selection. Refit huấn luyện mới trên train mở rộng theo số vòng ấy. Calibration điều chỉnh xác suất trên người học riêng. Outer evaluation đánh giá độc lập. Bảng theo dõi 11 cấu hình đã train. [Đối chiếu lifecycle](TRAINING_RQ_SCOPE_REVIEW_20261116.md)

| Miền, cấu hình | Selected-fit, vòng chọn | Refit | Calibration | Outer độc lập |
|---|---|---|---|---|
| Grade10 A0 | Có, 5 | Chờ | Chờ | Chờ |
| Grade10 A1 chuyên gia | Có, 5 | Chờ | Chờ | Chờ |
| Grade10 A1 đồ thị học | Có, 4 | Chờ | Chờ | Chờ |
| Grade10 A2 chuyên gia | Có, 4 | Chờ | Chờ | Chờ |
| Grade10 A2 đồ thị học | Có, 4 | Chờ | Chờ | Chờ |
| Grade10 A3 chuyên gia | Có, 4 | Chờ | Chờ | Chờ |
| Grade10 A3 đồ thị học | Có, 4 | Chờ | Chờ | Chờ |
| Junyi A0 | 12 vòng, chọn 9 | Đủ 9 vòng | Đã fit, artifact xác minh | Chờ |
| Junyi A1 chuyên gia | 12 vòng, chọn 9 | Đủ 9 vòng | Đã fit, artifact xác minh | Chờ |
| Junyi A2 chuyên gia | 12 vòng, chọn 9 | Đủ 9 vòng | Suy luận xong, chờ fit | Chờ |
| Junyi A3 chuyên gia | 12 vòng, chọn 9 | Đủ 9 vòng | Suy luận xong, chờ fit | Chờ |

Grade10 dùng 48/6/6 người học cho train/selection/calibration, với 1.260 target selection mỗi cấu hình. Junyi dùng outer fold 4, calibration gồm 15.847 người học và 1.621.484 target. Bốn mô hình đã suy luận đủ cohort này; A0/A1 có artifact temperature được xác minh trên Drive. Hai miền dùng vocabulary riêng. [Grade10](../runs/demo-grade10-selected-replay-20261117-01/REPLAY_MANIFEST.json), [Junyi inference](../runs/junyi-calibration-real-20261117-01/GPU_OUTPUT_ACCEPTANCE01.json), [A0/A1 calibration](../runs/junyi-calibration-real-20261117-01/POSTSTOP_CALIBRATION_METADATA_ACCEPTANCE01.json)

Để kiểm hiệu chỉnh xác suất đáp án, temperature điều chỉnh độ tự tin dự báo bằng một tham số dương. Trên chính cohort fit calibration, A0 có temperature 1,03018, Log Loss từ 0,358459 xuống 0,358315; A1 có temperature 1,02635, Log Loss từ 0,358434 xuống 0,358324. Đây là kết quả khép bước fit calibrator. So sánh tổng quát hóa và hiệu chỉnh quanh ngưỡng mastery tiếp tục cần dữ liệu đánh giá độc lập cùng định nghĩa tham chiếu khái niệm. [Nghiệm thu artifact và giới hạn](../runs/junyi-calibration-real-20261117-01/POSTSTOP_CALIBRATION_METADATA_ACCEPTANCE01.json)

## 5. Tổng hợp đóng góp hiện tại và bước nghiệm thu tiếp theo

Đóng góp đã có gồm giải thích có điều kiện cho các chỉ tiêu simulator, phát hiện sự tách rời dự báo/quyết định, kiểm tương tác môi trường/năng lực và giới hạn đối chứng log. CG-AKT đã có các cấu hình fitted để triển khai đánh giá. Demo hiện xem lại được bảy mô hình Grade10 trên cùng lịch sử và giữ chế độ GAM-KT quan sát quyết định đã lưu. [Demo và giới hạn E11](../runs/demo-grade10-selected-replay-20261117-01/README.md)

Để khép ba RQ, bước tiếp theo cần nối đánh giá dự báo độc lập với mastery/controller, hoàn tất lifecycle Grade10, chạy vòng kín ghép cặp và graph ablation, rồi phân tích bất định theo learner hoặc seed block. SAKT/GKT vẫn là đối chứng theo đề cương, hiện có kết quả engineering nhỏ và còn cần lifecycle matched. Các baseline BKT/GAM lịch sử giữ vai trò tham chiếu với split gốc. [Yêu cầu mô hình và đánh giá](../../paper2/DC%20KLTN0127%2023520355%2623521338_LeVanTuan.pdf), [đường hoàn tất nghiên cứu](TRAINING_RQ_SCOPE_REVIEW_20261116.md)

Kết quả âm, trung tính hoặc cổng tắt đồ thị đều có thể trả lời RQ3 khi các đối chứng được khép. Bản thảo hiện cung cấp phần lập luận và kết quả đã đủ nguồn cho luận văn, đồng thời giữ mở các kết luận về hiệu quả học tập của CG-AKT. [Tiêu chí nghiệm thu](RQ12_CLOSURE_MATRIX_20261112.md)
