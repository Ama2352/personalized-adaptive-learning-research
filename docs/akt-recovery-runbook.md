# Khôi phục lượt AKT bị ngắt

Áp dụng cho public smoke/pilot CLI trên cùng runtime/source đã xác minh. Không cấp quyền train dữ liệu thật, GPU, full CV hoặc Holdout. Luôn dùng Python trong `.venv` của repository.

## Trước lượt chạy

Config có thể thêm:

```json
"recovery": {"checkpoint_every_steps": 10}
```

Không thêm trường này thì giữ luồng cũ. Cadence là lựa chọn I/O, không đổi batch size hoặc hyperparameters. Smoke fixture dùng cadence 1; pilot thật phải dự toán tổng số snapshot × kích thước checkpoint và đủ đĩa. Mọi authorization cũ sẽ không còn hợp lệ khi config/build thay đổi. Gate2 PASS chỉ là software evidence, không là authorization.

## Sau khi bị ngắt

1. Chờ watchdog kết thúc worker và ghi `watchdog-resources.json`. Không đọc run đang ghi.
2. Kiểm `recovery-envelope.json` và SHA-256. Không có envelope thì không tự đoán checkpoint bằng glob/newest file. Run chưa có committed update có thể không có recovery.
3. Tạo config mới với `run_id`/`output_dir` mới. Giữ toàn bộ training/data/seed/optimizer/budget fields. Thêm đường dẫn tuyệt đối hoặc repo-relative đến envelope cũ và đúng hash:

```json
"recovery": {
  "checkpoint_every_steps": 10,
  "source_envelope": "experiments/akt/results/<old-run>/recovery-envelope.json",
  "source_sha256": "<64 ký tự hex SHA-256 thực tế>"
}
```

4. Chuẩn bị authorization riêng cho config mới, theo cổng đã có và phạm vi workload đã được người dùng duyệt. Không copy approval cũ hoặc sửa `approved` để tự mở quyền.
5. Chạy cùng entrypoint:

```powershell
$env:PYTHONPATH='src;third_party'
./.venv/Scripts/python.exe -B -m knowledge_tracing.akt.cli pilot --config <new-config.json> --authorization <new-authorization.json>
```

## Nghiệm thu

Kiểm manifest completed, attempt/retry_history, best epoch/history, checkpoint hash/reload, prediction source-row coverage và các budget/telemetry. Không coi exit code 0 hoặc file `.pt` xuất hiện là đủ. Recovery snapshot chưa hoàn thành epoch không được dùng làm selected model. Nếu validation/export lỗi, có thể khôi phục epoch đã train từ committed snapshot, nhưng validation/export phải thực hiện lại và kiểm đủ artifact.

Wall cap là tổng thời gian worker của cả chuỗi attempt; hết tổng budget thì dừng, không sửa cap để tiếp tục dưới authorization cũ. Source/model/window/split/graph/device/runtime khác bị từ chối. Không sửa envelope/checkpoint cũ để khắc phục identity mismatch. Tạo issue với logs/hash và phân loại lỗi trước retry.

## Bằng chứng hiện tại

Xem `docs/thesis_recovery/17_AKT_RECOVERY_ENGINEERING_LOG.md`: actual CPU AKT dropout parity và CLI parent/worker synthetic fixture. Chưa có CUDA/Modal hoặc successful real-data pilot cho build recovery mới. Colab kit v6 là snapshot trước thay đổi này; phải build kit mới trước khi dùng để kiểm recovery.
