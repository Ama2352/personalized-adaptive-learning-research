# AKT đã qua kiểm tra CUDA tổng hợp trên Colab T4 — 07/11/2026

## Kết luận

Agent đã thực sự chạy AKT qua Colab MCP: setup, kiểm tra CPU, một bước cập nhật GPU, lưu/nạp checkpoint, xuất dự đoán và khôi phục ở tiến trình mới đều đạt hợp đồng của probe. Không dùng Computer Use, không cần người dùng chạy từng cell và không dùng credit Modal. Đây là **nghiệm thu kỹ thuật có giới hạn**, chưa là full training, Task14/Gate4 hoặc bằng chứng cải thiện cho ba RQ.

## Nguồn và môi trường

- Upstream AKT: `01b7e8d7d7c862cabc9467108e3e7f2555653a88`; baseline NonRasch không prerequisite graph.
- Kit nguồn v12: 139 file, SHA-256 `ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b`. Nguồn AKT/shared/GAM và fixtures được hash trước các bước GPU. Package SAKT mới được kiểm riêng, chưa nằm trong kit này.
- Runtime thực tế: Python3.13.16, Torch2.14.1+cu130, CUDA13.0, Tesla T4. Dependency/runtime freeze nằm trong artifacts; môi trường này khác Windows CPU và chưa là Linux training lock được duyệt.
- Tạo `.venv` trong workspace Colab bằng `--without-pip --system-site-packages`, kiểm prefix/purelib trước cài dependency. Chỉ cài DuckDB1.5.6 vào venv; PyTorch kế thừa runtime. Không cài Python global.

## Kết quả đã kiểm

| Bước | Kết quả thực tế | Giới hạn diễn giải |
|---|---|---|
| Local Gate15 | 462 pass, 0 fail/error/skip; 294,17 giây | Suite AKT/shared trên Windows CPU; không bao gồm SAKT mới |
| CPU trong Colab | 505 pass, 2 deselected đã khai báo; 0 fail/error/skip; 117,23 giây | Có thêm GAM tests, nên không so trực tiếp số test với Gate15 |
| CUDA lifecycle | 400 targets, 1 optimizer update; finite gradient và thay đổi tham số; 400 predictions xuất đủ | Dữ liệu tổng hợp, không phải một epoch Junyi hoặc throughput đại diện |
| Checkpoint reload | Dự đoán sau reload khớp trong atol=rtol1e−6 | Kiểm trên chính runtime và artifact của probe |
| Nhân quả đầu vào | Đổi đáp án hiện tại/tương lai không đổi các dự đoán được bảo vệ | Kiểm fixture, không chứng minh mọi pipeline dữ liệu khác đều không leakage |
| CUDA recovery | Continuous5 updates so với interrupt2+resume3; 17 targets mỗi nhánh; tổng10 updates qua3 tiến trình | Ngắt có kiểm soát ở committed optimizer boundary; không hard-kill/preemption |
| Recovery parity | Model/Adam/predictions đạt tolerance1e−5; max state/prediction delta thực tế bằng0; ledger/RNG/sampler exact; interrupted checkpoint bất biến | Không suy tính quyết định cho mọi GPU, batch, kernel hoặc training run |

Bước optimizer lifecycle đo 0,916326 giây, peak allocated VRAM187.200.000bytes. Recovery mất28,943933 giây. Các số này không gồm đầy đủ startup/setup, nhiều epoch, validation, export, inference controller hoặc đồng bộ storage. **Chưa có cost/target đáng tin để dự báo fullCV hay complete experiment matrix.**

Hai ngoại lệ CPU giữ nguyên là `test_native_akt_import_cpu` và `test_actual_frozen_assignments_are_unchanged_and_student_disjoint`. Không thêm skip/xfail/exclusion để vượt gate. Các lỗi lịch sử vẫn lưu trong [preflight thất bại](../runs/colab-mcp-preflight-20261107-01/README.md):435pass/7fail/8errors. Lượt mới dùng workspace/source kit mới, không thay số liệu của lượt cũ.

## Vị trí bằng chứng

- [Bundle nghiệm thu CUDA](../runs/colab-cuda-synthetic-20261107-01/README.md): báo cáo, logs, JUnit, manifests, dự đoán tổng hợp, raw MCP receipts đã lọc và SHA inventories.
- Checkpoints/binary đầy đủ: `experiments/akt/results/colab-actual-cuda-20261107-01/`; giữ theo run, không đưa checkpoint lớn vào Git.
- ZIP gốc: `artifacts/akt/colab/actual-cuda-synthetic-20261107-01.zip`, 28.657.701bytes, SHA-256 `64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188`.
- Đã nhận tự động qua144 chunks tối đa200.000bytes/chunk, kiểm từng chunk và ZIP, CRC và toàn bộ44file đầu ra trước khi lưu bản trích. Cách tải qua browser được dispatch nhưng không có file local; không coi dispatch là tải thành công. Không cần user tải lại ZIP.

Sau khi nhận đủ artifacts, lệnh giải phóng đúng runtime thử nghiệm đã trả `KLTN_RUNTIME_RELEASE_ACCEPTED`; guard xác nhận không có GPU worker khác trước lệnh. Colab API đã chấp nhận unassign; chưa kiểm độc lập danh sách runtime phía cloud. Local MCP bridge đã đóng. Trường `remote_runtime_deleted=false` của client close chỉ nói chính thao tác đóng bridge không xóa runtime, khác lệnh unassign riêng đã được ghi receipt.

## Những gì còn chặn GPU training chính thức

Main worker chưa có hợp đồng Linux/CUDA tương đương: `authorization.py::preflight` còn kiểm đường dẫn Windows `.venv/Scripts/python.exe`; runtime validator yêu cầu origin Torch/NumPy trong venv; phase smoke/pilot hiện chỉ cho CPU. Probe độc lập chạy thành công không tự thay các điều kiện đó. Cần thiết kế explicit platform/runtime-origin mode và bounded GPU phase với negative controls; giữ nguyên safeguards Windows CPU, không âm thầm nới checks.

Tiếp theo cần nghiệm thu lifecycle của **main worker** trên synthetic cohort, định danh dữ liệu/split/vocabulary, train/validation/best-checkpoint/export/resume; sau đó mới benchmark đủ train/validation/export/inference overhead để lập budget. Modal cần revalidation image/Volume/checkpoint durability riêng. Không sử dụng Windows CPU wheel lock trên Linux CUDA.

`gate4_pass=false` trong cả hai CUDA reports. Chưa chạy Junyi/Grade10 training thật, không truy cập Holdout/Test, không fullCV, không chi tiền hoặc credit Modal. S04 mastery/calibration/controller và S05 phân bổ model–môi trường vẫn cần chốt trước các thí nghiệm kết luận; kết quả âm của graph vẫn được chấp nhận nếu bằng chứng hợp lệ.


## Cập nhật sau snapshot sourcekitv12

Batch runtime/mainworker sau đó đã sửa platform-aware executable/schema2 và kiểm syntheticParquet worker trên CPU (Gate17:513pass). Đọc [runtime](akt_linux_runtime_contract_20261107.md), [worker](akt_main_worker_lifecycle_20261107.md) và [contract20](../../docs/thesis_recovery/20_LINUX_CUDA_WORKER_CONTRACT.md). Phần blocker hardcodeWindows phía trên mô tả snapshotv12; component đó đã sửa, nhưng runtime-path wiring/publicGPUphase/LinuxCUDAhashlock và actualmainworkerCUDA vẫn chưa hoàn tất. BundleCUDAcũ giữ nguyên; không gán kết quảT4v12 cho source mới.
