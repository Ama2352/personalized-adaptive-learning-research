# Kết quả và tiến độ KLTN đến 16/11/2026

KLTN kế thừa hai paper về chọn bài và dự báo kiến thức, cùng đối chứng BKT/GAM-KT. Mục tiêu là tìm hiểu vì sao sơ đồ kiến thức cần học trước–sau chưa giúp người học tiến bộ rõ rệt, rồi kiểm chứng giải pháp CG-AKT.

**Đã có kết quả chẩn đoán và 4 model Junyi hoàn tất huấn luyện. Hiệu quả của CG-AKT đối với kết quả học còn chờ kiểm chứng độc lập.**

## 07–12/11 — Chẩn đoán kế thừa Paper 1 và Paper 2

- Đã chỉ ra điều kiện khiến số lần quay lại chương luôn bằng 0. Dưới luật quên đồng nhất, gain không âm và không luyện thêm, phần tăng điểm năng lực trung bình sau 14 ngày bằng 43,17% cuối buổi.
- Đối chiếu GAM-KT với gói bổ sung đồ thị trên 1.080 cặp trạng thái mô phỏng có 964 lần đổi xác suất dự báo, 90 lần đổi đánh giá thành thạo, 60 lần đổi tập chủ đề đủ điều kiện và 22 lần đổi gợi ý chủ đề xem trước. Đây là bốn số đo riêng trên cùng mẫu pilot, chưa đánh giá AKT.
- Có 120 lượt mô phỏng có đối chứng để tách năng lực ban đầu và cơ chế tiên quyết. Khác biệt giữa các nhóm còn bất định.
- Kiểm 13,35 triệu tương tác Junyi cho thấy 100/976 quan hệ chưa gặp lịch sử tiên quyết phù hợp trong đầu vào. Số đo này mô tả độ phủ. Độ đúng của cạnh cần kiểm riêng.

## 12–16/11 — Hiện thực và huấn luyện giải pháp

| Phiên bản | Thành phần |
|---|---|
| A0 | AKT không đồ thị |
| A1 | Đồ thị cố định |
| A2 | Độ tin cậy theo cạnh |
| A3 | Độ tin cậy cạnh và cổng điều tiết, có thể tắt đồ thị |

Junyi đã chọn checkpoint và refit đủ 9 epoch cho bốn phiên bản, trên 142.621 người học với 14,95 triệu target tương tác mỗi epoch. Phạm vi là một phép chia Development và graph expert. Model, checkpoint và log đã lưu, nghiệm thu.

Grade10 là mô phỏng Toán 10 có 28 khái niệm. Có checkpoint đã chọn cho 7 điều kiện trên 60 người học mô phỏng, còn refit và đánh giá. Hiệu chỉnh xác suất, so sánh dự báo độc lập và kết quả học vòng kín còn thiếu.

## Còn gì để trả lời trọn vẹn ba RQ?

1. RQ1 cần kiểm dự báo quanh ngưỡng thành thạo và tác động từ chọn bài đến tiến bộ.
2. RQ2 cần kiểm graph nhiễu, lịch sử, nhóm người học và ảnh hưởng thứ tự luyện Junyi.
3. RQ3 cần so A0–A3 trong Grade10 có cạnh thật/nhiễu, đánh giá cả trường hợp cổng tắt đồ thị.

Đối chứng SAKT/GKT, demo và bản thảo luận văn còn trong công việc phải hoàn thiện.

Nguồn là hai paper RIVF 2026, log chẩn đoán 07–12/11 và nghiệm thu training 12–16/11/2026. Số liệu chẩn đoán là thăm dò có điều kiện. Truy vết nguồn từng claim trong [rà soát RQ1–RQ2](../../../reports/RQ12_COMPLETION_REVIEW_20261116.md) và [đối chiếu training](../../../reports/TRAINING_RQ_SCOPE_REVIEW_20261116.md).
