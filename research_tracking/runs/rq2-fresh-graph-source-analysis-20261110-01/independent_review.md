# RQ2 recovery03 — kiểm độc lập và kết quả mô tả

10/11/2026. Chỉ đọc JSON, SHA và tính lại bằng PowerShell. Không Python, world/model call, test hoặc Git. Không thêm CI, p-value hoặc thay estimand. Các trung bình dưới đây làm tròn6chữ số, tính từ đủ10blocks mỗi nhóm.

D là `experiments/simulator/results/rq2-fresh-graph-source-robustness-20261109-03`. P là `artifacts/akt/local-tests/akt-research-runner-20261108-01`. Outer `P/rq2-fresh-graph-recovery03-outer/final.json` thực ghi `ACCEPTED59_RECOVERY_COMPLETE_PRIMARY120_NO_INFERENCE`, error=null, elapsed30.888886900036596s, cleanup=true/Job0 và nguồn trước–sau bằng nhau. Plan SHA59cf05947f0d2ff184af99070b5b58fe771b5e3134fb1e1c71241d3eb46a7ea2.

## Kiểm population và recovery

Đã so từng thành phần của `D/outcomes.json`:61rows đầu bằng ledger COMPLETED_CELL F001–F061 ở parent02,59rows sau bằng child_outcomes.json. Các identities/scalars và outcome binary64 đều khớp.120outcome keys duy nhất,60Q keys và30K keys đúng đủ grid21010–21019×ability1000/1150/1300×λ0/.55. Tính lại cả60Q từ hai outcomes và30K từ haiQ không có mismatch. Shared input copy bằng byteSHA với parent.

Đọc trực tiếp hai trace parent, chỉ lấy F062, và so nguyên line body với30rows đầu của child. Cả observable và oracle đều30/30exact, initial-F062.json có cùng SHA. Prefix receipt `/status=STRICT30_PREFIX_EXACT_BEFORE_STEP31`, `/rows=30`.20high controls bằng nguyên các fields của parent proof, đủ10blocks×full/learned, mỗi pair120observable/120oracle rows và endpoint_exact=true.

Logical primary gồm120worlds/14400responses. Parent61complete được dùng lại, partial30 của F062 bị loại khỏi primary và giữ audit. Physical gồm121world constructions và121policy builder calls, với14430responses bao gồm30responses replay. Child có59environment constructor returns,59policy builder returns và7080select/predict/interact/update returns, được outer ghi đủ. Không thêm scientific RNG draw hoặc block mới trong recovery. Primary study dùng10blocks21010–21019, khác3blocks21000–21002 của E9. Không gọi child là10blocks bổ sung lần nữa. Nguồn là `summary.json#/primary_projection`, `/primary_worlds`, `/primary_responses`, `/physical_constructors`, `/physical_response_calls`, `/duplicated_replay_exposures`, cùng `parent_reference.json#/complete_cells` và `/excluded_partial_rows`.

## Bốn phát hiện mô tả

### 1. Q vẫn đổi dấu giữa blocks ở mọi mức năng lực

Q=Y_expert−Y_learned. Y là mean net latent theta trên28concepts tại cùng endpoint ngày41, đơn vị theta/Elo points. Expert/learned chỉ đổi estimator graph. Environment/controller expert graph, S=P on/L off và nguồn learned graph cố định được giữ. Cùng artifact identity và topology SHA với E9, không fit learned graph mới.

| Ability | Mean Q λ0 | Mean Q λ.55 | Block dương/âm tại mỗi λ |
| --- | ---: | ---: | --- |
|1000|+0.078604|+0.083100|7/3|
|1150|+0.005212|+0.029742|6/4|
|1300|+0.116623|+0.116623|4/6|

Không có Q=0 trong60components. Mean dương không đồng nghĩa thắng ở mọi hoặc đa số blocks. Đặc biệt1300 có6/10Q âm dù mean dương. Range tại1300 là−0.209597 tới+1.368711. Nguồn là `graph_source_contrasts.json#/i/expert_minus_learned`, với i theo bảng pointer ở cuối. Mean/count chỉ là mô tả finite blocks, chưa practical significance hoặc xếp hạng graph quality.

### 2. Dấu K1150 của E9 không được lặp lại đồng loạt

K=Q(λ.55)−Q(λ0), cùng đơn vị theta/Elo points.

| Ability | Mean K | Dương/âm/zero trên10blocks |
| --- | ---: | --- |
|1000|+0.004496|6/4/0|
|1150|+0.024530|8/2/0|
|1300|0|0/0/10|

E9 có K1150 âm ở cả3blocks21000–21002. Study mới có8dương/2âm, nên nhận định dấu âm ổn định ở1150 không được dữ liệu mới hỗ trợ. Không suy đây là statistical reversal hoặc causal ability law. Nguồn mới là `conditional_lambda_contrasts.json#/i/lambda_difference` ở i={1,4,7,10,13,16,19,22,25,28}. Nguồn cũ là `research_tracking/runs/rq2-learned-graph-ability-20261109-01/native__conditional_lambda_contrasts.json` tại `/1/lambda_difference`, `/4/lambda_difference`, `/7/lambda_difference`, lần lượt−0.03515034511452697/−0.03827404092357689/−0.036009495991581986.

