# Agent chạy notebook qua Colab MCP — 07/11/2026

## Trạng thái đã xác nhận

Đã cài Colab MCP chính thức trong `.venv` của KLTN, pin Google commit `b9ab3899e0f1fa493390b1fd6d54aa2e464ecdf1`, package1.0.1/FastMCP2.14.5/MCP1.30.0. Thêm88packages bằng wheels có SHA;57package cũ giữ nguyên phiên bản, `pip check` đạt. Không cài Python global, không đổi lock AKT hoặc kiến trúc/protocol nghiên cứu.

Agent đã gọi tool thật `get_cells`, `update_cell`, `add_code_cell`, `run_code_cell`. Cell thử trả `2+2=4` từ Colab; sau khi user chọn T4 trong tab browser, agent nhận trực tiếp Python3.13.16/PyTorch2.14.1+cu130/TeslaT4/CUDA khả dụng. Đây là thực thi từ xa đã được agent ghi nhận, khác với JSON cell01 trước đó do user dán. Device discovery không tự chứng minh model chạy; lượt synthetic CUDA và recovery riêng đã có outputs nhận về local và kiểm SHA như bảng dưới.

MCP này nối **tab Colab trong trình duyệt**, không tự kế thừa kernel VSCode. Tab scratch đầu dùng CPU; user đã chuyển tab đó sang T4. Không yêu cầu user bấm Run All: agent điều khiển từng cell và kiểm outputs. Giữ tab MCP riêng trong lúc chạy; tool/runtime errors phải được phân loại trước retry. Không dùng Computer Use, SSH/tunnel, Colab paid tier hoặc Modal trong thiết lập này.

## Kết quả synthetic đã nhận và kiểm — 07/11/2026

Nguồn: [verification local](../artifacts/akt/colab/actual-cuda-verification-20261107.json) và [44 outputs gốc](../experiments/akt/results/colab-actual-cuda-20261107-01/). Kit hiện dùng là **v12, 139 files**, SHA `ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b`. Local Windows Gate15 đạt **462 pass**, 0 fail/error/skip, 294,17s; đây là source snapshot riêng với actual Colab acceptance.

| Kiểm thực tế trên Colab/T4 | Kết quả và giới hạn |
|---|---|
| CPU portability | **505 passed, 2 declared exclusions**, 0 failure/error/skip, 117,23s. [Acceptance JSON](../experiments/akt/results/colab-actual-cuda-20261107-01/cpu-acceptance.json) ghi rõ `test_native_akt_import_cpu` và `test_actual_frozen_assignments_are_unchanged_and_student_disjoint` bị loại; không gọi đây là main real-data Gate2. |
| CUDA lifecycle | [Report](../experiments/akt/results/colab-actual-cuda-20261107-01/synthetic-run/report.json): 400 synthetic targets, 1 optimizer step, 0,916326s, peak VRAM 187.200.000 bytes; gradient/update, checkpoint reload, export coverage và causal checks đạt. Lifecycle riêng vẫn có `mid_epoch_resume_verified=false`. |
| Controlled CUDA recovery | [Report](../experiments/akt/results/colab-actual-cuda-20261107-01/synthetic-recovery/report.json): 17 targets mỗi logical branch, continuous 5 steps so interrupted 2 + fresh-process resume 3, tổng 10 updates; 28,943933s. Target ledger/RNG/sampler exact; max state/prediction delta đều 0 với declared `atol=rtol=1e-5`. Đây là optimizer-boundary interruption trong cùng runtime, không hard-kill/preemption hoặc Volume durability. |

Cả hai CUDA reports giữ **`gate4_pass=false`**. Không full training, realdata/Holdout, Modal compute hoặc RQ efficacy. Colab dùng project venv kế thừa runtime packages; kết quả không thay Linux runtime-origin authorization hoặc image/Modal Volume contract của pipeline nghiên cứu.

Browser download đã được dispatch nhưng không được coi là file nhận thành công ở local. Agent nhận ZIP tự động qua MCP thành **144 chunks, tối đa 200.000 bytes/chunk**, ghép đủ **28.657.701 bytes**; ZIP SHA `64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188`, CRC và SHA từng output đã kiểm. Heavy checkpoints/predictions giữ ở output directory trên; không chép raw private MCP receipts/nonce vào tài liệu. Modal 30USD free credits/net trả thêm 0USD chưa được dùng bởi lượt kiểm này.

