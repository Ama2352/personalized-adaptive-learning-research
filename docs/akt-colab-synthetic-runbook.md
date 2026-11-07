# AKT tổng hợp trên Colab trong VS Code

**Cập nhật07/11:** agent đã tự chạy cell qua [Colab MCP](akt-colab-mcp.md) trên tab browser/T4. VSCode manual handoff bên dưới vẫn dùng được, nhưng không còn là kênh duy nhất.

## File duy nhất cần mở

Mở `D:\Dev\KLTN\notebooks\akt_colab_synthetic.ipynb` trong VS Code. Notebook hiện có8cells (1hướng dẫn,7code), nhúng sẵn kit nguồn v11 nên **không cần upload ZIP hoặc sửa đường dẫn**. Cell nguồn dài được đánh dấu thu gọn. Không dùng kernel `.venv` Windows local cho notebook này.

Extensions đã được liệt kê ở máy local: `google.colab`, `ms-toolsai.jupyter`, `ms-python.python`. Việc có extension không chứng minh Google đã đăng nhập hoặc GPU đã được cấp.

## Kết nối và chạy

1. Trong notebook, chọn **Select Kernel → Colab → New Colab Server**; chọn GPU T4 nếu tài khoản được cấp miễn phí. Hoàn tất đăng nhập Google/chấp thuận quyền bằng tài khoản của người dùng. Không mua compute units nếu không có GPU miễn phí.
2. Chạy cell **01 — kiểm kết nối**. Cell chỉ đọc thông tin Python/PyTorch/CUDA/device, không train hoặc cài packages. Phải thấy `CONNECTED_GPU`; nếu lỗi sai kernel/không GPU thì dừng và giữ output.
3. Có thể chọn **Run All** để chạy bộ kiểm tổng hợp nhỏ. Cell02 kiểm SHA rồi giải nén nguồn trong `/content/kltn-synthetic-<run-id>`; cell03 tạo `.venv` riêng ở đó và clone đúng upstream commit. Tạo bằng `--without-pip --system-site-packages` để tránh ensurepip lỗi trên image Colab, kiểm prefix/purelib của venv rồi dùng pip sẵn qua interpreter đó. Cài package còn thiếu vào `.venv`, kế thừa PyTorch runtime, không cài vào Python global.
4. Cell04 CPU portability phải có JUnit không rỗng, không fail/error/skip trước cell05 CUDA lifecycle và cell06 recovery. Mỗi bước có điều kiện chặn, không tự chuyển Modal khi lỗi.
5. Cell07 xuất `/content/akt-colab-results-<run-id>.zip` và file `.zip.sha256`. Mở thanh **Colab → Contents → /content**, nhấp phải từng file → **Download**. Lưu thêm notebook có output.
6. Tải kết quả xong dùng **Colab: Remove Server** để giải phóng runtime. Không chỉ đóng notebook rồi giả định server đã dừng.

Nếu bất kỳ bước nào lỗi, không bấm Run All để thử lại ngay. Chạy riêng cell07 để giữ log/checkpoint đã có, kể cả failure. Nếu lỗi xảy ra trước khi tạo workspace, giữ traceback trong output notebook. Không có auto-retry hoặc paid fallback. Agent terminal local chưa có kênh điều khiển kernel chỉ từ việc người dùng kết nối notebook; chạy qua giao diện VS Code chuẩn đã được chuẩn bị đầy đủ.

