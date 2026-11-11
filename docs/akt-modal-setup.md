# Kết nối Modal và giữ ngân sách30USD/tháng

## Trạng thái đối chiếu ngày 11/11/2026

Chưa nghiệm thu cho training chính trên Modal. User đã yêu cầu tập trung hoàn toàn vào hoàn thiện AKT. Ưu tiên thực thi hiện hành là entrypoint Modal, checkpoint/restore và throughput đủ lập allocation trong 30 USD free credits.

Đã nghiệm thu môi trường Linux cô lập 44 package và Gate CPU 1.993 ca trên 198 file nguồn, 92 module. T4 miễn phí đã chạy A0–A3, tổng 8 Adam updates/192 target giả/24 dự báo, cùng khởi tạo backbone. [Gate CPU](../research_tracking/runs/akt-colab-isolated-cpu-20261110-01/verification.json) và [CUDA smoke](../research_tracking/runs/akt-colab-t4-current-20261110-01/verification.json).

Source kiểm checkpoint CUDA A0/A3 đã chuẩn bị, mới qua AST/API review và chưa chạy. Lượt tiếp tục ngày10/11 chưa nhận được output thực thi mới qua MCP. [Trạng thái gói checkpoint](../research_tracking/runs/akt-t4-checkpoint-recovery-20261110-01/README.md).

Rà soát source ngày11/11 chưa tìm thấy entrypoint dùng Modal App/Image/Volume trong scripts hoặc src/knowledge_tracing/akt. File modal_plan_runner.py được nhắc trong backlog vẫn là việc cần triển khai. SDK/login local đã có hồ sơ lịch sử, còn cloud runtime và storage chưa được nghiệm thu.

Thứ tự hoàn thiện được thu hẹp theo yêu cầu user.

1. Chuẩn bị entrypoint, image từ lock Linux đã kiểm, ràng buộc input/output, một GPU/container, timeout và retry hữu hạn, checkpoint/output theo run.
2. Kiểm native checkpoint/restore và complete lifecycle trên môi trường đích, giữ model/optimizer/RNG/counters và dự báo có danh tính target. Nghiệm thu cloud storage trước lượt training dài.
3. Đo throughput đại diện và tính toàn chi phí của protocol đã chốt, sau đó đề xuất lượt training chính kèm giới hạn tiền và thời gian cụ thể.

Modal sử dụng 0 USD trong các hồ sơ đã nghiệm thu. Số dư và giới hạn tài khoản hiện tại cần được đọc lại trước job trả phí. Các thông tin SDK, đăng nhập và giá ở phần lịch sử dưới đây giữ mốc07/11, cần đối chiếu khi thực thi.


Ngày07/11/2026. User xác nhận workspace **honguyenminhsang2005**, còn **30USD free credits**, kỳ bắt đầu07/11/2026 và reset vào tháng kế tiếp. Ràng buộc **không trả thêm tiền: out-of-pocket ceiling0USD**, gross usage ceiling tối đa30USD trong kỳ. Đây là thông tin user cung cấp, chưa đối chiếu account/dashboard. Ngày/giờ reset chính xác chưa được xác minh; không tự giả có credits kỳ sau hoặc ngày reset cụ thể. Chưa có per-run authorization; chưa tạo remote job, image hoặc Volume.

## Local đã chuẩn bị

- Modal SDK1.6.3 cài trong `D:\Dev\KLTN\.venv`,27package mới,30existingpackage versions giữ nguyên. `pip check`, CLIversion/help pass. Không cài Python global, không đổi `requirements-akt.lock.txt`.
- `requirements-modal-client.in` và `requirements-modal-client.lock.txt` là phần bổ sung cho controller Windows hiện tại, pin public wheel hashes. Nó dựa trên projectvenv đã có các shared dependencies; không là standalone lock cho Linux/CUDA training image.
- Bằng chứng tại `research_tracking/runs/cpu-modal-client-20261107-01/`. Source-bound CPU Gate401 vẫn hợp lệ; suite đó chạy trước SDKinstall. Sauinstall đã kiểm versions/source/lock và localSDK, không claim rerun401.
- [Kiểm Git cuối](../research_tracking/reports/git_evidence_verification_modal_20261107.json) đối chiếu nguyên bytes của bundles và xác nhận privateconfig không tracked. Đây không là xác nhận tài khoản hoặc cloud budget đã được cấu hình.
- Private config dùng `artifacts/akt/private/modal.toml`, Gitignored đã kiểm. User đã hoàn tất browser login; kiểm SDK chỉ đọc xác nhận profilekltn/workspacehonguyenminhsang2005, token hết hạn14/11/2026 lúc17:37:38 giờ Việt Nam. Không đưa credentials vào logs, source, registry hoặc chat. [Kết quả kiểm](../research_tracking/reports/modal_access_readiness_20261107.md).