### 3. High-ability negative control tiếp tục tách hai câu hỏi

Cả10K1300 bằng0, phù hợp20high λ-pairs đã được kiểm semantic trace và endpoint exact. Đây là zero đã biết trước từ world condition, không10bằng chứng độc lập rằng graph không có tác dụng. Đồng thời Q1300 đều khác0 và có cả hai dấu. Vì vậy khác biệt expert–learned không thể được đồng nhất với riêng world prerequisite penalty. Điều này giữ kết luận có điều kiện của E9, chưa xác định signal, adaptation, action path hay challenge là mediator.

Nguồn là `conditional_lambda_contrasts.json#/i/lambda_difference` với i={2,5,8,11,14,17,20,23,26,29}, Q1300 ở bảng pointer, và `high_controls.json#/i/{block,graph,observable_rows,oracle_rows,endpoint_exact}` với i=0..19. Hash learned artifact ở `admission.json#/learned_artifact_identity` bằng E9 `a51fbf935be3dda0ee2d89c2ebe61ce736a2c87d7fe604c126f79f77e73cbb7a`, topology SHA `b7a76280175dba1e6119426b341172b9a1537c94a59655f5fc5537f7a3f2829c`.

### 4. Tất cả60cặp trajectory có phân kỳ câu hỏi

Tính tổng `trajectory_pairs.json#/i/question_id_differences`, i=0..59, được4936/7200ordinal positions. Cả60cặp có ít nhất một question difference. Trường `/i/labels_equal_before_first_question_difference` đều true. E9 cũng có cả18cặp phân kỳ,1409/2160positions. Hai tỷ lệ thuộc populations khác nhau, không là phép kiểm tăng/giảm effect.

Sau phân kỳ, cùng ordinal không bảo đảm cùng query/history. Không dùng chúng làm paired response LL, mastery mediation hoặc chứng minh lợi ích học trên người. Việc tính lại các counts này không sinh thêm responses.

## Pointer sets để kiểm lại mọi nhóm

Mỗi entry Q dùng `/i/expert_minus_learned`, mỗi entry K dùng `/i/lambda_difference`. Mean là tổng10giá trị chia10, signs từ nguyên giá trị chưa làm tròn.

| Ability | Q λ0 indices | Q λ.55 indices | K indices |
| --- | --- | --- | --- |
|1000|0,6,12,18,24,30,36,42,48,54|1,7,13,19,25,31,37,43,49,55|0,3,6,9,12,15,18,21,24,27|
|1150|2,8,14,20,26,32,38,44,50,56|3,9,15,21,27,33,39,45,51,57|1,4,7,10,13,16,19,22,25,28|
|1300|4,10,16,22,28,34,40,46,52,58|5,11,17,23,29,35,41,47,53,59|2,5,8,11,14,17,20,23,26,29|

## Những điều chưa được suy ra

Đây là10paired seed blocks, không120independent learners hoặc14400independent measurements. Một fixed learned graph, một GAM variant và finite simulated worlds chưa xác lập edge truth/confidence probability, calibrated controller benefit, Junyi hoặc neural model efficacy. New initial-state proof dùng actual child59 và sealed parent61, mạnh hơn giả thiết reconstructed expert initial của E9, nhưng không biến3blocks cũ thành cùng population với10blocks mới. Không pooling hai studies hoặc đặt thêm p-value/CI. Full proposal/main matrix và RQ completion vẫn còn riêng.

## Pins của dữ liệu đã đọc

| Artifact | SHA-256 |
| --- | --- |
| P/rq2-fresh-graph-recovery03-outer/final.json | 3cdd399ec6a94a17e0178dec76b416b87ed406ddef701a0d1cb420e2486c90d8 |
| D/outcomes.json | 35f6603726f21d717e1da8e75ada8369584fcdcbbacbf3d170981e027dd662fa |
| D/graph_source_contrasts.json | 645b395c81eedea3d42a7ebfb6521e1be0c14aeafa70eb3412468100f22de330 |
| D/conditional_lambda_contrasts.json | f48f5ec7f6683d8285288a5bffa05e46be2365d244aa83990c6797b43a721a38 |
| D/trajectory_pairs.json | 5c8f6a0dcdf2ec8c3783fb45d589b1d991664e628b4c1a360d94852d2b565f4d |
| D/high_controls.json | 026adf45ff9022cd5928b237e90c371daffff62b6bb287ae881ddf468987668c |
| D/prefix_parity.json | daa50a6d6d1c8cfd3701f48752e15f1eb910e69498c709111a15f6c11f39b2cf |

Note không cấp quyền chạy hoặc sửa artifacts. Root giữ việc đóng bundle và báo cáo canonical.
