# Handoff candidate data-only GKT nghiên cứu

09/11/2026. Chỉ hai source candidate dưới prep. Không sửa `src/`, engineering caps hoặc tests canonical. Chưa import, compile, test, đọc corpus thực hoặc chạy Git.

- `gkt_research_data_candidate01.py` SHA `1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873`.
- `test_gkt_research_data_candidate01.py` SHA `88cfd7f85ab90f2be08fb0eafcd2a92fceda03f80614a521f247c40125c89189`.
- Static17 unittest methods, chưa có execution result. Không model constructor/optimizer/forward hoặc new probability estimator. NumPy được import gián tiếp bởi shared research data; không gọi đây là stdlib-only import graph.

## API

`prepare_gkt_research_view(corpus, *, scope, recipe, graph_binding, encoding=None, selection_freeze=None)` tạo view chỉ giữ đúng phase. Recipe data cố định concept/full_prefix/query_only/unsupported_history, không có dims/GRU/dropout/optimizer. Graph binding là metadata static expert với bank-domain SHA, sorted28nodes/uniqueDAGedges, external topology byteSHA và TRAIN80 shard SHA. Chưa mở hoặc xác minh file topology, chưa execution/fit attestation.

Bank registry84 phải đủ ba difficulty1050/1200/1350 cho mỗi28concept. Registry công khai khác train-observed item vocabulary. Train item map có thể ít84 khi unsupported, không tự dùng bank để mở vocabulary. Refit mới dùng union90encoding/freeze, giữ graph train80. Không thêm item difficulty embedding hoặc dùng source-defined concept state như latent mastery.

`iter_gkt_research_inputs(view, *, training, limits)` trả mỗi target kể cả OOV suffix. Predictor record có query node và tuple past queries/node IDs/responses, không current label. Training wrapper tách target. Sidecar dùng nguyên `research_scoring_targets` và observable-prefix-chain-v1, không viết lại hashing/causal geometry. Các prior responses vẫn là đầu vào hợp lệ của full-prefix recurrence.

Sau OOV, mọi target sau bị unsupported_history, không reset state rồi chấm như đầy đủ lịch sử. `history_available=global_rank`, unsupported `history_used=0`, tuples/node=null. Đây là unsupported record, chưa prediction probability row. Current record được yield trước khi append current response vào past. Không retain full public corpus trong view, nhưng phase có nhãn role của nó như các shared data views.

Expanded-prefix materialization có chi phí O(sum rank). `GKTResearchInputLimits(max_targets,max_prefix_events)` chặn cả population/expandedprefix trước first yield. Không có mapping cache/Merkle/trainer mới. Future incremental state runner không thuộc batch này.

## Fixture và acceptance đề xuất

Fixture đúng PublicResearchCorpus/ResearchSplitPlan/provenance/auditor nhưng toàn observable dựng tay, metadata SHA giả nói rõ unverified.10 Development learners với8/1/1 roles,4events mỗi learner, bank28/84. Chỉ hai TRAIN items được thấy, cùng concept; selection item thứ ba là OOV. Không qua disk reader/publisher, không đủ84support và không giả train attestation.

17methods kiểm registry/vocab tách nhau,28/84/reference levels, full population/key/query/hash, current/future/peer isolation, OOV+suffix null, labels tách wrapper, role/vocab refusal, refit90/freeze/graph80, calibration lineage, DAG/duplicate/oracle/learned tags, domain/train-shard drift, recipe refusal, exact bounds32targets/48prefix events, nested tamper, immutable repeated records và calibration-label isolation.

Sau source review, Root có thể chạy đúng newfile dưới genuine bounded wrapper, whole30s/thread1–2, PYTHONPATH=src, không teacher/Torch/dataset/corpus/GPU. Child command dự kiến `.venv/Scripts/python.exe -B -m unittest discover -s artifacts/akt/local-tests/akt-research-runner-20261108-01 -p test_gkt_research_data_candidate01.py -v`. Chưa cấp dispatch hoặc pass count. Fresh import canary nên cấm Torch và neural package imports, cho NumPy data dependency.

Không có open scientific field cần quyết để dữ liệu này biểu diễn concept28/staticexpert/fullprefix theo21. Main runner vẫn phải kiểm actual docs21/source/reader/runtime/authority/bank/support trước model. Recurrence numerical profile, research training/checkpoint, selected-only export và fitted OnlineSession còn thiếu, không được tự suy từ data bridge.
