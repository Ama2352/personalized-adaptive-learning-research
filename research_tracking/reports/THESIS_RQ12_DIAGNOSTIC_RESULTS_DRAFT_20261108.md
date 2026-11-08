# Kết quả kiểm toán và chẩn đoán pilot cho RQ1–RQ2

Bản thảo tiểu mục luận văn, ngày 08/11/2026. Các kết quả dưới đây tổng hợp bằng chứng đã lưu; không có thí nghiệm, huấn luyện, truy vấn dữ liệu hay suy luận thống kê mới. Mã C01–C12 nối từng nhóm phát biểu với đường dẫn artifact immutable, JSON Pointer, giá trị và SHA-256 trong [hồ sơ nguồn](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json). Đây là kết quả chẩn đoán phục vụ thiết kế nghiên cứu tiếp theo, chưa đánh dấu RQ1 hoặc RQ2 hoàn tất.

## Từ dự báo đến quyết định trong fixed-stream pilot

Một khía cạnh thực hành của RQ1 là: dự báo khác nhau có đi kèm lựa chọn học tập khác nhau hay không? Pilot fixed-stream cho phép quan sát những khác biệt này tại các snapshot trước khi cập nhật đáp án hiện tại. Dữ liệu gồm ba seed blocks 20000–20002, mỗi block có các profile PG, PY, PYH. Mỗi comparison với graph-free có 1.080 event pairs, tương ứng chín quỹ đạo seed–profile và 120 bước mỗi quỹ đạo. Đây không phải 1.080 mẫu độc lập; các bước cùng quỹ đạo và các profile cùng seed có thể phụ thuộc nhau. Phần này chỉ mô tả dữ liệu đã lưu, không báo p-value, CI hoặc kiểm định hiệu quả. [C01: phân tích transition](../runs/cpu-rq1-transitions-20261108-01/analysis.json).

Cần phân biệt năm đại lượng. P là scalar p(correct) cho câu hỏi đang được ghi trong log; S là vector `mastery_score` của nguồn trên 28 concept; M là tập quyết định boolean `is_mastered`; R là ready set; A là concept action preview. S chưa được xác nhận là xác suất mastery đã hiệu chỉnh. M lấy từ quyết định nguồn, không được thay bằng S hoặc P lớn hơn một ngưỡng tự chọn. A được lấy từ bản sao policy để giữ fixed stream, chưa phải hoạt động thực sự phục vụ người học. Các cờ “đổi” dưới đây so sánh giá trị đã lưu theo quy ước exact của phân tích nguồn. Trace fixed-stream không lưu current item/question/timestamp hoặc question/difficulty của preview. Điều kiện shared stream dựa vào hồ sơ nguồn và matching keys/labels; từ riêng trace chưa kiểm độc lập được toàn bộ query identity. Vì thế A giữ chỉ xác nhận concept preview giữ. [C01–C02: định nghĩa và score vector](../runs/rq1-score-vector-20261108-01/analysis.json).

| Đại lượng, so với graph-free | Full graph package | Empty-graph package |
|---|---:|---:|
| Event pairs | 1.080 | 1.080 |
| P đổi | 964 | 37 |
| Ít nhất một phần tử S đổi | 1.080 | 267 |
| Concept-score pairs đổi | 27.017/30.240 | 454/30.240 |
| M đổi ở ít nhất một concept | 90 | 0 |
| R đổi | 60 | 0 |
| A concept preview đổi | 22 | 0 |
| S đổi nhưng A giữ | 1.058 | 267 |

Bảng trên cho thấy thay đổi số không truyền một-một thành thay đổi quyết định. Tuy nhiên, các tổng không tạo thành funnel nhân quả. M event là “có ít nhất một concept đổi”, còn 30.240 là mẫu số concept × event. Trong dữ liệu này, số M events và số concept mastery crossings cùng bằng 90 vì mỗi snapshot liên quan chỉ đổi một concept; hai đại lượng được đếm riêng, không phải quy tắc có thể áp dụng cho mọi dữ liệu, càng không phải 90 người học mới đạt mastery. [C01–C02].

