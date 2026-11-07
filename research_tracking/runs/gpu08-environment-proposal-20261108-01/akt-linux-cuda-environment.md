# Đề xuất môi trường AKT Linux/CUDA — GPU08, chỉ chuẩn bị

Ngày08/11/2026. **Trạng thái PARTIAL / proposal_only; chưa có Linux CUDA hash lock hoàn chỉnh, install report hoặc image digest.** File [proposal JSON](../experiments/akt/configs/linux-cuda-runtime-proposal.json) là tài liệu môi trường, không phải AKTConfig runnable hay authorization. Chưa cài package, tải wheel, dựng image, tạo Volume, chạy GPU/Modal hoặc thay phân bổ tài chính.

## Môi trường được đối chiếu

| Nguồn | Định danh đã thấy | Ý nghĩa và giới hạn |
|---|---|---|
| `requirements-akt.in`, `requirements-akt.lock.txt`, `artifacts/akt/preflight/runtime-v2.json`; đọc distribution metadata local | Windows CPython3.13.5, Torch2.7.1+cpu; lock có wheel cp313-win_amd64 | Là runtime CPU đang có; wheel Windows không dùng cho Linux/CUDA |
| `experiments/akt/results/colab-actual-cuda-20261107-01/synthetic-run/report.json`, `setup-status.json`, `artifacts/akt/colab/actual-cuda-verification-20261107.json` | Linux CPython3.13.16, Torch2.14.1+cu130, CUDA13.0, Tesla T4; runtime packages inherited | Probe actualCUDA kitv12 đã pass trong phạm vi synthetic. `gate4_pass=false`; không chứng nhận runtime đề xuất này hoặc main worker hiện tại |
| Official PyTorch index + PEP658 METADATA ngày kiểm | Torch2.7.1+cu126, cp313-cp313, manylinux_2_28_x86_64 | Candidate giữ base Torch2.7.1, đổi build CPU→CUDA. Chưa kiểm binary/kernel hoặc numeric parity |

