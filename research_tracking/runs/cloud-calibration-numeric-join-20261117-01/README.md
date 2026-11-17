# Nối numeric GPU sang raw calibration và V1 fit trên CPU — 17/11/2026

## Kết quả đã kiểm

`src/knowledge_tracing/akt/cloud_calibration_numeric_join.py` nối snapshot numeric đã đóng với calibration source. Lượt tests02 đạt13/13 trong35,66giây. Sau khi thêm on_raw_ready, tests03 xác minh hai trường hợp callback trước fitter và callback lỗi chặn fit, đạt2/2 trong4,46giây. Bốn trường hợp A0–A3 dùng probabilities tổng hợp, cửa sổ và prefix từ producer thật, có OOV. Raw Parquet giữ20targets,18fitted và2OOV, payload temperature khớp chính xác đường V1 hiện hành sau chuẩn hóa JSON. Lượt tests01 trước đó giữ12ca đạt trước bổ sung kiểm domain canonical.

Gói xác minh phần mềm bằng dữ liệu tổng hợp. Chưa chạy inference/calibration Junyi thật hoặc GPU. Tests không nạp weights. Một subprocess kiểm import module không nạp Torch.

## Hợp đồng API

`join_numeric_calibration_snapshot` nhận data paths calibration10, view, research encoding90, PredictionBinding frozen refit và NumericBinding của GPU. Đầu vào khác gồm GPU receipt đã pin SHA, window manifest, admission receipt đã pin, population/prefix identity, source pins, graph cache identity và hai tranche output riêng. Caller cung cấp physical mount bằng `CalibrationFitArtifactRoot(Path('/artifacts').resolve(strict=True))`.

GPU receipt dùng schema `JUNYI_CACHED_NUMERIC_INFERENCE_V1`, status COMPLETE. Role SHA là roles.identity. source_data_sha256 là canonical.parquet SHA, dataset_sha256 là population.identity. NumericBinding.source_sha256 khớp model_source_sha256 trong PredictionBinding. checkpoint_id là SHA checkpoint refit, phase và encoding khớp calibration/encoding90, domain trong PredictionBinding là canonical SHA. Graph cache identity được đối chiếu riêng theo snapshot đã được CPU chuẩn bị.

Window manifest/admission phải khớp key của window_cache_key, context100, target_block100, max_length200, source canonical và population counts. Mọi shard manifest phải có SHA nằm trong receipt GPU. Iterator numeric kiểm thêm payload hashes, thứ tự cửa sổ và coverage khi tiêu thụ đến cuối.

## Quy trình CPU

1. Kiểm ranh giới full calibration10, manifest chỉ chứa calibration, các source/split pins và binding của refit. Kiểm loại trừ train, selection, outer và Holdout trước khi đọc events.
2. Tạo sidecar bằng prepare_prediction_windows trên canonical reader hiện hành. Adapter replay chỉ chứa config/encoding/checkpoint, không có native model.
3. iter_numeric_prediction_records nối xác suất với cửa sổ CPU. iter_calibration_observations kiểm target identity, thứ tự, OOV, full prehistory prefix và population digest.
4. export_predictions xuất Parquet và audit đủ canonical targets. Kiểm lại source/GPU receipt/window metadata sau iterator hoàn tất.
5. Gom raw manifest và các shard đã audit thành RAW_EXPORT.zip ngay trên Volume bằng ZIP_STORED. INVENTORY.json trong ZIP giữ member sizes/SHA. Byte cap mặc định2GiB. Raw Parquet tiếp tục nằm trên Volume cho fitter.
6. Nếu caller cấp on_raw_ready(raw_publish_request), callback chạy ngay sau raw completion để commit Volume hoặc publish CPU trước fitter. Callback lỗi sẽ chặn fit và giữ raw artifacts hoàn chỉnh.
7. fit_volume_calibration đọc raw export đã pin và chạy V1 CPU riêng. Trả raw và fit publish requests cho Drive CPU worker.

## Artifacts và vận hành

Raw tranche chứa config.json, raw/manifest.json và các Parquet, RAW_EXPORT.zip, COMPLETE.json. Publish chỉ ba file config/ZIP/completion để phù hợp giới hạn256file/tranche của sink. Export lịch sử là learner-atomic nên full calibration15.847learners có thể tạo ít nhất15.847Parquet; đóng gói được thực hiện trên CPU cloud, không tải chúng về local.

Fit tranche dùng contract hiện hành gồm config, temperature, manifest, resource và completion. Caller dùng on_raw_ready để commit raw Volume trước fit, sau đó commit fit output và chuyển publish requests cho Drive worker. Artifact hoàn chỉnh và raw Parquet giữ nguyên khi fit chưa xong, phục vụ bước phục hồi. Thất bại trước completion phải giữ output chưa hoàn chỉnh và dùng tranche mới khi retry.

Hai vòng prefix validation CPU cần được dự toán riêng. Lượt prepare full population trước đó đã đo khoảng230giây. V1 default có tối đa200objective evaluations, benchmark4evaluations chưa đủ để xác định runtime full fit. Guard RAM hiện hành cho full1.621.484targets cần khoảng10,31GiB khả dụng; worker12–16GiB và wall cap phù hợp cần do điều phối cấp. Các bước này diễn ra sau khi GPU đã trả.
