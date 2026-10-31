# Báo cáo nghiên cứu baseline BKT–GAM-KT trên Junyi Academy

**Bản ghi benchmark Sprint 2**<br>
**Ngày tổng hợp:** 30-10-2026<br>
**Phạm vi:** Development 5-fold cross-validation; không đánh giá Holdout trong công việc tổng hợp này.

## 1. Tóm tắt điều hành

Mục tiêu của benchmark là thiết lập mốc dự đoán Knowledge Tracing (KT) tái lập trên Junyi Academy, kiểm tra hai họ mô hình dưới cùng một giao thức Development và chuẩn bị hợp đồng dữ liệu chung cho các thử nghiệm tiếp theo. Hai mô hình được đối chiếu là standard Bayesian Knowledge Tracing (BKT) theo từng exercise và GAM-KT graph-free dựa trên implementation Junyi đã lưu trong artifact RIVF. Kết quả GAM-KT ở đây thuộc benchmark KLTN mới, không phải kết quả RIVF.

Benchmark dùng 20.706.208 tương tác Development canonical trong năm fold student-disjoint, cùng outcome `correct`, thứ tự thời gian và assignment đã đóng băng. So sánh common-row giữ 20.706.014 dòng fitted; 194 dòng GAM-KT fallback được báo riêng. Trung bình không trọng số của metric theo năm fold cho thấy BKT có AUC-ROC 0,783413, Log Loss 0,375607, Brier 0,115105, ECE 0,002241 và Accuracy 0,847416. GAM-KT lần lượt đạt 0,774866, 0,394881, 0,120372, 0,055542 và 0,841453 trên cùng các dòng. BKT tốt hơn trên cả năm metric trong từng fold.

Learner-clustered bootstrap trong từng fold cho CI 95% không chứa 0 ở Log Loss, Brier, ECE và Accuracy. Đây là bằng chứng về độ nhất quán theo learner trong năm split/model fit hiện có; nó không giải thích nguyên nhân nhân quả, không đo bất định do huấn luyện lại và không bao quát split khác. Paired bootstrap CI cho AUC chưa được tính.

Kết quả này là **baseline benchmark**. Nó không bật graph, không kiểm tra chất lượng graph, không đánh giá chính sách chọn lộ trình và không trực tiếp trả lời RQ1–RQ3. Theo yêu cầu Sprint 2, các mốc kế tiếp cần tách hiệu ứng predictive model khỏi graph effect và policy outcome, sau đó triển khai AKT graph-free theo giao thức chung. Repository không có bản đăng ký thesis chứa nguyên văn RQ hoặc advisor feedback; phần ánh xạ RQ trong báo cáo vì vậy dùng mô tả thí nghiệm đã nêu trong yêu cầu Sprint 2, không tự nhận là trích dẫn thesis.

## 2. Bối cảnh nghiên cứu và liên hệ với thesis

KT ước lượng trạng thái kiến thức hoặc xác suất trả lời đúng từ lịch sử tương tác của learner. Ước lượng đó có thể là đầu vào cho việc chọn bài tiếp theo trong hệ thống adaptive learning. Khi mục tiêu sau cùng bao gồm learning path, cần phân biệt ba bước: dự đoán phản hồi, chuyển dự đoán thành quyết định chọn bài, rồi đánh giá chính sách trên trải nghiệm hoặc kết quả học tập. AUC hay Log Loss chỉ đo bước dự đoán; chúng không chứng minh quyết định hoặc chính sách tốt hơn.

Junyi có catalog exercise với trường `prerequisites`, nhưng exercise ID không đồng nhất với knowledge-component (KC) ID. Graph trên catalog có thể là tín hiệu cấu trúc cho mô hình; hiệu quả của nó cần được cô lập bằng so sánh graph-on/off với cùng dữ liệu, split và các thành phần khác. Mô hình graph-free trong benchmark này không thể cung cấp bằng chứng graph có ích hay không có ích.

Classical BKT cung cấp mốc xác suất với latent mastery state nhị phân và tham số diễn giải được. GAM-KT ở đây là một mô hình gain-adaptive có state tuần tự theo exercise, memory vector và uncertainty; graph signal, graph adaptation và time decay đều tắt. Hai baseline có thể giúp kiểm tra pipeline và khác biệt giữa các giả định, nhưng cấu hình/parameterization của chúng không giống nhau nên đây không phải ablation chỉ thay graph.

Repository chỉ có mục tiêu baseline BKT trong `_context/research_goals.md`; không tìm thấy proposal/outline thesis hoặc ghi chú advisor chứa RQ nguyên văn. Bảng dưới đây vì vậy ánh xạ các deliverable vào các yêu cầu RQ theo mô tả của đề bài Sprint 2. Các nhãn mô tả này không phải trích dẫn đã xác minh từ tài liệu đăng ký thesis.

| RQ theo phạm vi yêu cầu Sprint 2 | Bằng chứng benchmark hiện có | Deliverable Sprint 2 liên quan | Quan hệ với RQ |
|---|---|---|---|
| **RQ1:** kiểm tra graph-on/off và phân tích prediction → decision → policy | BKT và graph-free GAM-KT common-row CV; chưa có graph-on/off, decision hoặc policy outcome | Benchmark, paired bootstrap và hợp đồng KT dùng chung | Hạ tầng baseline; chưa trả lời graph effect hoặc policy effect |
| **RQ2:** kiểm tra chất lượng graph, độ dài history và learner conditions | Catalog prerequisite được kiểm toán sơ bộ; chưa có controlled graph-quality/history/learner-condition experiment | Graph metadata audit và sequence input contract | Chuẩn bị dữ liệu; chưa trả lời điều kiện nào graph/model có ích |
| **RQ3:** so sánh AKT, fixed-graph AKT và CG-AKT với edge confidence, graph-off gating và ablation | Chưa có các model hoặc ablation đó | Shared input/alignment contracts; chưa có model CV | Hạ tầng tích hợp; chưa có kết quả mô hình |

