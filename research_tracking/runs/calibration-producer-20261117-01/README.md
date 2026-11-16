# Producer calibration Junyi A0–A3 ngày 17/11

## Kết quả engineering đã kiểm

Đã nối được loader snapshot refit, raw prediction export, target/prefix provenance, fit temperature và consumer hiện hữu trên dữ liệu tổng hợp. API tách raw inference/export và fit temperature từ raw artifact trên local CPU. Các checkpoint nghiên cứu A0–A3 đã có không được mở/nạp trong lượt này.

| Lượt cuối | Phạm vi | Kết quả |
|---|---|---|
| `tests07.txt` / XML | Producer/provenance, CPU-only raw fit, reader Parquet và native A0/A1/A2/A3 | **29 passed, 22,96 giây** |

Lượt07 chạy cả 25 ca provenance/producer và 4 ca native trong cùng process sau khi source được freeze. Các lượt 03/05 trước đó có 4 ca native skip khi thiếu RAM. Lượt04/06 sau đó đạt riêng 4 ca native. Mọi log cũ được giữ nguyên.

Fixture native dùng `d_model=16`, snapshot khoảng 77–79 KB, không có bước training. CUDA admission được mock và CUDA detection trả false. Nguồn AKT upstream vẫn được loader kiểm Git commit/hash theo cơ chế hiện hữu. Trước ca native đầu ở lượt 07 có khoảng 4.34GB RAM khả dụng. Working-set peak qua cảprocess khoảng 369.5 MB, gồm import dependency và các kiểm pure/native. `NATIVE_RESOURCES07.json` giữ sốđo hiện hành; các file resource04/06 giữ lịch sử. Đó là footprint toy, chưa đại diện calibration Junyi đầyđủ.

## Các API đã có

Nguồn tại `src/knowledge_tracing/akt/research_junyi_calibration.py`.

1. `attach_refit_export` nhận adapter và encoding90 do caller dựng, kiểm pin `MODEL_INDEX.json`, checkpoint và từng member trong `SUPPORT.zip`, đối chiếu final-refit lifecycle, role/vocab, variant và training fields. Tái dùng `load_training_snapshot`, rồi strict-load model weights. Optimizer và RNG trong snapshot giữ nguyên trên đĩa, không được restore vào process inference.
2. `prepare_calibration_population` tạo manifest nhỏ từ learner calibration qua reader hiện hữu, độc lập với predictor. Source metadata và role view có pin. Manifest giữ target count, digest identity rows và digest exact keys với full observed prehistory.
3. `export_refit_calibration_predictions` kiểm frozen predictor rồi dùng `iter_predictions` hoặc `iter_predictions_batched` và exporter Parquet cũ. Callback cuối stream kiểm lại source/model boundary trước khi exporter đánh dấu complete. Batching là tham số tường minh. Đây là primitive inference/export, chưa là launcher GPU tối ưu cho full cohort.
4. `fit_response_temperature_from_raw_export` đọc raw Parquet đã có trên local CPU, kiểm manifest và từng shard hash, đối chiếu lại target/prefix population rồi gọi `fit_temperature` cũ. API này không nhận adapter/GPU. Vì vậy run GPU có thể kết thúc sau khi xuất artifact, phần fit T được chạy bằng process CPU sau khi tải raw artifact về D.
5. `fit_refit_response_calibration` là convenience local/toy nối hai bước trên. Nó không phải Modal entrypoint. Output gồm `raw/` và `fit/temperature.json`, `fit/manifest.json`. Calibrator trả về dùng trực tiếp được với `iter_calibrated_predictions`.

Public rawexport yêu cầu output mới để tránh reuse metadata-complete của exporter cũ mà chưa đọc/kiểm lại probability artifact. Đường reuse raw đã có là API CPU-only với manifest/shard pins độclập. Caller giữ grant, current-source Gate/runtime và việc xác minh canonical dataset/assignments của run. Các API này không tự cấp authority, chọn model/winner, thay đổi split, epoch hoặc hyperparameter.

## Hợp đồng target và history

Mọi event được dự đoán một lần theo stream hiện hữu, bao gồm target đầu lịch sử và OOV. OOV tiếp tục có probability null cùng lý do unsupported, không trở thành fitted prediction. Identity được đối chiếu đủ `source_row, user_id, exercise, time_done, correct, suggested, fold` với stream event độc lập trước khi đưa vào `CalibrationTarget`.

