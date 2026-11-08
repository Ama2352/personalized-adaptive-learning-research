# RQ2 diagnostic: retention tuyến tính và mastery readouts không cùng mức dư thừa

**Một counterexample trên trạng thái được dựng, không trajectory/policy experiment.** Dưới cùng homogeneous decay/no practice sau T, retained **net mean theta gain** vẫn là final gain nhân cùng hệ số như C08; nhưng **native soft-mastery gain có thể đảo thứ tự giữa hai trạng thái**. Hard mastery là threshold readout khác nữa: fixture này hòa ở T rồi phân biệt sau14ngày, **không** cho strict hard-order reversal.

[C08 gốc](../runs/cpu-rq12-20261107-03/retention.json) và [bản thảo hiện hành](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) giữ nguyên. Các báo cáo trước đã caveat nonlinear mastery, nhưng năm `retention.json` tìm được chỉ có scalar identity, chưa có fixture soft/hard ordering tương đương. Kết quả mới thu hẹp câu “retention dư thừa” theo đúng metric; không bác bỏ C08 hoặc tạo evidence graph benefit.

## Công thức nguồn và lập luận

Nguồn Paper2: notebook SHA `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f`.

| Readout/dynamics | Source anchor | Hàm đang xét |
|---|---|---|
| Response curve | Cell9 lines1–2, `elo_probability`, SHA `23c2f76a39550fbed2233b9b84fb3fde0049ce0ba012bd9ddddc79b81e509cf0` | `f(theta)=1/(1+10^((1250−theta)/400))` |
| Forgetting | Cell9 lines30–36, `theta_at`, SHA `52f6af6a08121c11e176bdb501bf648fc3342314176ebbf9af1957892d9e259f` | Decay nonnegative gain quanh fixed base, rate0,06/ngày |
| Native soft mastery | Cell19 lines16–17, SHA `1a195fbbcf2e28d5d1c9bd9877407798191507df6a2b8bd3f243c3108800ea0b` | Mean `elo_probability(theta,MASTERY_ELO)` trên snapshot |
| Native hard mastery | Cell19 lines83–84 | Mean indicator `theta≥1250` ở final/retention snapshots |
| Reported gains | Cell19 lines99–108 | Readout tạiT hoặcT+14 trừ initial readout; net mean-theta gain là endpoint riêng |

Với `theta_i(T)=b_i+g_i`, `g_i≥0`, và không practice sau T, đặt `c=exp(−0,06×14)=0,43171052342907973`. Khi snapshot gain tuân source decay, `theta_i(T+14)=b_i+c*g_i`; vì vậy `mean(g14)=c*mean(gT)`. C08 đã chứng minh identity đó. Nó không yêu cầu mọi concept được practice cùng lúc; đây là semigroup decay của gain từ snapshotT, không khẳng định lịch sử tạo snapshot.

Native soft gain lại là `DeltaS(c)=mean[f(b_i+c*g_i)−f(b_i)]`, không có identity chung `DeltaS(c)=c*DeltaS(1)`. Đặt `k=ln(10)/400`, ta có `f''(theta)=k²*f*(1−f)*(1−2f)`: độ cong khác theo vị trí quanh1250, nên giảm gain cùng một tỷ lệ vẫn có thể đổi đóng góp tương đối giữa concepts. Hard gain là `mean[1{b_i+c*g_i≥1250}−1{b_i≥1250}]`, hàm bậc thang, không linear readout.

Đây là native **true-state readouts**, không estimator mastery, calibrated P(K), reference-bank score hoặc ngưỡng0,563715 của ProtocolV1.

## Fixed fixture và số thực tế

Hai trạng thái dùng **cùng28base**: `(850,1200,1000,…,1000)`;26concept cuối không gain. A có gains `(0,250,0,…,0)`, B có `(450,0,0,…,0)`. Mọi gain không âm, mọi thetaT≤1600; retained states cũng nằm giữa base và1600. Đây là **constructed readout-domain states**, chưa chứng minh reachable từ persona initialization, graph, lịch sử practice hoặc policy nào. A/B không là tên model/treatment/persona.

