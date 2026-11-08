# GKT03: đề xuất một train-batch engineering — chờ parent duyệt

Ngày 08/11/2026. Chỉ đọc nguồn, chưa viết module/test và chưa chạy model, optimizer, dữ liệu hay mạng. Mục tiêu là bước kỹ thuật tiếp theo của GKT02, không S05/final baseline, author parity, corpus training, fitted adapter hoặc RQ3 completion.

## Phần nhỏ có thể triển khai trước

Chỉ thêm `src/knowledge_tracing/gkt/training.py` và `tests/gkt/test_training.py`; không sửa recurrent/core/config/shared/AKT, exports hoặc CLI. Dùng nguyên `GKTStaticRecurrentCandidate.sequence` (recurrent.py:194–219): score_t được lấy trước observe(i_t,r_t), state do caller giữ, adjacency/recipe cố định. Giữ ID `gkt_static_recurrent_convention_v1` cùng toàn bộ explicit constructor hiện có. Không chọn node=exercise/concept thay người nghiên cứu; toy domain và ordered node IDs phải được caller khai báo, không chuyển weights Junyi→Grade10.

API đề xuất (tên có thể parent chốt, mọi đối số cấu hình không có default):

```python
@dataclass(frozen=True)
class GKTTrainBatch:
    query_ids: Tensor          # CPU long [B,T]
    responses: Tensor          # CPU long [B,T], 0/1 tại event_valid_mask
    event_valid_mask: Tensor   # CPU bool [B,T], quyết định observe
    loss_mask: Tensor          # CPU bool [B,T], subset của event_valid_mask
    initial_state: GKTRecurrentState  # bắt buộc caller cấp, không implicit cache
    learner_ids: tuple[str, ...]
    source_rows: Tensor        # CPU long [B,T], identity cho events hợp lệ
    global_ranks: Tensor       # CPU long [B,T], thứ tự đã cung cấp, không tự sort
    binding: GKTBinding
    graph_sha256: str
    recipe_sha256: str
    initial_state_model_sha256: str
    role: str                  # đúng synthetic_engineering_train_only
    synthetic_only: bool       # đúng True; lời khai caller, không attestation

def train_gkt_batch(model, optimizer, batch, *, settings, budget): ...
```

`settings` bắt buộc objective=`mean_bce_on_explicit_loss_mask`, recipe ID/geometry/dtype, optimizer=`adam` và lr/betas/eps/weight_decay/max_grad_norm do caller cấp; đây là optimizer được helper hỗ trợ kỹ thuật, không lựa chọn scientific default. Caller tạo model và Adam; helper không khởi tạo model hay seed lại RNG. Kiểm đúng optimizer class, một param-group gồm toàn bộ registered trainable parameters đúng một lần, không params ngoại lai/thiếu/duplicate; đối chiếu optimizer settings thực tế với khai báo. Không lazy factory, không batch shuffle, epoch loop, best selection, refit hoặc dataset loader.

`budget` khai báo max_steps/max_targets/deadline; giới hạn engineering đề xuất ≤2 learners, ≤4 nodes, ≤12 events/learner, mỗi width≤8, ≤24 selected targets/call, một optimizer.step/call, cumulative toàn suite≤8 updates/≤60s. Các trần không là train authorization cho dữ liệu thật. Reject trước model.forward nếu budget đã hết, role khác train, domain/node order/vocab/graph/recipe/source drift, invalid IDs/labels/masks, empty selected mask, selected rows trùng hoặc chronology/ranks không tăng trong learner. Padding có thể chứa sentinel nhưng không được loss/observe; event hợp lệ nằm ngoài loss vẫn có thể là past history và ảnh hưởng future targets. Cold-target inclusion hoàn toàn qua explicit loss_mask; không tự adopt first-target policy/OOV fallback. Active unknown node reject, không graph rescue.

Một bước: snapshot binding/source/model/optimizer/state/input identity; `optimizer.zero_grad`; `model.sequence` một lần; chọn logits và responses bằng loss_mask; BCEWithLogits reduction=sum rồi chia đúng n_selected; backward; finite-gradient + explicit norm clipping; kiểm budget trước step; step một lần; kiểm finite params/optimizer state, source/input/graph/state bất biến và elapsed sau step. CPU device context bao forward/backward/Adam lazy state; kiểm CPU toàn parameters/buffers/state/batch/optimizer state, dtype explicit FP32 hoặc FP64 khớp model. Không `.to()` âm thầm sửa input. Test đặt default-device meta để bảo vệ lazy allocations; không CUDA/model allocation. Nếu vượt deadline sau step phải ghi bounded_after_update và đã tiêu thụ một update, không giả complete/rollback hay bỏ counter.

