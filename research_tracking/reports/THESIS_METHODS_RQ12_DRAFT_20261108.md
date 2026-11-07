# Bản thảo phương pháp và giới hạn của RQ1/RQ2

Ngày đối chiếu: 08/11/2026. Tài liệu phục vụ biên tập chương phương pháp và thảo luận của khóa luận; nội dung dưới đây mô tả các phân tích chẩn đoán đã có, phân biệt với thiết kế xác nhận còn cần thống nhất. **Chưa kết luận RQ1/RQ2 hoàn tất và không phê duyệt phương pháp, cấu hình hoặc thí nghiệm mới.** Những ghi chú quản lý tài liệu ở mục 7 có thể bỏ khi đưa phần học thuật vào luận văn.

## 1. Phạm vi và cấu trúc câu hỏi nghiên cứu

Khóa luận xem xét hệ thống học tập thích ứng qua ba thành phần liên kết: mô hình ước lượng trạng thái người học, biểu diễn quan hệ tiên quyết và chính sách lựa chọn hoạt động. Theo đề cương được người dùng xác nhận, RQ1 yêu cầu giải thích vì sao thông tin đồ thị chưa tạo ra cải thiện ổn định về mức độ thành thạo, xét các khả năng liên quan đến chất lượng dự báo, hiệu chỉnh xác suất và chính sách lựa chọn. RQ2 xem xét điều kiện hiệu lực theo chất lượng đồ thị, lịch sử tương tác và đặc điểm người học. Cơ chế tích hợp đồ thị theo độ tin cậy trên nền KT hiện đại thuộc RQ3, vượt ngoài phần bằng chứng được tổng hợp ở đây. [S01, trang 2–4; S02]

Hai nguồn thực nghiệm chính được giữ theo đề cương là Junyi Academy và bộ mô phỏng Toán lớp 10 gồm 28 khái niệm, ngân hàng bài tập và ba hồ sơ người học. Hai nguồn này có vai trò khác nhau. Bộ mô phỏng cho phép quan sát biến ẩn và khảo sát cơ chế trong phạm vi dynamics đã định nghĩa; dữ liệu Junyi ghi nhận hành vi dưới chính sách thu thập đã diễn ra. Phù hợp thứ tự trong logs không tự xác lập quan hệ tiên quyết nhân quả hoặc lợi ích giáo dục. Khóa luận không khẳng định hiệu quả trên người học thật khi chưa có thí nghiệm phù hợp. [S01, trang 3–4]

Phạm vi mô hình của đề cương vẫn gồm AKT, SAKT, GKT, GAM-KT, Graph-GAM-KT và BKT tham chiếu. Các chẩn đoán hiện tại sử dụng nguồn lịch sử của Paper1/Paper2; chúng không thay thế đánh giá các mô hình hiện đại hoặc so sánh CG-AKT. Số hiệu RQ trong Paper2 là cách tổ chức riêng của bài báo, không được đồng nhất với số hiệu RQ1/RQ2/RQ3 của khóa luận. Ví dụ, phân tích Junyi gate trong Paper2 có liên hệ với chẩn đoán điều kiện sử dụng đồ thị, nhưng không phải kết luận đầy đủ cho RQ2 của đề cương. [S01; S03; S04]

## 2. Nguyên tắc thông tin và phân loại bằng chứng

### 2.1. Dự báo trước cập nhật

Tại sự kiện thứ t, ký hiệu H(t−1) là lịch sử đã quan sát, q(t) là bài hiện tại và y(t) là đáp án. Xác suất dự báo được xác định từ H(t−1) và q(t); y(t) chỉ được sử dụng sau bước dự báo để cập nhật trạng thái. Cùng nguyên tắc đó, snapshot quyết định phải được lấy trước cập nhật bằng đáp án hiện tại. Khi đối chiếu mô hình, cần giữ danh tính người học, sự kiện, bài hỏi và thứ tự thời gian phù hợp với loại phép so đang thực hiện. [S01, trang 3; S03, phần Online ordering; S05]

