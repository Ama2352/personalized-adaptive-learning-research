# Phép đối chiếu RQ1 từ 120 readout đã có

## Mục tiêu và quần thể

Root chọn một phân tích mô tả từ dữ liệu đã lưu để kiểm khoảng cách giữa quyết định thành thạo của estimator và tiêu chí latent trong simulator. Nhánh này dùng đúng pilot observer03 đã nghiệm thu, key `(21000, PG, graph_on=False, mechanism_on=False)`, 120 thời điểm của khái niệm đang được hỏi. History đã được chọn từ pilot đo chi phí trước phân tích truth. Phân tích không chọn seed hoặc điểm cắt theo kết quả truth.

Bản ON được dùng đúng một lần. Bản OFF chỉ kiểm tính nhất quán của readout và state, không tăng quần thể. Fixed-history RQDIAG12 khác seed, clock và treatment nên không được ghép vào CPU09. Pilot này là một witness hẹp, chưa cung cấp population của RQDIAG23 hoặc so sánh graph.

## Định nghĩa đóng trước khi đọc oracle rows

Giữ đúng ngưỡng từ notebook nguồn353f487a và replay helper337677c1. Native M bằng `theta_est >= 1250.0 and pi_task_stored <= 0.55`. Tiêu chí latent bằng `CPU09.theta_before >= 1250.0`, thuộc khái niệm đang hỏi trước current-response update. Dùng so sánh binary64 inclusive nguyên bản, không làm tròn hoặc thêm epsilon. Stored pi là đầu vào của native gate, không đổi thành decayed pi. Đây là tiêu chí thành thạo do simulator định nghĩa.

Đầu ra chính là bảng2×2 của native M so với tiêu chí latent, giữ cả ô bằng0. Đầu ra phụ là bảng của theta gate riêng so với latent, cùng số thời điểm theta gate đạt nhưng precision gate chưa đạt, phân theo latent. Giữ bảng hàng120 đầy đủ để kiểm lại. Không tạo metric calibration của xác suất đáp án từ những boolean này.

## Điều kiện ghép bắt buộc

Kiểm SHA của manifest observer, ON/OFF, actual outer03 và receipt của pilot. Outer phải accepted, errors rỗng, Job0, nguồn trước/sau bằng nhau, môi trường đã khôi phục. Hai readout ON/OFF phải khớp các trường khoa học và initial/final state. Chọn ON sau kiểm integrity.

Dùng lại strict reader `analyze_rq2_cached_mechanism01.py` SHA8590381c85fe1e58df4a305c8bf4a33ebd9900d0fa8ffb1f1a93868fb56f1311. Reader phải kiểm CRC, manifest/grid và đủ14.400rows gốc, rồi lấy đúng120rows đã chọn trước. Ghim cả contract cache, provenance, topology/bank và gzip theo những manifest đã đóng. Reader chỉ chạy parser/validator stdlib, không gọi entrypoint replay hoặc import mô hình.

Khóa ghép phải giữ key history và step0–119. Đối chiếu đủ selected concept/question/difficulty qua bank, prediction bits, thứ tự và timestamp. Clock gốc UTC2026-01-01 cộng6h mỗi bước, thay bằng72h ở bước dương chia hết28. Ba trường theta_gate/stored_pi_gate/native_M phải tự tính lại khớp hoàn toàn. Thiếu/đúp khóa, khác quần thể, source, P hoặc clock phải reject toàn lượt, giữ log lỗi. Không ghép theo ordinal đơn thuần hoặc tự bỏ hàng không khớp.

## Tài nguyên và kiểm nghiệm

Chỉ stdlib trong `.venv`. Pure tests dùng fixture dựng tay cho inclusive1250/.55, sai key/query/P/time, OFF/ON drift và thiếu/đúp hàng. Pure tối đa8giây whole, analysis tối đa15giây whole, gồm cleanup và readback. Profile nhẹ dự kiến worker256MiB, free floor512MiB, admission1GiB, cần Root review source cụ thể trước dispatch. Bounded compressed1MiB/decoded8MiB/line8192B/14.400rows. Đầu ra nhỏ tối đa1MiB tổng, có joined120, summary, input/output identities, actual counters và run receipt. Không sinh policy/world/RNG, không forward/backward/optimizer hoặc import Torch/NumPy/Pandas.

Root sẽ review script/packet/hash và workload cụ thể trước từng lệnh. Gói này không tự khởi chạy từ việc có contract. Giữ lịch sử và các vùng dữ liệu được bảo vệ. Full14.400native readouts, nhiều profile/arms và RQ completion tiếp tục là công việc còn thiếu.
