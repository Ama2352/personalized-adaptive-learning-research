# ROOT duyệt dispatch continuous control A0

10/11/2026. Materialization đã đạt qua owned operation. ROOT đối chiếu toàn bộ config/AUTH/request với dry đã duyệt, SHA config và AUTH khớp request. Request thực có SHA `5c77bd7ba189dce4606bf0bcc2f9f6e197da50008cfbbfce2df38e6b29792a68`.

Ba mẫu RAM trống trước dispatch lần lượt4.839.022.592/4.838.760.448/4.851.810.304byte, vượt admission4GiB. Corpus public10×84 giữ nguyên, requested phases chính xác `select_train80` và `raw_selection10`. Root duyệt đúng một dispatch mới bằng normal entrypoint, trong phạm vi engineering đã được người dùng giao.

Training cap300s/40optimizer steps/13.440targets, main wall540s, worker560/owned580/outer600s. RSS1GiB và RAM hệ thống còn trống2GiB là điều kiện dừng. Tối đa hai model/Adam constructors,61forwards/21selection passes/1.764selection target evaluations theo trần20epochs, có fresh-best reload. Giữ cấu hình khoa học và seed theo hai review trước.

Đòi hỏi terminal selected-only complete, nguồn/runtime/data/counters đúng, prediction export đủ84targets, checkpoint reload và owned cleanup. Exit0 riêng lẻ chưa nghiệm thu. Nếu dừng vì tài nguyên hoặc lỗi, giữ logs, không tự chạy lại. Chỉ sau control được nghiệm thu mới chọn pause từ history thật và chuẩn bị parent/resume authorization riêng. Kết quả thuộc kiểm tích hợp trên corpus nhỏ, chưa là main matrix winner hoặc kết luận RQ3.
