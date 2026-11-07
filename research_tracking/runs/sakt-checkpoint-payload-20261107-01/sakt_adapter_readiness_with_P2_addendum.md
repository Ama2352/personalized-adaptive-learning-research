# SAKT frozen inference adapter — 07/11/2026

**Cập nhật08/11, trong cùng batch:** đã sửa P2 checkpoint payload binding sau adversarial review; current targeted suite **89 passed**. Phần87-case initial engineering bên dưới là snapshot trước sửa; bundle `sakt-inference-engineering-20261107-01` giữ nguyên. Xem addendum cuối tài liệu để không dùng87pass như bằng chứng đã kiểm TOCTOU.

## Kết quả và phạm vi

Đã thêm `src/knowledge_tracing/sakt/adapter.py` và `tests/sakt/test_adapter.py` với **frozen inference CPU FP32** từ raw PyTorch `state_dict`, caller-declared domain/vocabulary/config/geometry và checkpoint SHA. Final targeted suite `tests/sakt` đạt **87 passed, 0 failure/error/skip**, gồm 37 core cases có sẵn và 50 adapter cases, 6,35s. Không optimizer step, trainer, realdata/Holdout, GPU, Modal, dependency install hoặc thí nghiệm efficacy.

Đây là engineering với **random-weight fixture**, không fitted SAKT baseline. Adapter trả `SAKTInferenceScore` riêng có `weight_role=random_fixture` hoặc `unverified_state`; không gắn `OnlineScore(prediction_kind="fitted")`. `fit()` và `as_online_backend()` từ chối rõ. Vì shared `OnlineScore` chỉ có fitted/unseen-item, còn cold-unsupported và selected-fit provenance chưa được chốt/triển khai, **complete OnlineSession bridge vẫn incomplete**. Không sửa shared API, AKT, SAKT core/config/tensors hoặc `sakt/__init__.py` để ép các semantics này.

Nguồn contracts: [shared SequenceKTModel](../../src/knowledge_tracing/shared_kt.py), [simulator bridge](../../src/knowledge_tracing/simulator_bridge.py), [AKT online adapter](../../src/knowledge_tracing/akt/online.py), [SAKT core report](sakt_core_readiness_20261107.md). Import adapter mới phải explicit từ `knowledge_tracing.sakt.adapter`; package exports cũ giữ nguyên.

## API và các lựa chọn caller phải khai báo

| Thành phần | Contract thực hiện |
|---|---|
| `SAKTInferenceSpec` | Không default: caller cung cấp context, window/position policy, first-target policy, padding side, inference batch size, device và precision. Hiện chỉ hỗ trợ CPU FP32, `sliding_last_context`, `window_relative_interaction_rank`, left/right padding. Các lựa chọn khác bị từ chối, không fallback ngầm. |
| `inference_identity` | Bind toàn bộ core config/spec, simulator bank environment + item/concept/difficulty identity, vocabulary hash, weight role và SHA của bốn source files SAKT. Vocabulary phải canonical/sorted/unique và thuộc bank; cardinality khớp `num_items`. Đây là metadata equality do caller đối chiếu, không training certificate. |
| `load_frozen_sakt` | Caller cung cấp raw state_dict path, expected SHA/identity, weight role và explicit byte budget. Kiểm SHA trước/sau load; `torch.load(weights_only=True,map_location="cpu")`, chỉ finite FP32 tensors và strict key/shape loading. Không chấp nhận optimizer/checkpoint envelope hay tự tạo training format. Tạo core trong CPU RNG fork, không làm lệch random stream bên gọi. |
| `predict_details(CausalSequenceInputs)` | Chỉ item IDs, timestamps/order, shifted prior responses, learner segmentation và source rows. Không nhận target labels. Trả score/support reason/history accounting/learner/source-row/checkpoint SHA/binding SHA theo đúng thứ tự inputs. Không sort/resegment inputs âm thầm. |
| `predict(CausalSequenceInputs)` | Trả ndarray chỉ khi mọi target có probability. Nếu OOV/cold-unsupported thì từ chối và yêu cầu `predict_details` + explicit coverage accounting; không đưa NaN/null sentinel vào metrics như prediction fitted. Method presence không có nghĩa adapter có khả năng `SequenceKTModel.fit`. |
| `SAKTHistory`, `query`, `query_many` | History immutable mang learner ID và prior `Observation`s. Query chỉ là `ItemQuery(item_id,timestamp,source_row)`, không nhận current outcome/oracle. Learner ID phải khớp history; item/history phải trong bound bank và chronological/unique rows. Mỗi candidate dựng window riêng từ cùng prior history, không concatenate candidates thành fictitious practice. Không cache/commit history. |
| Frozen guards | Trước/sau inference kiểm config/spec/vocabulary/bank/source identity, eval mode, requires-grad flags và SHA của parameter state. Phát hiện cả sửa weights qua `.data` không tăng version counter. Metadata `binding` trả copy để caller không sửa identity nội bộ. |

