# Tổng hợp bằng chứng RQ1/RQ2 để viết KLTN — 07/11/2026

## Kết luận có thể dùng

Bằng chứng hiện có hỗ trợ **chẩn đoán cơ chế và giới hạn thiết kế**, chưa xác nhận graph cải thiện học tập hoặc xác định đầy đủ điều kiện hiệu quả của RQ2. Trong fixed-stream Paper2, full package thay đổi 964/1.080 xác suất nhưng chỉ 22/1.080 action previews; một thay đổi dự báo không bảo đảm thay đổi hành động. Closed-loop pilot có chênh lệch gain trái dấu giữa profiles. Factorial và Junyi controls làm rõ các giả thiết cần kiểm soát, không biến pilot thành kết luận nhân quả trên người học thật.

Đây là tổng hợp mới từ báo cáo và JSON aggregate đã lưu, không có model fit, benchmark, simulator run, graph generation hoặc truy cập raw learner predictions/realdata/Holdout mới. [JSON đi kèm](rq12_evidence_synthesis_20261107.json) lưu phép cộng/trung bình mô tả, danh sách chính xác 42 tệp đầu vào cùng SHA-256 và 21 phép đối chiếu output với manifest gốc. 21/21 hash khớp; điều này chứng minh identity của **các output được chọn**, không xác nhận toàn bộ bundles, validity khoa học hoặc source/runtime hiện hành.

## Cách trích và mức bằng chứng

- **Trực tiếp**: số đếm/kết quả của fixture hoặc pilot cụ thể có output đối chiếu manifest. Phạm vi giới hạn ở nguồn, seeds, profiles, horizon và treatment đã ghi.
- **Suy luận có điều kiện**: diễn giải toán học/cơ chế từ các quan sát và giả thiết được nêu; không coi là causal mediation đã nhận dạng.
- **Còn mở**: chưa có phép đo hoặc chưa đủ support/thiết kế để kết luận. Thiếu bằng chứng không phải effect bằng 0.

Khi trích: claim ID trong tài liệu này → bảng → run ID/tệp output dưới đây → `manifest.json` cùng thư mục → source provenance. SHA đầy đủ của đầu vào tổng hợp và các output trích dẫn nằm trong JSON đi kèm. Các báo cáo [nguồn RQ1/RQ2](cpu_rq12_20261107.md), [factorial/pilot](cpu_pilots_20261107.md), [matched controls](cpu_matched_controls_20261107.md), [common population](cpu_common_population_20261107.md) cung cấp lịch sử và giới hạn chi tiết.

## Chuỗi prediction → calibration → mastery → ready set → action → outcome

Chuỗi dưới đây là khung chẩn đoán. Các tỷ lệ dùng mẫu số khác nhau, không phải funnel lồng nhau hoặc phân rã effect nhân quả. `mastery_crossings` trong JSON được diễn giải là khác biệt quyết định mastery tại các concept–step được so sánh, không suy thành 90 người học đã đạt mastery mới.

