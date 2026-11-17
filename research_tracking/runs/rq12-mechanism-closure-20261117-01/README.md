# Khép ba luận điểm cơ chế của RQ1–RQ2

Ngày 17/11/2026. Đây là gói chẩn đoán cơ chế. Bằng chứng về re-entry và lịch sử quan sát được kế thừa từ các bundle đã nghiệm thu. Phần bổ sung gọi trực tiếp hai hàm nguồn đã đóng của Paper2 trên trạng thái nhỏ, không chạy trajectory, không tăng số mẫu nghiên cứu.

## 1. Giữ lại sau 14 ngày đang đo thêm điều gì

Paper2 lưu trạng thái mỗi khái niệm dưới dạng nền ban đầu `b`, trạng thái khi luyện gần nhất và thời điểm luyện gần nhất. Hàm `theta_at` trả phần tăng so với nền, suy giảm theo `exp(−0,06 × số ngày)`. Nếu khái niệm chưa luyện, trạng thái giữ bằng nền ban đầu.

Đặt T là thời điểm kết thúc lượt luyện. Với cùng tốc độ quên cho mọi khái niệm, phần tăng không âm và không luyện thêm sau T, hàm nguồn cho

`theta_c(T+14) − b_c = exp(−0,06×14) × [theta_c(T) − b_c]`.

Lấy trung bình hai vế cho kết quả giữ lại bằng 0,4317105234 lần phần tăng cuối lượt. Điều này vẫn đúng khi các khái niệm được luyện lần cuối vào các ngày khác nhau. So sánh hai chính sách trên cùng người học giữ nguyên nền vì vậy cho cùng thứ tự xếp hạng giữa final net mean-theta gain và retained net mean-theta gain.

Lượt kiểm mới trích AST đúng `theta_at` và `elo_probability` từ notebook SHA đã pin, kiểm AST trùng source excerpt lịch sử rồi gọi các hàm đó. Không thực thi nguyên cell hoặc notebook. Bốn khái niệm có tuổi luyện lần lượt 0, 1, 19 ngày và chưa luyện cho sai số semigroup lớn nhất 2,274×10⁻¹³ Elo. Cùng hai trạng thái 28 khái niệm A/B đã khai báo ngày08/11 được đọc lại bằng hàm native.

| Trạng thái dựng | Tăng theta cuối lượt | Tăng theta sau 14 ngày | Tăng soft mastery cuối lượt | Tăng soft mastery sau 14 ngày |
|---|---:|---:|---:|---:|
| A | 8,928571429 | 3,854558245 | 0,011828930 | 0,005502275 |
| B | 16,071428571 | 6,938204841 | 0,017162644 | 0,005120524 |

Thứ tự theta vẫn là B>A. Thứ tự soft mastery đổi từ B>A sang A>B do phép biến đổi xác suất phi tuyến quanh ngưỡng. Hai trạng thái được dựng để kiểm readout, chưa chứng minh chính sách nào tạo được chúng. [Bảng số đọc bằng native](cached_readout_native.csv), [kiểm last-seen lệch nhau](native_semigroup.csv).

**Luận điểm được khép.** Trong các điều kiện trên, retained net mean-theta gain không cung cấp thứ tự chính sách mới so với final net mean-theta gain. Practice order trước T vẫn có thể làm theta(T) khác nhau. Soft/hard mastery, tốc độ quên không đồng nhất hoặc có luyện sau T cần phân tích riêng. Kết quả này không kết luận mọi retention metric dư thừa.

## 2. Cùng lịch sử có thể che khuất khác biệt kiến thức thật

Nguồn cached fresh120 đã được kiểm chéo ngày17/11. Ở mức khởi tạo1150, có20 cặp thay núm phạt tiên quyết0→0,55, giữ đúng block và nguồn graph. Cả20 cặp có cùng chuỗi120 câu hỏi, đáp án và xác suất KT. Tuy nhiên, mức tăng năng lực ẩn đều giảm, chênh lệch từ−0,257317 đến−0,018351 Elo.

Với một KT chỉ nhận lịch sử, cố định weights, initialization, preprocessing và RNG, hai lịch sử giống nhau tạo cùng đầu vào ở từng bước. Dùng quy nạp qua hàm cập nhật state, đầu ra KT cũng giống nhau. Vì vậy mô hình dạng này không thể phân biệt hai mức gain ẩn chỉ từ những quan sát đã giữ nguyên. Đây là giới hạn quan sát trong cặp môi trường đó. Thông tin ngoại sinh hoặc lịch sử dài hơn có thể phá tính không phân biệt này.

**Luận điểm được khép.** Trong20 cặp đã lưu tại1150, thay núm cơ chế học làm latent outcome đổi khi hệ thống nhận cùng lịch sử. Chưa chứng minh mọi learner, horizon hoặc mô hình đều có hiện tượng đó. Phép ghép cặp không tự cấp một DiD nhận dạng lợi ích causal của graph. [Checker độc lập và mẫu số](../rq12-existing-evidence-20261117-01/SECONDARY_CHECK.json), [60 cặp quan sát](../rq12-existing-evidence-20261117-01/lambda_observable_pairs.csv).

## 3. Re-entry bằng0 có điều kiện controller rõ ràng

Proof theo PDF Paper1 đã đủ. Nếu graph là DAG nội chương, chỉ cập nhật khái niệm đang chọn, khái niệm đạt ngưỡng rời tập ready, không quên/reset và controller tiếp tục chương đang học khi còn node ready, mỗi chương được học trong một khối liên tiếp. Kết quả re-entry0 suy ra từ các điều kiện này.

Khi một cạnh ngoại chương còn chặn node trong chương đang học, phản ví dụ đã kiểm tạo chuỗi A→B→A dù controller vẫn tuân thủ continuity. Vì vậy proof nội chương không được áp tự động cho graph liên chương. PDF Paper1 tiếp tục là nguồn lịch sử có thẩm quyền. [Proof và điều kiện](../../reports/paper1_reentry_mechanism_20261109.md), [bốn fixture đã nghiệm thu](../paper1-reentry-mechanism-20261109-01/result.json).

## Nghiệm thu và sử dụng trong luận văn

- Reproduction kế thừa số liệu lịch sử Paper1/Paper2, không thay kết quả đã công bố.
- Diagnosis khép các phát biểu có điều kiện ở trên. Lượt native nhỏ bổ sung xác nhận đường thực thi cho công thức retention đã chứng minh.
- New research về calibration quanh ngưỡng, fitted action/outcome, noise/history/support và predictive order-controls Junyi vẫn còn mở. Ba claim hẹp không đồng nghĩa hoàn thành RQ1 hoặc RQ2 hay toàn Sprint1/Sprint5.

`ACCEPTANCE.json` lưu120 lần gọi native theta,224 lần gọi response curve,0 trajectory và SHA nguồn trước/sau. `check_native_retention.py` dùng stdlib cùng source đã có, không thêm dependency. Dùng `.venv/Scripts/python.exe -B` để chạy script trong một bundle mới. Script từ chối ghi đè output cũ.

`MANIFEST.json` giữ nguồn, PDF đề cương đã đọc lại, input cached và output. Không có cloud/GPU, real-Junyi, Holdout, training, chọn tham số hoặc thay simulator trong lượt này.
