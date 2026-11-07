# AKT tổng hợp trên Colab trong VS Code

**Cập nhật07/11:** agent đã chạy [Colab MCP](akt-colab-mcp.md) trên tab browser/T4, nhận về và kiểm đủ44outputs của CPU505pass, CUDA400targets/1step và controlled fresh-process recovery. `gate4_pass=false`; chưa full training/realdata/Modal/hard-kill/Volume. VSCode manual handoff bên dưới vẫn dùng được, nhưng không còn là kênh duy nhất.

## File duy nhất cần mở

Mở `D:\Dev\KLTN\notebooks\akt_colab_synthetic.ipynb` trong VS Code. Notebook hiện có8cells (1hướng dẫn,7code), nhúng sẵn kit nguồn v12 nên **không cần upload ZIP hoặc sửa đường dẫn**. Cell nguồn dài được đánh dấu thu gọn. Không dùng kernel `.venv` Windows local cho notebook này.

Extensions đã được liệt kê ở máy local: `google.colab`, `ms-toolsai.jupyter`, `ms-python.python`. Việc có extension không chứng minh Google đã đăng nhập hoặc GPU đã được cấp.

## Kết nối và chạy

1. Trong notebook, chọn **Select Kernel → Colab → New Colab Server**; chọn GPU T4 nếu tài khoản được cấp miễn phí. Hoàn tất đăng nhập Google/chấp thuận quyền bằng tài khoản của người dùng. Không mua compute units nếu không có GPU miễn phí.
2. Chạy cell **01 — kiểm kết nối**. Cell chỉ đọc thông tin Python/PyTorch/CUDA/device, không train hoặc cài packages. Phải thấy `CONNECTED_GPU`; nếu lỗi sai kernel/không GPU thì dừng và giữ output.
3. Có thể chọn **Run All** để chạy bộ kiểm tổng hợp nhỏ. Cell02 kiểm SHA rồi giải nén nguồn trong `/content/kltn-synthetic-<run-id>`; cell03 tạo `.venv` riêng ở đó và clone đúng upstream commit. Tạo bằng `--without-pip --system-site-packages` để tránh ensurepip lỗi trên image Colab, kiểm prefix/purelib của venv rồi dùng pip sẵn qua interpreter đó. Cài package còn thiếu vào `.venv`, kế thừa PyTorch runtime, không cài vào Python global.
4. Cell04 CPU portability phải có JUnit không rỗng, không fail/error/skip trước cell05 CUDA lifecycle và cell06 recovery. Mỗi bước có điều kiện chặn, không tự chuyển Modal khi lỗi.
5. Cell07 xuất `/content/akt-colab-results-<run-id>.zip` và file `.zip.sha256`. Với VSCode, mở **Colab → Contents → /content**, nhấp phải từng file → **Download** và xác nhận file đã có ở local. Với MCP, có thể nhận tự động theo chunks rồi kiểm ZIP/từng output SHA; browser download dispatch riêng chưa là local receipt. Lưu thêm notebook có output.
6. Tải kết quả xong dùng **Colab: Remove Server** để giải phóng runtime. Không chỉ đóng notebook rồi giả định server đã dừng.

Nếu bất kỳ bước nào lỗi, không bấm Run All để thử lại ngay. Chạy riêng cell07 để giữ log/checkpoint đã có, kể cả failure. Nếu lỗi xảy ra trước khi tạo workspace, giữ traceback trong output notebook. Không có auto-retry hoặc paid fallback. Kết nối VSCode không tự chia sẻ kernel cho terminal local; kênh [MCP đã kết nối](akt-colab-mcp.md) điều khiển tab browser riêng và đã chạy kiểm thực tế.

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

Kitv12 có139files,346362bytes, SHA256 `ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b`. ZIP ở `artifacts/akt/colab/akt-synthetic-20261107-v12.zip` và bytes nhúng trong notebook phải giống nhau. Allowlist chỉ source/tests/fixtures; không Junyi interactions, credentials, CV/refit/Test predictions hoặc checkpoint. Ba notebook Paper1/2 được strip outputs/metadata trong bản copy, giữ cell source và original hashes; bản gốc không đổi. Khi đổi nguồn, tạo kit mới và cập nhật payload/SHA cùng nhau, không sửa ZIP cũ.

