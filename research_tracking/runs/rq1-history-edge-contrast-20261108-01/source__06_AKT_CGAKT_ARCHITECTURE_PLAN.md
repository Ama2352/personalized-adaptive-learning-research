# Kiến trúc AKT và CG-AKT đề xuất

## Trạng thái đối chiếu implementation08/11

Các phần thiết kế phía dưới vẫn là **đề xuất cho thí nghiệm nghiên cứu**, không tự được phê duyệt bởi prototype. Đã có hai mốc engineering cụ thể:

| Thành phần | Bằng chứng hiện có | Phần chưa đạt |
|---|---|---|
| A0/A1/A2/A3 forward/backward | `4a256a4`, [43 targeted CPU tests](../../research_tracking/reports/akt_graph_confidence_gate_readiness_20261108.md); confidence explicit, gate sigmoid, native bypass khi off/no support/zero mass | Chưa fitted/calibrated confidence, CUDA hoặc kết quả nghiên cứu |
| Graph-aware lifecycle | `f8e9ab0`, [GRAPH04](../../research_tracking/reports/akt_graph_training_readiness_20261108.md); toy A3 một complete epoch/8targets, cập nhật backbone/message/readout/gate, selection4=3known+1OOV, full checkpoint reload delta0; negative partial không publish checkpoint | Chưa full corpus/context rollover100, graph resume, production fitted backend hoặc full software Gate hiện tại |

Recipe đã cài chỉ là engineering: message `Linear(mean observed correctness)`; gate `Linear4→1` rồi sigmoid với features `S/(1+S)`, mean confidence, population variance confidence trên **ALL declared query parents**, observed-parent fraction. Confidence0,25/0,75 trong fixture do caller khai báo, không được gọi là edge reliability đã học. Tuple score/calibration/reference/mastery chưa được suy ra từ các feature này. Các initializer, module recipe, graph/confidence/provenance, effective-window geometry và source hash đều nằm trong identity; không pickle arbitrary callable.

Whole actual suite GRAPH04 giữ **45PASS/1FAIL**; test inventory cũ thiếu hai helper graph được sửa và kiểm riêng bằng stored artifact/0fit. Không gọi là46suitePASS hoặc thay Gate24 cũ bằng targeted result. Bốn optimizer updates tổng gồm base/graph happy+partial, không bốn model variants đã fitted. Thời gian46,688882s là budget kiểm thử, không throughput dự báo GPU.

**Điểm chưa thể bỏ qua trước research fit:** S04 chốt reference item bank/weights, calibration target/partition, threshold và controller; S05 chốt model×environment×graph conditions/seed/evaluation allocation. Junyi và Grade10 vẫn là hai domain train riêng. Primary matched effective window ở prototype không tự phê duyệt primary methodology. Main confidence estimator, graph-realization split và learned-graph comparator vẫn chưa được thay bằng fixture structural score. Gate-off giữ same trained backbone; system fallback sang checkpoint A0 độc lập **chưa cài**.

Cập nhật engineering07/11: domain/session/reference và AKT online/checkpoint bridge đã được triển khai prototype theo18_SIMULATOR_KT_INTERFACE.md. Không tự adopt mastery/calibration/controller protocol hoặc graph architecture bên dưới; các phần đó vẫn cần review. Junyi checkpoint thiếu simulator identity bị từ chối.

Đây là design cần review trước implementation. Upstream AKT NonRasch giữ source commit đã pinned. Không sửa architecture trong phiên điều tra.

## Bốn điều kiện tối thiểu

Backbone trả latent h_t cho current exercise q với past QA strict causal. Bổ sung residual logit ngoài backbone. Với edge j→q, context s_j(t) lấy từ events trước t của concept j trong cùng causal history hoặc state cache causal đã khai báo. Timestamp/order ties theo source_row. Parent chưa có history dùng zero evidence và observed-mask, không đọc latent oracle trong input estimator.

m_q(t)=sum_j[c_jq * observed_j * f(s_j(t),e_j,e_q)] / max(1,sum_j[c_jq*observed_j]). Logit z=z_AKT+g(t,q)*wᵀm. f nhỏ là linear projection shared, không GNN nhiều lớp. Gate scalar sigmoid từ history support, average edge confidence, dispersion và observed fraction, không current y. Graph-empty trả exact residual0. Scale normalization giữ absolute confidence ảnh hưởng, cần doc normalization cụ thể và unit test tất cả c=0. Kiến trúc này giữ augmentation tối thiểu, không tuyên bố f là calibrated mastery.

A0 graph-free g=0 và bypass branch. A1 fixed graph c=1,g=1. A2 confidence-weighted g=1. A3 confidence-aware gated graph + explicit disable. Có two fallback notions, g=0 trong A3 chỉ tái hiện backbone A3 đã jointly trained, không bằng checkpoint A0 độc lập. System fallback dùng A0 checkpoint riêng và gate selection trên Dev. Demo phải phân biệt hai hành vi. Test disable parity so với same-backbone branch-off, thêm system selector test chọn đúng A0 manifest.

