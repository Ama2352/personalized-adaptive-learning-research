# Phản biện kế hoạch và điều chỉnh

## Bổ sung09/11 — state RQ1 và core CG-AKT

Đã có peer review nội bộ qua agent độc lập và một phép đối chiếu raw do ROOT viết riêng. [Bằng chứng RQ1](../../research_tracking/reports/rq1_native_mastery_reference_diagnostic_20261109.md) đã đóng92outputs; [core CG-AKT](../../research_tracking/reports/cgakt_research_core_20261109.md) đã đóng74outputs. Các ghi chú self-review ban đầu bên dưới giữ vai trò lịch sử, không phủ nhận vòng review mới này.

| Phản biện | Điều chỉnh được áp dụng |
|---|---|
|90 “crossings” có thể bị hiểu thành90 lần học vượt ngưỡng hoặc90mẫu độc lập |Dùng “bất đồng phân loại khái niệm–thời điểm giữa hai cấu hình”; trạng thái cùng concept có thể lặp qua nhiều thời điểm. Giữ tên field cũ chỉ để đối chiếu.|
|Cửa ngưỡng giống nhau bị suy thành state giống nhau; hai marginal20319 bị suy thành cùng records |000 chỉ đồng nhất hai predicate. Báo riêng từng marginal, không khẳng định giao nếu chưa join; theta là ước lượng model, không truth/learning gain.|
|253bất đồng raw-reference bị gọi thành lỗi calibration; hai số22 bị ghép sai |Không có nhãn truth cho bảng253;5query-M/22rawcriterion là biến khác90M-set và22preview cũ. Không dùng confusion-matrix/causal language.|
|Pi lớn hơn bị coi là định lý của mọi history hoặc độ tự tin kém hơn |Nguồn có Q graph không âm và recurrence đơn điệu khi noise/time-decay cùng điều kiện. Feedback times_forgotten có thể phá ordering decay; chỉ khẳng định dấu đã quan sát, không định lý vô điều kiện hoặc calibration accuracy.|
|18core tests bị nâng thành CG-AKT đã train |Chỉ A3/same-backbone-off,8forward/5backward,0optimizer; confidence trong fixture là metadata dựng sẵn, chưa A1/A2 native matrix hoặc independent fitted A0.|
|GPU sẽ tốn tiền dù forward nhỏ đã đúng |Phát hiện7fullcontext JSON hashes mỗi trainbatch. Cần tối ưu có kiểm chứng và throughput benchmark đại diện trướcpaidtraining; O(W) lookup còn lại là risk cần đo, không tự thêm framework hoặc blocker theo suy đoán.|

Root cũng giữ các failure thật: context01/02 là schema/fixture errors, model01/02 là bank84 và môi trường Git normalization. Sửa controller bằng process-scoped cấu hình đúng hệ thống, giữ nguyên original upstream verification và source; không sửa dữ liệu/validator hoặc bỏ kiểm nguồn. Chưa dùng Holdout/GPU/Modal trong vòng này; RQ1–RQ3 vẫn chưa hoàn tất.

Đây là self-review độc lập về lập luận, không có subagent/reviewer bên ngoài. Có ba pass chính và pass4 kiểm tra runtime làm thay đổi readiness. Giới hạn source/proposal approval identity được công khai.

