# Closed-loop: mô tả đường đi selector từ current-source reconstruction

**Bản thảo chẩn đoán, không causal/efficacy hoặc hoàn tất RQ1.** Original whole runner a585 vẫn thiếu; candidate d889 đã giữ exact stored legacy projection trong hai passes, không chứng minh recover original source. Metadata chỉ thuộc reconstruction mới, không backfill lịch sử.

M là explicit boolean trước bookkeeping; R là returned ready set, C là eligible candidates sau escape, B là balanced candidates; P được tính sau bookkeeping trước interact/current y. State-hash change trong bảng chỉ là khác biệt bytes state quanh selection, không learning/mastery gain.

## Toàn bộ trajectories

| Seed | Profile | Variant | Events | R→C set | R→C order only | C→B set | Selected ngoài R | Selected M=true | Hash đổi quanh select |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 20000 | PG | graph_free | 120 | 15 | 0 | 107 | 0 | 0 | 120 |
| 20000 | PG | graph_package | 120 | 12 | 0 | 107 | 0 | 0 | 120 |
| 20000 | PG | empty_graph_package | 120 | 15 | 0 | 107 | 0 | 0 | 120 |
| 20000 | PY | graph_free | 120 | 14 | 0 | 111 | 0 | 0 | 120 |
| 20000 | PY | graph_package | 120 | 13 | 0 | 111 | 0 | 0 | 120 |
| 20000 | PY | empty_graph_package | 120 | 14 | 0 | 111 | 0 | 0 | 120 |
| 20000 | PYH | graph_free | 120 | 10 | 0 | 111 | 0 | 0 | 120 |
| 20000 | PYH | graph_package | 120 | 10 | 0 | 111 | 0 | 0 | 120 |
| 20000 | PYH | empty_graph_package | 120 | 10 | 0 | 111 | 0 | 0 | 120 |
| 20001 | PG | graph_free | 120 | 12 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PG | graph_package | 120 | 11 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PG | empty_graph_package | 120 | 12 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PY | graph_free | 120 | 11 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PY | graph_package | 120 | 14 | 0 | 113 | 0 | 0 | 120 |
| 20001 | PY | empty_graph_package | 120 | 11 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PYH | graph_free | 120 | 14 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PYH | graph_package | 120 | 14 | 0 | 112 | 0 | 0 | 120 |
| 20001 | PYH | empty_graph_package | 120 | 14 | 0 | 112 | 0 | 0 | 120 |
| 20002 | PG | graph_free | 120 | 12 | 0 | 112 | 0 | 0 | 120 |
| 20002 | PG | graph_package | 120 | 10 | 0 | 113 | 0 | 0 | 120 |
| 20002 | PG | empty_graph_package | 120 | 12 | 0 | 112 | 0 | 0 | 120 |
| 20002 | PY | graph_free | 120 | 14 | 0 | 113 | 0 | 0 | 120 |
| 20002 | PY | graph_package | 120 | 13 | 0 | 113 | 0 | 0 | 120 |
| 20002 | PY | empty_graph_package | 120 | 14 | 0 | 113 | 0 | 0 | 120 |
| 20002 | PYH | graph_free | 120 | 10 | 0 | 113 | 0 | 0 | 120 |
| 20002 | PYH | graph_package | 120 | 10 | 0 | 113 | 0 | 0 | 120 |
| 20002 | PYH | empty_graph_package | 120 | 10 | 0 | 113 | 0 | 0 | 120 |

R/C/B size histograms đủ từng trajectory nằm trong [analysis.json](analysis.json); không lấy mean sizes che mất phân bố. Mọi selected thuộc B⊆C đã được kiểm trên toàn bộ rows. Selected ngoài raw R có thể là escape; selected M=true có thể là review/fallback của nguồn, không tự chứng minh lỗi hoặc vi phạm prerequisite. Empty chỉ là **empty estimator graph**: loader vẫn bind selector vào controller G chung (paper2_reference.py87–92), môi trường G giữ nguyên. Không suy R khác nhau nghĩa là controller graph bị đổi.

## Prefix có cùng toàn bộ lịch sử trước current event

Prefix chỉ còn common khi mọi actual served tuple +timestamp+y trước đó đều giống; một lần diverge thì không mở lại. Snapshot gây break vẫn có common-before=true. M/R/C/B so bằng sets, action bằng returned tuple ba trường; current label chỉ xác định prefix sau event. First action difference được lưu riêng trên toàn bộ quỹ đạo, kể cả sau label-only break.

| Seed | Profile | Candidate | Common-before | Common-after | M/R/C/B setdiff trên common-before | Tuple diff trên common-before | First break | First tuple diff |
|---|---|---|---:|---:|---|---:|---|---|
| 20000 | PG | graph_package | 62 | 61 | 0/0/0/0 | 1 | 61:served_tuple | 61:concept,question |
| 20000 | PG | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20000 | PY | graph_package | 68 | 67 | 0/0/0/0 | 1 | 67:served_tuple | 67:concept,question |
| 20000 | PY | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20000 | PYH | graph_package | 66 | 65 | 0/0/0/0 | 1 | 65:served_tuple | 65:concept,question |
| 20000 | PYH | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20001 | PG | graph_package | 24 | 23 | 0/0/0/0 | 1 | 23:served_tuple | 23:concept,question |
| 20001 | PG | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20001 | PY | graph_package | 28 | 27 | 1/1/1/1 | 1 | 27:served_tuple | 27:concept,question |
| 20001 | PY | empty_graph_package | 115 | 114 | 0/0/0/0 | 1 | 114:served_tuple | 114:concept,question |
| 20001 | PYH | graph_package | 68 | 67 | 0/0/0/0 | 1 | 67:served_tuple | 67:concept,question |
| 20001 | PYH | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20002 | PG | graph_package | 28 | 27 | 0/0/0/0 | 1 | 27:served_tuple | 27:concept,question |
| 20002 | PG | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20002 | PY | graph_package | 36 | 35 | 0/0/0/0 | 1 | 35:served_tuple | 35:concept,question |
| 20002 | PY | empty_graph_package | 120 | 120 | 0/0/0/0 | 0 | none | none |
| 20002 | PYH | graph_package | 35 | 34 | 0/0/0/0 | 1 | 34:served_tuple | 34:concept,question |
| 20002 | PYH | empty_graph_package | 84 | 83 | 0/0/0/0 | 1 | 83:served_tuple,label | 83:concept,question |

Giữ đủ tất cả seed/profile/comparisons, gồm zero/negative controls; không chọn ví dụ thuận lợi. [trajectory_flags.csv](trajectory_flags.csv) và [common_prefix_flags.csv](common_prefix_flags.csv) giữ đủ flags. Sau divergence không ghép ΔP/loss/current-query crossings theo cùng ordinal event hoặc diễn giải thành funnel/mediation. Không CI/p-value, ability effect hoặc causal learning benefit; ba seed families đã dùng, new independent N=0. Full S28/calibration/reference mastery và scientific interventions vẫn thiếu. Counter-path counts không phải probability của prerequisite edge đúng.

Phân tích chỉ đọc các artifacts đã freeze; không gọi native model/RNG, thay graph/dynamics/hyperparameters, hoặc chạy thêm seed. Raw reconstruction PASS và các phase timers là engineering evidence; không biến failure120s trước thành PASS.