| Mắt xích / claim | Đo trực tiếp đã có | Diễn giải được phép | Chưa đo / giới hạn |
|---|---|---|---|
| Prediction — SYN-RQ1-P | Run `cpu-rq12-20261107-03`, `comparisons.json`: full package đổi 964/1.080 supported probabilities; không có unsupported pairs. Empty-graph package đổi 37/1.080. | Package và graph-free có dự báo khác trên cùng item/đáp án/thời điểm; local pathway vẫn có thể đổi dự báo khi không có cạnh. | Full package không cô lập cạnh vì đồng thời bật parent signal, parent adaptation và local adaptation. Không suy predictive superiority từ số lần khác nhau. |
| Calibration — SYN-RQ1-C | Cùng JSON có signed correctness calibration gap quanh probability 0,5 theo seed/profile; số hàng trong band cộng lại là 250 graph-free và 248 full package. | Có kiểm correctness reliability cục bộ quanh 0,5 trong stream này. Band membership của hai models có thể khác. | Chưa có mapping/calibration latent mastery, chưa fit calibrator được đánh giá ngoài calibration sample, chưa có CI hoặc common-band causal comparison. Không thay `is_mastered` nguồn bằng `p >= 0,5`. |
| Mastery — SYN-RQ1-M | Full package: 90 khác biệt trên 30.240 concept decisions (1.080 × 28). Empty graph: 0/30.240. | Có thay đổi boolean `is_mastered` nguồn ở một phần nhỏ trạng thái được so sánh. | Chưa biết các thay đổi đúng hơn so oracle mastery hay tốt hơn về time-to-mastery. Threshold correctness và threshold mastery không cùng ý nghĩa. |
| Ready set — SYN-RQ1-R | Full package đổi 60/1.080 ready sets; empty graph đổi 0. JSON có Jaccard theo seed/profile. | Mastery/policy có thể truyền khác biệt sang tập sẵn sàng, nhưng mức truyền không đồng đều. | Không được lấy 60/90 làm xác suất chuyển tiếp: mẫu số và đơn vị khác nhau; chưa quy riêng đóng góp của controller graph. |
| Action — SYN-RQ1-A | Full package đổi 22/1.080 previews; empty graph đổi 0. Preview dùng bản sao để giữ fixed stream. | Dự báo thay đổi thường chưa chuyển thành hành động khác trong diagnostic này. Seed 20000/PG có 104 probabilities đổi và 0 preview đổi; seed 20001/PG có 108 probabilities và 15 previews đổi. | Preview không phải action thực đã phục vụ. Chưa có conditional table event-level nối từng Δp qua mọi trung gian; không dùng các số tổng để khẳng định đường truyền tuần tự duy nhất. |
| Outcome — SYN-RQ1-O | Run `cpu-closedloop-20261107-01`, `closed_loop_outcomes.json`: 27 trajectories × 120 steps = 3.240 events; bảng dưới. | Package có thể làm policy/trajectories và latent outcomes khác trong simulator đã chỉ định. | Closed loop không còn same-target paired prediction khi actions khác; labels cũng có thể khác. Chưa CI, chưa final independent seeds, chưa tách pathway/cạnh, chưa kết luận ngoài simulator. |

Run03 có 3 seeds 20000–20002 × 3 profiles × 120 steps. Cả graph-free và graph-package dùng cùng stream; G_env và G_controller giữ cố định. Bởi vậy đây là estimator-package diagnostic trong một graph-aware system, không phải so sánh toàn hệ thống “có graph” với “không graph”.

| Profile | Full package − graph-free net mean theta gain, mean 3 paired seeds | Actual action disagreement / 360 paired steps |
|---|---:|---:|
| PG | +0,1611440503 | 208 |
| PY | −0,4463139457 | 200 |
| PYH | +0,2249713515 | 72 |

Gain là mean Elo-scale trên 28 concepts, không là phần trăm tăng điểm hoặc learning effect trên Junyi. Ba seeds/profile là đơn vị paired mô tả; 360 steps không phải 360 independent learners. Không dùng trái dấu giữa profiles làm kiểm định heterogeneity.

## Ba bẫy trong kế hoạch chẩn đoán

Tên/nhóm trap theo [kế hoạch Paper1/Paper2](../../docs/thesis_recovery/04_PAPER1_PAPER2_DIAGNOSTIC_PLAN.md). Trap 1 gồm hai nội dung controller/re-entry và retention; tách hai hàng để tránh gộp hai lập luận khác nhau.

