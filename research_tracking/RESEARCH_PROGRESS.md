# Tiến độ nghiên cứu

**Bổ sung09/11:** [SAKT epoch/prediction bridge](reports/sakt_research_epoch_readiness_20261109.md) đã22PASS trên fixtures; chưa full corpus/profile/checkpoint nghiên cứu. [Cached RQ1cross-ready](reports/rq1_cross_ready_membership_20261109.md) đã đóng bundle32outputs/1.080cặp:55Rđổi-previewgiữ,17previewđổi-M/Rgiữ,5jointchanges. Bản GVHD08/11 vẫn là snapshottrước bổ sung này; bản09/11 đang chuẩn bị. Đây không tăng independentN hoặc hoàn tất RQ.

**Cập nhật hiện hành08/11:** [Báo cáo GVHD theo diễn tiến nghiên cứu](supervisor_reports/2026-11-08/01_tien_do/BAO_CAO.md) và [HTML độc lập](supervisor_reports/2026-11-08/01_tien_do/BAO_CAO_NGHIEN_CUU.html), commit `8fcbc77`. Ngữ cảnh hai paper → bảng đã làm/chưa chứng minh → bốn chặng điều tra → phần còn thiếu. Đã kiểm desktop/mobile, không còn chồng nhãn; browser preview đã đóng.

**RQ1/RQ2:** đã có matched edge contrast, footprint controller, history/ability controls và audit retention/Junyi; vẫn là bằng chứng chẩn đoán hữu hạn, chưa hoàn tất RQ. **RQ3:** corpus60người học/12.600tương tác đã tạo tại `1990d4c`. [Method24](reports/edge_confidence_native_results_20261108.md) vừa actualfit2.352surrogates trên TRAIN, tạo candidateDAG31cạnh trong45,17giây CPU; bundle `bbd7708` đã đối chiếu113rawGitoutputs. Điểm cạnh là predictive stability, khôngP(edge true); chưa neuralCG-AKT hoặc learningbenefit.

**Mô hình/phần mềm:** [SAKT research data](reports/sakt_research_data_readiness_20261108.md), commit `8082e04`, đã20dataPASS+3nativeexportsPASS, chưa researchfitted. Research epoch/prediction và strict confidence artifact reader đang triển khai, chưa dùng WIP để cấp quyền training. RAM snapshot03 hiện đủ4GiB admission nhưng fullGate chưa chạy: cần source/test mới freeze và actualcollection thay recipe counts cũ. GPU/CUDA current-source, fullCV, Holdout và Modal vẫn chưa được cấp quyền từ các kiểm CPU này.

[Protocol21](../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md) đã groupadopt S04-A/S05-B theo quyền user giao. Các đoạn “chưa sinh corpus”, “S04/S05 pending” và “hiện hành” bên dưới là snapshot lịch sử; dùng bản cập nhật này và INVESTIGATION_STATE cho trạng thái mới. Không dùng testcounts hoặc số task làm phần trăm hoàn thành nghiên cứu.


## Mốc mới08/11 — graph lifecycle, GPU-host preparation và demo closed-loop

- **GRAPH04 — `f8e9ab0`:** [toy graph lifecycle](reports/akt_graph_training_readiness_20261108.md), [bundle](runs/akt-graph-training-engineering-20261108-01/README.md), 89 outputs. Actual02 giữ **45 PASS/1 FAIL**; sáu graph tests PASS; inventory expectation kiểm riêng một corrected function trên stored artifact/0fit, không rerun toàn suite hoặc relabel failure. **4 optimizer reservations/body returns**, cumulative **46,6888821s ≤ 60s**; graph complete1update/8targets, selection4=3scored+1OOV, reload delta0; partial graph1update không checkpoint/export/COMPLETE. Chưa research fitted/calibration/S04/S05/context100/resume/full Gate/CUDA.
- **GPU09HOST — `c1d93ec`:** [source preparation](reports/akt_gpu_host_preparation_20261108.md), [bundle102outputs](runs/akt-gpu-host-preparation-20261108-01/README.md). Final warm20/generic9/cold24/packet41 methods là **bốn scopes local mock/AST/metadata**, không tổng fullGate. Historical CPU marker/tag engineering không actual GPU-host discovery/startup/hidden audit/install hoặc wheel-byte/CUDA proof.0model/optimizer/hardwarechange/remote trong batch. Report snapshot còn chữ proposed/pre-closure; mốc này chỉ xác nhận archive closure bằng manifest.
- **DEMO02 — source `22b3522`, bundle `b9eaaab`:** [viewer closed-loop](reports/demo_closed_loop_readiness_20261108.md), [bundle66outputs](runs/demo-closed-loop-engineering-20261108-01/README.md). **83 PASS**, cumulative36,1590131s ≤ 60s; giữ47PASS/36HTTPfailures trial01, không sourcefix giữa trials. Cùng trang chọn trajectory/common-prefix/first-break, giữ bảy negatives; actual mobile390×844, console0error, QA tab/server đã đóng. Post-hoc source-local CID/newN0/native Bscore noncalibrated/Pafterselect/package≠edges; không paired ΔP sau divergence hoặc live fitted personalization. T21 vẫn IN_PROGRESS/partial E11.