`CalibrationTarget.event_id` dùng source-row ID thật của event. `history_sha256` là hash-chain của **full observed prehistory**, cập nhật sau khi xuất key của target hiện tại. Nó không lấy `window_id` làm history hash. Chỉ event quá khứ gồm response đã quan sát đi vào chain. Native window ID, `history_available`, `history_used`, `context_reset` và score mask tiếp tục theo `iter_predictions`; full prefix là provenance, còn effective window là phần thực sự dùng để dự báo.

Hồi quy đã kiểm đổi current/future response không đổi prefix target hiện tại, đổi response quá khứ làm prefix sau đó đổi, OOV/reset và overlap tại các rank99/100/199 giữ đủ 410 target riêng biệt. Missing/extra/order/label/item/checkpoint hoặc source-population mismatch đều bị từ chối.

Training identity từ snapshot được lưu nguyên trong predictor receipt, bên cạnh inference-source identity riêng. Boundary còn kiểm graph/confidence condition, inference config/graph-enabled state và seal parameter/buffer theo tên, object ID, version, shape, dtype, device. Các ca thay graph condition, thêm/thay/in-place-update buffer bị chặn trước prediction. Seal này thuộc process đang attach và hành vi mutation thông thường của PyTorch, không phải cơ chế chống sửa bộ nhớ có chủ đích.

## RAM và phân tách CPU/GPU

`fit_temperature` hiện materialize targets, keys, sorted rows và logits. Producer giữ `max_targets` và `max_learner_events` tường minh, cùng heuristic 4 KiB/target so với RAM khả dụng trước fit. Đây là estimate bảo thủ chưa đo cho full Junyi, không phải điều kiện phương pháp học thuật hoặc kết luận cần một mức RAM cố định. Cần benchmark footprint calibration thực để điều chỉnh estimate/implementation hợp lý trước lượt đầy đủ.

Reader Parquet cho CPU fit giới hạn DuckDB128 MB và fetch2.000 record mỗi lần. `temp_directory=''` tắt spill ra CWD. Shard vượt khả năng sort128 MB sẽ dừng với lỗi RAM, cần chuẩn bị shard nhỏ hơn hoặc bổ sung temp directory đúng vùng chuẩn ở lượt engineering sau. Exporter hiện hữu mặc định50.000row/shard. Phần fit T vẫn materialize, nên streaming reader chưa làm toàn bộ fitter thành constant-memory. Các synthetic test xuất artifact nhỏ theo basetemp, không tạo lại cache/cohort/checkpoint nghiên cứu.

## Điều kiện trước lượt dữ liệu thật

- Dựng adapter/encoding90/graph-confidence80 từ bundle refit đúng pin và config. Loader API đã có, builder/entrypoint hoàn chỉnh từ export folder vẫn cần nối.
- Chuẩn bị source calibration10 riêng và population manifest độc lập. Cache train/selection/refit90 đã có không chứa calibration labels. Pin metadata trong producer chưa thay việc xác minh byte của canonical source theo pipeline run.
- Khóa binding domain/bank/reference của Junyi bằng metadata đúng nghĩa logged exercises. Đây là response calibration, không phải latent-mastery calibration hoặc Grade10 reference-bank score.
- Đóng request/Gate/runtime/authority cho inference thật. Ghi rõ prediction batch size và chuẩn bị CPU window/context phù hợp nếu dùng GPU, đo full-cohort throughput và artifact transfer.
- Sau raw export, giữ manifest/shard SHA từ gói transfer. Trả GPU, rồi gọi API CPU-only fit trên D. Nghiệm thu cả raw/calibrated coverage và đánh giá độc lập theo role/family đã chốt.

Chưa có full Junyi calibration, outer prediction hoặc kết quả RQ mới từ gói này. Bốn snapshot native trong test chỉ là dữ liệu tổng hợp dùng kiểm phần mềm.

## Bằng chứng và kiểm lại

`COMMANDS.json` giữ lệnh test và env per-process. `MANIFEST.json` ghim source, tests, logs và resource receipts. `ACCEPTANCE.json` là trạng thái gói. Các log cũ giữ nguyên whitespace. `tests01/02` phản ánh các bản trước refactor CPU-only; `tests07` là kết quả cuối cho source producer hiện hành. Không sửa Git global hoặc cài dependency global trong lượt này.
