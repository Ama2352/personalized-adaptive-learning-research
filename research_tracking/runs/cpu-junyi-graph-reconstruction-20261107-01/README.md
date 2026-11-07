# Tái dựng SCC graph bằng nguồn Paper2

Dùng catalog hiện tại và chọn lọc đúng6AST statements của SCC-removal trong notebook Paper2. Không chạy notebook toàn bộ, không đọc learner logs hoặc outcomes. Graph.json chứa nodes/raw edges/removed edges/corrected DAG và hashes. Self-loops được loại trước theo preprocessing nguồn.

Đây là graph version mới tái dựng từ bytes hiện có. Counts khớp979→976 là bằng chứng consistency với lịch sử, chưa chứng minh identical historical edge bytes vì artifact cũ không đóng băng raw Junyi hashes. Không tự thay graph của experiment lịch sử hoặc benchmark đã frozen. Phải chốt graph version cho experiment tương lai.
