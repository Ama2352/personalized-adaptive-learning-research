# CG-AKT: nghiệm thu index context dữ liệu nghiên cứu

09/11/2026 — **đã kiểm condition/context dữ liệu, chưa kiểm model/training**.
Recipe nghiên cứu là [quyết định26](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md), không tag engineering cũ. Bundle dự kiến [cgakt-research-context-engineering-20261109-01](../runs/cgakt-research-context-engineering-20261109-01/README.md); closure do ROOT kiểm và chạy riêng, không suy từ bản báo cáo này.

## Kết quả thật và lịch sử lỗi

ROOT đã chạy ba controller riêng, giữ nguyên từng log/JUnit/receipt và source-before/after. Không sửa lại lượt lỗi thành PASS.

| Lượt | Kết quả JUnit | Thời gian trong result.json | ROOT quan sát terminal | Nguyên nhân/kết luận |
|---|---|---:|---:|---|
|01|106 cases:67PASS,39setup errors,0fail/skip|7,2843940000s|7,2851355s|Fixture tạo source_row0, trái ItemQuery source_row≥1; sửa numbering+1, giữ global ranks0-based.|
|02|106 cases:67PASS,39setup errors,0fail/skip|5,9343819000s|5,9354833s|Source context đọc field `.labels` không tồn tại trên CausalSequenceInputs; lỗi API thật, sửa exact type/schema.|
|03|**109PASS,0failure/error/skip**|**10,6877745000s**|**10,6885863s**|66condition cases +43context cases; source18bindings trước/sau không đổi.|

Thời gian result và quan sát terminal có ranh giới đo khác nhau. Mỗi controller có cap90s/pytest child75s. Controller dùng ordinary subprocess, không phải chứng minh hard OS RAM quota hoặc Windows Job containment. Tests đã review không tạo descendants; không lấy testwall làm throughput/cost dự báo.

Context file ban đầu có40cases; sửa API thêm3negative cases nên thành43. Condition66 đã có kết quả lịch sử riêng trong [bundle13outputs](../runs/cgakt-research-condition-engineering-20261109-01/README.md), manifest `1c99ba062ace6cd3629fcbd65da4f31ddc1d7786cb3eb48ca95d4cd4cd6cbebd`. Test condition hiện sửa riêng cached-import canary để giữ class alias ổn định; kết quả66 cũ với testadcc vẫn nguyên giá trị lịch sử, không được relabel theo test mới2fdd. Các lần chạy lại không thêm research seeds hay independent N.

Cold-import canaries trước mỗi suite đều PASS: condition không NumPy/Torch, context cho NumPy và không Torch. Context test canary trong pytest chỉ kiểm cached import/class identity; không giả fresh import. **0neural model/optimizer/teacher**, không đọc actual Method24 artifacts/corpus/oracle; các typed observable records và provenance là handmade fixture, không research-trained attestation.

## Phần đã kiểm

`prepare_research_graph_context` nhận typed ResearchPhaseData/ResearchAKTEncoding/ResearchGraphCondition và explicit cache/time limits. Nó reuse `iter_research_windows` và `audit_graph_context`, không viết lại geometry hoặc parent arithmetic. Index chỉ giữ immutable window fingerprints, per-target audit records, source/phase/encoding/condition identities và OOV ledger; không giữ phase/trajectories/bank/corpus/labels hoặc arrays.

Fixture có hai selection learners×205events, OOV tại global rank102. Các train/calibration handmade records nhỏ phục vụ typed split/vocabulary lineage, không gọi teacher hoặc optimizer. Tests kiểm ranks99/100/199/200: effective starts lần lượt0/0/103/103, history_used99/100/96/97. Tại200, history_available100 khác history_used97; không dùng available hoặc min(rank,context) để thêm lịch sử cho graph. Full population410targets gồm408known và2OOV; OOV giữ null/unsupported ngoài native inputs, không graph rescue.

Current/future response perturbation và peer-learner perturbation giữ numerical evidence của query được kiểm; past response positive control làm mean/scoped-history hash đổi đúng. Full phase/condition provenance có thể đổi khi future labels đổi; đây không phải yêu cầu mọi metadata SHA bất biến. Full WindowInputs fingerprint gồm item/time/prior/source/user/ranks/masks/history/reset/window ID; modified/foreign/duplicate windows bị từ chối. Exact CausalSequenceInputs có7fields và không có labels; wrong type/ducktyped label carrier và concept_ids ngoài native item-only schema bị từ chối.

Condition train80 và neural phase/encoding lineage giữ riêng; wrong plan/role/train-input encoding bị từ chối. `for_windows` trả context đúng local position, non-target=None. Source seals/cache limits được kiểm tại boundaries. SHA/typed metadata là consistency hợp tác, không capability chống caller giả metadata hoặc chứng thực nguồn/fit bên ngoài.

## Giới hạn trước main training

Chưa có native graph forward/backward/optimizer/checkpoint/export trong bundle này; chưa có fitted CG-AKT, independent-A0 system fallback hoặc bằng chứng graph cải thiện prediction/learning. Source model đang được kiểm riêng. Các phép kiểm geometry là dữ liệu, không nghiệm thu research lifecycle hoặc current full software Gate.

**Hot path vẫn là blocker hiệu năng:** static review model/context dự kiến khoảng7lần full-index JSON hashing mỗi train batch. Đây là số call theo source review, chưa benchmark runtime toàn corpus. Giữ source hiện tại để kiểm correctness nhỏ trước; không tuyên bố main training sẵn sàng hoặc tối ưu ngầm trong archive. Cần bước bounded model checks, sau đó thiết kế cache validation phù hợp source/phase boundaries, checkpoint semantics và actual lifecycle admission trước research fit.

## Source và bằng chứng

- Context source `5a5ada91a78a5d7de2b4d5021dc3cf34e6c97de2e46931509b8f6faf5c56c4d5`; context tests `ac6bff7187ef37aa9b4455706992763681ccd9f433fd93965cf93d7ce7c9dd52`.
- Condition source giữ `6678f04c3c0b3655aa797edd3e491877d17ac3f0fa12f7dfc9971f637d875cf0`; combined-test revision `2fdd512ca905973306a27b2d0059d0110cff1e8f4b01b7db715aa23ec5d758e1`.
- [Actual03 receipt](../runs/cgakt-research-context-engineering-20261109-01/trial03__result.json): SHA `3b3b2a413ffd4ac66da12a02ed21b5ccf08272ddda954d566c50ab82f7c7e1ed`; [JUnit03](../runs/cgakt-research-context-engineering-20261109-01/trial03__junit.xml): `a4a8276be35c5ad81c2bbe1827b332de7909f1a945324a2440aab7c66243dc7f`.
- [Field audit](../runs/cgakt-research-context-engineering-20261109-01/field_audit.json), original source/test snapshots, cached-import fix và hai failure receipts được chọn copy nguyên byte. Các source dependencies còn lại giữ exact before/after maps trong raw receipts và tham chiếu bundle condition, không nhân đôi toàn bộ source archive cũ.

Báo cáo/packager chỉ tổng hợp bằng chứng đã lưu, không chạy lại test/model. Archive completion sau này chỉ xác nhận output integrity; khoa học và quyền thực thi vẫn theo21/22/26 cùng admission riêng.
