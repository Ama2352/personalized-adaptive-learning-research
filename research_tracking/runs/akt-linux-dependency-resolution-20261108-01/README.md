# AKT Linux dependency resolution — 08/11/2026

Actual Colab CPU/Linux CPython3.13.18/pip26.2.2 đã phân giải44packages:29root pins,
14NVIDIA dependencies vàTriton3.3.1. Torch2.7.1+cu126/Triton wheel hashes khớp
official index metadata đã lưu. Đây là candidate closure/index hashes, không
wheel-bytes verification, installation, image digest hoặc CUDA/main-worker acceptance.

Lượt resolver10.095353s,peak OBSERVED attempt-tree7350021bytes; limits180s/256MiB
là cooperative polling/postexit checks, cóovershoot, không hard network/disk cap.
Source có thể fetch wheel bytes nếu metadata khôngusable; không claim no-wheelGET.
Base pip --python điều khiển isolated .venv --without-pip; target Torch/NumPy/pip
specNone trước/sau, names/probe unchanged được source ghi. Không full content-hash
inventory của toàn site/globalfilesystem, nên không byte-attestation ngoài phạm vi.

Offline independent validation đối chiếu14rawfiles/512166bytes, transfer/archive
digests,44selected names/versions/URLs/SHA/CP313ABI tags,46active Requires-Dist
constraints với actualLinux markers;432optional/platform entriesinactive. Không
resolve version mới, chạy pip, install, model/GPU/cloud/network trong archive.

remote_manifest.json là manifest raw14 gốc; copy_inventory maps original nested
paths tới aliases phẳng và giữ bytes exact. Python sources là text, không Python
binary. Không wheels/caches/ZIP/chunks/privatefiles/rawMCPbase64 transfer data.
resume_resolver.py có literal verified approved-source embedding như code đã chạy;
receiver source chỉ tham chiếu private-folder path, không có nội dung/auth củafolder.
Receipt JSON được normalize riêng; remote receipt digests là provenance references,
không signed remote attestation hoặc bản copy raw private bridge responses.

Trạng thái completed chỉ archive integrity. Chínhproposal/bundleGPU08trước vẫn
giữ nguyên; actual resolver-source39c68... vàresume4109... có snapshot riêng.
Futureinstall script đang được chuẩn bị riêng không thuộc bundle này. Next cần
wheel-byteSHA/installreport/pipcheck/origins, freshschema2CPU/CUDA đúng stage,
immutableimage và actualboundedCUDA mainworker/Volume/throughput acceptance.
ProofT4kitv12Torch2.14.1+cu130 không certify2.7.1+cu126 hoặc source mới.

record_evidence_run/verify_evidence_bundle đóng và kiểm outputs, sau đó chỉ đọc.
29copies có inventory trước/sauSHA; canonical report links giữ theo repository.
git_ignore_check.json dùng từng explicit argv path, không stdin;force_add_paths.txt
ghi chính xác ignored logs. Git chỉ đọc, safe.directory process-only; parent quản
tracking/Git, không add/commit/push hoặc đổi globalconfig. Không có permission chạy
install/GPU/data/model/Modal từ việc archive này thành công.
