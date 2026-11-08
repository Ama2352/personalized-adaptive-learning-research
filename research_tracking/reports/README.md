# Mục lục báo cáo và phân tích KLTN

**CG-AKT checkpoint CPU:** [lưu/restore epoch](cgakt_research_checkpoint_readiness_20261109.md), [bundle119](../runs/cgakt-research-checkpoint-engineering-20261109-01/README.md). Native16 đạt, model/Adam/RNG/modes và một bước tiếp diễn khớp trong cùng process. Giữ cả hai failure trước; chưa fresh-process/lifecycle resume, fitted research hoặc GPU readiness.

**Main selection — kiểm tính nhất quán:** [admission core8](research_admission_core_readiness_20261109.md), [bundle27](../runs/research-admission-core-engineering-20261109-01/README.md). Đủ chín claims trước phép join, kiểm toàn bộ targets/nhãn và tập chung năm mô hình; typed fixtures chưa xác nhận chín file kết quả thật hoặc cho phép refit.

**CG-AKT online — chuẩn bị dữ liệu:** [35 kiểm tra history/geometry/OOV](cgakt_online_query_context_20261109.md), [bundle25](../runs/cgakt-online-query-context-engineering-20261109-01/README.md). Đã có evidence riêng cho từng query Grade10, không nới guard offline; chưa inference parity trên graph model hoặc fitted backend.

**RQ1 — nối readout với quyết định:** [đối chiếu từng snapshot](rq1_query_decision_overlap_20261109.md). Hai nhóm cùng có 22 thay đổi (tiêu chí xác suất tham chiếu và CID) chỉ trùng 2 snapshot; 20 trường hợp mỗi phía không trùng. Cùng 1.080 cặp cũ, không model call hoặc mẫu độc lập mới, không kết luận nhân quả. [Bundle bằng chứng](../runs/rq1-query-decision-overlap-20261109-01/README.md).

**Kernel selection09/11:** [8fixtures thống kê](research_selection_kernel_readiness_20261109.md) với6LLknownanswers đãđốichiếu evaluatorbaseline;50outputs giữ7PASS1FAIL01 và8PASS02. Chỉ response-pooled/sharedbootstrap/tie/fallback logic, chưa nine-terminaladmission hoặc externalfreeze.

**CG-AKT Adam09/11:** [actual3updates](cgakt_actual_adam_20261109.md),1nativecase accepted02 +pure5;48outputs giữ01rejected dù3updates đã xảy ra. Tổng6updates acrossattempts, khôngresearchfit/epoch/checkpoint/CUDA.

**Đo cost context09/11:** [API for_windows](cgakt_context_api_cost_20261109.md), completeTRAIN8010080targets/144windows/144ABBAcalls. Fullpasses20,17/20,44s, fast1,10/1,23s; chỉ lookupAPI, không epoch/NN/GPUthroughput. Giữ failure01, regression2 và accepted02 trong45outputs.

**CG-AKT hotpath09/11:** [135pure và25native cases](cgakt_hotpath_integrity_20261109.md), bundle41outputs;0full-cache serializer ở batch hotregions, vẫn explicitfullboundary. Không actualAdam/checkpoint/corpusfit/CUDA/throughput.

**RQ1 — kết quả trực tiếp bên trong mastery:** [trạng thái và hai điều kiện](rq1_native_mastery_reference_diagnostic_20261109.md), [bundle92](../runs/rq1-prediction-mastery-trace-20261109-01/README.md). Đủ2.160 snapshots khớp nguồn; trên30.240cặp khái niệm–thời điểm,3.428bất đồng điều kiện bất định bị điểm kiến thức thấp giữ lại,90bất đồng phân loại do điều kiện kiến thức. Không90temporal transitions, accuracy/calibration hoặc learning benefit.

**CG-AKT core:** [A3 forward/gradient thực trên CPU](cgakt_research_core_20261109.md), [bundle74](../runs/cgakt-research-core-engineering-20261109-01/README.md).18PASS với8forward/5backward/0optimizer; chưa fittedA0/A1/A2/CG-AKT hoặc main-training readiness.

**Context CG-AKT:** [109ca chung](cgakt_research_context_readiness_20261109.md),66condition+43context; [bundle52](../runs/cgakt-research-context-engineering-20261109-01/README.md) giữ hai lỗi trước sửa, kiểm cửa sổ/OOV và cold imports. NumPy dữ liệu, chưa training.

**Chi phí observer:** [microbenchmark](mastery_observer_cost_microbenchmark_20261109.md) / [bundle24](../runs/mastery-observer-cost-engineering-20261109-01/README.md). Chỉ fixture dựng sẵn; không dùng tỷ số này dự báo tốc độ GAM/GPU.

**CG-AKT nghiên cứu:** [condition metadata](cgakt_research_condition_readiness_20261109.md),66PASS/0FES và [bundle13outputs](../runs/cgakt-research-condition-engineering-20261109-01/README.md). Theo Recipe26; chưa context/forward/training.

**RQ1 — lượt trace chưa đạt:** [hai failures](rq1_prediction_mastery_trace_failures_20261109.md) / [bundle63outputs](../runs/rq1-prediction-mastery-trace-failures-20261109-01/README.md). Lượt01 lỗi metadata Windows, lượt02 timeout/Job0; partial không dùng làm kết quả. Không chạy lại trong allocation60s đã dừng.

**SAKT — bổ sung counter:** [delta33fixtures](sakt_checkpoint_counter_delta_20261109.md), chấp nhận boundary epoch2 và từ chối Adam step cũ trước mutation. [Bundle43outputs](../runs/sakt-research-checkpoint-counter-delta-20261109-01/README.md) đã đóng, tham chiếu bundle70 cũ;3tiny Adamsteps trong lượt mới, chưa baseline fitted.

