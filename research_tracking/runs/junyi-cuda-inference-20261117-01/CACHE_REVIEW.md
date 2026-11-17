# Rà soát tách CPU/cache và GPU suy luận calibration

Ngày 17/11/2026. Review tĩnh trên source đang triển khai. Không sửa code, tạo cache, gọi cloud hoặc chạy GPU trong nhánh này. Metadata tests và CPU probes chưa thay cho kiểm CUDA thực tế.

## Kết luận ngắn

Đường ngắn nhất tận dụng cache hiện có là CPU tạo một bộ cửa sổ calibration dùng chung, tạo context cache riêng cho A1/A2/A3, GPU chỉ chấm batch và ghi xác suất theo window, rồi CPU nối metadata/labels để xuất Parquet, fit V1 và upload Drive. Cần một cầu nối có kiểu và pin giữa output số của GPU với records CPU. Không cần viết lại fitter hoặc giả calibration thành selection để dùng cache cũ.

## 1. API cache đã có và phạm vi thực sự

| API | Có thể dùng ngay ở mức source | Điều kiện cần giữ |
|---|---|---|
| `research_junyi_window_cache.window_cache_key`, dòng67, và `build_junyi_window_cache`, dòng194 | Key lấy phase/encoding/source/target count, builder nhận `WindowInputs` cho phase prediction. Không khóa tên phase thành selection | `calibration_predict`, refit90 encoding, đủ15.847learners/1.621.484targets, chronology và target ranks liên tục. Dựng record bằng iterator nguồn đã ghim |
| `JunyiWindowCacheSession`, dòng322, `write_cpu_admission`, dòng459, `_verify_cpu_admission`, dòng480 | Strict-pass trên CPU rồi GPU nhận receipt SHA và kiểm shard byte | Receipt phải theo validator/source hiện hành. Không tái dùng receipt TRAIN80/selection/refit với phase calibration mới |
| `research_junyi_graph_cache.build_graph_context_cache`, dòng97 | Nhận `WindowInputs` prediction, không yêu cầu `TrainingWindow`. Binding dòng57 ghim phase/encoding/condition/source/window manifest | Dựng riêng theo condition A1/A2/A3 và confidence TRAIN80 đã freeze. Hai format A1 và confidence khác nhau, variant/condition nằm trong digest |
| `GraphContextCache`, dòng178, cùng adapter `set_phase`, dòng105 | Gắn cache có kiểu khi `compact_context=True`. `_collate`, dòng169 chọn cache trước nhánh dựng context động | Phải truyền cache khi set phase. Cache không lưu model probability hoặc được quyền thay checkpoint |
| `research_junyi_selection_cache._binding`, dòng69 | Hiện khóa `view.scope == raw_selection10` | `SelectionCacheSession` không dùng được nguyên trạng cho calibration. Không đổi scope của view để lách guard |

`WindowInputs` prediction trong cache giữ prior responses, geometry và target masks. Loss labels trong shard prediction được đặt sentinel−1 và loader kiểm điều đó. Nguồn là `_parts`, dòng89, `_save_shard`, dòng174, và `_load_shard`, dòng234 của window cache. Cohort calibration hiện có0OOV, nên graph builder chỉ nhận known-item windows phù hợp. Nếu dùng source cóOOV về sau, phải giữ nhánh null/coverage riêng vì graph builder từ chối `UnseenTarget`.

## 2. Finding cache bị reset và bản sửa đang có

Trong source đọc ở đầu review, `export_refit_calibration_predictions` gọi `adapter.set_phase(...)` mà không đưa cache, trong khi `set_phase` gán `_context_cache = context_cache`. Vì giá trị mặc định làNone, cache được caller gắn trước đó sẽ mất và `_collate` quay lại dựng compact context trong GPU function.

Root đã bổ sung optional `context_cache` vào producer. Source hiện tại tại `research_junyi_calibration.py`, dòng281 và dòng298, đã truyền cache qua `set_phase` và từ chối cache khácNone với A0. Đây là bản sửa source đã thấy, chưa là xác nhận regression/CUDA. Cần test cache object giữ nguyên qua producer và làm builder context động fail có chủ ý để chứng minh không rơi về nhánh cũ.

Ngay cả khi giữ graph cache, producer hiện tại còn gọi `iter_predictions_batched` từ `iter_junyi_phase_learners` rồi `export_predictions`. Nếu chạy cả producer trong GPU function, việc đọc/encode cửa sổ, tạo PredictionRecord, kiểm population và ghi Parquet vẫn dùng CPU khi GPU đang được thuê. Bản sửa cache giải quyết một phần đường nóng, chưa tự hoàn thành toàn bộ phân tách CPU/GPU.

## 3. Đường thực thi tối thiểu đề xuất

### CPU chuẩn bị

1. Dùng `inspect_cpu_refit_export` tại `research_junyi_inference.py`, dòng60 để đọc metadata và dựng encoding90/roles/condition theo compact export. Giữ graph/confidence TRAIN80. Đây là metadata trước khi import Torch.
2. Dùng cohort calibration đã chuẩn bị và population receipt để tạo stream `iter_windows(..., training=False, context=100, target_block=100)`. Gọi `build_junyi_window_cache` một lần cho cả A0–A3, rồi strict-admit và ghi receipt trên CPU. `prepare_calibration_population`, dòng226, cung cấp expected population/prefix digest để đối chiếu đầu ra.
3. Dùng các window đã cache để tạo ba graph-context SQLite bằng `build_graph_context_cache`. Một cache cho mỗi condition. Ghim expected_windows từ manifest và expected_targets=1.621.484. CacheA0 không cần graph context.
4. Commit input/cache vào Volume trước chuyển stage. Nguồn/cache và compact model có pin, vùng private/OAuth ngoài snapshot. Source Linux/Gate/runtime phải cùng snapshot đã freeze.

