# Validation theo batch128

Ngày13/11/2026. Gói này nối dự báo theo batch vào validation và best-checkpoint export Junyi. Trạng thái hiện tại là CPU_VERIFIED / T4_MEASUREMENT_PENDING / A0_FULL_REPLAY_PENDING. Chưa có số đo tăng tốc GPU từ gói này.

## Implementation

`prediction_batch.py` dùng lại geometry/masks/OOV của iterator lịch sử và hỗ trợ tối đa128window theo cấu hình adapter. Window của các learner có thể nằm trong cùng batch, mỗi window giữ lịch sử riêng. Batch được flush trước record OOV để giữ thứ tự và null semantics.

`research_junyi_selection.py` nhận validation_batch_size riêng. CLI dùng `--validation-batch-size 128`. Cùng tham số được dùng ở validation mỗi epoch và xuất raw best-checkpoint predictions. Kích thước batch được bind vào grant prepared_inputs, run/checkpoint identity và terminal. Đổi mode giữa các lần resume bị từ chối. Cách gọi cũ không truyền tham số vẫn giữ prediction implementation lịch sử.

Mode mới có tên `batched_windows_v1_batch128`. Tham chiếu A0 cũ ghi `legacy_single_window_v1`, nên guard sẽ từ chối gọi đó là hai điều kiện cùng execution mode. Trước main comparison cần kiểm lại A0 và đóng một reference mới có provenance dẫn về reference cũ. Chưa tạo reference mới hoặc áp dụng vào training chính trong gói này.

## Kiểm CPU đã đạt

tests04.log/xml ghi126ca đạt trong16,61giây. Có đối chiếu đầy đủ PredictionRecord/target order/labels/OOV/export bằng adapter giả, nhóm128window và batch cuối lẻ. Hai ca mới dùng native AKT và A1 trên CPU, so xác suất với atol/rtol1e-6 trên nhiều learner, độ dài khác nhau và OOV, đồng thời kiểm tham số/RNG không đổi và nhãn hiện tại/tương lai không thay dự báo trước đó. Giữ tests03 với124ca trước bổ sung hai kiểm về tham chiếu A0 khác mode.

Các ca orchestration kiểm grant đúng batch, validation/export cùng mode, fingerprint checkpoint và chặn đổi mode khi resume. Giữ tests02 với lỗi test gọi nhầm global_rank trên PredictionRecord. Rank chỉ có ở export, test đã sửa bằng cách đếm thứ tự trong từng learner. Lỗi này thuộc bộ kiểm, chưa có training hoặc artifact nghiên cứu bị thay đổi.

## Kiểm T4 đã chuẩn bị

`scripts/akt/synthetic_validation_batch_probe.py` đo A0/A1 fresh-seed42 trên64learner giả,128window và12.800target, vocabulary717. Có warm-up và3cặp đo đảo thứ tự hai mode. Giữ target metadata exact, max/mean sai lệch probability, Log Loss delta, thời gian và peak VRAM. Probe không cập nhật trọng số. Thời gian chưa bao gồm SQL/I/O Junyi vì learner đã ở RAM.

Notebook `notebooks/akt_colab_validation_batch.ipynb` dùng gói nguồn `artifacts/akt/colab/junyi-validation-batch-20261113-02.zip`,321file, SHAf19b30fd799a4c56a1cb4e8bc122ee2c692d9b49eb8c04d663edd464c3be3399. Notebook kiểm từng file, tạo venv trong dự án và chỉ cài bổ sung qua Python của venv. Phải đạt pytest trước probe GPU. Tất cả artifact cần tải về D và kiểm inventory.

Cầu nối Colab mới đã mở và đang chờ người dùng xác nhận MCP/T4. Không dispatch GPU khi chưa đọc actual runtime. Không sử dụng Modal trong gói này.

## Điều kiện nghiệm thu optimization

1. T4 đo parity và tăng tốc thực cho A0/A1, không OOM hoặc đổi target.
2. Dùng checkpoint A0 đã lưu để đánh giá lại toàn selection theo mode mới, không train lại. Muốn xác nhận nguyên quyết định early stopping cần kiểm lịch sử12checkpoint hoặc có cận sai số hợp lệ cho mọi quyết định liên quan.
3. `a0-stopping-margin.json` dựng lại quy tắc dừng từ lịch sử cũ. Margin nhỏ nhất tới ngưỡng cải thiện là5,1068e-5. Một điều kiện đủ là sai lệch Log Loss của từng checkpoint nhỏ hơn2,5534e-5. Đây là cận lý thuyết từ số liệu lịch sử, chưa phải sai lệch CUDA đã đo.
4. Đo toàn validation thực gồm reader/sort/window/hash/I/O và xuất dự báo để tính lại chi phí. Phép đo trên dữ liệu giả không bảo đảm cùng speedup trên toàn Junyi hoặc H100.

Sau các bước trên mới có cơ sở tiếp nhận optimization cho ma trận chính. Phần confidence và producer A2/A3 vẫn là công việc riêng cần hoàn thiện.