Bảng có điều kiện tại cùng snapshot làm rõ hơn mối liên hệ này. Mỗi mẫu số là số event pairs thỏa điều kiện ở cột đầu, không phải mẫu số của bảng trước được dùng lại tùy ý.

| Điều kiện, full package | Kết quả trong cùng snapshot | Số đếm/mẫu số |
|---|---|---:|
| P đổi | M đổi | 81/964 |
| P đổi | A giữ | 944/964 |
| P giữ | A đổi | 2/116 |
| M đổi | R đổi | 60/90 |
| R đổi | A đổi | 5/60 |
| R giữ | A đổi | 17/1.020 |

Các tỷ lệ này là đồng biến có điều kiện, không phải xác suất của các bước trung gian trong một mediation model. P giữ/A đổi không chứng minh vi phạm nhân quả hoặc lỗi đường đi ẩn: P chỉ mô tả current logged query, trong khi policy có thể dùng trạng thái rộng hơn. Tương tự, ready membership giữ nhưng A đổi phù hợp với khả năng scores/ranking khác nhau; dữ liệu chưa cô lập pathway gây khác bằng intervention. [C03: các conditional cells](../runs/cpu-rq1-transitions-20261108-01/analysis.json).

Hai trường hợp giúp diễn giải bảng. Ở `20000-PG/event0`, P thay từ 0,5 thành 0,4941767101, nhưng M/R giữ và cả hai nhánh preview `BatPhuongTrinhBacHaiMotAn`. Ở `20001-PG/event11`, M/R vẫn giữ nhưng concept preview chuyển từ `PhuongTrinhQuyVePhuongTrinhBacHai` sang `HamSoBacHaiVaDoThi`. Ngoài ra, cả hai event P giữ/A đổi đều có 25 phần tử S đổi. Vì vậy không thể xem chúng như hai trạng thái policy hoàn toàn giống nhau rồi cho ra quyết định khác. Các ví dụ là trường hợp truy vết đã lưu, không được chọn lại để tối đa hóa effect. [C04: examples và vector diagnostic](../runs/rq1-score-vector-20261108-01/analysis.json).

Empty-graph package là negative control quan trọng: vẫn có 37 P changes và 267 S changes nhưng không có M/R/A changes. Package còn pathway cục bộ ngay khi không có cạnh; empty-graph package vì thế không tương đương graph-free. Full-package contrast chưa cô lập đóng góp của prerequisite edges, và zero action change của control không chứng minh equivalence của graph ngoài pilot này. [C02].

## Bổ sung C13: query và full preview được quan sát trong reproduction mới

Bằng chứng mới bổ sung một giới hạn quan sát của C01–C04, trong khi các phát biểu về trace lịch sử ở trên vẫn giữ nguyên. Cùng pilot ba seed families 20000–20002 và các profile PG/PY/PYH đã được tái lập với observer. Control và observed mỗi pass giữ exact 3.240 legacy rows và 18 comparisons so với historical values. Trong pass observed, query arguments được ghi trước native `predict`, còn full preview là chính tuple **(concept, question, difficulty)** do native `select` trả trên policy copy. Tại **1.080 logical keys**, cả ba variants có cùng actual query tuple và label. [C13: reproduction đã đóng](../runs/rq1-query-observability-reproduction-20261108-01/parity.json), [báo cáo nguồn](rq1_query_observability_reproduction_20261108.md).

| So với graph-free, reproduction mới | Full graph package | Empty-graph package |
|---|---:|---:|
| Full preview tuple đổi / event pairs | 22/1.080 | 0/1.080 |
| P đổi nhưng toàn preview tuple giữ / P đổi | 944/964 | 37/37 |
| P giữ nhưng full preview tuple đổi / P giữ | 2/116 | 0/1.043 |
| Concept giữ nhưng full tuple đổi | 0/1.080 | 0/1.080 |
| Difficulty đổi | 0/1.080 | 0/1.080 |