**Kiểm phần mềm hiện hành09/11:** [AKT/shared KT trên Windows CPU](akt_windows_gate_readiness_20261109.md),1.418 PASS/0 failure/error/skip; [bundle đã đóng](../runs/akt-windows-gate-readiness-20261109-01/README.md) giữ cả lỗi trước sửa và log nghiệm thu. Đây chưa là CUDA hoặc kết quả mô hình nghiên cứu. Các dòng chưa full Gate bên dưới là mốc lịch sử trước lượt03.

**RQ1 — giải thích bước chọn khái niệm:** [tái dựng bộ lọc ứng viên](rq1_fixed_controller_candidates_20261109.md), khớp đủ2.160ready memberships/CID trên1.080cặp cũ. Bốn khác biệt bị bước cân bằng loại;51tập cuối khác vẫn cùng lựa chọn;17tập cuối giữ nguyên nhưng lựa chọn đổi. Đây là giải thích theo source, không thêm mẫu hoặc bằng chứng lợi ích học tập.

**SAKT — persistence cuối epoch:** [bản nghiệm thu31fixtures](sakt_research_checkpoint_readiness_20261109.md),3Adamupdates và continuous/restored parity; bundle70outputs đã đóng. Chưa mid-epoch/fullresearchresume hoặc baseline fitted; SGD format chưa thực chạy.

**Kiểm vận hành09/11:** [hồ sơ collection01–05](gate_collection_trials_20261109.md) đã đóng bundle127outputs; giữ nguyên tất cả failure. Chưa collection toàn bộ hoặc full Gate PASS; đây không phải thí nghiệm trả lời RQ.

**Consumer confidence09/11:** [đã đọc artifact thực](edge_confidence_artifact_readiness_20261109.md),66purePASS và31typed scores read-only; không fit lại hoặc hiệu quả CG-AKT.

**RQ1 bổ sung09/11:** [đề xuất có nằm trong tập sẵn sàng của cấu hình kia không?](rq1_cross_ready_membership_20261109.md), phân tích đủ1.080cặp đã lưu:55ready-change/preview-giữ,17preview-change/M–R-giữ,5jointchanges. RecordedR không capturedC/B; chưa causal hoặc score-only.

**SAKT09/11:** [epoch/prediction bridge đã kiểm](sakt_research_epoch_readiness_20261109.md),22PASS trên dữ liệu tự dựng; chưa baseline fitted, checkpoint/recovery hoặc profile nghiên cứu.

**Ước lượng cạnh đã thực chạy:** [Method24 trên TRAIN mô phỏng](edge_confidence_native_results_20261108.md),2.352solverfits trong45,17giây CPU; chưa CG-AKT neural hoặc bằng chứng cạnh đúng.

**SAKT — cầu nối dữ liệu:** [bản nghiệm thu kỹ thuật](sakt_research_data_readiness_20261108.md),20 data fixtures và3 native compatibility fixtures đã kiểm; chưa fitted model hoặc kết quả RQ.

**Bổ sung kỹ thuật sau gói GVHD08/11:** [metric sau calibration](akt_calibrated_reporting_readiness_20261108.md) có36purePASS và một lần kiểm evaluator pandas/sklearn thật trên5hàng tự dựng;0model/solver/realdata. Số AUC/Brier fixture không là kết quả RQ. Full Gate vẫn cần tách process trước khi chạy; không lấy batch này thay actual training/CUDA.

**Đọc báo cáo tiến độ GVHD:** mở [gói ngày09/11 — đợt01](../supervisor_reports/2026-11-09/01_tien_do/BAO_CAO.md), chỉ gồm bản tóm tắt và [báo cáo HTML độc lập](../supervisor_reports/2026-11-09/01_tien_do/BAO_CAO_NGHIEN_CUU.html) có diễn tiến nghiên cứu, số liệu và mười biểu đồ. Đã kiểm giao diện và đóng browser sau kiểm; bản08/11 giữ nguyên để đối chiếu. Notebook lịch sử đã được thay bằng HTML tại `31ce8ff`. Các đoạn revision4/chưa sinh corpus bên dưới là snapshot cũ, không mô tả trạng thái hiện tại. Corpus thực đã nghiệm thu tại `1990d4c`; controlled history tại `8f95fd6`, controlled ability tại `8b6487c`.

**Báo cáo hiện hành revision4 (`e502848`):** [GVHD](BAO_CAO_TIEN_DO_GVHD_20261108.md),32source inputs/25links đã kiểm. Bổ sung [full–empty edge contrast](rq1_fixed_edge_set_contrast_20261108.md) và [history bins](rq1_history_stratified_edge_contrast_20261108.md): kết quả gộp cải thiện nhỏ nhưng PG bất lợi; history/time còn confounding, không causal learning benefit hoặc RQ completion. Notebook bên dưới vẫn snapshot C01–C14, chưa chứa hai phân tích mới.

**RQ2 bổ sung:** [metric-specific retention counterexample](rq2_retention_metric_separation_20261108.md): soft gain có thể đảo ranking trên trạng thái dựng sẵn dù net-theta retention giữ common factor. Không policy/trajectory effect.

**Đường triển khai tiếp:** [first Development corpus profile](first_development_corpus_plan_20261108.md) đã chốt48/6/6×210 nhưng chưa sinh, [A0 lifecycle contract](../../docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md) chưa là trainer. [Archive lỗi native replay trước imports](../runs/rq1-history-availability-20261108-01/README.md) giữ verdict thất bại/UNKNOWN và0native calls, không scientific result; đang sửa owned Windows launch trước retry. Không Modal spending.

