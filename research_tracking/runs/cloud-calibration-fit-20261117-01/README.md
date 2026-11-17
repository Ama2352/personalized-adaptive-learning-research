# CPU fit calibration trên cloud Volume — 17/11/2026

## Mục đích

Nối raw prediction đã pin trên Volume với fitter temperature V1 để GPU được trả trước bước CPU. Helper `src/knowledge_tracing/akt/cloud_calibration_fit.py` không tạo tài nguyên cloud và không thực hiện upload. Worker điều phối gọi helper rồi commit Volume, sau đó dùng publish_request cho Drive CPU worker.

## API và dữ liệu

`fit_volume_calibration(raw, paths, view, ..., artifact_root, run_id, tranche_id)` nhận raw manifest/shard SHA, binding của checkpoint, population/prefix đã chuẩn bị và metadata nguồn. Chỉ nhận full calibration10, đúng roles/phase/encoding và manifest xác nhận train/selection/outer/Holdout không được đưa vào nguồn này. Raw và bốn DataPaths phải là file vật lý dưới mount `/artifacts`.

`CalibrationFitArtifactRoot(Path('/artifacts').resolve(strict=True))` là chính sách output tường minh. Modal có thể gắn `/artifacts` qua symlink. Chỉ mount tin cậy này được resolve một lần sang physical root, sau đó caller phải dùng physical root; mọi alias dưới root bị từ chối. `fit_response_temperature_from_raw_export` nhận thêm artifact_root tùy chọn. Nhánh local mặc định vẫn có kiểm vùng sở hữu trước đây. Root cloud yêu cầu mount tồn tại, output mới thuộc mount, không symlink/junction hoặc thoát path. Thuật toán và tham số temperature V1 được giữ.

Output nằm ở `/artifacts/<run_id>/<tranche_id>/payloads/`, gồm config.json, fit/temperature.json, fit/manifest.json, resource.json và COMPLETE.json. COMPLETE giữ SHA/size của các file trước nó. publish_request liệt kê đúng năm file cùng tổng byte. Khi fit lỗi, FAILED.json giữ loại lỗi và thời gian, không ghi COMPLETE. Retry cần tranche mới hoặc điều phối resume được duyệt, tránh ghi đè artifact đã có.

Caller phải commit Volume bền vững trước publish. Sink Drive tiếp tục upload/resume và kiểm SHA server. Repo local chỉ giữ biên nhận nhỏ và URI sau khi chạy thực.

## Kiểm chứng và giới hạn

Tests dùng Parquet/tương tác tổng hợp, OOV và prefix thật của producer. So sánh payload temperature với đường V1 hiện hữu sau chuẩn hóa JSON, kiểm sai root/source/split/raw pin, output đã tồn tại và import helper không nạp Torch. Log lần đầu giữ failure ở assertion do tuple V1 trở thành list trong JSON; đã sửa assertion chuẩn hóa hai vế.

Lượt cuối tests02 đạt33ca vàskip1ca trong23,25giây. Ca skip là tạo symlink directory do quyền hệ điều hành Windows; test vẫn có trong suite cho Linux. Kiểm raw Parquet cloud root, CPU fit và payload V1 parity đã chạy thực bằng dữ liệu tổng hợp.

Không chạy dữ liệu Junyi thật, Modal, GPU hoặc upload trong gói này. Helper chưa là worker Modal triển khai. Worker CPU thực cần budget/timeout và commit/upload do nhánh điều phối cấp.

Heuristic RAM của producer vẫn là4096byte/target và chỉ cho estimate không vượt60% RAM khả dụng. Với1.621.484targets, điều kiện hiện tại đòi ít nhất khoảng10,31GiB khả dụng. Worker12–16GiB phù hợp hơn với guard hiện hành. Đây là ước lượng kỹ thuật bảo thủ, benchmark100k targets của nhánh calibration-memory đã đo footprint thấp hơn; chưa đo full cohort.
