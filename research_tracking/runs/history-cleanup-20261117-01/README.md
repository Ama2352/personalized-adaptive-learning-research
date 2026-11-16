# Dọn archive lịch sử AKT đã giữ trên Drive ngày 17/11/2026

## Kết quả

Đã xóa đúng 35 ZIP lịch sử thông qua 70 hardlink local, tổng dữ liệu archive duy nhất 35.154.218.914 byte. Trước khi xóa đã hash lại cả 35 nội dung, liệt kê toàn bộ hardlink bằng NTFS API và đọc lại SHA-256 của Drive. Mỗi archive chỉ có hai tên local được duyệt, gồm source ZIP và tên gom trong thư mục upload.

Sau xóa, 70 đường dẫn đều mất. Kiểm SHA 44 file bảo vệ đạt, gồm các compact export selected/refit, Grade10 và ZIP A0 còn cần audit. Đọc lại Drive xác nhận 35/35 SHA-256 vẫn khớp. Bằng chứng tại ACCEPTANCE.json. Dung lượng trống đo trong lượt tăng 35.145.015.296 byte, từ 34.197.323.776 lên 69.342.339.072 byte. Hoạt động calibration khác cùng lúc có thể ảnh hưởng số đo.

## Khôi phục khi cần replay lịch sử

[Thư mục Drive](https://drive.google.com/drive/folders/1V-H0estsyh2oQQ3qnfapU9qSpGZFoF3H) giữ cả 35 ZIP. RELOCATION_MANIFEST.json ghi hai đường dẫn local trước đây, ID/URL Drive và SHA tương ứng. Khi cần notebook recovery hoặc tái kiểm run cũ, tải đúng ZIP về đường dẫn source cần dùng và kiểm SHA trước khi mở. Pipeline calibration hiện hành dùng compact model.pt, MODEL_INDEX.json và SUPPORT.zip trên D, các file đó đã được giữ.

Giữ MANIFEST.json và hướng dẫn trong thư mục upload cũ theo đúng bytes lịch sử. Những trường trạng thái lúc gom/upload là hồ sơ tại thời điểm ấy. Trạng thái hiện hành là archive trên Drive và local đã xóa theo DELETE_RESULT.json. Các nhóm thư mục rỗng được giữ để còn cấu trúc phục hồi. Danh mục duplicates 55,78 GB là đợt riêng.

Uploader lịch sử khi chạy --prepare hoặc upload lại sẽ phát hiện thiếu archive đúng theo guard. Đã chỉnh --login-only dùng kế hoạch đã lưu để gia hạn đăng nhập vẫn hoạt động sau dọn, có 30 kiểm thử đạt. Khi cần upload lại lịch sử, khôi phục nguồn từ Drive trước. Không sửa plan/manifest cũ để làm như file nguồn còn tồn tại.

## Chỉ mục bằng chứng

- DELETE_PLAN.json và PLAN_PIN.json giữ allowlist 35 nhóm/70 đường dẫn cùng SHA và file identity.
- PROTECTED_FILES.json giữ 44 pin trước xóa; kiểm sau được ghi trong ACCEPTANCE.
- LIVE_DRIVE_VERIFICATION.json giữ kiểm trước xóa. ACCEPTANCE giữ kiểm Drive sau xóa.
- DELETE_PREFLIGHT.json kiểm identity/hardlinks và file giữ ngay trước thực thi.
- DELETE_JOURNAL.jsonl giữ intent và xác nhận từng lần unlink. DELETE_RESULT.json giữ tổng và số đo free space.
- RELOCATION_MANIFEST.json giữ nguồn trước đây và nơi lưu remote. Các manifest/model/prediction lịch sử được giữ nội dung cũ.
- INDEPENDENT_REVIEW.md kiểm dependencies và ZIP A0 audit nằm ngoài allowlist.
- HARDLINK_SMOKE_RESULT.json giữ thử nghiệm read-handle/share-delete trên hai link của fixture 7 byte, đã xóa fixture sau kiểm. Lượt tạo hardlink đầu ở môi trường hạn chế quyền bị từ chối, lượt có quyền phù hợp đạt trước thao tác archive thật.
- uploader-tests.txt giữ 30 kiểm thử, gồm đăng nhập tiếp tục dùng được khi nguồn đã archived.

prepare_cleanup.py và verify_cleanup.py dùng .venv, stream SHA với bộ nhớ nhỏ, không nạp model. execute_cleanup.ps1 thực hiện xóa bằng Remove-Item -LiteralPath, kiểm absolute allowlist, reparse points và giữ handle từ chối ghi trong lúc hash/unlink từng archive. Không xóa recursive hoặc xóa theo glob.

Kiểm remote dựa SHA server, không có lượt download lại 35 GB. Các bản model/checkpoint/cache nghiên cứu khác tiếp tục theo layout pipeline. Lượt này không thay dữ liệu, split, mô hình hay kết luận thực nghiệm.
