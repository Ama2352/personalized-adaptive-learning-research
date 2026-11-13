# Validation theo batch128

Ngày 13/11/2026. Gói này nối dự báo theo batch vào validation và best-checkpoint export Junyi. Trạng thái chốt là CLOSED_T4_SYNTHETIC_PASS_A0_REAL_REPLAY_PENDING. Kiểm T4 đã đạt trên dữ liệu tổng hợp. Việc kiểm lại checkpoint A0 thật và chi phí đọc dữ liệu toàn Junyi còn chờ. Lượt này không train epoch và dùng 0 USD Modal.

## Implementation

`prediction_batch.py` dùng lại geometry/masks/OOV của iterator lịch sử và hỗ trợ tối đa128window theo cấu hình adapter. Window của các learner có thể nằm trong cùng batch, mỗi window giữ lịch sử riêng. Batch được flush trước record OOV để giữ thứ tự và null semantics.

`research_junyi_selection.py` nhận validation_batch_size riêng. CLI dùng `--validation-batch-size 128`. Cùng tham số được dùng ở validation mỗi epoch và xuất raw best-checkpoint predictions. Kích thước batch được bind vào grant prepared_inputs, run/checkpoint identity và terminal. Đổi mode giữa các lần resume bị từ chối. Cách gọi cũ không truyền tham số vẫn giữ prediction implementation lịch sử.

Mode mới có tên `batched_windows_v1_batch128`. Tham chiếu A0 cũ ghi `legacy_single_window_v1`, nên guard sẽ từ chối gọi đó là hai điều kiện cùng execution mode. Trước main comparison cần kiểm lại A0 và đóng một reference mới có provenance dẫn về reference cũ. Chưa tạo reference mới hoặc áp dụng vào training chính trong gói này.

## Kiểm CPU đã đạt

tests04.log/xml ghi126ca đạt trong16,61giây. Có đối chiếu đầy đủ PredictionRecord/target order/labels/OOV/export bằng adapter giả, nhóm128window và batch cuối lẻ. Hai ca mới dùng native AKT và A1 trên CPU, so xác suất với atol/rtol1e-6 trên nhiều learner, độ dài khác nhau và OOV, đồng thời kiểm tham số/RNG không đổi và nhãn hiện tại/tương lai không thay dự báo trước đó. Giữ tests03 với124ca trước bổ sung hai kiểm về tham chiếu A0 khác mode.

Các ca orchestration kiểm grant đúng batch, validation/export cùng mode, fingerprint checkpoint và chặn đổi mode khi resume. Giữ tests02 với lỗi test gọi nhầm global_rank trên PredictionRecord. Rank chỉ có ở export, test đã sửa bằng cách đếm thứ tự trong từng learner. Lỗi này thuộc bộ kiểm, chưa có training hoặc artifact nghiên cứu bị thay đổi.

## Kiểm T4 đã hoàn tất

`scripts/akt/synthetic_validation_batch_probe.py` đo A0/A1 fresh-seed42 trên64learner giả,128window và12.800target, vocabulary717. Có warm-up và3cặp đo đảo thứ tự hai mode. Giữ target metadata exact, max/mean sai lệch probability, Log Loss delta, thời gian và peak VRAM. Probe không cập nhật trọng số. Thời gian chưa bao gồm SQL/I/O Junyi vì learner đã ở RAM.

Nguồn chạy lần đầu là `artifacts/akt/colab/junyi-validation-batch-20261113-02.zip`, 321 file, SHA f19b30fd799a4c56a1cb4e8bc122ee2c692d9b49eb8c04d663edd464c3be3399. Toàn bộ hash được kiểm ở Colab. Runtime thực là T4, Python 3.13.16, Torch 2.14.1+cu130, CUDA 13.0. Dùng venv trong dự án kế thừa thư viện sẵn có, không cài global. Kiểm Linux đạt 126 ca trong 14,04 giây, giữ log và JUnit trong bundle.

Phép kiểm ban đầu dùng nhãn cân bằng, làm phần cộng đồ thị A1 triệt tiêu. Giữ nguyên `balanced-result.json` cùng log như đối chứng âm. Sau đó chỉ bổ sung lựa chọn tín hiệu tổng hợp dương vào probe để xác nhận đường đồ thị thật sự hoạt động. `colab-probe-source-overlay.json` giữ SHA trước/sau thay đổi. Không sửa logic production hoặc cấu hình training. Phép kiểm thứ hai giữ ở `positive-result.json`, residual đồ thị khác A0 tối đa 0,1233.

