# Bản thảo chương kết quả và thảo luận RQ1–RQ3

## Sản phẩm

`research_tracking/reports/THESIS_RESULTS_DISCUSSION_DRAFT_20261117.md` là bản thảo học thuật liền mạch từ ngữ cảnh Paper1/Paper2, cơ chế RQ1, ba bẫy RQ2 đến tiến trình đánh giá CG-AKT. File mới tổng hợp ba RQ, giữ các bản thảo cơ chế/phương pháp ngày 08–09/11 làm nguồn chuyên sâu. Đề cương PDF thật năm trang đã được đọc lại, kiểm SHA và phần sprint/deliverable.

Bản thảo có bảng chéo RQ1, ba caption SVG nghiên cứu đã lưu và bảng lifecycle 11 cấu hình Grade10/Junyi. Phần temperature A0/A1 dùng metadata nghiệm thu sau khi đọc lại artifact Drive. A2/A3 mới có suy luận calibration, fit và đánh giá độc lập vẫn mở. Giá trị Log Loss trước/sau thuộc chính cohort fit temperature.

## Kiểm và giới hạn

`verify_draft.py` kiểm số từ hiển thị, toàn bộ liên kết local, đúng 11 hàng cấu hình, các giá trị temperature/Log Loss và coverage calibration theo JSON đã nghiệm thu. `QA.json` cùng `SOURCES.json` giữ kết quả và SHA của các input nhỏ. `CLAIM_SOURCE_MAP.json` nối từng nhóm phát biểu với nguồn. Mọi đoạn kết quả có citation, bảng được nối nguồn ngay sau phần giải thích.

Lượt viết không chạy thí nghiệm, training, bootstrap mới, GPU, Modal CPU, tải output lớn hoặc mở Holdout. Bản thảo đã nối nghiệm thu thống kê v2 của nhánh khác, chạy hàm gốc trên seed outcomes và tái lập chính xác toàn bộ 117 phép so sánh. Version thư viện lịch sử chưa đủ pin, môi trường hiện hành cho cùng kết quả số. Phạm vi là tái lập thống kê từ outcomes đã lưu. Bản thảo chưa đóng RQ hay sprint. Vòng kín fitted, baseline matched và các điều kiện noise/history/support được giữ là công việc nghiên cứu tiếp theo. Đây là bản viết có thể chuyển sang Word/LaTeX sau chỉnh biên tập và bổ sung kết quả còn thiếu.
