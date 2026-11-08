# Generic GPU-host discovery — offline

08/11/2026. Chưa dispatch/hardwareselection, actualRPC, target, normalstartup, Torch/GPU/model/install/network. Không tạo fake freshGPU receipt. Source02/profile0944/CPU wrapper/bundles cũ giữ nguyên.

Frozen source `4c41381fe00069cf888addfa89865abcba98c711b2a1462294dbaf136b5cde03`; test `e53cf9a67c8452a43dbf1ecc25b8f20960f02f5977636352b5bf5472f82309e9`. Reuse exact discovery02SHA51c4.../profile0944... . Root review trước actual preparation/dispatch sau manualGPU choice.

ROOTabsent: snapshot ABSENT không tạo/read ROOT, source02 tự phân loại COLD_ROOT_ABSENT, inner targetchildNone và prepostABSENT. Chỉ source/profile/metadata staging ngoàiROOT tại GPU10_DISCOVERY/gpu-host-*. Rootpartial/mismatch STOP, không bootstrap/repair. ABI khácprofile thì source02 STOP, không fabricate cold. COLD_VENV_ABSENT/EMPTY giữ noauthority; chỉ ROOTabsent chắc chắn0targetchild (emptyvenv có thể cần stdlib probe).

Warm cần generic GPU_HOST attempt/approval/command,165source/lock exact prepost, source/profile/ABI/time, cả launcher+target cleanup/RC và currentGPU-host indication. COLAB_GPU/device-entry names không là T4/capability/CUDA proof. CUDA/NVIDIAhidden, controller/target-I-S-B. ForwardTPU presence sentinel, không address. HaiPG có cleanup scope riêng; không globalhardkill recovery proof.

Proposed CLI, chưa thực thi:

```text
.venv\Scripts\python.exe -I -S -B .../host_discovery.py --operation prepare
 --mode GPU_HOST_READONLY_DISCOVERY --attempt-id gpu-host-discovery01
 --approval-reference <ACTUAL_PARENT_GPU_HOST_REFERENCE_AFTER_MANUAL_SELECTION>

.venv\Scripts\python.exe -I -S -B .../host_discovery.py --operation receive
 --mode GPU_HOST_READONLY_DISCOVERY --attempt-id gpu-host-discovery01
 --receipt-id gpu-host-receipt01 --rpc-json <ACTUAL_RPC_PATH>
 --parent-review-reference <REVIEW_REFERENCE> [--result-file <EXACT_RAW_RESULT>]
```

Prepare chỉ AST/render/exactsource02argv parser, viết local request/contract độc quyền, không gửi. Request/reply≤48000byte. Receiver chỉ explicitRPC, không polling/callback; whole rawRPCSHA khi trongcap, exact stdoutlauncher/resultSHA. Oversizedfailure hash là capturedprefix, không wholeRPC. Không inline thì RETRIEVAL_REQUIRED, boundedresultfile phải khớpSHA/size, không rerun job. Không copyrawprivateRPC. Receipt-id mới không overwrite.

Acceptance là LOCAL_DERIVED_RECEIPT_FROM_VERIFIED_RPC, giữ rawRPC/result/launcherSHA+parentreviewref. Chỉ WARM khi predicates đúng; coldstatus COLD_DISCOVERY_NOT_GPU_READY_NO_INSTALL_AUTHORITY giữ actual_status ROOTabsent/venvabsent/empty; otherwiseSTOP. Relocation exactbyte vàoROOT là preparer riêng giữ provenance, không autoaudit/install. Coldbootstrap strictROOTabsent phải xem actual_status, không repairmissing/emptyvenv.

Separate15svalidation: trial01 9PASS0.3280892s; sau sửa honest oversizedRPCprefix label, finaltrial02 **9PASS**, posthash0.2286352s, cumulative **0.5567244s≤15**. Source/test/source02/profile trước/sau match; logs/snapshots giữ cả hai. Chỉ synthetic in-memoryGPU labels, stdlib snapshot/AST/CLI; không operation main/actualfreshT4receipts. CPUb003 là baseline, không fullsite/runtime/GPU/install proof.
