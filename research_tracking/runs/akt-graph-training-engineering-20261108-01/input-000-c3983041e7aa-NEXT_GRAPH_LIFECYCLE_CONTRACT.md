# Gói tiếp theo: lifecycle graph-aware toy — contract đề xuất, chưa duyệt triển khai

Ngày08/11/2026. Chỉ đọc source; không model/test/optimizer/cloud/data run. Tài liệu này là kế hoạch NEW, **không là input của bundle A2/A3 đang đóng**. Không có `simulator_training.py` trong source hiện tại; lifecycle thực tế là `akt/simulator_engineering.py`.

## Khoảng trống và điểm reuse

`run_engineering_epoch` hiện đã có scope/budget/output-exclusive, fit vocabulary train-only, target ledger, một complete epoch, đánh giá selection toàn population, checkpoint/reload/parity và failure receipt. Reuse lifecycle này. `training.train_epoch` đã có shuffle determinism, batch/step/resource accounting và partial-epoch semantics. Tuy nhiên nó tự collate `TrainingWindow` thành `AKTBatch`; `AKTAdapter.step` chỉ gọi/clip/đo update trên `adapter.native`. `checkpoint.save_checkpoint` chỉ lưu `adapter.native.state_dict()`. Nếu gắn backbone ở `.native` rồi gọi các API này nguyên trạng, branch/gate sẽ bị bỏ qua lúc train hoặc checkpoint. Không dùng cách đó.

`GraphAKTPrototype` đã nhận graph-aware batch, labels riêng, full-prefix→effective-window, source/confidence/gate binding, differentiable loss và exact disable. Nó chưa có step/predict_windows/encoding interface. `simulator_engineering._validate_scope` còn bắt domain `synthetic-akt-engineering-*`, graph prototype bắt `synthetic-akt-graph-engineering-*`; gọi trực tiếp không hợp lệ. Generic lifecycle cũng chưa ghi CSV, hiện chỉ có selection JSON.

## Gói code nhỏ nhất đề xuất

1. **Mới** `akt/graph_training.py` và `tests/akt/test_graph_training.py`: graph adapter/backend và public graph-engineering entry point. Không thêm trainer chung thứ hai. Adapter có `.native = toàn GraphAKTPrototype`, `.encoding = SimulatorEncoding.exercise_encoding()`, `.config`; native upstream bên trong giữ nguyên.
2. **Sửa hẹp** `akt/training.py`: optional keyword `batch_factory(entries)` ở đúng chỗ collate; default vẫn collate hiện tại. Callback nhận nguyên `TrainingWindow` cùng learner/window/global metadata, trả `AKTBatch` cho accounting. Không thêm graph-specific import, không đổi shuffle/loss/default budget/recovery.
3. **Sửa hẹp** `akt/simulator_engineering.py`: tách internal lifecycle backend/factory để base public API giữ nguyên; graph backend cung cấp scope, source inventory, identity, adapter/window factory, loader. Base purpose/domain/loader mặc định không nhận graph artifact. Graph purpose là enum riêng với toàn bộ caps cũ **và** giới hạn graph≤8items/4concepts/16edges; không nhận prefix/domain tùy ý của caller. Output CSV là writer nhỏ dùng ledger có sẵn. Nếu refactor này quá lớn, tách gói step+collation trước; không nhân đôi vòng lifecycle.
4. Không sửa upstream, graph arithmetic, config/hyper defaults, Junyi CLI, production OnlineSession hay recovery. `checkpoint.py` hiện đủ để lưu/restore toàn module nếu adapter.native đúng; không cần sửa nó.

## Collation và step thực sự

`batch_factory` phải lấy ordered window IDs từ entries do `iter_simulator_windows(train, encoding, training=True)` sinh thật; xác minh các window/labels đúng canonical train shard đang bind. Sau đó gọi `prepare_graph_batch(full_train_shard, ..., window_ids=ordered_ids, confidence=..., gate_feature_recipe=...)` thật. Collate loss labels bằng native helper hiện có, so khớp q/qa/valid/target/source rows với graph batch. Giữ một ticket nội bộ consume-once gắn chính object AKTBatch đó với graph batch đã seal; `step` từ chối batch ngoài hoặc ticket stale. Không suy learner từ source_rows, không match bằng tensor-content vì hai learner có thể trùng rows/sequence; AKTBatch không chứa learner/window IDs. Không reseal/mutate GraphAKTBatch sau khi builder trả về. Labels tối ưu truyền riêng vào `model.forward_details(graph_batch, batch.loss_targets)` như API hiện có.

Adam do lifecycle tạo từ **toàn bộ** `GraphAKTPrototype.parameters()`; verify exact parameter-object set, không foreign/missing/duplicate params. Zero_grad→forward graph→loss_sum/valid_target_count→backward→clip toàn model bằng cap config hiện có→step. Ledger ghi reservation trước step, Adam-return và batch-complete riêng; exception sau step không rollback/không được đếm0update. Evidence tách backbone/message/readout/gate parameter/gradient hashes; inactive branch được phép không update. Không yêu cầu loss/metric tăng tốt.

## Selection, checkpoint và identity

