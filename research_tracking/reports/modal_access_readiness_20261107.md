# Kiểm kết nối Modal sau khi user đăng nhập — 07/11/2026

## Kết quả xác minh

SDK1.6.3 xác thực thành công qua profile `kltn` tại private config của repository. TokenInfoGet trả đúng workspace **honguyenminhsang2005**; WorkspaceSettings đọc được environment mặc định **main**, image builder version **2026.10**. Token được tạo07/11/2026, hết hạn **14/11/2026 lúc17:37:38 Asia/Saigon (UTC+7)**. Không lưu token ID, secret, raw SDK stdout/stderr hoặc hash private config.

Chỉ gọi handshake ClientHello, TokenInfoGet và WorkspaceSettings. Không gọi app/function/image build/Volume hoặc đổi account settings. Không có compute do agent khởi chạy trong lượt kiểm này. Điều này không khẳng định các workload khác của workspace không tiêu credits.

Nguồn: [bundle5outputs](../runs/cpu-modal-access-20261107-01/README.md), có exact probe source, manifest nguồn/output hashes, log kiểm và sanitized API result. [Bản tổng hợp JSON](modal_access_readiness_20261107.json) tham chiếu SHA của API result và local audit. Kiểm prefix credential trong bundle không phát hiện chuỗi giống token; private config vẫn Gitignored và không tracked.

## Tách xác thực khỏi GPU readiness

| Điều kiện | Trạng thái và nguồn |
|---|---|
| Token/workspace/profile | VERIFIED bằng API chỉ đọc |
| Environment/image builder setting | VERIFIED main/2026.10; đây không là LinuxCUDAimage digest đã build |
|30USD free credits còn lại, kỳ bắt đầu07/11 | USER REPORTED; chưa có balance API readback |
| Workspace usage limit30USD / Spend limit0USD | User đã báo hoàn tất bước1 theo hướng dẫn; không đọc lại dashboard/API trong lần này |
| Credential file | Local presence/ignore/untracked checks PASS, không đưa nội dung vào evidence |
| Gate2 source401tests | Binding nguồn/lock vẫn PASS; không chạy lại suite do không đổi code |
| LinuxCUDAimage/dependency lock/remote resource limits | Chưa hoàn tất |
| GPU availability/finite gradients/throughput/checkpoint durability | Chưa chạy, không suy từ token valid |

CLI WorkspaceSettings chỉ expose default-environment/image-builder-version ở SDK đang dùng; probe không có credit/spend-limit response. Không gán các số user cung cấp thành accountverified, không mở endpoint billing đặc quyền hoặc thay settings để thử. [Token CLI](https://modal.com/docs/cli/latest/token), [Workspace settings](https://modal.com/docs/cli/latest/workspace#modal-workspace-settings-list), [budget semantics](https://modal.com/docs/guide/budgets).

## Điều kiện trước lượt compute đầu

Giữ gross ceiling30USD/free credits và out-of-pocket ceiling0USD. Chưa coi bước login là chấp thuận fulltraining hoặc tiêu hết quỹ. Còn phải chuẩn bị image/lock đúng LinuxCUDA (Windows CPUlock không dùng được), bounded launcher có1GPU/1container/timeout/retry0, output manifest/checkpoint/export và budget reservation cho exact run. Probe tổng hợp400targets/1step hiện có chỉ là workload ứng viên; chưa chạy nó trên Modal, chưa có numerical runtime/cost forecast đo được.

Không nới guard CPU của main smoke/pilot chỉ vì token hoạt động. S04/S05 và research protocol/fullcorpus vẫn là các phụ thuộc riêng. Chỉ chạy GPU khi gói đầu đã có input/output contract, giới hạn tài nguyên/thời gian/tiền và authorization tương ứng. Không tự tạo cron/service/container giữ nóng. Kiểm token còn hiệu lực trước mỗi lượt; không tự tạo token mới hoặc automation nhắc hạn.
