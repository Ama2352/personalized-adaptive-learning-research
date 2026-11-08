# SAKT: trainer CPU synthetic và checkpoint engineering — 08/11/2026

## Kết quả và mức sẵn sàng

**SAKT đã có đường training/validation/checkpoint CPU synthetic riêng**, bên cạnh core và frozen inference adapter đã có. Final `tests/sakt` đạt **139 PASS trong17,32s**,0failure/error/skip:89cases cũ và50cases mới. Lượt trước giữ138PASS/1failure, không đổi historical verdict. Hai controller cộng **39,980828s**, dưới trần120s của batch.

Ledger chung tính **18 charged/attempted `Adam.step` calls** qua hai lượt, gồm một call lỗi ở lượt01; không gọi18là committed updates. Lượt02 có9calls trả về thành công. Mỗi dataset fixture mới chỉ vài targets, API giới hạn tổng train+validation≤256targets; không có Junyi/Grade10 corpus, GPU/cloud, package install hoặc hyperparameter search. Tests không yêu cầu loss giảm sau mỗi step.

**Đây là partial training-ready engineering, chưa là full proposal baseline.** Không selected-fit research, best-epoch selection/refit, cross-validation, optimizer/RNG recovery hoặc fitted `OnlineSession`. S04/S05 về mastery/calibration, first-target research accounting, model/capacity/history/môi trường vẫn cần chốt. Artifact role cố định **`synthetic_trained_engineering_only`** không nâng thành efficacy hoặc shared fitted score.

## Phạm vi source

| Tệp mới | Hành vi |
|---|---|
|[training_data.py](../../src/knowledge_tracing/sakt/training_data.py)|Explicit recipe, train-only vocabulary, disjoint learner/source-row guards, chronology, sliding one-target windows, OOV/cold ledger và sealed content identity.|
|[training.py](../../src/knowledge_tracing/sakt/training.py)|Explicit optimizer/budget config, CPU FP32 train/evaluate, unique target loss masks, finite gradients, budget completeness và source/weight digest.|
|[training_checkpoint.py](../../src/knowledge_tracing/sakt/training_checkpoint.py)|Exclusive raw state_dict + bound canonical JSON sidecar, completed engineering epoch only, bounded single hashed payload load.|
|[test_training.py](../../tests/sakt/test_training.py), [test_training_checkpoint.py](../../tests/sakt/test_training_checkpoint.py)|50new cases, target/loss known answers, resource negatives, roundtrip và parity với adapter có sẵn.|

Không sửa existing `config.py`, `model.py`, `tensors.py`, `adapter.py`, `__init__.py`, native AKT hoặc shared contracts. Old frozen adapter vẫn chỉ nhận `random_fixture`/`unverified_state`, từ chối `fit` và fitted bridge; không thêm role bypass để đi qua guard cũ. Source SHA trước/sau mỗi invocation xác nhận các tệp frozen đã giữ nguyên.

`source_identity()` bind10tệp:6SAKTfiles (config/model/tensors và3trainer modules), AKT windows/encoding/types và `shared_kt.py`. Không tự là dependency/runtime certificate hoặc chữ ký chứng minh training provenance do bên ngoài khai báo.

## Data/geometry/policy đã explicit hóa

Caller đưa `SAKTDataRecipe` gồm context, padding side, first-target policy và hai conventions hiện được adapter hỗ trợ: `sliding_last_context`, `window_relative_interaction_rank`. Không có research defaults. Vocab lấy từ **train learners**, validation không thêm items; learners/source rows hai phía phải tách biệt, thời gian `(time_done,source_row)` đã tăng và identity thống nhất. Không tự sort hoặc gộp multiple concepts.

Reuse pure `akt.windows.iter_window_slices`/`slice_causal_inputs` với **target_block=1**; không dùng nguyên block100/context100 của AKT vì targets cuối block có thể nhìn history dài hơn declared SAKT context. Mỗi target chỉ xuất hiện đúng một lần trong epoch loss; overlap chỉ là context. Prior responses shift đúng một lần, first slot reset−1; current label chỉ vào BCE ngoài `SAKTCore.forward`.