| Trap / claim | Bằng chứng trực tiếp và nguồn | Suy luận có điều kiện | Câu hỏi còn mở / điều không được viết |
|---|---|---|---|
| Trap 1a: controller/re-entry — SYN-T1-REENTRY | `cpu-rq12-20261107-03/paper1_counterexample.json`: selector notebook Paper1 cell 11 cho A1→B1→A2, chapters A→B→A, 1 chapter re-entry ở cả `lowest_elo` và `cross_chapter_unlock`. Mastery được gán theo kịch bản trên synthetic DAG. | Selector **revision đang có** không bảo đảm zero re-entry trên mọi graph. Zero có thể do controller constraints trong revision khác. | Chưa tìm đúng source tương ứng PDF; counterexample không là reproduction bảng Paper1 hoặc kết luận PDF sai. Chưa có actual learning trajectory với mastery tự phát sinh cho fixture này. |
| Trap 1b: retention — SYN-T1-RETENTION | `cpu-rq12-20261107-03/retention.json`: nguồn Paper2 cell 9, rate 0,06/ngày, 14 ngày, factor 0,43171052342907973; fixture absolute error 1,7053×10⁻¹³. Tính lại trên 27 outcome aggregates closed-loop: max absolute error 2,5313×10⁻¹⁴. | Với không practice sau T, decay đồng nhất quanh cùng fixed base và miền gain của fixture: `G14 = exp(-0,84) × GT`; paired gain deltas cùng factor. Retained **net mean theta gain** không cung cấp ranking độc lập với final gain trong điều kiện này. | State tại T vẫn có thể phụ thuộc practice order trước T. Không nói retention/practice-order hoàn toàn bất biến; không mở rộng identity sang nonlinear soft mastery, heterogeneous forgetting, practice sau T hoặc gross learning gain. Chưa kiểm learning benefit của sensitivity forgetting mới. |
| Trap 2: ability, paired factorial và DiD — SYN-T2-FACTORIAL | `cpu-factorial-20261107-01/{manifest,contrasts,summary}.json`: 10 seeds 21000–21009 × 3 profiles × 4 cells × 120 = 14.400 events. Mean interaction PG 0; PY +0,03401725799; PYH +0,05352858741. Deficit coverage tại λ0,55: PG 0/2.400, PY 1.919/2.400, PYH 1.197/2.400 từ `cpu_pilot_followup_20261107.json`. | Estimand là `[(edge-on−edge-off)|λ0,55 − (edge-on−edge-off)|λ0]` conditional simulator, không raw graph gain. Cùng base realization/uniforms tránh đổi ability cùng treatment. PG minimum base 1269,3118 > readiness 1150 và theta không dưới base trong dynamics được kiểm; zero interaction có giải thích cơ chế bất hoạt. | Không gọi High/Low là treated/control rồi time-DiD; chưa có parallel-trends/counterfactual của cách so đó. Initial abilities vẫn graph-correlated theo nguồn. Parent signal/adaptation bật cùng nhau, local pathway off ở cả nhánh: chưa đủ full pathway ablation. Chưa CI/significance hoặc kết luận mọi high-ability learner không cần graph. |
| Trap 3: Junyi logged-order controls — SYN-T3-ORDER | `cpu-junyi-order-20261107-01`: 32 inner-train learners/1.211 events; 48 parent-first trên 52 coobserved pairs, 24 supported edges. Expanded/control và common-population results ở hai bảng sau. | Graph metadata có thể phù hợp thứ tự exposure trong logs; degree/strata matching không tự giữ learner-level exposure. Đây là chẩn đoán nguy cơ proxy-order. | Không đo prediction advantage, learning outcome hoặc instructional causal effect. Prefix missing không là prerequisite sai/chưa mastery. Controls ít exposure và contrast gần 0 không chứng minh graph neutral/equivalent. |

### Trap 3: graph version, denominators và exposure

Run `cpu-junyi-graph-reconstruction-20261107-01/graph.json` tái dựng current-catalog bằng SCC rule của Paper2: 835 nodes, 979 edges sau loại 2 self-loops, bỏ 3 intra-SCC edges thành DAG 976 edges. Đây là reconstruction theo quy tắc lịch sử, **không chứng minh identical historical edge bytes** vì certificate lịch sử thiếu raw/edge hashes. Graph version cho nghiên cứu xác nhận vẫn cần chốt.

Run `cpu-junyi-controls-20261107-02-expanded` giữ 256 inner-train learners outer-fold 0, tối đa 300 events/learner, tổng 12.575 events. Controls dùng seeds 0/1/2, mỗi seed 10 double-edge swaps và 40 changed edge entries, giữ in/out-degree, joint topic/area/prefix-support-bin pair counts. Bins 0/1–2/3–5/6+ là coarse prefix bins, không là full-training support. Không lấy mẫu đều toàn bộ DAG và không chọn seed theo kết quả.

| Graph | Supported edges | Coobserved edge–learner pairs | Parent-first pairs | Changed entries có child quan sát được |
|---|---:|---:|---:|---:|
| Raw sau loại self-loop | 199 | 650 | 576 | — |
| Corrected base 976 edges | 198 | 649 | 575 | — |
| Control seed 0 | 198 | 650 | 576 | 14 |
| Control seed 1 | 198 | 644 | 568 | 20 |
| Control seed 2 | 194 | 645 | 574 | 14 |

