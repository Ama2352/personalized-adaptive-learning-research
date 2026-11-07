# Hợp đồng nối KT với simulator — engineering CPU

Ngày07/11/2026. Tiếp REC01–REC06; giữ source/results Paper1/2, không train Junyi/GPU/Holdout. Đây là interface prototype cho thiết kế06, chưa thay controller hay chốt scientific protocol S04/S05.

## Các quyết định đủ bằng chứng để cài đặt

Paper2 có28concepts và84items, mỗi concept có item1050/1200/1350. AKT hiện mã hóa exercise và cửa sổ global target anchors, không nhận difficulty liên tục. Junyi vocabulary khác; checkpoint không có simulator-domain identity phải bị từ chối, không ánh xạ numeric indices giữa datasets.

Một session chỉ có một learner, một checkpoint/domain và lịch sử response quan sát được. Truy vấn candidate/reference item nhận item/time/source-row, không nhận current outcome hoặc latent theta. `observe` nhận outcome sau prediction, kiểm ticket cùng session/generation/history. Truy vấn không commit; nhiều reference queries tại cùng bước là counterfactual queries riêng, không phải fictitious practice events. Reset vô hiệu ticket cũ. Snapshot chỉ có history/provenance, không chứa simulator oracle.

Online prediction phải tái hiện đúng offline AKT global-block/context/OOV barrier semantics. Không cắt recent history rồi re-anchor block tại0. Không dùng unseen exercise như fitted prediction. History cap là budget explicit của session; không silent truncation. Weights frozen khi closed loop, update chỉ history.

Reference bank và weights phải khai báo rõ. Prototype trả `mean_reference_correctness`, coverage và missing items, không trả P(K) hoặc tự chọn mastery threshold. Thiếu reference item thì score None, không tự renormalize sang bank khác. Dùng84existing items là một lựa chọn draft, không sinh difficulty1250 giả vì chưa có exercise được train cho nó. Calibrator/threshold/action-controller mapping vẫn S04, cần protocol trước experiment kết luận.

## Gói và nghiệm thu

| ID | Mục tiêu | Nghiệm thu |
|---|---|---|
|SIM01|Item/domain/session/ticket/reference contract chung|Reject cross-domain, stale/foreign ticket, duplicate chronology, labels/oracle fields; queries pure; reset/snapshot isolation|
|SIM02|AKT next-item inference + checkpoint binding|Offline parity ở cold start, block boundary, OOV và partial block; checkpoint SHA/domain/recipe/vocab checked; model weights/RNG/mode không đổi|
|SIM03|Integration proof trên Paper2 item bank và native AKT|Bounded synthetic-trained fixture;84item/28concept mapping; probes không commit; no real-data training hoặc learning-benefit claim|
|SIM04|Persist source/log/hash/task state|Vietnamese report, immutable bundle, source-bound Gate2 refresh sau stable code, commit từng gói verified|

Không nối protocol vào run full experiment hoặc gọi native Paper2 `is_mastered` bằng score mới. Không tái sử dụng Junyi checkpoint cho Grade10. Không chọn reference weights/ngưỡng dựa trên Holdout hoặc final simulator seeds. Các tests chỉ chứng minh semantics phần mềm; diversity/coverage của training trajectories và calibration vẫn cần thí nghiệm riêng đã duyệt.
