# GKT08 selected-only, handoff candidate nguồn

ROOT đã duyệt hướng nhỏ ba file và giữ nguyên criterion response-pooled binary64 Log Loss theo recipe29. Chưa apply hoặc chạy. Bản đề xuất nguồn `GKT_SELECTED_PRODUCER_SOURCE_PROPOSAL01.md` SHA `8404506165cfcaf9a97b62bd3bbb44d868ee4b23a34984e90e6aa15c87dc906e` ghi API, giới hạn và input hiện hành.

## Candidate freeze

| Candidate trong prep | Target canonical dự kiến | SHA-256 |
|---|---|---|
| gkt_research_execution_candidate01.py | src/knowledge_tracing/gkt/research_execution.py | 305c8d7f7015a003f2522be8227cb7b61b410c2b569345f2ccacba9bed04ee49 |
| gkt_research_runner_candidate01.py | src/knowledge_tracing/gkt/research_runner.py | 173fbf7cea845a649da4a79f92394883210de239743e4f8f6c687e0730530d30 |
| test_gkt_selected_candidates01.py | tests/gkt/test_research_selected.py | 7d357f183391eb2d89c01e82f9bf4433b8ccdb43303a5a37ce2ab77957175c9e |

Inventory cuối `gkt_selected_candidates01_source_inventory02.json` SHA `a42feb78da4a52815b70ee8b6031d713ce3fabf834166b17c6a14aba42f2d675`. Trước bổ sung mandatory package-init pins, hai candidate cũ đã inventory/copy/rehash trong gkt-selected-package-init-before01. Canonical GKT model/trainer/checkpoint, Main, SAKT và recipe không bị sửa trong lượt này.

## Nội dung chính

- Admission riêng GKT, exact recipe29, typed source/runtime/current shared Gate/public corpus/topology và ba bộ component thực model11/trainer8/checkpoint28. Mỗi component cần external FilePins tới outer, child, owned receipt và JUnit, actual status/counts0FES, source/runtime trước–sau, method restoration và Job0. Parser dùng schema GKT thực, không dùng receipt SAKT22/33.
- Closed authorization có scope gkt_main_selected_only_v1 và decision AUTHORIZE_BOUNDED_GKT_MAIN_SELECTED_ONLY. Metadata inspection không tạo token. A0/SAKT/stage claims không thay được authorization này.
- Lazy runner dùng model/train/predict/save/restore GKT hiện hành. Graph là static expert concept28, actual pinned topology bytes và TRAIN80 shard. Registry84 không thành84graph nodes. Batch4 theo learner whole trajectories, shuffle42+epoch và owned dropout RNG/BN theo primitive.
- TRAIN progress chỉ nhận optimization. EVAL progress riêng giữ counters, RNG và readonly BN/model. CP save sau validation dùng receipt huấn luyện chưa bị đổi. CP budget/origin giữ nguyên khi fresh best restore, actual producer ledger không lùi về counters của best epoch.
- Selection dùng score_raw_predictions binary64 LL, genuine EarlyStopping50/patience5/delta0,0001. Fresh model/Adam cùng initialization trước actual best restore. Kiểm full raw prediction SHA parity trước model-neutral CSV/truth/coverage/SelectedCandidateClaim.
- Durable Adam pre/post hooks đếm target tổng chiều dài đúng những learners trong shuffled batch. Partial exceptions giữ reserved/returned/complete khác nhau, poison/counters của primitives nếu có, failure override. Không rollback/retry hoặc public resume.

SOURCE_NAMES ghim ancestor package __init__ của knowledge_tracing, akt, gkt, sakt, gam_kt và các module helpers được dùng. gam_kt/__init__.py bắt buộc vì _metrics được nhập trong scientific lazy phase. Không suy dependency closure từ cold test.

Đọc JSON/SHA của ba bộ component hiện có xác nhận outer.child_result bằng file child, outer.owned_receipt bằng file receipt, source/runtime maps tương ứng bằng nhau, actual counters bằng expected counters và JUnit SHA bằng outer.outputs. Đây là đối chiếu metadata bằng PowerShell, không thực thi candidate admission hoặc native tests mới. Các SHA outer gốc nằm trong inventory02.

## Cold fixtures đề nghị

Có22 physical test functions và27 parameterized cases theo source, chưa collect hoặc chạy. Tests dùng import canonical thật, không dựng namespace package hoặc successful fake grant. Vì thế cần ROOT review rồi apply byte-identical ba target trước chạy bộ này. Các phép kiểm là recipe/type/quota/source/package-init/negative family authority/artifact SHA và complete/null joins, thiếu/trùng/foreign/history/BN/nonfinite/unprocessed controls. Test source-mandatory có thêm subcase bỏ gam_kt/__init__.py, số physical cases không tăng.

Đề nghị ROOT giữ cold process không Torch/NumPy/Pandas/model/solver/corpus reads. Hai file JSON của negative tests chỉ nằm trong tmp_path sở hữu. Không cần chạy metadata trong lúc NN khác hoạt động hoặc tạo hồ sơ grant dương giả để làm xanh test. Agent chưa chạy Python/AST/import/test/Git.

## Acceptance tiếp theo còn thiếu

1. ROOT review source/syntax và apply có inventory/rehash, rồi actual cold collection/test với source pins hiện hành. Không dùng27 là số đã PASS.
2. Chuẩn bị actual GKT topology FilePin và closed GKT authorization từ runtime/current Gate/component receipts thực. Chưa có config/auth/request cho producer.
3. Native bounded positive qua run_gkt_selected_fit thật trong owned process, chứng minh epoch hoàn chỉnh, train/eval progress tách, CP save sau eval, BN/RNG caller, fresh-best parity và full coverage. Kèm actual constructors/Adam/sequence/tail counts và resources. Không dùng model11/trainer8/CP28 để gọi producer đã đạt.

Ví dụ reservation48×210 là tối đa600training sequence calls/504000optimized targets và204prediction API calls trên51passes, trong đó mỗi selection batch dài có prefix sequence cộng tail readout. Đây không phải804 tổng Torch forwards hoặc804 mẫu độc lập. Còn cần đo runtime/throughput/cost, chưa cấp ngân sách fit. Giá trị thời gian/RAM của declared_spec trong cold test chỉ là metadata fixture.

Không refit90, calibration, system winner, fitted OnlineSession, Junyi, CUDA hoặc crash recovery trong batch. Required models/RQs giữ nguyên.
