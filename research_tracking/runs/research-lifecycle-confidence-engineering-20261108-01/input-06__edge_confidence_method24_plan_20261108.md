# Method24: surrogate confidence train-only — đề xuất hữu hạn trước implementation

Ngày 08/11/2026. **APPROVED_ENGINEERING_IMPLEMENTATION_NOT_FIT_AUTHORIZATION**. Cụ thể hóa [protocol21 §4](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md). ROOT đã review hướng và cho phép implementation sau hai clarification dưới đây; chưa fit/test hoặc cấp quyền dùng graph trong nghiên cứu. Không thêm neural model. [Source plan](edge_confidence_method24_plan_20261108.sources.json) ghi SHA đã đọc, không giả primary-paper/author parity cho surrogate do nhóm thiết kế.

## 1. Input, population và API nhỏ

Recipe ID đề xuất `train-lagged-edge-confidence-v1`. Input thực tế sẵn có là public **TRAIN48×210 = 10.080 events**, bank84items/28concept của [corpus đã kiểm](simulator_development_corpus_20261108.md). Không collect lại. Candidate pool đúng toàn bộ 28×27 = **756 ordered nonself pairs** `(parent, child)`, thứ tự IDs theo chuỗi Unicode; không nhận G_env adjacency/true-edge labels, profile, latent state hoặc difficulty làm đầu vào estimator. Budget learned DAG là scalar31 do caller ghi trước, không mở expert-edge labels để rank.

Module dự kiến duy nhất `src/knowledge_tracing/edge_confidence.py`, tests `tests/shared_kt/test_edge_confidence.py`. API đề xuất, chưa implementation:

```python
prepare_train_lagged_rows(train: PublicRoleData, bank: SimulatorBank,
    plan: ResearchSplitPlan, *, expected_train_provenance_sha256: str,
    expected_train_observable_sha256: str, recipe: EdgeConfidenceRecipe,
    limits: EdgePreparationLimits) -> PreparedEdgeConfidence
fit_crossfit_edge_confidence(prepared: PreparedEdgeConfidence, *,
    expected_prepared_sha256: str, runtime: EdgeRuntimeBinding,
    limits: EdgeFitLimits) -> EdgeConfidenceResult
select_positive_dag(result: EdgeConfidenceResult, *, edge_budget: int
    ) -> LearnedGraphResult
```

Các dataclass sealed/frozen, recipe và limits bắt buộc caller cung cấp; không auto-fit trong constructor. Runtime binding bắt buộc versions NumPy/sklearn, lock SHA và method-source SHA; actual public fit kiểm versions đã import, còn lock/source bytes phải do outer ghim/kiểm trước-sau vì module không file I/O. Module không collector/model-adapter/trainer/controller integration, không import Torch. Fit mới import public NumPy/sklearn. Prepare kiểm `role=='train'`, typed observable roundtrip, learner assignments/seed families disjoint theo plan, đúng bank/provenance/observable SHA, chronology/domain và full population; chưa fit nếu nguồn hoặc bytes drift. Caller-supplied hashes là cooperative bindings, không độc lập attestation caller.

Current public corpus reader mở9publicinputs+DONE để kiểm toàn corpus. ROOT đã chấp nhận boundary **train-only optimization**: orchestration khai rõ lần đọc public selection/calibration phục vụ schema audit; chỉ truyền `role_data('train')` cho API này, không cần thêm loader. API không nhận `PublicResearchCorpus` hay trajectories selection/calibration/final, không dùng nhãn các vai đó để chọn features, regularization, folds, eligibility hay graph. Không gọi đó là train-only file-access.

## 2. Features và cross-fit đã xác định

Trong mỗi learner, duyệt đúng saved chronological order. Tại event target concept `c`, **emit feature row trước khi cộng đáp án hiện tại**. Với một lịch sử có `s` đáp án1 trong `n` events: `m(s,n)=(s+1)/(n+2)` và `h(n)=n/(n+5)`. Khi n=0, mean feature0,5 và support feature0 là Laplace prior, không phải fallback prediction.

Base4features theo thứ tự: `m_child, h_child, m_overall, h_overall`; augmented6 thêm `m_parent, h_parent`. Child/parent history gom mọi item của concept, overall gom mọi event trước đó của learner. Không đưa timestamp, source_row, learner ID, current/future y, difficulty, item-ID embedding hoặc profile vào X. Learner/source IDs chỉ làm ledger/fold grouping. Không scaler: cả6features đã bounded[0,1]; không fit normalization trên held-out learners. Update history chỉ sau emit và lưu current y làm target.