### GPU chỉ chấm số

5. Dùng `inspect_cuda_refit_export`, dòng116 và `build_cuda_refit_predictor`, dòng133. Cấu hình backend/profile CUDA trước dựng model. Kiểm actualGPU, dtype, checkpoint/encoding/condition và giữ optimizer bị chặn bởi phase inference.
6. Gắn đúng phase/cache một lần và chấm `adapter.predict_windows(tuple_batch)`, tối đa128windows. A0 và graph adapter hiện trả array float64 sau native forward, ở `model.py`, dòng109 và `research_junyi_graph_model.py`, dòng240. Ghi nguyên giá trị/dtype, window order/key/length và checkpoint/phase/source pins. Không đổi precision hoặc batch semantics để giảm byte.
7. Xuất shard số nhỏ và completion marker bền vững, commit Volume, dừng GPU ngay sau numeric stage. Hash/đóng gói output lớn và Drive upload thuộc stageCPU. Tránh đưa lại fit_temperature hoặc full Parquet record export vào function này.

### CPU tái dựng, fit và Drive

8. Cầu nối CPU đọc shards số, đối chiếu chính xác window key/order/shape với cache, rồi nối target events theo canonical chronology. Có thể tái dùng `prepare_prediction_windows` và cơ chế `iter_prepared_predictions_batched` tại `prediction_batch.py`, dòng57 và98 qua reader/replay có kiểu. Phải kiểm backend receipt, không giả object thành predictor neural đã attach để lách type guard.
9. Dùng lại `iter_calibration_observations` tại `research_junyi_calibration.py`, dòng247 để kiểm target/key/label/prefix digest, sau đó `export_predictions` với artifact root cloud để tạo raw Parquet chuẩn. CPU fitter nhận raw export có identity `junyi_response_calibration`, population/checkpoint/inference source và `prediction_batch_size=128` đúng producer.
10. Dùng `cloud_calibration_fit.fit_volume_calibration`, dòng42, với typed `CalibrationFitArtifactRoot`. Giữ V1, cùng full calibration partition và expected keys. Commit Volume rồi đưa `publish_request` vào `drive_artifact_sink.publish_from_environment`, dòng231. Đầu ra lớn giữ trên Volume/Drive, PC chỉ nhận metadata/URLs theo yêu cầu cloud-first.

## 4. Cache extension nhỏ nhất

Đề xuất trước hết dùng trực tiếp WindowCacheSession và GraphContextCache, giữ SelectionCacheSession nguyên trạng. Phần mới cần bổ sung là schema artifact xác suất theo window và reader/CPU bridge kiểm pin. Cách này giữ guard phase selection cũ và tránh thêm một bản sidecar đủ labels vào GPU stage.

Nếu root chọn đưa target metadata vào cache để giảm lần scan CPU14MB về sau, hãy tạo wrapper calibration có binding/kind/phase riêng dựa trên sidecar logic hiện có. Giữ tương thích cache selection lịch sử và kiểm join/coverage lại. Không đổi `_binding` thành chấp nhận tùy ý mọi scope.

Path ownership cũng cần được giải quyết bằng layout. Window cache `_owned_root`, dòng54 yêu cầu đường dẫn nằm dưới `PROJECT_ROOT/artifacts/akt/window-cache`, graph cache `_owned`, dòng44 yêu cầu `PROJECT_ROOT/artifacts/akt/graph-context-cache`. Có thể mount Volume đúng các base này hoặc chạy source project trong physical Volume root tương ứng. Symlink/monkeypatch globals để bỏ guard không phải phương án tái dùng hợp lệ. Chỉ cần typed cache root extension nếu layout cloud bắt buộc nằm ngoài các base ấy.

## 5. Những gap ngoài cache cần khép

- Old staged runner tại `experiments/akt/modal_junyi_staged.py`, dòng132 và279 chỉ allowlist selected/refit numerical workers. Cần inference entrypoint/validator riêng thay vì dùng training request cho inference.
- Old runner tại dòng341 từ chối snapshot có `experiments/akt/results`, trong khi minimal input bundle mới chứa compact exports ở thư mục đó. Cần input layout riêng hoặc allowlist model-only rõ ràng của inference controller, không nới thành mount mọi output lịch sử.
- `fit_volume_calibration` yêu cầu canonical/assignment/manifests/raw shards nằm trong typed Volume root. Các path trong PREPARED receipt cần được stage/map nhất quán, giữ content pins. Không dùng pathWindows từ receipt làm đường cloud trực tiếp.
- Cache receipt validator/source thay khi code cache hoặc phase logic thay. Gate trước bản optional-context-cache không tự chứng nhận source mới. Root đang điều phối freeze và LinuxCPUgate, không sửa source trong nhánh review này.
- Full CUDA parity/performance chưa có. Smoke cần chứng minh direct/cached cùng targets/window masks/order, cache giữ qua set_phase, không gọi dynamic graph builder, batch tail, null/OOV nếu source hỗ trợ và output bridge không thiếu/trùng row. A0–A3 cùng frozen inputs, checkpoint riêng và graph condition đúng.

## Ranh giới kết luận

Đây là review source và thiết kế đường thực thi, chưa nghiệm thu rằng numeric bridge hoặc GPU worker đã hoạt động. Không tạo quyền chạy cloud, không xác nhận utilization hoặc thời gian full cohort. Đánh giá dự báo/calibration thật vẫn chờ pipeline được khép và thực thi theo ngân sách đã cấp.