Theo nghĩa này, benchmark đóng góp nền tảng tái lập, kiểm tra độ khớp và baseline dự đoán. Nó không hoàn thành RQ nào. Predictive benchmark nên đi trước graph-effect và closed-loop evaluation để bảo đảm dữ liệu, target, alignment và metric được ổn định trước khi quy khác biệt cho graph hoặc chính sách.

## 3. Dataset và preprocessing

### 3.1. Dữ liệu và đơn vị phân tích

Nguồn tương tác là `dataset/junyi_ProblemLog_original.csv`; metadata exercise nằm tại `dataset/junyi_Exercise_table.csv`. Profiling và báo cáo baseline ghi **25.925.992** dòng raw ProblemLog và **247.606** learner duy nhất. Canonical preprocessing tạo bản dẫn xuất **25.924.553** dòng, giữ một đại diện cho mỗi bản sao hoàn toàn giống nhau và ghi lineage; **1.439** dòng dư bị loại khỏi bản dẫn xuất. CSV gốc không bị sửa.

Giao thức chia người học có 198.084 learner Development và 49.522 learner Holdout/Test. Các con số Holdout ở đây chỉ mô tả assignment; báo cáo này không truy vấn dự đoán, chấm điểm hoặc chọn cấu hình trên Holdout. Trong Development có 20.706.208 canonical interaction và năm fold validation student-disjoint. Trong mỗi lượt CV, bốn fold còn lại là train và fold thứ năm là validation.

Exercise coverage có hai mẫu số cần giữ riêng: profiling ProblemLog báo 722 exercise trong toàn log, còn CV/final-refit Development có 720 exercise quan sát được. Hai exercise ID chênh lệch không được phân tích ở đây; không suy diễn nguyên nhân bằng Holdout. Catalog metadata có 835 `name` ID duy nhất. Do đó 720 là số exercise của Development, 722 là số trong profiling toàn ProblemLog và 835 là số node catalog, không thể dùng thay lẫn nhau.

### 3.2. Split và thứ tự

Assignment dùng `sha256-user-rank-v1`, seed 42. Theo `src/knowledge_tracing/bkt_baseline/splits.py`, learner ID được xếp theo SHA-256 của chuỗi `junyi-bkt-split-v1|seed|user_id`, tie-break bằng ID; 80% đầu xếp vào Development và được gán fold theo vị trí modulo 5. Mỗi learner chỉ thuộc một partition/fold. Số Development learner theo fold là 39.617, 39.617, 39.617, 39.617 và 39.616.

Preprocessing gán `source_row` theo thứ tự record CSV trước deduplication. Dòng giữ lại cho bản sao chính xác có lineage về dòng gốc; các bản ghi trùng theo `(user_id, exercise, problem_number)` nhưng khác nội dung không bị gộp theo khóa yếu đó. Timeline dùng `(user_id, time_done, source_row)` để phá timestamp tie xác định. `time_done` được diễn giải theo microsecond; trong pipeline BKT, `order_id` được tạo theo `(user_id, exercise, time_done, source_row)`.

Outcome là `correct` nhị phân, true/1 thành 1 và false/0 thành 0. Tài liệu readiness ghi nhận mọi dòng có `hint_used=true` đều `correct=false`; do đó nhãn phản ánh định nghĩa đúng của dataset, bao gồm ảnh hưởng của việc dùng hint. `suggested` chỉ dùng để phân tầng báo cáo, không là predictor của hai baseline.

### 3.3. Leakage, coverage và giới hạn dữ liệu

Mỗi fold chỉ fit BKT và difficulty của GAM-KT trên bốn fold Development train. GAM-KT replay validation theo thời gian: dự đoán interaction hiện tại trước, sau đó mới update state bằng `correct` hiện tại để dự đoán interaction kế tiếp. BKT sử dụng one-step prediction của pyBKT với cùng outcome và thứ tự. Các fold là user-disjoint; learner validation mới với mô hình, nhưng trong giao thức tuần tự có thể đóng góp lịch sử phản hồi của chính họ sau khi từng phản hồi đã được dự đoán. Đây không phải cold-start đánh giá mọi event khi chưa có lịch sử.

Exercise không có model BKT trong train có prediction null và không vào metric fitted BKT. GAM-KT vẫn có thể tạo prediction bằng global difficulty fallback; các row này được đánh dấu fallback. So sánh common-row chỉ dùng dòng mà cả hai bên có fitted prediction. Cả hai pipeline lưu `source_row` để đối chiếu và phục hồi danh tính interaction.

Data readiness audit cũng ghi nhận 402 nhóm cùng `(user_id, exercise, problem_number)` nhưng có nội dung khác nhau, độ dài chuỗi learner–exercise lệch mạnh (median 8, max 5.174), exercise support long-tail và `suggested` gần như luôn đi cùng đáp án đúng. Không có interaction primary key độc lập. Các đặc điểm này hạn chế diễn giải skill hiếm, nhóm suggested và thứ tự của các bản sao; các số liệu chi tiết nằm ở `docs/bkt-data-readiness-audit.md`.

