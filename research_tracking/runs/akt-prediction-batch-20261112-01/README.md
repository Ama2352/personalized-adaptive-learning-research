# AKT — xuất dự đoán theo batch cửa sổ

## Phần đã hoàn thành

Gói ngày12/11/2026 bổ sung `src/knowledge_tracing/akt/prediction_batch.py` và `tests/akt/test_prediction_batch.py`. API opt-in là `iter_predictions_batched(adapter, learners, batch_size=None)`.

- Gom tối đa4cửa sổ trong giới hạn batch của adapter, có thể qua ranh giới learner. Chỉ `WindowInputs` nhân quả đi vào `predict_windows`.
- Gặp OOV, xuất batch đang chờ trước rồi phát record null đúng vị trí. Dòng toàn OOV được phát trực tiếp, không gọi mô hình.
- Giữ đủ các trường `PredictionRecord`, checkpoint/support, source/time/outcome/fold, history và context reset. Metadata target được nối sau inference.
- Hàng chờ chỉ giữ cửa sổ và target tương ứng trong batch. Đường `iter_predictions` lịch sử được giữ nguyên trong file cũ.

## Kiểm chứng

`tests01.log/xml` ghi29tests đạt. Adapter giả có đầu ra xác định được dùng để đối chiếu chính xác từng record với nguyên hai hàm `_checkpoint_id`/`iter_predictions` lấy bằng AST từ source lịch sử hiện hành. Cách lấy AST phục vụ kiểm hợp đồng, tránh import Torch trên máy local thiếu RAM.

Các ca kiểm có chuỗi450–520event, context100/target100, nhiều learner, OOV ở giữa và đầu/cuối, current/future-response invariance, batch cuối chưa đủ, checkpoint fallback hash, thiếu support và output không hợp lệ. Fixture6learner tạo2calls với kích thước4và2, giữ cùng record/thứ tự. Đây là số lần gọi của adapter giả.

`import-check.json` xác nhận fresh process import helper không nạp Torch.

## Phần còn thiếu

Chưa đo tăng tốc GPU hoặc số học batch1/batch4 bằng model thật. Cần kiểm trên runtime Linux/CUDA đã ghim và đối chiếu target metadata chính xác, xác suất trong tolerance đã duyệt trước khi producer nghiên cứu chính dùng đường batch. Khác shape batch CUDA có thể tạo chênh số học nhỏ.

Bundle đang mở để nhánh chính nghiệm thu. Không chạy GPU/cloud, training hoặc sửa artifact lịch sử.


## Nghiệm thu nhánh chính

Bundle đóng sau rà soát nhánh chính. Kiểm CUDA thực và nguồn Linux hiện hành được theo dõi tiếp ở `research_tracking/runs/junyi-gpu-optimization-20261112-01/`. Kết quả ở đây là bằng chứng engineering theo phạm vi từng phép kiểm.
