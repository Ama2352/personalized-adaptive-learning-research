# Thiết kế source-level: controlled available-history replay — CHƯA CHẠY

## Câu hỏi phân biệt với descriptive bins

Ở **cùng một target query/y và cùng cached thế giới**, estimator-edge-set contrast full−empty thay đổi thế nào khi thuật toán chỉ được cung cấp last10, last50 hoặc toàn bộ prior observed records? Khác binning theo vị trí chuỗi, đây là can thiệp có kiểm soát vào **available input history của thuật toán** tại target cố định. Không thay actual learner history/latent dynamics, không chứng minh thay practice làm outcome/mastery tốt hơn, không causal instructional benefit hoặc hiệu ứng ability.

Tìm trong scripts/research, reports và gam_kt package chưa thấy runner làm đúng native GAM full/empty available-history intervention này. Interface batching/window tests SAKT/GKT/AKT kiểm geometry khác, không thay thế native GAM replay. Đây là objective/run mới; task hiện tại chỉ đọc source và đề xuất, **chưa viết/chạy replay**.

## Nguồn đủ để implement không sửa world

- C13 fixed stream đã có actual `(cid,qid,difficulty,timestamp)` và y common; exact source legacy parity và initial-state equality full/empty. Reuse cùng3seed families×3profiles, không sinh query/labels/uniforms hay environment.
- `historical_runner.py` SHA `402dca905694d850f126e41f3b5dcc91b327e986ae2cfbb240dda739eed8dd45`, lines69–93: predict trước update; sau update tăng selection_counts/question_counts, append recent_concepts, set current_chapter theo **logged** item. Không select vào history replay.
- Notebook SHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`, cell13 `MemoryState`/`GAMKTPolicy`: theta1200; zero float32 memory; pi_task1/pi_time.05; attempts0; last_timestampNone; deque8; mastery flags/forgotten0; same explicit r_pos/r_neg/q/theta_lr/memory_lr/weights. Native predict/_decayed_pi/mastery_score chỉ đọc state; update thay theta/memory/pi/time/attempts/recent/mastery/forgotten. Không random draws trong các functions này.
- Cell11 `_init_selector` zero counters/None chapter/empty recent; choose_question stable distance/seen/qid sort; select deterministic mastery/chapter/visits/cid key nhưng **mutate counters**. Target preview phải trên deepcopy, tuyệt đối không chọn từng past event qua selector vì sẽ thay source history.
- `paper2_reference.py` SHA `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1`, lines30–96: load selected definitions/input CSV metadata, estimator_edges=[] chỉ empty estimator G, controller G vẫn full. Có thể dùng loader sẵn có; không notebook top-level execution/environment.interact/persona_base_abilities/RNG calls. Loader tạo definitions của environment nhưng không instantiate/call world.

## Khuyến nghị finite intervention contract

Targets là **Hpast=10,50,100** (`event_id`10/50/100), không target index1-based. Mỗi target có3seed×3profiles=9queries. Requested history labels k10/k50/full; actual length `L=min(k,Hpast)` hoặc Hpast cho full. Với H10 cả ba aliases là cùng10records; H50 k50/full cùng50records. Dedupe computation và ghi alias mapping, không nhân bản như observations mới.

Mỗi unique `(seed,profile,targetH,L,estimatorGraph)`:

1. Tạo **fresh native policy** cùng constructor `GAMKTPolicy(True)`/initial fingerprint; full và empty cùng parameters/features/node order, chỉ estimator edges khác. Không clone state đã học full history rồi cắt list, không giữ hidden state/counters từ records bị loại.
2. Feed đúng cached history indices `[H−L,H)` với timestamp tuyệt đối gốc, không nén/đổi gaps. Với từng past record: native predict ở state của **condition đó**, rồi native update dùng cached y và chính p_pred vừa tính; sau đó source-equivalent fixed-stream bookkeeping lines90–93. **Không reuse historical full-history p_pred** cho truncated updates vì residual/gain path sẽ sai.
3. Current target query predict trước khi được cung cấp target y. y chỉ dùng đánh LL/Brier sau prediction; future records không được đọc vào state. Optional target full preview trên deepcopy với timestampNone như source; không serve action hoặc interact world.
4. Freeze/verify state/input/source hashes; allconditions giữ cùng targets/y/graph-controller/world provenance. No optimizer, NN weights, model selection, calibrator, seeds hay response simulation.

Khuyến nghị coherent available-history contract cho **toàn native policy + controller bookkeeping**: chỉ các exposed past records cập nhật counters/chapter/recent. Vì preview cũng dùng counters, preview sensitivity là package-level available-history response, **không riêng estimator memory effect**. Predictive P/LL/Brier không trực tiếp dùng selector counters. Giữ controller counters full trong truncated condition sẽ là một counterfactual khác, không được âm thầm trộn vào design này.

Fresh reset giữ native initial uncertainty và `last_timestamp=None` cho concept chưa thấy trong retained window; không tự “age” state theo excluded events hoặc thêm synthetic gaps. Do đó đây là **reconstruct-from-limited-records algorithm**, không hậu nghiệm xóa memory ở một student có cùng learned state. Own/parent evidence coverage có thể khác cùng với retained records; graph effects gồm parent update propagation, không direct-logit-only.

## Acceptance và số call trước thực thi

- **Primary negative control:** mọi full-history endpoint phải exact-match stored P/S/M/R/fullpreview của cùng full/empty arm, tổng54arm endpoint snapshots =3H×9trajectories×2variants. Failure bất kỳ STOP, không tolerance/drop/tune. Nếu bỏ intermediate pure probes ở history mà parity không exact thì phải source-review, không bịa same-source claim.
- K≥H aliases exact cùng output, không rerun/cộng N; fresh learner/condition isolation và input immutability; target-label flip không đổi current prediction/preview, chỉ loss; future-label/input mutation không được truy cập. Giữ clocks absolute và bookkeep exact.
- Unique history lengths per targetH: H10→10; H50→10,50; H100→10,50,100. **54unique target pairs/108policy instances**. Total native state updates =`2×9×[10+(10+50)+(10+50+100)]=4.140`; history predicts4.140 +target predicts108. Nếu thu target previews thì108native select trên deepcopy; source scoring bên trong có bounded28nodes/84items. Đây là model-state replay calls, **không gọi “0model execution”**; chỉ0teacher/newworld/RNG/NNoptimizer.
- Không có empirical throughput cho recipe mới. Các số call là allocation bounds, không runtime forecast. Không dùng cached arithmetic cap10s cho native replay. Parent cần pin source/inventory/driver/cap/free-RAM/time ledger trước chạy; có thể đề xuất một allocation≤60s cho ONE attempt sau source review, nhưng hiện chưa authorize budget/run hay tự mở rộng nếu timeout.
- Legacy full endpoint parity là positive control sử dụng cùng targets, không “test set” mới. New independent N=0;9trajectory blocks nằm trong3seed families; targets trong trajectory/các windows phụ thuộc nhau.

## Metrics nếu được duyệt riêng

Predeclare LL/Brier như existing clip1e−15/rawP, và full-preview differences. Tại **cùng targetH/query/y**: `E(H,L)=metric(full_edges,H,L)−metric(empty_edges,H,L)`; available-history interaction `E(H,L)−E(H,H)`. Mọi H/L/profile/seed và aliases/negative outcomes được giữ; không chọn window theo signs, không p/CI/benefit/retention claim. Full/empty cùng condition và full-window comparator phân biệt algorithmic availability rõ hơn vị trí-bin observational contrast, nhưng không là causal mediation, quality từngedge hay generalization final seeds.

Chưa chọn/chạy metric quantities, chưa sửa simulator/source/history/protocol, không xóa gap final learned graph/calibration/train-support/noise hoặc yêu cầu RQ2 khác. Root review design+scope trước mọi implementation/run mới.