**Trạng thái vận hành hiện tại:** Linux Gate24 771 PASS và CPUdummy48train/8val/2updates/durable9files là **bằng chứng lịch sử source trước Graph03/04**. Không dùng Gate24 hoặc targeted tests/mocks mới để chứng nhận current full Gate, actual CUDA/GPU ready, hiệu quả CG-AKT hay hoàn thành RQ. Windows Gate22 đã stale. Các snapshot hiện hành cũ phía dưới giữ nguyên thời điểm/verdict.

**Mốc mới08/11:** [A2/A3 confidence/gate](reports/akt_graph_confidence_gate_readiness_20261108.md) commit `4a256a4`:43targeted CPU PASS/0optimizer,37outputs rawGitverified; chưa graph-aware trainer/fit/calibration hoặc GPU. Gate24 trước thay đổi này **không chứng nhận current source**. [Bản thảo C14](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) commit `4edf1f8`:14claims/104pointers/28inputs/24links đã kiểm; C01–C13 giữ nguyên, C14 post-hoc source-local/newN0, không finalRQ.

**RQDIAG05 đã đóng (`850f5ab`):** [closed-loop và concept ranking](reports/rq1_closed_loop_reconstruction_20261108.md) giữ exact legacy 3.240events/pass,27statepairs và9uniformpairs. Native ranking key khớp3.240/3.240 CID; trong common-prefix first breaks,8full+2empty cases có cùng M/R/C/B membership nhưng khác score chọn khác concept. Đây là **post-hoc source-local explanation**, không edge-only/causal/learning-benefit hoặc hoàn tất RQ1. Served-item P được tính sau selection trong source này. Accepted-02 có125outputs; failed archiver-01 có116outputs giữ nguyên; cả241raw Git blobs đã kiểm. Report snapshot còn chữ PROPOSED vì được freeze trước closure; mốc chỉ mục này xác nhận actual closure bằng manifest.

**GKT06 đã nghiệm thu (`f204f69`):** [epoch pipeline](reports/gkt_epoch_pipeline_readiness_20261108.md) có38purePASS và actual2epochs/2Adamreturns;6train targets mỗi epoch, selection đủ4=2scored+2unsupported/0research_fitted.95outputs raw Git verified. Đây là lifecycle engineering, chưa full corpus/final GKT baseline/refit/resume hoặc S04/S05 adoption.

## Bổ sung08/11 — GKT05 và discovery CPU đã nghiệm thu

- [GKT05 adapter](reports/gkt_adapter_readiness_20261108.md), commit `4a64525`:32portable tests và1actual stored checkpoint load;6targets=2scored+4unsupported,0research_fitted/optimizer.69outputs đã kiểm raw Git; chưa epoch/corpus/fitted OnlineSession hoặc training-attested item mapping.
- [Discovery CPU trước T4](reports/akt_t4_discovery_readiness_20261108.md), commit `04b8ac1`:165source/lock hashes,44versions, cả hai cleanup accepted; **warm candidate, chưa CUDA/GPU ready**.53outputs raw Git verified; giữ timeout, failed discovery01 và scheme correction. Không cài lại venv/đổi hardware/Modal.

## Hiện hành08/11 — Linux CPU worker đã đóng (`1c52043`)

Mốc vận hành hiện tại là **Linux Gate24 771 PASS, 0 fail/error/skip** và **native CPU dummy 48 train targets / 8 validation predictions / 2 optimizer updates thật**, với **9 file đã lưu bền vững và khớp SHA**. [báo cáo](reports/akt_linux_worker_readiness_20261108.md), [bundle đã đóng](runs/akt-linux-worker-readiness-20261108-01/README.md), [manifest](runs/akt-linux-worker-readiness-20261108-01/manifest.json). Đã kiểm lại toàn bộ **194 output SHA** của bundle và 9 bản sao artifact. GKT03 (`b67eba0`) và các kết quả nghiên cứu phía dưới giữ nguyên phạm vi.

| Bằng chứng hiện tại | Kết quả đã xác minh | Phạm vi |
|---|---|---|
| Linux native Gate24 | 268.092342194s ≤ 600s; 771 PASS; Linux lock `60dad3de…35cc45a` | Software/source gate trên Linux CPU, không CUDA readiness. |
| Native CPU dummy | Phase 26.110794024s; 48 train targets/6 windows; 8/8 validation predictions, 0 unseen; 2 nonzero-gradient và 2 parameter-update steps; reload exact | Synthetic engineering, không research fitted efficacy, model selection/refit/resume hoặc RQ completion. |
| [Durable copy inventory](../experiments/akt/results/ctx-linux-20261108-01/transfer-copy-inventory.json) | 4 binary (448378 B) + 5 native text = 9 file khớp SHA/size trước–sau; checkpoint `f77b39c6…de8cc6` | Artifact Colab CPU đã hoàn tất, không local fit hoặc model/Parquet load. Binary giữ ngoài Git. |