Trong reproduction này, 22 full-tuple changes cũng là 22 concept/question changes; không phát hiện thêm item differences khi concept giữ. Vì vậy có thể nâng phát biểu “P đổi nhưng concept preview giữ” thành **“944/964 P changes vẫn giữ toàn bộ returned preview tuple” cho reproduction này**. Hai P-same/full-preview-changed rows vẫn tồn tại. P là một scalar của current query, không toàn bộ state/ranking mà selector sử dụng; chúng không tự chứng minh lỗi, causal mediation hoặc learning benefit. Empty package còn local pathway, nên 37 P changes/0 full-preview changes không phải isolated edge effect hay equivalence proof. [C13: counts trực tiếp](../runs/rq1-query-observability-reproduction-20261108-01/attempt01__sidecar_analysis.json).

Cross-profile query tuples cũng trùng **360/360** trong từng cặp PG–PY, PG–PYH và PY–PYH. Labels/histories và initialization vẫn có thể khác. Đây là ba seed families đã dùng, **new independent N = 0**, không phải chín independent replicates hoặc causal ability intervention. New metadata chỉ thuộc reproduction; không backfill các trường chưa log trong historical trace. `preview_is_served=false`; selector không nhận timestamp nên không gán query time thành preview time. Kết quả này khép phần diagnostic về **actual shared query và returned full preview** của cùng fixed-stream pilot, còn closed-loop mastered/ready/served-item chain, reference calibration/mastery và interventions cô lập pathway vẫn chưa được xác minh đầy đủ. [C13: phạm vi và acceptance](../runs/rq1-query-observability-reproduction-20261108-01/frozen_acceptance.json).

## Predictive loss, profile và ranh giới của closed loop

Số lần dự báo thay đổi không cho biết dự báo tốt hơn. Reanalysis đã tính Log Loss/Brier trên cùng paired labels và đối chiếu với aggregates cũ. Full package có pooled ΔLog Loss −0,000694 và ΔBrier −0,000365 so với graph-free, nhưng kết quả theo profile khác nhau. Bảng dùng trung bình ba seed cùng kích thước; mỗi profile có 360 event pairs. [C05: các seed–profile rows và phép trung bình được khai báo trong hồ sơ nguồn](../runs/rq1-score-vector-20261108-01/analysis.json).

| Profile | ΔLog Loss | ΔBrier | M events đổi | A previews đổi |
|---|---:|---:|---:|---:|
| PG | +0,002558 | +0,001165 | 86 | 20 |
| PY | −0,002998 | −0,001450 | 0 | 2 |
| PYH | −0,001641 | −0,000809 | 4 | 0 |

PG có loss xấu hơn ở cả ba seed–profile rows, dù chiếm 20/22 preview changes. Do đó không thể kết luận graph package cải thiện mọi profile hoặc nhiều quyết định đổi hơn là tốt hơn. Với seed block 20000, S đổi ở toàn bộ 360 event pairs nhưng M/R/A đều không đổi. Những quan sát này hỗ trợ chẩn đoán prediction–decision mismatch; chúng chưa đo calibration của S quanh một reference mastery hợp lệ, cũng chưa xác định ảnh hưởng nhân quả của ability. [C05].

Closed-loop pilot cung cấp evidence khác: full package có served-concept disagreements lần lượt 208/360, 200/360 và 72/360 ở PG, PY, PYH; empty package có 0/360, 2/360 và 2/360. Mẫu số là các timestep được ghép trong ba seed pairs/profile. Khi policy đã chọn items khác nhau, histories và labels có thể khác; đây không còn là phép so paired prediction trên cùng target. Closed trace thiếu explicit mastered decisions và ready set, nên chưa thể nối đủ P/S/M/R/A cho served actions. Không lấy oracle diagnostics lấp vào trường thiếu, hoặc chia action disagreements của closed loop cho 22 preview changes để suy “khuếch đại”. [C06: action audit và missing fields](../runs/cpu-rq1-transitions-20261108-01/analysis.json).

## Bổ sung C14: native concept ranking và thứ tự closed-loop — post-hoc

