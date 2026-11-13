# Kiểm nhanh checkpoint A0 thật với validation batch128

Ngày 13/11/2026. Trạng thái FAIL_STRICT_PROBABILITY_PARITY. Đây là kiểm kỹ thuật trên CPU, dùng trọng số checkpoint thật và lịch sử tổng hợp. Không train epoch, không dùng Modal hoặc Holdout.

## Đã xác nhận

- Checkpoint epoch 9 tại `experiments/akt/results/model-export-a0-batch128-20261112-01/A0_JUNYI_SELECTED.pt` đúng SHA trong MODEL_INDEX, identity và trạng thái complete. Nạp strict toàn bộ trọng số vào kiến trúc gốc, vocabulary 717.
- Dự đoán 3.538 target của 130 learner tổng hợp, gồm nhóm đủ 128 cửa sổ, batch cuối lẻ và hai lịch sử dài 201/301 tương tác để kiểm cửa sổ có context. Thứ tự learner, target, nhãn và metadata khớp.
- Model weights và bytes checkpoint giữ nguyên sau kiểm. Lượt đo cuối khoảng 4,10 giây bên trong chương trình, peak RAM tiến trình khoảng 408 MiB. Runtime CPU là Torch 2.7.1+cpu, khác runtime T4 trước đó.

## Phần chưa đạt

Sai lệch xác suất tối đa 2,2382e-5, vượt ngưỡng kiểm atol/rtol 1e-6. Chênh lệch Log Loss toàn fixture chỉ 2,1764e-8. Hai đại lượng này phản ánh hai tiêu chí khác nhau. Chưa có cơ sở suy ngưỡng mastery hoặc quyết định chọn epoch trên Junyi thật giữ nguyên từ fixture này.

Không nới ngưỡng kiểm hoặc tiếp nhận batch128 vào training chính từ kết quả này. Chưa xác định nguyên nhân đầy đủ. Sai số tính toán FP32 phụ thuộc hình dạng batch là giả thuyết cần phân biệt với lỗi batching. Kiểm tiếp phù hợp là đối chiếu cùng checkpoint trên CUDA và selection Junyi, giữ dữ liệu và cách chọn epoch đã chốt. Chưa có kết quả cho toàn selection hoặc lịch sử 12 checkpoint.

## Lịch sử lượt thử

- `check.log` giữ lỗi fixture đầu dùng ID người học chưa sắp theo thứ tự từ điển. Đã sửa bằng ID đệm số, không thay dữ liệu thật hoặc pipeline.
- `check02.log` giữ lần gặp sai lệch xác suất vượt ngưỡng. Không thay ngưỡng để làm ca kiểm đạt.
- `check03.log` và `result.json` giữ số đo cuối, gồm cả Log Loss và tính bất biến checkpoint. Mã ghi kết quả trước khi trả lỗi nghiệm thu.
- `check_checkpoint.py` là mã dựng lại. Chạy bằng `.venv` trong repository. Chỉ tạo bundle mới khi tái kiểm, giữ bundle này sau đóng.

Hồ sơ T4 trước đó dùng model khởi tạo mới ở `research_tracking/runs/junyi-validation-batch-20261113-01/`. Kết quả ấy vẫn đúng trong phạm vi dữ liệu và model đã kiểm, chưa đủ để nghiệm thu trọng số A0 đã train. `manifest.json` giữ SHA nguồn/input/output và liên kết checkpoint gốc, không nhân đôi file model.