Xác suất trả lời đúng một bài không mặc nhiên là xác suất đã nắm một khái niệm. Trong phân tích RQ1 hiện có, quyết định thành thạo lấy trực tiếp từ trường boolean native đã lưu, không áp một ngưỡng mới lên p(correct). Với AKT hoặc các mô hình hiện đại, ngân hàng bài tham chiếu, trọng số tổng hợp, calibrator và ngưỡng thành thạo vẫn cần thống nhất trong quyết định S04. Trạng thái thật của simulator được phép dùng để audit hoặc làm reference theo thiết kế được duyệt; không đưa biến oracle vào đầu vào của chính sách như thể quan sát được khi triển khai. [S03, phần Selector interpretation; S05; S10, S04]

### 2.2. Fixed stream và vòng kín

Phân tích trên luồng cố định giữ các sự kiện được nguồn khai báo dùng chung và đối chiếu dự báo, trạng thái cùng thời điểm. Action preview được lấy bằng bản sao của chính sách nhằm quan sát lựa chọn tiềm năng mà không làm đổi luồng. Ngược lại, trong vòng kín, hoạt động thực sự được chọn có thể khác giữa các cấu hình; lịch sử, bài hỏi và đáp án về sau cũng có thể khác. Do đó, hai chế độ trả lời hai câu hỏi khác nhau: khác biệt trên cùng luồng và kết quả khi thay estimator trong một hệ điều khiển cụ thể. Không dùng xác suất từ các bài đã khác nhau trong vòng kín như paired predictions trên cùng target. [S03, phần Selector interpretation; S05; S09]

Graph-free trong chẩn đoán Paper2 là estimator không dùng graph package; environment và controller vẫn giữ đồ thị lịch sử. Full package đồng thời thay parent signal và adaptation. Empty-graph package còn có local adaptation. Bởi vậy, so full package với graph-free là phép so giữa các package trong một hệ có sử dụng đồ thị, chưa phải can thiệp chỉ thay cạnh hoặc so toàn hệ thống có/không có đồ thị. [S03, phần Prerequisite context; S09]

### 2.3. Phạm vi phân tích lại

Hai phân tích mới ngày 08/11 sử dụng bằng chứng đã lưu. Nhánh RQ1 đọc synthetic traces và aggregates trong các bundle nguồn; nhánh RQ2 chỉ đọc selected aggregates, graph/control summaries và manifests. Bản thảo này tiếp tục dùng các báo cáo và output đã đóng, không chạy lại simulator, train mô hình hoặc truy vấn Junyi interactions/correctness/Holdout. Reanalysis và phép tái lập cùng một JSON không được tính như hai thí nghiệm độc lập. [S05–S08]

## 3. Phương pháp chẩn đoán RQ1: từ dự báo đến quyết định

### 3.1. Đối tượng và đơn vị quan sát

Fixed-stream diagnostic nguồn có 3 seeds 20000–20002, ba profiles PG/PY/PYH và 120 sự kiện trên mỗi trajectory. Mỗi comparison với graph-free có 1.080 paired snapshots, thuộc 9 seed–profile trajectories. Các variants được join theo `(learner_id, event_id)` và kiểm label/concept cùng những trường identity đã lưu. Các trajectory cùng seed có thể phụ thuộc qua cách sinh và RNG; 1.080 snapshots không phải 1.080 người học độc lập. [S05; S06, `fixed_stream`]

Tại mỗi paired snapshot, phân tích xác định bốn cờ:

| Ký hiệu | Định nghĩa trong phân tích đã thực hiện | Giới hạn của đại lượng |
|---|---|---|
| P | Scalar p(correct) của current logged query khác giữa hai variants, theo exact float inequality của comparator nguồn | Không phải toàn vector dự báo 28 khái niệm; không đặt ngưỡng ý nghĩa thực tiễn mới |
| M | Ít nhất một explicit native `is_mastered` decision trong 28 khái niệm khác | Đơn vị event khác với số concept decisions/crossings |
| R | Ready-set membership khác | Không tóm tắt toàn bộ scores hoặc trạng thái xếp hạng của policy |
| A | Concept action preview khác | Không xác nhận question/difficulty hoặc toàn bộ item-level action khác |