## Client terminal đang dùng

`scripts/colab_mcp_client.py` dùng trực tiếp FastMCP Client và server/proxy của Google. Không cần sửa cấu hình MCP global hay restart ứng dụng để có thể gọi tool từ terminal trong phiên này. Vì dùng client terminal, Colab không tự xuất hiện như một tool mới trong danh sách builtin của chat.

```powershell
.\.venv\Scripts\python.exe -u -B scripts/colab_mcp_client.py --open-browser --ttl-seconds 7200
```

Tiến trình cần quyền loopback local. Trong tiến trình hạn chế mạng trên Windows, `asyncio.run` treo tại socketpair/accept trước khi MCP khởi động; diagnostic30s đã chỉ ra vị trí đó. Lượt ngoài giới hạn mạng đã được duyệt chạy thành công: list tool rồi close, không browser/GPU. Không đổi policy toàn máy để né lỗi.

Client nhận từng JSON qua stdin:

```json
{"action":"status"}
{"action":"list"}
{"action":"call","name":"get_cells","args_file":"D:/Dev/KLTN/artifacts/akt/colab/requests/get-cells.json"}
{"action":"close"}
```

Arguments phải ở `artifacts/akt/colab/requests/*.json`, tối đa2MiB. Response đầy đủ nằm trong `artifacts/akt/private/colab-bridge/session-*/result-*.json`; preview trên terminal có thể bị wrap/truncate, không chép thủ công UUID từ ConPTY. Dùng file JSON thật để lấy `newCellId` và output. Không coi `is_error=false` của MCP là cell đạt: phải kiểm `output_type=error`, transcript và artifact contracts.

Client chỉ relay lệnh có chủ đích, không tự cấp/xóa runtime hoặc mua credits. Timeout tool1–660s và TTL tối đa2giờ; các subprocess notebook vẫn có caps riêng. Đóng client không tự xóa runtime: giải phóng runtime Colab sau khi xuất/nhận đủ artifacts. Mất kết nối không được coi là lý do tự chạy lại model.

Nonce websocket chỉ nằm trong bộ nhớ/tab Google; không in URL nonce. Logs/raw responses mặc định private và Git-ignored; chỉ sao evidence đã kiểm không chứa credentials. Không gửi token/mật khẩu trong chat. Giữ các quyền xác thực của Google ở giao diện Google.

## Cài đặt có kiểm soát