## 4. Mô hình và implementation

### 4.1. Standard BKT

BKT dùng một Hidden Markov Model hai trạng thái tiềm ẩn cho mỗi `exercise`: chưa mastery và đã mastery. Tham số chuẩn gồm prior mastery, learning transition, guess và slip; `forgets=False` khóa quên ở mức 0. Quan sát là `correct`. Với từng exercise, CAHLR/pyBKT 1.4.3 ước lượng tham số bằng EM trên interaction train; runner gọi `Model.fit` cho riêng skill, rồi dùng pyBKT one-step prediction trên chuỗi validation. Sau dự đoán tại thời điểm t, phản hồi t chỉ ảnh hưởng state dùng cho bước kế tiếp.

CV dùng `num_fits=1`, `forgets=False`, `tol=0.005`, `maxiter=100`, `base_seed=42`; seed fit cho từng exercise/fold được dẫn xuất xác định từ base seed. C++ backend trong WSL dùng patch tương thích likelihood đã ghi ở `docs/pybkt-provenance.md`; patch không viết lại EM. Protocol và hash backend/source nằm trong `experiments/bkt_baseline/results/wsl_cpp/cv_cpp/run_manifest.json`. CV aggregate đọc từ `experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json`.

Đơn vị BKT là exercise dùng tạm như một skill; không có KC mapping. Model được fit qua learner train của fold cho từng exercise, còn state dự đoán áp dụng tuần tự lên learner validation. Skill chưa thấy trong train không có model fitted và không được gán điểm giả.

### 4.2. Graph-free GAM-KT

Implementation model được trích nguyên định nghĩa từ Junyi notebook cell 11 trong artifact RIVF; `src/knowledge_tracing/gam_kt/original_junyi.py` giữ model, còn adapter/runner xử lý dữ liệu và protocol. GAM-KT không phải standard BKT và không phải Graph-GAM-KT.

Model có ability `theta` khởi tạo 1200, memory vector 64 chiều khởi tạo 0, `pi_task` khởi tạo 1, `pi_time` khởi tạo 0,05, cùng số lần thử, thời gian gần nhất, lịch sử outcome gần và bộ đếm forgetting. State có chỉ số exercise và được reset khi đổi learner. Feature vector hashed từ exercise, `problem_type`, topic và area. Prediction dựa trên ability so với difficulty, item-memory similarity và confidence shrinkage; update ability/memory/uncertainty bằng residual sau dự đoán. Các learning/update rate là tham số cố định của source model, không được fit bằng CV labels.

Difficulty được fit riêng trong từng fold từ bốn fold train: global correctness và exercise correctness smoothing với `alpha=20`, sau đó đổi sang Elo-like difficulty; probability và difficulty bị clip theo source. Exercise không có train support dùng global difficulty và được đánh dấu fallback. Theo `src/knowledge_tracing/gam_kt/model.py`, benchmark đặt `use_graph_context=False`, `graph_weight=0`, `graph_source=None`, `graph_signal_enabled=False`, `graph_adaptation_enabled=False` và `time_decay_rate=0`. Do đó graph signal, graph adaptation và time decay đều disabled; metadata topic/area vẫn là input feature tĩnh. Đây là **graph-free GAM-KT**.

Manifest CV ghi model cell SHA-256 `5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc`, assignment SHA-256 `ee588c5b72fc214295e6eef1839b5110c884f43ab52ab4a792ca82e35812be20`, canonical manifest SHA-256 `035fb113fcbbd0f433fcda210d43ef279f6eb8163e0b3b4b72c9d4f066a02fb7` và timestamp unit `us`. Manifest đầy đủ: `experiments/gam_kt/results/wsl_cpp/cv/cv.json`.

### 4.3. Khác biệt có ý nghĩa cho diễn giải

BKT học tham số HMM theo exercise bằng EM. GAM-KT dùng update rule/memory cố định và preprocessing difficulty train-only. GAM-KT có metadata feature (problem type/topic/area) mà BKT chuẩn không dùng; BKT có tham số latent chuyển trạng thái fit cho mỗi exercise. Vì họ mô hình, cách fit, state và feature khác nhau, quan sát BKT tốt hơn không thể quy riêng cho graph, cũng không phải kết luận rằng mọi deep KT kém hơn BKT.

## 5. Experimental protocol và metric

CV dùng cùng frozen global user assignment và 5 fold Development. Trong mỗi fold, mọi preprocess học từ nhãn (BKT EM và GAM-KT global/exercise difficulty) chỉ dùng bốn fold train. Mỗi validation interaction được dự đoán trước khi outcome hiện tại update state. GAM-KT runner lưu native, supported-only và common-row metrics; BKT metric chỉ tính skill fitted. Common-row được ghép theo `source_row`, sau đó audit `user_id`, exercise, `correct`, `suggested` và train support.

Metric được tính trong mỗi fold riêng. Bảng kết quả chính báo **trung bình số học không trọng số của năm fold**, kèm sample standard deviation (`ddof=1`). Đây là mean-of-fold metrics; không phải metric tính trên một bảng prediction pooled. Bootstrap cũng lấy trung bình không trọng số của fold-level paired differences. Pooled-row AUC/metrics không được báo cáo.

Với nhãn $y_i\in\{0,1\}$, xác suất dự đoán $p_i\in[0,1]$, và $n$ dòng fitted:

**AUC-ROC** (cao hơn tốt hơn) là xác suất score của một mẫu dương lớn hơn score của một mẫu âm; ties được tính một nửa:

$$
\mathrm{AUC}=\frac{1}{n_+n_-}\sum_{i:y_i=1}\sum_{j:y_j=0}\left(\mathbf{1}[p_i>p_j]+\frac{1}{2}\mathbf{1}[p_i=p_j]\right).
$$

AUC không xác định nếu fold chỉ có một lớp.

**Log Loss** (thấp hơn tốt hơn):

$$
\mathrm{LogLoss}=-\frac{1}{n}\sum_{i=1}^{n}\left[y_i\log(p_i)+(1-y_i)\log(1-p_i)\right].
$$

**Brier Score** (thấp hơn tốt hơn):

$$
\mathrm{Brier}=\frac{1}{n}\sum_{i=1}^{n}(p_i-y_i)^2.
$$

**Expected Calibration Error (ECE)** (thấp hơn tốt hơn):

$$
\mathrm{ECE}_{15}=\sum_{b=1}^{15}\frac{n_b}{n}\left|\mathrm{acc}(B_b)-\mathrm{conf}(B_b)\right|.
$$

$B_b$ là bin thứ $b$, $n_b$ là số dòng trong bin, `acc` là tỷ lệ đúng trung bình và `conf` là xác suất dự đoán trung bình. Dùng 15 equal-width bins `[k/15,(k+1)/15)`; $p=1$ thuộc bin cuối. ECE phụ thuộc số lượng và cách chia bin.

**Accuracy** (cao hơn tốt hơn), với ngưỡng 0,5:

$$
\mathrm{Accuracy}=\frac{1}{n}\sum_{i=1}^{n}\mathbf{1}\left[\mathbf{1}(p_i\ge0.5)=y_i\right].
$$

BKT common-row metric và BKT supported metric cùng mẫu số vì 194 GAM fallback cũng là 194 BKT unseen rows. GAM native metric tính toàn bộ predictions kể cả fallback; supported/common-row loại fallback. Native và common-row không được trộn trong cùng kết luận. CV mean ± SD mô tả khác biệt giữa năm fold; SD không phải confidence interval hay sai số chuẩn. Bootstrap CI là phân tích bất định riêng.

## 6. Kết quả định lượng

### 6.1. Counts và coverage theo fold

Số predictions native của cả hai hệ bằng tổng validation rows; common fitted rows bằng BKT scored rows và GAM supported rows.

| Fold | Learner validation | Validation rows | BKT fitted / common rows | GAM native rows | GAM fallback rows | Fitted coverage |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 39.617 | 4.198.649 | 4.198.615 | 4.198.649 | 34 | 99,99919% |
| 1 | 39.617 | 4.061.255 | 4.061.239 | 4.061.255 | 16 | 99,99961% |
| 2 | 39.617 | 4.182.390 | 4.182.390 | 4.182.390 | 0 | 100,00000% |
| 3 | 39.617 | 4.126.864 | 4.126.864 | 4.126.864 | 0 | 100,00000% |
| 4 | 39.616 | 4.137.050 | 4.136.906 | 4.137.050 | 144 | 99,99652% |
| **Tổng** | **198.084** | **20.706.208** | **20.706.014** | **20.706.208** | **194** | **99,99906%** |

Không có unmatched `source_row`, duplicate `source_row`, identity mismatch hoặc support mismatch trong kiểm tra common-row. Các số kiểm tra lại bằng `scripts/bootstrap_bkt_gam_cv.py` và lưu audit theo fold trong `reports/paired_cluster_bootstrap_bkt_gam.json`.

### 6.2. Common-row scores theo fold

Các bảng dưới đây chỉ dùng common fitted rows. AUC, Log Loss, Brier, ECE và Accuracy trong từng ô được tính trực tiếp từ từng fold JSON; tổng hợp lại bằng `cv.json`.

| Fold | Rows | AUC-ROC ↑ | Log Loss ↓ | Brier ↓ | ECE ↓ | Accuracy ↑ |
|---:|---:|---:|---:|---:|---:|---:|
| **BKT** |||||||
| 0 | 4.198.615 | 0,783453 | 0,374842 | 0,114848 | 0,001728 | 0,847632 |
| 1 | 4.061.239 | 0,782911 | 0,377469 | 0,115749 | 0,003417 | 0,846624 |
| 2 | 4.182.390 | 0,785234 | 0,373335 | 0,114251 | 0,001768 | 0,848557 |
| 3 | 4.126.864 | 0,783397 | 0,376275 | 0,115401 | 0,002446 | 0,846907 |
| 4 | 4.136.906 | 0,782072 | 0,376116 | 0,115277 | 0,001847 | 0,847360 |
| **GAM-KT** |||||||
| 0 | 4.198.615 | 0,775099 | 0,393885 | 0,119964 | 0,055997 | 0,841975 |
| 1 | 4.061.239 | 0,774012 | 0,396646 | 0,121101 | 0,054758 | 0,840144 |
| 2 | 4.182.390 | 0,776388 | 0,393073 | 0,119640 | 0,056448 | 0,842817 |
| 3 | 4.126.864 | 0,775131 | 0,395446 | 0,120630 | 0,055216 | 0,840829 |
| 4 | 4.136.906 | 0,773700 | 0,395355 | 0,120523 | 0,055291 | 0,841500 |

### 6.3. Chênh lệch theo fold và tổng hợp