**Lịch sử giữ nguyên:** Windows Gate22 768 PASS là **STALE sau test-only `dd80006`**; Gate23 763 PASS/5 FAIL và các failure loader/transport vẫn giữ verdict gốc. Các dòng “current”, “pending archive”, “chưa Linux Gate/mainworker” trong snapshot cũ phía dưới mô tả thời điểm trước mốc này. GPU09 còn **actual CUDA pending**; immutable image, CUDA lifecycle/resume và protocol S01/S04/S05 chưa được đóng bằng CPU proof. Không đánh dấu RQ hoàn tất hoặc GPU ready.

**Vận hành Linux CPU sau cập nhật nguồn:** Gate23 có 763 PASS/5 FAIL, chưa được chấp nhận. Bốn lỗi do checkout thiếu upstream loader; lỗi còn lại được tái hiện là khác CPU threads (matched threads cho kết quả bitwise bằng nhau). Test-only fix `dd80006` đạt 26 targeted tests; native model giữ nguyên. Gate22 Windows là bằng chứng lịch sử cho source trước sửa test, không chứng nhận source hiện tại. Xem [state phục hồi](../docs/thesis_recovery/INVESTIGATION_STATE.json) và [log](../docs/thesis_recovery/INVESTIGATION_LOG.md); chưa chạy main worker/CUDA/Modal.

## Bổ sung08/11 — GKT04 và bản thảo C13 đã đóng

- **GKT04 — `2d8aaf8`:** [weights-only checkpoint report](reports/gkt_checkpoint_readiness_20261108.md), [bundle60outputs](runs/gkt-checkpoint-engineering-20261108-01/README.md), [manifest](runs/gkt-checkpoint-engineering-20261108-01/manifest.json). Final **40 PASS/0 fail/error/skip**; **2 actual Adam updates tổng hai trials** (1/trial), conservative **24,609858s ≤ 60s**, toàn bộ60outputSHA và source/test SHA đã kiểm lại. Trial01 vẫn **1PASS/39fixtureERROR** do quyền hard-link `WinError5`; trial02 cùng source/test được chạy trong bounded process đã được phép. Không đổi failure thành PASS hoặc gọi đây là source bugfix.
- **Phạm vi GKT:** GKT03 (`b67eba0`) vẫn là one train-batch/45tests/4updates/32outputs. GKT04 là followup hoàn tất weights-only save/load riêng, không thay giới hạn lịch sử của GKT03. Không optimizer/RNG/hidden-state restoration, resume, epoch/corpus, refit/selection hoặc fitted inference; scientific S04/S05 và baseline nghiên cứu đầy đủ vẫn pending.
- **WRITE02 hiện tại — `1b3d3f9`:** [bản thảo RQ1–RQ2](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) và [source map](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json) có **13 claims/80 JSON pointers/21 inputs** được kiểm. C13 chỉ tích hợp observability reproduction: **944/964 P changes giữ full preview**, **2/116 P-same rows đổi preview**, **22/1.080 full-preview changes**, actual shared queries1.080keys; ba seed families, **new independent N=0**. C01–C12/16inputs cũ và snapshot `d30dafe` giữ nguyên lịch sử; không backfill trace, causal/served-action/calibration claim hoặc RQ completion. Mốc Linux Gate24/CPU worker phía trên giữ nguyên.

## Bổ sung08/11 — engineering, bản thảo và reproduction

- **GKT03 — `b67eba0`:** [train-batch readiness](reports/gkt_training_readiness_20261108.md),45CPUtests/4actual Adam updates/32outputs; conservative cumulative10,844604s≤60. Manifest `c1194df13f6f8f6efa41469264e6ced6447135bf389c2d03729a755d1ed14e0f`; COMPLETED_ENGINEERING_ONLY sau GKT02. Chưa checkpoint/resume/epoch/corpus/fitted adapter hoặc S04/S05; cooperative budget/state/source không là nonresettable authorization.