Vì chưa có trainer/selected artifact, loader hiện **không nhận** weight role `fitted`/`selected_fitted`. Random fixture và `unverified_state` vẫn có finite mathematical scores để kiểm software; chúng không là fitted evidence và không đủ điều kiện export/metrics như benchmark.

## Geometry, first target và OOV

`context=C` nghĩa là tối đa C past interactions **cộng một query slot**; cần `config.max_length >= C+1`. Với mỗi target, adapter lấy sliding prefix suffix, giữ thứ tự đã cung cấp và tái đánh số position theo interaction rank trong window. Đây là geometry khai báo của core hiện có, **không giả tương đương AKT global block anchors**. Batch size chỉ gom các windows độc lập, không tăng context.

Vocab IDs shared 0..N−1 chuyển sang native IDs 1..N qua collator hiện có; −1 là OOV sentinel. Unknown current target trả `probability=None, support_reason=oov_item`. OOV interaction trong prefix là barrier: chỉ known contiguous suffix phía sau nó được dùng; không kéo previous label từ trước barrier vào cold slot. Không biến unknown item thành random finite fitted prediction.

Caller phải chọn một trong hai first-target policies:

- `query_only`: zero usable history vẫn trả score query-only của core với `has_history=False`, reason `cold_query_only`.
- `unsupported`: zero usable history trả None/reason `cold_unsupported`.

Policy cũng áp dụng sau OOV reset hoặc khi context=0, không chỉ interaction đầu toàn learner. Đây là **explicit caller contract để kiểm kỹ thuật**, chưa adoption scientific first-target scoring/S04/S05. Không ánh xạ cold-unsupported thành unseen-item của shared bridge vì hai nghĩa khác nhau.

Trong output, `global_rank` là vị trí target trong learner sequence/history; `history_available=min(global_rank,context)`, `history_used` là known suffix thực sự được dùng; `context_reset` báo OOV barrier/current OOV. Timestamps/source rows chỉ kiểm chronology và tie ordering. Gap 14 ngày không tự đổi score khi history giữ nguyên; core không nhận elapsed calendar time. Điều này không chứng minh learner retention bất biến.

## Kiểm thực tế và positive/negative controls

Fixtures khai báo riêng: bank A/B/C/D thuộc domain `synthetic-sakt-fixture-not-trained`, vocab A/B/C (D là known-bank/OOV), d_model8, 2heads, head_dim4, max_length4, context2, dropout0,2 nhưng inference eval, seed42, byte cap1.000.000. Đây không là final benchmark architecture/geometry.

| Nhóm kiểm | Điều đã xác nhận |
|---|---|
| Strict loading/binding | Wrong SHA, config, vocab, environment, bank metadata, geometry và source binding bị chặn; envelope, NaN, FP64, thiếu parameter và byte-budget violation không load được. Raw fixture state chỉ được load, không optimizer/training. |
| Causality | Đổi current/future response không đổi current/earlier probabilities; đổi future items không đổi past scores. Positive control thay observed past response làm score sau đó đổi. Đổi input ngoài declared context không đổi target cuối. |
| Geometry parity | Adapter output khớp independently prepared core windows; không double-shift responses. C=0 và C=2, cả hai cold policies và OOV reset đều được kiểm. |
| Batch và learner isolation | Singleton/batched/left/right padding/permuted candidates và multi-learner offline segments tương đương trong abs1e−6. Thay learner A không đổi learner B; foreign learner/history binding, mixed-user segments hoặc repeated learner segments bị từ chối. |
| Queries thuần | Repeated candidate queries không đổi history; OOV candidate giữ vị trí unsupported trong batch. Current outcome keyword/Observation dùng làm query bị từ chối. Online-style query khớp cùng target trong offline prefix. |
| Input/provenance guards | Duplicate rows, chronology đảo, current response ở cold slot, invalid IDs và cross-bank item bị chặn. Metadata trả về không cho sửa internal identity; random role không được đổi sang fitted path. |
| Frozen state/RNG | Load/predict không đổi caller RNG, source checkpoint bytes hoặc input arrays; không gradient/update; sửa weights bằng `.data`, train mode, requires-grad hoặc spec sau load bị chặn. |

