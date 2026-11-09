# RQ1 — đối chiếu trên120 câu do policy chọn

Đã ghép đúng120readouts của một history cũ21000/PG/S=Poff/Loff với cacheCPU09.
Controller vẫn giữ đồ thị tiên quyết. Cả120native theta dưới1250 trong khi tiêu chí
latent của queried concept đều đạt. Số lượt theta đạt để xét thêm pi bằng0.
22concept được phục vụ đều latent-positive từ first visit. Đây là mẫu on-policy,
không đại diện độ chính xác toàn bộ state, không graph comparison hoặc learning gain.
First-visit là kiểm cơ chế hậu nghiệm, không independent confirmation.

Gói giữ pure8 ở hai phiên bản, cached01 bị dừng do RAM bộ đo, cached02 accepted,
probe3calls phát hiện ctypes type retention và probe02 xác nhận cache ổn định.
Analyzer/tests không đổi khi sửa bộ đo, caps giữ nguyên. Crosscheck độc lập đã đạt,
giữ source trước sửa CSV BOM. Dataset và file lịch sử không đổi.

Chưa có model/world/RNG khoa học mới. Các raw inputs lớn tham chiếu qua SHA,
không nhân bản gzip. Bản nháp kỹ thuật giữ trong gói. Báo cáo canonical và hai file
GVHD còn cần xuất bản ở batch nối tiếp, chưa được bundle này coi là đã cập nhật.
