# Nối model refit Junyi vào calibration — 17/11/2026

## Mục tiêu và kết quả

Builder `src/knowledge_tracing/akt/research_junyi_inference.py` đọc MODEL_INDEX và SUPPORT của bốn export refit nghiên cứu đang giữ trên D. Builder tái sử dụng parser encoding, binding confidence, loader checkpoint và producer calibration hiện hành. Metadata bao gồm roles, encoding90, encoding80, graph expert và confidence học trên TRAIN80. Các identity được kiểm trước khi nạp weights.

Phase `junyi-inference` cho phép CPU với kiến trúc và training fields đã đóng băng. Các entrypoint optimizer, fit và collate training từ chối phase này. Quy tắc research training CUDA hiện hành vẫn giữ. Training-source identity của checkpoint được giữ riêng với source identity của inference hiện tại.

`METADATA_INSPECTION.json` ghi kết quả CLI metadata của bốn export. `tests01.txt/xml` giữ 57 ca đạt và một ca skip do RAM tại thời điểm import Torch. Bốn ca native model nhỏ của producer trong lượt này đạt. `tests02.txt/xml` giữ 20 ca pure đạt, gồm từ chối local full export/fit ngay trước nạp model hoặc tạo output. Lượt cuối tests03.txt/xml đạt21/21 trong27,27 giây, gồm optimizer entrypoints thật từ chối phase inference-only. Các ca tổng hợp này xác minh phần mềm và ranh giới thông tin.

Chưa chạy calibration thật 1.621.484 tương tác. Chưa có temperature, prediction calibration nghiên cứu hoặc đánh giá outer mới từ gói này. PROBE_STATUS.json giữ hai lượt weights thật A0/A1 đạt, hai lượt dừng trước Torch do RAM (A1 cũ và A2), A3 chưa chạy sau khi A2 bị chặn. A0 xử lý26,41 giây, peak313,66MiB; A1 xử lý62,47 giây, peak326,85MiB. Mỗi lượt110 tương tác tổng hợp/hai cửa sổ. Startup headroom là ước lượng kỹ thuật, được hạ sau khi đo A0, guard RSS640MiB/reserve128MiB vẫn giữ. Không tiếp tục hạ floor sau A2. Các request probe đã pin metadata, chỉ đọc checkpoint hiện hữu, không training.

## Entrypoint

Dùng `.venv/Scripts/python.exe -B scripts/akt/run_junyi_calibration.py --request <probe-aN.json>` để kiểm metadata. Thêm `--run --request-sha256 <SHA của request>` mới cho chạy probe nhỏ. Request chỉ cho một learner tổng hợp, tối đa128 targets, tối đa hai cửa sổ, CPU một thread, 180 giây, có watchdog process con và RAM. Checkpoint nghiên cứu được đọc tại chỗ, không nhân bản.

Theo yêu cầu mới, local CLI chặn full `export` và `fit`. Dry-run có thể đối chiếu PREPARED/POPULATION input nhưng không tạo predictions lớn. Không dùng CLI này làm worker GPU.

## Hợp đồng lưu trữ cloud-first cho bước kế tiếp

1. CPU chuẩn bị input nhỏ đã pin gồm canonical calibration-only14MB, assignments, manifest, split manifest frozen, roles, encoding90, PREPARED và POPULATION. Confidence/graph/encoding80 từ SUPPORT giữ đúng training provenance.
2. Worker inference có purpose riêng nhận source/package/input identities cùng URI cloud scratch. Kích thước batch prediction khai báo riêng, training fields của checkpoint giữ nguyên. Admission CUDA hiện hành phải được tái sử dụng. Worker refit90 cũ không được đổi purpose để chạy calibration.
3. GPU worker chỉ nạp model, thực hiện inference đã chuẩn bị và ghi raw output/checkpoint tiến độ vào cloud Volume hoặc durable scratch. Sau tranche phải commit durable manifest trước trả URI. Lưu shard IDs, target range, checkpoint SHA, RNG khi cần, số dòng, coverage và byte hashes để retry không trùng target. GPU phải trả trước phần fit nhiệt độ, báo cáo hoặc upload CPU.
4. Worker CPU đọc raw manifest/shard đã pin, xác minh target/prefix/coverage bằng `iter_pinned_prediction_export` và `fit_response_temperature_from_raw_export`. Prefix full-history tốn khoảng230 giây cho1,62M targets ở lượt chuẩn bị input đã nghiệm thu, nên khâu này phải nằm ngoài thời gian thuê GPU. Fitter V1 materialize nhiều bản target/key/logit. Nhánh calibration-memory-20261117-01 đã đo synthetic25k/50k/100k; cần cloud CPU8–12GiB cho full1,62M targets theo dự toán, chưa phải footprint đo full. Giữ V1 để tránh đổi thuật toán.
5. Sink Drive nhận artifact từ cloud scratch, lưu resumable session state bền vững, đối chiếu size/SHA phía server và publish remote receipt. Local repo chỉ nhận URI, SHA, summary và chỉ mục nhỏ. Thất bại upload giữ cloud artifact và remote progress để tiếp tục; không download checkpoint/prediction lớn về D. Credentials chỉ qua secret/runtime riêng, không nằm trong source package.
6. Tối thiểu output phải có raw prediction shards, target/prefix population pin, model/binding, config, source identities, counts/coverage/OOV/warmup, resource log, durable completion marker và Drive receipt. Fit CPU bổ sung temperature, objective/config, population và source binding, convergence/boundary status. Các công đoạn thực chỉ hoàn tất khi artifact được kiểm, không chỉ dựa exit code.

## Giới hạn

Probe weights thật sử dụng đáp án tổng hợp, chỉ xác nhận nạp model và chạy CPU đúng wiring. Nó không tạo bằng chứng dự báo hay kết luận RQ3. Không chạy GPU, cloud, Holdout hoặc train trong gói này. Input staging14MB đã có trước ràng buộc cloud-first vẫn giữ nguyên. Việc nối worker và Drive sink do nhánh chính thực hiện sau handoff.
