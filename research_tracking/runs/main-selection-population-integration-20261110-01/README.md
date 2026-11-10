# Quần thể selection chuẩn trước so sánh mô hình

Helper `research_population.py` đã tích hợp vào source và chạy sáu unittest qua normal import. Lượt integration02 thực đạt trong1,130giây/20giây, đọc public corpus Main60 và engineering10. Đã dựng đủ1260targets/6learners của Main và84targets/1learner engineering. Hash K và K/y của engineering khớp độc lập full84target export A0 đã nghiệm thu. Nguồn/input trước–sau nguyên, không model, oracle, chọn winner hoặc refit. Dữ liệu gốc và model artifacts chỉ được đọc; bundle giữ pins, không sao chép corpus.

Driver01 đã chạy sáu tests nhưng dừng trước đọc corpus do gọi sai tên tham số `max_learners_per_role`; driver02 dùng API thật `max_trajectories_per_role`. Giữ cả log lỗi. Không cộng các lần chạy lại thành số test độc lập.

Candidate IO vẫn riêng trong prep. Lượt chín methods có0failures/1error tại `Opened exact file identity` trong so sánh stat/fstat trên Windows. Chưa xác định nguyên nhân hoặc sửa guard, chưa tích hợp candidate này. Các adapters đang viết đã được ngắt theo yêu cầu giảm subagent. Đây không phải nghiệm thu file admission đủ chín mô hình.

Build source hiện185files do thêm module và test. Gate183/1913 trước đó là snapshot lịch sử, cần refresh sau khi ổn định các module mới trước chạy model tiếp. Không tiêu Modal.