| Task/commit | Kết quả source-bound | Giới hạn còn giữ |
|---|---|---|
| GKT02 — `6035262` | [Recurrent candidate](reports/gkt_recurrent_candidate_readiness_20261108.md):88finalCPUtests/0optimizer, [47outputs](runs/gkt-recurrent-candidate-engineering-20261108-01/README.md); source recurrent SHA `510195d71c1ddb743f747e78d7d874c04bb809931c5ec24ae6fe907fe53ec072`, manifest `b00ca32d5c4385da9a84d3442b82638ec344a64cb191b91b1b02c5ab513d09ac`. | Hoàn tất engineering candidate sau GKT01; chưa trainer/fitted adapter/learned graph, author parity hoặc final S05/required baseline. |
| WRITE02 — `d30dafe` | [Tiểu mục diagnostic results](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md), [source map](reports/THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json):12claims/53JSONPointers/14links, reviewPASS+3P3clarifications. MD `da64fbae222b9d116ebdc41933f02912ed04385eac43491d3a438b4f649caa8e`; JSON `04e879674243dbdcbc8ba69423819662509bf8bdd7039b42d0fac92a69b50fbf`. | Hoàn tất bản thảo sau WRITE01; stored pilot/descriptive evidence, không final RQ1/RQ2 hoặc causal efficacy. |

- **RQDIAG04 — `7dd8338`:** [query/full-preview reproduction](reports/rq1_query_observability_reproduction_20261108.md),12spyPASS/40outputs,71,9959014s≤120/new independentN=0/0optimizer. Giữ exactlegacy và parent kiểm1080sharedqueries; observation mới thuộc reproduction, không backfill trace cũ, không servedaction/causal/finalRQ1.

TASKS ghi GKT02 phụ thuộc GKT01; WRITE02 phụ thuộc WRITE01/RQDIAG03; RQDIAG04 phụ thuộc RQDIAG03. Các snapshots cũ ghi GKT chỉ kernel vẫn là lịch sử trước candidate này. Không cập nhật verdict runtime/Linux Gate đang chạy từ hai deliverables trên; STATE/LOG và kết quả vận hành do parent đối chiếu riêng.

## Mới nhất08/11 — Windows Gate22 và audit existing Linux CPU venv

**Windows Gate22 hiện hành768PASS/0fail/error/skip,477.7091635s≤540s**; [report](../artifacts/akt/preflight/gate2-evidence-20261108-linux-tooling-22.json) SHA`f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd`. Run-id `linux-tooling` chỉ mục đích sửa tooling, không phải actual Linux fullGate. Các heading “mới nhất/current” Gate21 hoặc pending archive phía dưới là snapshots trước cập nhật này; giữ nguyên lịch sử.

| Phạm vi hiện tại | Điều đã xác minh | Điều không được tự suy |
|---|---|---|
| [Linux install/audit](reports/akt_linux_isolated_install_20261108.md), [bundle80outputs](runs/akt-linux-isolated-install-20261108-01/README.md) | Hai controllers01/02 đều **FAILED**.02 pip-install/report44selected và pip-check exit0 nhưng controller fail metadata guard. Audit riêng **EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY**,23.361956656s≤90s,1child,44versions/all RECORD origins/8CPUimports/1CPUscalar. | Không relabel02. Torch2.7.1+cu126/CUDA12.6 là build metadata, CUDA chưa initialize; chưa CUDA/image/fullLinuxGate/main-worker/cost forecast. |
| [Tooling118PASS](reports/akt_linux_gate_tooling_readiness_20261108.md), [bundle44outputs](runs/linux-gate-tooling-engineering-20261108-01/README.md), commit `7b07d61` | Explicit selectedlock/publicpackaging giữ Windows default/strictguards; RED107PASS/11FAIL; parent raw44Git verified. |0optimizer ở targeted suite; không scientific protocol/trained baseline/RQ completion. |
| [Linux exact-source kit](../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/README.md) | Local archive980252bytes,161payload/120exactGate-source paths; SHA/inventory đã kiểm. | Chưa upload/extract remote, upstream clone hoặc Linux Gate/worker. |

Đã kiểm124new output SHA cho80+44bundles; WindowsGate22 snapshots trong bundle80. Audit riêng chỉ kiểm existing venv/CPU imports/scalar,0pip/install/network/model/optimizer/Modal. Đây là môi trường/kỹ thuật, không efficacy. S01/S04/S05/allocation/required baselines, giới hạn RQ1/RQ2 pilot và RQ3 chưa fittedcomparisons giữ nguyên.

**Kết nối/vận hành:** bridge98978 đã hết phiên. Cầu nối mới55463 đã trả `ready/browser_open` sau khi khởi chạy localhost ở quyền thực thi được duyệt; đang chờ người dùng xác nhận MCP, giữ CPU. Không kết luận người dùng kết nối sai. Phải kiểm runtime/venv cũ còn đúng identity trước khi dùng tiếp. Chưa actual Linux full software Gate, bounded public main-worker lifecycle, CUDA hardware/image hoặc end-to-end throughput/cost. Không dùng Windows pointer hoặc audit CPU làm GPU readiness.

## Trạng thái mới nhất08/11 — Gate21 và các batch engineering đã đóng

