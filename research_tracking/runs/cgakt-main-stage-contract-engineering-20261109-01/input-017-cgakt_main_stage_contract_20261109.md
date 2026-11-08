# GRAPH18 — hợp đồng main selected-only,09/11/2026

ROOT đã chạy **14unittest methods PASS/0failure/error/skip** bằng Python của
`.venv` trên Windows. Đây là kiểm hợp đồng metadata/phase, không actual main
producer, selected-fit epoch, admission file, selector freeze hoặc quyền chạy.
Mọi head của contract giữ trạng thái `NO_EXECUTION_AUTHORITY`.

## Interface và thứ tự đã chốt

Module `src/knowledge_tracing/akt/research_main_stage.py` SHA
`77b7dbfd75f715f3a4179286cd742780581151dc39c39748213c9c55c25b13c1`;
test SHA `68f1e02921729c3de9595528302a1bd07513fbaf926871a4308048c72cefa851`.
Reuse trực tiếp `research_admission.MainSelectionContext` và
`SelectedCandidateClaim`; không tạo class admission tương đương hoặc đổi pilot A0.

`MainSelectedStageSpec` bind candidate/context/config/source/runtime và graph
condition/TRAIN80 nếu có. Mapping giữ đủ9conditions: A0, A1/A2/A3×expert/learned,
SAKT và GKT; không xem graph-off cùng weights là independent A0. Hai environment
được giữ riêng. Các IDs protocol21/lifecycle22/accounting23/recipe26/allocation
chỉ là metadata bindings; disk driver tương lai vẫn phải kiểm actual bytes.

State bất biến đi theo `READY → selected_fit80 → raw_best_selection10 →
SELECTED_ONLY_COMPLETE`. Trong fit80, `phase_inputs()` chỉ trả train refs;
`epoch_validation_inputs()` trả **raw selection10 read-only mỗi epoch**, không
optimization entitlement. Vì vậy EarlyStopping không phải chờ train hết epoch.
`raw_best_selection10` là export best epoch cuối cùng, tách khỏi validation mỗi
epoch. Terminal reuse typed claim và revalidate candidate/context/config/source/
runtime/graph binding, selected epoch complete và full-support/null counts.

Trước lần chạy đầu, ROOT source review phát hiện API thiếu per-epoch validation.
Hai source trước sửa cdad9d97/77f0d990 được snapshot nguyên bytes và inventory
SHA trước/copy/sau. Đây là static correction **trước execution**, không fake RED
test hoặc gán14PASS cho revision cũ. Số test methods giữ14, thêm assertions trong
vòng9candidates×2environments và kiểm sai thứ tự.

## Không tạo external authority từ claim

`artifact_bytes_verified=False`, `external_freeze_authority=False` luôn được giữ.
Chưa có actual external-freeze file verifier; vì vậy
`request_refit_after_external_freeze(...)` luôn báo
`EXTERNAL_FREEZE_FILE_VERIFIER_UNAVAILABLE`. SHA/bool/dict/typed claim hoặc object
tự nhận verified không mở refit, không được gọi như callback. Calibration bị bác
trong mọi selected-only state. Không consume calibration labels hoặc thay winner.

Seal phát hiện mutation hợp tác của spec/state/terminal. Nó không chống caller
fork/reset head, không chứng minh model vừa train, artifact tồn tại hoặc budgets
đã được giữ. Trách nhiệm đó thuộc actual file/execution driver và receipt riêng.

## Actual kiểm tra và giới hạn

14methods bao phủ mapping9×2, phase/epoch-validation refs, ordering/terminal,
cross-context/config/source/runtime/graph mismatch, pilot/refit/calibrated/
incomplete claims, mutation, fake freeze/callback và semantic file-I/O denial.
Modules thật được import cold, admission/stage class identities dùng cached
normal import; không mock namespace hoặc reload để qua guard.

|Nguồn thời gian|Actual|
|---|---:|
|unittest stderr|14tests,0.058s,OK|
|worker stored elapsed|0.567881099996157s|
|owned helper stored elapsed|0.8717484474182129s|
|outer final stored elapsed|1.1478381999768317s|
|ROOT thông báo printed elapsed|1.1524253999814391s|
|ROOT terminal wall|1.9423193s|

Whole cap30s, owned remaining≤29s gồm cleanup2s và reserve final1s; worker active
budget27s. Clocks có điểm capture khác nhau, không thay nhau hoặc cộng thành fit
time. Actual owned worker vào Job trước domain import, cleanup active0/handles
closed, environment restored;14source và11runtime fingerprints trước/sau khớp.
Không có scientific modules hoặc denied attempts trong worker. Không Torch,
NumPy, corpus/model/optimizer, Windows metadata subprocess hay network trong
worker. Parent owned helper dùng psutil đã pin. Không có RSS-monitor/hard-quota
proof mới trong batch stdlib này.

Final receipt SHA `6720977ab7d863a4aebef36b5c78e4066c8ef406c99862496503724f65694ed4`;
worker result SHA `943a5c1623c0c79d3298fffe855dc4509d1e0589479022bb61dc682cf3072ab5`.
Bundle dự kiến `cgakt-main-stage-contract-engineering-20261109-01` giữ raw
logs/canary/owner receipts, source/test/packet/controller và before snapshots;
copy SHA trước/sau, không copy dependencies/runtime/corpus. ROOT đóng và cập nhật
backlog sau review; tài liệu này không tự đặt trạng thái TASKS.

Phần tiếp theo vẫn là actual selected-only producer/real authority guard, native
epoch/checkpoint/best raw export và actual all-nine file admission; refit chỉ sau
verified external freeze.14PASS không thay những outputs đó, không nghiệm thu
main matrix, GPU/paid readiness hoặc hoàn tất RQ.