Kết quả là `GKTTrainBatchResult`: status/stop_reason, loss_sum/mean/n_selected, selected source-row keys, observed-event counts, optimizer_steps=0 hoặc1, grad_norm, source/config/batch/graph/recipe/weights-before/weights-after/optimizer identities, role=`synthetic_trained_engineering_only` chỉ khi step thực xảy ra. Đánh dấu `complete_train_step`, KHÔNG `complete_epoch`, fitted research model hay metric efficacy. Trả detached clone final_state nếu cần diagnostic, có `state_computed_with_model_sha256=weights_before`; không mutate caller state/arrays/model mode (khôi phục mode trong finally). Không trả state còn autograd graph để caller vô tình backward xuyên batch.

**Điểm cần chốt rõ:** final_state được tính trước optimizer.step nên không phải state mới dưới weights_after. GKTRecurrentState hiện chỉ bind domain/graph/recipe, chưa bind parameter version. Wrapper phải kiểm `initial_state_model_sha256 == digest(model)`; state có requires_grad phải reject ở API train-batch này. Muốn bước tiếp dưới weights mới phải caller recompute prefix hoặc bắt đầu zero state và cấp đúng binding; không âm thầm carry stale hidden state, detach TBPTT, hay hứa gradients xuyên chunk. Identity/hash chỉ kiểm cooperative consistency, không chứng minh caller không đưa future history vào state. Test chronology của recurrent đã có không thay thế nguồn gốc state.

## Reuse đúng và phần không nên nối cơ học

- Reuse trực tiếp recurrent sequence/predict/observe, GKTBinding và adjacency digest; giữ nguyên predict-before-update, mask và node geometry đã được GKT02 kiểm.
- SAKT training.py:107–115 có đúng toán học masked BCE; dùng làm reference/known-answer. Có thể viết local 5–10 dòng BCE cho GKT để tránh import cả SAKT trainer/data/AKT chain chỉ vì một utility. Không tạo framework/shared module mới hoặc sửa nguồn đang gated.
- SAKT training.py:76–81 state digest và finite/clip/cap-before/after-step là mẫu kỹ thuật; source inventory GKT phải bind actual GKT training/recurrent/core/config và helpers thực dùng, không chép danh sách SAKT.
- Không reuse SAKT collate_target_batch hoặc training_data: chúng fit exercise vocabulary từ train LearnerEvents và sliding terminal-query windows, còn GKT là whole sequence node IDs + answered responses. Nối trực tiếp sẽ lặng lẽ chọn item→node/window/first-target semantics. Shared StableVocabulary/mapping audit hữu ích khi sau này có adapter được duyệt; GKTBinding.vocabulary_sha256 hiện là caller-supplied, không train-only fit certificate.
- Train-only ở bước này là role + identity/allowlisted toy observables; không đọc validation/test để tạo graph/vocab, không tạo chứng nhận train graph từ metadata tự khai. Mapping concept/exercise_tag, multi-tag, graph construction và S05 vẫn pending.

## Acceptance tối thiểu, không ép loss giảm

Một suite mới bounded, có ledger ghi TRƯỚC mỗi Adam.step và fail trước update thứ9; controller postelapsed≤60s, không chỉ subprocess timeout. Dự toán **6 genuine updates tổng**: (1) implementation một step + scalar/manual same-initialized control một step =2, so loss/count/grad/weights với cùng optimizer config; (2) shared happy fixture2 successive fresh/recomputed-state steps=2, finite nonzero gradient/parameter delta và input immutability; (3) padding-vs-equivalent packed case một step mỗi bên=2, so selected population/parameter update trong tolerance đã khai báo. Không đòi mọi parameter nonzero gradient trong mọi tiny batch hoặc positive efficacy/loss drop. Các case còn lại 0 updates dùng mô hình/fixture đã tạo: independent masked-BCE known answer, label causality ở forward, role/domain/vocab/graph/recipe/source/state/model-version drift, wrong optimizer params/settings, empty/subset mask/duplicate rows/OOV, caller-state requires_grad, expired/zero budget, default-meta CPU, post-step deadline bằng shared happy receipt và fake clock (không thêm update). Nếu cần thêm genuine update phải còn ledger budget≤8; không tăng cap ngầm. Negative guards phải reject trước forward/step bằng spies, không dùng auth bypass. Không rerun existing GKT/SAKT broad suites chỉ để tăng counts.

