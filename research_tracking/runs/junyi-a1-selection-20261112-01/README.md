# Producer selected A1 Junyi dùng chung protocol với A0

Đã thêm run_junyi_selected cho A0 và A1_EXPERT. Entry A0 hiện có giữ signature. Cùng một state machine thực hiện grant, TRAIN80/selection10, early stopping20/patience3, checkpoint trước validation, best reload và raw export. A1 dùng đúng typed condition/encoding, chuyển phase train/selection tường minh, đưa owned collator vào recovery có signature.

Graph condition SHA có trong grant prepared inputs, logical identity và terminal. Mã A1_EXPERT khớp allocation KLTN đã chốt. Backbone initialization được hash riêng, giữ khả năng đối chiếu seed với A0. Refit và calibration tiếp tục đợi external freeze.

## Kiểm đã đạt

Source06 đạt2.226ca, gồm ba kiểm orchestration mới bằng model/Adam/checkpoint CPU thật và vòng train/evaluate mock. Sau đó chuẩn hóa candidate ID thành A1_EXPERT theo allocation, thêm condition vào terminal và assertion đối chiếu allocation. Source07 cũng đạt2.226ca,0failure/error/skip trong142,15giây. Giữ cả hai receipt/archive/XML.

Ba kiểm mới xác nhận chọn epoch/best reload/export dùng cùng quy tắc, phục hồi trước validation không train lại epoch đã hoàn tất, và grant A0 không cấp quyền chạy A1. Kiểm native graph math và phục hồi riêng được giữ ở bundle junyi-a1-recovery-20261112-01.

## Giới hạn

Đây là bằng chứng phần mềm. Chưa có selected fit A1 Junyi hoặc kiểm CUDA producer A1 từ gói này. A1_LEARNED và confidence A2/A3 Junyi cần artifact confidence/topology TRAIN80 tương ứng. A0 chính đang chạy/được phục hồi bằng source04 riêng, giữ identity cũ. Không nâng nguồn của lượt đang chạy sang source07.