| Metric, đơn vị | A tạiT | B tạiT | A tạiT+14 | B tạiT+14 | Thứ tự |
|---|---:|---:|---:|---:|---|
| Net mean theta gain, Elo points/concept |8,9285714286 |16,0714285714 |3,8545582449 |6,9382048408 |B>A cả hai thời điểm |
| Native soft-mastery gain, tỷ lệ |0,0118289301 |0,0171626438 |0,0055022750 |0,0051205241 |**B>A → A>B** |
| Native hard-mastery count /28 |1/28 |1/28 |1/28 |0/28 |Hòa → A>B; không strict reversal |

Soft-gain difference `A−B` xấp xỉ **−0,00533371365868** tạiT và **+0,000381750955297** sau14ngày. Mỗi trạng thái riêng đều giảm soft mastery khi forgetting; reversal không có nghĩa A học thêm trong14ngày không practice. Vì cùng base, ranking soft level và soft gain đều đảo. Raw values/states đầy đủ28chiều được lưu, không chọn subset thuận lợi.

Net-theta identity residual sau tính float nhỏ hơn1e−12 ở cả hai cases. Negative controls: zero-gain state có mọi gain readout bằng0; identical states cho identical readouts; `f(1250)=0,5`. Không tìm kiếm/tune vectors hoặc thêm cases sau khi thấy số. Hard outcome báo đúng actual tie→strict ordering, không ép thành hard reversal.

## Điều có thể kết luận

| Metric pair | Kết luận trong điều kiện đang xét | Không được suy |
|---|---|---|
| Final / retained net mean-theta gain |Common positive scalar transform; cùng ranking, C08 giữ nguyên |Practice order trướcT vô nghĩa; mọi retention metric đều dư thừa |
| Final / retained native soft-mastery gain |Không có guarantee cùng ranking; fixed counterexample đã đảo dấu |Hai endpoints độc lập thống kê, policy tạo được states đó, graph cải thiện retention |
| Final / retained native hard mastery |Threshold crossings có thể đổi distinction giữa states; fixture hòa rồi khác |Strict hard reversal đã xảy ra trong fixture này |

Vì vậy không nên loại `retention_soft_mastery_gain` chỉ vì `retention_theta_gain` proportional. Nếu đánh giá thêm cả hai trong future trajectories, vẫn phải freeze metric family/estimand/multiple-comparison handling; counterexample này không bổ sung p-value/CI hoặc xác nhận hiệu quả giáo dục. Chưa kiểm heterogeneous forgetting, gross learning gain hoặc dynamics mới, và cũng **không cần** đổi dynamics để có soft-ranking reversal ở mức readout.

## Thực thi và provenance

Một stdlib-only arithmetic dispatch, controller **0,1298041s≤10s**, exit0. Pinned source được đọc/AST-hash nhưng **không exec native functions/classes**; dùng Python arithmetic/math.fsum cho cùng công thức, không tuyên bố bitwise NumPy execution. Không teacher `interact`, learner trajectories, model, RNG, Junyi, data replay, tests rộng hoặc cloud/spend. Source/input SHA trước=sau; C08 SHA `bd952fb707f04712508aa50def877d21da9ff71b1b0a5e9c74b4692d10645b54` không đổi.

[Bundle](../runs/rq2-retention-readout-separation-20261108-01/README.md) giữ predeclared plan/source, raw calculated values, negative controls, static source excerpts, stdout/stderr/receipt, derivation note và copy SHA trước/sau. [Raw readouts](../runs/rq2-retention-readout-separation-20261108-01/readouts.json), [execution receipt](../runs/rq2-retention-readout-separation-20261108-01/run.json). Đây là source-level diagnostic evidence mới cho trap retention, không completeRQ2 hoặc bằng chứng policy outcome/causal mediation.