**Gate21 CPU software757PASS,0fail/error/skip,467.1361735s≤540s**; [report](../artifacts/akt/preflight/gate2-evidence-20261108-elapsed-guard-21.json), current pointer/source/lock đã được reader xác minh. Gate20 vẫn **REJECTED_RESOURCE_BOUND** dù724functional PASS vì1083.995106s>540s. Không sửa Gate20 hoặc dùng nó để chấp thuận source mới. Các đoạn “current” có ngày cũ phía dưới là snapshot lịch sử.

| Phạm vi hiện có | Bằng chứng mới đã đóng | Phần chưa được suy thành hoàn tất |
|---|---|---|
| SAKT03 | [139PASS/51outputs](runs/sakt-training-engineering-20261108-01/README.md), commit `9952bc7`; CPU synthetic train/validation/checkpoint engineering | Chưa fitted baseline nghiên cứu, selection/refit/resume/calibration hoặc complete Grade10 training bridge |
| SIMTRAIN01 | [40targeted PASS/93outputs](runs/akt-simulator-engineering-20261108-01/README.md), commit `000ea22`; Gate19 lịch sử701PASS, toy train/selection lifecycle | Chưa full research corpus/trainer/epoch-selection protocol; không efficacy |
| Graph-GAM variants | [38PASS/27outputs](runs/graph-gam-variant-engineering-20261108-01/README.md), commit `96004e2`;97native state updates,0optimizer/global fit | Parent/local adaptation kết hợp; chưa fitted comparator CV hoặc instructional benefit |
| Resource guard | [47PASS/68outputs](runs/gate2-budget-fix-20261108-01/README.md), commit `4af8f85`; actual RED19PASS/25FAIL giữ lại | Operational fix, không training/GPU acceptance; snapshot rejected pointer trong archive là lịch sử trước Gate21 |
| A0/A1 native graph branch | [23targeted PASS/196outputs](runs/akt-graph-prototype-engineering-20261108-01/README.md), commit `6377265`;0optimizer; bundle chứa Gate21 accepted | Parent-mean fixedc1/g1 toy prototype; A2/A3/confidence/learned gate/graph-aware trainer và fitted CG comparisons còn thiếu |
| Linux dependency resolution | [37outputs](runs/akt-linux-dependency-resolution-20261108-01/README.md), actual CPU44packages/14NVIDIA,0install | Candidate index hashes/metadata closure, chưa wheel bytes/import/image/CUDA |

Sáu bundle có472outputs đã đối chiếu SHA; parent đã kiểm raw Git27/68/196outputs ở ba commit Graph-GAM/budgetfix/graph prototype. Tests/source readiness không thay kết quả RQ: RQ1/RQ2 vẫn pilot/descriptive có giới hạn; RQ3 chưa có trained scientific A0–A3 comparisons. S01/S04/S05 và minimum experiment allocation chưa được tự chấp thuận. SAKT/GKT và required baselines tiếp tục giữ trong phạm vi đề cương; GKT hiện là partial kernel.

Gate21 có suite `tests/akt tests/shared_kt`; targeted SAKT139 và Graph-GAM38 được kiểm riêng, không cộng hoặc gán lại vào757tests.

**Colab CPU/Linux mới đã archive:** [report](reports/akt_linux_dependency_resolution_20261108.md), [bundle37outputs](runs/akt-linux-dependency-resolution-20261108-01/README.md) và [raw14files/SHA verified](../artifacts/akt/colab/gpu08-linux-20261108-01/received/manifest.json). Resolution44packages/14NVIDIA,0install; kiểm offline46active constraints và tái dựng lock là validation cùng evidence. Site unchanged là probe/danh sách tên theo source, không full byte attestation. Candidate hashes chưa chứng minh wheel bytes/install/image/CUDA runtime/main-worker. Không GPU/Modal mới từ batch này; actual Linux/CUDA training và Gate4 vẫn thiếu.

**Bước tiếp theo chưa chạy:** [addendum acceptance](reports/akt_linux_dependency_resolution_20261108_addendum.md) làm rõ cài trực tiếp44URLs trong candidate lock bằng pip `--require-hashes` có thể dùng stage/budget/isolated target riêng; giữ wheelhouse là tùy chọn tách biệt. Wording future-step trong report gốc không bổ sung runtime evidence hoặc approval cài đặt.

**Đính chính demo:** “12/120 nodes” của [report visualQA](reports/demo_readiness_20261108.md) là số phần tử timeline `#route li`, domain vẫn28concepts. Giữ nguyên [bundle demo93outputs](runs/demo-readonly-engineering-20261108-01/README.md); đây là preview replay, chưa served-action/live fitted personalization.

## Snapshot engineering08/11 — xem giới hạn từng bằng chứng