Raw và controls dùng graph khác: không so control với denominator raw như cùng base. Có child quan sát không đồng nghĩa cả endpoints co-observed cùng learner. Với pilot 32 learners, coverage note báo changed entries co-observed cùng learner chỉ 0/2/0 dù mỗi control cũng đổi 40 entries; bảng này giải thích vì sao đủ số swaps chưa bảo đảm phép so có lực chẩn đoán.

`cpu-junyi-common-20261107-01/common_population.json` giữ cùng observed learner–child opportunities, incoming-degree denominator; trung bình child trong learner rồi equal-weight learner. Có 239/256 eligible learners, 1.361 opportunities; base prior fraction 0,1658617320 và unobserved-parent fraction 0,8208523602. Đây là mean phân cấp, không phải 82% prerequisite toàn Junyi thiếu.

| Seed | Opportunities đổi parent set / 1.361 | Learners đổi prior / 239 | Δprior fraction, control−base | Common-coobserved opportunities | Common learners | Δprior trên common subset |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 43 | 1 | +0,0006973501 | 569 | 96 | 0 |
| 1 | 42 | 7 | −0,0011790446 | 564 | 96 | −0,0030826185 |
| 2 | 12 | 1 | −0,0008368201 | 566 | 95 | 0 |

Identity control có mean contrasts bằng đúng 0 ở cả bốn categories: prior/later/tie/unobserved. Common subsets giữ lần lượt 41,8075% / 41,4401% / 41,5871% opportunities, có attrition lớn và target population khác nhau theo comparison. Không pool/xếp hạng ba subsets như cùng estimand. Zero prior contrast không có nghĩa toàn bộ category distributions giống nhau: seed 2 vẫn có thay đổi later/missing trên common subset. Ties được tách theo timestamp, không bị source-row tie-break ép thành before/after; các opportunities này không có tie.

## Claim → evidence sẵn trích dẫn và phần thực sự hỗ trợ RQ

| Claim tổng hợp | Câu có thể đưa vào kết quả/thảo luận | Mức bằng chứng | Liên hệ RQ / khoảng trống |
|---|---|---|---|
| SYN-RQ1-CHAIN | “Trong diagnostic Paper2 trên 1.080 paired events, full package đổi 964 probabilities, 90/30.240 mastery decisions, 60 ready sets và 22 action previews.” | Trực tiếp, fixed stream. | Hỗ trợ một phần E03/RQ1: chẩn đoán prediction–decision không truyền một-một. Chưa calibration-to-latent/mastery validity, pathway isolation hoặc CI. |
| SYN-RQ1-PACKAGE | “Empty-graph package vẫn đổi 37 probabilities nhưng không đổi mastery, ready set hoặc action preview trong phạm vi đã đo.” | Trực tiếp. | Hỗ trợ sự cần thiết của local-only negative control. Không gán mọi full-package difference cho edges. |
| SYN-RQ1-LOOP | “Pilot closed-loop cho gain deltas khác dấu giữa PG/PY/PYH khi cùng source dynamics/controller và paired random starts.” | Trực tiếp, descriptive pilot. | Hỗ trợ phân biệt fixed-stream và closed loop. Chưa chứng minh population effect/heterogeneity hoặc tác động chỉ do cạnh. |
| SYN-RQ12-INVARIANTS | “Re-entry counterexample phụ thuộc source revision; retained14 net gain là scalar transform của final net gain dưới giả thiết decay đã chỉ định.” | Fixture trực tiếp + suy luận toán học có điều kiện. | Hỗ trợ E01/E02/RQ1/RQ2 về provenance/invariant. Revision Paper1 đúng PDF và sensitivity dynamics còn mở. |
| SYN-RQ2-MECHANISM | “Paired λ×edge pilot cho thấy feasibility của interaction contrast; PG không có prerequisite deficit trong 2.400 mechanism-on events.” | Trực tiếp, conditional simulator. | Hỗ trợ một phần E04/RQ2 về mechanism coverage; chưa đủ xác nhận điều kiện lợi ích, graph-independent initialization sensitivity hoặc full ablations. |
| SYN-RQ2-COVERAGE | “Matched controls bảo toàn degree và coarse strata vẫn thay learner-level exposure; chỉ 1–7/239 learners đổi prior score trong common-population diagnostic.” | Trực tiếp, descriptive logged-order. | Hỗ trợ thiết kế E05/RQ2 và giải thích low-exposure null. Chưa có predictive controls/common-fitted metrics hoặc E06 noise/history/profile efficacy. |

