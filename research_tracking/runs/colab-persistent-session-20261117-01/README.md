# Colab OAuth bền vững và đọc runtime bằng official MCP

## Trạng thái

Client đã có12kiểm thử offline đạt. Chưa xác thực Google thật hoặc kiểm quyền API bằng tài khoản Sang trong gói này. Không cài CLI/dependency, không tạo runtime, không thực thi code từ xa, không sửa cấu hình Cloud project/billing và không dùng Modal.

## Đăng nhập một lần trên Edge

Chạy tại repository bằng `.venv` hiện có.

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/colab_session.py login
```

Lệnh mở Edge bằng một trong hai đường cài đặt chuẩn trên Windows, dùng callback localhost cổng ngẫu nhiên và chờ tối đa600giây. Nếu Edge không có, lệnh báo `EDGE_BROWSER_MISSING`, không chuyển sang trình duyệt mặc định.

Client đọc cấu hình ứng dụng Desktop tại `artifacts/akt/private/drive-upload/client_secret.json` nhưng không sửa file đó. Token Colab mới được lưu riêng tại `artifacts/akt/private/colab-session/credentials.json`. Token Drive cũ giữ nguyên. Không gửi nội dung token/client config vào chat hoặc báo cáo. Output đăng nhập không in OAuth URL, authorization code hoặc credentials.

Scopes được yêu cầu gồm `openid`, `userinfo.email` và `colaboratory`. Client dùng account check của Google để yêu cầu đúng Sang trước khi đọc MCP. Scope Colab full chuẩn bị cho quyền API, nhưng phiên bản client hiện tại chỉ cho gọi bốn tool đọc. REST Colab chính thức chấp nhận scope `colaboratory` cho việc đọc subscription/runtime/specs. [Authorization của REST](https://developers.google.com/colab/api/reference/rest/v1beta/TopLevel/getSubscription)

## Các lệnh chỉ đọc

```powershell
.\.venv\Scripts\python.exe -B scripts/akt/colab_session.py subscription
.\.venv\Scripts\python.exe -B scripts/akt/colab_session.py runtimes
.\.venv\Scripts\python.exe -B scripts/akt/colab_session.py specs
.\.venv\Scripts\python.exe -B scripts/akt/colab_session.py runtime runtimes/ID_DA_CO
```

Client gọi endpoint `https://colaboratory.googleapis.com/mcp` bằng `AuthorizedSession`. JSON-RPC dùng `tools/call`, tên tool và arguments theo schema. Hỗ trợ JSON hoặc SSE terminal result. HTTP/RPC errors chỉ in loại lỗi hoặc mã, không đưa server message có thể chứa token/URL vào output. [Endpoint và công cụ chính thức](https://developers.google.com/colab/api/reference/mcp)

Token OAuth hết hạn được refresh bằng refresh token đã lưu. Nếu token bị thu hồi hoặc thiếu scope, lệnh đọc dừng và yêu cầu đăng nhập rõ ràng, không tự bật hàng loạt trang xác nhận. `AuthorizedSession` có thể tự refresh trong request, sau đó client lưu credentials cập nhật atomically. Official CLI cũng sử dụng refresh token và credential persistence, dù CLI hiện chưa hỗ trợ Windows. [Nguồn auth chính thức](https://github.com/googlecolab/google-colab-cli/blob/main/src/colab_cli/auth.py), [phạm vi nền tảng CLI](https://github.com/googlecolab/google-colab-cli)

## Hai loại thời hạn cần phân biệt

OAuth persistent giúp tránh xác nhận lại chỉ vì access token ngắn hạn hết hạn. Runtime proxy token là quyền kết nối khác, thường khoảng1giờ. Client lưu thông tin proxy tại `artifacts/akt/private/colab-session/runtime-proxies.json`, reuse khi còn hơn5phút và gọi `get_runtime` để làm mới khi gần hết hạn. Public output loại `connectionInfo`, token và URL. Chỉ file private có thông tin kết nối đầy đủ. [Hợp đồng get_runtime](https://developers.google.com/colab/api/reference/mcp/tools_list/get_runtime)

Việc refresh quyền truy cập không kéo dài vô hạn vòng đời VM hoặc bỏ qua quota. Để xác nhận khả năng dùng CPU miễn phí, bước tiếp theo cần đọc subscription và specs của đúng tài khoản, chọn spec CPU/NONE/STANDARD có `eligible=true`. Tier FREE không bảo đảm còn capacity tại mọi thời điểm. Gói hiện tại không có tool tạo runtime hoặc execute_code. [Thông tin subscription](https://developers.google.com/colab/api/reference/mcp/tools_list/get_subscription), [runtime eligibility](https://developers.google.com/colab/api/reference/mcp/tools_list/list_runtime_specs)

Nếu sau này nối thực thi, cần giữ session và executionId UUID. Official `execute_code` cho biết request có thể hết hạn sau600giây trong khi code tiếp tục chạy, khi đó reattach bằng cùng request/session/executionId. Sau khi đã nhận terminal result, đánh dấu hoàn tất trước khi retry vì dùng lại ID lúc đó có thể chạy lại code. Đây là thiết kế tiếp theo, chưa được cài trong client này. [Hợp đồng execute_code](https://developers.google.com/colab/api/reference/mcp/tools_list/execute_code)

Tài liệu CLI ghi backend duy trì liveness theo hoạt động kernel và đã bỏ keepalive daemon. Gói này không tạo ping giả hoặc script tránh giới hạn idle. [Lịch sử thiết kế session chính thức](https://github.com/googlecolab/google-colab-cli/blob/main/docs/01_session_management.md)

## API enable và giới hạn chưa kiểm thực tế

Hướng dẫn MCP tổng quát của Google yêu cầu bật product API trong Cloud project và nhắc kiểm billing. REST Colab mô tả quyền người dùng trực tiếp. Chưa kiểm tài khoản/project Sang có cần bước enable riêng hay không, vì chưa đăng nhập mới và chưa gọi endpoint bằng Colab scope. Nếu nhận lỗi quyền/API, giữ mã lỗi an toàn và xử lý đúng nguyên nhân, không tự bật billing hoặc tạo tài nguyên trả phí. [Hướng dẫn MCP của Google](https://docs.cloud.google.com/mcp/enable-disable-mcp-servers)

## Bằng chứng

`tests-red01.txt` giữ lần đầu thiếu module. `tests-edge-red01.txt` xác nhận regression yêu cầu Edge/timeout chưa được cài. `tests03.txt/xml` giữ12ca đạt trong0,56giây, bao gồm refresh/save token không mở browser, explicit login offline, lỗi HTTP/RPC không lộ URL, private path, SSE, proxy expiry/reuse và chặn create_runtime trước network.

Đọc tài liệu và mã nguồn chính thức ngày17/11/2026. Không đọc hoặc in nội dung client secret/token thật khi xây gói này. `MANIFEST.json` pin source/tests/logs của gói.