Gate18 WindowsCPU661PASS; real-guard watchdog toy lifecycle48targets/2updates/8predictions đã kiểm. **Actual new-worker Linux/CUDA và GPU08fullhashlock/image vẫn thiếu**, chưa Gate4/fulltraining. GKT43PASS purekernel vẫn incomplete; demo53PASS+visualQA là storedsynthetic replay/partialE11; bản thảo phương phápRQ12 đã cósourcesmap. RQ1/RQ2 chỉ pilot/descriptive, RQ3 chưa fittedcomparisons. [Context report](reports/akt_worker_context_readiness_20261108.md), [demo](reports/demo_readiness_20261108.md), [GKT](reports/gkt_core_readiness_20261108.md), [thesisdraft](reports/THESIS_METHODS_RQ12_DRAFT_20261108.md). No Modal credit used by batch, no Holdout or external sending. Các snapshot cũ dưới đây là lịch sử, không thay current verdict.


**Trạng thái hiện tại — 07/11/2026:** đọc dashboard này trước các snapshots lịch sử bên dưới. Đề cương và Paper1/2 đã tìm được; lịch sử04/11 “chưa thấy” không còn mô tả inventory hiện tại. Không dùng các số test/version của snapshot cũ thay nghiệm thu mới.

| Phạm vi | Trạng thái dựa bằng chứng hiện tại | Việc còn thiếu |
|---|---|---|
| RQ1/RQ2 | PARTIALLY VERIFIED: source diagnosis, fixed-stream/closed-loop pilots, factorial và Junyi controls; đã tổng hợp với giới hạn | Final estimands, đủ mechanism exposure, controlled inference và S04/S05; không causal graph-benefit claim |
| Paper1 | Audit PDF/source/Git/archives hoàn tất trong phạm vi local; exact submitted revision vẫn thiếu | Source+inputs+actual seed list+per-seed outputs và xác nhận tác giả/advisor |
| AKT graph-free | Actual Colab T4 bounded CUDA lifecycle/recovery PASS; local Gate15462pass, Colab CPU505pass/2declared exclusions | Linux/CUDA mainworker contract, representative pilot/throughput, full Development protocol; Gate4false |
| Graph residual/gate | Kernel độc lập42tests pass, reuse causal context guards, graph-off parity | Chưa native AKT integration, learned gate/confidence training hoặc CG-AKT result |
| SAKT | Paper-equation core37CPUtests pass,0optimizersteps | Adapter/trainer/export/resume/final protocol; không full baseline benchmark |
| GKT và required comparisons | Yêu cầu đề cương giữ nguyên | GKT và các evaluation pipelines còn phải triển khai/kiểm; không tự loại baseline |
| Modal | 30USD free credits do user báo,0USD trả thêm; **chưa dùng compute/credits** | Runtime/image/Volume/budget controls và exact approved run allocation |

Đọc [nghiệm thu CUDA](reports/colab_cuda_acceptance_20261107.md), [phản biện](reports/colab_cuda_adversarial_review_20261107.md), [RQ1/RQ2 synthesis](reports/rq12_evidence_synthesis_20261107.md) và [mục lục bằng chứng](EVIDENCE_INDEX.md). Heavy artifacts giữ tại `experiments/akt/results/colab-actual-cuda-20261107-01/`; không nhầm software acceptance với hoàn thành RQ. Next task làGPU06 trong backlog, chưa launch training/Modal.

## Batch tiếp theo: runtime và worker đã được kiểm trên CPU

- **Gate17:513pass,0fail/error/skip**,269,98s; tách với Gate16failed512pass1fail và giữ bằng chứng đường dẫn. Không actualLinux/CUDAworker pass từ mocks.
- [Runtime report](reports/akt_linux_runtime_contract_20261107.md) và [worker report](reports/akt_main_worker_lifecycle_20261107.md): platform-aware strictvenv metadata; actualsyntheticParquet→8train targets→validation/checkpoint/export4rows. Chưa Junyi pilot hoặc fulltraining.
- [SAKT adapter](reports/sakt_adapter_readiness_20261107.md):89CPUtests gồm payloadregressions; random/unverified weights không fitted baseline, trainer/completebridge còn thiếu.
- Current backlog chuyển GPU07→GPU08→GPU09. Không dùng creditModal hoặc GPU trongbatch; kết quảT4trước đó thuộc frozenkitv12.

## Thành quả báo cáo GVHD08/11

[Báo cáo tiến độ](reports/BAO_CAO_TIEN_DO_GVHD_20261108.md) đã có claim/source/limitations và S01/S04/S05. RQ1 mới xác minh944/964 scalar-probability-changed snapshots giữ concept preview; RQ2 mới cho thấy PYH−PY không robust dưới LOO và Junyi pooled-rate sensitivity do denominator. Đây là descriptive/exploratory diagnosis, chưa hoàn thành RQs. Hai analyzer có25+27synthetic tests đạt, stored-input SHA/reproduction checks đã lưu. Nhánh AKT đang triển khai immutable worker context và bounded CUDA phase; chưa có actualCUDA-mainworker hoặc creditModal run mới.

## Snapshot ngày04/11 và nhật ký cập nhật tiếp theo