Các cờ này phản ánh trạng thái cùng snapshot trước update. M, R và A còn phụ thuộc lịch sử và trạng thái policy, nên bảng conditional không được đọc như can thiệp thay P ngay tại event t rồi đo tác động tức thời lên các tầng còn lại. Fixed trace không lưu current item/question/timestamp, cũng thiếu question/difficulty mà preview selector trả về; do đó không kiểm độc lập đầy đủ query identity chỉ từ trace, dù paired keys/labels khớp và nguồn khai báo shared stream. [S05, mục Dữ liệu và điều kiện join; S06, `definitions`]

### 3.2. Đếm sự kiện và bảng conditional

Với hai cờ X và Z, tỷ lệ mô tả được tính bằng số paired events có X và Z cùng đúng chia số paired events có X đúng. Nếu điều kiện không có event, giá trị tỷ lệ phải để không xác định thay vì gán bằng 0. Toàn bộ cells của bảng đối chiếu được giữ, kể cả cells 0 và các trường hợp không phù hợp một sơ đồ funnel đơn giản. Đây là phân bố đồng thời có điều kiện, không phải tỷ lệ chuyển tiếp thời gian hoặc mediation. [S05; S06]

Full package có 964 snapshots với P khác, 90 events với M khác, 60 ready-set differences và 22 concept-preview differences. Trong cùng dữ liệu có 90 mastery concept crossings trên 30.240 concept decisions (=1.080×28). Số M events và concept crossings cùng bằng 90 vì mỗi event có M khác chỉ đổi một concept trong sample này; không được coi hai cách đếm là đồng nhất trong mọi dữ liệu. [S05; S06]

| Đối chiếu minh họa — full package | Count / mẫu số event | Ý nghĩa được hỗ trợ |
|---|---:|---|
| P khác, A giữ | 944/964 | Thay scalar prediction không bảo đảm concept preview đổi |
| P khác, A khác | 20/964 | Có một phần snapshots đồng thời khác ở cả hai đại lượng |
| P giữ, A khác | 2/116 | Scalar prediction đang hỏi không tóm tắt toàn bộ trạng thái lựa chọn |
| R khác, A khác | 5/60 | Ready-set membership khác không bắt buộc đổi concept được chọn |
| R giữ, A khác | 17/1.020 | Cùng membership vẫn có thể đi cùng khác biệt lựa chọn |

Trong empty-graph control có 37 scalar probability differences nhưng không có M/R/A differences trên fixed stream. Kết quả này giúp phân biệt package difference với edge effect; không xác lập rằng local pathway hoặc mọi cạnh đều trung tính. Các tỷ lệ trên là mô tả hậu kiểm, chưa có p-value, khoảng tin cậy xác nhận hoặc kết luận về learning benefit. [S05; S06]

### 3.3. Đối chiếu với hành động được phục vụ trong vòng kín

Closed-loop source lưu 27 trajectories×120 bước, có actual concept/question/time và outcomes. Full package so graph-free có số served-concept disagreements lần lượt PG 208/360, PY 200/360 và PYH 72/360; 360 là số timestep pairs cho ba seeds trong một profile, không phải số người học độc lập. Source này thiếu explicit mastered/ready fields nên chưa dựng được full P/M/R/A chain; không suy các trường còn thiếu từ theta thật hoặc p_true. [S05; S06, `closed_loop`]

Không chia số served-action differences trong vòng kín cho 22 fixed-stream preview differences để định lượng “khuếch đại”, vì hai chế độ có histories và logging khác nhau. Tương tự, các chênh lệch gain trái dấu giữa profiles trong pilot ba seeds không tự là kiểm định heterogeneity. Phần bằng chứng hiện tại hỗ trợ lập luận rằng predictive change và instructional decision cần được đánh giá riêng; nguyên nhân nhân quả và calibration quanh ngưỡng mastery vẫn chưa được nhận diện đầy đủ. [S04; S05; S09]

## 4. Phương pháp chẩn đoán RQ2: exposure, profile và graph controls

### 4.1. Factorial contrast có điều kiện trong simulator

