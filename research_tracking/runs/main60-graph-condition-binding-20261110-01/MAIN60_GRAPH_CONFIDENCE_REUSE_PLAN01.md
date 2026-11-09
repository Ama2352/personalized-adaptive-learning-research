# Main60 — tái dùng Method24 để bind sáu điều kiện đồ thị

## Phạm vi đề xuất

Đây là kế hoạch nguồn cho một lượt kiểm dữ liệu chỉ đọc. Chưa gọi loader, chưa tạo condition thực tế, chưa cấp quyền chạy mô hình trong lượt chuẩn bị này. Bản wire đầy đủ nằm ở `MAIN60_GRAPH_CONFIDENCE_REUSE_PLAN01.json`, SHA `236fc69face0c19e160ade000d924f25c0fd243eeb75d65df3ea348af9be3cca`.

Method24 đã fit trên đúng corpus Main60, gồm 48 learner train và 10.080 sự kiện. Có thể tái dùng artifact đó để tạo sáu condition theo recipe26. Không cần fit lại surrogate. Các condition là metadata và trọng số cạnh dành cho neural adapter. Chúng chưa là mô hình CGAKT fitted hoặc kết quả lựa chọn hệ thống.

## Bằng chứng và lineage phải khớp

- Corpus `grade10-development-lifecycle01-20261108`, corpus SHA `555ed695c7c7121af474edb542fa3eef664b340162ced46cdfc001a5d7a4ad72`, DONE SHA `66232663868baafd2f012b4d79afad373e2fd5e831d30622153163b94e1b733f`.
- Logical `ResearchSplitPlan.identity` là `7222b7c34051f41d99648421b940167c2da705efa604070957a23812273e02ed`. File `plan.json` có raw SHA `b48c3657eac3c04cbad5e3b7864021e5860eef8ef01ba8808cc9161deaa8b2f6`. Hai trường có ý nghĩa khác nhau và phải giữ riêng.
- Train provenance `10287bccb20804a1504981c5a5d6551e280369fac283df74a4eabf5aed15e9e5`, train observable raw SHA `e2f3d7c0e1cf1fefa8b3c952d21a0531436f86259d6a7c8a07699cc0435fc07b`.
- Public preflight `main60-data-preflight01/result.json` SHA `e9fa2c402efb3350b011364a6d53a2564563b253f32de4f09089da6af8b6eb0c` đã xác nhận 48/6/6 learner, 10.080/1.260/1.260 target, đủ 84 item và không OOV. Các minimum 47–48 learner mỗi concept chưa chứng minh support của một cặp cạnh.
- Producer đóng tại `research_tracking/runs/edge-confidence-windows-bootstrap-20261108-01/manifest.json`, SHA `6e0cbe7129e52752fe2457ca44c04a9c942b6c2d660b0e10e164ec7c2088e270`. Actual producer đã ghi 2.352 solver fits, 756 cặp supported và DAG 31 cạnh. Không cộng chúng thành neural fits.
- Consumer03 đã chấp nhận learned31. `edge_artifact_native03_expectation.json` SHA `fe968b7c87aa868e7d98fc29dcacc5fa6ddd5ec20fd21d517eda4ac75e35ce20` chứa external envelope/training/source/runtime expectations. Loaded identity lịch sử `a51fbf935be3dda0ee2d89c2ebe61ce736a2c87d7fe604c126f79f77e73cbb7a` chỉ thuộc lần bind learned graph đó. Bind expert tạo identity riêng.

## API hiện có cần dùng

1. `src/knowledge_tracing/simulator_corpus_reader.py` — `read_public_research_corpus` đọc canonical public inputs và thực hiện audit trước/sau. Có thể audit cả ba Development role cho provenance theo contract22. Không fit, đánh giá metric hoặc chọn condition từ selection/calibration.
2. `src/knowledge_tracing/akt/research_graph_condition.py:72` — tạo `GraphTrain80Binding` từ corpus thật. Lấy ba `role_data(role).audit['audit']['shard_sha256']` sau canonical audit. Không điền raw JSONL SHA thay logical audited shard SHA.
3. `src/knowledge_tracing/edge_confidence_artifact.py:355` — `load_method24_scores(ref, expected_training=..., bank=..., declared_graph=..., graph_binding=..., limits=...)`. Dùng nguyên `Method24ArtifactRef`, `Method24TrainingBinding`, `Method24ReadLimits` từ expectation đã pin. Mapping JSON phải đổi sang immutable sorted tuples theo schema thật.
4. `src/knowledge_tracing/akt/research_graph_condition.py:229` — `prepare_research_graph_condition` với actual bank, train80 binding và external source inventory. Factory kiểm domain, topology, support, nguồn artifact và recipe26. Không tự tạo dataclass bằng cách bỏ qua factory.
5. `src/knowledge_tracing/akt/research_main_execution.py:266` — `MainGraphInput` nhận topology file/raw SHA, ba JSON wire Method24, expected loaded identity và actual condition identity. `_actual_condition` ở dòng424 sẽ tái kiểm qua cùng public factories khi có genuine Main allocation sau này.

Không dùng các entry `fit_crossfit_edge_confidence` hoặc `select_positive_dag` để dựng lại kết quả trong lượt kiểm này. Không import neural adapter, trainer hay optimizer.

## Hai lần đọc artifact, sáu condition

