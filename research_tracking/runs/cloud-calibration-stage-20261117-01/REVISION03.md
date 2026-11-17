# Chẩn đoán an toàn sau lượt stage thật dừng

Root báo lượt cloud stage01 đã dừng với ValueError, nhưng lớp ngoài chỉ trả tên loại lỗi nên chưa phân biệt được nguyên nhân. Chưa có căn cứ kết luận là tải ZIP, metadata Drive hoặc giải nén sai. Không tự retry cloud trong nhánh này.

Worker hiện ghi phase MOUNT, AUTH, DOWNLOAD, EXTRACT hoặc RECEIPT. Chỉ những thông báo tĩnh do chính worker định nghĩa được đưa ra công khai. Nội dung lỗi HTTP/OAuth hoặc lỗi ngoài whitelist bị thay bằng null. JSON lỗi giữ phase, loại lỗi, thông báo đã duyệt và số byte ZIP/part. File FAILED-uuid.json được ghi mới trên Volume và commit nếu có thể. Thông tin lỗi trong lượt trước và partial artifact được giữ nguyên.

Các ca kiểm thêm xác nhận thông báo tĩnh được lưu đúng, token/URI giả trong ngoại lệ không xuất hiện ở log/file, và lỗi commit diagnostic không làm lộ ngoại lệ bên trong. `tests05.txt` đạt **18/18** trong 0,48 giây. Các kiểm thử này bảo đảm cơ chế báo lỗi, chưa chứng minh cloud stage hoàn tất.

MANIFEST03.json ghi nguồn mới và nối manifest trước. Root cần review rồi tự chạy một lượt CPU riêng để thu nguyên nhân thực từ phase/message.