Factorial pilot nguồn dùng 10 seed blocks 21000–21009, ba profiles và bốn cells theo λ∈{0;0,55} và edge package on/off. Outcome Y là net mean theta gain trên thang Elo, trung bình qua 28 concepts sau 120 bước. Với seed s và profile p, contrast được giữ đúng như nguồn:

```text
E(s,p,λ) = Y(s,p,λ,edge-on) − Y(s,p,λ,edge-off)
I(s,p)   = E(s,p,0,55) − E(s,p,0)
```

Edge treatment bật parent signal và parent adaptation cùng nhau; local pathway tắt ở cả hai nhánh. Trong từng phép so cơ chế, nguồn giữ paired base realization và random uniforms; environment/controller vẫn giữ graph lịch sử và initialization còn có graph correlation. I là chênh lệch graph-package effects giữa hai mức λ trong simulator, không phải raw graph gain, time-DiD hoặc hiệu ứng chỉ của một pathway. [S07; S08, `factorial`; S09]

Điều kiện exposure được đối chiếu bằng tỷ lệ deficit-exposed diagnostic events trong followup: PG 0/2.400, PY 1.919/2.400 và PYH 1.197/2.400. Mẫu số 2.400 là pooled diagnostic events/profile, không phải 2.400 learners độc lập và không được dùng làm n cho CI của seed effects. PG có I=0 trong cả 10 seeds và không có measured prerequisite-deficit exposure; graph-effect components ở λ=0 và λ=0,55 vẫn khác 0. Do đó, kết quả này phù hợp cơ chế chưa được kích hoạt trong điều kiện đo, chưa phải equivalence hoặc bằng chứng đồ thị vô ích. [S07; S08]

### 4.2. So profile và độ nhạy theo seed

Phân tích mới ghép I theo cùng seed identifier, tính chênh lệch giữa hai profiles và mean khi bỏ đúng một seed. Giữ đủ ba profile pairs và đủ 10 leave-one-seed-out means cho mỗi pair, không chọn subset theo hướng kết quả. Đây là descriptive profile-moderation contrast; các profiles khác initialization/dynamics nên không gọi là causal ability effect. [S07; S08, `factorial.paired_profile_contrasts`]

Mean I(PYH)−I(PY) bằng +0,019511329, nhưng có 5 seed dương và 5 seed âm. Mean sau khi bỏ từng seed nằm trong [−0,018702521; +0,043941085]. Vì vậy, thứ tự sample means PYH>PY không giữ dấu dưới mọi one-seed deletion. Khoảng leave-one-seed-out là phép kiểm độ nhạy, không phải khoảng tin cậy; tolerance arithmetic dùng để đếm zero cũng không phải equivalence margin khoa học. Exposure chỉ có pooled summaries, thiếu exposure theo seed/cell để kiểm dose–response hoặc mediation. [S07; S08]

### 4.3. Graph version và mẫu số trên Junyi

Expanded logged-order cohort nguồn gồm 256 inner-train learners thuộc outer-fold0, tối đa 300 events/learner và tổng 12.575 events. Raw catalog graph sau bỏ self-loop có 979 edges; corrected base có 976 edges. Đây là các phiên bản khác nhau, không dùng raw denominator làm base của corrected controls. Reconstruction theo quy tắc nguồn không chứng minh historical graph bytes giống hệt nếu certificate lịch sử chưa đầy đủ. [S07; S09]

Với cạnh e=(u→v), ký hiệu d(e) là số learner prefixes đã quan sát cả u và v, n(e) là số pairs đó có first(u) đứng trước first(v). Supported edge có d(e)>0. Hai estimands order khác nhau được phân biệt:

```text
A_pair = tổng n(e) / tổng d(e)
A_edge = mean qua supported edges của [n(e)/d(e)]
```

A_pair cho trọng số lớn hơn cho cạnh được nhiều learners cùng quan sát; A_edge cho mỗi supported edge trọng số bằng nhau. Với corrected base, hai giá trị lần lượt là 575/649≈0,885978 và 0,805739. Chênh lệch giữa chúng phản ánh đổi estimand, không phải hai estimates cùng quantity đang mâu thuẫn. Order summary so first exposure theo tuple `(timestamp, source_row)`; common-population estimator dùng timestamp và tách ties/missing riêng. Không đồng nhất hai định nghĩa khi gặp cùng timestamp. [S07; S08, `junyi`]