Một current-source reconstruction mới bổ sung explicit M/R/candidates và served-item metadata cho cùng closed-loop pilot; không điền ngược các trường thiếu của trace lịch sử nêu ở C06. Candidate runner `d8892fc3…` giữ exact stored legacy projection trong hai passes, nhưng nguyên runner lịch sử `a585d5f3…` vẫn chưa tìm được. Archive đã đóng và commit `850f5ab`; phần dưới là **giải thích source-local, khám phá post-hoc**, được kiểm độc lập trên raw, không phải effect đã preregister hoặc hoàn tất RQ1. [C14: archive/source binding](../runs/rq1-closed-loop-reconstruction-20261108-02/manifest.json).

Native selector lấy concept có key nhỏ nhất trên balanced candidates B: `(mastery_score(c), chapter tie, prior selection_count[c], lexical cid)`. Tất cả B-score calls vốn có đã được ghi đầy đủ, một lần/concept theo đúng B order. Visits được dựng từ toàn bộ prior served concepts; previous chapter lấy từ source map và selector bookkeeping. Exact Python min khớp native selected concept ở **3.240/3.240events**, không missing/unsupported capture. Trên các common-before snapshots, toàn bộ lịch sử served tuple, timestamp và y trước đó còn giống nhau, nên visits/chapter tie context cũng giống. [C14: key replay và giới hạn](../runs/rq1-closed-loop-reconstruction-20261108-02/posthoc__ranking_candidate.json), [independent raw/key review](../runs/rq1-closed-loop-reconstruction-20261108-02/prep__parent-ranking-review.json).

| Candidate, so với graph-free | First tuple break cùng M/R/C/B và khác B-score key | Membership đổi | Không tuple break trong120steps |
|---|---:|---:|---:|
| Full graph package | 8/9 comparisons | 1/9 | 0/9 |
| Empty-estimator package | 2/9 comparisons | 0/9 | 7/9 |

Mẫu số9 là ba seed families × ba profiles, không9independent seeds; giữ đủ18comparisons kể cả negatives. Ở8full và2empty breaks cùng membership/tie context, logged B-score vectors khác nhau tái hiện đúng hai selected concepts khác nhau. Case full còn lại có membership đổi, được giữ riêng và không gọi score-only. Điều này giải thích **CID component** của quyết định nguồn; không replay `choose_question` hoặc quy toàn bộ question/difficulty rule cho B-score. Full S28 không cần cho ranking cục bộ trên B đã log đủ, trong khi reference mastery/calibration và global S vẫn là câu hỏi khác. Empty estimator vẫn dùng controller G và environment G chung; package/local pathway còn hoạt động, nên contrast này không cô lập prerequisite-edge effect.

Thứ tự native code cũng giới hạn cách nối các đại lượng: **select bằng B-score key → predict P cho served query sau selector bookkeeping → environment.interact → update(y,P)**. P của item vừa được phục vụ không là đầu vào gây ra chính same-step selection đã chọn item đó; P đi vào update và state tương lai. Vì vậy linear within-step `P→M→R→A` không diễn đạt đúng closed-loop này. B-score trong selector, reference probe/global S và served-item P cần được phân biệt khi chốt S04; thứ tự gọi predict trước preview trong fixed stream ở C01–C13 cũng không tự xác lập causal mediation. [C14: immutable source excerpts](../runs/rq1-closed-loop-reconstruction-20261108-02/prep__closed_loop_native_source_snapshot.json), [closed-loop call order](../runs/rq1-closed-loop-reconstruction-20261108-02/current_candidate_runner.py).

Sau prefix divergence, histories/items/labels có thể khác, nên không ghép ΔP/loss/current-query crossings theo cùng ordinal event để suy cơ chế hoặc lợi ích. Các kết quả này không thêm seed family độc lập (**new independent N=0**), không CI/p-value, calibrated mastery, causal learning benefit hoặc edge-only conclusion. Scientific S04/S05 và independent evaluation vẫn cần evidence riêng; closure chỉ giữ integrity và review scope đã ghi. [C14: closure không methodology adoption](../runs/rq1-closed-loop-reconstruction-20261108-02/closure_review.json).

## Ba bẫy khi diễn giải điều kiện hiệu quả

### Bẫy 1: tính liên tục chương và retention có thể phản ánh cấu trúc nguồn

