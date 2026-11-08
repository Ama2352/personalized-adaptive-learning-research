# GRAPH16 — evidence động cho query online,09/11/2026

Đã kiểm **35cases PASS/0failure/error/skip** trên Windows CPU: dựng graph evidence
từ lịch sử đã quan sát, geometry/OOV và identity của counterfactual query. Đây là
**phần evidence/geometry của GRAPH16**, chưa dynamic graph-model inference parity,
backend fitted, GRAPH17 hoặc nghiệm thu toàn RQ3.

## Interface và ranh giới thông tin

Module mới `src/knowledge_tracing/akt/research_graph_online.py` SHA
`c44ad90a699e76ce3bcf2e0cc7264a7f9d87f6639ee59f8033d51a87ef1b2c88`;
test `tests/akt/test_research_graph_online.py` SHA
`d9dc5e62458c1d357722d1502cc5f14775501daa49e4de9a887de4867844a8f9`.
`prepare_research_graph_online` nhận typed bank/ResearchAKTEncoding/condition,
tuple Observation quá khứ của một learner, ItemQuery hiện tại, namespace và caps
explicit. Không có tham số đáp án hiện tại, future trajectory, peer state, teacher,
model hoặc calibration. Correctness của **past observations** là input hợp lệ.

Helper dùng lại `audit_graph_context`, `iter_window_slices` và `slice_causal_inputs`,
context100/targetblock100. Mỗi query có seal chứa item/time/source-row, learner,
bank/domain, encoding/vocabulary/condition, full-history SHA và geometry. Các item
counterfactual dùng cùng event time/row hợp lệ qua các lời gọi độc lập, nhưng không
có cùng identity/windowID. Không sửa unique-window guard của index offline.

Namespace explicit `grade10_simulator_item_id`; label Junyi bị bác. Domain/plan và
origin-shard encoding phải khớp graph TRAIN80 binding. Điều này chống trộn nhầm
namespace/encoding trong hợp đồng hợp tác; không chứng thực caller đã cung cấp
đúng learner history hoặc model từng fitted. Không đổi chỉ số Junyi thành Grade10.

## Kiểm source độc lập và các kiểm soát đã chạy

Chronology kiểm cả history+query: item trong bank, source_row duy nhất, cặp
`(timestamp,source_row)` tăng nghiêm ngặt. Vì vậy cùng timestamp nhưng row lớn hơn
hợp lệ; query trùng row lịch sử bị bác. Source gọi kernel trước dựng window; kernel
chỉ đọc history, không có đáp án query. Scope effective-window có thể không đổi
khi sửa quá khứ ngoài cửa sổ, trong khi full-history SHA vẫn đổi để truy vết.

35cases gồm tám đối chiếu offline-prefix/evidence tại global ranks
0/99/100/102/103/199/200/204 (OOV tại102); counterfactual cùng event khác item;
first-query; current/future-answer invariance; full-vs-effective past; learner
binding;13negative domain/lineage/chronology/caps; cùng timestamp; input ownership;
3tamper negatives và4invalid-limit cases. Fixtures là typed handmade streams,
không actual corpus. Đối chiếu geometry là prefix của cửa sổ offline tại query,
không đòi dynamic window chứa các future target slots.

OOV target trả `window=None`, `evidence=None`, audit `target_fitted=False`; không
graph rescue hoặc gán probability. `history_available` dùng native global block
anchor; `history_used=0`, reset=True. Với supported query, available/used/reset và
prior reset lấy từ native slicing, không suy đoán `min(rank,context)`. Các arrays
result là owned read-only copies; seal phát hiện cả forced payload/source drift.
Không giữ full bank/encoding/condition/history/corpus objects trong output.

Learner binding/invariance tests không chứng minh nguồn của từng Observation:
Observation không có learner field, nên caller/OnlineSession sau này vẫn phải
chịu trách nhiệm history của đúng session. Read-only flags và SHA không là sandbox
chống caller sửa private state một cách có chủ đích.

## Actual receipt và tài nguyên

ROOT chạy một lần qua helper Windows owned Job đã kiểm, actual worker vào Job
trước GO rồi mới import NumPy/pytest. Cold import thật của module ghi NumPy=True,
Torch=False. Không model/optimizer/forward/backward/solver/teacher/corpus/backend;
zero Torch calls được bảo vệ bằng fresh-import/module checks, không tạo call-count
thực nghiệm neural giả. Metadata Windows dùng một lệnh thật `cmd /c "ver"` trong
phase giới hạn, sau đó subprocess/network bị chặn. Không giả OS hoặc thay hook
platform để làm xanh fixture.

| Đồng hồ/nguồn | Actual |
|---|---:|
|JUnit test suite|5.357s,35PASS/0FES|
|Worker stored elapsed|7.008747400017455s|
|Outer `final.json` stored elapsed|7.603182699996978s|
|ROOT thông báo outer printed elapsed sau ghi final|7.637670600030106s|
|ROOT terminal wall|8.3114283s|
|Budget outer/owned/worker|90/87/80s,cleanup reserve3s|
|Observed worker peakRSS|57442304B|
|Observed minimum free RAM|4792061952B|
|Resource samples|60|

Các clocks có điểm capture khác nhau; không đồng nhất hoặc cộng làm research
duration. Guards RSS1GiB/free2GiB là observations/cooperative monitoring, không
hard OS quota. Actual Job active sau cleanup=0, Popen handle closed, environment
restored;25source và9runtime fingerprints trước/sau khớp. Không copy runtime/deps.

Final receipt `graph-online-pure01-owned/final.json` SHA
`393d8b341afbdfe55585bca106d8eb95f898735af6955f93c49523d539efdcce`;
child result SHA
`89b17d1a27eb1c633bde28baa86672f081be1f0e84b2ef37eb1837b196efea3a`.
Raw logs/JUnit/cold canary/owner receipts được giữ trong bundle dự kiến
`cgakt-online-query-context-engineering-20261109-01`, copy với SHA trước/sau;
không giữ test temporary directory `gop01` hoặc actual corpus.

## Phần chưa được chứng minh

Chưa gọi dynamic model, kiểm graph-off SAMEbackbone probabilities, weight/RNG
invariance của backend, fitted checkpoint/temperature loader hoặc actual closed
loop. Không thể thay engineering role thành fitted bằng một SHA hoặc bằng35PASS.
Chi phí query84items/step, main-training throughput/CUDA và kết quả nghiên cứu cần
receipt riêng. Kế hoạch nối tiếp vẫn là
[plan27](../../docs/thesis_recovery/27_MAIN_CANDIDATE_LIFECYCLE_PLAN.md), giữ recipe26
và boundary của offline index; kiểm này không thay protocol hoặc required models.
