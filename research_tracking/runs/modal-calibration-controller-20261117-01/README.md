# Function calibration tách CPU/GPU — 17/11/2026

## Phạm vi và bằng chứng

Chỉ viết source và chạy kiểm nhỏ local. Không tạo App/Volume, không dựng image, không gọi GPU/cloud, không đọc dữ liệu Junyi thật. `TESTS05.txt` ghi 22 ca đạt trong 2,78 giây. Các kiểm dùng Modal giả để xác nhận GPU function không có Drive Secret, chỉ một H100, timeout300, retries0, single-use; CPU join16GiB/1core/timeout3600 và Secret riêng. Có kiểm request/authorization, input mutation, pilot/full guard, CUDA metadata loader không mở canonical data và archive numeric với262file. Chưa nghiệm thu image/runtime cloud thực của wrapper mới.

Đã đọc SDK Modal1.6.3 tại `_utils/function_utils.py`269–275 và `app.py`962 để kiểm yêu cầu nested function. Test thực FunctionSourceInfo xác nhận nested mặc định bị từ chối và serialized=True tạo bytes thành công, không RPC. Decorator dùng serialized=True. Function nhập controller từ `/opt/kltn/scripts/akt` sau khi thiết lập sys.path; ROOT trên Linux cố định `/opt/kltn`, tránh phụ thuộc vị trí module auto-mount.

Source gồm `scripts/akt/modal_junyi_calibration.py`, `scripts/akt/calibration_cloud_worker.py`; tests tại `tests/akt/test_modal_junyi_calibration.py`. Không thay KT source đã đóng.

## Đường thực thi

1. Root CPU stage riêng giải nén và kiểm bundle allowlist, giữ relative paths. Controller này không giải nén input ZIP. Data/model/population/request đã pin nằm trên Volume `kltn-junyi-calibration-artifacts-v1`. Dùng root vật lý từ `/artifacts`. Không đưa token vào request.
2. `create_app()` trả `(app, functions)` với keys `prepare`, `predict`, `join_fit`. Chỉ định nghĩa resource, không gọi `.remote`. Root dùng context app và gọi từng function sau budget admission thực. Chạy file trực tiếp với `--request ... --stage ...` chỉ kiểm schema local.
3. `prepare(request_entry, worker_sha256, authorization)` chạy CPU helper bốn export, cùng calibration/refit90, cache window chung và graphcache riêng. CPU cache commit trước GPU. Request của stage này trỏ đường dự kiến của CACHE_RECEIPT; SHA thực chỉ có sau prepare và được pin trong request GPU mới.
4. `predict(request_entry, worker_sha256, authorization)` dùng một H100,2CPU,8GiB host, timeout300; child tối đa270s, numeric budget tối đa240s. Không có Drive Secret. GPU loader chỉ kiểm MODEL_INDEX/population metadata/cache, không mở canonical Parquet. Kiểm source identity trước CUDA model load, gọi configure_cuda theo recipe FP32/batch128, native CUDA admission, chấm full cache và commit. Trả receipt path/SHA nhỏ, không tải binary về PC. Function single-use trả GPU khi xong.
5. `join_fit(request_entry, worker_sha256, authorization, gpu_result_entry)` dùng CPU16GiB/1core, timeout3600, child3420. GPU result entry pin file result.json của stage GPU, trong đó có receipt path/SHA. CPU xác minh source/graph/cache/population, join toàn bộ records; callback đóng numeric snapshot thành ZIP_STORED trên CPU rồi commit/upload numeric archive + raw trước fit V1. Numeric archive luôn xuất ba file config.json,NUMERIC.zip,COMPLETE.json, giữ inventory/SHA bên trong ZIP và completion, giới hạn2GiB. Regression262file nguồn được gói thành263member gồm inventory và upload chỉ ba file, tránh trần256file/tranche của sink. Giữ nguyên numeric shards/receipt trên Volume. Fit xong commit/upload temperature, sau đó upload operation config/log/result/completion. Không import Torch trong CPU entrypoints.

## Request và allocation

