# Đề xuất gói confidence Junyi TRAIN80 cho A2/A3

Ngày12/11/2026. **PROPOSED_ENGINEERING_CONTRACT_PENDING_ROOT_FREEZE**. Gói này đọc source và protocol hiện hành để xác định bước triển khai tiếp. Chưa fit, đọc learner logs, tạo confidence hoặc cấp quyền sử dụng cloud. Source/model/test đang freeze phục vụ lượt AKT hiện hành được giữ nguyên.

## 1. Đích cần đạt

Một lượt surrogate TRAIN80 cung cấp confidence cho expert graph và learned graph. A2/A3 chia sẻ đúng artifact trong từng topology. A1 learned lấy topology đã nghiệm thu và confidence1. Graph/confidence giữ nguyên qua neural refit90 theo Recipe26. Các điều kiện A0, A1/A2/A3 expert/learned trên Junyi vẫn thuộc matrix KLTN.

Semantics giữ `conditional_predictive_stability_not_edge_truth_probability`. Điểm phản ánh độ ổn định của cải thiện dự báo surrogate trên TRAIN. Diễn giải Junyi giới hạn ở quan hệ dự báo trong logged sequence. Thứ tự luyện và kênh năng lực vẫn cần các control của RQ1/RQ2.

## 2. Primitive hiện có và chỗ cần adapter

Nguồn [edge_confidence.py](../../../src/knowledge_tracing/edge_confidence.py), [artifact loader](../../../src/knowledge_tracing/edge_confidence_artifact.py), [Method24 đã chốt](../../reports/edge_confidence_method24_plan_20261108.md).

| Hàm/kiểu | Dùng trong Junyi |
|---|---|
| `EdgeConfidenceRecipe` | Giữ seed42,3learner-fold, Laplace1, support scale5, C1, tol1e-6, max_iter200, clip1e-6,200bootstrap, min20eligiblelearners |
| `EdgeRuntimeBinding` | Ghim actual NumPy/sklearn versions, lock và source trước/sau |
| `label_free_fold_assignments(recipe, plan_sha256, learner_ids)` | Tái dùng mapping whole learner, có hash plan label-free riêng Junyi |
| `label_free_bootstrap_seed(recipe, plan_sha256, learner_ids, parent_id, child_id)` | Tái dùng deterministic seed, correctness hash nằm riêng ở provenance |
| `_mean(successes,count)`, `_support(count)` | Tái dùng chính xác smoothing và support transform |
| `_fit_one(x,y,recipe,runtime)` → `_FitOutcome` | Tái dùng public sklearn LogisticRegression, các trạng thái thiếu lớp/convergence/exception |
| `_probabilities(fit,x)` | Tái dùng trên sequence có truthiness xác định. NumPy matrix cần adapter vì source dùng `if not x` |
| `_loss(y,p,clip)` | Tái dùng paired binary Log Loss |
| `OOFRow`, `EdgeSummary`, `_summarize_edge(rows,recipe,seed,fits_supported)` | Là chuẩn đối chiếu estimand/flags. Xử lý một edge mỗi lần, benchmark RAM/time trước quy mô lớn |
| `_acyclic(nodes,edges)` | Tái dùng kiểm DAG |

Các orchestration hiện có giới hạn Grade10 và cần entry Junyi có lineage riêng.

- `prepare_train_lagged_rows` nhận `PublicRoleData`, `SimulatorBank`, `ResearchSplitPlan`. Prepared giới hạn48learners,210events/learner,10.080rows,28concepts.
- `fit_crossfit_edge_confidence` lặp toàn bộ ordered pairs, cap2.352fits/272.160edge-OOF rows và110giây active. Prepared giữ tuple/dense concept counts.
- `select_positive_dag` yêu cầu complete allpairs và edge budget tối đa31.
- `Method24TrainingBinding`/`load_method24_scores` yêu cầu đúng10public files của simulator và bank. `research_graph_condition._scores` nhận learned graph đúng28nodes/31edges.
- Source features Method24 lịch sử dùng toàn bộ history trước target, với tổng concept counts bằng global rank.