Nguồn thao tác giao diện: [Colab VS Code User Guide](https://github.com/googlecolab/colab-vscode/wiki/User-Guide) (đọc07/11/2026). Notebook không còn phụ thuộc `google.colab.files.upload/download`, dùng nguồn nhúng và tải file qua extension. Không cần mount Drive hoặc cung cấp token trong repository.

## Workload và nghiệm thu

| Bước | Giới hạn | Điều kiện đạt |
|---|---|---|
| Setup | venv120s; missing-packages300s; clone180s; pin60s; freeze60s, không optimizer step | `.venv` riêng, upstream `01b7e8d7d7c862cabc9467108e3e7f2555653a88`, logs/runtime identities |
| CPU portability | subprocess600s, worker ẩn CUDA | JUnit có tests>0,0fail/error/skip. Hai exclusions được ghi rõ trong acceptance JSON |
| CUDA lifecycle | d256,H/T100,400targets,1update,subprocess600s | Finite gradients/update,400predictions,checkpoint reload parity1e-6,current/future-label invariance,artifact SHA |
| CUDA recovery | d32,dropout0.2,H/T2,batch2,17targets mỗi nhánh; continuous5 so interrupt2+resume3, tổng10updates | Exact target ledger/RNG/sampler,source checkpoint bất biến; model/Adam/predictions atol=rtol1e-5. Worker60s,controller180s,notebook240s |
| Export | ZIP mới, không ghi đè, chỉ synthetic outputs của run | CRC/từng output SHA trong RESULT_MANIFEST,ZIP SHA ngoài,flags phản ánh cả failure |

Lifecycle report giữ `mid_epoch_resume_verified=false`; recovery chỉ xác nhận CUDA nếu probe riêng đạt thật. `gate4_pass=false` trong cả hai. Đây chưa là full training, real-data pilot, throughput full-fold, hard-kill/preemption hay Modal Volume durability. Không dùng kết quả software để kết luận graph cải thiện RQ1–RQ3.

## Source snapshot và bằng chứng local

Kitv11 có137files,339864bytes, SHA256 `0d4d59a973b4909b26837f795ead499f3b0da6375db3dd6f58096c57530a9f09`. ZIP ở `artifacts/akt/colab/akt-synthetic-20261107-v11.zip` và bytes nhúng trong notebook phải giống nhau. Allowlist chỉ source/tests/fixtures; không Junyi interactions, credentials, CV/refit/Test predictions hoặc checkpoint. Ba notebook Paper1/2 được strip outputs/metadata trong bản copy, giữ cell source và original hashes; bản gốc không đổi. Khi đổi nguồn, tạo kit mới và cập nhật payload/SHA cùng nhau, không sửa ZIP cũ.

Main source-bound Gate2 hiện407passed là CPU software snapshot, không được rerun trong gói sửa frontend này. Notebook nằm ngoài build hashes Gate2 và source ZIP; code/model/tests nguồn v11 không đổi. [Báo cáo recovery](../research_tracking/reports/colab_recovery_readiness_20261107.md) giữ các bước trước. Bundle `cpu-vscode-colab-notebook-20261107-01` lưu kiểm local mới:20cases, extraction137files và ZIP export thật; GPU/setup/CPU guard dùng mocks. Đó là snapshot local trước khi kết nối; actual MCP device discovery và setup Colab hiện đã đạt theo hồ sơ MCP. CUDA model checks còn cần nghiệm thu riêng.

Lịch sử source kits v4–v10 và các bundles cũ được giữ nguyên; không dùng số tests của kit cũ thay nghiệm thu nguồn hiện tại. Cell upload/download browser của notebook trước sửa đã có snapshot theo evidence/Git, không bị sửa trong bundle đã đóng.

## Kênh điều khiển và chi phí

Ưu tiên **local CPU → Colab free → Modal**. Modal chỉ30USD free credits,0USD trả thêm; không launch từ tài liệu hoặc từ token validity. [FAQ Colab](https://research.google.com/colaboratory/faq.html) nêu GPU/quota/time có thể thay đổi. Không mua paid tier hoặc dùng workaround vượt quota.

[Colab CLI chính thức](https://github.com/googlecolab/google-colab-cli) có terminal execution/upload/download/stop, hiện README công bố Linux/macOS, không Windows; chưa cài/chạy CLI hoặc kiểm WSL. [Colab MCP chính thức](https://github.com/googlecolab/colab-mcp) cần client handshake hỗ trợ notifications/tools/list_changed và Python>=3.13; projectPython3.13.5 khớp yêu cầu phiên bản nhưng MCP chưa cài/kết nối. Đây là các hướng khác để điều khiển, không là bằng chứng phiên này đã có kernel access. VS Code notebook là hướng handoff hiện tại người dùng chọn.
