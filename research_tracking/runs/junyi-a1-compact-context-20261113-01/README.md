# A1 — thử biểu diễn ngữ cảnh đồ thị gọn trên CPU

## Mục tiêu và kết quả ngày 13/11/2026

Sau lượt T4 chỉ tăng thông lượng 1,26 lần, kiểm tiếp hướng loại phần tạo cây audit Python khỏi đường tính toán mỗi batch. Prototype tạo hai mảng gồm message đồ thị FP32 và mặt nạ vị trí áp dụng. Alpha vẫn thuộc model và được học trong forward. Chưa sửa trainer, adapter, backbone hoặc checkpoint.

Đọc đúng shard đầu của TRAIN80 đã có cache, chọn seed43 với 128 cửa sổ, 102 learner, 5.527 target và 2.246 target có quan sát prerequisite. Vocabulary 717 exercise, graph đã xử lý 976 cạnh. Không đọc sự kiện selection, calibration hoặc Holdout. Metadata phân vai được dùng để dựng đúng session.

| Đường chuẩn bị context và bốn checksum | Thời gian trung bình |
|---|---:|
| Reference hiện hành, đầy đủ evidence và helper JSON mới | 0,825750 giây |
| Prototype mảng gọn, gồm dựng message và khóa input | 0,250777 giây |

Hai lượt mỗi bản theo thứ tự reference, compact, compact, reference. Tăng tốc riêng phần đã đo là 3,293 lần, giảm thời gian khoảng 69,6%. Toàn lệnh kiểm 7,99 giây, đỉnh RSS 231.378.944 byte, khoảng 220,7 MiB, 0 USD Modal.

## Bằng chứng đúng ngữ nghĩa

Đối chiếu mọi vị trí trong hai mảng 128 × 200 với message tính từ evidence cũ, sau cùng phép chuyển FP32 như forward A1. Giá trị message và mặt nạ khớp tuyệt đối. Target có message bằng 0 vẫn giữ mặt nạ active nếu có prerequisite được quan sát.

Giữ kiểm phase và native window trước/sau mỗi cửa sổ. Prototype chỉ đọc `prior_responses`, cập nhật response của item trước trước khi tính message hiện tại. Đổi các response nằm sau target đang xét giữ nguyên mọi message trước đó. Người học ngoài vai bị từ chối. Đổi response trong input hoặc window ID làm đổi khóa gói. Kiểm cuối xác nhận input/source pins đã đọc giữ nguyên.

Payload batch gồm header provenance, bytes của message và mặt nạ, tổng 128.389 byte trong mẫu này. Bốn checksum trên payload đã có trung bình 0,000473 giây trong 100 lần đo. Con số này chỉ tính checksum sau khi dựng payload, chưa gồm đọc cache hoặc chuẩn bị dữ liệu.

## Phạm vi nghiệm thu

Đây là prototype CPU cho A1 với confidence cố định bằng 1. Chưa tạo cache trên đĩa, chưa nối adapter/native, chưa kiểm gradient, optimizer, checkpoint/resume hoặc đo GPU. Toàn bộ graph audit chi tiết vẫn được giữ trong implementation tham chiếu. Hai representation có digest khác nhau vì định dạng khác nhau, đối chiếu đúng dựa trên giá trị và mask theo target.

Mẫu chỉ thuộc shard đầu, chưa đại diện toàn dataset. Tăng tốc 3,293 lần áp dụng riêng phần context đã đo. Chưa có căn cứ quy đổi thành thời gian epoch H100 hoặc khẳng định GPU đạt 50%. Máy có thể chịu tải khác lượt kiểm cũ, nên kết luận dựa trên đối chiếu reference/compact trong cùng tiến trình.

## Thứ tự triển khai tiếp theo

1. Nối representation gọn vào adapter/native theo một hợp đồng có version. Giữ đường tham chiếu cho kiểm đối chiếu. Tính message và mặt nạ từ input quá khứ như hiện tại, giữ alpha trong forward để gradient ở alpha0 tồn tại.
2. Khóa artifact theo dataset, phase/fold, graph, encoding, geometry cửa sổ và phiên bản builder. Cache chỉ chứa giá trị cố định theo input và graph. Ghi inventory và nghiệm thu artifact trước khi GPU sử dụng. Khóa prototype hiện chưa thay thế hợp đồng cache production.
3. Kiểm loss, xác suất, gradient, Adam/RNG và checkpoint/resume từ source2 epoch1. Nghiệm thu quần thể target, source rows, thứ tự và biên learner như pipeline hiện hành. Chưa cho phép source mới âm thầm mở checkpoint có source pin cũ.
4. Đo end-to-end trên T4 gồm data loading, context, checksum, truyền dữ liệu và optimizer. Quyết định H100 dựa vào target/giây, thời gian CPU, GPU-Util và chi phí dự kiến.

A2 có thể tái sử dụng cách đóng gói khi confidence artifact đã cố định đúng train-only. A3 có thể tính trước feature cố định cho gate, còn trọng số gate và output phụ thuộc trọng số vẫn tính trong model. Hai nhánh này chưa được kiểm trong prototype A1.

## Files bằng chứng

- `compact_context.py` chứa prototype đã chạy, tách khỏi source production.
- `benchmark_compact.py` dựng đúng roles/encoding/graph và kiểm nguồn trước đọc một shard. Chạy bằng `.venv` tại repository, giới hạn 120 giây, 1 GiB RSS. Có nguồn tham chiếu từ bundle CPU profile A1 trước.
- `result.json` giữ pins, số liệu, điều kiện kiểm và giới hạn. `component-data.csv` và `compact-context-cpu-v1.svg/.png/.pdf` giữ dữ liệu và hình độc lập. `build_figure.py` dựng lại hình.
- `manifest-final.json` giữ inventory bundle. Source helper production giữ phiên bản đã kiểm T4 ở commit b356a95, chưa thay bởi prototype.