Gói Junyi cần typed plan, prepared features, artifact binding và loader riêng. Các điều kiện Grade10 tiếp tục gắn implementation/artifact lịch sử. Adapter Junyi nhận records từ train window cache đã nghiệm thu để giữ ranh giới dữ liệu.

## 3. Features và history scope phải chốt trước fit

Đề xuất extension `junyi-native-window-conditional-surrogate-v1`, giữ numeric recipe Method24, ghi rõ history scope Junyi. Đây là extension cần ROOT freeze trước thực thi. Source Method24 lịch sử và Recipe26 có phạm vi history khác nhau, nên chỉ thay input path sẽ tạo phép so sánh thiếu nhất quán.

Tại target global rank r, dùng native `WindowInputs` có đúng context100/targetblock100/OOV reset. Prefix là các vị trí `[0,j)` trong window hiện tại, responses tương ứng `prior_responses[1:j+1]`. Số quan sát có thể tới199 trước target cuối block. Tại rollover rank200, native start thông thường là100. Luật này cần được tái dùng từ window cache, thay vì tự áp dụng một cửa sổ trượt100event.

Gọi m(s,n)=(s+1)/(n+2), h(n)=n/(n+5). Base có bốn features `m_child,h_child,m_overall,h_overall` tính trên cùng prefix. Overall past mean/support là control cho kênh năng lực chung có thể quan sát. Augmented thêm `m_parent,h_parent`, cũng trên prefix đó. Current correctness chỉ là y nối bằng source row sau khi feature row được tạo. Learner ID dùng grouping/fold, source row dùng alignment. Tất cả target rows chỉ lấy ở `target_mask=True` để mỗi target xuất hiện một lần.

Full train window cache của nhánh chính chứa232.662windows/13.347.331targets/126.774learners. Những số này là đầu vào lập workload do nhánh chính cung cấp, cần ghim manifest của cache khi execution. Gói thiết kế này chưa mở lại cache. Encoding TRAIN80 và learner role identity phải khớp artifact confidence. Selection/calibration/outer-validation/Holdout không cung cấp fit rows hoặc tiêu chí chọn candidate pool.

## 4. Candidate pool hữu hạn, độc lập correctness

[Protocol21 §4](../../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md) cho phép freeze finite candidate pool trước fit. Đề xuất pool learned chỉ dùng TRAIN interaction identities/order, giúp phân biệt rõ với declared expert graph.

1. Với mỗi TRAIN target, lấy tối đa4exercise khác child, gần nhất và phân biệt nhau trong đúng native prefix. Việc duyệt prefix bắt đầu lại theo window/OOV geometry. Chỉ dùng exercise IDs và learner IDs để đếm.
2. Đếm số learner đồng quan sát cho từng directed pair trong tập gần nhất trên. Mỗi learner chỉ góp một lần/pair, dùng tập hữu hạn trong learner rồi cộng vào bảng count. Tập candidate chưa vượt universe TRAIN exercise pairs, không tạo learner×edge×event tensor.
3. Giữ candidate có ít nhất20learner, chọn tối đa4parent/child theo count giảm dần, tie theo cặp ID cố định. Freeze K4, tie rule, candidate table và SHA trước khi fit hoặc nhìn selection. Đây là scope learned candidate từ recency/co-observation, cần ghi trong kết luận.
4. Pool scored là hợp của toàn bộ expert edges và learned candidate pool. Learned topology chỉ được chọn trong learned pool. Expert edges luôn có bản ghi, kể cả endpoint chưa fitted hoặc support thiếu. Chia sẻ baseline fits/edge scores khi pair trùng nhau.

Với C=717TRAIN exercises đã được nhánh chính kiểm, learned pool tối đa4C=2.868pairs. Expert graph đã tái dựng có835nodes/976edges. Union scored tối đa3.844pairs trước dedup/support screening. Một pass tạo pool cần tối đa4update/target ở bước gần nhất, khác với quét mọi parent ở mỗi event. Phải đo thời gian và số cặp thực trước cấp fit budget.

Pool này phụ thuộc practice order. Nó chưa thiết lập prerequisite causality. Order-only và matched graph controls của RQ2 vẫn cần được giữ để giải thích kết quả.