Wheels ở `artifacts/akt/colab/client-wheels`, package versions/hashes ở `requirements-colab-client.lock.txt`. Đây là **Windows local controller lock**, không phải Linux/CUDA training lock. Wheel colab-mcp được build từ source pin; cần giữ wheel/hash hoặc lập hồ sơ lock mới khi dựng lại, không dùng package cùng version từ nguồn khác để thay ngầm.

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --find-links artifacts/akt/colab/client-wheels --require-hashes -r requirements-colab-client.lock.txt
.\.venv\Scripts\python.exe -m pip check
```

Không chạy `pip install` global hoặc tự nâng57package baseline. Installer đã cảnh báo không dọn được một số temp folders trong vùng tạm của tiến trình; không xóa hoặc thay ACL để xử lý cảnh báo đó.

## Notebook và chuẩn bị môi trường Colab

Nguồn chạy hiện tại là7codecells từ `notebooks/akt_colab_synthetic.ipynb`, kitv12 nhúng139files, SHA `ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b`. Bản chuyển MCP có thêm cell thử/ghi chú; map local→remote cell IDs ở `artifacts/akt/colab/mcp-cell-map.json`. Kitv11 và các setup failures dưới đây là lịch sử, giữ nguyên bytes và verdict.

Lượt setup01 thất bại ở `python -m venv` khi gọi ensurepip, trước model/optimizer step. Giữ workspace cũ và xuất ZIP9161bytes SHA `86f2719d6084ad57c58f892ea365920ea937a5293a2a7b838e8a501690dfec51`; đã kéo về local và kiểm CRC/từng output SHA.

Setup02 dùng `venv --without-pip --system-site-packages`, đọc pip sẵn của runtime qua system-site-packages. Trước mọi install, kiểm `sys.prefix != sys.base_prefix`, prefix đúng ROOT/.venv và `sysconfig.purelib` nằm trong `.venv`. Pip chạy bằng interpreter `.venv`, nên destination vẫn là venv; không cài global. Đã kiểm native local và actual Colab setup thành công trong workspace mới, không ghi đè failure.

Chỉ chạy CUDA model khi CPU portability đạt, giữ caps của runbook. Gate4/full training/throughput/research efficacy không tự đạt từ việc MCP kết nối hoặc setup thành công.

Nguồn: [Google Colab MCP](https://github.com/googlecolab/colab-mcp), [Python venv](https://docs.python.org/3.13/library/venv.html), [MCP trong Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli). Các source được đối chiếu ngày07/11/2026; kết nối thực tế được xác nhận bằng MCP responses, không suy từ tài liệu.

## Lịch sử preflight thực tế đầu tiên — giữ verdict thất bại

Sau setup02, suite CPU trong Colab chạy115.86s: **435passed,7failed,8errors,2deselected**, JUnit450cases,0skip. GPU lifecycle/recovery chưa được gọi vì CPU_PORTABILITY_OK vẫnfalse. Không đổi gate, bỏ thêm test hoặc sửa số liệu để đi tiếp.

12trường hợp lỗi nằm ở fixture DuckDB COPY TO ? trên phiên bản1.3.2 của runtime;3trường hợp còn lại là2test retry PermissionError theoWindows và1test wheel Windows trênLinux. Đây là phân loại từ JUnit/traceback, không kết luận mọi lỗi đều chỉ do môi trường cho đến khi có regression phân biệt. Runtime đang dùngNumPy2.4.6,pandas2.2.3,pytest8.4.2,Torch2.14.1+cu130. Cần pin/kiểm dependency API và làm fixtures platform-explicit; không nới validator Windows hoặc bỏ gate để chạy GPU.

ZIP preflight failure32693bytes SHA `bed12d2a1ff28de5ad4d7d23a1dc637793eab4972d4ff21e474a2c59b554cdbb` đã được agent kéo qua MCP về local và kiểm CRC/từng outputSHA. Không cần user tự download hai ZIP failure nhỏ; không ghi đè workspace cũ. Main local Gate407 lúc đó là snapshot source/Windows riêng, không được trình bày như450testColab đã đạt. Lượt v12/505-pass và actual CUDA phía trên có identity/output riêng, không viết lại failure này.

## Phương án Kaggle sau câu hỏi của user

Kaggle CLI chính thức hỗ trợ `kernels push` để gửi/chạy notebook, `kernels status` theo dõi và `kernels output` tải artifacts; có timeout và `--no-run`. Đây là hướng đáng cân nhắc cho jobbatch tự động, không cần giữ frontend notebook cho từng lệnh như bridge Colab. Nguồn đọc07/11/2026: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md. GPU/quota/thời lượng/entitlement tài khoản Kaggle chưa kiểm; không gán mốc30h hoặc đảm bảo hardware từ tài liệu chung. Chưa cài Kaggle SDK, xác thực, upload dataset/notebook hoặc cấp runtime.

Colab hiện đã có v12 CPU acceptance và bounded CUDA/recovery evidence được nhận về local; không cần chuyển provider chỉ để xử lý preflight failure cũ. Kaggle vẫn là phương án jobbatch chưa được thiết lập/xác thực, chỉ xem xét khi có nhu cầu hoặc quota/độ ổn định Colab thực sự chặn. Không tự launch nền tảng khác hoặc thay protocol/model/dataset từ đề xuất vận hành này.


Hồ sơ đã đóng: [nghiệm thu CUDA](../research_tracking/reports/colab_cuda_acceptance_20261107.md) và [bundle68outputs](../research_tracking/runs/colab-cuda-synthetic-20261107-01/README.md). Sau khi nhận đủ44outputs local và kiểm không GPU worker khác, guarded runtime.unassign đã trả RELEASE_ACCEPTED; bridge local đã đóng. Đây là APIacceptance, chưa independentcloudlist verification; thao tác đóng bridge tự nó không xóa runtime khác.