Counterexample đã lưu chạy selector của revision Paper1 hiện có trên synthetic DAG với mastery transitions được gán theo kịch bản. Cả `lowest_elo` và `cross_chapter_unlock` đều tạo A1→B1→A2, tương ứng chương A→B→A và một lần re-entry. Nó bác bỏ mệnh đề “selector của revision này bảo đảm không quay lại chương trên mọi graph”, nhưng không tái lập bảng kết quả của PDF. Audit revision vẫn chưa tìm được bộ source, inputs và outputs khớp submission; không được biến khác biệt này thành kết luận PDF sai. [C07: counterexample](../runs/cpu-rq12-20261107-03/paper1_counterexample.json), [audit revision](../runs/paper1-revision-audit-20261107-01/paper1_revision_reconciliation_20261107.json).

Retention cũng cần đọc theo định nghĩa. Với decay đồng nhất, không practice sau T, gain đo quanh cùng fixed base và gain không âm trong fixture, nguồn cho hệ số exp(−0,06 × 14) = 0,4317105234; absolute error được lưu là 1,7053×10⁻¹³. Trong các điều kiện đó, retained net theta gain là final net theta gain nhân cùng hệ số, nên không cung cấp ranking độc lập với final gain. Đây là hệ quả của dynamics/metric đang xét, không tự là bug. Nó không nói practice order trước T không quan trọng, hoặc mọi retention metric, nonlinear mastery hay heterogeneous forgetting đều bất biến. [C08: retention fixture và scope](../runs/cpu-rq12-20261107-03/retention.json).

### Bẫy 2: tương tác λ×edge chưa phải hiệu ứng nhân quả của ability

Factorial pilot giữ bốn cells trên mỗi seed/profile và định nghĩa:

`I(s,p) = [(edge-on − edge-off) tại λ=0,55] − [(edge-on − edge-off) tại λ=0]`.

Outcome là net mean theta gain trên 28 concept. Edge treatment bật parent signal và parent adaptation cùng nhau; local pathway tắt ở cả hai nhánh. Có 10 seed blocks 21000–21009; 30 profile–seed rows không phải 30 blocks độc lập. Đây là contrast tương tác có điều kiện trong simulator đã chỉ định, không tự là time-DiD với nhóm ability cao/thấp làm treated/control. Các profiles không phải can thiệp chỉ thay ability và nguồn initialization vẫn có graph correlation. [C09: factorial estimand và README nguồn](../runs/rq2-conditions-evidence-20261108-01/conditions.json).

| Profile | Mechanism-exposed events của followup | Mean edge effect λ=0,55 | Mean edge effect λ=0 | Mean I |
|---|---:|---:|---:|---:|
| PG | 0/2.400 | +0,110853316 | +0,110853316 | 0 |
| PY | 1.919/2.400 | +0,051485897 | +0,017468639 | +0,034017258 |
| PYH | 1.197/2.400 | +0,378081797 | +0,324553209 | +0,053528587 |

PG có I bằng zero ở cả mười seeds và không có measured mechanism exposure trong followup, nhưng hai edge-effect components khác zero. Do đó đây là bằng chứng cơ chế ít được nhận diện trong điều kiện pilot, không phải chứng minh graph vô ích hoặc tương đương. Mẫu số 2.400 là pooled diagnostic events, không phải learners độc lập; aggregates exposure cũng chưa ghép được với effect theo seed/cell để suy dose–response. [C09].

Mean I(PYH)−I(PY) bằng +0,019511329 nhưng leave-one-seed-out means nằm từ −0,018702521 đến +0,043941085. Thứ tự hai sample means vì thế không giữ dấu dưới mọi one-seed deletion. Đây là sensitivity đã lưu, không phải CI; không loại seed bất lợi hoặc coi LOO là kiểm định heterogeneity cuối. [C10: paired profile contrast](../runs/rq2-conditions-evidence-20261108-01/conditions.json).

### Bẫy 3: graph khớp logged order chưa chứng minh lợi ích sequencing