Các [claim/evidence ledger](../CLAIM_EVIDENCE_MATRIX.md) và [index](../EVIDENCE_INDEX.md) có hàng lịch sử ghi “chưa có result” trước các cập nhật CPU07/11. Khi dùng cần đọc phần bổ sung: nay có diagnostics/pilots, nhưng vẫn chưa có qualifying confirmatory graph-benefit result. Không tự thay trạng thái ledger trong tài liệu này.

## Bằng chứng tối thiểu còn thiếu

Theo [truy vết yêu cầu](../../docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md) và [experiment matrix đề xuất](../../docs/thesis_recovery/05_EXPERIMENT_MATRIX.md), các mục sau còn cần quyết định/thu thập; bảng không phải approval thực thi.

| Phần | Tối thiểu để đi từ chẩn đoán sang kết luận có giới hạn |
|---|---|
| E01/E02 | Adjudication source-revision Paper1; ghi rõ phần tái lập được/phần unresolved. Giữ original retention identity; nếu thêm forgetting sensitivity phải version và freeze giả thiết trước xem kết quả. |
| E03/RQ1 | Freeze mastery/reference calibration và numerical threshold convention; full signal/parent/local ablations với local control bằng nhau; matched denominators, shadow/actual decisions và oracle evaluation đúng boundary. Paired seed uncertainty trên end outcomes; không coi events độc lập. |
| E04/RQ2 | Freeze λ×graph estimand, same base/clock/random realization và mechanism coverage; phân biệt original graph-correlated initialization với graph-independent sensitivity. Có precision/inference plan phù hợp trước final seeds. |
| E05/RQ2 | Chốt graph version, learner/child population và coverage rule; controls có exposure được báo trước; bổ sung order-only/train-only graph/frequency controls cùng predictive metrics trên shared fitted targets nếu được duyệt. Logs vẫn chỉ là predictive association. |
| E06/RQ2 | Chưa có xác nhận delete/add/reverse nhiều mức với history/sparsity/profile và intra/cross strata, expert/learned graphs; không bỏ learned graph khỏi phạm vi. Tách retraining dưới noise với inference-only perturbation. |
| Comparator và thống kê | Giữ BKT, GAM, Graph-GAM, AKT, SAKT, GKT theo allocation được duyệt; reuse BKT/GAM aggregates, không chạy lại vì tiện. Freeze primary families/CI/correction/seed handling và giới hạn Test trước confirmatory execution. Omission model không tự được duyệt ở đây. |

S04/S05, methodology và allocation vẫn pending theo hồ sơ; không tự thông qua từ việc pipeline/tests hoặc pilots đã có. Tài liệu không tuyên bố RQ1/RQ2 hoàn tất và không cho completion percentage.

## Năm việc CPU nhỏ có acceptance cụ thể

Đây là đề xuất bàn giao tiếp theo, **chưa chạy trong synthesis**. Cả năm có thể chuẩn bị bằng source/aggregates đã lưu, không cần raw Holdout/Test, realdata query, simulator/model run mới, GPU hoặc cloud.

