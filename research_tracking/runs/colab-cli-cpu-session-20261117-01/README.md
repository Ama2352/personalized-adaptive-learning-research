# Consumer transport chính thức để dùng CPU Colab

## Vì sao có transport này

Root đã xác thực Sang thành công, nhưng official MCP mới trả403 vì product API chưa bật trong OAuth project. Nhóm giữ cấu hình Cloud project/billing. Cùng credential đã được root dùng thành công với endpoint consumer do Colab CLI chính thức sử dụng. Gói này tái hiện phần HTTP/Jupyter cần thiết trên Windows, không cài CLI vốn chưa hỗ trợ nền tảng này. [Nguồn client Google](https://github.com/googlecolab/google-colab-cli/blob/main/src/colab_cli/client.py)

## CPU và quota

Request chỉ có variant `DEFAULT`, accelerator `NONE`, không gửi shape high-memory. UUID notebook hash được lưu riêng trên D trước GET/POST. Sau POST chưa rõ kết quả, request tiếp theo GET cùng hash trước để đối chiếu, giữ nguyên định danh.

Admission thực trả `acc='none'`, nên root đã chuẩn hóa riêng trường accelerator theo uppercase trước khi so `NONE`. Assignments vẫn phải xác nhận variant0, acceleratorNONE, shape0 và đúng endpoint riêng. Không có lệnh xóa VM/session của người dùng trong adapter.

Root xác nhận CPU thực có paid balance0, `consumptionRateHourly=0,08` và free quota còn4.568token. Rate đó đo mức tiêu thụ compute units. Guard ban đầu đòi rate0 đã bị sửa tại nguồn thành balance0, rate hữu hạn không âm và hoặc rate0 hoặc free quota còn dương. Các fixture còn kiểm rate dương nhưng thiếu free quota bị dừng. CCU response cung cấp balance/rate/quota, còn tier subscription chưa được xác minh qua endpoint này. [Định nghĩa CCU của CLI](https://github.com/googlecolab/google-colab-cli/blob/main/src/colab_cli/consumption.py)

## Session và discovery

Own notebook UUID được tạo qua Jupyter Contents API và own session Python3 qua Sessions API. Lần tiếp theo tìm đúng notebook path trước khi POST. Sau POST session chưa rõ và chưa thấy session trong list, dừng để đối chiếu thay vì tạo kernel khác. Session notebook cũ của người dùng không bị sửa hoặc xóa. [Jupyter REST](https://jupyter-server.readthedocs.io/en/latest/developers/rest-api.html)

Package `jupyter-kernel-client==1.0.2` đã có trong `.venv`. Discovery dùng kernel ID đã biết, proxy header và websocket token parameter theo runtime.py của Google. Không tạo kernel qua package khi đã có ID. Constructor/start có tối đa3attempt chỉ cho ConnectTimeout/ReadTimeout, cùng kernel ID, chờ2và4giây. Lệnh execute không được gửi lại tự động.

Cleanup đóng channels/socket trực tiếp, không gọi manager.stop hoặc shutdown. Lỗi cleanup không che kết quả/lỗi chính. [Cách kết nối và cleanup của Google](https://github.com/googlecolab/google-colab-cli/blob/main/src/colab_cli/runtime.py)

`discover` chỉ đọc Python, executable và MemAvailable. Không chuyển credential Drive, nạp model hoặc đọc dataset. Proxy URL/token chỉ nằm trong private `artifacts/akt/private/colab-session/cli-runtime.json`; console lọc thông tin đó.

## Đã kiểm và phần còn chờ

`tests11.txt/xml` giữ lượt cuối20kiểm thử offline đạt trong1,20giây, gồm11ca CLI và9ca token runner, sau khi root mở allowlist cho operational driver trong main bundle. Các logs red giữ regression quota, cleanup, constructor retry và phase execution. Nhánh child không chạy API tạo VM hay discovery thật. Việc root thực thi thật có hồ sơ riêng, không được suy thành công chỉ từ tests này.

Entrypoints dùng `.venv/Scripts/python.exe -B scripts/akt/colab_cli_session.py` cùng command `cpu`, `status`, `kernel` hoặc `discover`. Mỗi CLI giữ một writer lock. UserInfo dùng domain `www.googleapis.com/oauth2/v3/userinfo` theo lượt root đã kiểm, thay endpoint OpenID bị lỗi DNS.

Command `execute` yêu cầu file `.py` canonical trong repo `scripts/akt/` hoặc main operational bundle `research_tracking/runs/junyi-calibration-real-20261117-01/`, SHA256 và phase rõ ràng. Phase UUID/source SHA được ghi private trước lần gửi code duy nhất, remote marker atomic chứa PID/status. Code chạy đồng bộ trong kernel, giữ trạng thái busy khi làm việc thực. `--timeout-seconds` tối đa10.860giây cho controller, driver từ root có trần subprocess3giờ. HTTP đọc STATUS/logs có thể theo dõi trong lúc kernel busy.

Khi WS mất sau lúc gửi, phase chuyển UNCERTAIN và lần gọi cùng phase bị chặn để root đối chiếu marker/PID/STATUS trước. Phase COMPLETE trả summary đã lưu. Raw stdout/stderr ở private state, console chỉ in summary. Kernel transport được đóng trong finally và kernel vẫn giữ. Đây là guard local chống chạy hai lần, cần kiểm thực tế khi root triển khai full calibration.

Không có keepalive giả, project API enable, thanh toán Google mới, GPU hoặc Modal CPU trong gói này. Provider vẫn quản lý lifetime/quota của VM.
