# RQ1 · Quan sát toàn miền làm rõ giới hạn của câu hỏi được chọn

## Câu hỏi nghiên cứu

GAM của Paper2 đánh dấu một khái niệm đã thành thạo khi θ ước lượng đạt 1250 và π_task lưu trong trạng thái không vượt 0,55. Quan sát duy nhất khái niệm của câu hỏi được chọn có thể bỏ qua trạng thái ở phần còn lại của miền. Kiểm tra này mở rộng bảng quan sát sang đủ 28 khái niệm trước mỗi bước trên các lịch sử đã lưu.

Ba ô được cố định trước khi chạy hai đối chứng mới. Chúng cùng block 21010, đồ thị đầy đủ, λ bằng 0, signal và parent adaptation bật, local adaptation tắt. F041 có mức khởi tạo 1000 đã nghiệm thu và chỉ được tham chiếu. F081 có mức 1150 và F001 có mức 1300. F001 lấy từ 61 ô parent đã hoàn thành, F081 lấy từ 59 ô child được Recovery03 nghiệm thu. Failure của lượt parent vẫn được bảo toàn.

Mỗi ô có 120 bước và 3360 cặp khái niệm–thời điểm. Trong đó 120 cặp thuộc câu hỏi được chọn và 3240 cặp còn lại thuộc các khái niệm khác. Đây là ba lịch sử của một block tái sử dụng, với các đường đi câu hỏi khác nhau. Các hàng lặp theo thời gian không tạo thêm người học hay block độc lập.

## Nguồn và cách đo

Recorder sao chép kết quả của 28 lời gọi is_mastered đầu tiên vốn có trong ready_set. Không thêm getter hoặc thay đổi mô hình. Mỗi lượt có một policy mới, 120 select, predict và update. Cả 120 action/P, trạng thái cuối policy và fingerprint đều phải khớp lịch sử gốc trước khi đóng native panel và ghép latent.

Phía latent dùng toàn bộ initial thực đã lưu bằng float_hex và chuyển trạng thái theo phương trình nguồn. Không tạo environment, gọi interact, sinh đáp án hoặc lấy số ngẫu nhiên mới. Giá trị θ_at được đánh giá cho đủ 28 khái niệm tại mỗi thời điểm. Cả 120 SHA fullvars trước bước và endpoint toàn miền phải khớp bản gốc. Criterion đối chiếu là θ_at ≥ 1250 trong simulator. Criterion này không bao gồm π và không phải nhãn thành thạo người thật hoặc chuẩn mastery đã hiệu chỉnh của S04.

Checker stdlib độc lập tái hiện lại phương trình latent, SHA trạng thái và bảng đếm từ cache. Mỗi ô mới có 3360 phương trình, 120 fullvars SHA và 28 endpoint khớp. Checker không chạy lại GAM, getter, world hoặc RNG. Thời gian checker F001 là 0,3916622 giây và F081 là 0,4774345 giây, mỗi lượt dưới cap 5 giây.

## Kết quả đầy đủ

TP, FP, FN và TN dưới đây đối chiếu native M với criterion latent của simulator tại cùng khái niệm và thời điểm. Giữ nguyên các ô bằng không.

| Ô · mức khởi tạo | Phạm vi | Số cặp | TP | FP | FN | TN |
|---|---|---:|---:|---:|---:|---:|
| F041 · 1000 | Toàn bộ 28 khái niệm | 3360 | 0 | 0 | 0 | 3360 |
| F041 · 1000 | Khái niệm câu hỏi được chọn | 120 | 0 | 0 | 0 | 120 |
| F041 · 1000 | Các khái niệm còn lại | 3240 | 0 | 0 | 0 | 3240 |
| F081 · 1150 | Toàn bộ 28 khái niệm | 3360 | 0 | 5 | 1 | 3354 |
| F081 · 1150 | Khái niệm câu hỏi được chọn | 120 | 0 | 0 | 0 | 120 |
| F081 · 1150 | Các khái niệm còn lại | 3240 | 0 | 5 | 1 | 3234 |
| F001 · 1300 | Toàn bộ 28 khái niệm | 3360 | 215 | 0 | 2808 | 337 |
| F001 · 1300 | Khái niệm câu hỏi được chọn | 120 | 0 | 0 | 117 | 3 |
| F001 · 1300 | Các khái niệm còn lại | 3240 | 215 | 0 | 2691 | 334 |

