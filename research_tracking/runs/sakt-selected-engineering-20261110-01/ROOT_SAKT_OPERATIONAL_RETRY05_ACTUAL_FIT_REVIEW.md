# ROOT duyệt retry05 sau admission ổn định

Request05 SHA `e5346deff6b8d8f5ecd857449487baafebbb6095265ec4a63dbfe66a4911c52f` giữ nguyên spec/evidence/auth03 và allocation. Native run03 chưa được tạo sau NoGo04. Các source/input/runtimepins đã kiểm khớp. Không có model hoặc optimizer trước đó của run03.

Root đổi shell khởi chạy sang cmd.exe để giảm overhead tiến trình cha, không đổi interpreter .venv, worker, hyperparameters hoặc canonicalfloor4GiB. Phối hợp tạm ngừng subprocess của các nhánh ở cửa sổ admission. Ba mẫu mới4703780864,4702580736,4699283456byte đều vượt cả floor4GiB và256MiB headroom đã đề xuất trước. Kiểm này được giữ tại sakt-retry05-light-admission02.json.

Cho phép đúng một publicCPU retry05 với caps600/580/560/540/train300,2GiBworker/family/free2GiB,300updates33600targets. Giữ NoGo04elapsed và failure run02 trước, không tự retry nếu lượt này lỗi. Nghiệm thu cả producer, telemetry finally, sourcepost và Job0. Chưa có quyền refit/calibration hoặc dùng Modal.
