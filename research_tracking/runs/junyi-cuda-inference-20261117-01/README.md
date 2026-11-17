# Nối suy luận CUDA và lưu cloud — 17/11/2026

## Đã kiểm

Config junyi-inference nhận CUDA chỉ khi có ResearchCUDAExecutionProfile batch128 đã đóng băng. Builder metadata CUDA tái dùng toàn bộ kiểm roles, encoding90, graph/confidence và export refit của CPU. Cả CPU/CUDA inference vẫn chặn optimizer/fit. Chưa chạy nhánh CUDA mới trên GPU thật.

`tests03.txt` đạt36ca metadata/config, `tests04.txt` đạt70ca và1skip trong27,83giây, gồm producer, CPUfit cloud, loader inference và CUDAconfig. Skip là quyền tạo directory symlink trên Windows. Các test dùng dữ liệu tổng hợp, không là kết quả calibration Junyi thật. tests01 giữ lỗi thiếu PYTHONPATH rồi tests02 xác nhận26ca đạt sau đặt PYTHONPATH trong .venv.

## Cache và chi phí GPU

Rà source phát hiện producer rawexport thay phase có thể bỏ context_cache đã gắn. Đã thêm context_cache rõ ràng và truyền lại khi set_phase. Regression test giữ đúng object cache khi chuyển phase đạt trong tests04. Cache của A1–A3 vẫn được adapter kiểm typed binding như trước. A0 từ chối nhận graph cache.

API rawexport giờ có typed artifact_root cho Volume, default output cũ giữ behavior local. API này còn đọc/join/audit trên CPU, nên không được xem là function GPU đã tách CPU hoàn toàn. Worker GPU tiết kiệm cần lấy windows/contextcache đã chuẩn bị từ CPU, xuất numeric probabilities và window IDs; CPU worker join/audit/Parquet/fit rồi Drive. SelectionCache hiện chỉ dành raw_selection10, không được đổi tên scope để dùng cho calibration.

## Còn phải làm trước inference Junyi thật

1. Đóng/pin source sau tích hợp và refresh input plan. Chuẩn bị source/upstream Git checkout đúngcommit trên cloud.
2. CPU dựng windowcache chung calibration10, contextcache riêng A1–A3, chứng minh tất cả target/key và prefix khớp. Cache paths cần phù hợp owned-root của pipeline.
3. Nối GPU-only numeric prediction vào CPUjoin/export, kiểm parity CPU hoặc GPU nhỏ với cùng target/batch128. Đo runtime/VRAM và lưu Drive receipt.
4. Chạy rawinference A0–A3 cùng population, trả GPU, CPU12–16GiB fitV1 rồi đồng bộ Drive. Kiểm integrity mọi tranche trước tiếp tục.
5. Sau calibration mới chuyển outer evaluation riêng. Không dùng calibration/outer để chọn lại epoch. Holdout nằm ngoài gói.

Source và logs nằm trong ROOT_MANIFEST.json. Đây là bằng chứng engineering, chưa có kết luận mới về hiệu quả đồ thị.
