# Phản biện kế hoạch và điều chỉnh

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