Ở mức 1300, chỉ nhìn câu hỏi được chọn sẽ không thấy cả 215 trạng thái native M dương đúng ở phần còn lại của miền. Đồng thời bảng toàn miền vẫn có 2808 âm giả. Việc tìm thấy các dương đúng ngoài câu hỏi không xác nhận độ chính xác chung của bộ phân loại.

Ở mức 1150, 120 câu hỏi được chọn đều là TN. Bảng đủ miền cho thấy 5 FP và 1 FN, tất cả ngoài khái niệm câu hỏi được chọn. Vì vậy, hàng queried chỉ có một lớp âm không đủ để mô tả khả năng phân loại của native M trên miền.

Ở mức 1000, toàn bộ bảng chỉ có lớp latent âm. Kết quả này giữ nguyên giới hạn của báo cáo F041 trước đó.

## Cổng θ và cổng π

| Ô | Cặp θ ước lượng ≥ 1250 | Cặp bị π_task > 0,55 chặn khi θ đạt ngưỡng |
|---|---:|---:|
| F041 | 0 | 0 |
| F081 | 5 | 0 |
| F001 | 215 | 0 |

Trong 220 cơ hội θ đạt ngưỡng ở ba lịch sử này, không có trường hợp π chặn native M. Phạm vi quan sát chỉ gồm block 21010, ba lịch sử 120 bước và cấu hình S1P1L0. Chưa thể suy π dư thừa trong cấu hình, lịch sử hoặc thời gian khác. Cũng chưa đo calibration, response accuracy, hiệu quả học hay lợi ích nhân quả của đồ thị.

## Nghiệm thu và khả năng truy vết

Hai outer thực tế được Root nghiệm thu với Job active sau cleanup bằng 0, môi trường được phục hồi và source/input SHA trước–sau khớp. Thời gian lưu trước final của F001 là 5,3348680 giây và F081 là 5,3735609 giây. Quan sát terminal của Root lần lượt là 5,3408713 và 5,3763793 giây. Hai loại thời gian có vị trí đo khác nhau và không được cộng với nhau.

Manifest tại các bundle dưới đây là căn cứ xác nhận đóng gói. Bản báo cáo này được chốt trước khi đóng bundle, nên sự tồn tại và checksum của manifest cần được đọc tại chỉ mục thực tế. Scientific JSONL giữ trong thư mục experiments theo từng ô, bundle nhỏ chỉ lưu đường dẫn, SHA và số byte.

- [F001 và hồ sơ kiểm độc lập](../runs/rq1-ability-native-panel-f001-20261110-01/README.md).
- [F081 và hồ sơ kiểm độc lập](../runs/rq1-ability-native-panel-f081-20261110-01/README.md).
- [F041 đã nghiệm thu](../runs/rq1-f041-native-panel-20261110-01/README.md).
- [Báo cáo F041](rq1_f041_fixed_time_native_panel_20261110.md).
- [Recovery03 và phân định parent61/child59](../runs/rq2-fresh-graph-recovery-20261110-01/manifest.json).
- [Nguồn native recorder](../../src/knowledge_tracing/gam_kt/native_panel_observer.py).

Quần thể này khác witness PG120 trước đây. Không gộp hai quần thể hoặc coi các lịch sử mức khởi tạo khác nhau là ba block độc lập. RQ1 và full CPU09 truth replay vẫn chưa hoàn tất.
