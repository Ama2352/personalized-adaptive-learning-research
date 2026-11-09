# Lượt chẩn đoán đọc file cho revision02

Ngày 09/11/2026. Root đã đọc diff worker/outer02 so với source01 đã lưu. Revision02 chỉ thêm entitlement đọc đúng contract đã bind external SHA, context lỗi đọc hữu hạn và namespace output mới. Danh sách runtime paths/suffixes giữ như lần trước.

Worker `0f786c71dbd5415938e5f8daa01e4117a7c899f71e422510fa9bb89c30712ac0`, outer `ccec43d6336c9737ebc9793ae6ab8fda3b6dc23b55f4924f689116804fc4200b`, contract `34ca70174d055a3c6e222f5ac48913dde1f797b69ea93fc68e98043a1282f024`.

Cho phép một lần native02 để phân biệt lỗi entitlement đã biết với file bị chặn đầu tiên. Giới hạn là 60 giây tổng, worker 53 giây, owned tối đa 57 giây với cleanup reserve 3 giây, RSS 1 GiB và RAM khả dụng tối thiểu 2 GiB. Scope tối đa hai policy mới trên một history cũ, 240 updates. Không tự tăng cap hoặc gọi lại nếu bị từ chối.

Tiêu chí nghiệm thu parity giữ nguyên review02. Nếu read guard còn chặn, context mới phải cho biết đường dẫn/mode/flags/phase và vài frame đang có, để quyết định bước tiếp theo bằng nguồn thực tế. Một failure có thông tin chẩn đoán vẫn giữ verdict rejected. Nhánh full replay cũ tiếp tục dừng.
