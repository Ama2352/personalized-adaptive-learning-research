# Phục hồi batch đồ thị A1 Junyi

Đã nối collator A1 vào native train_epoch recovery bằng hợp đồng typed. Chỉ bound method collate_training của đúng JunyiGraphAKTAdapter được dùng cùng recovery. Identity bắt buộc giữ condition, encoding, phase và trạng thái graph. Mỗi batch kiểm lại signature nhẹ. Factory tùy ý tiếp tục bị từ chối.

## Bằng chứng

Linux CPU source05 đạt2.223tests,0failure/error/skip trong74,32giây. Năm ca mới kiểm model/Adam/RNG/loss cùng kết quả giữa chạy liên tục và phục hồi, cho graph bật và tắt. Các ca âm từ chối context chưa ghim, factory được bọc và graph đổi giữa epoch. Native AKT/graph math chạy thật trên CPU. Admission CUDA được mock trong fixture như bộ adapter trước.

Archive94.432bytes cùng receipt và XML đã tải về, kiểm inventory. App CPU đã dừng. Không có training nghiên cứu A1 hoặc kiểm phục hồi CUDA A1 từ gói này. Producer selected A1 và confidence A2/A3 Junyi còn cần nối.

A0 full đang chạy bằng source04 và Gate2.218 riêng đã đóng gói. Source05 của gói này được kiểm độc lập và phục vụ bước triển khai tiếp theo. Checkpoint A0 tiếp tục dùng đúng nguồn/identity đã ghi trong lượt chạy.
