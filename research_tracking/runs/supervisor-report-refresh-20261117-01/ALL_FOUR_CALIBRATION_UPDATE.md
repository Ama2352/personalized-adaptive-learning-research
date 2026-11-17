# Chốt báo cáo khi cả bốn lượt tính dự báo hoàn tất

Bản báo cáo hiện hành ngày17/11 đã cập nhật cho đủ A0–A3. Mỗi model có1.621.484xác suất/15.847người học,0OOV/28.653window. Đọc trực tiếp bốn GPU_RESULT01 và bốn REQUEST_A*_GPU01 xác nhận statusSTAGE_COMMITTED, cùng cache/source/population/budget. Worker durations làm tròn58/42/42/48giây. Các con số này mô tả inference của model đã refit, chưa phải kết quả chất lượng dự báo trên tập đánh giá độc lập.

Đã giải thích rõ vai trò calibration10 của outer-fold4 bằng lời mô tả nhóm người học dành riêng. Phạm vi AKT hiện một phép chia phát triển. BKT/GAM-KT5fold aggregate còn cần lấy đúng phần paired trước so sánh. Bước ngày17/11 dùng các model đã refit trước đó để tính dự báo và tìm hiệu chỉnh. CPU join/fit còn chờ nghiệm thu tại thời điểm chốt, không báo hoàn tất RQ3 hoặc cải thiện CG-AKT.

Mốc diễn tiến, bảng A0–A3, Sprint4 và việc tiếp theo được cập nhật đồng bộ. Giữ mô tả A0 NVMLmean6.2/max43 từ55mẫu, có giới hạn chưa50%; không đưa hiệu suất GPU thành kết luận nghiên cứu. Không thêm figure vì trọng tâm là tiến độ tạo đủ dữ liệu cho đánh giá. SVG RQ1 và các phát hiện RQ1/RQ2 giữ nguyên.

`QA05.json` là kiểm hiện hành, dùng `check_calibration_update.py` và các metadata source nhỏ. Kiểm cấu trúc HTML/ID/anchor, sự nhất quán hai report, cùng inputs/execution giữa bốn request và làm tròn số liệu đều PASS. Không mở browser/preview, chưa kiểm trực quan mới. Checker nhập Page/digest từ check_a0_update.py mà không chạy checker A0 cũ.

QA04/MANIFEST04/A0_CALIBRATION_UPDATE ghi lượt audit nháp A0 trước khi A1–A3 hoàn tất trong cùng phiên, được kế tiếp bằng QA05/MANIFEST05. Bản reader chỉ phát hành một lần sau khi đủ bốn kết quả. Checker QA04 có các câu trạng thái của nháp cũ và không dùng nghiệm thu bản reader hiện hành. Các nguồn experiment gốc không bị sửa hoặc sao chép predictions về PC.
