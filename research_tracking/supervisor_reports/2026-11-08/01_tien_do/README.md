# Báo cáo tiến độ KLTN — ngày 08/11/2026

**Đọc theo thứ tự dưới đây.** Đây là gói báo cáo tiến độ, chưa phải kết luận hoàn thành ba câu hỏi nghiên cứu.

1. [BAO_CAO.md](BAO_CAO.md): nội dung chính để trao đổi với GVHD — đã đạt gì, ý nghĩa và phần còn thiếu.
2. [KET_QUA_NGHIEN_CUU.ipynb](KET_QUA_NGHIEN_CUU.ipynb): bảng, biểu đồ và diễn giải theo RQ; mở bằng Colab CPU hoặc VS Code. Không cần training lại.
3. [BANG_CHUNG.md](BANG_CHUNG.md): tra từng thành quả đến file kết quả, mã thực thi và log; tách đã xử lý/chưa xử lý.
4. `tai_lieu/`: các phân tích đọc kèm, protocol và bản sao JSON kiểm chứng. Không cần tìm giữa toàn bộ thư mục nghiên cứu.
5. [NGUON.json](NGUON.json): nguồn gốc, SHA trước/sau và cách sao chép; dùng khi đối chiếu tính toàn vẹn.

## Mở notebook trên Colab

Mở Google Colab → **File → Upload notebook**, chọn `KET_QUA_NGHIEN_CUU.ipynb` trong thư mục này. Giữ runtime **CPU**, rồi chọn **Runtime → Run all**. Notebook tự chứa số liệu tổng hợp, không yêu cầu tải dataset, cài thư viện hoặc kết nối Modal. Để kiểm nguồn đầy đủ, dùng các đường dẫn repository trong phần nguồn của notebook.

Notebook đã lưu sẵn bảng và 4 biểu đồ SVG. Cả 8 cell tính toán đã được chạy local và đối chiếu lại kết quả; chưa kiểm trực tiếp giao diện/runtime Colab. [Biên bản kiểm notebook](KIEM_TRA_NOTEBOOK.json), [danh mục nguồn notebook](tai_lieu/nguon_notebook.json).

## Phạm vi thời gian của báo cáo

Snapshot tổng hợp kết quả đã có đến ngày 08/11, gồm kết quả lịch sử và các batch mới. Không khẳng định tất cả thí nghiệm đều chạy trong ngày 08/11. Báo cáo kỹ thuật nền là revision6, commit `8b6487c`; corpus là commit `1990d4c`, replay lịch sử là `8f95fd6`. Những phần đang viết chưa được coi là đã nghiệm thu.

## Gói này có tự mang toàn bộ thí nghiệm không?

Không. Notebook mang số liệu tổng hợp đã ghim để xem/chạy báo cáo độc lập. Tài liệu đọc kèm có trong gói; log đầy đủ, mã nguồn đóng băng và kết quả chi tiết vẫn ở các run gốc được dẫn trong BANG_CHUNG. Chỉ gửi riêng thư mục này sẽ không mang theo các liên kết ra repository. Muốn kiểm toán toàn bộ, cần checkout repository và artifacts tương ứng. Không chép dataset, checkpoint hay Holdout vào gói.