## Người dùng cần cung cấp

Đã nhận: workspacehonguyenminhsang2005,30USDfreecredits remaining và bắt đầu07/11/2026. Không hỏi lại các thông tin này. Còn cần:

1. Đăng nhập local đã hoàn tất và workspace được API xác minh; không yêu cầu user tạo token lại khi còn hiệu lực.
2. User đã báo hoàn tất bước1 đặt limits theo hướng dẫn. Ghi nhận usage30/spend0 là user-reported, chưa API/dashboard readback. Dashboard vẫn là nguồn đối chiếu balance/currentusage và reset date chính xác; các workload khác trong workspace cũng tiêu ngân sách chung.
3. Plan/quyền GPU thực tế khi kiểm account. Modal yêu cầu payment method cho GPU; việc thêm/xác minh thẻ do chủ tài khoản tự thao tác, không gửi thông tin thẻ cho agent. [Tài liệu chính thức](https://modal.com/docs/guide).

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

Trong Usage & Billing, đặt **Workspace usage limit30USD** cho toàn kỳ và **Spend limit0USD**, rồi xác minh đã áp dụng đúng workspacehonguyenminhsang2005. Workspace budget tính gross trước credits; Spend limit tính net sau credits. Không coi notification/email là hard cap. Nếu UI/quyền không cho đặt0USD hoặc chưa xác minh, chưa launch job; không tự đổi sang mức trả thêm. Các bước này chủ tài khoản tự thực hiện. [Budgets chính thức](https://modal.com/docs/guide/budgets).

## Cách dùng quỹ — đề xuất, chưa là quyền chạy

Ưu tiên user07/11: **kiểm thử CUDA dùng chung trên Colab free trước khi dùng Modal credits**. Gói Colab tại `notebooks/akt_colab_synthetic.ipynb` và [runbook](akt-colab-synthetic-runbook.md). Phần2USD dưới đây chỉ là reserve cho kiểm đặc thù môi trường Modal sau Colab, không là ngân sách mặc định debug CUDA. Chưa có actual Colabrun; không tự chuyển sang Modal khi Colab hếtquota.

| Phần quỹ | Mức tối đa dự kiến |
|---|---:|
| Kiểm riêng image/Volume/recovery Modal sau Colab nếu cần |2USD|
| Throughput/larger bounded benchmark để dự báo cost/target |3USD|
| Training đã chốt protocol và có forecast nằm trong quỹ còn lại |20USD|
| Reserve cho startup/storage/failure/usage khác |5USD|

Không giải ngân cả quỹ bằng một command. Lượt paid đầu phải có config/authorization riêng với1GPU,1container, workload và timeout nhỏ, retry0; không deploy service/cron, không min-container giữ nóng. Chưa có launcher thực thi các controls này; SDKready không là GPUready. Checkpoint durable và export phải pass trước full training. LinuxCUDAimage/lock, Volume semantics và main runtime origin guard còn cần T08/T14.

Rate minh họa đã kiểm từ [Modal pricing](https://modal.com/pricing): L4 .7992USD/h,2physical CPU cores .09432USD/h,8GiB RAM .063936USD/h, tổng **.957456USD/h** trước startup/idle/storage và actual usage vượt request. Đây không là upper-bound bill hoặc throughput forecast. Sửa phép cộng CPU/RAM ở costplan cũ từ.222336 thành.158256; không sửa experimental metrics.30USD chưa bảo đảm đủ fullJunyiCV×mọivariant/baselines. Phải đo targets/s rồi quyết định allocation khoa học; không âm thầm bỏ mô hình/RQ hoặc kéo dài job vượt cap.

Trước mỗi job: remaining usable ceiling = min(user monthly ceiling trừ toàn bộ usage cùng kỳ, applicable credit/headroom đã xác minh theo budget type) trừ reservations/reserve. Không launch nếu projected worst-case vượt phần đã cấp, checkpoint/recovery lỗi, source/data/role mismatch, hoặc chưa có chấp thuận cho exact run. Budget metadata trong tài liệu/state là kế hoạch; dashboard limits và future runner controls mới là thực thi. Starter không có Environment budgets; dùng Workspace cap, không giả API billingreport Team/Enterprise có sẵn trên Starter. [Budgets](https://modal.com/docs/guide/budgets), [billing](https://modal.com/docs/guide/billing).