Fold seed42. Sort ordered TRAIN learner IDs trước; với mỗi learner sort theo `(identity_hash([recipe_id,'fold',42,plan_identity,ordered_train_learner_ids,learner_id]), learner_id)`, assign fold=`rank % 3`. Với48learners đúng16held-out/fold,32training/fold. Đây là balance số learner, **không stratify profile hoặc labels**. Lưu toàn bộ mapping+hash trước fit. Fold seed cũng không dùng full train SHA chứa nhãn. Held-out learner không có bất kỳ row nào trong fit của fold; lịch sử past của chính họ được dùng để tạo test features theo sequential prediction contract, không dùng để fit coefficients.

Với mỗi child và fold, baseline fit trên **tất cả child-target rows của32training learners**. Với mỗi parent khác child, augmented fit trên **đúng cùng row IDs và y**; không lọc training rows theo parent eligibility. Baseline fit reuse qua27parents. Không sample/class reweighting, không resampling fit rows, không warm start. Các augmented rows n_parent=0 vẫn có prior features.

## 3. Solver, support và estimand chính xác

Đề xuất public `sklearn.linear_model.LogisticRegression(C=1.0, l1_ratio=0.0, solver='lbfgs', tol=1e-6, max_iter=200, fit_intercept=True, class_weight=None, random_state=42, warm_start=False, verbose=0)`. L2 qua `l1_ratio=0.0` là API thực đọc trong sklearn local1.9.1; không dựa default penalty đang deprecated, không đặt `n_jobs` deprecated. Float64, fit tuần tự, BLAS/OMP thread1 ở outer, không joblib/process workers. Ghi class ordering `[0,1]`, coefficients/intercept, iterations và warnings; không pickle model.

Training fold thiếu một lớp, ConvergenceWarning, exception, nonfinite parameters/probabilities hoặc `n_iter_>=200` → fit unsupported. Ngưỡng iteration này là guard bảo thủ: không giả lần chạm cap là convergence proof. Baseline lỗi ảnh hưởng mọi edge tới child; augmented lỗi chỉ edge đó. Không tự đổi solver/C/iterations hoặc trả probability0,5. OOF predictions luôn từ learner-held-out fit; **không refit full train** để thay OOF.

OOF full child denominator `N_c` gồm mọi child-target row của48learners. Với edge e=(p,c), eligible target khi `n_parent(history before target)>=1`. Dùng **cùng eligible target IDs** cho cả baseline/augmented losses. Mọi target ineligible vẫn xuất ledger+reason; không impute score hoặc drop khỏi denominator không báo. Báo `N_c`, eligible targets, excluded targets, eligible learners, eligible-label counts và theo fold. Edge cần ít nhất20eligible learners và đủ3fold fits hợp lệ; thiếu thì c=null+reason, không giả cạnh sai. **Hai lớp là điều kiện của tập FIT trong từng child-training fold**, không phải điều kiện để giữ subgroup OOF: binary LL/paired delta vẫn xác định nếu eligible OOF labels chỉ có một lớp; ghi `unary_evaluation_labels=true`, không tính AUC và không drop subgroup vì lý do này.

Clip cả probabilities vào `[1e-6,1-1e-6]` chỉ khi tính binary Log Loss: `ell(y,p)=-y*log(p)-(1-y)*log1p(-p)`. Với eligible rows J_ei của learner i:

`d_ei = mean_{j in J_ei}[ell(y_j,p_base_j)-ell(y_j,p_aug_j)]`.

Điểm edge là **`Delta_e=mean_{eligible learners i} d_ei`**, mỗi learner trọng số bằng nhau. Dương nghĩa augmented giảm response Log Loss trên population eligible này. Không pooled-event mean hoặc mean của3fold means. Base/aug fit objective vẫn row-unweighted; đó là khác biệt được công bố với estimand evaluation equal-learner. Báo thêm full child coverage, không so Delta của edge khác eligibility như một causal effect.

Bootstrap đúng200 replicates, **không refit**: sort eligible learner IDs, vector d_ei theo thứ tự đó. Seed integer lấy big-endian8bytes đầu SHA256 của canonical identity JSON `[recipe_id,'learner-bootstrap',42,plan_identity,ordered_train_learner_ids,parent_id,child_id]`. Không dùng fulltrainSHA chứa labels; fulltrainSHA vẫn ghim riêng provenance. Eligible IDs phụ thuộc strictly-past parent event counts, không phụ thuộc đáp án. Dùng `numpy.random.Generator(numpy.random.PCG64(seed))`, mỗi replicate draw n eligible learner indices with replacement, lấy mean d_ei; `c_e = count(bootstrap_mean>0)/200`. Vì seed và ordering label-free, resamples giữ paired dưới label perturbation/negative controls khi event identities giữ nguyên. Tie0 không positive. Ghi seed, n, positives và score lattice0,005. Đây là **conditional predictive-stability score** của frozen OOF surrogate trên cùng một source world/corpus; không P(edge true), p-value, calibrated probability, graph-realization uncertainty hoặc proof causal prerequisite. Không dùng true-edge labels/noise-generator labels trong fit/ranking/bootstrap.

