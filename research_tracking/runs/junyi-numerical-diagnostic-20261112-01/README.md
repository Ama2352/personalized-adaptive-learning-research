# Chẩn đoán dự đoán và phục hồi AKT Junyi

Bundle đang mở. Bằng chứng kỹ thuật được giữ riêng với kết quả nghiên cứu chính.

## Câu hỏi và tiến trình

Probe năm epoch trước dừng vì parity legacy/batch vượt ngưỡng1e-6. Lượt này dùng nguyên checkpoint epoch5 đã có để đo sai lệch, không chạy lại selected fit. Request ban đầu bị chặn trước dispatch vì còn phép tính billing delta của tranche cũ. Log và request trước sửa đã giữ. Admission được sửa theo ủy quyền mới về ngân sách toàn KLTN30USD.

T4 đã hoàn tất chẩn đoán. Trên1.405 dự báo có hỗ trợ,113 giá trị vượt1e-6, delta tối đa6,699562e-5. Metadata và null/OOV khớp trên1.530targets. Kiểm20truy vấn bằng thay đáp án hiện tại và dữ liệu tương lai đạt ngưỡng1e-6. Chi tiết ở `numerical-summary.json` và `causal-perturbation.json`.

Kiểm phục hồi chạy79bước liên tục đối chiếu40bước rồi nạp và chạy39bước. Trọng số, Adam, Python/NumPy/Torch CPU/CUDA RNG, sampler và loss_sum đều khớp chính xác. Tổng158updates/23.666target exposures là workload kiểm phục hồi. `native-recovery-proof.json` giữ counters. Bốn checkpoint được sao chép bền vững rồi tải về trong archive đã kiểm SHA/CRC.

CPU03 đọc cùng checkpoint trên CPU, không cập nhật trọng số. `cpu-numerical-summary.json` ghi ba đường legacy/batch4/same-length, cùng coverage và hash model giữ nguyên. Đây là kiểm số học, chưa xác định duy nhất nguyên nhân sai khác CUDA. Full probabilities, delta CSV và metadata nằm trong archive CPU03.

## Quyết định triển khai

Producer Junyi chính dùng `legacy_single_window_v1`, ghi rõ trong run identity. Giữ nguyên ngưỡng1e-6 và helper batch như đường opt-in chưa nghiệm thu. Checkpoint cũ vẫn là bằng chứng pilot với prediction profile cũ. Không tái gắn nhãn thành mô hình nghiên cứu chính. Huấn luyện vẫn dùng batch4 theo cấu hình hiện hành.

## Lỗi được giữ và kiểm tiếp

CPU03 có16lỗi setup A1 do thiếu thư mục cha của pytest basetemp, trước khi chạy model. Diagnostic CPU riêng hoàn tất. Lỗi và logs được giữ trong `cpu03-a1-tests.log`, receipt và archive. CPU04 sẽ tạo thư mục cha và kiểm nguồn hiện hành, gồm regression đường legacy. Không dùng lỗi setup để kết luận adapter đúng hay sai.

Controller CPU03 bị chỉnh đồng thời sau khi tiến trình đã đọc file. Request thực thi lưu trong output native, gồm worker/diagnostic/archive pins và conservative envelope5,35USD, là nguồn ghi cấu hình lượt này. Worker, source packet và input đã giữ nguyên trong lượt chạy. Không coi file controller sau chỉnh là snapshot chính xác toàn bộ mã local đã thực thi.

## Vị trí và bảo toàn

- GPU native output `experiments/akt/results/modal-junyi-numerical-t4-20261112-01/` chứa archive101.269.469bytes, receipt và watchdog stop acknowledgment.
- CPU03 native output `experiments/akt/results/modal-junyi-numerical-cpu-20261112-03/` chứa archive965.958bytes và receipt.
- `checkpoint-index.json` trỏ chính xác bốn envelope trong archive và durable Volume. Mỗi envelope có state, metadata và COMPLETE.
- `request.json`, `project-budget-fix.json` và tám kiểm thuần ghi thay đổi budget admission. `research_tracking/COMPUTE_BUDGET.json` giữ tổng trần30USD, dự phòng và từng allocation. Historical upper là dự phòng bảo thủ, không là hóa đơn thực tế.

## Giới hạn và bước tiếp

Chưa full Junyi fit, chưa epoch selection chính, refit/calibration hoặc benchmark final. Chưa tuyên bố graph model tốt hơn. Sau CPU04 cần đo training với chuỗi dài đại diện và tính cả validation/checkpoint trong dự toán trước main fit.

## Nghiệm thu nguồn hiện hành

CPU04 đã đạt **2.218tests,0failure/error/skip** trong109,96giây. Nguồn giữ nguyên trong lượt kiểm. Gồm16ca native A1 và regression producer dùng dự đoán tuần tự. Archive94.871bytes đã tải và kiểm inventory. Watchdog xác nhận App dừng. Gate gắn source04, không nghiệm thu CUDA A1 hoặc full training Junyi.