Training collation đặt target mask tại terminal slot: right padding dùng `sequence_length−1`, left padding dùng `batch_width−1`. Context/padding không được tính loss. OOV target không đưa vào core; OOV trong history cắt suffix rồi áp first-target policy lại. `query_only` cho phép cold query score; `unsupported` loại cold khỏi objective/validation denominator. Không gán probability0 cho unsupported. Các trạng thái expected/eligible/OOV/cold-excluded/optimized-or-evaluated/unprocessed được ghi riêng.

**Giới hạn input domain:** API hiện nhận in-memory `LearnerEvents`/`KTEvent` có trường fold, reuse types kiểu pipeline exercise hiện tại. Fixture cố ý là dummy, không phải role-aware Grade10 simulator training bridge. Không được dựng fold giả cho corpus Grade10 rồi coi S05 đã được duyệt. Cần mapper/role-aware data contract riêng nếu allocation sau này yêu cầu; training API này chưa hoàn thành inference `OnlineSession`.

## Training/validation và cap

`SAKTTrainingConfig` yêu cầu caller truyền Adam/lr/betas/eps/weight_decay/clip, epochs, batch size, seed, objective reduction, max steps/targets/seconds và CPU FP32. Batch này chỉ hỗ trợ `mean_bce_on_eligible_targets`; epoch loss báo summed BCE và actual eligible denominator. Không early stopping, không tìm best validation epoch, không chọn hyperparameters bằng kết quả.

Ceilings engineering fail **trước model allocation**: d_model≤64, heads≤8, head_dim≤64, max_length≤257, batch_size/epochs≤32; vocab bị giới hạn bởi256input targets; geometry phải chứa declared context+query. Đây là max bounds, không cấu hình nghiên cứu được khuyến nghị. Training max_steps≤32 là cap mỗi call; tests có ledger chung chặn trước call thứ33 qua mọi attempts.

Toàn training, gồm SAKTCore constructor, Adam constructor/lazy state, shuffle/forward/backward/step và validation, nằm trong explicit CPU device context. Init dùng CPU default generator trong forked CPU RNG; shuffle dùng generator local. Negative control với caller default=`meta` và trap CUDA seeding pass; không dùng actual GPU để kiểm.

Max-seconds có checks trước update, trước/giữa/sau validation, sau optimizer và final stage. Bị hết budget trả `bounded`, giữ processed/unprocessed ledger, checkpoint từ chối. Đây là **cooperative deadline checks giữa operators/stages**, không hard interrupt hay peak-RAM attestation; outer subprocess timeout mới là boundary của invocation. Validation dùng eval/inference mode, giữ weights và khôi phục caller training mode; validation ledger ghi evaluated targets, không gọi đó là optimizer updates.

## Checkpoint semantics

`save_engineering_weights` chỉ chấp nhận unchanged model/source với toàn requested epochs hoàn tất, positive optimizer steps và counters khớp population/epochs/batch/caps. Nếu run bị bounded, kể cả vừa train đủ nhưng timeout ở validation/final stage, không lưu artifact hoàn tất. Không chọn model từ metric validation; lưu last requested completed epoch.

Binary vẫn là **raw state_dict** tương thích core hiện có. Sidecar JSON bind model/training config, domain/vocab/order, input/role/window/cold policy, source hashes, checkpoint/state hashes, completion counters; canonical JSON identity dùng cùng list representation cho betas khi save/return/load. Exact schema int phân biệt bool; counter mismatch và rehashed invalid metadata bị reject trước deserialize. Output chỉ được tạo exclusive trong engineering test/results paths; không ghi đè artifact cũ.

Load đọc bounded sidecar và **một immutable checkpoint payload `max_bytes+1`**, hash đúng bytes rồi `torch.load(BytesIO(payload),weights_only=True,map_location='cpu')`. Strict finite CPU FP32 keys/shapes và state digest được đối chiếu; model construction có CPU context. Serialized byte cap không là peak-memory/decompression guarantee của PyTorch. Không optimizer/RNG state, resume format hoặc cross-runtime parity claim; không author checkpoint reproduction.