**Cập nhật:** 2026-11-04. Trạng thái theo evidence workspace và RQ/sprint từ yêu cầu người dùng; repo không có proposal/advisor feedback để xác minh wording chính thức.

## Dashboard

| Phạm vi | Trạng thái công việc | Xác minh | Bằng chứng và giới hạn |
|---|---|---|---|
| Junyi/BKT baseline | EXPERIMENTALLY VALIDATED | VERIFIED | BKT CV/refit/Test; Test dùng một lần, không tuning. |
| GAM-KT graph-free | EXPERIMENTALLY VALIDATED | VERIFIED | Pilot, 5-fold CV, common-row và learner bootstrap; Development only. |
| AKT graph-free | TECHNICALLY VALIDATED; pilot FAILED | VERIFIED | Gate 2 155 tests pass và bounded smoke; pilot 14-02 failed trước validation/export. Không có benchmark. |
| Graph-GAM-KT, SAKT, GKT | NOT STARTED trong scope tìm thấy | MISSING | Không thấy implementation/run trong source, experiments và reports đã kiểm tra. |
| Fixed-graph AKT, CG-AKT | NOT STARTED trong scope tìm thấy | MISSING | Chưa thấy graph-aware AKT implementation/result. |
| Grade 10 simulator/policy loop | NEEDS REVIEW | MISSING | Không thấy simulator/output; Junyi prerequisite catalog không thay thế simulator. |

## RQ coverage

| RQ | Coverage | Đã hỗ trợ | Còn thiếu |
|---|---|---|---|
| RQ1 — vì sao prerequisite graph không ổn định | Chưa trả lời | BKT/GAM predictive baselines; Junyi catalog metadata sơ bộ. | Graph on/off, threshold calibration, decision transitions, policy effects. |
| RQ2 — điều kiện graph có ích/trung tính/có hại | Chưa trả lời | Metadata/sparsity mô tả, không phải controlled experiment. | Graph perturbation/quality, history/cold-start/profile strata, edge confidence. |
| RQ3 — CG-AKT | Chưa trả lời | AKT source, Gate 2 và bounded smoke kỹ thuật. | Full AKT benchmark, fixed graph, CG-AKT, ablations, robustness, closed loop. |

## Sáu sprint

| Sprint | Trạng thái | Bằng chứng | Còn thiếu |
|---|---|---|---|
| 1. Nền tảng/tái lập | NEEDS REVIEW | Research notes, protocol, data audit, RIVF source artifact | Literature protocol, proposal/advisor text, simulator reproduction. |
| 2. Dữ liệu/baselines | IN PROGRESS | Junyi, splits/eval, BKT, GAM; AKT technical work | AKT benchmark, Graph-GAM, SAKT, GKT; simulator chưa thấy. |
| 3. RQ1 diagnosis | NOT STARTED | Predictive BKT/GAM differences | Threshold, decision/policy decomposition, graph ablations. |
| 4. RQ3 method | NOT STARTED | AKT graph-free technical integration | Fixed graph, confidence/gating/fallback, CG-AKT, ablations. |
| 5. RQ2/RQ3 evaluation | NOT STARTED | Bootstrap cho baseline pair, không thay graph study | Perturbation, strata, closed loop, retention/mastery, planned inference. |
| 6. Consolidation | NOT STARTED | Baseline report | Thesis claims, final tables, demo, reproducibility/publication package. |

## Ưu tiên

1. Điều tra lỗi lưu progress AKT; không diễn giải pilot hiện tại thành epoch hoàn tất.
2. Chốt benchmark AKT graph-free, Development-only checkpoint selection và comparability trên 5 folds.
3. Xác minh simulator Grade 10 và graph source.
4. Đăng ký trước graph variants, history/profile strata, mastery thresholds và statistical plan.

## Cập nhật CPU07/11/2026

Adapter nguồn Paper2, explicit mastery trace, matched graph và integrity verifier đã được kiểm. RQ1/RQ2 còn thiếu controlled factorial, Junyi order analysis và inference.

## Pilot CPU09/10 và refit07/11/2026

User chấp thuận bounded pilot trước execution. Xem reports/cpu_pilots_20261107.md về factorial và Junyi order, gồm cơ chế PG không hoạt động trong cohort và cycle witness của catalog thô. Engineering snapshot ở runs/cpu-readiness-pathways-20261107-01, không đồng nghĩa GPU/full-training acceptance.

## Matched-control exposure07/11/2026

Run32learner và run mở rộng256learner có notes/manifests riêng. Xem reports/cpu_matched_controls_20261107.md. Source controls giữ degree/topic/area/prefix-support-bin counts, còn learner-level co-observation thay đổi. Không suy graph neutral từ controls thiếu exposure. Mở rộng256×300/180s do user giao lựa chọn sau proposal cụ thể.

## Portable-kit và Gate2 cuối batch07/11