## 5. Fit, OOF và bootstrap giữ cùng estimand

- Ba fold theo whole TRAIN learner. Plan seed/hash chỉ lấy từ role IDs, geometry, config và pool label-free. SHA nguồn có correctness giữ ở provenance riêng.
- Với mỗi child/fold, baseline fit trên mọi child rows của hai fold còn lại. Augmented fit đúng cùng row IDs/y, kể cả rows parent chưa xuất hiện. Baseline fit được dùng lại qua các parent.
- Hai lớp là điều kiện trên mỗi tập FIT. Eligible OOF có một lớp vẫn giữ binary Log Loss. ConvergenceWarning, chạm200iterations, exception hoặc nonfinite cho unsupported có reason.
- Eligible evaluation khi parent có ít nhất một observation trong native prefix. Base/augmented loss dùng cùng target IDs. Giữ full child denominator, eligible/excluded counts và counts theo fold.
- Với learner i, lấy trung bình paired loss delta trên eligible targets của learner đó. `Delta_e` là trung bình các learner deltas, cùng trọng số cho từng learner. Đây là estimand của `_summarize_edge`; primary response-weighted LL của benchmark neural có vai trò riêng.
- Bootstrap200draw trên eligible learner deltas đã frozen, PCG64/seed/order theo Method24. Confidence là fraction bootstrap mean lớn hơn0, tie0 giữ quy tắc cũ. Supported score0 và unsupported null được lưu riêng. Min20eligiblelearners là điều kiện tối thiểu.

Source `_summarize_edge` tạo matrix200×Nlearner và lặp Python kiểm từng index. Ở N=126.774, riêng int64 index matrix khoảng193,4MiB. Cần benchmark phần này cùng logistic fit. Nếu phải xử lý theo block để giảm RAM/time, giữ cùng PCG64 draw stream và exact `math.fsum` sign trên từng draw. Đối chiếu kết quả/indices với primitive cũ trên fixtures trước production. Các thay đổi chỉ số hóa/buffer phải giữ nguyên Delta/confidence và schema semantics.

## 6. Learned DAG, expert weights và bind vào A2/A3

Theo Protocol21, learned edge budget bằng số expert edges có cả hai endpoint thuộc TRAIN-supported vocabulary. Bước thực thi phải tính đúng scalar này từ graph/vocabulary đã ghim trước fit. Số31 thuộc accepted Grade10 artifact; số976 là full Junyi declared edge count. Hai số này không tự xác định Junyi learned budget.

Rank các candidate learned supported có finite Delta>0 theo `(-Delta,parent,child)`, greedy thêm cạnh nếu giữ DAG tới budget đã freeze. Giữ đầy đủ node domain, gồm isolated/unfitted nodes. Nếu thiếu positive supported edges hoặc bị cycle constraint, trả `UNSUPPORTED_EDGE_BUDGET` và giữ diagnostic. Required learned conditions vẫn được ghi là chưa đủ điều kiện, cần quyết định xử lý có truy vết. Giá trị confidence không được dùng để đổi ranking rule.

Expert A2/A3 giữ topology declared đầy đủ. Unsupported edge có null/reason và operational weight0; supported score0 vẫn mang trạng thái supported. Learned A2/A3 dùng đúng topology/weights của artifact đã nghiệm thu. A1 learned dùng topology đó với confidence1. Artifact graph/confidence fitTRAIN80 được giữ qua neural refit90; temperature calibration dùng luồng riêng theo Recipe26.

## 7. Artifact tối thiểu và cấu trúc streaming

Hai lớp triển khai kế tiếp được đề xuất là core Junyi prepare/fit và typed Junyi artifact loader, với CLI hữu hạn dùng research tracking/output hiện có. Cần giữ các dữ liệu sau.