**Đính chính dự toán:** [hạch toán23](../../docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md) phân biệt9neural conditions với18selected/refit phases mỗi môi trường, tổng36phases cho allocation đầy đủ hai môi trường; chưa tính inference/GAM/surrogate. Không27lượt, không runtime/cost đã đo hoặc quyền chạy.

**Báo cáo GVHD hiện hành:** [tiến độ08/11](BAO_CAO_TIEN_DO_GVHD_20261108.md) / [source/revision](BAO_CAO_TIEN_DO_GVHD_20261108.json). [Notebook báo cáo](../../notebooks/thesis_evidence_report.ipynb) đã có outputs cached; [integrity bổ sung](thesis_evidence_notebook_integrity_20261108.md), chưa Jupyter-kernel/visual QA.

**Cập nhật sau chỉ thị user:** [Protocol21 Development đã được chọn](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), supersede trạng thái chờ phương pháp trong snapshot bên dưới; không cấp quyền chi Modal/fullCV/Holdout.

- [Research-data contract](simulator_research_data_contract_20261108.md):76PASS, chưa corpus generator.
- [Response calibration](response_calibration_readiness_20261108.md):39PASS, chưa research-fitted neural model.
- [Reference controller](reference_controller_readiness_20261108.md):36PASS, chưa outer runner.
- [Cross-module151PASS](../runs/reference-pipeline-integration-20261108-01/README.md): kiểm cùng phiên bản hiện hành; không151quan sát hoặc cộng với targeted suites.

**Cần review phương pháp trước research fit:** [S04/S05 — lựa chọn cụ thể, chưa áp dụng](s04_s05_decision_options_DRY_20261108.md), [27 nguồn và kiểm metadata](s04_s05_decision_options_DRY_20261108.sources.json), commit `762bb20`. Bao gồm reference/mastery/calibration/controller, split/refit, required model×environment matrix, Plan B cần duyệt và chi phí logical reference queries. Đây là proposal, không kết quả nghiên cứu hoặc quyền chạy CV/Modal. Câu hỏi duyệt đã được gửi cho user; việc chuẩn bị môi trường vẫn tiếp tục độc lập.


## Mốc mới08/11 — graph lifecycle, GPU-host preparation và demo closed-loop

- **GRAPH04 — `f8e9ab0`:** [toy graph lifecycle](akt_graph_training_readiness_20261108.md), [bundle](../runs/akt-graph-training-engineering-20261108-01/README.md), 89 outputs. Actual02 giữ **45 PASS/1 FAIL**; sáu graph tests PASS; inventory expectation kiểm riêng một corrected function trên stored artifact/0fit, không rerun toàn suite hoặc relabel failure. **4 optimizer reservations/body returns**, cumulative **46,6888821s ≤ 60s**; graph complete1update/8targets, selection4=3scored+1OOV, reload delta0; partial graph1update không checkpoint/export/COMPLETE. Chưa research fitted/calibration/S04/S05/context100/resume/full Gate/CUDA.
- **GPU09HOST — `c1d93ec`:** [source preparation](akt_gpu_host_preparation_20261108.md), [bundle102outputs](../runs/akt-gpu-host-preparation-20261108-01/README.md). Final warm20/generic9/cold24/packet41 methods là **bốn scopes local mock/AST/metadata**, không tổng fullGate. Historical CPU marker/tag engineering không actual GPU-host discovery/startup/hidden audit/install hoặc wheel-byte/CUDA proof.0model/optimizer/hardwarechange/remote trong batch. Report snapshot còn chữ proposed/pre-closure; mốc này chỉ xác nhận archive closure bằng manifest.
- **DEMO02 — source `22b3522`, bundle `b9eaaab`:** [viewer closed-loop](demo_closed_loop_readiness_20261108.md), [bundle66outputs](../runs/demo-closed-loop-engineering-20261108-01/README.md). **83 PASS**, cumulative36,1590131s ≤ 60s; giữ47PASS/36HTTPfailures trial01, không sourcefix giữa trials. Cùng trang chọn trajectory/common-prefix/first-break, giữ bảy negatives; actual mobile390×844, console0error, QA tab/server đã đóng. Post-hoc source-local CID/newN0/native Bscore noncalibrated/Pafterselect/package≠edges; không paired ΔP sau divergence hoặc live fitted personalization. T21 vẫn IN_PROGRESS/partial E11.

**Trạng thái vận hành hiện tại:** Linux Gate24 771 PASS và CPUdummy48train/8val/2updates/durable9files là **bằng chứng lịch sử source trước Graph03/04**. Không dùng Gate24 hoặc targeted tests/mocks mới để chứng nhận current full Gate, actual CUDA/GPU ready, hiệu quả CG-AKT hay hoàn thành RQ. Windows Gate22 đã stale. Các snapshot hiện hành cũ phía dưới giữ nguyên thời điểm/verdict.

**Mốc mới08/11:** [A2/A3 confidence/gate](akt_graph_confidence_gate_readiness_20261108.md) commit `4a256a4`:43targeted CPU PASS/0optimizer,37outputs rawGitverified; chưa graph-aware trainer/fit/calibration hoặc GPU. Gate24 trước thay đổi này **không chứng nhận current source**. [Bản thảo C14](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) commit `4edf1f8`:14claims/104pointers/28inputs/24links đã kiểm; C01–C13 giữ nguyên, C14 post-hoc source-local/newN0, không finalRQ.