| Objection | Kiểm tra | Correction hoặc lý do giữ |
|---|---|---|
|Tracking có thể sai hoàn toàn về nguồn |Đã tìm paper2 source và proposal, paper1 notebook |Thay NOT STARTED Graph-GAM thành source available, giữ integrated KLTN pending |
|Zero reentry có thật bị cưỡng bức |P1 PDF continuity filter, notebook không có filter |Không claim invariant mọi DAG, thêm cross-chapter counterexample và source-revision blocker |
|Retention không có tác dụng phân biệt |P2 decay homogeneous/base cố định |Chỉ khẳng định proportional net gain sau T, vẫn order-dependent trước T, soft mastery nonlinear |
|GAM package được gọi edge effect |Local root adaptation thay cùng switch |Factorial local-only/empty controls, edge estimator/controller/env riêng |
|DiD được gắn nhãn cơ học |High/Low khác latent baseline/trends |Paired randomized λ×graph estimand, causal simulator only |
|Junyi true graph vs random đủ causal |Logged order influences exposures |Matched null/order graph/crossfit, no instructional causality |
|Junyi AKT prerequisite simulator |Vocab khác và no mapping |Train separately, sim data/mastery adapter trên critical path |
|Gate-off A3 bằng A0 |Joint training đổi backbone |Same-backbone exact-off test, independent A0 system fallback |
|Oracle confidence lẫn deployment |True labels chỉ simulator |Oracle separate ceiling, main train-only reliability, held graph realization calibration |
|Bỏ SAKT/GKT hoặc learned graph trong PlanA |Proposal trang3–4 yêu cầu |Giữ task và comparator evidence, giảm allocation cần advisor, không call implementation-only complete |
|Epoch early stopping đồng nghĩa nestedKfold |Code inner holdout/outer refit |Count selection+refit cost, không thêm innerKfold |
|BKT pilot invalidates mọi benchmark |Selection fold0 limitation |Giữ historical results descriptive, báo optimism, không retrofit methodology |
|Holdout vẫn untouched với AKT |BKT Test đã xem, published paper2 seeds đã biết |Access ledger, freeze selection, new simulated final seeds, residual analyst adaptation disclosure |
|Synthetic pass bảo đảm pilot/GPU |Current tests fail filesystem publish |Readiness NOT READY, historical Gate2 164 khác current runtime, task filesystem trước GPU |
|os.link publish portable |Checkpoint/export call hard-link |Stage2 filesystem capability/durability acceptance, không sửa model trong planning |
|Costs chỉ tính1 fit AKT |4 variants×CV×selection/refit+sim+baselines |Formula work=(8E+1)D per model5fold, scenarios chưa đo, budget before full |
|Modal budgets chỉ alerts |Official budgets doc có enforced usage/spend caps |Use actual workspace limits+per-run local ledger, account confirmation, timeout reserve |
|PlanB effort vẫn quá lớn |58–78pd và53days |Flag capacity uncertain, milestone03/12 fallbackA, freeze14/12, C ngoài deadline |
|Viết/demo để cuối |Proposal có demo và article draft |Writing tuần1, fixture viewer tuần2, article tuần6, defense buffer |
|Statistical null coi equivalence |CIs conditional model fits |Không claim neutral chính xác nếu chưa equivalence margin/power, báo inconclusive |
|Confidence graph feature dùng future state |Proposed causal parent cache |Current/future perturbation tests, inaccessible true state trong inputs |

## Final quality gate

| Criterion | Verdict | Evidence/gap |
|---|---|---|
|RQ1–3 evidence path |PASS design |02,05 map đầy đủ |
|Ba trap concrete |PASS design |04, E02/E04/E05 |
|Proposal preserved |PASS design conditional |Mandatory models/deliverables giữ, dataset allocation pending S05 |
|Inventory/source evidence |PASS bounded audit |03 + SHA inventory, không raw dataset/Holdout audit mới |
|Paper1/2 reuse justified |CONDITIONAL |Paper1 exact revision thiếu |
|Junyi/simulator compatibility |CONDITIONAL |Train riêng resolved conceptual, mastery contract chưa accepted |
|AKT artifact/recovery contract |PASS design, FAIL implemented readiness |07, tests hard-link failure, no mid-epoch resume |
|GPU budget measurable |CONDITIONAL |Official rates, no measured throughput, ladder prerequisite |
|Owners/dependencies |PASS design |TASKS.json DAG validated |
|Deadline realistic |CONDITIONAL |Capacity assumption và stage5 chưa đo |
|Supervisor decisions identified |PASS |09 S01–07 |
|Adversarial consistency |PASS review, NOT READY execution |Current contradictions become blockers, no auto training |

Biggest unresolved issue là simulator integration contract và adequacy của generated data/mastery decision, vì dù Junyi AKT train thành công vẫn chưa có closed-loop evidence RQ3. Source Paper1 missing revision hạn chế reproduction, GPU filesystem/resume là execution blockers. Kết luận **NOT READY** cho full experiment. Safe engineering batch có thể review và triển khai sau chỉ thị tiếp theo. Không declare convergence từ file existence.

## Cập nhật sau engineering CPU ngày07/11

Các dòng implementation-readiness phía trên là verdict của audit ban đầu. Recovery mid-epoch, selection/refit và public smoke/pilot đã được nối, có actual AKT CPU dropout parity và subprocess export proof; xem17_AKT_RECOVERY_ENGINEERING_LOG.md. CUDA/real-data acceptance vẫn chưa có. Gate2-07 phát hiện Windows long temporary path (271pass2fail), giữ log và không publish; đã sửa tên tạm, kiểm parent/runner51pass và chạy Gate2-08 cho source cuối. Không coi targeted pass là full Gate2 pass trước output.