$\Delta=\text{GAM-KT}-\text{BKT}$. Giá trị âm tốt hơn với AUC/Accuracy; giá trị dương tốt hơn với các loss/error metric theo chiều ngược lại. Cột `|Δ|` cho biết độ lớn tuyệt đối, không đồng nghĩa với relative percent change.

| Fold | Δ AUC | Δ Log Loss | Δ Brier | Δ ECE | Δ Accuracy |
|---:|---:|---:|---:|---:|---:|
| 0 | −0,008353 | +0,019043 | +0,005116 | +0,054269 | −0,005658 |
| 1 | −0,008899 | +0,019177 | +0,005352 | +0,051341 | −0,006480 |
| 2 | −0,008846 | +0,019738 | +0,005389 | +0,054680 | −0,005740 |
| 3 | −0,008266 | +0,019170 | +0,005228 | +0,052770 | −0,006077 |
| 4 | −0,008372 | +0,019239 | +0,005246 | +0,053444 | −0,005859 |
| **Mean Δ** | **−0,008547** | **+0,019273** | **+0,005266** | **+0,053301** | **−0,005963** |
| **Abs mean Δ** | **0,008547** | **0,019273** | **0,005266** | **0,053301** | **0,005963** |

| Metric | BKT mean ± sample SD | GAM-KT common-row mean ± sample SD | Mean-of-fold Δ | Hướng tốt |
|---|---:|---:|---:|---|
| AUC-ROC | 0,783413 ± 0,001158 | 0,774866 ± 0,001064 | −0,008547 | Cao hơn |
| Log Loss | 0,375607 ± 0,001575 | 0,394881 ± 0,001407 | +0,019273 | Thấp hơn |
| Brier Score | 0,115105 ± 0,000576 | 0,120372 ± 0,000575 | +0,005266 | Thấp hơn |
| ECE | 0,002241 ± 0,000719 | 0,055542 ± 0,000673 | +0,053301 | Thấp hơn |
| Accuracy | 0,847416 ± 0,000748 | 0,841453 ± 0,001029 | −0,005963 | Cao hơn |

Trên relative scale, GAM-KT có Log Loss cao hơn khoảng 5,13% và Brier cao hơn khoảng 4,58% so với mean BKT; Accuracy giảm khoảng 0,60 điểm phần trăm (0,70% tương đối). Không dùng relative percent cho ECE vì giá trị BKT rất gần 0; chênh lệch tuyệt đối 0,053301 dễ diễn giải hơn. Các con số là fold-average, không phải pooled-row scores.

GAM-KT native CV có 20.706.208 prediction rows, trong đó 194 fallback. Mean native GAM-KT theo `report_vi.md` là AUC 0,774867, Log Loss 0,394882, Brier 0,120372, ECE 0,055542 và Accuracy 0,841452 (± sample SD giữa fold lần lượt 0,001064; 0,001408; 0,000575; 0,000673; 0,001030). Khác biệt nhỏ so với supported mean đến từ 194 fallback; BKT aggregate trong `cv.json` trùng common-row BKT. Bảng so sánh chính dùng common rows.

## 7. Statistical analysis: learner-clustered bootstrap

Các interaction của cùng learner có phụ thuộc do lịch sử, state update và hành vi lặp. Bootstrap từng interaction độc lập sẽ phá cấu trúc chuỗi và đánh giá thấp sự phụ thuộc trong cùng learner. Do đó đơn vị resampling là learner: trong mỗi fold, lấy learner có hoàn lại và giữ toàn bộ common fitted interaction của learner được chọn. Resample độc lập trong từng fold để giữ nguyên thiết kế 5-fold; ở mỗi replicate tính fold-level metric differences rồi lấy mean không trọng số giữa 5 fold.

Phân tích dùng 1.000 replicate, seed 20261030, percentile 95% interval. Script tổng hợp per-learner sufficient statistics một lượt từ predictions Parquet trong DuckDB; không nạp toàn bộ event table vào RAM. Kết quả dưới đây được kiểm tra với JSON `reports/paired_cluster_bootstrap_bkt_gam.json`.

| Metric difference (GAM-KT − BKT) | Estimate | Percentile CI 95% |
|---|---:|---:|
| Log Loss | +0,019273 | [+0,018780; +0,019730] |
| Brier | +0,005266 | [+0,005096; +0,005413] |
| ECE | +0,053301 | [+0,052170; +0,053826] |
| Accuracy | −0,005963 | [−0,006201; −0,005702] |

CI không chứa 0 hỗ trợ nhận định rằng các chênh lệch này ổn định theo resampling learner có điều kiện trên năm split và model fits đã lưu. Về practical magnitude, Accuracy giảm khoảng 0,60 điểm phần trăm còn ECE tăng 0,0533; đánh giá ý nghĩa giáo dục cần outcome/policy study và ECE cũng nhạy với binning. CI không xác lập nguyên nhân nhân quả, không thay thế randomized/counterfactual policy study, không bao gồm variability do refit/seed/split mới và không chứng minh mức khác biệt có ý nghĩa giáo dục thực tiễn. Không có paired learner bootstrap CI cho AUC; chỉ có AUC fold metrics và fold dispersion.

## 8. Diễn giải và thảo luận

### Bằng chứng quan sát được