Các numerical equivalence tests dùng tolerance ghi tại từng assertion (abs1e−7 cho prefix/query examples, abs1e−6 cho batch/peer comparisons); không hứa bitwise batch equality trên mọi kernel/runtime. Positive/negative fixtures là bằng chứng software, không AUC/learning outcome.

| Lượt | Kết quả đã lưu | Vai trò snapshot |
|---|---|---|
| `parallel-sakt-adapter-20261107-01` | **82 passed**, 5,67s; controller elapsed6,817595s, exit0. | 37 core + 45 adapter cases, trước năm cases multi-learner/cold-reset/clock bổ sung. Có exact source/test snapshots riêng. |
| `parallel-sakt-adapter-20261107-02` | **87 passed**, 6,35s; controller elapsed7,669797s, exit0; JUnit0fail/error/skip. | Final 37 core + 50 adapter cases. Core/shared dependencies giữ SHA trước/sau; chỉ test file mới mở rộng so với trial01. |

Logs/JUnit/source snapshots/run JSON nằm trong `artifacts/akt/local-tests/<run-id>/`; mỗi invocation dùng timeout120s, `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=''`, `-B`, `-p no:cacheprovider`, tmp riêng. Không có failed targeted test invocation trong hai lượt này. Cả hai success snapshots giữ nguyên để đối chiếu số test/source thực sự, không gán final test source cho trial01.

Lệnh final từ repository root:

```powershell
$env:PYTHONPATH = 'src'
$env:CUDA_VISIBLE_DEVICES = ''
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp=artifacts/akt/local-tests/parallel-sakt-adapter-20261107-02/tmp --junitxml=artifacts/akt/local-tests/parallel-sakt-adapter-20261107-02/pytest.xml tests/sakt
```

Lệnh thực tế được wrapper standard-library chạy với `subprocess.run(...,timeout=120)` và stdout/stderr vào `pytest.log`; danh sách arguments đầy đủ trong `run.json`. Khi tái chạy phải dùng run/output ID mới, không ghi đè basetemp/log/JUnit hiện có.

## Những phần intentionally incomplete

1. **Selected-fit provenance và training pipeline:** chưa có trainer/fit, train-only vocabulary derivation/split attestation, selected epoch/refit, optimizer/resume/export/calibration hoặc checkpoint training schema SAKT. State_dict SHA + external caller metadata chỉ bind identity đã khai báo; không tự chứng minh weights/vocabulary được tạo đúng domain/role. Người gọi có thể gán sai metadata; adapter không là cơ chế xác thực training artifacts.
2. **Complete simulator `OnlineSession` backend:** own scores không là shared `OnlineScore`; không sửa bridge để random weights được gọi fitted hoặc cold unsupported bị gọi unseen item. Cần selected model artifact/provenance và quyết định first-target/unsupported accounting trước adapter bridge hoàn chỉnh, tickets/snapshot/domain semantics end-to-end.
3. **Information boundary end-to-end:** `SAKTHistory` chặn foreign learner ID và model không lưu histories, nhưng prior `Observation` tự nó không có learner ID/source attestation. Caller vẫn phải bảo đảm observations được lấy đúng learner/domain. Offline numeric `CausalSequenceInputs` cũng không mang domain certificate; hash binding tại loader không xác thực origin của từng input row.
4. **Scientific protocol:** context/position/cold convention được explicit hóa chứ chưa freeze benchmark equivalence hoặc S04 mastery. Không calibrator/reference-masterty/threshold/controller adoption; correctness score không là P(K). Không thay bank/vocab numeric IDs để dùng Junyi weights cho simulator.
5. **Runtime/packaging:** CPU FP32-only trong module này; chưa CUDA/Linux/Colab validation, throughput/RAM production benchmark, large checkpoint budget hoặc source-kit inclusion. Actual Colab proof của AKT không nghiệm thu SAKT adapter mới. Không nâng Gate15/Gate4/overall readiness từ targeted tests.

