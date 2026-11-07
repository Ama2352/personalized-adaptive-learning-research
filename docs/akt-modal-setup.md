# Kết nối Modal và giữ ngân sách30USD/tháng

Ngày07/11/2026. User đã có Modal và nêu mức30USD/tháng. Chưa xác minh đây là free credits hay ngân sách trả thêm, workspace/balance/reset date chưa được cung cấp. Tạm giữ **trần tổng sử dụng30USD**, không cộng thêm credits hoặc vay ngân sách tháng sau. Chưa có per-run authorization; chưa tạo remote job, image hoặc Volume.

## Local đã chuẩn bị

- Modal SDK1.6.3 cài trong `D:\Dev\KLTN\.venv`,27package mới,30existingpackage versions giữ nguyên. `pip check`, CLIversion/help pass. Không cài Python global, không đổi `requirements-akt.lock.txt`.
- `requirements-modal-client.in` và `requirements-modal-client.lock.txt` là phần bổ sung cho controller Windows hiện tại, pin public wheel hashes. Nó dựa trên projectvenv đã có các shared dependencies; không là standalone lock cho Linux/CUDA training image.
- Bằng chứng tại `research_tracking/runs/cpu-modal-client-20261107-01/`. Source-bound CPU Gate401 vẫn hợp lệ; suite đó chạy trước SDKinstall. Sauinstall đã kiểm versions/source/lock và localSDK, không claim rerun401.
- Private config dùng `artifacts/akt/private/modal.toml`, Gitignored đã kiểm. Chưa có token được tạo. Không đưa credentials vào logs, source, registry hoặc chat.

## Người dùng cần cung cấp

1. Tên workspace cần dùng và plan hiện tại.
2.30USD là free credits hay gồm tiền trả thêm; credits còn lại, usage đã dùng trong kỳ và ngày reset kỳ. Các workload khác trong cùng workspace cũng tiêu ngân sách chung.
3. Giá trị Workspace usage limit và Spend limit đang đặt. Chỉ gửi số liệu không nhạy cảm, không gửi thông tin thẻ/token/password.
4. Xác nhận account đã đủ điều kiện GPU hay chưa. Modal yêu cầu payment method cho GPU; việc thêm/xác minh thẻ do chủ tài khoản tự thao tác, không gửi thông tin thẻ cho agent. [Tài liệu chính thức](https://modal.com/docs/guide).

## Đăng nhập một lần trên máy này

Chạy trong PowerShell của VSCode tại repository, tự đăng nhập/chọn đúng workspace trong trang trình duyệt mở ra:

```powershell
Set-Location D:\Dev\KLTN
$env:MODAL_CONFIG_PATH = 'D:\Dev\KLTN\artifacts\akt\private\modal.toml'
$env:MODAL_PROFILE = 'kltn'
.\.venv\Scripts\python.exe -B -m modal token new --profile kltn --expires-in 7d
```

Lệnh này tạo credentials local từ browser session, không phải lệnh chạy GPU. Profile flag/version/help đã kiểm local; thời hạn token còn phụ thuộc policy workspace. Sau khi hoàn tất, chỉ báo “đã đăng nhập” và workspace, không chép token/link xác thực/config file vào chat. Các phiên terminal sau phải đặt lại hai biến cấu hình này; chưa thay environment global của Windows. [Token CLI](https://modal.com/docs/cli/latest/token), [config path/profile](https://modal.com/docs/sdk/py/latest/config).

## Giới hạn trên dashboard trước khi chạy

Trong Usage & Billing, đặt **Workspace usage limit30USD** cho toàn kỳ. Nếu chỉ dùng freecredits và không trả thêm, đặt **Spend limit0USD** nếu tài khoản cho phép và xác minh đã áp dụng. Workspace budget tính gross trước credits; Spend limit tính net sau credits. Không coi notification/email là hard cap. Nếu UI/quyền không cho cấu hình hoặc chưa xác minh, chưa launch job. Các bước này chủ tài khoản tự thực hiện. [Budgets chính thức](https://modal.com/docs/guide/budgets).

## Cách dùng quỹ — đề xuất, chưa là quyền chạy

| Phần quỹ | Mức tối đa dự kiến |
|---|---:|
| CUDA smoke + checkpoint/recovery verification |2USD|
| Throughput/larger bounded benchmark để dự báo cost/target |3USD|
| Training đã chốt protocol và có forecast nằm trong quỹ còn lại |20USD|
| Reserve cho startup/storage/failure/usage khác |5USD|

Không giải ngân cả quỹ bằng một command. Lượt paid đầu phải có config/authorization riêng với1GPU,1container, workload và timeout nhỏ, retry0; không deploy service/cron, không min-container giữ nóng. Chưa có launcher thực thi các controls này; SDKready không là GPUready. Checkpoint durable và export phải pass trước full training. LinuxCUDAimage/lock, Volume semantics và main runtime origin guard còn cần T08/T14.

Rate minh họa đã kiểm từ [Modal pricing](https://modal.com/pricing): L4 .7992USD/h,2physical CPU cores .09432USD/h,8GiB RAM .063936USD/h, tổng **.957456USD/h** trước startup/idle/storage và actual usage vượt request. Đây không là upper-bound bill hoặc throughput forecast. Sửa phép cộng CPU/RAM ở costplan cũ từ.222336 thành.158256; không sửa experimental metrics.30USD chưa bảo đảm đủ fullJunyiCV×mọivariant/baselines. Phải đo targets/s rồi quyết định allocation khoa học; không âm thầm bỏ mô hình/RQ hoặc kéo dài job vượt cap.

Trước mỗi job: remaining usable ceiling = min(user monthly ceiling trừ toàn bộ usage cùng kỳ, applicable credit/headroom đã xác minh theo budget type) trừ reservations/reserve. Không launch nếu projected worst-case vượt phần đã cấp, checkpoint/recovery lỗi, source/data/role mismatch, hoặc chưa có chấp thuận cho exact run. Budget metadata trong tài liệu/state là kế hoạch; dashboard limits và future runner controls mới là thực thi. Starter không có Environment budgets; dùng Workspace cap, không giả API billingreport Team/Enterprise có sẵn trên Starter. [Budgets](https://modal.com/docs/guide/budgets), [billing](https://modal.com/docs/guide/billing).
