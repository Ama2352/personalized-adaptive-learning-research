# KT Papers Survey Report

## 1. Knowledge Tracing là bài toán gì?

**Knowledge Tracing (KT)** là bài toán theo dõi sự thay đổi của **trạng thái kiến thức của người học theo thời gian** dựa trên lịch sử tương tác của họ với hệ thống học tập, từ đó dự đoán performance trong các tương tác tiếp theo [1][3][4].

Một interaction cơ bản thường được biểu diễn bằng:

```
(question / exercise, response)
```

Ví dụ:

```
Fractions ✓ → Algebra ✗ → Fractions ✓ → ...
```

Từ history đó, KT model ước lượng knowledge state hiện tại và dự đoán xác suất learner trả lời đúng câu hỏi hiện tại hoặc tiếp theo.

$$
P(y_t = 1 \mid q_t, X_{1:t-1})
$$

Trong đó:

- `$q_t$`: question/exercise tại thời điểm `t`
- `$X_{1:t-1}$`: toàn bộ interaction history trước thời điểm `t`
- `$y_t$ = 1`: learner trả lời đúng
- Output: xác suất learner trả lời đúng

Original DKT paper formalize KT theo hướng: từ các interactions trước của một student, dự đoán interaction tiếp theo; trường hợp phổ biến nhất là biết exercise hiện tại và dự đoán learner sẽ trả lời đúng hay sai [1].

### Tại sao sequence quan trọng?

KT không chỉ hỏi:

> Student này giỏi đến đâu?
> 

Mà quan trọng hơn là:

> Knowledge state của student thay đổi như thế nào sau từng interaction?
> 

Ví dụ:

```
Student A:
Wrong → Wrong → Correct → Correct

Student B:
Correct → Correct → Wrong → Wrong
```

Cả hai đều có `2 correct + 2 wrong`, nhưng learning trajectory khác nhau. Vì vậy **interaction order / sequence** là thành phần cốt lõi của KT [1][3].

Timestamp có thể được dùng để reconstruct đúng order hoặc làm temporal feature cho một số model, nhưng không phải mọi KT model đều cần raw timestamp làm input.

### Input của KT có thể rộng hơn question + response

Ngoài exercise/KC và correctness, learning systems còn có thể ghi nhận:

```
response time
difficulty
hints
opportunity count
engagement
timestamp / time gap
question text
KC relationships / prerequisite graph
...
```

Các KT variants sử dụng những thông tin này để model thêm các yếu tố như **forgetting, learner individualization, engagement, difficulty hoặc relationship giữa knowledge concepts** [3][4].

### KT không chỉ là next-response prediction

Prediction là cách phổ biến để đánh giá knowledge state mà model đã học:

```
Interaction history
        ↓
   KT Model
        ↓
Estimated knowledge state
        ↓
   P(correct next)
```

Nhưng knowledge state còn có thể được dùng cho:

- personalized learning;
- exercise/resource recommendation;
- adaptive learning paths;
- curriculum design;
- khám phá relationships giữa exercises/KCs [1][3][4].

### Tóm tắt

> **Knowledge Tracing sử dụng ordered learning history để duy trì một representation của learner's evolving knowledge state và dùng state đó để dự đoán future learning performance.**
> 

```
Learning history
(q1, ✓) → (q2, ✗) → (q3, ✓)
                  ↓
               KT Model
                  ↓
        Estimated knowledge state
                  ↓
             P(correct q4)
                  ↓
      Personalization / recommendation
```

---

## 2. Các hướng model chính trong Knowledge Tracing

Qua các survey, KT có thể được nhìn thành hai nhóm lớn: **Traditional KT** và **Deep Learning KT** [3][4]. Traditional KT thường biểu diễn knowledge state bằng các giả định/xác suất hoặc các yếu tố được định nghĩa rõ, trong khi DLKT học một **latent representation** trực tiếp từ learning history. 

### 2.1. Tổng quan các model family