Review bổ sung đã sửa thất thoát budget lineage khi retry fail trước checkpoint mới: attempt reserve/copy verified pointer trước loader, test chain12.5+7=19.5s. Commit-count là prefix model đã publish; hard kill có thể mất update sau snapshot, cần báo rollback và đo I/O/cadence trước GPU. Tổng wall worker được cộng kể cả import/load/validation/export của failed attempts. Run mới vẫn authorization riêng; không tự tạo retry loop hoặc dùng envelope để tự approve. Global cloud allocation còn cần ledger/limits trước paid execution, không suy hard spending cap từ CPU watchdog.

Trap3 thêm diagnostic trên cùng learner/child opportunities, không thay final protocol. Phản biện “matched degree đã đủ” bị bác bởi missing-parent và exposure counts: chỉ1–7/239learners đổi prior score, intersection96/96/95learners. Kết quả0 không là equivalence/graph-neutral proof. Common subsets khác giữa controls, không xếp hạng hoặc pool chúng như cùng estimand. Không dùng logs để claim instructional causality.

Biggest research blocker vẫn là accepted Junyi/simulator mastery/training contract và confirmatory protocol. Hoàn tất engineering recovery không hoàn tất RQ3; RQ1/RQ2 diagnostic evidence không tự hoàn tất research questions. Các baseline/deliverable bắt buộc trong proposal vẫn giữ. Full CV, Holdout, CUDA và thay scientific methodology vẫn cần đúng gate; phần safe CPU được user cho phép tiếp tục.

Nghiệm thu sau review: Gate2-08 274passed, nofail/error/skip, source-bound pointerverified. Hai lỗi mới đã có regression tests và artifact proof trong cpu-akt-recovery-20261107-01. Software readiness CPU đã cập nhật; research/GPU readiness không nâng theo.

## Review interface simulator–KT

SIM01–03 đã có typed observation/query/session, SHA/domain/recipe binding và native parity. Gate2-09 đạt293pass/no failures/errors/skips264.44s. Raw reference correctness không được tự đổi thành P(K) hoặc boolean mastery; S04 vẫn cần chốt. Source defect double re-anchor có failing/passing regression, không sửa artifacts cũ. Native elapsed-time invariance là architecture limitation; retention phải lấy latent environment, không suy từ delayed KT score.

Phản biện mới: “graph cache past-only nên fair”. Không đủ: bridge full history phục vụ replay, nhưng AKT A0 chỉ nhìn effective window. CG cache dài hơn sẽ thêm information/history ngoài graph. Sửa design06/decision register: primary cùng effective window, hoặc thêm graph-free matched-cache control nếu chọn full cache. Đây là đề xuất cần chốt, chưa sửa model hoặc method. Chi phí closed-loop reference queries cũng phải tính ngoài chi phí train; fixture d16/168targets không là throughput d256/GPU.

SauSIM05, Gate2-10 296tests pass292.02s; independent probes batch có tolerance proof và không fake history. Tolerance1e-6 không bảo đảm threshold decisions identical với scores nằm sátτ; cần numerical convention/sensitivity trong S04. Không cache qua observe vì globalattention. Suite gần300s cap, không bỏ tests hoặc coi timeout làPASS khi mở rộng gate. Overall full research execution vẫn NOTREADY vì protocol/data/calibration/GPU requirements.

## Review collector/runner trước paid execution

- Phản biện “collector đã có24targets nên dataset sẵn sàng”: bác bỏ. Fixture chỉ quan sát22/84items,2profiles;62items chưa có support. T10 fullcorpus và coverage/distribution/allocation chưa hoàn thành. DATA06 là windows adapter, không complete epoch-selection/refit/final runner.
- Phản biện “hash notebook đầy đủ là domain identity mạnh nhất”: không đủ. Bundler strip output/metadata làm full SHA khác nhưng mọi cell source giống nhau; v1collector sẽ reject cross-runtime checkpoint đúng về equations. Cần semantic definitions/constants/input/clock identity, đồng thời giữ raw storage hashes để audit. Chưa được sửa historical domain/checkpoints; fix mới có version và tests, giữ RNG namespace để identity fix không đổi responses.
- Phản biện “Colab cóvenv là tương đương local authorization”: bác bỏ. Main runtime origin guard yêu cầu Torch/NumPy trongvenv, Colab system-site-packages có semantics khác; Windows CPU wheel lock không dùng cho Linux CUDA. Không nới guards chỉ để command chạy. T08/T14 cần runtime lock/provenance và bounded remote proof riêng.
- Phản biện “full software suite qua thì GPU/researchready”: bác bỏ. Full suite có native synthetic steps, không real-data/CUDA/Volume measurement; S04/S05 và current GPU allocation vẫn chưađược duyệt. Gate cho sourcev1 giữ như snapshot nếu source tiếp tục sửa; finalpointer phải tương ứng source mới.
