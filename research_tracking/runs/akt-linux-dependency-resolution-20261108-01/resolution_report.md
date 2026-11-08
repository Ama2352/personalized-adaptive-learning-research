# AKT: phân giải dependency trên Linux CPU — 08/11/2026

**Đã phân giải được candidate closure 44 packages trên actual Linux CPython3.13.18, chưa cài package hoặc nghiệm thu CUDA.** Kết quả gồm 29 root pins từ profile Windows đang có, đổi riêng Torch2.7.1+cpu thành2.7.1+cu126, cộng14NVIDIA packages và Triton3.3.1. Các hashes trong candidate lock là index/pip-report hashes; không đồng nhất với kiểm độc lập wheel bytes, installed imports, image digest hoặc main-worker/GPU readiness.

Bundle mới: [akt-linux-dependency-resolution-20261108-01](../runs/akt-linux-dependency-resolution-20261108-01/README.md). Nguồn raw nhận về tại `artifacts/akt/colab/gpu08-linux-20261108-01/received/`. Báo cáo này không thay [proposal môi trường trước](../../docs/akt-linux-cuda-environment.md), proposal JSON hoặc bundle `gpu08-environment-proposal-20261108-01` đã đóng.

## 1. Execution thực tế và nguồn

| Thuộc tính | Bằng chứng đã nhận |
|---|---|
| Runtime thực tế | Linux6.6.159+, x86_64, glibc2.39; CPython3.13.18; pip26.2.2 |
| Workspace | `/content/KLTN_GPU08_20261108_01` |
| Target interpreter | `.venv/bin/python`, prefix đúng project venv; purelib trong `.venv/lib/python3.13/site-packages` |
| Venv | Tạo bằng `--without-pip`; `include-system-site-packages=false`. Base pip dùng `--python` để điều khiển target, không cài pip vào target |
| Lượt resume đã chạy | Chỉ `resolve_dependencies.py`; tái dùng venv đã chuẩn bị, không chạy lại bootstrap |
| Command semantics | `pip --python <target> install --dry-run --ignore-installed --only-binary=:all: --report ...`; official PyTorch cu126 index và PyPI, không sdist/build |
| Kết quả | Returncode0, stop_reason=null; `CANDIDATE_CLOSURE_RESOLVED_NOT_INSTALLED` |
| Đo resource | 10,095353 giây cho resolver/cleanup; peak **quan sát** của attempt tree7.350.021bytes, khoảng7,01MiB |
| Budget | 180giây/256MiB kiểm cooperative theo polling và hậu kiểm sau process exit; có thể overshoot, không hard network/disk cap |
| Những gì không thực hiện | 0 package installs, 0 GPU model steps, 0 Modal calls; không import Torch để chạy mô hình |

Source resolver đã thực thi có SHA `39c68ed7921ccd7660ab1e625ab5df6ca3d2cfd473339b2b9babc7de3665b861`. Lượt này có source hash guard trước/sau, cleanup toàn owned process group và post-exit budget guard, nên observed overbudget không được ghi candidate thành công chỉ vì pip đã exit0. Loader resume được bind bằng SHA `4109fab102d2fa93b666e0d88b50874e721667bf0a0cf5691d2374d736d47dc9`; receipt ghi `approved_resolver_executed_once`.

Môi trường resolver là Linux thật, không dùng `pip --platform` trên Windows để giả platform markers. Vì vậy, các điều kiện Linux/x86_64 của Torch đã kích hoạt14NVIDIA dependencies và Triton. Đây là tiến bộ so với proposal chỉ có metadata hai wheels; vẫn chưa phải installation hoặc CUDA execution.

## 2. Candidate profile và closure

[Candidate lock](../runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt) có44dòng URL+SHA, được dựng lại và so raw bytes từ selected pip report. Đây là profile có **29Windows-lock packages được giữ thành root pins**, không gọi là Linux minimal dependency set. Colorama/tzdata có thể là root pin dù một số dependency markers trên Linux không đòi chúng.

| Thành phần | Version | SHA từ official index/pip report |
|---|---|---|
| Torch | 2.7.1+cu126, cp313-cp313-manylinux_2_28_x86_64 | `a05c0001fd1d0ceae9cda8c8c1b8a16ed5def858fe996c9237a28016559dad52` |
| Triton | 3.3.1, cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64 | `b89d846b5a4198317fec27a5d3a609ea96b6d557ff44b56c23176546023c4240` |

