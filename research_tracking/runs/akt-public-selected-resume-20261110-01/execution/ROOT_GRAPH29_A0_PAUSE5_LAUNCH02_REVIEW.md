# Sửa cách nạp nguồn cho launcher CPU

Launch01 dừng sau 0,43 giây trước owned GO và trước NN vì outer gọi construct trước khi thêm repo/src vào import path. Stderr và toàn bộ attempt01 được giữ nguyên. Native output và owned worker chưa được tạo.

ROOT duyệt launcher02 thêm duy nhất repo/src vào sys.path của interpreter bằng runpy trước khi nạp outer nguyên byte. sys.argv vẫn giữ đúng tên outer và các tham số đã duyệt. Không đặt PYTHONPATH hoặc thay môi trường global. Bốn source pins, actual request, config, authorization, runtime, Gate và ngân sách parent180/lineage540 giữ nguyên. Output wrapper mới có hậu tố02, original01 được giữ.

Nghiệm thu vẫn yêu cầu toàn bộ assertion actual prefix, tài nguyên, provenance và cleanup như review đầu. Không coi lỗi import này là một lượt train.
