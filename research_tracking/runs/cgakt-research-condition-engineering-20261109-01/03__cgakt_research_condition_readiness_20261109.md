# CG-AKT: tầng condition nghiên cứu đã kiểm, chưa có forward hoặc model fitted

09/11/2026. Theo [Recipe26](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md), đã triển khai tầng nhận cấu hình nghiên cứu A0–A3 và gắn nguồn graph/confidence. **66 ca kiểm metadata đạt,0 failure/error/skip**, trong2,9972164giây của lượt kiểm CPU. Dữ liệu trong test đều dựng sẵn; không đọc artifact Method24 thực, corpus, oracle hoặc chạy model/optimizer/solver.

Tầng này giữ khác biệt giữa cạnh không đủ hỗ trợ và cạnh được hỗ trợ nhưng có score0. Cả hai có thể tạo operational weight0, nhưng metadata vẫn giữ flag/reason và null của trường hợp đầu. Expert graph được nhận theo declared topology; điều kiện learned graph phải đáp ứng rule28nodes/31edges được hỗ trợ. Không dùng việc learned graph chưa đạt để bác mọi confidence trên expert graph.

Graph/confidence gắn train80 xuyên qua neural refit90; encoding/vocabulary có lineage riêng. SHA của external system freeze chỉ là tham chiếu metadata, chưa xác minh quyền refit. Source/tag/domain/graph/role/oracle và các trường hợp thiếu/thừa/trùng được kiểm từ chối. Module và converter trả kwargs thuần dữ liệu, không import NumPy/Torch. Các container `LoadedMethod24Scores` trong test là **UNVERIFIED fixture**, không receipt của2.352 fits mới.

Nguồn: [condition](../../src/knowledge_tracing/akt/research_graph_condition.py), [tests](../../tests/akt/test_research_graph_condition.py), [log/bằng chứng](../runs/cgakt-research-condition-engineering-20261109-01/README.md). Source trước/sau lượt kiểm được đối chiếu nguyên byte; JUnit đủ66cases. Đây là21test functions có tham số hóa, không66mẫu nghiên cứu.

**Chưa đạt:** graph context cho cửa sổ thật, forward/backward research wrapper, checkpoint graph nghiên cứu, selected-only/external-freeze refit, training và so sánh RQ3. Các phần này đang được triển khai riêng; không nâng tầng metadata thành mô hình CG-AKT đã hoàn thiện. Gate1.418 trước đó chỉ chứng nhận snapshot154 nguồn, cần refresh khi các source nghiên cứu mới ổn định.