| Family | Representative models | Knowledge representation | Ý tưởng chính | Data cần |
| --- | --- | --- | --- | --- |
| **Bayesian** | BKT, DBKT | Probability trên mastery state | Theo dõi xác suất learner đã master từng KC | KC, response, interaction order |
| **Factor Models** | IRT, AFM, PFA, KTM | Explicit factors | Model ability, difficulty, practice, success/failure | Student, item/KC, response; practice history tùy model |
| **Sequential** | DKT, DKT+, DKT-F, KQN | Continuous hidden state | Học knowledge state từ ordered interaction sequence | Question/KC, response, sequence |
| **Memory-based** | DKVMN | Key-value memory | Lưu knowledge state theo các latent KCs trong memory | Sequence, question/KC, response |
| **Attention-based** | SAKT, AKT, SAINT | Attention-weighted history | Xác định past interactions nào relevant nhất cho prediction hiện tại | Ordered interaction history |
| **Graph-based** | GKT, GIKT, SKT | Knowledge states + graph structure | Khai thác dependency giữa KCs/questions | Sequence + graph/relation information |
| **Robustness variants** | ATKT | Neural latent state | Cải thiện generalization bằng adversarial training | Basic KT sequence |

pyKT chọn các representative DLKT models bằng cách khảo sát các baseline thường xuất hiện trong top AI/ML venues, sau đó chia thành sequential, memory, adversarial, graph và attention-based approaches [2].

---

### 2.2. Traditional Knowledge Tracing

#### Bayesian models

**BKT** biểu diễn mastery của một KC bằng latent state dạng:

```
Learned / Unlearned
```

và duy trì một probability learner đang ở trạng thái `Learned`.

Model sử dụng các tham số như:

```
Initial mastery
Learning / transition
Guess
Slip
```

Sau mỗi response:

```
Previous mastery probability
        +
Correct / Incorrect
        ↓
Bayesian update
        ↓
New mastery probability
```

Ưu điểm chính là **đơn giản và dễ diễn giải**, nhưng binary latent state tạo ra representation khá hạn chế so với complexity của knowledge thực tế [1][3].

#### Factor models

Factor models nhìn KT theo hướng khác: prediction được tạo từ một tập các explicit factors, ví dụ:

```
Student ability
Item difficulty
Practice count
Previous successes
Previous failures
```

Một số representative approaches:

```
IRT → ability + item difficulty
AFM → thêm practice
PFA → tách previous successes / failures
KTM → hỗ trợ nhiều factors và interactions
```

Khác với BKT, chúng không nhất thiết duy trì một binary mastery state; thay vào đó prediction được tạo từ các factors có ý nghĩa cụ thể [3].

---

### 2.3. Deep Sequential Models

**DKT** là model tiêu biểu mở đầu hướng Deep Learning KT [1].

Thay vì:

```
KC → Learned / Unlearned
```

DKT dùng một continuous hidden vector:

```
Interaction sequence
        ↓
      LSTM
        ↓
Hidden knowledge state h_t
        ↓
   P(correct next)
```

Representation này được **learn từ data**, không cần con người định nghĩa trước từng factor hoặc latent concept [1]. Original DKT paper nhấn mạnh việc dùng RNN để học representation linh hoạt hơn và không bắt buộc explicit expert knowledge encoding. 

Các variants tiếp tục mở rộng ý tưởng này:

- **DKT+**: xử lý một số vấn đề về reconstruction và prediction consistency.
- **DKT-F**: thêm forgetting-related information.
- **KQN**: tách representation của student knowledge state và skill rồi đo compatibility giữa chúng [2].

---

### 2.4. Memory-based Models

**DKVMN** thay vì nén toàn bộ knowledge của learner vào một hidden vector duy nhất, sử dụng external memory:

```
Key Memory
→ representations / relations của KCs

Value Memory
→ evolving mastery state của learner
```

Khi learner interaction với một question:

```
Question
   ↓
Attention over memory
   ↓
Read relevant knowledge
   ↓
Predict response
   ↓
Update memory
```

Mục tiêu là tạo knowledge representation có cấu trúc hơn và cho phép đọc/ghi mastery theo từng latent knowledge component [2][3].

---

### 2.5. Attention-based Models

Attention-based KT thay đổi chủ yếu **cách khai thác learning history**.

Thay vì information phải truyền tuần tự qua toàn bộ RNN:

```
t1 → t2 → t3 → t4
```

attention cho phép current question trực tiếp xem các past interactions:

```
Past interaction 1 ── weight ─┐
Past interaction 2 ── weight ─┼→ Context → Prediction
Past interaction 3 ── weight ─┘
```

Representative models:

- **SAKT**: self-attention trên interaction history.
- **AKT**: attention kết hợp temporal/monotonic effects và Rasch-inspired representation.
- **SAINT**: Transformer encoder-decoder cho question và response sequences [2][3].

Ý tưởng chính là:

> Không phải mọi past interaction đều quan trọng như nhau đối với current question.
> 

---

### 2.6. Graph-based Models

Graph-based KT đưa thêm **structural relationships giữa KCs/questions** vào model:

```
Fractions
    ↓
Algebra
    ↓
Equations
```

Learning history vẫn được sử dụng, nhưng knowledge state còn được truyền qua graph:

```
Interaction sequence
        +
   KC / Question graph
        ↓
Graph message passing
        ↓
Knowledge representation
        ↓
P(correct)
```

Representative models:

- **GKT**: graph giữa knowledge concepts.
- **GIKT**: khai thác question–KC structure.
- **SKT**: hỗ trợ nhiều loại relationships giữa KCs [3].

Graph-based approaches đặc biệt relevant khi dataset có prerequisite, similarity hoặc các relation structures đáng tin cậy.

---

### 2.7. Các model khác nhau chủ yếu ở đâu?

Có thể tóm lại evolution của KT như sau:

```
BKT
Explicit probabilistic mastery
        ↓

Factor Models
Add explicit learner/item/practice factors
        ↓

DKT
Learn latent knowledge state from sequence
        ↓

DKVMN
Store knowledge in structured memory
        ↓

SAKT / AKT / SAINT
Select relevant history using attention
        ↓

GKT / GIKT / SKT
Add structural relations between KCs/questions
```

Điểm quan trọng là các model mới **không đơn giản chỉ “thêm nhiều parameters hơn”**. Chúng thay đổi cách represent hoặc process knowledge:

```
DKT      → How to encode history?
DKVMN    → Where to store knowledge?
Attention→ Which history matters?
GKT      → How does knowledge propagate between related KCs?
```

Survey của Shen et al. cũng tổ chức DLKT theo recurrent, memory, attention và graph architectures, đồng thời nhấn mạnh rằng các KT variants còn khác nhau ở assumptions về individualization, engagement, forgetting và side information [4]. 

### Tóm tắt

> **KT models phát triển từ các explicit probabilistic/factor representations sang learned latent representations. Các DLKT families khác nhau chủ yếu ở cách chúng encode interaction history, lưu knowledge state, lựa chọn relevant history và khai thác relationships giữa knowledge concepts.**
> 

---

## 3. Benchmark Knowledge Tracing được xây dựng như thế nào?

Một **benchmark KT** không chỉ là chọn một dataset rồi chạy nhiều models. Để kết quả có thể so sánh, các models cần được đánh giá dưới **cùng preprocessing, data split, prediction task, tuning protocol và metrics** [2][3].

pyKT được xây dựng chính vì KT literature trước đó thiếu sự chuẩn hóa: cùng một model trên cùng dataset vẫn có thể cho reported AUC rất khác nhau do preprocessing và evaluation protocol khác nhau [2]. 

### 3.1. Benchmark pipeline

```
Raw interaction data
        ↓
Preprocessing
        ↓
Build student sequences
        ↓
Train / Validation / Test split
        ↓
Train & tune models
        ↓
Predict future responses
        ↓
Evaluate with the same metrics
        ↓
Compare models
```

Mục tiêu là giữ các yếu tố bên ngoài model càng nhất quán càng tốt, để difference trong kết quả chủ yếu phản ánh **difference giữa các approaches**.

---

### 3.2. Dataset & preprocessing

Các KT benchmarks thường sử dụng public educational datasets như:

```
ASSISTments
Algebra
Bridge
Statics
NIPS34
POJ
Junyi
...
```

pyKT sử dụng 7 datasets thuộc nhiều domains và áp dụng cùng một preprocessing procedure [2].

Các bước preprocessing điển hình gồm:

```
Remove missing / invalid interactions
        ↓
Remove unusable student histories
        ↓
Reconstruct chronological order
        ↓
Build question / KC sequences
        ↓
Truncate / pad sequences if needed
```

Preprocessing đặc biệt quan trọng trong KT vì model phụ thuộc vào **interaction sequence**. Duplicate records, incorrect timestamps hoặc cách mapping questions–KCs khác nhau có thể thay đổi benchmark result đáng kể [3].

