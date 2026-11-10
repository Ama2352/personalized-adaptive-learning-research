# Quy mô đọc file chín điều kiện với1.260target giả

Ngày10/11/2026,71tests đạt trong `.venv` và lượt synthetic9conditions×1.260target hoàn tất. Fixture có6learner×210events,18CSV,11.340row checks,22.680index entries, common1.259target do1OOV của A3 expert. Không có dữ liệu/model thật hoặc Holdout.

## Số đo và nguyên nhân

Lượt01 có68tests đạt nhưng reader bị từ chối sau45.005giây tại cap45giây. Cách cũ mở lại file và kiểm đường dẫn mỗi lần đọc một dòng. Nguồn trước sửa và failure/stdout/stderr được giữ ở bundle này. Không nâng cap rồi coi là sửa thành công.

Lượt02 giữ45giây reader cap, hoàn tất trong11.807giây, peak worker57769984bytes, fixture6995894bytes. Explicit max_open_files đổi từ1 sang18 để giữ các CSV đã xác minh trong context. Mỗi dòng vẫn kiểm length/SHA/K, file handle được bind identity trước đọc, kiểm lại stamp/path khi đóng và toàn input được rehash cuối. ExitStack đóng handle trước kiểm cuối. Callers dùng cap1 vẫn giữ cách đọc cũ và được kiểm hồi quy. Kết quả thống kê, coverage, input inventory và logical read-byte count của hai cách khớp trong fixture cùng4target.

Không gọi đây là tỷ lệ tăng tốc định lượng vì lượt cũ chưa hoàn tất và chưa ghi số dòng đã xử lý lúc timeout. So sánh quan sát là timeout45giây với cap1, sau sửa hoàn tất11,807giây với cap18 trên cùng quy mô target và workload giả. Peak lấy từ process high-water mark, không phải OS hard memory quota. Giới hạn outer120giây áp dụng bằng timeout child, không có subprocess/model/network bên trong.

## Bằng chứng và giới hạn

71tests gồm bảo toàn đường đọc cũ, handle close, cursor hết hiệu lực, tamper trong context, handle limit, parity của cả9môhình, population và kernel. Không cộng68và71thành139ca độc lập. Result02 giữ source195 trước–sau, caps, RAM, thời gian, read bytes và trạng thái không chọn mô hình. Fixture-inventory02 ghim các file ở local-tests/nine-file-scaling02/manufactured-fixture; các file giả và sources còn tại đó, không sao chép toàn bộ vào Git.

Đây là throughput đọc artifact sau training, không phải training/GPU throughput hoặc bằng chứng RQ3. Chưa có main operation admission, exclusive freeze/publication, actual9fits hoặc refit. Source195 cần Gate mới, Linux/CUDA/fault recovery/durability và GPU cost còn chưa đo. Không dùng Modal. Hai file báo cáo GVHD giữ kết luận khoa học hiện hành, kế hoạch GPU07 được cập nhật trạng thái chuẩn bị.