Parent cần review ba owned files, đóng evidence bundle rồi cập nhật map/index/registry nếu phù hợp. Gói này không sửa state/tasks/index hoặc Git; không bỏ SAKT/required comparators vì adapter/trainer còn thiếu.

## Addendum P2: bind đúng checkpoint payload được deserialize — 08/11/2026

Adversarial review chỉ ra loader đầu tiên gọi `stat`, hash path, `torch.load(path)` rồi hash path lần nữa. Nếu file đi từ A→B→A giữa các lần đọc, before/after hashes vẫn là A trong khi loader có thể deserialize B. Initial87cases chưa kiểm sự khác nhau giữa các reads này; hash-before/after path không đủ để nhận diện actual loaded bytes. Đây là lỗi engineering trong loader hiện có, không phải lỗi metric hoặc một thay đổi scientific protocol.

Sửa nhỏ nhất chỉ trong owned adapter/test: bỏ `stat` làm byte-budget gate; đọc **một payload bounded bằng `max_checkpoint_bytes+1`**, chặn rỗng/overflow dựa actual length, SHA-256 chính payload đó phải khớp expected, sau đó `torch.load(io.BytesIO(payload),weights_only=True,map_location="cpu")`. Như vậy actual deserialization dùng đúng immutable bytes vừa được hash, dù path thay đổi trong lúc load. Không thêm training checkpoint format, optimizer hoặc model feature.

Post-path drift check vẫn đọc bounded để từ chối file đang khác expected sau load, nhằm giữ consistency với caller. Nó không được dùng làm security basis và không được tuyên bố phát hiện mọi A→B→A; identity của model đã load dựa trên single hashed payload. State-dict/config/vocab/domain checks và incomplete fitted bridge vẫn như phạm vi trước.

Read-only review của agent platform đã kiểm patch/tests/logs và không còn blocking issue trong phạm vi P2; không rerun hoặc sửa source. Byte cap giới hạn serialized payload được đọc, **không** là peak-RAM/decompression attestation của PyTorch/tensor allocation.

| Attempt mới | Kiểm và kết quả |
|---|---|
| `parallel-sakt-payload-20261107-01-before` | Chạy đúng hai regression tests trên source cũ: **2 failed**, 7,88s, exit1; không collection error. A→B→A fault injection cho thấy deserialized SHA khác authorized SHA; negative control `stat` khai size nhỏ hơn file cho phép overflow mà không raise. Giữ source/test snapshots, log/JUnit và pre/post SHA riêng. |
| `parallel-sakt-payload-20261107-02-after` | Chạy toàn `tests/sakt` sau fix: **89 passed**, 7,33s; 37 core + 52 adapter cases,0fail/error/skip; controller8,677624s, dưới120s. Hai regressions đạt, không optimizer step/GPU/realdata. |

Regression dùng deterministic fault injection tại `torch.load` và `Path.stat`, không giả làm một actual concurrent filesystem exploit. Test A→B→A vừa kiểm SHA của argument thực tế được deserialize vừa kiểm loaded prediction bias bằng state A. Overflow test thêm đúng một byte quá cap, giả `stat` size cũ và xác nhận deserialize không được gọi. Các model tensors chỉ được load/randomize để kiểm loader, không train.

Logs/JUnit/source snapshots ở `artifacts/akt/local-tests/<attempt-id>/`; byte inventories và corrected evidence được đóng trong run mới `sakt-checkpoint-payload-20261107-01`. Bundle37outputs cũ giữ nguyên source87 snapshot và historical verdict. Sửa này không nghiệm thu trainer/fitted OnlineSession/S04/S05 hoặc Gate16 native AKT/shared; không thay root indexes/state/tasks/Git.
