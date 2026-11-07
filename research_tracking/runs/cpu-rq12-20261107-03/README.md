# Chẩn đoán RQ1 và retention Paper2

Đây là bounded diagnostic trên simulator inputs lịch sử và định nghĩa nguồn được nạp bằng AST allowlist. Nguồn gốc, cell hashes và input hashes nằm trong source_provenance.json.

Cùng chuỗi item, đáp án và timestamp cho graph-free, graph-package và empty-graph package. Graph môi trường và controller giữ nguyên. Empty-graph package vẫn bật adaptation cục bộ. Mastery boolean theo đúng is_mastered nguồn, khác score>=0.5. Action là preview trên bản sao.

comparisons.json chứa mỗi seed/profile, traces.jsonl.gz chứa trace trước update. retention.json kiểm đẳng thức decay trên actual theta_at.

paper1_counterexample.json kiểm selector nguồn với DAG A1→B1→A2 và mastery được gán theo kịch bản. matched_graph.json chứa một swap giữ degree/chapter counts, chưa matching train support.

Có thể trích bằng chứng cơ chế và sự khác biệt trên các stream đã đo. Chưa là closed-loop learning-outcome comparison, chưa là causal benefit trên Junyi, chưa có CI hoặc kiểm định kết luận. Action preview trong fixed stream không phải actual served action. Seed diagnostic được công khai, không dùng lại như final unseen test.
