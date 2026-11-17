# Nối shard xác suất GPU với metadata CPU — 17/11/2026

## Mục tiêu và kết quả

Module `src/knowledge_tracing/akt/research_junyi_numeric_predictions.py` tách đầu ra số của inference khỏi bước dựng record đánh giá. Module và dependency được kiểm trong process mới, không nạp Torch. Đây là kiểm kỹ thuật tổng hợp, chưa có inference CUDA hoặc calibration Junyi thật trong lượt này.

`TESTS02.txt` ghi 80 ca đạt trong 2,22 giây, gồm tests mới và bộ `test_prediction_batch.py` hiện hữu. Kiểm parity đối chiếu toàn bộ trường PredictionRecord, cho cả A0–A3, lịch sử dài, warm-up, timestamp trùng, OOV ở giữa và toàn OOV. Các ca lỗi kiểm shard mất/thừa/đảo thứ tự, sai checkpoint/binding, thay cửa sổ, sai shape/dtype/giá trị, sidecar sai và sửa binary/manifest. `TESTS.txt` là lượt trước khi thêm flush/fsync.

## Hợp đồng API

1. CPU dùng `NumericWindow.from_window(WindowInputs)` để chuẩn bị ID, khóa đầy đủ từ graph cache, độ rộng và số target. Binding chung schema A0–A3 ghim variant, checkpoint ID/SHA, phase, encoding, window manifest và source identity. Khóa cửa sổ bao gồm lịch sử đã được mã hóa, mask và geometry.
2. GPU gọi `write_numeric_shard(root, name, identities, probabilities, binding=..., shard_index=...)`. Root phải là đường dẫn tuyệt đối vật lý, không alias. Tối đa 128 cửa sổ mỗi shard. Mỗi xác suất phải là vector float64, hữu hạn trong [0,1]. API này không nhận đáp án, learner metadata hoặc adapter. NPZ giữ vector số, JSON giữ binding/ID/khóa/shape/count/SHA. Không có nhãn đúng sai trong artifact số.
3. Writer flush/fsync trước công bố từng file. Không ghi đè tên đã tồn tại. Manifest công bố sau binary và là dấu hoàn tất. Nếu lỗi giữa chừng, binary hoặc partial có thể còn để điều tra. Dùng tên run/shard mới để retry. Caller vẫn phải commit Volume sau công bố để có durability cloud.
4. CPU gọi `iter_numeric_prediction_records(adapter, prepared, shards, binding=..., expected_records=..., expected_windows=..., expected_targets=...)`. Adapter ở đây chỉ cung cấp config/encoding/checkpoint, không gọi predict của model. `prepared` lấy từ `prepare_prediction_windows` trên canonical learners hoặc sidecar đã nghiệm thu tương đương. Bridge kiểm các chỉ số target, user/source-row/timestamp/nhãn của sidecar, key cửa sổ, thứ tự shard, SHA và tổng coverage, rồi reuse `iter_prepared_predictions_batched` để dựng record/OOV.
5. Caller phải tiêu thụ iterator đến cuối. Nghiệm thu coverage thực hiện ở cuối, nên consumer ghi artifact tạm và chỉ công bố sau khi iterator hoàn tất. OOV giữ record null chuẩn và không cần numeric vector. `expected_targets` là số target fitted, `expected_records` bao gồm OOV.

## Ranh giới và bước tích hợp còn lại

- Đây là replay artifact có kiểu tường minh, không phải `RefitCalibrationPredictor` và không vượt qua native predictor admission. Producer hiện hữu vẫn cần một entrypoint riêng nhận numeric replay sau khi GPU đã dừng.
- Binding là pin do controller cung cấp. Controller phải đối chiếu với canonical phase/encoding/checkpoint/source/cache manifest đã nghiệm thu trước khi writer được chạy. Checkpoint ID phía CPU được bridge kiểm lại trực tiếp. Module này không tự nạp checkpoint hoặc mở dataset.
- Controller phải pin danh sách shard hoàn chỉnh, tổng counts và manifest SHA từ đầu ra GPU. Không chấp nhận scan thư mục như bằng chứng đủ coverage.
- CPU canonical population/target digest và label-history validation tiếp tục thuộc `iter_calibration_observations`. Iterator record chung không tự chứng minh rằng toàn bộ cohort đúng người hoặc đúng split.
- Chưa đo CUDA parity/throughput, I/O cloud, thời gian export/fit hoặc Drive upload của đường mới. Không chi cloud, không truy cập Holdout, không đọc dữ liệu thật hoặc thay model/hyperparameter.
- Mỗi shard được đọc hữu hạn tối đa128×200 phần tử. Các window/record của toàn cohort không được materialize bởi bridge. CPU caller vẫn cần reader canonical/sidecar streaming.

## Chạy lại kiểm tổng hợp

Trong PowerShell tại root repo, đặt PYTHONPATH tới `D:\Dev\KLTN\src`, dùng `.venv\Scripts\python.exe -B -m pytest tests/akt/test_research_junyi_numeric_predictions.py tests/akt/test_prediction_batch.py -q -p no:cacheprovider` với basetemp mới dưới `artifacts/akt/test-temp/`.

Các source/test/output đã ghim tại `MANIFEST.json`. Không có figure vì lượt này kiểm hợp đồng dữ liệu phần mềm.