PyTorch công bố riêng Torch2.7.1 với CUDA12.6 cho Linux/Windows. AKT hiện không cần thêm torchvision/torchaudio chỉ vì chúng xuất hiện trong lệnh ví dụ của website. [Previous versions](https://pytorch.org/get-started/previous-versions/).

Kitv12 khác cả Torch/CUDA build và origin contract: nó dùng venv `--system-site-packages`. Main worker hiện vẫn yêu cầu Torch/NumPy ở trong isolated project venv, Linux executable `.venv/bin/python`, prefix/source/lock/platform bound và runtime report mới. Không đổi origin guard hoặc coi inherited Colab packages là isolated install. Linux entrypoint có thể symlink ra base interpreter nhưng prefix vẫn phải đúng venv; không resolve executable đến base rồi dùng base path làm identity. Xem [worker contract](thesis_recovery/20_LINUX_CUDA_WORKER_CONTRACT.md).

## Candidate được xác minh bằng metadata nhỏ

Nguồn index chính thức: [Torch cu126](https://download.pytorch.org/whl/cu126/torch/), [Triton qua PyTorch](https://download.pytorch.org/whl/cu126/triton/). Các đường dẫn wheel dưới đây **chưa được GET/download**; SHA là giá trị index công bố, chưa phải hash kiểm từ wheel bytes.

| Candidate filename | SHA-256 wheel từ index |
|---|---|
| `torch-2.7.1+cu126-cp313-cp313-manylinux_2_28_x86_64.whl` | `a05c0001fd1d0ceae9cda8c8c1b8a16ed5def858fe996c9237a28016559dad52` |
| `triton-3.3.1-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` | `b89d846b5a4198317fec27a5d3a609ea96b6d557ff44b56c23176546023c4240` |

Exact wheel URLs nằm trong proposal và receipts `torch-candidate-02.json`, `triton-candidate-03.json` dưới `artifacts/akt/gpu08-env-20261108-01/`. PEP658 METADATA được tải riêng và hash bytes khớp cả thuộc tính `data-dist-info-metadata` và `data-core-metadata` của index: Torch `f1c769baeb1e24665230008f9b4ba220dcb6786b9a351cd85332ffa3e87c7426`, Triton `34d1dcbf4948d86b691e0dc803a1aa9e9d884af8ea1281394371809b0a8e234d`.

Torch METADATA yêu cầu Python>=3.9.0; candidate ABI là CPython3.13 thường, không cp313t/free-threaded, không aarch64. Tag manylinux_2_28 yêu cầu kiểm host glibc/platform tags phù hợp; proposal đặt glibc>=2.28, chưa đo image thực tế.

Torch có 24 Requires-Dist entries: 7 dependency Python chung, 14 NVIDIA pins với Linux/x86_64 markers, Triton3.3.1 với cùng marker, và 2 extras optree/opt-einsum không chọn. Các pins NVIDIA là:

```text
nvidia-cuda-nvrtc-cu12==12.6.77
nvidia-cuda-runtime-cu12==12.6.77
nvidia-cuda-cupti-cu12==12.6.80
nvidia-cudnn-cu12==9.5.1.17
nvidia-cublas-cu12==12.6.4.1
nvidia-cufft-cu12==11.3.0.4
nvidia-curand-cu12==10.3.7.77
nvidia-cusolver-cu12==11.7.1.2
nvidia-cusparse-cu12==12.5.4.2
nvidia-cusparselt-cu12==0.6.3
nvidia-nccl-cu12==2.26.2
nvidia-nvtx-cu12==12.6.77
nvidia-nvjitlink-cu12==12.6.85
nvidia-cufile-cu12==1.11.1.6
```

Dependency chung: filelock, typing-extensions>=4.10.0, setuptools khi Python>=3.12, sympy>=1.13.3, networkx, jinja2, fsspec. Triton base yêu cầu setuptools>=40.8.0; extras build/tests/tutorials không chọn. Full strings/markers giữ nguyên trong proposal và raw METADATA. NVIDIA cuFile hiện diện như dependency không có nghĩa đã bật GPUDirect Storage hoặc kiểm Volume.

## T4, CUDA runtime và driver: giả định cần nghiệm thu

NVIDIA xác nhận T4 có compute capability7.5. Đây là cơ sở chọn hardware target `sm_75`; khả năng chạy exact wheel vẫn phải kiểm `torch.cuda.get_arch_list()` và workload có giới hạn trên máy thực. Không suy tương thích binary chỉ từ tên cu126. [NVIDIA GPU table](https://developer.nvidia.com/cuda/gpus).

CUDA12.6 Update3 liệt kê runtime12.6.77 và các library versions phù hợp pins trên, cùng Linux driver560.35.05. Proposal lấy **driver>=560.35.05** làm giả định bảo thủ cho lần nghiệm thu sau; chưa đo driver máy đích. Mức CUDA12.x minor-compatibility tối thiểu525.60.13 là thông tin khác, không phải bảo đảm mọi feature/PTX chạy được. [CUDA12.6U3 release notes](https://docs.nvidia.com/cuda/archive/12.6.3/cuda-toolkit-release-notes/index.html). NVIDIA nêu hạn chế feature set và PTX khi dựa vào driver cũ; không dùng minimum đó để bỏ phép kiểm runtime. [Minor compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html).

Modal cung cấp driver/Driver API trên GPU host; user-space runtime/library có thể đi cùng package. Snapshot tài liệu lúc đọc ghi driver610.57.04/Driver API13.3; đây là website claim, chưa phải đo máy T4 được cấp. Không cài driver vào image hay đồng nhất `nvidia-smi` CUDA maximum với `torch.version.cuda`. [Modal CUDA guide](https://modal.com/docs/guide/cuda).

## Phần chưa hoàn tất trước image hoặc job

1. Resolver thật trên Linux x86_64/CPython3.13 hoặc công cụ hiểu đầy đủ target markers phải chốt toàn bộ dependency closure. **`pip --platform` trên Windows không tự chuyển PEP508 `platform_system`/`sys_platform`; có thể bỏ NVIDIA dependencies.** Không xây custom resolver trong batch này.
2. Chốt Linux wheels + URLs + SHA cho 14 NVIDIA packages, 7 dependency chung, transitive dependencies, cùng numpy/pandas/duckdb/scikit-learn/psutil/pytest và toàn bộ dependency của chúng. Versions trong `requirements-akt.in` chỉ là yêu cầu nền cần đối chiếu, chưa có Linux wheel availability/compatibility proof tại đây. Torch/Triton metadata không đủ làm full lock. Không thêm optional extras chưa cần.
3. Pin Python patch/build, pip bootstrap, base OS/glibc và immutable image digest; ghi SBOM/install report và package file/origin inventory. Image đề xuất cần Linux slim/Python3.13; khả năng đáp ứng của Modal base image, SDK recipe và digest chưa được xác minh/chọn. Không dùng mutable image tag làm certificate.
4. Kiểm offline install từ wheelhouse có manifest; `pip check`, exact versions/origins, runtime schema2 gắn đúng Linux lock/source và negative guards. Metadata hashes không thay kiểm wheel bytes trong bước tải/cài tương lai.
5. Refresh source-bound Gate2 trên đúng source. Sau đó mới bounded synthetic main-worker CUDA lifecycle: loader/split/vocabulary, train/validation/selection, checkpoint/export/resume, VRAM/watchdog và fail-closed controls. Không coi các probe kitv12 là pass cho source mới.
6. Modal image/Volume durability, hard interruption/recovery, end-to-end throughput và budget forecast vẫn cần nghiệm thu riêng, trước bất kỳ pilot có dùng credits. Synthetic optimizer timing không là cost/target cho corpus thật.

## Lệnh chuẩn bị cho bước sau — chưa thực hiện

Đây là mẫu cho một checkout/image Linux mới, sau khi closure/wheelhouse/hashlock thực sự hoàn tất và bước provisioning được cho phép. Các đường dẫn `linux-cu126` sau **chưa tồn tại như lock được nghiệm thu**. Không truyền proposal JSON cho worker. Không chạy các lệnh này trong batch metadata hiện tại.

```bash
# Trong checkout/image Linux mới; không kế thừa system-site-packages.
test ! -e .venv || exit 1
python3.13 -m venv .venv
# Chỉ dùng sau khi đã có full lock, wheelhouse và manifest SHA được review.
test -s artifacts/akt/runtime/linux-cu126/requirements-linux-cu126.lock.txt || exit 1
.venv/bin/python -m pip install --no-index --find-links artifacts/akt/runtime/linux-cu126/wheelhouse \
  --require-hashes --only-binary=:all: --no-deps \
  -r artifacts/akt/runtime/linux-cu126/requirements-linux-cu126.lock.txt
.venv/bin/python -m pip check
# Phép kiểm này sẽ import runtime/CUDA; dành cho stage được cho phép sau.
.venv/bin/python scripts/akt/check_runtime.py --device cuda \
  --upstream artifacts/akt/dependencies/upstream \
  --lock-file artifacts/akt/runtime/linux-cu126/requirements-linux-cu126.lock.txt \
  --output artifacts/akt/preflight/runtime-linux-cu126.json
```

Không có lệnh `modal run/deploy`, image build hoặc GPU allocation ở đây. Hạn mức30USD/tháng, out-of-pocket0USD và các allocations đang có giữ nguyên; không có quyền chi tiêu mới.

## Receipts và kiểm local trong batch này

`artifacts/akt/gpu08-env-20261108-01/` giữ DNS failure lượt01, receipts02/03, hai raw index và hai raw METADATA. Tổng4 HTTP responses thành công **265.132bytes**, lớn nhất147.978bytes; cap1MiB/response,10MiB tổng cho metadata fetch. GET đầu trong môi trường restricted bị `getaddrinfo11001`; hai lượt metadata02/03 ở network context được phép sau đó thành công. Không retry vô hạn hoặc fallback tải wheel. Số byte này đo các request metadata có receipt; các trang tài liệu đọc bằng web tool chỉ dùng để đối chiếu, không có raw HTTP byte accounting.

`local-validation.json` ghi kiểm SHA index→metadata, candidate href/hash, Requires-Dist, đối chiếu input SHA và xác nhận proposal không load được bằng AKTConfig. Không chạy test/model/GPU/cloud suite trong batch nghiên cứu môi trường; không thay các số pass lịch sử. `inventory.json` ghi các files mới và SHA nguồn local; parent xử lý chỉ mục/archive/Git.
