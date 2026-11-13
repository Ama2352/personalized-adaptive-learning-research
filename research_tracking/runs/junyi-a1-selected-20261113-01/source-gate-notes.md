# Chuẩn bị nguồn và Linux CPU Gate A1

Ngày 13/11/2026. Source mới tại `artifacts/akt/modal/junyi-a1-selected-20261113-01/source.zip`, 323 file, 1.171.634 byte, SHA 0e6cdd2b32f7ff2fcd04da2a65889c7cfa303b54fb35763dff5435a21ac581df. Chưa có CPU Gate mới tại thời điểm chuẩn bị này.

`prepare_source_gate.py` dùng lại allowlist của `scripts/akt/build_colab_bundle.py` và dependency từ source A0 đã nghiệm thu. Có graph Junyi 976 cạnh corrected cùng A0 comparison reference `data-audit.json`. Notebook được xử lý theo cơ chế strip-output có provenance sẵn của builder. Không có dataset Junyi, checkpoint, credentials hoặc Holdout trong source zip này. Dữ liệu train/selection dùng archive riêng đã được phép chuyển.

Đã kiểm AST ba script chuẩn bị/controller/worker, ZIP CRC, inventory SHA từng file, toàn bộ module source/tests/scripts AKT hiện hành khớp local và loại trừ vùng bảo vệ. Dry-run controller đạt, in `paid_execution_requested=false`. Dry-run đầu trong môi trường hạn chế bị kẹt trước khi in request và được ngắt. Chạy lại với quyền phù hợp đạt trong khoảng 0,83 giây, không cloud dispatch.

Controller/worker lấy từ hồ sơ A0 H100, version run ID và source path riêng. Giữ Gate policy, timeout 600 giây VM CPU, pytest deadline 480 giây, reservation 0,15 USD, không GPU, không retry tự động. `refresh_gate2.py` vẫn kiểm upstream có sẵn trong image `im-ldjZsYO21pzaupmQXGLhnS`. Không phát hành Gate mới từ trạng thái synthetic T4 hoặc sửa report cũ.

Root cần thêm allocation `junyi-a1-selected-cpu-20261113-01` cap 0,15 USD vào ledger rồi chạy bằng Python `.venv` trong repository. Lệnh thực thi là `cpu_controller.py --source-zip artifacts/akt/modal/junyi-a1-selected-20261113-01/source.zip --source-sha256 0e6cdd2b32f7ff2fcd04da2a65889c7cfa303b54fb35763dff5435a21ac581df --run`. Bỏ `--run` để dry-run. Artifact CPU native sẽ ở `experiments/akt/results/modal-junyi-a1-selected-cpu-20261113-01/`.

Chỉ tiếp nhận khi receipt `MODAL_CPU_GATE_VERIFIED`, inventory tải về đã kiểm, Gate status PASS, source unchanged và App đã dừng. Nếu lỗi, giữ native log và failure. Không sửa nguồn bundle đã đóng, không áp dụng Gate cũ cho source mới.
