# Kiểm hợp đồng simulator–AKT trên CPU

Dùng đúng28concept/84item của Paper2; không đổi simulator hoặc chạy latent environment. Response labels là chuỗi arithmetic fixture, không phải học sinh hoặc model simulator. Chỉ train168targets,1epoch≤2updates để có checkpoint fitted thật cho kỹ thuật; không dùng random weights rồi gọi fitted, không báo accuracy/mastery gain.

Reference weights1/3 chỉ để kiểm API, chưa là mastery protocol. Probes không commit history, snapshot/reset/cross-learner isolation và domain/recipe rejects phải pass. Lưu checkpoint ngoài bundle ở experiments/akt/results/<run-id>, bundle chỉ giữ hash/provenance/results. Không dùng kết quả làm bằng chứng CG-AKT có ích hoặc GPU/real-data ready.