Local Windows source-bound Gate15 đạt462pass,0fail/error/skip,294,17s; [bundle portability](../research_tracking/runs/cpu-portability-gate-20261107-01/README.md) giữ report/log/JUnit, v12 harness20cases và dependency4mockcases. Gate15 không đồng nhất với actual Colab CPU acceptance và không bao gồm SAKT. Gate407/kitv11 là snapshot trước đó: [báo cáo recovery](../research_tracking/reports/colab_recovery_readiness_20261107.md) và bundle `cpu-vscode-colab-notebook-20261107-01` giữ20localcases/extraction137files, có mocked GPU/setup/CPU guards; không sửa các evidence cũ khi cập nhật v12.

## Kết quả actual Colab đã kiểm SHA — 07/11/2026

[Verification JSON](../artifacts/akt/colab/actual-cuda-verification-20261107.json) xác nhận44outputs ở [run directory](../experiments/akt/results/colab-actual-cuda-20261107-01/). CPU log ghi **505 passed,2deselected,117,23s**, không fail/error/skip; [acceptance](../experiments/akt/results/colab-actual-cuda-20261107-01/cpu-acceptance.json) nêu đúng hai exclusions: `test_native_akt_import_cpu` và `test_actual_frozen_assignments_are_unchanged_and_student_disjoint`.

[CUDA lifecycle](../experiments/akt/results/colab-actual-cuda-20261107-01/synthetic-run/report.json) đạt400targets/1optimizer step trong0,916326s, peak VRAM187.200.000bytes. [Recovery](../experiments/akt/results/colab-actual-cuda-20261107-01/synthetic-recovery/report.json) dùng17targets mỗi branch, continuous5steps so interrupted2+fresh-process resumed3, tổng10updates,28,943933s; ledger/RNG/sampler exact, maxstate/predictiondelta0 với declared `atol=rtol=1e-5`. Lifecycle không tự kiểm mid-epoch resume; chính recovery report riêng xác nhận `cuda_mid_epoch_resume_verified=true`. Cả hai vẫn `gate4_pass=false`.

Agent nhận ZIP tự động qua144MCPchunks, tối đa200.000bytes/chunk, tổng28.657.701bytes; SHA256 `64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188`, CRC và mọi outputSHA đã kiểm. Browser download dispatch trước đó chưa chứng minh nhận file ở local. Heavy checkpoints/predictions giữ theo run directory, không đưa vào source kit.

Đây là controlled synthetic optimizer-boundary recovery trong cùng runtime với processes mới; chưa hard-kill/preemption, durable Modal Volume, representative throughput/cost hoặc realdata/full training/RQ efficacy. Không dùng venv kế thừa runtime của Colab để bỏ Linux runtime-origin/image checks của main pipeline.

Lịch sử source kits v4–v11 và các bundles cũ được giữ nguyên; không dùng số tests của kit cũ thay nghiệm thu nguồn hiện tại. Cell upload/download browser của notebook trước sửa đã có snapshot theo evidence/Git, không bị sửa trong bundle đã đóng.

## Kênh điều khiển và chi phí

Ưu tiên **local CPU → Colab free → Modal**. Modal chỉ30USD free credits,0USD trả thêm; không launch từ tài liệu hoặc từ token validity. [FAQ Colab](https://research.google.com/colaboratory/faq.html) nêu GPU/quota/time có thể thay đổi. Không mua paid tier hoặc dùng workaround vượt quota.

[Colab CLI chính thức](https://github.com/googlecolab/google-colab-cli) có terminal execution/upload/download/stop; README được đọc07/11 công bố Linux/macOS, không Windows, chưa cài/chạy CLI hoặc kiểm WSL ở lượt này. [Colab MCP chính thức](https://github.com/googlecolab/colab-mcp) đã cài trong project `.venv`, pin commit `b9ab3899e0f1fa493390b1fd6d54aa2e464ecdf1`, package1.0.1; đã agent-control tab browser/T4 và nhận outputs thật. Xem [hồ sơ MCP](akt-colab-mcp.md) để phân biệt kênh này với VSCode kernel và snapshots mock cũ. Lượt Colab synthetic không dùng compute units trả phí hoặc Modal; hạn mức Modal30USDfree/net0 vẫn giữ nguyên.


Hồ sơ đã đóng: [nghiệm thu CUDA](../research_tracking/reports/colab_cuda_acceptance_20261107.md) và [bundle68outputs](../research_tracking/runs/colab-cuda-synthetic-20261107-01/README.md). Sau khi nhận đủ44outputs local và kiểm không GPU worker khác, guarded runtime.unassign đã trả RELEASE_ACCEPTED; bridge local đã đóng. Đây là APIacceptance, chưa independentcloudlist verification; thao tác đóng bridge tự nó không xóa runtime khác.