Request có kind `JUNYI_CLOUD_CALIBRATION_REQUEST_V1`, workspace `honguyenminhsang2016`, mode `full` hoặc `pilot`, run_id, variant A0–A3, exports map bốn MODEL_INDEX `{path,sha256}`, data_paths bốn file canonical/assignments/manifests có pin, population file pin, source_pins, cache_receipt pin, numeric_budget, cpu_budget, gpu_output, full_cohort_approved, max_cost_usd, source_identity. GPU output phải là `<run_id>/<variant-lower>-numeric/payloads`.

`numeric_budget` theo `CachedNumericBudget`, `cpu_budget` theo `JunyiCPUInferenceBudget`. Window cache counts phải lấy từ receipt CPU thực; không dự đoán số cửa sổ để điền. Các paths phải là absolute physical paths dưới Volume. source_identity bằng inference_source_identity của KT source/upstream/protocol hiện hành.

`authorization` có đúng workspace,stage,allocation_id,reserved_usd,request_sha256. Đây là bằng chứng cooperative từ root budget controller, không phải hệ thống tự duyệt. Root phải đối chiếu provider workspace/billing và ledger toàn KLTN, ghi reservation trước remote call. Request không được vượt allocation. Không tự suy free credits từ billed0. Lượt A0 full calibration inference đã được root quyết định với trần0,40USD và1H100/300s; A1–A3 chờ nghiệm thu A0 và số đo thực.

Mode full bắt buộc full_cohort_approved=true. Đây là inference calibration, không phải training/CV hoặc chọn epoch. Mode pilot chỉ nhận cache riêng tối đa4096targets/64windows, không được cắt stream từ full cache. Helper CPU prepare hiện giữ full calibration, nên pilot muốn dùng cần recipe chuẩn bị riêng đã review; CPU join/fit từ pilot bị chặn. Không tự đổi sang pilot khi full gặp lỗi.

## Image và artifact

Image từ `im-FLsPV1Te1DGul7RBdUy5HH` đã có biên nhận runtime cũ Python3.13.18/Torch2.7.1+cu126 tại `junyi-refit-pipeline-20261114-01/workspace2016-runtime01.json`. Layer build mới cài git rõ ràng, loại src/artifacts/results cũ trong image, copy current src, Protocol21/Recipe26, các wrapper/helper allowlist; git init/fetch depth1 và checkout upstream commit01b7e8d7d7c862cabc9467108e3e7f2555653a88. Image build dùng pip trong `.venv` của image cho Modal1.6.3/requests2.34.2/google-auth2.62.1. Không cài local/global. Root cần Linux runtime gate lại sau khi image build.

Input source ZIP còn giữ để audit, source image phải khớp source identity đã pin. Worker script SHA được đối chiếu trước subprocess. Không upload `dataset/`, credentials hoặc các thư mục local artifacts vào image mới. Model/data chỉ đọc từ Volume đã stage.

GPU vẫn cần CPU host đọc cache/collate/copy tensor/verify model. Không tuyên bố zero CPU wait. Numeric receipt có setup/inference/publish timings và peak memory; worker result thêm tổng worker/Volume commit. Image startup và cache/session open trước core phải được tính vào function billing và worker duration. Utilization thực chưa được đo trong lượt code này.

## Failure và recovery

Request/worker/schema sai dừng trước numerical loop. Runtime/model/finite-probability/cache/caps sai dừng function, không fallback CPU hoặc auto-retry. Operation giữ `FAILED.json` cùng log trên Volume. Không có COMPLETE/receipt thì chưa nghiệm thu. Root archive failure qua CPU publisher sau khi GPU dừng.

Nếu upload hoặc CPU fit lỗi sau raw đã xuất, raw/numeric vẫn nằm trên Volume và raw callback có thể đã lưu Drive. Root dùng fit_volume_calibration riêng từ raw đã pin để phục hồi, không chạy GPU lại hoặc cố ghi đè run/tranche cũ. Wrapper gói này chưa có state machine tự retry/reuse output. Drive-primary yêu cầu root kiểm biên nhận publish, không chỉ trạng thái STAGE_COMMITTED.

Root cần hoàn tất input stage, cache receipt/source pins, reservation và Linux integration gate trước launch. Module này không tự thực hiện các bước đó.