**RQDIAG05 đã đóng (`850f5ab`):** [closed-loop và concept ranking](rq1_closed_loop_reconstruction_20261108.md) giữ exact legacy 3.240events/pass,27statepairs và9uniformpairs. Native ranking key khớp3.240/3.240 CID; trong common-prefix first breaks,8full+2empty cases có cùng M/R/C/B membership nhưng khác score chọn khác concept. Đây là **post-hoc source-local explanation**, không edge-only/causal/learning-benefit hoặc hoàn tất RQ1. Served-item P được tính sau selection trong source này. Accepted-02 có125outputs; failed archiver-01 có116outputs giữ nguyên; cả241raw Git blobs đã kiểm. Report snapshot còn chữ PROPOSED vì được freeze trước closure; mốc chỉ mục này xác nhận actual closure bằng manifest.

**GKT06 đã nghiệm thu (`f204f69`):** [epoch pipeline](gkt_epoch_pipeline_readiness_20261108.md) có38purePASS và actual2epochs/2Adamreturns;6train targets mỗi epoch, selection đủ4=2scored+2unsupported/0research_fitted.95outputs raw Git verified. Đây là lifecycle engineering, chưa full corpus/final GKT baseline/refit/resume hoặc S04/S05 adoption.

## Bổ sung08/11 — GKT05 và discovery CPU đã nghiệm thu

- [GKT05 adapter](gkt_adapter_readiness_20261108.md), commit `4a64525`:32portable tests và1actual stored checkpoint load;6targets=2scored+4unsupported,0research_fitted/optimizer.69outputs đã kiểm raw Git; chưa epoch/corpus/fitted OnlineSession hoặc training-attested item mapping.
- [Discovery CPU trước T4](akt_t4_discovery_readiness_20261108.md), commit `04b8ac1`:165source/lock hashes,44versions, cả hai cleanup accepted; **warm candidate, chưa CUDA/GPU ready**.53outputs raw Git verified; giữ timeout, failed discovery01 và scheme correction. Không cài lại venv/đổi hardware/Modal.

## Hiện hành08/11 — Linux CPU worker đã đóng (`1c52043`)

- [Linux worker readiness](akt_linux_worker_readiness_20261108.md) — [bundle 194 output](../runs/akt-linux-worker-readiness-20261108-01/README.md), [manifest](../runs/akt-linux-worker-readiness-20261108-01/manifest.json): actual Linux Gate24 **771 PASS/0 fail/error/skip**, native elapsed **268.092342194s ≤ 600s**; native CPU dummy **48 train targets/8 validation predictions/2 genuine optimizer updates**, reload exact. Đây là engineering synthetic CPU, không kết quả efficacy hoặc hoàn tất RQ.
- [Durable artifact inventory](../../experiments/akt/results/ctx-linux-20261108-01/transfer-copy-inventory.json) — **9 exact copies**, gồm 4 binary/448378 B và 5 native text; nguồn là job Colab CPU đã hoàn tất, không local fit. 194 output SHA của bundle và 9 copy SHA/size đã kiểm lại; binary không vào Git.
- **Mốc hiện tại thay thế các snapshot vận hành cũ:** Windows Gate22 là lịch sử **STALE sau `dd80006`**; Gate23 763 PASS/5 FAIL và failure loader/transport không bị relabel. Actual CUDA/GPU09, image, refit/resume và scientific S01/S04/S05 vẫn pending. GKT03 (`b67eba0`) giữ nguyên scope; không thêm GKT04 trong cập nhật này.

## Bổ sung08/11 — GKT04 và bản thảo C13 đã đóng

- **GKT04 — `2d8aaf8`:** [weights-only checkpoint report](gkt_checkpoint_readiness_20261108.md), [bundle60outputs](../runs/gkt-checkpoint-engineering-20261108-01/README.md), [manifest](../runs/gkt-checkpoint-engineering-20261108-01/manifest.json). Final **40 PASS/0 fail/error/skip**; **2 actual Adam updates tổng hai trials** (1/trial), conservative **24,609858s ≤ 60s**, toàn bộ60outputSHA và source/test SHA đã kiểm lại. Trial01 vẫn **1PASS/39fixtureERROR** do quyền hard-link `WinError5`; trial02 cùng source/test được chạy trong bounded process đã được phép. Không đổi failure thành PASS hoặc gọi đây là source bugfix.
- **Phạm vi GKT:** GKT03 (`b67eba0`) vẫn là one train-batch/45tests/4updates/32outputs. GKT04 là followup hoàn tất weights-only save/load riêng, không thay giới hạn lịch sử của GKT03. Không optimizer/RNG/hidden-state restoration, resume, epoch/corpus, refit/selection hoặc fitted inference; scientific S04/S05 và baseline nghiên cứu đầy đủ vẫn pending.
- **WRITE02 hiện tại — `1b3d3f9`:** [bản thảo RQ1–RQ2](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) và [source map](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json) có **13 claims/80 JSON pointers/21 inputs** được kiểm. C13 chỉ tích hợp observability reproduction: **944/964 P changes giữ full preview**, **2/116 P-same rows đổi preview**, **22/1.080 full-preview changes**, actual shared queries1.080keys; ba seed families, **new independent N=0**. C01–C12/16inputs cũ và snapshot `d30dafe` giữ nguyên lịch sử; không backfill trace, causal/served-action/calibration claim hoặc RQ completion. Mốc Linux Gate24/CPU worker phía trên giữ nguyên.

## Bổ sung08/11 — GKT02, WRITE02 và RQDIAG04

- **GKT03 — `b67eba0`:** [train-batch readiness](gkt_training_readiness_20261108.md),45CPUtests/4actual Adam updates/32outputs; conservative cumulative10,844604s≤60. Manifest `c1194df13f6f8f6efa41469264e6ced6447135bf389c2d03729a755d1ed14e0f`; COMPLETED_ENGINEERING_ONLY sau GKT02. Chưa checkpoint/resume/epoch/corpus/fitted adapter hoặc S04/S05; cooperative budget/state/source không là nonresettable authorization.

