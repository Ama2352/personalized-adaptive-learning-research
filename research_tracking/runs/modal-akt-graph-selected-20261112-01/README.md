# AKT đồ thị Main60 trên Modal — 12/11/2026

## Phạm vi đã được duyệt

Người dùng đã duyệt thêm tối đa 2,50 USD từ free credits cho sáu điều kiện A1/A2/A3, mỗi điều kiện trên nguồn đồ thị expert và learned. Mỗi lúc chỉ chạy một GPU, không tự retry training lỗi. Allocation đã ghim trong `allocation.json`. Dự toán bảo thủ cho sáu lượt compute là 2,016 USD, giữ khoảng dự phòng 0,484 USD trong grant đợt này. Tổng workspace trước đợt là 0,17055957 USD, số API có thể cập nhật trễ.

Đây là corpus mô phỏng Grade 10 gồm 48 học viên train, 6 selection và 6 calibration. Các lượt này chỉ fit80 và chọn epoch bằng raw selection. Calibration giữ riêng, chưa refit90, chưa final evaluation. Seed42 và cấu hình mô hình/optimizer/early stopping giữ như A0 đã nghiệm thu.

## Các biến thể

| ID | Nội dung | Nguồn đồ thị |
|---|---|---|
| A0 | AKT không đồ thị, đã nghiệm thu ở bundle trước | Disabled |
| A1_EXPERT / A1_LEARNED | Đồ thị cố định | Expert / learned |
| A2_EXPERT / A2_LEARNED | Trọng số cạnh theo confidence | Expert / learned |
| A3_EXPERT / A3_LEARNED | Confidence kết hợp gate có thể giảm ảnh hưởng đồ thị | Expert / learned |

Graph và confidence dùng kết quả Method24 đã fit từ TRAIN48. Score là mức ổn định dự báo có điều kiện trên surrogate đã fit. Không diễn giải score thành xác suất cạnh đúng. True-edge labels từ oracle không được đưa vào training.

## Tìm lại checkpoint và artifact

`checkpoint-index.json` là chỉ mục theo candidate và run. Mỗi lượt hoàn tất có epoch được chọn, SHA của state/metadata/COMPLETE, archive local và đường dẫn dự phòng trên Modal Volume v2. `saved_epochs` giữ danh sách các checkpoint đã lưu. Bản selected-fit80 được ghi đúng phase để tránh nhầm với model sau refit.

Models, checkpoints, predictions và logs lớn nằm trong `experiments/akt/results/<run-id>/`. Checkpoint local hiện nằm bên trong `artifacts.zip`, có ba file trong mỗi thư mục epoch. Khi trích để nạp mô hình cần đối chiếu SHA với chỉ mục. Bản durable giữ ở Volume tên `kltn-akt-<run-id>`, thư mục `<run-id>/checkpoints/epoch-<n>/`. Mỗi checkpoint hoàn tất được copy, kiểm hash và commit trước khi chạy tiếp.

Chỉ mục cập nhật bằng Python `.venv`.

```powershell
.\.venv\Scripts\python.exe -B research_tracking/runs/modal-akt-graph-selected-20261112-01/update_checkpoint_index.py
```

## Kiểm trước chạy và sự cố đã giữ

Đã parse ba module, kiểm CRC/SHA của 37 file input và dry-run đủ sáu candidate. `local-preflight.json` giữ kết quả. Bộ kiểm mô hình CPU1994 và nghiệm thu checkpoint GPU trước đó vẫn ở bundle `modal-akt-recovery-20261112-01`.

Lượt mở App đầu bị lỗi thư mục log ở phía local. App đã dừng trước khi có function được tạo, đọc layout trả danh sách rỗng. `cancelled-launch01.json` giữ nguyên nhân, hash của reservation và request trước đổi runID. Reservation/lock cũ được giữ ở file có hậu tố cancelled. Run A1_EXPERT tiếp theo dùng ID kết thúc bằng02. Không có training retry từ lỗi này.

## Junyi là nhánh dữ liệu riêng

Những checkpoint ở đây dùng 84 item của Grade 10. Junyi có vocabulary bài tập riêng và phải train checkpoint riêng. Protocol21 đã chọn outer fold4 trên Development, bên trong outer-train là80/10/10 cho train/selection/calibration. Outer-validation và Holdout tách riêng khỏi chọn epoch/cấu hình.

Audit mới xác nhận reader Junyi hiện có đọc canonical theo người học và thứ tự `time_done, source_row`, vocabulary train-only và cửa sổ nhân quả. `src/knowledge_tracing/akt/splits.py` còn là inner split90/10 của baseline cũ. Main selected producer hiện chặn Junyi trong `research_main_execution.py`. Vì vậy cần nối role split80/10/10 và producer CUDA cho Junyi trước khi gọi là sẵn sàng training đầy đủ. Việc này không sửa partition/BKT lịch sử. Không tự suy tốc độ hoặc chi phí Junyi từ corpus60học viên.

## Nguồn

- `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md`.
- `docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md`.
- `research_tracking/runs/main60-graph-condition-binding-20261110-01/`.
- `research_tracking/runs/modal-akt-recovery-20261112-01/main60-a0-verification.json`.
- [Modal pricing](https://modal.com/pricing).
