# GPU08 — nghiên cứu/đề xuất runtime Linux CUDA, chưa provisioning

Owned docs/akt-linux-cuda-environment.md và experiments/akt/configs/linux-cuda-runtime-proposal.json; không sửa core/tests/index/state/Git. Proposal_only, executionfalse, lock_completefalse, không runnableAKTConfig.

Nguồn chính thức: PyTorch previous versions + official torch/triton cu126 indexes và PEP658 metadata; NVIDIA T4 compute capability/CUDA12.6U3/minor compatibility; Modal CUDA guide. Candidate Torch2.7.1+cu126 CP313 regular manylinux2_28x86_64 giữ baseTorch2.7.1 localCPU; chưa chứng nhận runtimebinary/kernel/parity.

fetch-01.json giữ DNS getaddrinfo11001 khi GET index trong restricted network. Hai lượt02/03 sau đó qua network read được phép chỉ tải index/PEP658:4responses,total265132B, max147978B, cap1MiB/response và10MiB/tổng. Không GETwheel; SHA wheel là index-provided, metadata bytes SHA đã kiểm đúnghaiPEP658attrs. Không resolve/install hoặc fallbackwheeldownload. Raw index/METADATA giữ nguyên.

Offline validation command: .venv\Scripts\python.exe artifacts/akt/gpu08-env-20261108-01/validate_local.py ; wrappertimeout60s. PASS consistency trong0.36s,returncode0:2candidatehref/wheelSHA,2PEP658hash,4responsehash,8localinputhash,Requires-Dist24Torch/14Triton,14NVIDIApin; proposal bịAKTConfig reject unexpectedschema_version. Không importTorch/Modal, không test/model/GPU/cloudrun. Đây khôngLinuxruntimepasshayfullhashlock.

FullLinuxmarkerresolution/NVIDIA+generic+projecttransitivewheelhashes/Pythonbootstrap/imageDigest/installreport/runtimeSchema2/sourceGate/mainworkerCUDA/VolumeDurability/throughputcònUNRESOLVED. Windows pip--platform không tựđổiPEP508platform_system/sys_platform; khôngcustomresolver. V12ColabTorch2.14.1+cu130 inheritedruntime khôngcertifynewTorch2.7.1+cu126isolatedvenv/currentworker.

Không thay financialallocation, khôngauth/credits/credentialchange, khôngModalSDKbackend/imagebuild/Volume. Docs giữmẫucommandstươnglai chưaexecute. inventory.json liệt kêhashoutput vàinputđểparentarchive; không bao gồmhashcủachínhinventory. Tất cả dướiartifacts/akt bịGitignore, parent quyếtđịnh archive/forceadd; khôngaddpytesttmp hoặcwheel/checkpoint.