Selection adapter giữ full **selection** shard riêng, kiểm window IDs/contents so với canonical iter; gọi cùng graph builder/model với no_grad và mode được khôi phục. Mọi `(learner_id, source_row, global_rank)` của `scoring_targets` xuất đúng1lần: OOV probability/gate/residual=null, reason rõ; không graph-rescue. Ghi cùng scalar p, base p, applied flag, gate/null, confidence mass/normalizer và window anchors cho target supported. Phân biệt gate0 thực với slot inactive; không gọi các đại lượng này mastery/confidence calibrated. Kiểm weights/input/source không đổi khi selection. Labels chỉ vào scoring sau prediction.

Identity/checkpoint bắt buộc: purpose/weight_role engineering_only, plan/train/selection SHA, bank+item→concept map, encoding train-shard/vocab, graph full directed edges+SHA, **full EdgeConfidence asdict** (kind/values/provenance/fitted_role)+identity, GraphPrototypeSpec+message/gate feature tags, explicit caller module-construction recipe/parameter schema, source inventory gồm native+graph helpers+pinned akt.py, config/budget/seed/runtime và target-ledger digest. Không serialize module/callable pickle; restore bằng caller-reviewed factory recipe rồi strict state_dict. State dict phải gồm backbone+message+readout+gate; optimizer state dùng cùng named parameter order. Generic payload đã lưu optimizer/Python/NumPy/Torch RNG; khai báo **resume_supported=False** vì không có graph sampler/recovery contract, không biến RNG payload thành resume proof.

Loader bounded8MiB/actual-byte SHA/weights_only/CPU, source+recipe+graph+confidence+encoding strict, chỉ COMPLETE epoch; rebuild graph adapter rồi restore chung, parity toàn supported probabilities/gates/residuals và toàn target keys/OOV. Không có training_domain/selected research certificate; production online phải reject engineering artifact. Tắt branch là cùng backbone đã train; chưa phải A0 system checkpoint.

Một epoch chỉ có một candidate: ghi policy explicit `only_complete_epoch`, không gọi early-stopping/Junyi select_checkpoint và không tuyên bố chọn epoch tốt nhất. Epoch partial không publish selected checkpoint/COMPLETE/result; giữ failure/accounting, không giấu updates đã xảy ra. Publication dùng path exclusive/no-clobber primitive hiện có; CSV/metadata xong trước complete run marker.

## Acceptance và budget đề xuất trước khi xin chạy

Freeze code + pure contracts trước mọi Adam update. Đề xuất ONE A3 handmade epoch2learners/≤12events, batch2 →1plannedstep; 1negative partial run có thể thêm1step, **hardmax4steps/60s cumulative kể cả failures** nếu root duyệt. Không bốn variant fits. A0/A1/A2 routing/parameter ownership/cap/source/role/wrongconfidence/wrongfactory guards kiểm bằng pure hoặc no-update tests. Happy cần actual nonzero/update backbone+branch+gate, complete train ledger, full selection CSV có OOV, strict actual reload parity, immutable evaluation, no production fitted promotion. Negative kiểm foreign/stale batch trước forward, optimizer bỏ gate trước step, partial không COMPLETE, altered confidence/graph/encoding/source trước load. Không test efficacy hay favorable seed. Cold CUDA-visible/default-meta guards và threads1/2 restore reuse existing contracts.

Đây chỉ engineering recipe cùng effective window, không fit estimator confidence/calibration, không thêm full-history cache, không chọn scientific node/item mapping hay S04/S05. Arbitrary caller module/provenance vẫn cooperative declaration. Gate24 source binding sẽ stale khi sửa training/lifecycle và thêm native module/tests; cần root refresh software evidence, không suy PASS cũ cover code mới.

## Source đã đọc (SHA tại lúc lập kế hoạch)

- `src/knowledge_tracing/akt/simulator_engineering.py`: `c6a6060906f354309ed6a8da3a33a23f4272497eff8f50e8428360396f1d6c5e`
- `src/knowledge_tracing/akt/training.py`: `8eff1265e9fccb6488c6bfc0c6af9cda8c8ea68966a2b001752991de0db5805a`
- `src/knowledge_tracing/akt/model.py`: `e40b068bc305d0157a03f4baea3cd8e06c5777611c492f02fb65f792760e9e9f`
- `src/knowledge_tracing/akt/checkpoint.py`: `bc1a6fbdcaa55c864cb9f18d531dcede440f9cf364dc9025420615520394fc91`
- `src/knowledge_tracing/akt/simulator_data.py`: `06110c6f3d85c9feab65e54a57c79595e30957df76ccdd26e464389417760a73`
- `src/knowledge_tracing/akt/tensors.py`: `688fb915f8aa4958f47ee541e9ed92be577c0e14bc9c29e1d969be94863a4867`
- `src/knowledge_tracing/akt/graph_prototype.py`: `9fc6b8271da503ce16d25147a320bf0ffb9312e5416abae40fbb034f26d3157a`
- `src/knowledge_tracing/graph_augmentation.py`: `105aa918f1dc5d8fcfae22c9d8e7d2e13c1832b71d8b6a7ce8deed67d443ff08`
