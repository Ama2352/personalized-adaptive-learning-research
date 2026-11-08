# Báo cáo tiến độ gửi GVHD

**Bản mới nhất:** [08/11/2026 — đợt01](2026-11-08/01_tien_do/README.md).

Đây là điểm bắt đầu cho người xem tiến độ. Các phân tích chuyên sâu vẫn ở `research_tracking/reports/`, bằng chứng gốc ở `research_tracking/runs/`; không di chuyển hoặc thay thế chúng.

## Cách lưu từ nay về sau

Mỗi ngày có một thư mục `YYYY-MM-DD/`. Nếu cùng ngày có nhiều mốc đã nghiệm thu, tạo `01_tien_do/`, `02_.../` theo thứ tự; không dùng thời gian tạo file để suy ra thời gian chạy thí nghiệm.

Mỗi gói gồm:

- `README.md`: đọc gì trước, phạm vi thời gian và cách mở notebook.
- `BAO_CAO.md`: thành quả, ý nghĩa theo RQ, phần đã/chưa xử lý và mốc tiếp theo.
- `BANG_CHUNG.md`: thành quả → file số liệu → mã/plan/log/manifest → giới hạn.
- `KET_QUA_NGHIEN_CUU.ipynb`: bảng, biểu đồ và nhận định có nguồn; chạy Colab CPU từ kết quả đã lưu, không tự training hoặc tải dữ liệu nhạy cảm.
- `tai_lieu/`: tài liệu đọc kèm và JSON cần thiết. Chỉ sao chép có mục đích; không nhân bản dataset/checkpoint/log lớn.
- `NGUON.json`: ghi nguồn, SHA trước/sau sao chép, bản sao byte-exact hay bản đọc đã chỉnh đường dẫn. Notebook ghi nguồn số liệu bên trong.

Sau khi kiểm và commit, giữ snapshot. Đợt sau chỉ bổ sung phần mới và giải thích thay đổi so với đợt trước; cập nhật link “bản mới nhất” tại đây. Không sửa kết quả lịch sử để đồng bộ cách diễn giải mới. Không tự gửi gói ra ngoài.

## Lịch sử các gói

| Ngày | Đợt | Nội dung | Loại bằng chứng |
|---|---|---|---|
|08/11/2026|[01 — Tiến độ hiện tại](2026-11-08/01_tien_do/README.md)|Chẩn đoán RQ1/RQ2, đối chứng lịch sử/năng lực, corpus đã sinh và phần RQ3 còn thiếu|Tổng hợp lịch sử và pilot có kiểm soát; chưa hoàn tất RQ|
