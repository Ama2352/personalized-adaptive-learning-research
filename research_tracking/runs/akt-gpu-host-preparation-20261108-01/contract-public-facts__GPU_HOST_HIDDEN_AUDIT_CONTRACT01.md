# Contract trước code: GPU_HOST_CUDA_HIDDEN_AUDIT_ONLY

08/11/2026. **Proposal trước implementation/dispatch.** Lượt này chỉ đọc source và metadata local, không test, remote, GPU selection/query, import Torch hoặc cài đặt. Giữ nguyên CPU installer v3, auditor gốc và các bundle đã đóng. Đây không là authorization dùng hardware; người dùng tự chọn free T4 ở bước sau.

## Piece tối thiểu và API

Chỉ thêm controller artifact `gpu10-hidden-audit01/hidden_audit01.py` và test stdlib riêng; không sửa production/native/config/Gate reader. Output remote mới độc quyền `/content/KLTN_GPU08_20261108_01/gpu-host-hidden-audit-<attempt-id>/`. Trusted ROOT/venv entry giữ nguyên; không arbitrary-root CLI.

CLI bắt buộc: `--mode GPU_HOST_CUDA_HIDDEN_AUDIT_ONLY`, `--expected-source-sha256`, `--attempt-id`, `--approval-reference`, `--baseline-discovery PATH --baseline-sha256`, `--fresh-discovery PATH --fresh-sha256`, `--fresh-launcher PATH --fresh-launcher-sha256`, `--fresh-acceptance PATH --fresh-acceptance-sha256`, `--profile PATH --profile-sha256`. Startup manifest là input tùy chọn **đã review actual bytes**, có path+SHA đi đôi; mặc định không chấp nhận executable startup hook lạ. Mọi path là relative POSIX trong owned ROOT, chặn escape/symlink/private/protected paths; SHA strict64hex, schema bool bị reject. Không có install/repair/execute-model option.

Accepted verdict duy nhất: `GPU_HOST_CUDA_HIDDEN_CPU_AUDIT_ACCEPTED_NOT_CUDA_READY`. Cold/missing/partial/unknown startup/fingerprint mismatch trả STOP với0target child, giữ log; không tự tạo venv/cài/repair hay fallback CPU workflow. Accepted phase có **đúng một target child**, không thêm discovery/pip/check-runtime subprocess bên trong phase này.

## Inputs có nguồn thật, không giả host parity

- **Baseline CPU:** actual discovery02 raw SHA `b0032f9d556d0ca3655d4bafa6d010d30feca05e1d4d6c02ac8148757d8c4ec9`, source02 SHA `51c4b98053ba4eaac42b8c8be51ac29645c0b5fdcdf243b19d07c760a8a9db5f`, profile SHA `0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228`. Nó là pre-switch metadata baseline, **không phải fresh GPU-host evidence**.
- **Fresh sau manual selection:** phải là discovery thực tế mới, được parent nhận/hash/review; SHA khác baseline; source/profile/ABI/pyvenv/source165/selected44versions/metadata+RECORD fingerprints và tám origin fingerprints khớp kỳ vọng. Check fresh launcher/inner RC0+cleanup accepted, exact result SHA và pre/post source digest. Fresh host signals phải ghi GPU-host indication, TPU absent; reject CPU baseline, cold/partial hoặc không có indication. COLAB_GPU/device-entry names không chứng minh model T4/compute capability: visible hardware probe vẫn để phase sau.
- **Historical install provenance:** pin/read-only original44 selected wheel report, install02 report, lock60dad, original failed02 result/output manifest/pip-check stdout/source021 và cfg0b853... như auditor gốc. Chúng là lịch sử cài đặt CPU, không đổi tên thành install trên host mới. Thiếu proof hoặc bytes khác thì STOP/review, không chép proof cũ để tạo host mới giả.

Metadata fingerprints khớp không là full installed-site-byte attestation hay whole-host/runtime persistence. Không gọi hai host là giống nhau chỉ vì path ROOT và version strings giống nhau. Nếu VM reset làm mất venv/root hoặc ABI/profile đổi thì stage này không áp dụng; cold provisioning là source/approval khác.

## Reuse thuật toán auditor, giữ guards gốc

Chỉ reuse **CHILD template** của `gpu08-linux-20261108-01/post_install_audit01.py`, source SHA `dd7738bfe06032ffaea6a921619767fd659e626ff53ee5a2a7203fb33f885132`; template UTF-8 SHA **`a2b6bf03cb1c0a546a4d437525a80e869edfc6ed1abaca11fdc177b2c3991d98`**. Embed/extract bằng AST rồi hashcheck; chỉ thay đúng một sentinel `EXPECTED_VERSIONS` bằng selected44 như source gốc. **Không gọi old main**, vì old main chủ động reject GPU host và guard đó phải giữ nguyên; CPU-v3 source578181... cũng không đổi.

CHILD giữ exactly44 names/versions, top-level hai-part `*.dist-info/METADATA` duy nhất, Name/Version đúng và **mọi RECORD origin** trong venv, gồm nested vendored metadata/bin scripts. Fresh normal startup phải cho lexical executable `.venv/bin/python`, actual prefix=venv, base=/usr, ABI/profile đúng, no inherited external sites và user-site disabled. Không fake `sys.prefix` hoặc dùng no-site prefix `/usr` làm bằng chứng normal startup.