Mỗi matched control giữ 976 edges, shared identities 956, thay 20 edges bằng 20 edges. Tỷ lệ edges gốc bị thay là 20/976≈2,049%, còn symmetric difference có 40 entries vì tính cả removed và added. Các controls giữ in/out-degree và coarse strata đã định nghĩa trong nguồn; điều đó không bảo toàn chính xác co-observation của từng learner và không tạo mẫu đều của toàn bộ DAG null population. [S07; S09]

Same-learner co-observation của changed entries chỉ là 2/40, 10/40 và 6/40 cho ba controls. Các số global endpoint coverage 8/40, 18/40 và 12/40 không được thay cho mẫu số này: hai endpoints xuất hiện ở những learners khác nhau chưa tạo một cơ hội quan sát cạnh trong cùng learner. Exposure thấp làm phép so khó nhận diện khác biệt; kết quả gần 0 không chứng minh graph quality, neutrality hoặc equivalence. [S07; S08, `junyi.controls`]

### 4.4. Quần thể chung và phân rã thay đổi mẫu số

Common-population sensitivity giữ 239 eligible learners với 1.361 observed learner–child opportunities. Tại mỗi child, prior-parent fraction dùng toàn bộ incoming degree làm denominator; sau đó lấy mean qua child trong learner rồi mean với learner weights bằng nhau. Đây là hierarchical mean, khác A_pair và A_edge. Unobserved-parent fraction khoảng 0,820852 trong prefix này không có nghĩa khoảng 82% edges toàn Junyi sai hoặc người học chưa mastery. [S07; S08, `junyi.common_population_sensitivity`]

Control2 minh họa độ nhạy của dấu contrast: parent-first count giảm 575→574, nhưng pair denominator giảm 649→645 nên A_pair tăng khoảng +0,003944052. Trên all-fixed learner-weighted population, prior-fraction contrast lại bằng −0,000836820; trên common supported subset bằng 0. Ba số có estimands/quần thể khác nhau, không được dùng để xếp graph thành tốt/xấu hoặc giải thích như probability-of-benefit. [S07; S08]

Common subsets chỉ giữ khoảng 41,44–41,81% opportunities và khoảng 39,75–40,17% eligible learners; intersections khác nhau theo control. Việc conditioning trên co-observation thay target population, nên không pool ba subsets như một quần thể chung duy nhất. Selected common aggregates không chứa learner-level rows để tính lại bootstrap, learner LOO hoặc precision. Không dựng pseudo-rows từ means và không coi edge–learner pairs là samples độc lập. [S07; S08]

## 5. Đơn vị suy luận, giới hạn đo lường và tái lập

### 5.1. Phụ thuộc và phân tích đã xem kết quả

Đối với RQ1, event-level counts dùng để mô tả snapshots trong các seed–profile trajectories; đối với factorial RQ2, đơn vị paired contrasts là 10 seed blocks. Với Junyi, trọng số và quần thể tùy estimand phải được khai báo trước khi diễn giải. Các tầng concept decisions, event pairs, seed blocks, learners và edge–learner pairs không hoán đổi được để tăng sample size. [S05–S08]

Các phân tích ngày 08/11 là exploratory/post-hoc trên pilot đã được xem. Chúng không báo kiểm định xác nhận, causal mediation hoặc equivalence. Đề cương yêu cầu uncertainty và hiệu chỉnh Holm cho nhiều phép so, nhưng comparison family, inferential unit, precision target và tập seeds đánh giá sau freeze vẫn cần chốt cho các thí nghiệm xác nhận. Không tự sao chép family sizes hay test choices của Paper2 sang ma trận mới của khóa luận. Development đã tham gia lựa chọn và exploration; không dùng Holdout/Test để chọn graph, calibrator, model hoặc threshold, và không coi các seed đã phân tích như unseen final seeds. [S01; S03; S04; S10]

### 5.2. Retention và provenance của nguồn lịch sử

