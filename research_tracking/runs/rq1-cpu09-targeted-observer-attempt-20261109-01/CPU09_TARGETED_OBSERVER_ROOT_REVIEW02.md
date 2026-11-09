# Duyệt lại sau sửa khôi phục observer

Ngày 09/11/2026. Review02 thay các source pins và số kiểm dựng tay trong review01. Allocation vẫn là một lần native có trần tổng 60 giây, worker 53 giây, owned operation tối đa 57 giây và cleanup reserve 3 giây. Scope vẫn là một lịch sử 120 bước, hai policy mới và 240 updates.

Worker `23698defe20f5cccb5f8f70bc100c3709c353f7cb6e91cf0e12405b315814660`, controller `c892124ff8efe531374a95fa770a019c91418e14c1a7d12eb5a50a8a5f438e86`, contract `7f8f8b16371ea95fb2d99642f613b83896a54f3ef61a58a99ed5e423d693e163`.

Root và reviewer độc lập đã đọc logic rollback từng attribute, giữ exception gốc và ghi lỗi cleanup riêng. Năm kiểm dựng tay gồm ba kiểm gốc và hai tình huống failure mới. Chúng chạy trước native trong cùng allocation. Old source và review01 được giữ trong snapshot trước sửa. Các tiêu chí parity, source/input, RAM, Job0 và monitor terminal của review01 tiếp tục áp dụng.

Trước dispatch local RAM khả dụng đã được đọc là khoảng 3,33 GB. Controller và worker còn kiểm mức tối thiểu 2 GiB trong operation. Nếu từ chối thì giữ failure, dừng allocation này và đánh giá nguyên nhân bằng evidence.