Old eight CPU imports là **torch,numpy,pandas,duckdb,sklearn,scipy,psutil,pytest**. Discovery tám origin fingerprints dùng **packaging thay pytest**; không gọi hai tập là đồng nhất. So discovery fingerprints ở đúng tám entrypoint của discovery trước/sau; old CHILD vẫn import đúng old8, kiểm mọi imported origin trong venv. Giữ Torch2.7.1+cu126/build metadata12.6, explicit CPU scalar, `cuda.is_initialized()==False` trước/sau. Không model constructor/forward/backward/optimizer.

**Không gọi `check_runtime` trong hidden phase:** source hiện gọi `cuda.is_available()` kể cả CPU report. Không pip/check/install, network, device_count/properties/name/arch list, nvidia-smi hoặc visible CUDA runtime probe. New audit output không được dùng làm runtime CUDA report/authorization. CUDA runtime native phải được tạo ở phase visible riêng sau này.

## Startup preflight trước target normal startup

Controller stdlib đọc/check không thực thi các startup hooks ở actual no-site sys.path + explicit venv purelib, trước khi launch target `-I -B`. Kiểm source/profile/ABI/metadata baseline, cfg excludes system sites và actual RECORD file hashes khớp fresh/baseline; dùng những RECORD đã bind đó để kiểm declared hash/path của startup files và các imported startup helper nếu có. Bounded metadata/text reads, không scan/hash fullsite bytes vô hạn.

Unknown `.pth`, `sitecustomize`/`usercustomize` hoặc hook/helper bytes chưa được parent review: **STOP_NO_CHILD**, emit nhỏ path/SHA/bounded text để review; không tự coi hook trong setuptools là an toàn, không lấy canonical SHA từ trí nhớ hoặc Windows local venv. Nếu actual Linux hook manifest đã được review thì chỉ exact path+bytes/RECORD binding đó mới được phép. Không viết generic hook evaluator hoặc sửa/xóa hook. Nếu actual reviewed hook cần `SETUPTOOLS_USE_DISTUTILS=stdlib` để vô hiệu shim, environment flag đó cũng phải được review/bind trong contract nguồn mới; chưa tự adopt từ một Windows sample.

Child env được controller tạo trước launch: CUDA_VISIBLE_DEVICES/NVIDIA_VISIBLE_DEVICES rỗng, PYTHONNOUSERSITE=1, `-I -B`, OMP/MKL/OpenBLAS2; loại inherited PIP_/UV_/PYTHON*/CONDA_/VIRTUAL_ENV và custom HOME. HOME/TMP/cache/Torch/Triton/CUDA cache trong owned stage mới, PIP_CONFIG_FILE=/dev/null; không thay global env/dependencies. Unknown startup hook không được xử lý bằng cách bỏ normal prefix check hoặc chạy fake site initialization.

## Budget, cleanup và outputs

**90s tổng** gồm preflight, child, cleanup, hashes và final inventory; child deadline dùng remaining budget có reserve cleanup. Giữ workspace20GiB/min30GiB free như auditor gốc, cooperative sampling (không hard quota/network cap). Một target PID/session/PGID; cleanup_attempted đặt trước signal, immediate finally cleanup_once/reap; handled PGID không signal lại; signal/reap/resource/post-exit deadline failure đều chặn accepted. Final receipt giữ RC/elapsed/cleanup cả khi child lỗi. Không lặp lỗi discovery01 làm mất failed child receipt. Không suy external cancellation/global cleanup đã được chứng minh; outer bridge timeout không là lý do rerun.

Artifacts nhỏ: `result.json`, `audit-child.py`, `audit.stdout/.stderr`, `input-hashes.json`, `startup-preflight.json`, `resources.json`, `output-manifest.json`; failure giữ `failure.log`. Bind new source/template/profile/baseline/fresh receipt/selected44/lock/source165/pyvenv và startup manifest SHA trước/sau. Ghi mode, actual host signals, đúng1target child accepted, normal prefix/origins, CPU scalar, CUDA uninitialized. Reply toàn bộ≤48000byte; nếu quá thì path/SHA và bounded text frames, không whole binary/base64 archive.

`gpu_device_queries=0` của CHILD là ledger **0 explicit device-query calls trong source**, không instrumentation/attestation mọi syscall bên trong dependency imports hoặc cả host. CUDA hidden + `is_initialized=False` không tự chứng minh không có mọi dạng driver/library lookup. Kết quả accepted chỉ là CPU import/origin audit trên host có indication GPU, không CUDA-ready/T4-ready/resume/image/Modal/research proof.

## Validation nhỏ đề nghị sau khi root approve implementation

Cap local stdlib checks **≤30s cumulative mới**,0actual target/model/device/install/network, không rerun suite40/Gate. Khoảng12nhóm guard: exact CLI required mode/flags; CPU baseline-as-fresh; cold/noGPU-indication/TPU; bool/schema/SHA/path; changedsource/profile/ABI; changed44metadata/origins; missing/inherited venv; unknown/modified startup; explicit child env; unchanged CHILD+old8imports/no availability calls; cleanup/reap/postexit-budget negatives; synthetic accepted payload với1child và allnormalprefix/origin/scalar flags. Reuse stored old auditor metadata regressions làm provenance; không nói mock output là actual GPU-host success.

**Chưa implementation/test/remote trong contract này.** Root review trước; actual fresh post-manual GPU discovery và startup-hook evidence chưa tồn tại thì không có accepted audit request để dispatch.