1. BKT tốt hơn GAM-KT trên cả AUC, Log Loss, Brier, ECE và Accuracy ở cả năm fold common-row.
2. ECE common-row của GAM-KT khoảng 0,0555, so với khoảng 0,00224 của BKT. Theo định nghĩa ECE 15 bin đã dùng, xác suất GAM-KT lệch calibration nhiều hơn trên tập này. ECE phụ thuộc lựa chọn bin và không mô tả toàn bộ calibration curve.
3. Bootstrap learner-clustered cho cùng chiều với mean-of-fold differences ở bốn metric đã có CI.
4. GAM-KT có feature `problem_type`, topic và area, nhưng graph và decay bị tắt. Benchmark không so sánh graph-on với graph-off.

### Giả thuyết cần thí nghiệm tiếp

Khác biệt có thể liên quan đến việc BKT ước lượng transition/emission parameters bằng EM theo exercise, còn GAM-KT dùng update rates cố định; smoothing difficulty theo correctness có thể chưa phù hợp với mọi exercise; confidence shrinkage và memory update có thể tạo calibration behavior khác; hoặc phân phối event/sequence của Junyi có thể phù hợp hơn với một biểu diễn cụ thể. Đây là giả thuyết dựa trên khác biệt implementation, chưa được kiểm chứng bằng ablation chẩn đoán trong các artifacts hiện có. Không thể từ kết quả này suy ra toàn bộ neural/deep KT kém BKT, hay graph prerequisite không hiệu quả.

## 9. Audit metadata Junyi và prerequisite graph

`dataset/junyi_Exercise_table.csv` có 837 dòng và 835 `name` ID duy nhất; hai ID lặp một lần và các bản ghi trùng giống nhau ở trường prerequisite/topic/area/live. Development CV có 720 exercise IDs và cả 720 khớp `name`. Graph tái dựng trong bộ nhớ giữ 835 node, đọc danh sách parent từ `prerequisites`, gộp cạnh trùng và loại 2 self-edge, còn 979 cạnh duy nhất. Có 59 node không incident với cạnh; node vẫn được giữ trong graph. Không có endpoint prerequisite nào ngoài catalog trong lần audit.

Hướng cạnh được biểu diễn **prerequisite → dependent exercise**: mỗi ID trong trường `prerequisites` trỏ tới `name` của dòng catalog đó. Mapping exercise→graph node là phép khớp ID trực tiếp qua `name`, không phải KC mapping. Catalog có `topic` và `area` nhưng không thấy explicit knowledge-component ID hoặc bảng ánh xạ exercise–KC trong nguồn được kiểm tra. Hai CSV relationship annotation có cặp exercise và nhãn quan hệ, nhưng không được dùng làm gold-standard prerequisite graph trong benchmark.

Các cạnh là curriculum metadata do dataset cung cấp. Chúng chưa được xác minh độc lập về causal semantics, thứ tự mastery, độ đúng hướng cho mọi relation hay confidence. Graph này là candidate structural prior cho future graph-aware models; không nên gọi là ground-truth causal graph. GAM-KT benchmark hiện tại không dùng cạnh nào.

## 10. Shared KT evaluation infrastructure

Sprint 2 đã thêm và test các reusable components trong `src/knowledge_tracing/shared_kt.py`:

- `StableVocabulary` tạo ID ổn định và encode/decode; caller dùng train-fold vocabulary cho held-out data và cần chọn chính sách OOV tường minh.
- Mapping audit báo unmapped, ambiguous exercise/concept và graph nodes thiếu mapping mà không tự suy diễn.
- `PrerequisiteGraph` lưu node/cạnh có hướng prerequisite→dependent và kiểm tra endpoint/self-edge.
- `validate_fold_isolation` kiểm tra learner không xuất hiện qua nhiều fold.
- `build_causal_sequence_inputs` sắp theo `(user_id,time_done,source_row)`, đưa item hiện tại và response history đã shift vào inputs; target hiện tại tách riêng.
- `causal_attention_mask`, prediction identity/alignment theo `source_row` và coverage summary.
- `SequenceKTModel.fit(inputs, targets)` / `predict(inputs)` là batch protocol; không ép deep model theo online BKT/GAM state update.

Các hợp đồng giúp tích hợp AKT, SAKT và GKT theo cùng chronology, response shift, vocabulary và alignment; graph abstraction chuẩn bị cho Graph-GAM-KT, fixed-graph AKT và CG-AKT. Chúng không phải implementations của các model này. Test contract không chứng minh chất lượng khoa học của model hoặc hiệu quả dự đoán.

## 11. Limitations và threats to validity

### Giới hạn đã xác minh

- **Dữ liệu quan sát:** Junyi log phản ánh hoạt động trong một nền tảng; không phải randomized intervention hay đo trực tiếp lượng kiến thức đạt được.
- **Outcome semantics:** `correct` có quy ước false khi learner dùng hint. Đây là target benchmark đã chốt, không phải phép đo thuần mastery.
- **Exercise/KC mismatch:** BKT fit theo exercise; graph node cũng là exercise ID. Explicit KC mapping chưa có.
- **Graph validation:** prerequisite metadata chưa có independent causal ground truth và không tham gia GAM-KT benchmark.
- **Model-family confounding:** BKT EM và GAM-KT fixed-rule differ về parameterization/features/state; không thể cô lập một thành phần duy nhất.
- **User-disjoint scope:** đo generalization tới learner không dùng fit tham số, nhưng validation cho phép online update từ phản hồi đã dự đoán trước; không đo thuần cold-start hoặc policy deployment.
- **Calibration metric:** ECE phụ thuộc binning; Accuracy phụ thuộc threshold; AUC không đánh giá calibration.
- **CV vs Holdout:** báo cáo này chỉ dùng Development CV. Không đưa kết quả final Holdout vào chọn cấu hình hoặc benchmark này.
- **Aggregation/coverage:** mean của năm fold cho trọng số bằng nhau dù số dòng/fold hơi khác; fallback 194 row bị loại khỏi common-row. Không được coi mean-fold là pooled-event estimate.
- **Bootstrap scope:** learner resampling có điều kiện trên năm fits/splits; không đo lại fitting noise, split uncertainty hoặc model-selection uncertainty. AUC CI chưa tính.
- **Practical outcome:** không có đo lường learning gain, retention, fairness hay real-world adaptive-policy impact trong benchmark.