- **GKT02, commit `6035262`:** [recurrent candidate readiness](gkt_recurrent_candidate_readiness_20261108.md), [đặc tả recipe](gkt_recurrence_specification_20261108.md), [bundle47outputs](../runs/gkt-recurrent-candidate-engineering-20261108-01/README.md). Final **88CPUtests**,0optimizer; manifest SHA `b00ca32d5c4385da9a84d3442b82638ec344a64cb191b91b1b02c5ab513d09ac`. Recurrent source SHA `510195d71c1ddb743f747e78d7d874c04bb809931c5ec24ae6fe907fe53ec072`; report SHA `17e2d57e139a96dbef7dce0e768b4969dd32fdff1980dcc9a84720c496236807`. Đây là engineering recipe candidate sau GKT01; chưa author parity/S05 adoption, trainer/fitted adapter/learned graph hoặc full comparator.
- **WRITE02, commit `d30dafe`:** [tiểu mục kết quả kiểm toán/chẩn đoán pilot](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md), [claim-source JSON](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json). MD SHA `da64fbae222b9d116ebdc41933f02912ed04385eac43491d3a438b4f649caa8e`; sources SHA `04e879674243dbdcbc8ba69423819662509bf8bdd7039b42d0fac92a69b50fbf`. Parent/independent review và [validation05](../../artifacts/akt/local-tests/thesis-rq12-draft-20261108-01/validation05.json) giữ53JSONPointers/14links;3P3wording đã bổ sung, các bảng số/claim values không đổi. Đây là bản thảo sau WRITE01, không final RQ1/RQ2 completion hoặc thí nghiệm mới.

- **RQDIAG04, commit `7dd8338`:** [query/full-preview observability reproduction](rq1_query_observability_reproduction_20261108.md),40outputs/12spyPASS,71,9959014s≤120,0optimizer/new independentN=0. Nativecontrol/observer giữ exactlegacy của cùngpilot; parent kiểm1.080sharedqueries. Newsidecar không backfill metadata lịch sử; preview≠servedaction, không causal/finalRQ1.

Các phần GKT kernel/methods draft phía dưới là các mốc trước, giữ nguyên vai trò lịch sử. Các cập nhật này không bổ sung actual Linux Gate/runtime outcome, GPU/Modal hoặc fitted research result.

## Hiện hành08/11 — Linux install/audit và Windows Gate22

Đọc cập nhật này trước các đoạn Gate21/resolution-only/pending archive lịch sử phía dưới. Đã kiểm124output SHA của hai bundle mới, không thêm model/RQ result từ kiểm môi trường.

- [Linux isolated install/audit](akt_linux_isolated_install_20261108.md), [bundle80outputs](../runs/akt-linux-isolated-install-20261108-01/README.md): controllers01/02 đều giữ **FAILED**.02 pip-install/report44selected và pip-check exit0 nhưng controller fail metadata guard. Audit riêng **EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY**,23.361956656s≤90s,44versions/all RECORD origins/8CPUimports/1CPUscalar/Torch2.7.1+cu126, CUDA chưa initialize. Không relabel02, không actual Linux fullGate/GPU/image/main-worker acceptance.
- [Linux Gate tooling](akt_linux_gate_tooling_readiness_20261108.md), [bundle44outputs](../runs/linux-gate-tooling-engineering-20261108-01/README.md), commit `7b07d61`:118targeted PASS, parent raw44Git verified, RED107PASS/11FAIL giữ lại;0optimizer. Publicpackaging/explicit selectedlock giữ Windows default và strictguards.
- **Windows Gate22 hiện hành:** [report](../../artifacts/akt/preflight/gate2-evidence-20261108-linux-tooling-22.json)768PASS/0fail/error/skip,477.7091635s≤540s, SHA`f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd`; snapshots trong bundle80. Run-id `linux-tooling` không đổi host Windows thành Linux.
- [Exact Linux source kit](../../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/README.md): chỉ local ZIP980252bytes/161payload, chưa upload/extract/run remote. Bridge98978 expired; startup kỹ thuật mới pending, không gán lỗi cho user.

Audit riêng không chạy pip/install/network/model/optimizer/Modal.44installed distributions và CUDA12.6 build metadata chưa chứng nhận CUDA hardware/image, full Linux suite/worker hoặc forecast chi phí. Report resolution/addendum cũ giữ scope metadata; S04/S05 và RQ claims không đổi.

Đây là nơi thống nhất cho báo cáo/phân tích tổng hợp. Bằng chứng theo run nằm ở [../runs](../runs/); dữ liệu/models/predictions lớn giữ ở artifacts/experiments theo [bản đồ repository](../../docs/REPOSITORY_MAP.md). Các file dưới đây có vai trò khác nhau, không phải tất cả đều là kết luận nghiên cứu hoặc chương luận văn.

## Baseline đã có kết quả

| Nội dung | Báo cáo đọc được | Số liệu tổng hợp |
|---|---|---|
| BKT Junyi | [BKT results](../../docs/bkt-baseline-results.md) | Nguồn CV/refit lịch sử trong experiments, xem báo cáo |
| BKT–GAM-KT Development CV | [Bản ngắn](../../docs/bkt-gam-kt-benchmark.md), [bản chi tiết](../../docs/research/bkt-gam-kt-baseline-benchmark-report.md) | [Paired bootstrap JSON](paired_cluster_bootstrap_bkt_gam.json) |