Survey literature cũng cảnh báo rằng reported results không nên được so trực tiếp nếu dataset subsets hoặc preprocessing settings khác nhau [3].

---

### 3.3. Data split

KT thường split data ở **student level**, thay vì random từng interaction.

Ví dụ pyKT [2]:

```
All students
    │
    ├── 20% → Test
    │
    └── 80%
          ↓
       5 folds
       Train / Validation
```

Lý do là nếu interactions của cùng một student xuất hiện ở cả train và test:

```
Student A

Train: q1 → q2 → q4
Test:       q3 → q5
```

thì train/test không còn độc lập hoàn toàn.

Student-level split giúp benchmark gần với câu hỏi:

> Model đã học từ previous learners có generalize sang unseen learners không?
> 

---

### 3.4. Prediction task phải được định nghĩa rõ

pyKT phân biệt hai settings [2]:

**One-step ahead prediction**

```
q1 → q2 → q3 → q4 → ?

                  predict q5
```

Dùng history để dự đoán **response tiếp theo**.

**Multi-step ahead prediction**

```
q1 → q2 → q3 → ? → ? → ?
```

Dùng một phần history để dự đoán **nhiều future responses**.

Main benchmark của pyKT chủ yếu sử dụng one-step prediction; original DKT cũng tập trung vào dự đoán response tiếp theo [1][2].

Ngoài ra cần xác định evaluation ở:

```
Question level
```

hay

```
KC level
```

vì một question có thể liên quan tới nhiều KCs.

---

### 3.5. Evaluation metrics

KT model thường output:

```
P(correct)
```

Literature dùng nhiều nhóm metric khác nhau:

| Mục tiêu | Metrics |
| --- | --- |
| **Ranking / discrimination** | AUC-ROC |
| **Binary classification** | Accuracy, Precision, Recall, F1 |
| **Probability quality** | Log Loss, Brier, RMSE, MAE |
| **Calibration** | ECE |

Trong các paper đã khảo sát, **AUC là metric phổ biến nhất**. Original DKT sử dụng AUC trên cả ba datasets [1], còn pyKT dùng **AUC làm main metric và Accuracy làm supplementary metric** [2].

Điểm quan trọng là không có một metric duy nhất mô tả toàn bộ model quality:

```
AUC
→ ranking tốt không?

Accuracy / F1
→ binary decision tốt không?

Log Loss / Brier
→ predicted probability tốt không?

ECE
→ confidence có calibrated không?
```

---

### 3.6. Hyperparameter tuning phải công bằng

Không thể benchmark công bằng nếu:

```
Model A → tune rất kỹ
Model B → default parameters
```

pyKT chuẩn hóa hyperparameter search và dùng validation AUC cho model selection/early stopping [2].

Do đó một fair benchmark nên giữ chung:

```
Same Train / Validation / Test
Same tuning budget
Same model-selection metric
Same stopping rule
Test set not used for tuning
```

---

### 3.7. Leakage control

Một trong những findings quan trọng nhất của pyKT là **evaluation design sai có thể gây label leakage và inflated performance** [2].

Ví dụ một question có:

```
Question Q
├── KC1
├── KC2
└── Response = Correct
```

Nếu expand thành:

```
KC1 → Correct
KC2 → Correct
```

và model được thấy response của `KC1` trước khi dự đoán `KC2`, thì `KC1` và `KC2` thực chất chia sẻ cùng response của một question.

```
Ground-truth information
        ↓
leaks into prediction
        ↓
AUC artificially increases
```

Vì vậy benchmark phải đảm bảo model chỉ sử dụng **information hợp lệ tại thời điểm prediction**.

---

### 3.8. Những yếu tố benchmark nâng cao

pyKT còn cho thấy performance có thể phụ thuộc vào:

- **short vs long student histories**;
- cách aggregate predictions khi một question có nhiều KCs;
- **one-step vs multi-step** prediction;
- accumulative vs non-accumulative multi-step prediction [2].

Điều này cho thấy một leaderboard score duy nhất chưa chắc mô tả đầy đủ model behavior.

---

### Tóm tắt

Một KT benchmark hợp lý có thể được tóm tắt như sau:

```
1. Choose dataset
        ↓
2. Standardize preprocessing
        ↓
3. Build chronological student sequences
        ↓
4. Split Train / Validation / Test
        ↓
5. Define prediction task
        ↓
6. Train & tune models fairly
        ↓
7. Prevent information leakage
        ↓
8. Evaluate with common metrics
        ↓
9. Compare results
```

> **Benchmark KT không chỉ là chạy nhiều models trên cùng dataset. Fair comparison yêu cầu thống nhất preprocessing, student split, prediction setting, available information, tuning procedure và evaluation metrics.**
> 

---

## 4. Những kết luận chính từ literature

Sau khi tổng hợp các model papers, benchmark paper và surveys, có một số kết luận quan trọng hơn việc chỉ nhìn vào leaderboard của từng model.

### 4.1. Deep Learning mở rộng đáng kể cách biểu diễn knowledge state

Original DKT cho thấy knowledge state không nhất thiết phải được mô hình hóa bằng các discrete assumptions như BKT. RNN/LSTM có thể học một **continuous latent representation** trực tiếp từ interaction sequence và trong benchmark gốc cho kết quả prediction cao hơn BKT [1]. 

Điều này mở ra các hướng DLKT sau đó:

```
Sequence → DKT
Memory   → DKVMN
Attention→ SAKT / AKT
Graph    → GKT / GIKT
```

Tuy nhiên, architecture phức tạp hơn không đồng nghĩa chắc chắn performance tốt hơn.

---

### 4.2. Model mới không nhất thiết vượt xa DKT

Một finding đáng chú ý của pyKT là khi **preprocessing và evaluation được standardized**, phần lớn các DLKT approaches mới chỉ cải thiện tương đối nhỏ so với vanilla DKT [2]. pyKT cũng ghi nhận AKT là một trong những models mạnh nhất trong benchmark của họ, nhưng advantage thay đổi theo dataset và information available.

Điều này gợi ý rằng:

> Không nên chọn model chỉ dựa trên độ mới hoặc complexity; model cần được đánh giá dưới cùng benchmark protocol.
> 

---

### 4.3. Evaluation protocol có thể ảnh hưởng kết quả mạnh như model architecture

pyKT phát hiện một số evaluation settings ở KC-level có thể gây **label leakage**, khiến AUC tăng giả [2].

Ví dụ:

```
Question Q
├── KC1
├── KC2
└── Response = Correct
```

Nếu model đã nhìn thấy response của `KC1` trước khi predict `KC2`, trong khi cả hai thực chất thuộc cùng một question:

```
Ground truth
    ↓
leaks into model input
    ↓
Inflated performance
```

Đây là một finding quan trọng vì nó cho thấy:

> Một model có reported score cao chưa chắc thực sự tốt hơn nếu evaluation protocol không hợp lệ.
> 

pyKT được xây dựng chính để giải quyết vấn đề preprocessing và evaluation không standardized, đồng thời authors chỉ ra wrong evaluation settings có thể gây performance inflation [2]. 

---

### 4.4. Dataset và preprocessing ảnh hưởng trực tiếp đến kết quả benchmark

Các survey chỉ ra rằng cùng một model + cùng tên dataset vẫn có thể cho kết quả khác nhau do [3]:

```
Different dataset versions
Different subsets
Different preprocessing
Duplicate interactions
Noise / missing values
Question–KC mapping
Sequence reconstruction
```

Do đó các AUC lấy từ hai papers khác nhau **không nên được so trực tiếp** nếu experimental setup không giống nhau.

Điều này đặc biệt quan trọng với KT vì chronological interaction sequence là một phần của input; sai timestamp hoặc preprocessing có thể làm thay đổi chính history mà model nhìn thấy.

---

### 4.5. Dataset characteristics quyết định model nào có lợi thế

pyKT cho thấy performance không chỉ phụ thuộc architecture mà còn phụ thuộc vào characteristics của data [2]:

- có question information hay không;
- có KC information hay không;
- một question chứa bao nhiêu KCs;
- learner histories dài hay ngắn;
- domain là mathematics hay programming;
- lượng historical information available.

Ví dụ attention mechanism hoặc question-difficulty representation có thể hữu ích khi dataset cung cấp đủ question/KC information, nhưng advantage có thể giảm khi những signals đó không tồn tại.

Vì vậy:

```
Model performance
      ≠
architecture only
```

mà gần hơn với:

```
Model performance
      =
Model
+ Dataset characteristics
+ Preprocessing
+ Evaluation protocol
```

---

### 4.6. Một overall score chưa mô tả hết model behavior

pyKT còn phân tích learner có **short history và long history** và nhận thấy performance có thể khác đáng kể giữa hai nhóm [2].

Điều này cho thấy chỉ report:

```
AUC = 0.82
```

có thể che mất:

```
Cold / short-history learners → ?
Long-history learners        → ?
Multi-KC questions           → ?
Multi-step prediction        → ?
```

Do đó ngoài overall metrics, subgroup hoặc scenario-specific evaluation có thể giúp hiểu model rõ hơn.

---

### 4.7. Prediction performance không phải toàn bộ mục tiêu của KT

Các survey nhấn mạnh rằng KT cuối cùng muốn **tracing learner knowledge state**, trong khi next-response prediction chỉ là cách phổ biến để gián tiếp đánh giá state đó [3][4].

Knowledge state còn có thể phục vụ:

```
Exercise recommendation
Adaptive learning
Learning path planning
Curriculum design
Knowledge diagnosis
```

Survey của Shen et al. cũng chỉ ra limitation của current evaluation: phần lớn tập trung vào student performance prediction, trong khi score này chưa trực tiếp phản ánh effectiveness của KT trong practical educational applications [4].

Vì vậy một model có AUC cao hơn chưa tự động đồng nghĩa với:

> learner sẽ học tốt hơn khi model đó được đưa vào learning system.
> 

---

## Key Takeaways

Có thể cô đọng literature thành 5 ý chính:

> **1.** DLKT cho phép học knowledge representation linh hoạt hơn các traditional models [1].
> 
> 
> **2.** Model phức tạp hoặc mới hơn không đảm bảo improvement lớn; DKT vẫn là baseline mạnh [2].
> 
> **3.** Benchmark protocol và leakage control có ảnh hưởng rất lớn đến reported performance [2].
> 
> **4.** Dataset characteristics và preprocessing phải được xem xét trước khi so sánh models [2][3].
> 
> **5.** Predictive performance chỉ là một góc của KT; practical usefulness và knowledge-state quality cũng quan trọng [3][4].
> 

```
Better KT research
      ↓
Not only
"Which model has highest AUC?"

But also
      ↓
Was comparison fair?
Does the dataset support the model?
Does it generalize across learners/scenarios?
Is the estimated knowledge state useful?
```

---

## 5. Implications for Our Study

Từ các nghiên cứu đã tổng hợp, mục tiêu tiếp theo không nên là tìm một **“best KT model”** từ reported results. Các survey cho thấy cùng model và dataset vẫn có thể cho kết quả khác nhau do preprocessing và experimental settings; pyKT cũng được xây dựng chính để giải quyết vấn đề thiếu standardized evaluation này [2][3]. 

Do đó, literature review này dẫn đến một số định hướng chính cho nghiên cứu tiếp theo.

### 5.1. Chọn representative models thay vì implement tất cả

KT literature có rất nhiều models và variants. Thay vì benchmark toàn bộ, nên chọn một số models đại diện cho các hướng modeling khác nhau:

```
Traditional
    ↓
BKT / Factor-based

Sequential
    ↓
DKT

Attention
    ↓
SAKT / AKT

Graph
    ↓
GKT / related variants
```

Cách chọn theo representative families cũng tương tự cách pyKT xây benchmark của họ với các sequential, memory, adversarial, graph và attention-based approaches [2].

Mục tiêu là so sánh **các cách represent và model learner knowledge khác nhau**, thay vì tạo một leaderboard với càng nhiều models càng tốt.

---

### 5.2. Xây một common benchmark protocol

Tất cả selected models nên được đánh giá trên cùng một experimental pipeline:

```
Common Dataset
      ↓
Common Preprocessing
      ↓
Same Train / Validation / Test Split
      ↓
Same Prediction Task
      ↓
Fair Hyperparameter Tuning
      ↓
Same Evaluation Metrics
      ↓
Model Comparison
```

Đặc biệt cần đảm bảo:

- student-level data split;
- chronological interaction sequences;
- cùng definition của prediction target;
- không sử dụng future/current response trước prediction;
- test set không tham gia model selection;
- preprocessing và filtering được report rõ.

