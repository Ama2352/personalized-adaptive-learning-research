# Rà dung lượng AKT trong lúc upload ngày 16/11

## Kết luận vận hành

Đã kiểm metadata hai vùng `artifacts/akt/` và `experiments/akt/`, đối chiếu tiếp với inventory và các biên nhận trước. Chưa xóa file. Đang chờ duyệt danh sách cụ thể 416 file, tổng 3.564.916.775 byte. Đây là các phần truyền tạm và checkpoint kiểm thử tổng hợp, không phải model nghiên cứu.

| Nhóm | File | GB thập phân | Căn cứ |
|---|---:|---:|---|
| Phần chia đã sao lưu Drive | 7 | 0,424 | SHA từng phần trùng biên nhận đọc lại Drive, ZIP nguồn còn giữ |
| Phần chia recovery cũ | 9 | 1,367 | Đã đọc ZIP đầy đủ, dựng từng khoảng byte và kiểm SHA từng phần |
| Checkpoint pytest tổng hợp | 400 | 1,774 | Nguồn test, lệnh chạy, log, cấu hình và đường dẫn fixture được đối chiếu |

Hai nhóm đầu có thể khôi phục nguyên byte. Với nhóm pytest, giữ bằng chứng kiểm phần mềm và khả năng chạy lại test tạo fixture mới. Nếu xóa, binary chứa UUID cũ sẽ không còn nguyên bản. Không dùng các fixture này làm chứng cứ hiệu quả mô hình trên Junyi hoặc Grade10.

## Phạm vi đã bảo vệ

Hai thư mục `drive-offload-duplicates-20261116-01` và `drive-offload-history-20261116-01` đang upload được giữ nguyên. Script loại cả file cùng định danh NTFS với nội dung trong hai thư mục ấy khỏi danh sách dọn. Không đổi source keeper có hardlink dùng cho upload.

Giữ model refit/selected A0–A3, model Grade10, checkpoint audit A0, input encoding, learner roles, graph/confidence, prediction và hồ sơ nghiên cứu. Không xóa cache/window hoặc staged snapshot chỉ vì chúng lớn. Các snapshot cần rà liên kết phụ thuộc ở mức từng nội dung trước khi bỏ, danh sách bản trùng hiện hành vẫn phải chờ nghiệm thu upload.

## Gói nhỏ đã upload

[Gói bằng chứng 07 trên Drive](https://drive.google.com/file/d/1u4UVVStQdocViKVlv84noq2i_c0O5nTH/view) có 676.937 byte, 486 member. Đã kiểm SHA từng member trước đóng gói và đọc lại toàn bộ byte của bản Drive, khớp SHA gói local. `STORAGE_SMALL_DRIVE_RECEIPT02.json` giữ biên nhận, không lưu URL tải tạm.

Gói giữ inventory dọn, log/config/source test và metadata liên quan. Các binary checkpoint tổng hợp thuộc danh sách dọn không được nén vào gói. Gói nằm trên D tại `experiments/akt/results/storage-small-evidence-20261116-01/STORAGE_CLEANUP_EVIDENCE.zip`. Không tạo thêm bản nén hàng chục GB.

## Đo dung lượng và giới hạn

Lượt metadata hợp lệ tại `artifacts/akt/runtime/storage-review-20261116-03/` đếm 178,55 GB theo tổng đường dẫn, 122,53 GB khi gộp cùng định danh file NTFS. Con số sau vẫn là tổng kích thước file, chưa đo allocation thực tế của NTFS. Hardlink làm tổng theo đường dẫn tăng, không tương ứng từng ấy byte vật lý mới. Không dùng số unique theo từng nhóm để quyết định xóa vì phụ thuộc thứ tự duyệt.

Lượt 02 ban đầu dùng `DirEntry.stat` trả inode/volume bằng 0 trên Windows, nên kết quả unique không hợp lệ. Đã đánh dấu superseded, đổi sang `Path.stat`, kiểm định danh khác 0 và chạy lại thành lượt 03. Giữ dấu vết để tránh trích nhầm.

Dung lượng trống biến động trong lúc kiểm, từ khoảng 2,67 GB đến 30,72 GB dù agent chưa xóa file. Không quy phần tăng này cho thao tác dọn của agent. Vùng private/Holdout/Test và symlink/junction được bỏ qua, không tuyên bố đã rà các vùng ấy.

## Nguồn và bước kế tiếp

- `STORAGE_REVIEW02_STATE.json` trỏ inventory metadata hợp lệ.
- `STORAGE_CLEANUP_REVIEW02.json` giữ đầy đủ đường dẫn, SHA, kích thước, mtime, file identity và số liên kết của 416 ứng viên.
- `prepare_storage_cleanup_review.py` thực hiện kiểm nguồn/parts, loại inode đang upload, đóng gói và kiểm member.
- `STORAGE_SMALL_PACKAGE02.json` giữ pin bản gói tại thời điểm tạo, cờ uploaded trong file này phản ánh lúc đóng gói. Biên nhận Drive mới xác nhận trạng thái upload sau đó.

Sau khi duyệt, phải kiểm lại SHA/định danh, xác nhận ZIP nguồn còn nguyên và ghi nhật ký từng file trước khi xóa. Chỉ xóa đúng đường dẫn được duyệt. Hai thư mục upload lớn tiếp tục chờ người dùng báo hoàn tất rồi nghiệm thu riêng.