## Confidence và privileged information

Oracle c=I(edge true) chỉ simulator upper reference, không main deployment claim. Noise probability do generator biết cũng privileged nếu gắn theo true labels. Main c_hat học/ước lượng từ train-only simulated sequences hoặc Junyi train logs, không truy cập true-edge labels lúc deploy. Default đề xuất simple edge bootstrap stability của preregistered lagged association conditional target history, exercise frequency và learner intercept proxy, fit trong train folds. Cần kiểm identifiability, stability không tự là xác suất edge true. Gọi structural reliability score nếu chưa calibration. Simulator Dev known true/noisy edges có thể calibrate reliability trên graph realizations tách train/test, rồi report Brier/ECE/AUPRC edge correctness trên graph realizations mới. Không calibrate trên cùng corrupted edge labels đánh giá.

Structural score và learned gate là hai nguồn evidence khác nhau. Gate learned bằng train response loss, validation chọn fallback. Gate thấp không chứng minh edge causal false. Learned edge confidence end-to-end làm tăng identifiability và training burden, DEFER optional. Khi edge-confidence không identifiable, main c dùng transparent reliability with uncertainty, oracle separate ceiling và honest limitation, xin advisor duyệt operationalization.

## Junyi và Grade10

Junyi exercise IDs ≠ 28 Grade10 concept IDs và 84 item IDs. Không có crosswalk semantic được xác minh. Junyi-trained embedding/checkpoint không thể trực tiếp dùng Grade10 controller, matching numeric indices không có ý nghĩa. Train riêng theo environment_id/vocab hash. Optional cross-domain backbone transfer chỉ exploratory, reset embeddings/head và test, ngoài critical path.

Simulator encoder đề xuất exercise=item84, concept map28 dùng graph projection concept→items. AKT n_pid0 vẫn item embedding84, graph context concept aggregate past observations. GKT có thể concept28 rồi item difficulty feature, comparator input khác phải ghi và kiểm calibration cùng reference bank. Chốt contract trước train. Synthetic logs đủ về số lượng có thể generate nhưng diversity/coverage chưa chứng minh. Split learner IDs độc lập train/selection/calibration/final, seed families độc lập, reuse cùng logs across variants. Development includes trajectory coverage test, final closed loop giữ frozen model weights chỉ cập nhật causal history.

Mastery adapter queries fixed reference items per concept (ví dụ bank1050/1200/1350 hoặc chuẩn difficulty1250 nếu supported), aggregate calibrated correctness probability. Không coi p(correct current item) trực tiếp là P(K) BKT. Chọn τ/mapping trên simulator Dev với true state chỉ làm supervision/evaluation được ghi privileged calibration, estimator deployment input vẫn lịch sử. Primary selection dùng common reference probability criterion, historical native thresholds giữ reproduction riêng. Item selection chooses difficulty closest calibrated expected-success target đã freeze, không ép arbitrary Elo inverse cho AKT không được fit. Action candidates đều thuộc trained vocabulary, OOV null báo coverage.

## Training fairness và checkpoints

Review sau interface07/11: session giữ full history để replay/snapshot nhưng A0 chỉ dùng window theo global anchors. CG branch dùng full-history concept cache trong khi A0 bị cắt window sẽ trộn graph effect với thêm lịch sử. Default **đề xuất, chưaadopt**: primary graph context dùng cùng effective causal window; nếu dùng cache dài hơn thì thêm graph-free cache/information-matched control và báo thành thiết kế khác. Chốt scope này cùng S04/S05 trước implementation/training graph variants, không xem “past-only” là đã đủ fairness.

A0/A1/A2/A3 cùng random backbone initialization theo seed, same training logs, optimizer/backbone hyperparams/budget. Branch parameters extra report count. Train riêng mỗi variant là primary ablation. Warm-start từ A0 được phép thiết kế riêng với cùng pretraining exposure và fine-tune budget cho cả A0 control, không so pretrained CG với scratch A0. Noise inference-only sensitivity có thể reuse frozen checkpoints nhưng không gọi robustness-under-noisy-training. Candidate graph học thay train data thì graph hash và confidence construction nằm trong fold train.

Chi phí tối thiểu main4 fits mỗi simulator seed, 3 seed core là12 fits, thêm oracle/shuffled/gate-off inference ablation không luôn cần retrain. Fixed/no-confidence/gate variants được retrain cho causal architecture ablation. Gate-off same-backbone cần inference-only. Không reuse inner checkpoint làm outer refit nếu vocab/loss exposure khác. Reuse deterministic encoded windows cùng mapping và semantic hash, không share train-fitted calibrator across outer folds.

## Acceptance

G0/no-edge exact same-backbone outputs CPU deterministic, CUDA tolerance documented. Current/future y perturbation không đổi p_t. Cross-learner isolation. True latent inaccessible từ model batch. Learned graph fit train-only. Source/count/hash contract rõ, every target scored once, full uncertainty/gate export. Negative model metrics không fail implementation gate.