Các aggregates Junyi đã lưu dùng cohort 256 inner-train learners, tối đa 300 events/learner, tổng 12.575 events; bản thảo này không đọc lại interactions hoặc correctness. Corrected graph có 976 edges, với 575 parent-first/649 co-observed edge–learner pairs. Raw reference có 979 edges và 576/650 pairs; không trộn raw denominator vào contrast với corrected controls. Mỗi control thay 20 edges bằng 20 edges, giữ degree và strata constraints của pilot; symmetric difference có 40 entries. Tuy nhiên chỉ 2, 10 và 6 changed entries thực sự co-observed trong cùng learner ở controls 0, 1, 2. Số lần swap đủ theo kế hoạch không đồng nghĩa exposure đủ mạnh. [C11: order, controls và decomposition](../runs/rq2-conditions-evidence-20261108-01/conditions.json).

Sensitivity trên cùng observed learner–child opportunities cho mỗi child dùng incoming degree làm mẫu số, trung bình qua child rồi cho mỗi eligible learner trọng số bằng nhau. Nó giữ 239/256 learners và 1.361 opportunities. Base prior fraction bằng 0,165861732; unobserved-parent fraction bằng 0,820852360 là trung bình phân cấp trong prefix, không phải 82% prerequisite của toàn bộ Junyi sai hoặc chưa mastery. [C12: common-population sensitivity](../runs/rq2-conditions-evidence-20261108-01/conditions.json).

| Control | Opportunities đổi parent set/1.361 | Learners đổi prior/239 | Δprior all-fixed | Common opportunities | Common learners | Δprior common subset |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 43 | 1 | +0,000697350 | 569 | 96 | 0 |
| 1 | 42 | 7 | −0,001179045 | 564 | 96 | −0,003082618 |
| 2 | 12 | 1 | −0,000836820 | 566 | 95 | 0 |

Control2 minh họa rõ denominator sensitivity: parent-first count giảm từ 575 xuống 574, nhưng denominator giảm từ 649 xuống 645 nên pooled alignment tăng. Cùng control này, all-fixed learner-weighted contrast âm còn common-subset contrast bằng zero. Ba kết quả nhắm các estimands/quần thể khác nhau, không mâu thuẫn số học. Common subset giữ learner–child opportunities có ít nhất một parent co-observed trong mỗi graph của cặp so sánh; không đòi hỏi cùng một parent xuất hiện ở cả hai graph. Các subsets chỉ giữ khoảng 41–42% opportunities và khác nhau giữa comparisons; không pool chúng thành cùng target population. Order summary dùng first exposure theo `(timestamp,source_row)`, còn common estimator tách timestamp ties và missing parent riêng. Không coi thiếu quan sát là prerequisite sai. [C11–C12].

## Phạm vi kết luận và bằng chứng còn thiếu

Các kiểm toán đã chỉ ra ba điều có thể kết luận trong phạm vi nguồn: khác biệt prediction/score không bảo đảm khác biệt decision preview; một số retention/continuity claims phụ thuộc dynamics và revision; order-control contrast có thể rất nhạy với exposure, trọng số và quần thể. Counterexample có thể phủ định một bảo đảm phổ quát của selector hiện có; retention identity là kết quả toán học có điều kiện. Ngược lại, P giữ/A đổi hay dấu contrast đổi giữa estimands chưa phải bằng chứng lỗi phần mềm. SHA bảo vệ identity của evidence, không tự xác nhận validity khoa học.

Để đóng các giả thuyết RQ1/RQ2, nghiên cứu còn cần reference/mastery/calibration contract được chốt; trace đầy đủ current query, full policy state, mastered/ready và served action; các interventions đủ cô lập cạnh, local pathway và controller; phân biệt ability intervention với profile tổng hợp; estimand, coverage/perturbation rule và inference unit được quyết định trước phép so xác nhận. Source revision Paper1 cần được xác nhận hoặc ghi rõ phần chưa tái lập; graph version và quần thể Junyi cần khóa cùng controls có exposure phù hợp. Final independent evaluation phải giữ required comparators và không dùng pilot seeds để chọn một kết luận thuận lợi. Cho đến khi có các evidence này, kết quả trình bày ở đây hỗ trợ chẩn đoán và thiết kế, chưa chứng minh graph cải thiện học tập hoặc xác định đầy đủ điều kiện hiệu quả ngoài simulator.