Dưới dynamics Paper2 đã kiểm, không practice sau thời điểm T và decay đồng nhất 0,06/ngày quanh cùng fixed base, retained net mean theta gain thỏa `G14 = exp(−0,84)×Gfinal`. Quan hệ này làm retained net gain không cung cấp một ranking độc lập với final net gain trong chính điều kiện đó. Trạng thái tại T vẫn có thể phụ thuộc thứ tự luyện trước T. Không mở rộng identity sang soft mastery phi tuyến, heterogeneous forgetting hoặc practice sau T; cũng không bỏ metric retention bắt buộc của đề cương vì đã thấy sự phụ thuộc trong pilot. [S01; S09]

Provenance của Paper1 còn khoảng trống giữa PDF đã nộp và revision notebook tìm được. Counterexample re-entry của revision hiện có chỉ giới hạn claim của chính revision đó, không bác bỏ finite-run result của PDF hoặc chứng minh đã tái lập bảng gốc. Tương tự, phần mềm pass tests, checkpoint reload hoặc CUDA synthetic không trực tiếp chứng minh graph giúp học tập hay hoàn thành một RQ. [S04; S09]

### 5.3. Giới hạn khái quát hóa

Simulator responses và biến ẩn được sinh từ dynamics cụ thể; việc nhìn thấy cơ chế bên trong không loại bỏ model misspecification hoặc graph-correlated initialization. Các profiles không đại diện tự động cho phân bố người học thật. Junyi prefix order còn chịu ảnh hưởng logging policy, khả năng tiếp cận bài, thiếu quan sát và chọn cohort. Vì vậy, các kết quả hiện tại là bằng chứng chẩn đoán trong nguồn đã quan sát; chưa nhận diện instructional causal effect hoặc điều kiện hữu ích/trung tính/gây hại trên người học nói chung. [S01; S05; S07; S09]

## 6. Khoảng trống bằng chứng cần nêu trong luận văn

| Thành phần còn thiếu | Hệ quả đối với kết luận | Quyết định/bằng chứng cần bổ sung, chưa được thực hiện ở đây |
|---|---|---|
| Mastery reference và calibration quanh ngưỡng | Chưa xác định chất lượng dự báo đã đủ để tạo mastery/action change hợp lệ hay chưa | S04: bank/weights/calibration population/threshold và oracle boundary; instrumentation đủ query/state |
| Pathway isolation và chain trong vòng kín | Full package differences chưa quy được riêng cho parent edges; closed trace thiếu M/R | Ablations giữ local pathways/thông tin so sánh được; ghi đầy đủ pre-update query/mastered/ready/served action |
| Factorial/profile identification | I và profile ordering chỉ có nghĩa trong simulator và profiles hiện có | S02/S03/S05: estimand/initialization sensitivity/seed plan được chốt trước final evidence; không đổi bất lợi thành exclusion |
| Graph quality × history × sparsity × profile | Chưa có ma trận xác nhận đủ chuyên gia, graph học từ train, nhiễu xóa/thêm/đảo nhiều mức và intra/cross strata | Allocation được GVHD thống nhất; kiểm exposure/support và phân biệt retraining với inference-only noise |
| Valid common-population inference | Stored summaries không đủ tái tính learner-level uncertainty; common subsets có attrition | Target population/weighting/coverage rule và dữ liệu đủ cho inference được xác định trước, trong ranh giới truy cập được phép |
| Baselines và modern KT evaluation | Diagnostic GAM/Paper2 không thay complete AKT/SAKT/GKT/CG-AKT comparison | Giữ các đối chứng bắt buộc; fit/selection/export/calibration và coverage cùng population theo protocol được duyệt |
| Source adjudication và final inference | Chưa exact reproduction Paper1; explorations hiện có không là final untouched evaluation | S01, S05/S06: source ledger, comparison family, CI/correction, seeds/splits và Test access boundary |

