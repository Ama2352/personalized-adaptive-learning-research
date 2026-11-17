# Core inference số từ cache CPU — 17/11/2026

## Kết quả kiểm kỹ thuật

Module mới `src/knowledge_tracing/akt/research_junyi_cached_numeric.py` giữ hot loop đọc cache đã chuẩn bị, chấm xác suất và ghi numeric shard. Bộ kiểm dùng fake predictor/cache, `PredictionBinding` thật và dữ liệu tổng hợp. Không gọi CUDA/cloud hoặc đọc dữ liệu Junyi thật. Source model, cấu hình và pipeline cũ không bị sửa.

`TESTS04.txt` ghi kết quả cuối. Các kiểm gồm parity toàn trường sau numeric replay cho A0–A3, nhiều cửa sổ, OOV giữa chuỗi và toàn OOV, giữ graph cache khi đổi phase, từ chối source/roles/model/coverage sai, cap RAM/VRAM/wall và root đã tồn tại. Cùng chạy bộ numeric bridge và prediction_batch hiện hữu. Kiểm này chưa chứng minh tốc độ hoặc parity CUDA thực tế.

## API và hợp đồng

- `CachedNumericBudget` khai báo cap thời gian, RSS, VRAM, exact số cache record, cửa sổ, target, OOV và batch tối đa128. Batch không vượt cấu hình model đóng băng.
- `run_cached_numeric` là core cho kiểm tổng hợp và orchestration, nhận predictor/cache đã nghiệm thu cùng callback telemetry. Core tự kiểm bindings và counts nhưng không phải cổng admission native CUDA.
- `run_cuda_cached_numeric` là entrypoint production. Caller phải cấu hình CUDA trước. Wrapper yêu cầu `ResearchCUDAExecutionProfile`, `JunyiWindowCacheSession` có CPU admission và `GraphContextCache` thật nếu graph variant. Sau kiểm backend thực, reuse `build_cuda_refit_predictor`, không fallback CPU. Profile/cap VRAM phải khớp.
- `dataset_sha256` là population.identity. `source_data_sha256` lấy từ cache, là SHA canonical input. `roles_sha256` là roles.identity. Hai loại danh tính dữ liệu được giữ riêng. Predictor domain binding của entrypoint này dùng canonical SHA.
- Với A1–A3, phase phải khớp variant/encoding/view; graph cache phải khớp population và window manifest. Adapter nhận cache qua `set_phase(..., context_cache=...)`. Không xây context/confidence trong hot loop.
- Core chỉ chấp nhận `WindowInputs` hoặc `UnseenTarget`, từ chối TrainingWindow. OOV không gọi model. Kết quả float64 qua writer không nhãn của numeric bridge, giữ thứ tự cửa sổ và ghim checkpoint/source/cache.
- Artifact `RECEIPT.json` chỉ công bố sau full coverage và kiểm boundary cuối. Chưa có receipt thì run chưa nghiệm thu dù một số shard tồn tại. Root output phải mới, retry dùng run ID mới. Không tải output về PC.

## Receipt cho CPU hậu xử lý

Kind `JUNYI_CACHED_NUMERIC_INFERENCE_V1`, status `COMPLETE`. Fields gồm binding, roles_sha256, dataset_sha256, source_data_sha256, window_admission_sha256, graph_cache_identity, shards (manifest_path/manifest_sha256), counts, wall_seconds, timings, telemetry và resource_caps.

Counts giữ `records` là số record cache, `windows` là số cửa sổ chấm, `targets` là toàn bộ interaction gồm OOV, `fitted_targets` và `oov_targets`. CPU numeric replay dùng expected_records=counts.targets, expected_windows=counts.windows, expected_targets=counts.fitted_targets. Canonical sidecar/population phải được kiểm độc lập ở CPU join.

Timings giữ setup_seconds (wrapper admission/load), inference_seconds (forward và đồng bộ/kiểm tài nguyên sau batch), numeric_publish_seconds, core_seconds. wall_seconds gồm setup+core. volume_commit_seconds để null vì caller thực hiện và đo commit ngoài hàm. Caller commit Volume rồi trả container GPU, CPU mới export record/fit/Drive upload. Controller cần ghim receipt SHA và danh sách shard, không dùng directory scan làm nghiệm thu.

## Giới hạn và phần CPU host còn lại

Builder hiện hữu xác minh SUPPORT.zip một lần khi nạp model. GraphContextCache vẫn đọc SQLite theo khóa và copy context sang tensor. Cache NPZ read/decode, collate, copy, kiểm integrity, telemetry và ghi shard vẫn dùng CPU host. Đợt này loại preprocessing, canonical label join, context build, confidence fit, raw Parquet export, temperature fit và upload ra khỏi GPU hot loop. Chưa có cơ sở tuyên bố GPU không phải chờ CPU.

Resource caps kiểm cooperative trước/sau batch. Một forward hoặc loader bị treo không bị ngắt tức thời bởi core. Modal timeout/watchdog bên ngoài và giới hạn ngân sách vẫn bắt buộc. RAM snapshot production dùng RSS/peak nếu OS cung cấp, VRAM dùng peak reserved allocator, chưa đo nvidia-smi utilization hoặc phần memory ngoài allocator. Hàm không tự reset allocator peaks.

GPU session construction từ CPU admission và GraphContextCache.open vẫn do caller thực hiện trước wrapper. Controller cần đo phần setup đó riêng nếu nó xảy ra trong container GPU. Kết quả thời gian tổng trả phí phải bao gồm cả image/startup và Volume commit, không chỉ timings của hàm.

## Tái kiểm

Dùng `.venv` với PYTHONPATH trỏ `src`, chạy ba file tests `test_research_junyi_cached_numeric.py`, `test_research_junyi_numeric_predictions.py`, `test_prediction_batch.py` dưới `tests/akt/`. Log và SHA source/tests được giữ trong bundle này. Không commit hoặc gọi cloud trong nhánh triển khai này.
