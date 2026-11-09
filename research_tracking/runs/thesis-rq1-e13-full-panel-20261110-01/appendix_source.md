

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