Các mục trên là khoảng trống cần công bố và bàn giao, không phải thay đổi tự động của methodology. Kết luận phù hợp với bằng chứng hiện có là: đồ thị cần được đánh giá qua cả dự báo, trạng thái/quyết định và kết quả của chính sách; đồng thời, mức exposure và cách chọn mẫu số có thể giới hạn khả năng nhận diện hiệu lực. Chưa có cơ sở từ các bundle này để tuyên bố đồ thị luôn có lợi, trung tính, gây hại hoặc RQ1/RQ2 đã được giải quyết. [S01; S04–S10]

## 7. Nguồn và ghi chú biên tập

Companion [source map JSON](THESIS_METHODS_RQ12_DRAFT_20261108.sources.json) lưu SHA-256, locator theo mục/trường, đối chiếu selected output với closed manifest, liên kết từng claim và kết quả kiểm local links. SHA xác nhận bytes nguồn; không là chứng nhận hiệu lực khoa học hay phê duyệt thiết kế.

| ID | Nguồn dùng trong bản thảo | Locator chính |
|---|---|---|
| S01 | [Đề cương gốc](../../paper2/DC%20KLTN0127%2023520355%2623521338_LeVanTuan.pdf); [bản trích 5 trang](../../docs/thesis_recovery/evidence/proposal.txt) | Trang 2–4; RQ, phương pháp, phạm vi và giới hạn |
| S02 | [Truy vết yêu cầu](../../docs/thesis_recovery/02_RESEARCH_TRACEABILITY.md) | Bảng yêu cầu; bằng chứng tối thiểu E01–E06/E10 |
| S03 | [Paper2 submitted TeX](../../paper2/rivf2026_paper2_submission_v21.tex) | Method; Selector interpretation; Experimental Design — dùng phân biệt quy trình lịch sử |
| S04 | [Báo cáo GVHD 08/11](BAO_CAO_TIEN_DO_GVHD_20261108.md); [JSON kiểm nguồn](BAO_CAO_TIEN_DO_GVHD_20261108.json) | Mục 1–2 và 5; không coi báo cáo tiến độ là approval |
| S05 | [Báo cáo RQ1 mới](rq1_transition_evidence_20261108.md) | Identity, definitions, conditional table, closed-loop limits |
| S06 | [RQ1 analysis](../runs/cpu-rq1-transitions-20261108-01/analysis.json); [closed manifest](../runs/cpu-rq1-transitions-20261108-01/manifest.json) | `fixed_stream`, `closed_loop`, `definitions`; manifest có 12 outputs |
| S07 | [Báo cáo RQ2 mới](rq2_conditions_evidence_20261108.md) | Estimand/exposure; all profile pairs; graph versions; denominator/common sensitivity |
| S08 | [RQ2 conditions](../runs/rq2-conditions-evidence-20261108-01/conditions.json); [closed manifest](../runs/rq2-conditions-evidence-20261108-01/manifest.json) | `factorial`, `junyi`; manifest có 6 outputs |
| S09 | [Tổng hợp RQ1/RQ2 lịch sử](rq12_evidence_synthesis_20261107.md) | Package boundaries; retention; source revision; graph-control construction |
| S10 | [Sổ quyết định](../../docs/thesis_recovery/09_DECISION_REGISTER.md) | D01; S01–S06; không coi proposed decisions là accepted protocol |

Đề cương được dùng theo trạng thái người dùng xác nhận trong D01, chưa độc lập xác thực chữ ký bản scan. Trong lần biên soạn này, PDF gốc được kiểm SHA `941e9c43e5bbd29075051debf6cdf81256c65b89e612d001e1a5377474b4836a`; nội dung đọc từ bản trích 5 trang hiện có và đối chiếu source inventory của báo cáo GVHD. Thử trích lại bằng pdftotext local thất bại vì MiKTeX registry/setup bị chặn; không cài thêm, sửa registry hoặc dùng mạng để thay thế. Không tuyên bố đã render/kiểm trực quan PDF lần này.

Bản thảo là tài liệu mới, không ghi đè báo cáo GVHD hay nguồn luận văn/bài báo hiện có. Việc kiểm lần này giới hạn ở file/link/hash và selected closed aggregate outputs; không mở raw traces, predictions, Junyi/Holdout, chạy model/simulator hoặc thay source AKT/tracking/Git.