## 4. Learned DAG và artifact contract

Lấy supported edges có finite `Delta_e>0`, sort `(-Delta_e,parent_id,child_id)`; không dùng c_e để đảo thứ tự. Greedy từ graph rỗng28nodes, thêm p→c nếu không self/duplicate và chưa có path c→p; tiếp tục tới31edges hoặc hết candidates. Nếu thiếu31 vì support/positivity/cycles: status `UNSUPPORTED_EDGE_BUDGET`, giữ partial diagnostic rõ nhãn, **không fill bằng edge nonpositive/unsupported/random/expert** và không cấp graph binding cho downstream. Không chọn budget theo output đẹp. Edge table vẫn có đủ756rows; score null có reason tách biệt c=0.

Artifact dự kiến do một outer đã được ROOT approve ghi vào output mới riêng, không thêm file vào canonical17corpus. Module trả typed objects, chưa tự publisher hay tạo folder. Population artifacts tối thiểu: recipe+dependency/source/input bindings; learner-fold mapping; baseline fit ledger84fits; augmented fit ledger2268fits (coefficients/intercept/warnings/n_iter/row-ID hashes); baseline OOF10080rows; edge OOF ledger272160rows gồm identity/fold/y/p_base/p_aug/eligibility/paired loss; learner deltas tối đa36288rows; edge summaries756rows; graph result; resource/failure/result receipt và SHA inventory. Float xuất roundtrip17digits, finite-only; thứ tự canonical. Outer cap đề xuất tối đa96MiB cho OOF ledger,128MiB toàn output; cap breach giữ partial+failure, không complete marker. Không serialize fitted sklearn pickle hay latent/oracle state.

Input bindings ghim corpus/DONE/plan/bank/train manifest/train JSONL/train provenance, method recipe/fold/source SHA và exact dependency lock/version. G_env identity được phép giữ như **provenance opaque**, không đưa adjacency/labels vào estimator. Artifact phân biệt `COMPLETE_CONDITIONAL_SURROGATE` và graph `SUPPORTED_DAG`/`UNSUPPORTED_EDGE_BUDGET`; marker không thay outer success+resource+cleanup+posthash acceptance. Không tự nối confidence vào AKT/Graph-GAM/GKT.

## 5. Finite source/test/run plan để ROOT review

Workload đầy đủ là **84 baseline +2268 augmented =2352 fits**, không phải756fits. Ba folds tạo tổng564480training-row appearances và282240OOF row predictions nếu baseline reuse và augmented predict all child rows; đây là logical counts từ10.080targets, không measured throughput. Tối đa200iterations/fit, không hyperparameter search. Không có measured evidence hiện tại rằng2352fits sẽ hoàn tất120s.

ROOT đã approve source/test implementation với hai clarification: unary OOF vẫn được score và label-free bootstrap/fold identity. Meaningful synthetic tests phải chứng minh current/future-answer invariance; strictly-past parent eligibility; whole-learner fold exclusion/balance/hash repeatability; base/aug exactsame fit rows; correct feature hand calculations; eligible paired-denominator/equal-learner versus pooled counterexample; bootstrap seed/ties/200replicates; one-class FIT/convergence/nonfinite unsupported; unary OOF được giữ; DAG asymmetric direction/cycle/tie/insufficient31; role/source/provenance drift rejection. Test fixtures không chứng minh actual48learner fit. ROOT-only thực thi bounded tests; chưa đề xuất chạy actual fit trong batch implementation.

Actual fit tương lai cần ROOT pin source+recipe+output và preflight measured dependency-import RSS/free RAM. Proposed CPU-only phase120s gồm cleanup/finalization reserve10s (active≤110s), RSS≤512MiB và available≥1GiB; CUDAhidden, noTorch, no network/remote/realdata/Holdout. Nếu môi trường không đạt RAM/import floor, không hạ guard. Nếu resource/cap/convergence chặn, giữ partial/failure và không phát confidence/graph complete; không auto-retry, không đổi recipe theo kết quả. Thời gian khả thi chỉ được kết luận sau actual receipt; bước kế tiếp trước mắt là review/implementation, **không fit**.