Kitv6 có113source/fixture files, source-only notebook copies và project venv. Manifest comparison chỉ ra AKT/shared v6 giống v5 đã kiểm240passed1deselected; GAMv6 đạt31passed1deselected. Hai local integration exclusions được ghi rõ. Actual Colab/CUDA chưa chạy. Main Gate2 đạt241test khôngskip. Tất cả log thành công/thất bại của batch ở runs/cpu-controls-portability-20261107-01.

## Recovery CLI và common-population07/11, cập nhật mới

AKT public smoke/pilot recovery đã nối và kiểm trên actual CPU model/parent-worker synthetic fixture; chưa real-data/GPU. Xem `docs/thesis_recovery/17_AKT_RECOVERY_ENGINEERING_LOG.md`. RQ2 có descriptive learner/common-opportunity analysis tái dùng3controls, chưa confirmatory protocol; xem `reports/cpu_common_population_20261107.md`. RQ1/RQ2 còn PARTIAL, RQ3 chưa trained/evaluated. Các Gate2 số test ở mục trước là snapshot lịch sử, build mới cần refresh.

### Nghiệm thu engineering cuối07/11

REC01–REC06 và CPU11 completed **CPU synthetic only**. Source-bound Gate2-08 đạt274pass, pointerverified; GAM riêng45pass. HaiCLI cases có artifact-level exact model/Adam/RNG/prediction proof,85targets/3steps/9predictions/case. Source Paper1/2 và historical results giữ nguyên. RQ1/RQ2 vẫn PARTIAL; fixed/CG-AKT, required comparators và controlled final experiments chưa được hoàn tất từ software tests. Kitv7 mới chỉ ZIP integrity, chưaactualColab/CUDA.

## Interface simulator–KT và batching, cuối07/11

SIM01–SIM05 completed CPU engineering: source bank28concept/84item,168synthetic train targets/1update cho fixture, predict-before-update/session/reset/snapshot/domain guards, fixed duplicate-window export và independent batching84→42calls. Gate2-10 296pass/no fail/error/skip. Xem reports/simulator_kt_interface_20261107.md và runs/cpu-sim-kt-batch-gate-20261107-01. Raw correctness score chưa là mastery, native AKT không nhận elapsed time; research/CG-AKT/GPU readiness không nâng theo software pass. V9 kit ZIP-only, khôngremoteexecution.

## DATA01–04: split/schema và graph-context boundaries, cập nhật cuối07/11

Completed CPU engineering,70targeted tests và Gate2-11 mới361pass0fail/error/skip152.84giây. Có4-role split với explicit namespaces/RNG, observable schema/oracle guards và role-shard coverage; graph context reuse AKT effective-window/OOV, full-history sensitivity riêng, confidence provenance/off/empty/zero controls. Bundles cpu-sim-data-context-20261107-01/02/03 và cpu-sim-data-context-gate-20261107-01 giữ logs/proofs/hashes. Source-only finding: Paper2 latent base parent-smoothed và replay item chọn theo theta thật; collector phải giữ base realization và tách oracle sidecar. Xem report simulator_data_graph_boundaries_20261107.md và contract19. Chưa generate research cohort/train CG-AKT hoặc đo GPU; S04/S05 vẫn pending. V9 không chứa source mới.

## DATA05–07: collector/adapter và domain portability, current software gate07/11

Completed CPU engineering: train-only collector≤2×12fixture, source-environment replay và oracle separation, role-aware KT windows/collator khôngfoldJunyi, versionedsemantic domain đểstripnotebookoutputs không đổi môi trường. Giữ RNGnamespacev1, v1/v2oracle/RNG/query/labels exact.65targeted tests và finalGate2-13 **401pass/no fail/error/skip374.53s**; prior396 là snapshotv1. Archive cpu-sim-collector-gate-20261107-01 và report simulator_collection_runner_20261107.md. V10sourcekit135files ZIP/sourceparity-only, chưaactualLinux/Colab/CUDA.24targets chỉ22/84items, không fullcorpus/T10/fulltrainer hoặc graphmodels/RQbenefit. S04/S05 vẫnpending; các comparator/model/confirmatory deliverables chưa được bỏ.

## COLAB01 — current software gate và recovery,07/11

Gate2-14 **407passed,0fail/error/skip169.05s**, thay401current sau sửa CPU-normalization CUDA RNG state. Probe production train_epoch chạy CPU3processes5vs2+3updates/17targets: model/Adam/RNG/sampler/predictions exact, khôngskip/duplicate.19notebookguardcases giả lập đạt,kitv11 137files cóSHA/CRC/sourceparity. Xem [báo cáo](reports/colab_recovery_readiness_20261107.md), bundles cpu-colab-recovery-20261107-01 và cpu-colab-recovery-gate-20261107-01. Không actualColab/CUDA/Modal compute hoặc credits; chưa hard-kill/Volume durability/Gate4/RQefficacy. RQ1/2 vẫnPARTIAL,RQ3model/evaluation chưahoàn tất.