JSON bootstrap chuyển từ root `reports/` với bytes/SHA giữ nguyên. [Hồ sơ relocation](report_relocation_20261107.json) lưu vị trí cũ/mới và hashes; số liệu không được tính lại. Bootstrap hai baseline graph-free không chứng minh graph hoặc chính sách học có ích.

## RQ1/RQ2 — Chẩn đoán và pilot

- [cpu_rq12_20261107.md](cpu_rq12_20261107.md): chuỗi prediction→decision, graph package, retention/re-entry và giới hạn nguồn.
- [cpu_pilots_20261107.md](cpu_pilots_20261107.md): approved bounded factorial và Junyi order pilots.
- [cpu_matched_controls_20261107.md](cpu_matched_controls_20261107.md): graph controls và độ phủ của thay đổi cạnh.
- [cpu_common_population_20261107.md](cpu_common_population_20261107.md): so sánh trên cùng learner/child opportunities, missingness và weak exposure.

Đọc run IDs/manifests được mỗi báo cáo chỉ ra. Pilot không tự trở thành confirmatory result; không suy lợi ích nhân quả từ logged Junyi order.

## Kỹ thuật và tính tái lập

- [Agent chạy Colab MCP](../../docs/akt-colab-mcp.md): kết nối/thực thiT4 đã xác nhận trực tiếp; [44outputs](../runs/colab-mcp-preflight-20261107-01/README.md) giữ failedpreflight435pass/7fail/8errors, chưa CUDAmodel/Gate4.

- [Colab recovery readiness](colab_recovery_readiness_20261107.md): sửa CUDA RNG restore từ source/regression, CPU recovery qua3processes exact,19mockguards và Gate407. Kitv11; cập nhật notebookVSCode mộtfile/20localchecks, chưa actualColab/CUDA, không dùng Modal credits.
- [Modal setup](../../docs/akt-modal-setup.md): kết nối local và trần30USD/tháng; [SDK proof](../runs/cpu-modal-client-20261107-01/README.md) chỉ kiểm projectvenv/CLI/dependencies, chưa auth hoặc cloud execution.
- [Modal access readiness](modal_access_readiness_20261107.md): token/workspace/environment đã kiểm bằng API chỉ đọc; vẫn chưa chạy compute hoặc xác minh CUDA/budget bằng API.
- [Colab-first runbook](../../docs/akt-colab-synthetic-runbook.md): ưu tiên kiểm CUDA trênColabfree; [local notebook guard proof](../runs/cpu-colab-first-20261107-01/README.md) chỉ8mockcases và1packagingtest, chưa actualremoteGPU.
- [simulator_collection_runner_20261107.md](simulator_collection_runner_20261107.md): collector Paper2 train-only và role-aware KT windows/collation; fixture engineering, chưa là corpus/full trainer hoặc research benefit.
- [simulator_data_graph_boundaries_20261107.md](simulator_data_graph_boundaries_20261107.md): split/schema cho dữ liệu mô phỏng và graph-context history scope; fixture kỹ thuật, chưa là CG-AKT efficacy.
- [simulator_kt_interface_20261107.md](simulator_kt_interface_20261107.md): typed session/query/checkpoint bridge, export fix, frozen inference và independent batching. Đây là engineering evidence, không là CG-AKT efficacy.
- `git_evidence_verification_*.json`: đối chiếu output hashes với bytes trong Git.
- `colab_bundle_*_verification_*.json`, `colab_upstream_*_inventory_*.json`: kiểm bundle/dependency/portability; không tự chứng minh đã chạy Colab/CUDA.
- Các JSON có tên `coverage`, `followup`, `diagnostics_verification`: số liệu kiểm tra hỗ trợ; đọc scope trong file và báo cáo tương ứng, không lấy tên file làm verdict nghiên cứu.

## Draft, lịch sử và hồ sơ vận hành

- [CPU09_CPU10_PROTOCOL_DRAFT.md](CPU09_CPU10_PROTOCOL_DRAFT.md): protocol pilot/draft; phạm vi được duyệt và confirmatory design là hai việc riêng.
- [initial_audit.md](initial_audit.md): snapshot audit ban đầu; không dùng inventory cũ thay trạng thái mới.
- [report_relocation_20261107.json](report_relocation_20261107.json), `temporary_relocation_*.json`, `uncommitted_inventory_*.json`: hồ sơ sắp xếp workspace, không phải kết quả mô hình.

## Quy ước duy trì

1. Bản diễn giải theo chủ đề có tên rõ và ngày; thêm vào đúng mục ở đây. JSON tổng hợp đi cùng báo cáo hoặc bundle có provenance.
2. Một execution mới dùng run ID mới trong `research_tracking/runs/`; không tạo thêm một root `reports/` hay thư mục tên chung chung để chứa cùng loại file.
3. Không đổi số liệu, seed hoặc protocol khi di chuyển file. Ghi inventory trước, so SHA sau và cập nhật chỉ mục; manifests/models/predictions/bundles lịch sử giữ nguyên.
4. Bản luận văn sau này trích nhận định có scope, bảng/số liệu và run ID; không đưa toàn bộ debug logs vào thân báo cáo.

## Bổ sung từ các bundles local đã đóng — 07/11/2026

Đã kiểm SHA-256 đủ 114 outputs của bốn bundles được dẫn dưới đây. Báo cáo tổng hợp, exploratory analysis và kiểm phần mềm có mức bằng chứng riêng; các mục lịch sử phía trên giữ nguyên.