Sidecar/checksums xác nhận consistency với expected identity caller cung cấp, không tự chứng minh nguồn dữ liệu là synthetic hoặc methodology đã được phê duyệt. Raw weight file không được tự đổi role thành fitted research. Test so parity đi qua adapter cũ dưới **test-only `unverified_state`**, trong khi training artifact giữ engineering role; adapter vẫn từ chối OnlineSession promotion.

## Bằng chứng đã chạy

| Attempt | Output thật | Diễn giải |
|---|---|---|
|Pretest static review|0tests/0optimizer|Giữ3source snapshots và review receipt. Reviewer phát hiện canonical tuple/list, deadline/completion, geometry caps, CPU constructor/RNG và validation/source-ledger gaps; sửa trước first test. Không dựng red-test hoặc raw log giả.|
|`parallel-sakt-training-20261108-01`|138PASS/1FAIL,18,11s; controller20,4109295s;9charged step calls|Meta-default regression fail tại Adam lazy state: ctor-only CPU guard chưa đủ. Giữ source/log/XML/run/copy SHA. Không đổi test để che lỗi.|
|`parallel-sakt-training-20261108-02`|**139PASS**,17,32s; controller19,5698982s;9step calls|Bọc toàn train scope trong CPU context. Meta regression giữ nguyên và pass;0failure/error/skip. Source/tests freeze sau PASS.|

Acceptance gồm masked BCE known answer; unique exhaustive target populations; train-only vocab/disjoint chronology; OOV/cold resets; current-label perturbation giữ p_t nhưng có thể đổi prior tại t+1; finite gradients/weights đổi; deterministic tiny runs; validation không cập nhật; checkpoint roundtrip/canonical identity, source/domain/config/vocab tamper negatives; strict single payload; allocation và deadline negatives. Parity tests giữ đủ left/right × query_only/unsupported; so history accounting và scores với old adapter trên weights đã reload, tolerance abs1e−7.

Reviewer platform đọc source/tests và cuối cùng chấp nhận scope fix CPU context; không execute hoặc sửa source. Review không thay actual139PASS receipt và không là scientific protocol approval.

## Tái lập và archive

Original evidence tại `artifacts/akt/local-tests/parallel-sakt-training-20261108-{01,02}/` gồm exact source/test snapshots, [log02](../../artifacts/akt/local-tests/parallel-sakt-training-20261108-02/pytest.log), [XML02](../../artifacts/akt/local-tests/parallel-sakt-training-20261108-02/pytest.xml), [receipt02](../../artifacts/akt/local-tests/parallel-sakt-training-20261108-02/run.json). [Budget receipt](../../artifacts/akt/local-tests/sakt-training-budget-20261108-01/budget.json) và [shared step-call ledger](../../artifacts/akt/local-tests/sakt-training-budget-20261108-01/optimizer_updates.jsonl) giữ cumulative charge, không reset giữa retries. [Pretest note](../../artifacts/akt/local-tests/sakt-training-pretest-review-20261108-01/review.json) phân biệt static findings với actual failure01.

Invocation dùng project `.venv\Scripts\python.exe -B -m pytest tests/sakt -q -p no:cacheprovider`, basetemp/JUnit riêng từng attempt, CPU-hidden CUDA,1thread, source SHA trước/sau. Outer timeout02 lấy phần còn lại của120s cumulative, không một120s mới. Khi tái lập phải chọn run/budget/attempt paths mới, không append ledger cũ hoặc overwrite snapshots. Không có broad/native gate run mới trong batch.

Bundle bất biến [sakt-training-engineering-20261108-01](../runs/sakt-training-engineering-20261108-01/README.md) giữ source/report/log/XML/receipts/hash và selected small sidecars; `.pt` giữ ngoài Git, chỉ inventory SHA. Archive không chạy lại tests/model. Parent review/index/state/Git riêng. Trước fitted research baseline còn thiếu selected-fit/inner-selection/refit protocol, corpus/splits/role-aware bridge, required comparator allocation và S04/S05; không dùng kết quả toy loss làm thành tích KLTN.
