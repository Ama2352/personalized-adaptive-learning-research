# Dọn bản trùng và lưu lạnh workspace KLTN ngày18/11/2026

## Phạm vi và ủy quyền

Người dùng yêu cầu dọn thư mục KLTN, upload đủ bộ bàn giao, tách kho lịch sử, chuyển lạnh phần nặng và commit. Đợt1 gỡ bản staging trùng/CONTENT/gói vận chuyển; đợt2 chuyển lạnh output/cache; đợt bổ sung đọc đầy đủ các fixture bị sandbox chặn. Kết quả âm, failure quan trọng, model/checkpoint/dự đoán/manifest nghiên cứu được giữ đúng bytes trên Drive. Không chạy training, GPU hoặc dùng Test để chọn cấu hình.

Không dọn dataset/, artifacts/bkt_baseline/, venv/, .venv/, .wsl/ hoặc .git/ gốc.790đầu vào chuẩn và15model chính có inventory bảo vệ trước/sau. Bản cold-project ban đầu giữ do lỗi đường dẫn dài; sau xác nhận extended-length path đã kiểm kê17.474file và gỡ bản dựng thử. COLD_COPY_KEPT.json giữ failure ban đầu, COLD_COPY_INVENTORY.json/BULK_UNLINK_LOG.jsonl giữ diễn tiến tiếp theo.7file mã/metadata nhỏ đã tracked được phục hồi đúng pin từ Git/blob hoặc checkout EOL filter, không loại source khỏi commit.

## Bằng chứng và thứ tự

1. SCAN_BEFORE.json giữ metadata trước dọn, free space và496thư mục bị sandbox chặn quyền. Đợt bổ sung dùng quyền đọc được duyệt để kiểm nốt fixture; không đổi ACL.
2. STAGING_PLAN.json hash lại21.004bản trùng/38.901.211.925byte và bản giữ, đối chiếu INPUTS.json từng snapshot. Metadata lịch sử trong RETENTION_REVIEW02.csv giữ nguyên; ủy quyền mới được ghi ở run này.
3. RECONSTRUCTION_ACCEPTANCE.json kiểm21snapshot,21.004đường dẫn dùng keeper,10.381member không đổi; dựng thử một snapshot1.490file bằng hardlink trong runtime của lượt này. Không ghi đè manifest snapshot.
4. DEDUP_PACKAGE.json pin archive và từng member. Nội dung2.219file duy nhất của gói dedup cùng metadata và ánh xạ lịch sử được nén, đọc lại toàn bộ member trước upload. DRIVE_ACCEPTANCE.json chỉ xuất hiện sau xác minh SHA256/size/owner/parent trên Drive.
5. PACKAGE_COPIES_VERIFIED.json hash18gói vận chuyển local/4.237.708.775byte, kiểm trực tiếp bản Drive tương ứng. Đây là bản đóng gói phụ, không là model/dataset gốc.
6. DELETE_PLAN.json là allowlist chính xác, RELOCATION.json ánh xạ snapshot cũ sang keeper và archive Drive. unlink_verified.ps1 kiểm đường dẫn tuyệt đối nằm trong workspace/allowlist, cấm vùng bảo vệ/junction, kiểm size/mtime và keeper rồi gỡ từng file bằng Remove-Item -LiteralPath; không xóa đệ quy.
7. UNLINK_LOG.jsonl và UNLINK_SUMMARY.json giữ kết quả từng file. AFTER_VERIFICATION.json kiểm file đã gỡ vắng mặt, hash lại keeper và manifest snapshot. PROTECTED_BEFORE/AFTER.json kiểm790đầu vào và15model. Chỉ dùng số đo free space để nói dung lượng thực trả lại; không cộng tổng hardlink thành dung lượng giải phóng.

## Phục hồi khi audit lịch sử

Tra RELOCATION.json theo đường dẫn gốc. Nếu keeper còn local, kiểm SHA/bytes rồi copy về đúng path cần audit. Không cần phục hồi mọi snapshot để tiếp tục nghiên cứu hiện hành.

Khi cần nguồn lưu lạnh, tải archive được DRIVE_ACCEPTANCE.json định vị, kiểm SHA archive bằng DEDUP_PACKAGE.json, giải nén vào vùng làm việc riêng. Thư mục drive-offload-duplicates-20261116-01 bên trong chứa MANIFEST.json, CONTENT, AUDIT_METADATA.zip và audit_backup.py. Chạy helper với --directory trỏ thư mục đó để kiểm nội dung; chỉ dùng --restore-root với thư mục mới riêng nếu muốn dựng lại các đường dẫn lịch sử. Không phục hồi toàn bộ hàng chụcGB vào project hiện hành một cách tự động.

Archive giữ cả mapping21.604đường dẫn từ catalog cũ; đợt này chỉ gỡ21.004bản staging trong số đó, không gỡ594bản trong kết quả nghiên cứu hoặc16bản modal. Kết quả refit/CV/Test gốc không thuộc allowlist.

## Giới hạn

Đủ SHA và ánh xạ phục hồi xác nhận tính toàn vẹn, không là bằng chứng hoàn tất RQ. Các thư mục không đọc được hoặc chưa phân loại chắc chắn tiếp tục giữ. Archive lớn kiểm SHA bằng metadata Drive sau khi upload; đã tải lại một gói929.575byte và phục hồi member thật để kiểm đường cold restore. Việc tái lập runtime/tiếp quản của người nhận là kiểm riêng. Hồ sơ và các lệnh ở đây không tự cấp quyền dọn thêm ngoài allowlist.

## Phạm vi hoàn tất mở rộng

Xem PLAN_FULL_SCOPE.md, BULK_AFTER_VERIFICATION.json, [đợt fixture bổ sung](../workspace-cleanup-hidden-20261118-01/README.md), [chỉ mục lưu trữ](../../storage/README.md) và [báo cáo vận hành](../../reports/WORKSPACE_STORAGE_HANDOFF_20261118.md). Hai thư mục Drive tách biệt, code/config/docs/runs giữ bố cục khoa học, scripts/storage và docs/operations gom công cụ/hướng dẫn.13.535thư mục rỗng đã được gỡ ở lượt đầu. Gói source cuối được xây qua .partial và xuất bản nguyên tử, kiểm từng member và Gitbundle đúng commit. Hai lỗi quan trọng từ review độc lập đã có kiểm thử thất bại trước/sau; helper cold restore8test, source publisher2test, helper bàn giao6test đạt. Bằng chứng chi tiết/raw inventory/log giữ local và trên Drive, Git giữ summary/mã/catalog nén; không commit payload/model/credentials.
