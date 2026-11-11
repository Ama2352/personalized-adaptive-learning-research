# Sửa đóng gói nguồn cho corpus đã ghim danh tính

Lượt A0 engineering01 đã dừng trước khi tạo model. Corpus cũ ghi đúng SHA của notebook mô phỏng Paper2, nhưng bộ đóng gói đã viết lại cả notebook vốn không có outputs. Vì vậy actual selected guard từ chối đối chiếu nguồn. Đây là lỗi đóng gói của agent, không là lỗi dữ liệu hoặc bằng chứng cần đổi corpus.

Đã sửa `scripts/akt/build_colab_bundle.py` để giữ nguyên bytes của notebook không có outputs và execution_count. Notebook còn kết quả thực thi vẫn được làm sạch ở bản sao. Notebook mô phỏng Paper2 cần cho corpus có27cell,0outputs và0execution_count, dung lượng69.017bytes. Dataset, corpus và các notebook gốc giữ nguyên.

Đã thêm ca hồi quy bảo vệ byte identity và đối chiếu nguồn corpus. Bộ kiểm đóng gói local đạt14/14 với `.venv`, basetemp trong vùng artifacts. Lượt kiểm đầu giữ log, có một assert cũ cần cập nhật và các lỗi tạo thư mục tạm ngoài vùng được ghi. Không cài thư viện global.

`source-package-correction.json` ghi gói nguồn mới và xác nhận cả13nguồn của corpus khớp. Gate CPU đầy đủ đã đạt1.993ca trên gói trước, còn gói đã sửa cần Gate mới dự kiến1.994ca. Các file Gate mới và kết quả training tiếp theo được ghi riêng, không sửa hồ sơ cũ.
