# Pilot CPU09/CPU10 được chấp thuận ngày07/11/2026

## Phạm vi và trạng thái

User chấp thuận giới hạn trong chat trước execution. Factorial hoàn tất14400events trong62.05s, Junyi hoàn tất32inner-train learners/1211events trong9.31s. Các con số dưới đây là pilot mô tả, chưa có confirmatory inference hoặc kết luận instructional benefit. Artifact lịch sử và Holdout không được dùng để chọn cấu hình.

## CPU09 — ability và prerequisite mechanism

Run `cpu-factorial-20261107-01`,10seeds21000–21009×3profiles×4cells×120steps. Model treatment bật parent signal và parent adaptation, control tắt cả hai, local pathway tắt trong cả hai. G_env/G_controller giữ graph lịch sử, mỗi nhóm4cells dùng cùng base_theta và uniforms. Mechanism coefficient0 hoặc.55 có parity với phương trình nguồn tại.55. Net mean theta gain là outcome.

| Profile | Mean interaction contrast | Số paired seeds |
|---|---|---|
| PG |0.000000|10|
| PY |+0.034017|10|
| PYH |+0.053529|10|

Estimand là (edge-on−edge-off)|lambda.55 − (edge-on−edge-off)|lambda0. Đơn vị là Elo-scale mean trên28concept. Giá trị này không phải raw graph gain hoặc time-DiD. Initial abilities giữ cách sinh có graph correlation của nguồn, nên diễn giải conditional trên simulator và intervention cụ thể. Chưa kiểm CI/significance, chưa chọn final seeds.

### Kiểm độ hoạt động của mechanism

Trong các cell lambda.55, PG có0/2400events bị prerequisite deficit, PY có1919/2400, PYH có1197/2400. Minimum base ability của PG trên10seed là1269.31, cao hơn readiness1150. Dynamics giữ theta_at≥base, nên penalty không hoạt động cho nhóm PG đã đo. Interaction0 của PG có giải thích cấu trúc trong điều kiện này. Không dùng nó để suy graph vô ích cho mọi learner mạnh.

Nguồn raw nằm trong outcomes.json, contrasts.json, summary.json và traces.jsonl.gz của run. Các kết quả kiểm mechanism coverage ở cpu_pilot_followup_20261107.json.

## CPU10 — Junyi logged practice order

Run `cpu-junyi-order-20261107-01`. Cohort hash-selected32learner chỉ từ inner-train, outer-fold0. Prefix tối đa120events/learner, tổng1211events. Query chỉ lấy user/exercise/time/source row và fold, không lấy correctness. Kết quả không xuất raw learner IDs.

Catalog có835exercise,981directed prerequisite entries, bao gồm2self-loop được ghi riêng. Sau loại self-loop khỏi order comparison có979edges. Trong prefix pilot,24edges được co-observe ít nhất một learner, tổng52edge–learner pairs. Có48pairs parent xuất hiện trước child và4pairs ngược lại. Đây là statistic weighted theo supported pairs, các pairs không độc lập. Cohort nhỏ và prefix censoring giới hạn support. Không diễn giải48/52 như causal evidence của graph quality hoặc full Junyi prevalence.

### Cấu trúc graph cần xử lý trước model DAG

Catalog thô vẫn có cycle sau khi bỏ self-loops. Witness gồm simplifying_radicals → adding_and_subtracting_radicals → radical_multiplication_and_division → simplifying_radicals. Degree/chapter DAG rewiring hiện có chưa áp dụng trực tiếp lên catalog cyclic này. Junyi cần matching topic/area và train support riêng.

Điều tra tiếp tìm được preprocessing SCC đã có trong Paper2, code cell23 của junyi_cycle_corrected_ablation_confirmation.ipynb. Run cpu-junyi-graph-reconstruction-20261107-01 chọn đúng6AST statements, loại cạnh nội bộ SCC trên bản graph mới. Kết quả835nodes,979raw edges không self-loop,3removed edges,976corrected edges và DAG=true, khớp counts trong certificate lịch sử. Graph.json công khai danh tính cạnh và corrected-edge-set hash. Dataset gốc không bị sửa.

Đây là current-catalog reconstruction theo historical rule. Certificate cũ ghi rõ thiếu raw input/edge hashes, nên chưa thể chứng minh identical historical edge bytes. Phần blocker thiếu cách xử lý cycle đã được giải quyết bằng source hiện có. Quyết định graph-version cho experiment tương lai vẫn cần chốt. Các order statistics ở trên là trên raw graph sau bỏ self-loops, giữ nguyên artifact và không thay bằng reconstructed-DAG numbers âm thầm.

Nguồn output ở catalog_audit.json, order_summary.json và reverse_summary.json của run. Cycle witness lấy từ static catalog cùng source identity được hash trong manifest, ghi trong cpu_pilot_followup_20261107.json.

## Giá trị đối với RQ và phần còn thiếu

Các pilot bổ sung bằng chứng cho trap simulator-embedded answers, khả năng kiểm soát ability/mechanism và logged-order confounding. Chưa hoàn tất RQ1/RQ2. Cần full pathway ablation, support-matched negative controls, protocol statistical families, graph cleanup/version decision và confirmatory matrix được chốt. Mọi readout pilot tiếp theo giữ nguyên các seed đã công khai, tránh seed shopping.
