# Rà ranh giới CPU/GPU trước lượt A0 — 17/11/2026

Đã đọc controller `scripts/akt/modal_junyi_calibration.py`, worker `scripts/akt/calibration_cloud_worker.py`, cached numeric core, CPU cache builder, CPU numeric join và V1 fit. Đây là rà source/read-only, chưa gọi cloud hoặc GPU trong lượt này. STAGED02 xác nhận181files/134.460.287bytes được ghim và staging trên Volume. PREFLIGHT02 xác nhận runtime Python3.13.18, Torch2.7.1+cu126, upstream01b7e8d7 và CUDA chưa khởi tạo. Parent environment/request RPC được sửa sau preflight02, cần receipt preflight03 của image mới.

## Ranh giới nghiên cứu đã thấy đúng trong source

- Calibration chỉ dùng15.847learners/1.621.484targets, phase calibration_predict, outerfold4 là ranh giới nghiên cứu đã chốt. DataPaths/poulation/source pins và role identities được kiểm qua CPU preparation. TRAIN80 confidence và encoding90 đi theo SUPPORT của các refit exports; code không tối ưu weights trong stage calibration.
- GPU load_inputs(cuda=True) đọc metadata/checkpoint và cache CPU đã admit, không mở canonical tương tác. NumericBinding ghim checkpoint, phase, encoding, window manifest và inference source. Cached core kiểm graph condition/cache đúng variant, giữ batch128/frozen FP32 recipe, chỉ trả numeric shard.
- CPU join dựng lại target sidecar, đối chiếu fullpopulation/prefix với canonical calibration10 và xuất/audit Parquet. V1 fit chạy sau numeric/raw packaging. Raw publication callback commit/upload trước fit; GPU không giữ container trong lúc CPU fit/upload.
- Raw ZIP và numeric ZIP đều có inventory/member SHA và byte cap2GiB, giải quyết số lượng learner-atomic Parquet lớn. Secret Drive chỉ nằm ở CPU join function. Kết quả lớn giữ trên Volume/Drive, PC nhận receipts nhỏ.
- Resource boundaries được khai báo rõ. GPU function300giây, subprocess270giây, cooperative body240giây, một H100 vàmax_containers1. CPU cache/join16GiB/1core/function3600giây/subprocess3420giây. Stage request và allocation được ghim với workspace và SHA. Tổng30USD vẫn cần ledger/remaining-credit của root trước launch, các trường max_cost_usd không tự đọc hoặc áp hard cap tài khoản Modal.

## Hai khoảng trống vận hành cần xử lý

### P1 — Retry CPU sau failure chưa khép qua controller

`_run` tạo operation directory bằng exist_ok=False. Sau lỗi CPU fit hoặc upload, cùng request/stage không thể chạy lại. Đổi run_id khiến archive_numeric_snapshot từ chối receipt/config GPU cũ vì đường snapshot và request phải trùng. CPU join cũng có raw/fit tranche bất biến.

Điều này ảnh hưởng khả năng tự khôi phục qua controller. Numeric và raw files đã commit vẫn có thể dùng lại, nhưng cần đường CPU resume/finalize rõ ràng. Đề xuất giữ GPU request và snapshot lịch sử, cho CPU replay raw đã hoàn tất, fit tranche mới, operation attempt mới và gọi publisher idempotent trên archive đã tồn tại. Không cần rerun GPU để xử lý một lỗi upload/fit CPU. Đã báo root trước launch.

### P1 — Failure evidence mới commit Volume, chưa tự publish Drive

Nhánh except của _run ghi FAILED.json và commit Volume rồi raise. GPU/cache operation logs và numeric partials chưa có biên nhận Drive tại nhánh này. Publisher của operations hiện chỉ chạy cuối CPU join thành công.

Cần CPU-only finalizer hoặc bước điều phối gọi Drive publisher với config/worker.log/FAILED và result nếu đã có. Drive Secret tiếp tục chỉ cấp CPU. Chưa cần diễn giải partial numeric như kết quả dự báo hoàn chỉnh. Đã báo root trước launch.

### Bước điều phối — Cache receipt trước GPU

CPU-cache thành công hiện chỉ commit Volume. STATE dự kiến publish cache config/receipt trước GPU, nhưng controller chỉ tự publish metadata operation sau CPU join. Root cần gọi CPU Drive publisher riêng sau prepare để hoàn thành bước lưu bằng chứng này.

## Đối chiếu source trước request

Local inference_source_identity là16f97eb396fb0202a1e250ec59d2b3a9cb170070b3f0f8b8575488ad0cf20764. PREFLIGHT02 Linux làd22f6d2e3d6bb4a6c2d7f72da748e55c5c647ce8b41a7ab46b25c82290a4c96c. Đã kiểm khác biệt chỉ ở bytes upstream akt.py. Local SHA BE2788C20CAC602E86EF3A51E5294B37DD7B200F818BE4E173DBD69069A3EC6D có CRLF; Linux SHA ace9e4486ea6d8f8c52310a8ddf27212022136eda719c12d8204fab1bfcfdc67. Thay đúng pin này trong mapping local tính ra chính xác identity Linux của PREFLIGHT02. Request GPU/CPU phải dùng identity của actual preflight03 trên image triển khai.

Worker SHA tại lượt đọc làb97a3053f83a482d6f5e6b18016ecb68c7b112f3cbd851926e5ceac69eb90772, khớp PREFLIGHT02. Controller SHA hiện1b50f18c1714ff795df966c96fe0762be37609491054e38ca1c81b52756d3a01, thay đổi so với preflight02 do parent environment/request RPC. Source kiểm này chưa thay source mô hình.

## Kết luận giới hạn

Chưa thấy lỗi split, target leakage hoặc thay đổi toán học làm mất tính so sánh A0–A3 trong các đường đã đọc. Readiness vận hành còn phụ thuộc preflight03, full CPU cache receipt/counts, stage budget hiện hành và xử lý retry/failure publication ở trên. Tỷ lệ GPU utilization và runtime fullcohort chưa được xác minh bằng lượt A0 này. Telemetry hiện có chủ yếu RSS/VRAM/timings/counts, chưa đủ để khẳng định GPU utilization trên50%.