| Việc | Input và output mong muốn | Acceptance / điểm dừng |
|---|---|---|
| CPU-A: bảng discrepancy Paper1/Paper2 | Dùng source notes/provenance và counterexample đã lưu; bảng claim PDF–revision notebook–fixture–unresolved. | Mỗi claim có page/cell/hash nếu đã biết; missing revision ghi rõ; không khẳng định exact reproduction. Không sửa notebooks/archive. |
| CPU-B: paired-factorial audit từ aggregates | Đọc 30 `contrasts.json` records/summary và mechanism coverage; bảng theo profile với số seeds, signs/zeros, mean và định nghĩa contrast. | Đúng 10 seeds/profile, giữ PG zeros, mean khớp summary trong tolerance 1e−12; không p-value/CI hay chọn seeds, không gọi time-DiD. |
| CPU-C: phiếu quyết định calibration/mastery | Từ protocol và interface contracts hiện có; bảng correctness probability/native mastery/reference mastery, calibration population, oracle boundary, threshold/numerical convention và required artifacts. | Không đồng nhất p(correct) với latent mastery; mọi lựa chọn cần S04/S05 có owner/pending; không thay threshold/code/checkpoint hoặc fit calibrator. |
| CPU-D: bảng feasibility/exposure graph controls | Chỉ dùng controls/common-population JSON đã lưu; bảng fixed/common denominators, changed-parent opportunities, changed-prior learners, attrition và giới hạn bins/swaps. | Giữ đủ seeds 0/1/2; raw/corrected tách; common-subset target khác được ghi; proposed exposure floor/perturbation rule là draft, không sinh controls hay tự chọn floor theo correctness. |
| CPU-E: checklist preregistration RQ1/RQ2 | Reconcile E01–E06/E10, ledger và tổng hợp này; output claim–required comparison–inference unit–primary family–artifact–pending decision. | Giữ đủ required baselines/expert+learned/noise types; published/pilot seeds không gọi untouched final; phân biệt approval methodology và authorization execution. Không sửa TASKS/state hoặc coi checklist là duyệt S04/S05. |

## Tệp đã đọc, kiểm chứng và giới hạn của lượt này

Danh sách máy đọc đầy đủ tại `input_inventory` trong [JSON tổng hợp](rq12_evidence_synthesis_20261107.json), mỗi đường dẫn có SHA và read mode. Các nhóm chính:

1. `AGENTS.md`, `docs/REPOSITORY_MAP.md`; bốn reports CPU được liên kết ở đầu; `research_tracking/CLAIM_EVIDENCE_MATRIX.md`, `research_tracking/EVIDENCE_INDEX.md`.
2. `docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md`, `04_PAPER1_PAPER2_DIAGNOSTIC_PLAN.md`, `05_EXPERIMENT_MATRIX.md`; targeted text search trong `19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md` để kiểm pending calibration/graph boundaries. Một lượt tìm từ khóa toàn `docs/thesis_recovery/*.md` chỉ dùng để tìm đúng mục trap; các hits ngoài bốn docs này không làm căn cứ claim mới.
3. `runs/cpu-rq12-20261107-03/`: `manifest.json`, `README.md`, `comparisons.json`, `retention.json`, `paper1_counterexample.json`, `matched_graph.json`, `source_provenance.json`.
4. `runs/cpu-closedloop-20261107-01/`: `manifest.json`, `README.md`, `closed_loop_outcomes.json`. Thử đọc `summary.json` không tồn tại; manifest chỉ đúng file outcomes, dùng file này để tổng hợp.
5. `runs/cpu-factorial-20261107-01/`: `manifest.json`, `README.md`, `contrasts.json`, `summary.json`; `reports/cpu_pilot_followup_20261107.json` cung cấp mechanism coverage/initial minimum ability.
6. `runs/cpu-junyi-order-20261107-01/`: `manifest.json`, `README.md`, `order_summary.json`, `catalog_audit.json`; `runs/cpu-junyi-graph-reconstruction-20261107-01/manifest.json`, `graph.json`.
7. `runs/cpu-junyi-controls-20261107-02-expanded/`: `manifest.json`, `README.md`, `order_summary.json`, `matched_controls.json`, `corrected_graph.json`; `reports/cpu_matched_control_coverage_20261107.json` cho cohort 32 learners trước.
8. `runs/cpu-junyi-common-20261107-01/`: `manifest.json`, `README.md`, `common_population.json`.

Các đường dẫn ở mục 3–8 tương đối với `research_tracking/`. Không mở traces gzip, prediction shards, raw learner IDs, raw canonical logs hoặc dữ liệu vùng bảo vệ. Source notebook/hash ở đây được **trích từ provenance đã lưu**, không thực thi lại Paper1/2 và không tự xác nhận source hiện hành trùng historical runtime. Không chạy regression/model tests vì chỉ thêm tài liệu và arithmetic synthesis; kiểm phù hợp là JSON parse, arithmetic assertions, hash/đường dẫn trích dẫn. Index/archive/commit do lượt review tích hợp xử lý riêng; bundle/manifests cũ giữ nguyên.
