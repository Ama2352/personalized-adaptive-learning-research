# Bàn giao và chuyển lạnh workspace KLTN ngày18/11/2026

## Phạm vi

Người dùng yêu cầu Drive đủ tài nguyên để thành viên khác hoàn thiện KLTN, kho lịch sử ngoài bàn giao tách riêng, gỡ file trùng/cache/output nặng khỏi local, giữ repo gọn và commit. Đây là hồ sơ vận hành, không phải thí nghiệm nghiên cứu mới.

## Nơi nhận và cách sử dụng

- [Bộ bàn giao](https://drive.google.com/drive/folders/1T6GseWOnUbbj-eXTcWIELAp2hPemGrLQ): hướng dẫn cuối, source hiện hành và lịch sử Git, dữ liệu/split/graph, model, calibration và kết quả đã nghiệm thu. Bắt đầu từ BAT_DAU_TAI_DAY_FINAL và MANIFEST_BAN_GIAO_FINAL; core/ready được tách rõ.
- [Kho lịch sử/audit riêng](https://drive.google.com/drive/folders/1QoqGGMj6NUW7soLPxSkKDeKknFO_uyw6):42asset lịch sử tách khỏi bộ bàn giao cũ, archive dedup7.472.006.393byte và34gói nội dung mới13.009.132.758byte. Các nguồn bàn giao cũ được bảo toàn khi cập nhật bản cuối.
- [Catalog phục hồi](../storage/README.md):226.534đường dẫn theo73.145nội dung SHA,54file/gói Drive được tham chiếu. Tra đúng file trước khi phục hồi; không phải tải cả kho lịch sử để chạy tiếp.

## Đã kiểm trước khi gỡ local

Đợt1 hash lại21.004bản staging trùng, đối chiếu keeper và INPUTS.json. Kiểm21snapshot bằng ánh xạ phục hồi và dựng thật một snapshot1.490file. Archive dedup được đọc lại từng member trước upload và so SHA256/size/owner/parent Drive.

Đợt2 hash86.462file còn lại trong output/cache; tái dùng nội dung Drive đã có, đóng gói47.486nội dung còn thiếu thành34archive độc lập, đọc lại member và kiểm SHA Drive. Các bản dữ liệu nhạy cảm/private không được chọn. Source manifest/model/prediction được giữ đúng bytes trong bản lưu lạnh; không sửa giá trị để hợp bố cục mới.

Tổng128.702file đã được gỡ qua allowlist, gồm bản trùng, payload chuyển lạnh, gói vận chuyển và17.474file của project dựng thử. Không có lỗi xóa trong hai allowlist. Các thư mục rỗng được dọn riêng, không xóa đệ quy hoặc thay ACL.790đầu vào chuẩn và15model gọn khớp SHA sau dọn. Manifest21snapshot khớp pin trong bản lưu lạnh.

## Bố cục và tái lập

Giữ các vùng source/config/docs/reports/runs theo vai trò hiện hành. scripts/storage chứa helper phục hồi, research_tracking/storage chứa catalog và locator, docs/operations chứa runbook. Không chuyển tùy tiện các paper hoặc frozen bundles vì đường dẫn là một phần lineage.

Các raw inventory/log thao tác lớn không đưa vào Git; giữ tại bundle local và trong archive bằng chứng Drive. Git giữ summary, mã và catalog nén. Model/checkpoint/dataset/credentials không được commit. Thay đổi notebook CPU có trước được rà và bảo toàn trong nguồn bàn giao.

Helper phục hồi mới đã có8kiểm thử tổng hợp và đã tải lại gói Drive929.575byte để phục hồi một member thật, kiểm đúng SHA. Bộ source/input/model bàn giao trước đó có cold restore790input/15model và Git; source cập nhật cuối được pin riêng theo commit và member inventory.

## Số đo và giới hạn

Đầu lượt D trống59.885.293.568byte. Sau hai allowlist, trước các file hướng dẫn/commit cuối, D trống147.728.375.808byte: tăng khoảng87,84GB. Đây là free space thực đo, không cộng tổng đường dẫn hardlink thành dung lượng trả lại. Số cuối và phân bố theo vùng ở REPO_FINAL_SIZE.json trong bundle.

dataset/, artifacts/bkt_baseline/, venv/, .venv/ và .wsl/ được giữ theo quy tắc bảo vệ.496thư mục fixture bị chặn quyền được ghi và giữ, không đổi ACL. Lỗi đường dẫn dài ở bản cold-project đã được xác nhận bằng extended-length path và khắc phục trước khi kiểm kê/gỡ bản dựng thử. Execution policy chỉ đặt RemoteSigned cho tiến trình PowerShell chạy script local đã duyệt, không đổi policy toàn máy.

SHA/commit và tải đủ file không tự chứng nhận runtime của người nhận hoặc hoàn tất RQ. Không chạy training, GPU/Modal, chọn cấu hình hoặc mở lại Test để tối ưu trong lượt này. [Bundle nguồn](../runs/workspace-cleanup-20261118-01/README.md) và [hướng dẫn tiếp quản](../../docs/operations/STORAGE_AND_HANDOFF.md) giữ đường kiểm chứng và bước tiếp tục.
