# RQ2 — tái kiểm nguồn đồ thị trên10khối mô phỏng mới

Ngày10/11/2026. Đơn vị so sánh là paired seed block, không120người học độc lập.

## Câu hỏi và thiết kế

Phép kiểm tiếp nối E9 bằng10block21010–21019 mới, ba mức khởi tạo và hai mức lambda0/0,55. Giữ G_env và G_controller expert31, chỉ thay G_estimator expert31/learned31. S=P=True và L=False. Learned artifact/topology giống E9, không có10đồ thị học độc lập.

Y là trung bình trên28concept của theta cuối trừ base ban đầu. Q(a,lambda)=Y_expert−Y_learned. K(a)=Q(a,0,55)−Q(a,0). Đây là controlled simulator interaction contrast. Không thiết kế pre/post DiD trên người học và không có giả định parallel trends cho dữ liệu người thật.

## Kết quả mô tả

## Chặng 15. Kiểm lại đối chứng đồ thị trên mười khối mô phỏng mới

Ba khối trước cho thấy thay đồ thị trong bộ ước lượng có thể đổi đường đi ngay cả khi cơ chế phạt thiếu tiên quyết không hoạt động. Tuy nhiên, ba trường hợp còn ít và dùng lại trạng thái cũ. Nhóm tiếp tục một phép kiểm với mười khối khởi tạo mới đã định trước, giữ cùng trạng thái ban đầu và cùng chuỗi số ngẫu nhiên trong từng cặp so sánh.

Mỗi khối có ba mức khởi tạo1000,1150,1300, hai nguồn đồ thị và hai mức cơ chế phạt. Tổng cộng120ca, mỗi ca120lượt, đã hoàn tất. Đồ thị trong môi trường và bộ chọn bài giữ nguyên. Chỉ nguồn đồ thị trong bộ ước lượng thay giữa đồ thị chuyên gia và một đồ thị31cạnh được ước lượng từ dữ liệu huấn luyện. Hai đường tín hiệu và điều chỉnh theo cha cùng bật, điều chỉnh cục bộ tắt. Đây là một đồ thị học được cố định, chưa đại diện cho mọi đồ thị học từ dữ liệu.

Để biết chênh lệch giữa hai đồ thị có thực sự đi qua cơ chế phạt hay không, trước hết lấy mức tăng kiến thức trung bình của đồ thị chuyên gia trừ đồ thị học được. Sau đó đối chiếu chênh lệch này giữa lúc bật và lúc tắt cơ chế phạt. Đại lượng thu được diễn tả phần thay đổi của chênh lệch khi cơ chế được bật, theo thang Elo của simulator.

| Mức khởi tạo | Trung bình | Khoảng quan sát | Số block dương / âm / bằng0 |
|---|---:|---|---|
| 1000 | +0.004496 | -0.069250 đến +0.095294 | 6 / 4 / 0 |
| 1150 | +0.024530 | -0.004716 đến +0.079790 | 8 / 2 / 0 |
| 1300 | +0.000000 | +0.000000 đến +0.000000 | 0 / 0 / 10 |

Ở mức1000 và1150, phần thay đổi có cả dấu dương lẫn âm giữa các khối. Trung bình dương vẫn cần được đọc cùng những trường hợp âm và độ phân tán. Đây là thống kê mô tả trên mười khối, chưa có kiểm định hoặc khoảng tin cậy để kết luận ưu thế ổn định.

Ở mức1300, phần thay đổi bằng0 trong cả mười khối. Đây là đối chứng bất hoạt đã được dự kiến từ điều kiện của simulator. Đồng thời, chênh lệch trực tiếp giữa hai đồ thị vẫn khác0 và có cả hai dấu. Vì vậy, khác biệt do đổi nguồn đồ thị còn có thể đi qua các đường khác ngoài riêng cơ chế phạt thiếu tiên quyết. Kết quả chưa tách riêng vai trò của tín hiệu đồ thị, điều chỉnh theo cha và mức thử thách của câu được chọn.

Cả60cặp so sánh đổi chuỗi câu hỏi, với4936/7200vị trí khác câu. Sau khi đường đi phân kỳ, cùng số thứ tự không bảo đảm cùng câu và cùng lịch sử, nên chưa dùng những vị trí này để so sai số dự báo trên cùng targets.

Phép kiểm mới củng cố chẩn đoán cần tách nguồn đồ thị, năng lực khởi tạo và cơ chế môi trường. Nó cũng cho thấy dấu hiệu ở ba khối cũ chưa đủ để khái quát. Phần còn thiếu là thống kê theo đơn vị khối, khảo sát thêm chất lượng đồ thị và các so sánh chính của mô hình mới. Chưa RQ nào hoàn tất.

## Kiểm đầy đủ và khôi phục

Logical120worlds/14400responses gồm parent61 và child59. Physical121constructors/14430responses có30lượt replay. F062 initial snapshot và30dòng observable/oracle khớp chính xác trước khi chạy bước31. Giữ failure parent và không đổi ledger cũ.20highcontrols đầy đủ. Saved10base/U được tái sử dụng, recovery không sinhRNGdraw mới.

## Giới hạn

Mười block chưa xác lập kết luận tổng quát về năng lực. Các lượt thời gian trong một trajectory có tương quan. Một learned artifact và một biến thể GAM chưa chứng minh edge truth, confidence calibration, hiệu quả neural/Junyi hoặc instructional benefit. Không pooling ba block E9 với mười block mới. K1300=0 là negative control được cơ chế dự kiến. Chưa tính CI, p-value hoặc hiệu chỉnh multiple comparisons trong đợt xuất bản này.

## Bằng chứng

[Bundle recovery](../runs/rq2-fresh-graph-recovery-20261110-01/README.md) giữ actual receipts và nguồn. [Bundle phân tích](../runs/rq2-fresh-graph-source-analysis-20261110-01/README.md) giữ dữ liệu mô tả, review độc lập và bản báo cáo. Rawtraces giữ nguyên trong experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03 cùng parent02. Đã kiểm lại đủ60Q,30K,20highcontrols và60trajectory pairs. Các đường dẫn kỹ thuật không đưa vào bản HTML dành cho GVHD.
