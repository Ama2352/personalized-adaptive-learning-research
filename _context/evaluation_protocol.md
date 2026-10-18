# Giao thức đánh giá

## Chia và fit

- Phân vùng toàn cục theo học sinh: 80% Development, 20% holdout Test; assignment seed 42. CV gồm 5 fold student-disjoint bên trong Development.
- Pilot `num_fits` chỉ dùng Development; lựa chọn đã đóng băng là 1. Không dùng Test để tuning.
- Fit một BKT độc lập cho mỗi exercise, dùng riêng các tương tác của phần train trong split/fold tương ứng.

## Dự đoán tuần tự

Với mỗi học sinh và exercise, sort theo `time_done`, sau đó `source_row` để phá timestamp tie một cách xác định. Dự đoán tương tác `t` chỉ được dùng state từ các tương tác trước đó (`t−1` trở về trước). Sau khi tạo dự đoán, phản hồi ở `t` có thể cập nhật state cho tương tác tiếp theo.

## Metric và coverage

Báo AUC-ROC, Log Loss, Brier, ECE 15 bin độ rộng bằng nhau và Accuracy với ngưỡng 0,5. Coverage là số dòng có dự đoán BKT fitted chia tổng số dòng trong nhóm. Exercise không thấy trong train được báo là unseen, có dự đoán null, bị loại khỏi denominator các metric của mô hình; không thay bằng xác suất fallback rồi gọi là dự đoán fitted.

Báo thêm subgroup `suggested`/`non-suggested`. Nhóm hiếm được xác định theo số học sinh Development trong từng exercise, sau đó báo coverage theo nhóm support. CV tổng hợp metric trung bình và độ lệch chuẩn mẫu giữa 5 fold; Test được đánh giá một lần sau final refit và không quay lại tuning.
