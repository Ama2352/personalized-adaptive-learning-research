# Giảm đồng bộ CPU–GPU trong bước training AKT


## Kết quả cuối đợt và chi phí

Đã kết thúc đợt đo, không còn container ở snapshot20giờ07. Chưa có phương án tăng tốc được tiếp nhận vào bản chính. `src/knowledge_tracing/akt/model.py` đã khôi phục nguyên byte source04. Những candidate vẫn nằm trong bundle này.

| Lượt | Bằng chứng | Kết luận |
|---|---|---|
| 01, gom đồng bộ step | Sáu case training, ba cặp checkpoint giống từng byte, CUDA synthetic đạt. Trung vị giảm0,13%, một cặp chậm hơn | Không tiếp nhận. Worker toàn lượt FAILED do thử batch dự báo32 vượt tolerance1e-6 |
| 02, cast khoảng cách trên GPU | Sáu case, ba cặp checkpoint giống từng byte. Giảm0,91%/3,53%/3,43% | Dưới ngưỡng5% đã đặt, giữ bản thử nghiệm |
| 03, cache hằng số attention | CPU khớp, client chạm400giây, stop acknowledgment đạt | Chưa có artifact GPU dùng được, chưa xác định nguyên nhân sâu hơn. Không retry trong đợt này |

Dùng `analyze_training_profile.py --execution 01` hoặc02 để dựng CSV/JSON từ archive. Lượt01 được phân tích riêng phần training có sáu hồ sơ hoàn tất và ba hồ sơ exact, giữ nguyên FAILED của toàn job. Phép dự báo sai tolerance chưa lưu maxdifference trước assert nên chưa thể kết luận độ lệch lớn hay nhỏ. `analyze_results.py` là bản chuẩn bị ban đầu yêu cầu toàn bộ phép thử thành công, không dùng để diễn giải kết quả01.

`sync-profile-v2.svg` và `attention-profile-v2.svg` là hình đã sửa nhãn, có PDF/PNG, CSV và script dựng lại. Bảnv1 được giữ nguyên. Đã kiểm trực quan bảnv2 attention bằng ảnh render.

`billing-final.json` ghi metered3,24858233USD, credits3,24USD, billed0USD. Từ trước phép đo01 đến cuối đợt, số tổng ghi nhận tăng khoảng0,04USD. Đây là delta giữa snapshot, chưa phải hóa đơn mỗi App. Tổng dự phòng ba lượt là0,40USD, khác với tiền thực ghi nhận. `containers-final.json` rỗng. `reservation*.json` và request tương ứng giữ hạn mức, source pin và tên lượt.

Bước tiếp theo cần một giả thuyết mới hoặc chẩn đoán queue/startup của lượt03 trước khi đo lại. Chưa chạy tiếp A0 dài hoặc triển khai candidate vào pipeline. Dự toán toàn ma trận phải tính lại vì A0 đã cần ít nhất5epoch refit nếu quy tắc dừng giữ best hiện tại.

## Thiết kế được ghi trước các lượt đo

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

## Đo riêng batch dự báo

Sau training packet, dùng cùng một checkpoint để đo batch dự báo4 và32, ba cặp đảo thứ tự. Không cập nhật optimizer. Tổng tối đa337.992lượt target cần chấm và600.192dự báo token hợp lệ. Đòi hỏi xác suất lệch tuyệt đối tối đa1e-6, model và RNG giữ nguyên. Giới hạn GPU0,20USD và runtime giữ nguyên. Đây là hướng tăng tốc validation riêng, chưa thay batch training hoặc giao thức chính.

## Xác nhận dừng trước dispatch

A0 execution06 đã trả receipt PARTIAL và tạo archive trên Volume. Bộ kiểm dừng ban đầu chưa xác nhận được trạng thái. Kiểm độc lập sau đó thấy đúng App stopped/tasks0 và danh sách container rỗng. Log guard gốc giữ nguyên, xác nhận độc lập nằm ở `experiments/akt/results/modal-junyi-main-selected-t4-20261112-06/independent-stop-confirmation.json`. Tải/kiểm archive cũ tiếp tục bằng CPU, độc lập với profile khởi tạo mới. Không cần chờ tải hết archive cũ để đo packet không sử dụng checkpoint đó. Controller vẫn đòi hỏi xác nhận dừng. Bộ kiểm dừng đã thêm tối đa ba lần đọc trạng thái trong thời hạn cũ, đạt29ca kiểm.
