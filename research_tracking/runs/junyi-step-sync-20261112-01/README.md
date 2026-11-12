# Giảm đồng bộ CPU–GPU trong bước training AKT

## Mục đích và trạng thái

Ưu tiên kiểm một thay đổi giữ nguyên batch4, dữ liệu, phép loss, backward, clipping, Adam và RNG. Gộp các số kiểm tra và chẩn đoán vào ít lần đọc về CPU hơn. Giữ chỉ số probe trên GPU đến khi kiểm trạng thái sau cập nhật.

Kiểm dữ liệu giả trên CPU đã khớp tuyệt đối qua8bước mỗi bản, gồm model, Adam, gradient, RNG, metric và prediction. Đã kiểm nhánh không có target và target NaN. Chưa nghiệm thu tốc độ hoặc tương đương CUDA trong gói chuẩn bị này. Mã candidate ở checkout chưa được đưa vào archive source04 đang chạy.

## Thiết kế đo GPU

Dùng controller hiện có, một T4, dự phòng tối đa0,20USD trong trần30USD toàn KLTN. Đợi execution06 có archive đã kiểm và stop acknowledgment. Kiểm không còn container KLTN trước dispatch. Không mở training chính tiếp theo trong lúc đo.

Mỗi bản chạy cùng packet1.024window/56.332target từ TRAIN80 đã được phép chuyển, batch4/256updates, cùng seed42 và thứ tự shuffle43. Ba cặp đo theo thứ tự reference–candidate, candidate–reference, reference–candidate. Mỗi trường hợp có checkpoint và kiểm reload. Đối chiếu chính xác model, Adam và RNG cuối mỗi cặp. Thêm16updates/1.536target dữ liệu giả để kiểm tương đương CUDA trước benchmark. Giới hạn tổng1.552updates/339.528lượt target, worker320giây, guard400giây, function420giây, không tự retry.

Thu nvidia-smi mỗi khoảng0,25giây và ghi pha thực thi. Đo thời gian gồm collate và step, đồng bộ CUDA mỗi batch như phép đo gốc. Xuất cả thời gian toàn lượt và bỏ batch đầu. GPU-Util là mẫu theo thời gian của NVIDIA, có thể chứa trễ hoặc lẫn biên giữa hai pha. Thời gian validation, checkpoint và startup được ghi riêng khỏi thông lượng training.

## Tiêu chí tiếp nhận

- Tất cả kiểm chính xác CPU và CUDA đạt, không mất kiểm invalid target, mask, output hữu hạn hoặc clipping.
- Archive tải về đúng SHA, CRC và inventory, sáu checkpoint đủ và App đã dừng.
- Cả ba cặp đều nhanh hơn và trung vị giảm ít nhất5% thời gian sau batch đầu. Ngưỡng này là tiêu chí kỹ thuật thực dụng, chưa là kiểm định thống kê.
- Nếu chênh lệch nhỏ, trái chiều hoặc candidate chậm hơn, giữ bản hiện hành và ghi kết quả âm. Không suy ra tối ưu toàn bộ GPU từ phép đo ngắn.
- Muốn dùng cho training chính còn cần ghim nguồn mới và đối chiếu resume cùng checkpoint. Bundle này chưa cho phép gắn candidate vào execution06 đang chạy.

## Bằng chứng và dựng lại

`model-before.py` giữ nguyên byte từ source04. `model-candidate.py` giữ candidate được đo. `model-candidate-v1.py` và `cpu-equivalence-v1.json` giữ bước gom chẩn đoán ban đầu. `verify_equivalence.py` dựng lại đối chiếu synthetic bằng Python trong `.venv`. `gpu_worker.py` và `request.json` ghi workload và phép đo. `run_after_a0.py` chỉ đợi một lượt A0 rồi dispatch đúng một profile.

`cpu-equivalence.log` giữ lỗi quyền sở hữu Git ban đầu. Đã xử lý bằng safe.directory riêng trong biến môi trường của tiến trình, không sửa Git global. `regression-tests.log` giữ lỗi thư mục tạm của pytest cùng8ca đạt. Lượt sau dùng vùng tạm riêng dưới `artifacts/akt/tmp/`, đạt15ca trong11,18giây. Các log tiếp theo phải gắn với phiên bản candidate tương ứng.

Không sử dụng Holdout, calibration, outer validation hoặc nhãn thật/nhiễu của cạnh. Phép đo kỹ thuật này chưa tạo kết luận RQ mới.

## Rà soát candidate trước CUDA

Bản đo dùng gather với chỉ số dạng vector trên GPU để đọc probe trước/sau Adam. Bảnv1/v2 và kết quả CPU tương ứng được giữ riêng. Bản cuối đã khớp CPU qua8updates mỗi phía, log ở `cpu-equivalence04.log`. Các primitive loss/backward/clipping/Adam và mọi phương thức ngoài step giữ nguyên AST. Việc giảm đồng bộ phù hợp hướng dẫn PyTorch, tốc độ thực phải xác nhận bằng profile. [Hướng dẫn PyTorch](https://docs.pytorch.org/tutorials/recipes/recipes/tuning_guide.html#avoid-unnecessary-cpu-gpu-synchronization).