| Condition | Topology | Loader binding | Trọng số |
|---|---|---|---|
| A1_EXPERT | public expert31 | không cần cho A1 | uniform 1 |
| A2_EXPERT | cùng expert31 | declared | predictive stability, giữ support/null |
| A3_EXPERT | cùng expert31 | dùng lại typed loaded expert | cùng A2_EXPERT |
| A1_LEARNED | accepted learned31 | method24_learned | uniform 1 sau kiểm provenance topology |
| A2_LEARNED | cùng learned31 | dùng lại typed loaded learned | predictive stability |
| A3_LEARNED | cùng learned31 | dùng lại typed loaded learned | cùng A2_LEARNED |

Expert topology lấy đúng `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/data/simulator_inputs/edges.csv`, có toàn bộ 28 bank concepts kể cả isolated nodes. Lượt chuẩn bị tiếp theo phải pin CSV rồi ghi JSON topology mới vào namespace riêng dưới `artifacts/akt/`; file này hiện chưa được tạo. Raw SHA của JSON đó là `topology_source_sha256` cho expert.

Learned topology đã có ở `method24-native01/graph.json`, raw SHA `6b31728f0f2bd1714cfe0b37b9dae85e10aedcb06a16b639a4d53e607f17972a`. Loader kiểm 28 node, 31 cạnh supported/positive, acyclic, budget và toàn bộ envelope. Semantic exported graph SHA `b7a76280175dba1e6119426b341172b9a1537c94a59655f5fc5537f7a3f2829c` được giữ riêng với raw file SHA.

Gọi loader hai lần cho expert và learned. Tái dùng hai typed loaded objects cho các factory condition. Giữ nguyên supported zero, unsupported null cùng reason và mapping operational zero được recipe26 chấp thuận. `estimated_probability` chỉ là enum legacy của kernel. Ý nghĩa thực tế là conditional predictive stability.

## Kiểm chấp nhận đề xuất

- Source/input/runtime trước–sau trùng external SHA. Producer envelope đầy đủ 14 output SHA, 13 DONE entries, terminal RC0 và cleanup đã được parser xác nhận.
- Corpus/logical plan/train provenance/train observable/domain khớp chính xác Method24TrainingBinding. Không đọc oracle. Calibration chỉ tham gia audit provenance.
- Sáu ID condition chính xác, đủ 28 nodes, graph/confidence đều fit scope train80 và frozen qua neural refit90. Sáu actual identity phải do factory sinh, không điền trước bằng hash giả.
- A1 uniform 1. A2/A3 trên cùng topology có cùng score/support/reason ledger. Learned31 bắt buộc supported và positive point delta. Expert giữ toàn bộ cạnh declared dù confidence zero hoặc unsupported.
- Negative control metadata thay corpus/train binding thành engineering10 phải bị factory từ chối trước model. Không đọc thêm corpus engineering10 cho negative control này.
- Tạo `MainGraphInput` wire từ actual raw topology SHA, loaded identity, condition identity. Kiểm round-trip wire và nguồn hiện hành. Chưa gọi authorization factory hoặc runner.
- Output nhỏ gồm sáu condition manifest, source/input inventory và receipt. Không ghi lại score OOF CSV hoặc checkpoint. Chấp nhận theo integrity/lineage, không dựa chất lượng metric.

## Giới hạn tài nguyên và chi phí I/O

Actual metadata file-size inventory hiện có 14 native output, tổng **69.519.761 byte**. Parser stream-hash toàn bộ file theo cap, không chỉ đọc 31 score. Hai lần loader có thể quét lại cùng khoảng 69,52 MB, cộng các lượt parse/metadata. Tổng byte thực đọc phải đo và ràng buộc, không coi artifact đã cache trong bộ nhớ là miễn phí.

Đề xuất một lượt whole60s, worker50s, owned57s gồm cleanup3s, full owned-Job RSS512MiB, free1536MiB và admission2GiB. Hai loader giữ cap20s mỗi lần, `max_read_bytes=160MiB` mỗi lần, aggregate320MiB. Public corpus có read cap riêng hữu hạn, cần cộng vào tổng operational I/O ledger. NumPy data-only được phép, Torch/Pandas/sklearn/scipy/solver/teacher không cần import.

Future `MainSelectedExecutionSpec.max_graph_input_bytes` phải ít nhất160MiB vì `_actual_condition` so cap với `Method24ReadLimits.max_read_bytes`. Dùng cap8MiB từ A0 engineering sẽ bị chặn đúng hợp đồng. `MainSelectedExecution.revalidate` còn hash `_graph_files` ở các boundary nên neural allocation tương lai phải tính I/O lặp lại. Kế hoạch này chưa đo throughput hoặc chứng minh fit Main60 khả thi trong một runtime cụ thể.

## Bước sau khi Root duyệt

Chuẩn bị một worker/controller/packet data-only nhỏ dùng những API trên và namespace mới. Root review external pins, topology JSON publication, limits và output schema trước một dispatch hữu hạn. Không cần thay production source hoặc rerun surrogate.

Artifact train48 không được dùng làm learned/confidence fit từ train8 của engineering10. Một positive A1_EXPERT trên engineering10 có thể dùng public topology, condition bound train8 riêng và fresh initial backbone cùng seed với A0. A2/A3 hoặc learned trên engineering10 cần đúng realization train8 nếu muốn thử tại corpus đó.

Main60 graph selected fits chỉ chạy khi có genuine allocation. Matrix vẫn giữ A0, sáu graph conditions, SAKT và GKT. A2 là ablation. Toàn bộ raw selection cần có trước system freeze và trước bất kỳ main refit/calibration nào. Độc lập A0 fallback tiếp tục có checkpoint fitted riêng.