### Rủi ro cần kiểm tra thêm

Thời lượng lịch sử, support exercise, hint policy và sự mất cân bằng `suggested` có thể tạo dị biệt giữa nhóm learner/item. Nên phân tích theo condition đã đăng ký trước và tránh diễn giải subgroup mô tả như tác động nhân quả. Việc chọn maximum history length, truncation, OOV behavior, optimizer, early stopping và hyperparameter search cho deep models chưa được xác định trong benchmark này; các quyết định phải fit trong fold train và không dùng Holdout.

## 12. RQ: bằng chứng đã có và còn thiếu

Nguyên văn RQ và advisor feedback không thấy trong repository. Nội dung dưới đây là ma trận theo các yêu cầu bằng chứng được nêu trong task consolidation, cần đối chiếu với thesis registration trước khi trích dẫn như wording chính thức.

| RQ | Bằng chứng cần thiết | Bằng chứng hiện có | Còn chưa trả lời | Thí nghiệm tiếp theo |
|---|---|---|---|---|
| **RQ1 — graph effect và adaptive decision/policy** | Graph-on/off dưới cùng protocol; prediction-to-decision-to-policy; outcome đánh giá phù hợp | BKT và graph-free GAM-KT Development CV; audit catalog | Hiệu ứng graph, chất lượng quyết định, policy benefit/learning outcome | Giữ model/data fixed để ablate graph trước; sau đó đánh giá decision/policy với protocol riêng, không dùng predictive score thay outcome |
| **RQ2 — graph quality, history và learner conditions** | Controlled graph-quality, history-length và learner-condition comparisons | Metadata graph sơ bộ; frozen fold sequence contracts | Sensitivity với graph noise/coverage, lịch sử ngắn/dài, learner/item sparsity | Đăng ký nhóm history/learner trước; tạo các graph variant có provenance/confidence và chạy ablation trên cùng fold |
| **RQ3 — graph-aware deep KT** | AKT, fixed-graph AKT, CG-AKT; edge confidence, graph-off gating, ablations | Shared input/alignment contracts; chưa có model CV | Mức cải thiện và nguồn đóng góp của attention, graph confidence/gating | AKT graph-free làm bước đầu; tiếp đó fixed-graph AKT/CG-AKT với edge confidence, graph-off gate và ablation đã định trước |

Không RQ nào được trả lời hoàn chỉnh bởi BKT–GAM-KT benchmark. Những mục “thí nghiệm tiếp theo” là kế hoạch đề xuất theo yêu cầu task, không phải kết quả đã chạy.

## 13. Trạng thái Sprint 2 và mốc kế tiếp

| Model/hạ tầng | Implementation | Tests | Development CV evidence | Việc còn lại |
|---|---|---|---|---|
| BKT | Có; standard per-exercise, frozen protocol | Baseline suite hiện có | Có; 5 fold, fitted coverage 99,9991% | Giữ làm baseline; báo unseen support rõ ràng |
| GAM-KT graph-free | Có; Junyi model adapter/replay | Parity, pipeline và metric tests | Có; native/supported/common-row 5 fold | Giữ phân biệt fallback và fitted; không gắn nhãn Graph-GAM-KT |
| Graph-GAM-KT | Chưa triển khai trong benchmark KLTN này | Chưa có | Chưa có | Định nghĩa graph source, edge semantics và ablation graph-on/off |
| AKT graph-free | Chưa triển khai | Chưa có | Chưa có | **Mốc khuyến nghị kế tiếp**; cố định input, truncation/OOV, training-only vocab, checkpoint/selection protocol |
| SAKT | Chưa triển khai | Chưa có | Chưa có | Dùng shared sequence contract sau khi AKT protocol ổn định |
| GKT | Chưa triển khai | Chưa có | Chưa có | Cần xác định node semantics và graph quality trước |
| Fixed-graph AKT | Chưa triển khai | Chưa có | Chưa có | Chờ graph provenance/edge direction/confidence và AKT graph-free baseline |
| CG-AKT | Chưa triển khai | Chưa có | Chưa có | Cần edge confidence, graph-off gating và ablations được thiết kế trước |

Mốc AKT graph-free tạo comparator attention-based không dùng graph và giúp kiểm tra sequence contract. Không có blocker implementation AKT nào được xác minh ở repo; các quyết định OOV, sequence truncation, tối ưu và chọn checkpoint là việc phải chốt trước khi train. Thiếu explicit KC mapping và graph quality ground truth là blocker cho diễn giải graph/KC-aware results, không phải blocker để xây baseline AKT theo exercise IDs. **Sprint 2 chưa hoàn tất** theo phạm vi rộng gồm graph/deep model experiments và RQ analyses.

## 14. Phụ lục tái lập