Điều này giúp kết quả phản ánh model differences thay vì differences do experimental setup [2][3]. 

---

### 5.3. Không chỉ dựa vào một metric

AUC là metric phổ biến trong KT literature [1][2][3], nhưng nó chủ yếu đánh giá khả năng **discriminate/rank correct và incorrect responses**.

Một benchmark rộng hơn có thể kết hợp:

```
AUC
→ discrimination / ranking

Accuracy
→ binary prediction

Log Loss / Brier
→ probability quality

ECE
→ probability calibration
```

Việc lựa chọn metrics cuối cùng nên phụ thuộc vào research question. Nếu output của KT được sử dụng như một probability hoặc knowledge estimate, chỉ nhìn Accuracy/AUC có thể chưa mô tả đầy đủ chất lượng prediction.

---

### 5.4. Dataset characteristics cần được xem xét cùng model performance

Model performance không tồn tại độc lập với dataset:

```
Model
  +
Sequence characteristics
  +
Question / KC information
  +
Data sparsity
  +
Available side information
  +
Preprocessing
  ↓
Observed performance
```

Do đó trước khi benchmark cần profiling dataset để xác định những signals thực sự có sẵn và model nào có thể sử dụng chúng.

Ví dụ, graph-based KT chỉ thực sự kiểm tra được contribution của structural knowledge nếu dataset có một graph/relation structure phù hợp; temporal variants cần temporal information; question/KC-aware models phụ thuộc vào mapping tương ứng.

Survey cũng cho thấy preprocessing có thể làm thay đổi đáng kể số interactions và characteristics của cùng một KT dataset [3].

---

### 5.5. Evaluation phải chú ý đến leakage và robustness

pyKT cho thấy một evaluation setup không phù hợp có thể gây **label leakage và inflated performance** [2].

Do đó benchmark cần kiểm tra:

```
Is current/future information leaked?
            ↓
Is question–KC expansion safe?
            ↓
Are train/test students separated?
            ↓
Does performance remain stable
across different learner histories?
```

Ngoài overall result, có thể phân tích thêm các conditions như:

- short vs long interaction histories;
- sparse vs dense learners/items;
- single-KC vs multi-KC questions;
- one-step vs multi-step prediction.

Những phân tích này giúp xác định **khi nào một model hoạt động tốt**, thay vì chỉ biết average score của nó.

---

### 5.6. Proposed research direction

Từ literature review, workflow nghiên cứu tiếp theo có thể được cô đọng thành:

```
Understand dataset
      ↓
Select representative KT models
      ↓
Define common preprocessing
      ↓
Define fair benchmark protocol
      ↓
Select complementary metrics
      ↓
Run models under the same conditions
      ↓
Analyze overall + subgroup results
      ↓
Determine which modeling assumptions
are actually useful for the dataset
```

Điểm quan trọng là:

> **Mục tiêu không phải chọn model dựa trên reported scores từ các paper, mà xây một controlled benchmark để kiểm tra các representative KT approaches dưới cùng điều kiện.**
> 

Kết quả benchmark sau đó mới cung cấp cơ sở để xác định model family, representation hoặc additional information nào thực sự có giá trị cho bài toán đang nghiên cứu.

---

## References

**[1]** C. Piech, J. Bassen, J. Huang, S. Ganguli, M. Sahami, L. Guibas, and J. Sohl-Dickstein. *Deep Knowledge Tracing*. Advances in Neural Information Processing Systems (NeurIPS), 2015.

**[2]** Z. Liu, Q. Liu, J. Chen, S. Huang, J. Tang, and W. Luo. *pyKT: A Python Library to Benchmark Deep Learning based Knowledge Tracing Models*. NeurIPS 2022, Datasets and Benchmarks Track. 

**[3]** G. Abdelrahman, Q. Wang, and B. Nunes. *Knowledge Tracing: A Survey*. ACM Computing Surveys, Vol. 55, No. 11, 2023. 

**[4]** S. Shen, Q. Liu, Z. Huang, Y. Zheng, M. Yin, M. Wang, and E. Chen. *A Survey of Knowledge Tracing: Models, Variants, and Applications*. IEEE Transactions on Learning Technologies, Vol. 17, pp. 1898–1919, 2024.