- Plan/config/source/runtime/input hashes, TRAIN-only role/vocabulary/window-cache lineage, candidate pool provenance, geometry/history scope, fold map và execution budget.
- Fit ledger từng baseline/augmented fold, physical fit count, row-ID hash, classes, coefficients/intercept, n_iter/warnings và unsupported reasons. Sklearn models phục vụ fit hiện hành, artifact dùng tham số số và ledger.
- Baseline OOF table theo child, có learner/source IDs, fold, y và probability. Edge outputs tham chiếu cùng ordered child-row IDs, lưu augmented probabilities/validity/eligibility. Có thể dùng Parquet hoặc numeric shards để tránh lặp mọi identity trong CSV.
- Learner deltas, edge summaries đầy đủ, accepted DAG hoặc unsupported result, resources/failures và SHA inventory. Một edge/child được xử lý trong RAM mỗi lần, không giữ dense Ntarget×Cconcept matrix hoặc toàn bộ edge-OOF Python objects.
- Marker complete chỉ sau khi mọi candidate đã có result/unsupported record, output counts khớp plan, hashes và resource acceptance đạt. Các lượt bị dừng có partial ledger và failure receipt.

Khi thêm adapter ndarray cho `_probabilities` hoặc streaming summary, test phải đối chiếu số học/flags với helpers cũ. Loader Junyi nhận đúng TRAIN/vocab/pool/topology version của artifact. Typed simulator binding giữ phạm vi lịch sử của nó.

## 8. Workload và acceptance trước fit chính

Cho K là số scored pairs sau screen và C_child là số child cần fit, upper bound physical logistic fits là `3*(C_child+K)`. Bound thô C_child≤717 và K≤3.844 cho13.683fits. Đây là bound từ thiết kế, chưa measured runtime. Full allpairs835nodes cần2.091.675fits ở ba fold. Số OOF predictions cần dự toán bằng `sum_c N_c*(1+K_c)` thay vì chỉ đếm số cạnh.

Các prerequisite theo thứ tự cần làm trước khi cấp lượt CPU lớn.

1. Freeze extension history scope, K4/pool/tie rule, source identity và target edge budget trước fit. Ghi quyết định trong tracking, giữ cả expert/learned model conditions.
2. Kiểm metadata TRAIN child sizes/class counts, candidate support và mức lớn nhất N_c/Neligible. Chỉ có metadata/pilot phù hợp mới định RAM/output caps.
3. Nghiệm thu synthetic current/future-answer invariance, native rollover/OOV, whole-learner exclusion, equal-fit rows, equal-learner estimand, unsupported handling, bootstrap parity, DAG ties/cycles và loader drift.
4. Bounded CPU pilot đề xuất tối đa8pairs được chọn bằng ID hash trước khi xem outcomes, tối đa48baseline+augmented fit attempts, cùng solver/feature recipe. Resource/timeout và cohort pilot phải được chốt riêng. Kết quả pilot dùng kiểm lifecycle/cost, có nhãn phạm vi riêng.
5. Đo rows/fit, seconds/fit theo child size, feature-prep cost, bootstrap cost và bytes/OOF row. Dự toán tổng CPU/RAM/storage từ workload thực và đơn giá đã kiểm. GPU không phải dependency của surrogate này.
6. Chỉ mở fullTRAIN confidence run khi cap tài nguyên, checkpoint ledger/resume theo đơn vị child/edge, stop-on-failure/budget và artifact contract đã nghiệm thu. Không có quyền chi mới từ tài liệu này.

Acceptance khoa học của artifact không phụ thuộc số cạnh được hỗ trợ hoặc confidence cao. Sau confidence artifact hợp lệ, A2/A3 còn cần Junyi native-adapter/checkpoint/CUDA tests và các neural selected fits riêng. Confidence hoàn tất chưa đồng nghĩa RQ3 hoàn tất.

## 9. Trạng thái và bước kế tiếp

**Thiết kế sẵn để ROOT review, chưa implementation hoặc fit.** Điểm cần chốt là extension native-window so với history toàn bộ của Method24 lịch sử và finite learned candidate pool. Protocol21 đã dành bước freeze pool trước fit cho nhóm. Giữ traceability về mọi condition chưa chạy và lý do, gồm trường hợp learned budget không được đáp ứng. Bước kỹ thuật tiếp theo là typed plan/features không fit và các ca parity, sau khi nguồn AKT hiện hành được nghiệm thu.