- [Graph residual/gate prototype](graph_gate_prototype_20261107.md) và [factorial pilot uncertainty](factorial_pilot_uncertainty_20261107.md), [bundle 32 outputs](../runs/parallel-graph-diagnostics-20261107-01/README.md): 75 CPU synthetic cases cho kernel; 10 seed blocks/profile với joint resampling post-hoc. Chưa native CG-AKT/training, chưa formal population CI hoặc efficacy.
- [Platform fixtures](colab_platform_fixtures_20261107.md) và [RQ1/RQ2 evidence synthesis](rq12_evidence_synthesis_20261107.md), [bundle 38 outputs](../runs/cpu-portability-gate-20261107-01/README.md): Windows Gate15 462 pass, v12 mocked harness/dependency checks, one-row DuckDB version/API contrast và snapshot aggregates. Không suy full runtime acceptance hoặc confirmatory graph benefit từ các kiểm này.
- [Paper1 revision reconciliation](paper1_revision_reconciliation_20261107.md), [bundle 14 outputs](../runs/paper1-revision-audit-20261107-01/README.md): source/PDF/Git/candidate inventory thu hẹp local provenance; chưa exact reproduction, Q01/S01 vẫn mở.
- [SAKT core readiness](sakt_core_readiness_20261107.md), [bundle 30 outputs](../runs/sakt-core-engineering-20261107-01/README.md): source-bound final 37 CPU synthetic cases, random weights và 0 optimizer steps. Chưa fitted baseline/adapter/trainer; Gate15 và kit v12 không chứa SAKT.

Chỉ mục này không thêm GPU/runtime verdict khi chưa có evidence bundle đã đối chiếu; không tự thông qua S04/S05 hoặc bỏ required baselines.

## Nghiệm thu GPU thực tế07/11

- [colab_cuda_acceptance_20261107.md](colab_cuda_acceptance_20261107.md): actual ColabT4 CPU505pass,400target lifecycle và controlled fresh-process CUDA recovery; trả đủ44outputs/SHA, không fulltraining/Gate4.
- [colab_cuda_adversarial_review_20261107.md](colab_cuda_adversarial_review_20261107.md): kiểm độc lập source/coverage và các blockers Linuxruntime, mainworker lifecycle, throughput, Modal durability/budget.
- [Bundle CUDA68outputs](../runs/colab-cuda-synthetic-20261107-01/README.md) giữ raw receipts/logs/JUnit/manifests/source snapshots, không heavy checkpoints trong Git. Các failures preflight vẫn giữ nguyên trong bundle lịch sử.

## Runtime Linux, main worker CPU và SAKT inference — batch bắt đầu07/11

- [Runtime contract](akt_linux_runtime_contract_20261107.md), [main worker](akt_main_worker_lifecycle_20261107.md), [bundle](../runs/cpu-linux-worker-20261107-01/README.md): targeted63cases và2newworker cases; fullGate513pass/269.98s, source-bound WindowsCPU. Linuxbranches mocked, chưa actualLinux/CUDA worker.
- [SAKT adapter](sakt_adapter_readiness_20261107.md), [bundle ban đầu](../runs/sakt-inference-engineering-20261107-01/README.md), [checkpoint followup](../runs/sakt-checkpoint-payload-20261107-01/README.md):89CPUcases=37core+52adapter,0optimizersteps; random/unverifiedweights không fitted benchmark hoặc completeOnlineSessionbridge.

## Gói gửi GVHD và phân tích RQ mới08/11

- [BAO_CAO_TIEN_DO_GVHD_20261108.md](BAO_CAO_TIEN_DO_GVHD_20261108.md): bản tổng hợp đọc độc lập, nguồn/giới hạn/những điểm cần GVHD chốt. JSON đi cùng lưu claim→artifact và SHA; chưa tự gửi ra ngoài.
- [rq1_transition_evidence_20261108.md](rq1_transition_evidence_20261108.md): conditional event tables và trường hợp cụ thể từ stored synthetic traces,25unitcases; không biến scalar-P/preview thành causal full-chain.
- [rq2_conditions_evidence_20261108.md](rq2_conditions_evidence_20261108.md): profile-pair LOO, graph-control exposure và đổi dấu theo weighting/population,27unitcases. [Primary](../runs/rq2-conditions-evidence-20261108-01/README.md) và [validation](../runs/rq2-conditions-validation-20261108-01/README.md) có vai trò khác nhau; không tăng n bằng việc archive/reproduce.

## Batch08/11 — sản phẩm kỹ thuật và bản thảo luận văn

- [AKT worker context](akt_worker_context_readiness_20261108.md), [review độc lập](gpu07_adversarial_review_20261108.md): Gate18 661PASS, actual-guard WindowsCPU toy lifecycle48targets/2updates/8predictions; actual Linux/CUDA mới vẫn chưa kiểm.
- [GKT source plan](gkt_source_and_core_plan_20261108.md), [GKT kernel](gkt_core_readiness_20261108.md):43PASS, chỉ toán tử message/readout, chưa recurrence/trainer/fitted baseline.
- [Demo chỉ đọc](demo_readiness_20261108.md):53PASS và visual QA, partialE11; replay stored synthetic artifacts, không giả lập fittedCG-AKT/live personalization.
- [Bản thảo phương pháp RQ1/RQ2](THESIS_METHODS_RQ12_DRAFT_20261108.md): phần sẵn trích dẫn với [.sources.json](THESIS_METHODS_RQ12_DRAFT_20261108.sources.json), giữ pilot/descriptive/provenance limits, không tự chốt protocol.
- [GPU08 environment proposal](../../docs/akt-linux-cuda-environment.md): official metadata và receipts đã archive; full Linux transitive hash lock/image/actual runtime còn thiếu. Không dùng Windows --platform để chứng nhận Linux markers.

- [Model completion delta](model_completion_contract_20261108.md): required comparators vẫn giữ đủ; core/inference/trainer/fitted results/simulator bridge là các mức khác nhau. SAKT03 và SIMTRAIN01 tiếp tục synthetic-only, chưa adoption S04/S05.

