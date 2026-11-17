# Điều phối Colab CPU miễn phí bằng request có trạng thái

## Phạm vi và trạng thái

`scripts/akt/colab_cpu_execution.py` được chuẩn bị ngoài source KT frozen. Gói này chỉ chạy tests offline. Chưa tạo runtime/session hoặc chạy code từ xa. Quyền OAuth/API thật vẫn cần được root nghiệm thu trước khi dùng.

Thiết kế dùng schema Google đã tải tại `../colab-persistent-session-20261117-01/PUBLIC_TOOL_SCHEMAS01.json`. Module auth đã có được tái sử dụng để đọc MCP, lưu credentials và xử lý JSON/SSE. Không cài Colab CLI hoặc package global.

## Các ranh giới thực thi

- Chỉ chấp nhận tài khoản có tier `SUBSCRIPTION_TIER_FREE` và spec `VARIANT_CPU`, accelerator `NONE`, shape `SHAPE_STANDARD`, `eligible=true`. Không có phương án tự chuyển sang GPU, high-memory hoặc paid tier.
- Ưu tiên runtime CPU chuẩn đang tồn tại. Trước khi dùng runtime đã lưu, gọi `get_runtime` và kiểm lại spec thực tế. Không tác động session notebook của người dùng.
- Session riêng có ID `kltn-<UUIDhex>` được ghi vào private state trước khi gửi `create_session`. Module không có lệnh xóa runtime/session.
- Chỉ gửi code từ file `.py` canonical trong `scripts/akt/`, có SHA256 caller cung cấp và tên phase rõ ràng. Compile kiểm cú pháp trước khi gửi. Không tự thực thi khi import module.

## Request và tiếp tục

State tại `artifacts/akt/private/colab-session/cpu-execution.json`, cùng vùng private D với OAuth. Request tạo runtime có UUID4 `requestId`. Request code có UUID4 `executionId`, session riêng, nguyên code và SHA nguồn. Tất cả được ghi atomically **trước khi gửi**.

Timeout hoặc UNAVAILABLE được nhận diện bằng mã RPC4/14, timeout transport hoặc HTTP504. State chuyển `UNCERTAIN`, lần gọi tiếp theo giữ nguyên tool arguments và UUID để reattach. Không tự gửi lại với một UUID mới. Các lỗi khác chuyển `FAILED` và yêu cầu xem xét, không retry mù. Provider error chưa nhận diện được cũng dừng, tránh suy đoán một request đã chạy hay chưa.

Khi nhận terminal result, kiểm runtime spec hoặc session/executionId trước khi ghi `COMPLETE`. Phase đã hoàn tất trả lại summary lưu trước đó, không gửi code lần nữa và không tạo thêm runtime chỉ để đọc kết quả cũ. Cả terminal Python exception cũng là một kết quả thực thi đã kết thúc. Muốn sửa code và chạy lại cần phase mới rõ ràng, giữ hồ sơ phase cũ.

Output stdout/stderr/result đầy đủ chỉ giữ trong private state. Console chỉ có tên phase, trạng thái, SHA, executionId và cờ exception/truncated. Code phase phải được caller rà nội dung, giữ credentials ngoài source. Không đưa private state vào báo cáo hoặc commit.

## Entrypoints

Các lệnh `runtime` và `session` chỉ được root gọi sau khi đã nghiệm thu OAuth và quyền API.

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/colab_cpu_execution.py runtime
.\.venv\Scripts\python.exe -B scripts/akt/colab_cpu_execution.py session
```

Lệnh `execute` yêu cầu đủ `--script`, `--sha256` và `--phase`. File phase thực thi calibration chưa được triển khai/gọi trong gói này. Module giữ cơ chế transport/session chung để root nối launcher đã duyệt.

CLI dùng `single_writer` hiện hữu cho toàn lifecycle tại private `cpu-execution.lock`. Caller dùng trực tiếp các helper Python cần serialize cùng state. Không gọi song song hai phase chung session vì official execute_code xếp hàng và có thể timeout. Request ID giúp tiếp tục sau lỗi truyền tải, khóa CLI giữ một writer cho state.

## Đã kiểm

`tests04.txt/xml` giữ lượt cuối26ca đạt trong0,93giây, gồm10ca phase CPU và16ca auth. Các ca mới kiểm tier paid bị chặn, spec không eligible bị chặn, runtime CPU reuse không gọi create, pin ghi trước gửi, timeout create và execute gửi lại đúng UUID/arguments, completed phase không chạy hai lần, response sai spec không được ghi complete, request bị đổi tool bị chặn, lỗi terminal không retry và script ngoài vùng tin cậy bị từ chối.

Các logs red được giữ để chứng minh regression về response binding và pending request chưa được chặn trước sửa. Toàn bộ client network trong tests là fake. Không có compute, dataset thật, binary download hoặc thay đổi split/hyperparameter/KT source.

## Giới hạn còn chờ

Chưa xác nhận quyền free CPU của tài khoản thật, capacity, reconnect qua provider lỗi thật, thời hạn VM hoặc full calibration. Module không tạo keepalive giả. VM vẫn chịu quota/lifetime của Colab, còn artifact/checkpoint nghiên cứu phải tiếp tục lưu Drive theo launcher calibration.

Nếu VM đã mất, client dừng khi kiểm runtime cũ thất bại. Khôi phục artifact và quyết định runtime mới cần root xử lý rõ ràng, không âm thầm bỏ session/phase đang chạy.