## Checkpoint là bước sau, chưa gộp vào miếng đầu

SAKT training_checkpoint.py:85–173 là **weights-only** + bound JSON, `resume_supported=False`; không có optimizer/RNG snapshot. Không gọi nó là GKT resume hoặc dùng typed SAKT loader cho GKT. Sau khi train-batch acceptance đạt, có thể thêm riêng `gkt/training_checkpoint.py` + tests: exclusive approved run path, bounded weights_only CPU load, strict registered state-dict shapes/dtype/finite/buffer + graph/recipe/node/model-config/source identity, outer SHA/sidecar hash, completed-step counters, exact reload prediction parity. Role engineering-only và `complete_train_step`; không fabricate completed epoch hoặc fitted baseline. Sidecar ghi optimizer class/config + state digest/counters và RNG policy/source; nếu chỉ lưu weights thì ghi rõ optimizer/RNG/state continuation NOT restored, resume_supported=False. Torch/Python/NumPy caller RNG nên không bị đổi bởi helper; model construction/reload phải fork Torch CPU RNG + CPU context, không seed toàn cục.

Muốn resume thật là deliverable khác cần lưu optimizer state_dict (param-name/order map, CPU finite states), Torch CPU RNG và mọi Python/NumPy/local-generator RNG thực dùng, exact batch position/learner hidden state + parameter-version + cumulative budgets và nguồn. Phải chứng minh uninterrupted vs split/reload cùng updates/weights/optimizer/RNG, reject recipe/mapping/source/counter drift trước load. Không có bằng chứng đó thì chỉ checkpoint weights, không claim interruption recovery. Với optimizer caller-owned ở GKT03, chưa có epoch/corpus runner để xác định full resume boundary; defer thay vì chọn protocol ngầm.

**Parent cần duyệt trước code:** ownership hai file; one-step Adam explicit objective; state-version/cooperative provenance và không stale carry; hard toy/suite caps; checkpoint tách riêng. Không blocker kỹ thuật buộc phải chốt S05 trước engineering toy step, nhưng mọi corpus/final fit, node mapping, graph variant, normalization/journal parity, cold/OOV denominator, optimizer research recipe, calibration/selection/refit và scientific S04/S05 vẫn chưa adopt.

## Nguồn đã đọc và SHA-256

- `src/knowledge_tracing/gkt/recurrent.py` — `510195d71c1ddb743f747e78d7d874c04bb809931c5ec24ae6fe907fe53ec072`
- `src/knowledge_tracing/gkt/config.py` — `8785a608e017ed4f6f77f8bd027ed3b3ee8a57d6e5b34bbb6d787acd9952c5d2`
- `src/knowledge_tracing/gkt/core.py` — `4663e25d158a08d344d2f5f85735d8db927f96e14199b5d16f40b8e32701b3e1`
- `src/knowledge_tracing/sakt/training.py` — `6a05c6c20a910c0d8cf50a1def4fbdfb6e72f709ff0b5462adbc2538aa58b826`
- `src/knowledge_tracing/sakt/training_checkpoint.py` — `4f9ca08164748b47f43271924059377b1800c170771460e00a48a3fadfe60249`
- `src/knowledge_tracing/sakt/training_data.py` — `ed69caec2dcb5165b91b16952495ab05b2c8afab334f866ba1d03504a2c32cdb`
- `src/knowledge_tracing/shared_kt.py` — `06922d5a6bfd6c806fd1abb61232f58a9ccd63826e30cefaf87ce3d3b36dffa8`
- `tests/gkt/test_recurrent.py` — `bb173f7dd9b7b8cf14dbe00dd5fc75097dc87c9f5a794d90e29fd670d26afdce`
- `tests/sakt/test_training.py` — `7cf51df2915bcc80ddea71ceda3e59d3c659a7aa71cb339c2cf4ca708d68be8c`
- `tests/sakt/test_training_checkpoint.py` — `ad6367c2438978eba7b582507d6beba4f18505f7c73e59c1a86c26d9973bc7f0`