### Evidence paths

- Dataset protocol/lineage: [`docs/bkt-baseline-results.md`](../bkt-baseline-results.md), [`docs/bkt-data-readiness-audit.md`](../bkt-data-readiness-audit.md), [`preprocess.py`](../../src/knowledge_tracing/bkt_baseline/preprocess.py), [`splits.py`](../../src/knowledge_tracing/bkt_baseline/splits.py), [`_context/evaluation_protocol.md`](../../_context/evaluation_protocol.md).
- BKT CV: [`cv.json`](../../experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json); protocol/runtime/source hashes: [`run_manifest.json`](../../experiments/bkt_baseline/results/wsl_cpp/cv_cpp/run_manifest.json).
- GAM-KT CV: [`cv.json`](../../experiments/gam_kt/results/wsl_cpp/cv/cv.json), `fold=0.json` … `fold=4.json`, [`report_vi.md`](../../experiments/gam_kt/results/wsl_cpp/cv/report_vi.md); configuration and provenance are recorded trong `cv.json`.
- Metric definitions: [`metrics.py`](../../src/knowledge_tracing/bkt_baseline/metrics.py) và [`evaluation.py`](../../src/knowledge_tracing/gam_kt/evaluation.py).
- GAM-KT configuration/source: [`model.py`](../../src/knowledge_tracing/gam_kt/model.py), [`difficulty.py`](../../src/knowledge_tracing/gam_kt/difficulty.py), [`replay.py`](../../src/knowledge_tracing/gam_kt/replay.py), [`original_junyi.py`](../../src/knowledge_tracing/gam_kt/original_junyi.py); integration note: [`docs/gam-kt-integration.md`](../gam-kt-integration.md).
- Bootstrap: [`bootstrap_bkt_gam_cv.py`](../../scripts/bootstrap_bkt_gam_cv.py), [`paired_bootstrap.py`](../../src/knowledge_tracing/paired_bootstrap.py), [`paired_cluster_bootstrap_bkt_gam.json`](../../reports/paired_cluster_bootstrap_bkt_gam.json).
- Shared contracts: [`shared_kt.py`](../../src/knowledge_tracing/shared_kt.py), tests ở [`tests/shared_kt/`](../../tests/shared_kt/).
- Research context locally available: `papers/KT Papers Survey Report.md`, `papers/Deep Knowledge Tracing.pdf`, `papers/A Survey of KT.pdf`. Không tìm thấy registered thesis outline hoặc advisor feedback trong `docs/`, `papers/` hoặc `_context/`.

### Lightweight checks

Lệnh test đã chạy trong repository:

```powershell
$env:PYTHONPATH = 'src'
.\venv\Scripts\python.exe -m pytest -q tests/bkt_baseline tests/gam_kt tests/shared_kt
```

Kết quả kiểm tra gần nhất trong workspace: **43 passed**. Kiểm tra whitespace:

```powershell
git diff --check
```

Bootstrap command đã dùng với artifact Development CV đã lưu:

```powershell
.\venv\Scripts\python.exe scripts/bootstrap_bkt_gam_cv.py --replicates 1000 --seed 20261030 --output reports/paired_cluster_bootstrap_bkt_gam.json
```

Lệnh bootstrap đọc predictions đã lưu; nó không fit model hay chạy lại CV. JSON giữ số dòng join/common-row/fallback theo fold cùng estimate và CI.

### Commit và trạng thái thay đổi

HEAD khi bắt đầu tổng hợp report là `df39ff1 feat(gam-kt): integrate Junyi development benchmark`. Trước khi tạo report, working tree đã có các untracked Sprint 2 deliverables: `docs/bkt-gam-kt-benchmark.md`, `docs/kt-data-semantics.md`, `reports/paired_cluster_bootstrap_bkt_gam.json`, `scripts/bootstrap_bkt_gam_cv.py`, `src/knowledge_tracing/paired_bootstrap.py`, `src/knowledge_tracing/shared_kt.py` và `tests/shared_kt/`. Chúng có trước task tài liệu này; report không commit hay chỉnh sửa các thay đổi đó. File report này là output mới của task.

Không huấn luyện model, không chạy lại Development CV, không truy cập/đánh giá Holdout và không triển khai model mới trong lần tổng hợp này.

## Tài liệu tham khảo

1. C. Piech, J. Bassen, J. Huang, S. Ganguli, M. Sahami, L. Guibas và J. Sohl-Dickstein. “Deep Knowledge Tracing.” NeurIPS, 2015. Bản PDF trong `papers/Deep Knowledge Tracing.pdf`.
2. Z. Liu, Q. Liu, J. Chen, S. Huang, J. Tang và W. Luo. “pyKT: A Python Library to Benchmark Deep Learning based Knowledge Tracing Models.” NeurIPS Datasets and Benchmarks Track, 2022.
3. G. Abdelrahman, Q. Wang và B. Nunes. “Knowledge Tracing: A Survey.” ACM Computing Surveys, 55(11), 2023.
4. S. Shen, Q. Liu, Z. Huang, Y. Zheng, M. Yin, M. Wang và E. Chen. “A Survey of Knowledge Tracing: Models, Variants, and Applications.” IEEE Transactions on Learning Technologies, 17, 1898–1919, 2024. Tóm tắt thư mục và taxonomy trong `papers/KT Papers Survey Report.md`.
5. CAHLR. `pyBKT` 1.4.3, vendored source và local patch provenance tại `docs/pybkt-provenance.md`.