- [RQ1 score-vector diagnostic](rq1_score_vector_diagnostic_20261108.md) và [.sources.json](rq1_score_vector_diagnostic_20261108.sources.json):Sdiff1080/M90/A22, PG losses xấu hơn trongcả3seed-profile rows; no model/simulator rerun, không suy mastery calibration từ S.

## Bổ sung08/11 — bằng chứng kỹ thuật đã đóng và Gate21

Sáu bundle sau đã kiểm đủ472output SHA; các mục cũ giữ đúng vai trò snapshot lịch sử. Các kết quả này chưa là fitted research comparisons hoặc hoàn thành RQ1–RQ3.

- [SAKT training readiness](sakt_training_readiness_20261108.md), [bundle51outputs](../runs/sakt-training-engineering-20261108-01/README.md), mốc commit `9952bc7`:139PASS, synthetic CPU training/validation/checkpoint engineering; không selected-fit/refit/resume/calibration hoặc complete Grade10 training bridge.
- [AKT simulator engineering](akt_simulator_engineering_readiness_20261108.md), [bundle93outputs](../runs/akt-simulator-engineering-20261108-01/README.md), mốc commit `000ea22`:40targeted PASS/Gate19 lịch sử701PASS, toy role-aware lifecycle; intentional incomplete path được giữ. Không full simulator corpus/trainer protocol hoặc research efficacy.
- [Graph-GAM variants](graph_gam_variant_readiness_20261108.md), [bundle27outputs](../runs/graph-gam-variant-engineering-20261108-01/README.md), commit `96004e2`:38PASS/97native online state updates,0optimizer/global fit. Adaptation parent/local kết hợp; empty graph không tự là graph-free endpoint.
- [Gate2 elapsed budget fix](gate2_elapsed_budget_fix_20261108.md), [bundle68outputs](../runs/gate2-budget-fix-20261108-01/README.md), commit `4af8f85`:47targeted PASS, giữ actual RED19PASS/25FAIL. Ngân sách hữu hạn và resource fields bắt buộc ở cả publisher/reader; software fix không cấp quyền chạy nghiên cứu.
- [A0/A1 graph prototype](akt_graph_prototype_readiness_20261108.md), [bundle196outputs](../runs/akt-graph-prototype-engineering-20261108-01/README.md), commit `6377265`:23targeted PASS/0optimizer sau source rebind; bundle mới kèm **Gate21 757PASS,467.1361735s≤540s**, current pointer/source/lock được reader xác minh. Report targeted/addendum ghi trạng thái trước Gate21; accepted verdict mới nằm trong bundle. Chưa A2/A3/confidence/gate/graph-aware trainer hoặc CG performance.
- [Linux dependency resolution](akt_linux_dependency_resolution_20261108.md), [bundle37outputs](../runs/akt-linux-dependency-resolution-20261108-01/README.md): actual CPU resolution44packages/14NVIDIA, raw14files verified,0install. Kiểm offline46active constraints/tái dựng lock là validation cùng evidence, không runtime experiment thứ hai; index hashes không chứng nhận toàn wheel bytes/import/image/CUDA.

**Gate20 bị từ chối resource acceptance** dù724functional PASS vì1083.995106s>540s. Giữ report/log/XML và audit thu hồi trong bundles, không sửa verdict lịch sử thành accepted. Gate21 chỉ chứng nhận CPU software suite tại source snapshot; chưa actual Linux/CUDA main-worker hoặc Gate4/full training.

Gate21 chỉ chạy `tests/akt tests/shared_kt`; các số139SAKT và38Graph-GAM thuộc targeted suites riêng.

**Làm rõ future install:** [addendum acceptance](akt_linux_dependency_resolution_20261108_addendum.md) xác định pip `--require-hashes` có thể cài trực tiếp44URLs trong [candidate lock](../runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt) theo stage/budget riêng; lưu wheelhouse là tùy chọn tách biệt. Đây là bước chưa chạy, không nâng resolution thành installed origins hoặc runtime/CUDA readiness; không sửa wording/report gốc đã freeze.

**Errata demo:** “12/120 nodes” trong [report gốc](demo_readiness_20261108.md) là số mục timeline **`#route li`**; miền28concepts. Giữ nguyên [bundle93outputs](../runs/demo-readonly-engineering-20261108-01/README.md), không biến timeline preview thành số concept hoặc served-action evidence.


- [Worker độ tin cậy cạnh](edge_confidence_worker_readiness_20261108.md):21purePASS và cả lượt timeout trước được giữ trong bundle; chưa actualsolver/corpus/AKTfit hoặc hiệu quả RQ3.

- [AKT/reference/calibrator](akt_reference_calibrator_binding_20261108.md):36purePASS sau sửa bank/schema và giải phóng model/Adam sớm; chưa native lifecycle hoặc kết quả nghiên cứu.

- [Gate chia tiến trình](akt_gate_process_isolation_20261108.md):76targeted fixtures PASS, giữ đầy đủ67modules/3processes; actual full Gate/runtime và RAM acceptance vẫn chưa chạy.

- [RQ1: thành thạo hay đủ số lần luyện?](rq1_ready_set_exposure_results_20261108.md):3240cached served actions;2740có tiên quyết gồm2041exposure và699strict. [Bundle28outputs](../runs/rq1-ready-set-exposure-20261108-01/README.md); không lợi ích nhân quả/calibration/RQcomplete.

- [AKT metric consistency](akt_metric_consistency_20261108.md):13actual evaluator fixtures PASS; sửaepsilonbootstrap khớp metricchuẩn, chưa impact trên artifacts thật hoặc fullGate.
