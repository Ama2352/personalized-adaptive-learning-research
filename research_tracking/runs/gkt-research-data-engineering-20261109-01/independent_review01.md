# GKT research data — review độc lập chỉ đọc nguồn

Ngày09/11/2026. Verdict `SCOPED_STATIC_PASS_NO_DETERMINISTIC_BLOCKER_FOUND`. Phạm vi hai candidate data/tests, protocol21/22, shared phase và adapter hiện có. Không import/compile/test/Python/Git, không đọc corpus hay oracle thật, không sửa source hoặc hồ sơ canonical. Verdict này không là kết quả test hoặc quyền chạy/fit.

## Ranh giới thông tin và role

- Candidate lines163–177dựng `ResearchAKTShard` từ đúng public role, gọi `prepare_research_phase` và `fit_research_encoding`. Shared `_check_pair` lines192–209kiểm train80 optimization identity, selection chỉ dùng train80encoding, calibration chỉ dùng cùng frozen refit90encoding. Scope final không có trong SCOPES. Candidate227cấm training trên selection/calibration. Không thấy đường đổi role để fit calibration hoặc silently refit từ selection.
- Iterator242–263đối chiếu canonical key/query/y/origin với sidecar rồi yield record trước khi append current query/response vào past. Predictor inputs không chứa current label; training wrapper206–208tách target. Shared `research_scoring_targets:260–279` tính prefix hash trước current response, không ghi lại hash model-specific. Tests147–165kiểm current/future/peer labels trên query/prefix channels. Không thấy current/future-label leakage vào local predictor features.
- Global phase/encoding/graph IDs có thể đổi khi nội dung role đổi. Đây là provenance metadata, không feature đưa vào neural layer. Future runner phải tiếp tục truyền các trường query/node/past cụ thể, không dùng provenance SHA như feature hoặc learner embedding.
- `GKTResearchView` dùng InitVar corpus và không giữ whole corpus trong instance. Phase vẫn chứa nhãn của role để trusted orchestration tách loss/scoring. Việc public corpus đã được audit cả ba roles phù hợp protocol22, không phải lý do đòi reader mới. Không có oracle/final-event API trong candidate.

## OOV và đơn vị node

- Bank84/concept28registry ở128–137khác item vocabulary được optimization quan sát ở138–142. Mapping trả node index theo sorted graph nodes; node0 được giữ hợp lệ vì check `is None`, không check truthiness.
- Query item chưa được TRAIN thấy vẫn là `oov_item`, kể cả cùng concept với item đã thấy. Tests167–177kiểm chính trường hợp đó. Đây là support convention bảo thủ đang được khai báo, phù hợp adapter hiện tại `_node:174–178`, không phải khẳng định concept đó chưa từng học. Không suy concept coverage từ item support hoặc đổi unseen-item thành known chỉ vì registry công khai biết concept.
- Sau một OOV, records tiếp theo có full history chưa biểu diễn được nên `unsupported_history`, tuples/node null và history_used0. Không reset state rồi chấm suffix như full-prefix. History_available vẫn là rank thực, mọi target kể cả unsupported được giữ.
- **Cần giữ ở future exporter**. `gkt_research_scoring_targets()`211–216trả shared sidecar có `train_supported` chỉ theo item hiện tại. Sau OOVprefix, một later-known item có sidecar train_supported=true nhưng `GKTResearchInput.eligible=false`. Export/metric phải dùng actual eligibility/support_reason của predictor input và full-population coverage, không lấy sidecar train_supported làm fitted-valid mask. Candidate hiện chưa có exporter nên đây là điều kiện tích hợp tiếp, chưa phải lỗi đang thực chạy.

## Frozen graph, limits và phạm vi software

- GraphBinding53ghi rõ caller metadata, không mở hoặc xác minh topology file/fit attestation. Shape/DAG/sorted28nodes ở61–79, actual domain và TRAIN80 shard ở135–137được ràng buộc riêng. Refit90thay encoding nhưng giữ graph train80; tests194–212kiểm boundary/freeze. SHA-shaped fixture hoặc graph_kind không phải grant và không chứng minh đã nạp expert graph thật.
- Expanded-prefix cost là quadratic, được candidate230–233tính và chặn trước first yield. Toàn population bao gồm cả unsupported. Không thấy helper/abstraction thừa cần refactor trong scope nhỏ này. Chi phí hash/audit và materialized prefixes chưa được đo, không có throughput claim.
- Candidate là data bridge. Nó chưa tương thích trực tiếp như một research runner28nodes với adapter fitted cũ. `gkt/adapter.py:89–98` còn engineering caps≤4nodes/≤8items và current prediction API dùng shared causal inputs riêng. Training/checkpoint/model binding/actual topology verification/export và fitted OnlineSession cần implementation riêng. Không lấy data-only success làm GKT research baseline hoàn thành hoặc nới old adapter caps trong batch này.
- Tests là17methods trên PublicResearchCorpus dựng tay, không qua genuine disk publication/reader. Fake hashes được khai báo đúng tên. Cold-import fixture chỉ bảo vệ candidate import, Root wrapper cần giữ no-Torch/native/solver guard trong toàn lượt test. Chưa có PASS output được suy ra từ static review này.

## Exact source pins

| File | SHA-256 |
|---|---|
| `P/gkt_research_data_candidate01.py` | `1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873` |
| `P/test_gkt_research_data_candidate01.py` | `88cfd7f85ab90f2be08fb0eafcd2a92fceda03f80614a521f247c40125c89189` |
| `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md` | `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6` |
| `docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md` | `96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1` |
| `src/knowledge_tracing/akt/research_simulator_data.py` | `9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b` |
| `src/knowledge_tracing/gkt/adapter.py` | `2e6c4ed64433dac63f54344710303cf0908b0c66cc63735a71f3f6d23f42c0f4` |
| `src/knowledge_tracing/gkt/training_data.py` | `db5a9c41d29eaf5ccb834965cfe1e7952a3b9dfe2a4dca573d91791909403339` |
| `src/knowledge_tracing/simulator_corpus_reader.py` | `e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90` |

P là `artifacts/akt/local-tests/akt-research-runner-20261108-01`. Không đề nghị đổi candidate để lấp các future integration gaps trong cùng batch data-only này.