| Điều kiện | A0 từng cửa sổ → batch128 | A1 từng cửa sổ → batch128 | Thời gian chương trình |
|---|---|---|---|
| Nhãn cân bằng | 1,853 → 0,426 giây, 4,35 lần | 5,239 → 2,990 giây, 1,75 lần | 42,31 giây |
| Tín hiệu đồ thị dương | 1,321 → 0,340 giây, 3,88 lần | 5,068 → 2,522 giây, 2,01 lần | 41,56 giây |

Thời gian là trung bình ba lượt mỗi mode. Lượt A0 cân bằng có một điểm chậm 2,88 giây, còn hai lượt gần 1,34 giây. A1 tín hiệu dương cũng có một lượt chậm 6,23 giây. Giữ từng phép đo và thể hiện chúng bằng chấm trên hình, không chỉ giữ trung bình. Các số đo này chưa bao gồm SQL/I/O Junyi và không suy ra tốc độ H100 hoặc toàn epoch training.

Cả hai phép kiểm giữ target metadata và thứ tự chính xác. Sai lệch xác suất lớn nhất của fixture dương là 1,1921e-7 cho cả A0 và A1, chênh lệch Log Loss bằng 0 theo phép đo. Peak VRAM cấp phát của PyTorch khoảng 1,14 GiB ở batch128. Đây là bộ nhớ tensor cấp phát, chưa bao gồm mọi loại bộ nhớ CUDA của tiến trình. Không thực hiện backward hoặc cập nhật trọng số.

Artifact gốc đã tải về `experiments/akt/results/colab-validation-batch-20261113-01/artifacts.zip`, 9.624 byte, 8 file cùng inventory. `artifact-verification.json` xác nhận SHA trước/sau tải, ZIP CRC và hash từng file. Không chuyển dữ liệu Junyi thật hoặc checkpoint A0 đã train lên Colab trong lượt này. Đã thực hiện lệnh `runtime.unassign()` sau khi kiểm artifact trên D và đóng cầu nối, trạng thái local ghi `closed`.

Notebook tái lập hiện ghim gói nguồn `artifacts/akt/colab/junyi-validation-batch-20261113-03.zip` và chọn rõ `--signal positive`. Gói 03 gồm thay đổi probe đã chạy qua overlay, SHA 2d44808eb6b58bc67ab09e034f803a18acd6479032b3fdbc2f4234af36d38ff3. Manifest cuối giữ cả nguồn 02 và 03.

## Figure và cách dựng lại

`validation-batch-t4-v2.svg`, `.png`, `.pdf` là bản minh họa được kiểm trực quan, dữ liệu tại `validation-batch-data-v2.csv`. Dựng lại bằng Python của `.venv` với `build_gpu_figure.py` trong bundle. Script đọc trực tiếp `positive-result.json`, không nhập tay số đo. Giữ bản hình đầu và `build_gpu_figure_v1.py` để truy vết thay đổi khoảng cách nhãn. Figure dùng quy ước từ figures4papers, commit e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15, giấy phép CC BY-NC 4.0. Hồ sơ nguồn và giấy phép ở `research_tracking/runs/figures4papers-akt-20261112-01/`.

`manifest-cpu.json` là snapshot lịch sử trước phép đo GPU. `manifest-final.json` đóng bundle sau khi cập nhật bằng chứng T4. `record_gpu_progress.py` lưu cách cập nhật hai báo cáo và trạng thái, không chạy lại sau khi bundle đã đóng.

## Điều kiện nghiệm thu optimization

1. T4 đo parity và tăng tốc thực cho A0/A1, không OOM hoặc đổi target.
2. Dùng checkpoint A0 đã lưu để đánh giá lại toàn selection theo mode mới, không train lại. Muốn xác nhận nguyên quyết định early stopping cần kiểm lịch sử12checkpoint hoặc có cận sai số hợp lệ cho mọi quyết định liên quan.
3. `a0-stopping-margin.json` dựng lại quy tắc dừng từ lịch sử cũ. Margin nhỏ nhất tới ngưỡng cải thiện là5,1068e-5. Một điều kiện đủ là sai lệch Log Loss của từng checkpoint nhỏ hơn2,5534e-5. Đây là cận lý thuyết từ số liệu lịch sử, chưa phải sai lệch CUDA đã đo.
4. Đo toàn validation thực gồm reader/sort/window/hash/I/O và xuất dự báo để tính lại chi phí. Phép đo trên dữ liệu giả không bảo đảm cùng speedup trên toàn Junyi hoặc H100.

Sau các bước trên mới có cơ sở tiếp nhận optimization cho ma trận chính. Phần confidence và producer A2/A3 vẫn là công việc riêng cần hoàn thiện.