Hai digests trên khớp candidate đã ghi từ [official Torch index](https://download.pytorch.org/whl/cu126/torch/) và [official Triton index](https://download.pytorch.org/whl/cu126/triton/) trong bundle proposal cũ. Lần kiểm hiện tại chỉ đối chiếu stored metadata/receipts ở local, không truy cập các URL đó.

| NVIDIA package | Version được chọn |
|---|---|
| nvidia-cuda-nvrtc-cu12 |12.6.77|
| nvidia-cuda-runtime-cu12 |12.6.77|
| nvidia-cuda-cupti-cu12 |12.6.80|
| nvidia-cudnn-cu12 |9.5.1.17|
| nvidia-cublas-cu12 |12.6.4.1|
| nvidia-cufft-cu12 |11.3.0.4|
| nvidia-curand-cu12 |10.3.7.77|
| nvidia-cusolver-cu12 |11.7.1.2|
| nvidia-cusparse-cu12 |12.5.4.2|
| nvidia-cusparselt-cu12 |0.6.3|
| nvidia-nccl-cu12 |2.26.2|
| nvidia-nvtx-cu12 |12.6.77|
| nvidia-nvjitlink-cu12 |12.6.85|
| nvidia-cufile-cu12 |1.11.1.6|

Metadata này không có nghĩa GPUDirect Storage, NCCL communication hoặc các CUDA kernels đã được gọi/kiểm. `--dry-run` cũng không bảo đảm không GET wheel đầy đủ khi metadata thiếu; source giữ `wheel_fetch_absence_proven=false` và `network_byte_cap=false`. Không sửa hai cờ thành true chỉ từ một log trông như toàn `.metadata` hoặc từ peak disk thấp.

## 3. Đối chiếu độc lập sau transfer

Validator mới chỉ đọc local artifacts, dùng parser `pip._vendor.packaging` hiện có để kiểm **selection đã được cung cấp**. Nó không chạy pip resolver, chọn version mới, tải metadata, cài dependency hoặc import Torch. Mỗi Requires-Dist được đánh giá với toàn bộ target environment của report và `extra=''`; không dùng Windows host markers. Không extras nào được requested trong profile này.

| Kiểm độc lập | Kết quả |
|---|---|
| Raw inventory |14/14tệp khớp SHA và size, tổng512.166bytes; manifest/transfer ZIP digest khớp acceptance |
| Source chain |Remote resolver bytes khớp approved39c68…; embedded SPEC khớp input spec; resume receipt khớp loader4109… |
| Root/profile |29root pins đúng version; chỉ Torch build khác Windows CPU lock. Exactly44selected names=29roots+14NVIDIA+Triton |
| Candidate URLs/wheels |HTTPS public PyPI/PyTorch hosts, không credentials/query/fragment; wheel name/version khớp metadata; Linux x86_64/universal và CPython3.13-compatible ABI tags |
| Python requirements |Các Requires-Python của selected packages chấp nhận3.13.18 |
| Active dependency constraints |**46/46** thỏa version trong selection, kể cả Linux CUDA dependencies |
| Inactive metadata entries |432optional/platform-marker entries không hoạt động; không giả chúng là packages thiếu hoặc extras được chọn |
| Candidate lock |44dòng được tái dựng từ pip report và khớp raw bytes/SHA |
| Venv/no-install evidence |Isolated cfg hash đúng; Torch/NumPy/pip find_spec=None cả trước/sau; source ghi probe và tên site entries không đổi |
| Historical preservation |25outputs của proposal bundle cũ vẫn khớp manifest; proposal JSON/docs canonical giữ SHA cũ |

Kết quả chi tiết và mỗi active constraint nằm trong [independent-validation.json](../runs/akt-linux-dependency-resolution-20261108-01/independent-validation.json), cùng source validator. Có thể kiểm tất cả44versions/URLs/hashes ở candidate lock và pip-report snapshot, không cần suy từ bảng rút gọn ở đây.

**Giới hạn no-install:** raw artifacts không xuất full content-hash inventory của toàn site-packages/global filesystem. `isolated_site_unchanged` do source tính từ probe và danh sách tên, không phải byte attestation toàn môi trường. Venv `--without-pip`, target module specs và command dry-run hỗ trợ kết luận không cài package ở stage này; không gọi đó là nghiệm thu installed origins hay chứng minh mọi global byte không đổi. Pip26.2.2 được dùng từ base cho điều khiển, không có pip distribution được cài vào target.

## 4. SHA và lưu bằng chứng

| Artifact | SHA-256 |
|---|---|
| Remote selected-file manifest |`f0dbfd8b5ce20034e5c2ec1a61b348bbe484bc51d6af6a86405d1e0bc1a34cde`|
| Raw pip report |`92a2bbae1cdf285491bac1d67082d16c824aeb2ca9447d841a8182807be671dd`|
| Candidate Linux/CUDA lock |`60dad3de310562db4f775d1977e2097a6d1c8f57a22bfa4f7afc3ceab35cc45a`|
| Raw resolution summary |`32fe949645d44a84e236c5a579be6312cd8c72e19ebd2e8c3c35de0aee216397`|
| Transfer archive, chỉ đối chiếu digest |`5decb9a6cb011e2461e7c0a4978fd358fb2f40feaf5f487004c6227073a98acf`|
| Source Windows CPU lock, giữ nguyên |`3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`|

Bundle mới giữ nguyên bytes14selected files, remote manifest, sources resolver/resume/export/receiver, normalized receipts, independent validation, report và SHA inventories trước/sau copy. `.venv/pyvenv.cfg` là text config, không có Python executable trong archive. Không copy wheels, caches, transfer ZIP/chunks, raw MCP base64 responses hoặc private bridge/auth files. Resume **source code** giữ literal embedded approved-source bytes theo yêu cầu truy vết; không có base64 binary transfer payload hoặc credentials đi kèm. Receiver source chỉ tham chiếu một private-folder path, không chép nội dung folder đó.

Đây là một remote resolver attempt và một lần kiểm offline của cùng bằng chứng, không hai independent runtime experiments. Old proposal/bundles không được ghi lại thành kết quả mới. Source revisions trước preexec và các receipt local vẫn được giữ ở workspace; actual executed source trong archive là39c68….

## 5. Acceptance kế tiếp, chưa được thực hiện ở đây

1. **Wheel bytes và isolated install:** cấp stage/budget riêng, tải và kiểm từng wheel đối chiếu44SHA, kiểm manifest wheelhouse rồi cài hash-only vào project venv/image không kế thừa system packages. Ghi install report, `pip check`, exact versions và origins sau import. Resolver budget180s/256MiB không là allocation cho full wheelhouse hoặc install. Không tự cài global/fallback.
2. **CPU import/binary compatibility:** kiểm Torch/NumPy và native extensions trên Linux target đã cài, actual Python/glibc/ABI và dependency libraries. Candidate metadata không chứng nhận khả năng import. CPU check/report vẫn có device='cpu', không dùng để duyệt CUDA config.
3. **Fresh CUDA runtime contract:** trên stage GPU được cho phép, đo driver, device/architecture, `torch.version.cuda`, availability và strict origins; report schema2 bind executable/prefix/source/Linux lock/requested device. Venv kế thừa Colab packages không được thay isolated origin contract. Proof kitv12 Torch2.14.1+cu130 trên T4 không chứng nhận profile2.7.1+cu126 này.
4. **Main-worker lifecycle trên synthetic:** đúng source/Gate2/context/authorization và caps, kiểm loader→train→validation→checkpoint reload/export/resume cùng VRAM/watchdog. Không coi metadata closure, Windows tests hoặc một optimizer probe khác là Gate4.
5. **Image/durability/forecast:** pin immutable base OS/Python/image digest, kiểm storage/Volume và recovery theo môi trường đích, sau đó đo end-to-end throughput gồm validation/export/inference trước allocation nghiên cứu hoặc Modal pilot. Chưa có image build, Modal compute/credits hoặc quyết định phương pháp/S04/S05 mới từ stage này.

Parent/agent khác chuẩn bị install draft riêng; không đưa future script chưa chạy vào bundle resolution để tránh lẫn mức bằng chứng. Phần việc hiện tại chỉ tạo báo cáo, validator/inventory và archive local; không remote calls, installation, GPU, realdata/Holdout, model runs, root tracking/state hoặc Git writes.
