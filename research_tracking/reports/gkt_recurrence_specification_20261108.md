# GKT: đặc tả recurrence có thể triển khai để review — 08/11/2026

**Có thể triển khai full recurrent core ngay sau khi reviewer chấp nhận một recipe được ghi rõ; chưa đủ căn cứ gọi đó là exact author implementation.** Điểm chặn thực sự là phép chuyên biệt hóa erase–add của DKVMN thành unary gate trong GKT, không phải thiếu thư viện hay không thể viết recurrence. Đề xuất dưới đây đóng từng phép toán cho một engineering fixture; không chọn baseline variant/hyperparameters/protocol S05.

Đây là follow-up của [source plan](gkt_source_and_core_plan_20261108.md) và [Batch A43tests](gkt_core_readiness_20261108.md). Chỉ đọc nguồn/local metadata, tìm12queries trong3web-search calls và mở nguồn sơ cấp có mục tiêu. Không sửa source/tests GKT hoặc native AKT, không model/data/GPU/install/Git. [Source map](gkt_recurrence_specification_20261108.sources.json) phân biệt primary facts, suy luận, proposal và SHA local; chưa đóng immutable bundle.

## 1. Thu hẹp bằng chứng: không trộn các revision

| Nguồn sơ cấp | Anchor đã đọc | Kết luận hẹp |
|---|---|---|
| [Workshop manuscript](https://rlgm.github.io/papers/70.pdf) | PDF pp.2–3 §2.1–2.2, Eq.(1)–(2); p.7 Appendix B | Aggregate→message→unary erase–add→GRU; graph đọc hai chiều; output node đích dùng dự báo bước kế. [Accepted list](https://rlgm.github.io/papers/) xác nhận workshop, không main track |
| [Journal2021 PDF](https://journals.sagepub.com/doi/pdf/10.3233/WEB-210458) | Printed pp.91–92 §3.1–3.3, pp.95–96 §4.2.2/4.3 | Xác nhận chỉ cập nhật answered/related nodes, đọc state đích; gộp simultaneous tags; MLP hai lớp ELU/dropout/BN output. Không tìm thấy h0 hoặc gate mapping cụ thể |
| [JSAI2019, cùng ba tác giả](https://www.jstage.jst.go.jp/article/pjsai/JSAI2019/0/JSAI2019_1Q3J203/_pdf/-char/en) | PDF p.2 §3.1, Eq.(1) và đoạn ngay dưới | Revision riêng có average+tanh cho simultaneous concepts và nói bỏ bias ở erase–add/GRU. Không nhập chi tiết này vào journal như thể cùng một specification |
| [DKVMN v2](https://arxiv.org/html/1611.08108) | §3.2.3, Eq.(6)–(9); [version page](https://arxiv.org/abs/1611.08108) | Write cần prior memory, write input và write weight. Cung cấp đại số erase/add, chưa chỉ ra cách GKT gán ba vai trò đó cho một message |
| [Cho2014 v3](https://arxiv.org/html/1406.1078v3) | §2.3, Eq.(5)–(8) | Reset đặt trước hidden matrix trong candidate. [PyTorch2.7 GRUCell](https://docs.pytorch.org/docs/2.7/generated/torch.nn.GRUCell.html) đặt reset sau hidden affine; hai phép toán không đồng nhất tổng quát |

Journal PDF16trang đã đọc qua web extraction, nên nay có printed page anchors; chưa tải raw PDF/HTML bytes, không có external-byte SHA. Không claim visual screenshot review: screenshot request không cung cấp ảnh để kiểm trong lượt này. Supplement endpoint không truy cập được; HTML không tìm thấy `Supplement`, `initial` hoặc `code`. Không chứng minh supplement/code không tồn tại ở nơi khác. Search bounded chưa xác minh author-official GKT code; không dùng/copy `jhljx/GKT` hoặc nâng provenance của repo đó. Trang lab tác giả được search tìm thấy nhưng direct-open lỗi; không dùng nội dung trang đó để lấp gate.

**Phát hiện mới có ích:** sparse support được mô tả rõ hơn bởi journal §3.1 và JSAI, nhưng G_ea vẫn thiếu mapping; JSAI bổ sung chi tiết **khác revision**, không phải lời giải tự động cho journal. BN axes/placement và h0 vẫn chưa được xác định duy nhất. Không cần tiếp tục tìm không giới hạn để thừa nhận ranh giới này.

## 2. Những gì Batch A đã cho phép chốt

Giữ nguyên `StaticGKTKernel`, directed message arithmetic, binding/domain/node order và actual A hash. Không sửa kernel đã archive. Quy ước chỉ số repo: H_t là state **trước khi quan sát** response t. Với query i_t:

```text
score_t = sigmoid(w_out · H_t[i_t] + b[i_t])
z_i = [H_t[i_t], E_x[i_t + N*r_t]]       # chỉ sau observe
z_j = [H_t[j], E_c[j]]                  # j khác i_t
m_i = f_self(z_i)
m_j = A[i,j]*f_out([z_i,z_j]) + A[j,i]*f_in([z_i,z_j])
```

Đây là reindexing của workshop §2.1–2.2, không đổi target sang response vừa dùng để update. Không query embedding/readout của neighbor làm thêm attention hay đưa graph vào prediction head. Graph được dùng khi update; score vẫn correctness, không phải P(K), calibrated mastery hoặc causal prerequisite strength.

Support của node j được đề xuất đóng bằng `j==i OR A[i,j]!=0 OR A[j,i]!=0`. Sau GRU phải dùng `where(support, proposed_H, old_H)`; message0 **không** đủ giữ node cô lập nếu gate/GRU có bias hoặc dynamics riêng. Đây là phép operationalize neighborhood từ source, không edge threshold học mới. `A!=0` là đúng support của matrix caller đã cung cấp; không tự normalize, symmetrize, threshold hoặc thêm self-edge. Dense N>1 cập nhật mọi node; empty graph chỉ cập nhật answered node.

## 3. Chốt đúng chỗ còn thiếu: một recipe đề nghị, chưa adoption

Recipe ID đề nghị: **`gkt_static_recurrent_convention_v1`**. Tên phải có trong config/checkpoint metadata tương lai; không gọi là tác giả đã xác nhận. Chỉ hỗ trợ một known concept/exercise-tag cho mỗi event, binary response và static A đã bind. Không fit graph hoặc biến multi-tag thành nhiều pseudo-timesteps.

### 3.1. G_ea: lựa chọn toán học phải review

DKVMN viết `erase=σ(Eᵀv+b_e)`, `add=tanh(Dᵀv+b_a)`, `M_new=M_old*(1-w*erase)+w*add`. GKT chỉ viết `G_ea(m)`. Không thể suy ra duy nhất M_old, v và w từ unary notation đó. Do đó, dùng h_old làm memory, dùng learned node write weight hoặc bỏ gate đều là lựa chọn thêm, không dữ kiện paper đã chốt.

**Một specialization tối thiểu đề nghị:** đặt **M_old=m, v=m, w=1**, dùng elementwise gate cùng message dimension H:

```text
e(m) = sigmoid(W_e*m + b_e)       # W_e: H×H; b_e: H
a(m) = tanh(W_a*m + b_a)          # W_a: H×H; b_a: H
u(m) = m*(1-e(m)) + a(m)
```

Không tạo thêm memory state hoặc learned node scalar ngoài graph. Đúng hình dạng unary, có erase và add; **mapping M_old=v=m, w=1 là suy luận thiết kế của repo**, không công thức GKT được primary source xác nhận. Cần review công khai trước code; thiếu source không biến mapping này thành “routine tensor wiring”. Nếu mục tiêu bắt buộc exact author recurrence/checkpoint parity, đây vẫn là blocker thực và phải lấy author specification/code; unit tests không giải quyết được identifiability.

### 3.2. GRU: chọn rõ reset convention

Để không âm thầm dựa PyTorch variant, fixture đề nghị dùng literal Cho2014 reset-before, bias-free như Eq.(5)–(8), φ=tanh:

```text
r = sigmoid(W_r*u + U_r*h)
z = sigmoid(W_z*u + U_z*h)
n = tanh(W_n*u + U_n*(r*h))
g = z*h + (1-z)*n
H_next = where(support, g, H_old)
```

Các W/U có shape H×H, dùng chung theo node/learner. `r*(U_n*h)` của PyTorch không thay được `U_n*(r*h)` cho mọi U_n. Bias-free ở đây là **literal Cho recipe được chọn cho fixture**, không chứng minh journal GKT bỏ bias; không mượn bias rule JSAI để gọi là journal parity. Nếu sau này chọn `torch.nn.GRUCell`, phải đổi recipe ID/metadata và có known-answer cho reset-after, không coi hai checkpoint tương thích.

### 3.3. h0, MLP và normalization: đóng fixture mà không giả training recipe

| Trường mandatory | Giá trị fixture đề nghị | Giới hạn rõ |
|---|---|---|
| State/message widths | `message_dim=state_dim=H`, H/E/MLP-width do caller cung cấp | Không chọn32 hoặc capacity cho benchmark |
| Initial state | zeros `[B,N,H]`; caller có thể cung cấp explicit continuation state đúng binding | Không learned h0/learner ID; zero là convention, không tìm thấy author initialization |
| f_self/out/in | Ba MLP độc lập; `ELU(Linear2(ELU(Linear1(x))))`, output H, biases explicit True; hidden width mandatory | Tương thích mô tả hai-layer ELU nhưng exact activation placement chưa được tác giả xác minh |
| Message normalization | `none` | **Omission có khai báo** so với journal training BN, không một faithful training reproduction |
| Dropout | explicit0 trong engineering fixture | Không áp dụng0 thành final scientific hyperparameter; dropout/BN training recipe cần review riêng |
| Update mask | answered OR incoming/outgoing support; event padding làm toàn event no-op | Không normalize qua learners/time hoặc cập nhật unsupported node |

BN huấn luyện trên flattened `[batch*node,feature]` trộn peers; flatten thêm time có thể đọc future responses. Sửa bằng LayerNorm sẽ đổi thuật toán; BN theo node riêng hoặc frozen statistics cũng là recipe khác, chưa suy được từ source. Vì vậy **không thêm normalizer thay thế** trong fixture này. `none` được chọn minh bạch để core causal/row-local kiểm được; chưa thể đưa core đó vào bảng kết quả như journal-BN model. Dùng train-only frozen BN trong tương lai vẫn cần ghi axis, placement, singleton behavior, running-state lifecycle và exclusion của padding trước khi fit.

Với h0 zero, first query có score hữu hạn từ node bias. Core có thể trả score này kèm mask/history count; không tự coi nó là fitted prior, không tự bỏ khỏi denominator. Cold-target inclusion/calibration và fitted eligibility nằm ở adapter/protocol sau.

## 4. API nhỏ đủ viết full recurrence

Đề nghị thêm file mới `gkt/recurrent.py` và `tests/gkt/test_recurrent.py` sau review, giữ nguyên Batch A. Không trainer/export/shared bridge trong batch này.

```text
model = StaticGKTRecurrent(config, binding, fixed_A, explicit_recipe)
state = model.initial_state(batch_size)          # zeros; có binding, không learner ID
readout = model.predict(state, query_ids)        # không nhận response, không mutate
state2 = model.observe(state, answered_ids, r, event_valid_mask)
outputs = model.sequence(events, initial_state) # predict_t trước observe_t
```

`predict`/`observe` nhận và trả caller-owned tensors, không cache learner history trong module. `sequence` dùng đúng cặp `(i_t,r_t)` của event t, không double-shift hoặc ghép concept hiện tại với response trước. Event padding trả maskFalse và finite placeholder0, state giữ nguyên, không tính target; không index sentinel vào embedding. Unknown IDs/multi-concept events bị reject, chưa dựng OOV reset/skip policy. State continuation phải giữ domain/vocab/order/A/recipe/dtype/geometry binding; caller metadata không là chứng nhận graph/vocab train-only.

Readout gồm common vector w_out và per-node bias như Batch A. Parameters mới là concept/interaction embeddings, ba MLP, hai erase/add affines và các GRU affines đã nêu; không thêm item difficulty head, graph encoder học được hoặc attention/prerequisite constraint ngoài source. Engineering weights/seed chỉ phục vụ fixtures, outputs giữ role chưa fit.

**Acceptance nhỏ, có điểm dừng cụ thể:** hand-calculated erase/add và non-diagonal-U GRU positive control; asymmetric3node incoming/outgoing; dense/empty/disconnected support; two-step sequence==manual predict/observe; đổi current/future responses không đổi earlier scores; learner batch permutations/eval-single equivalence; padding no-op; immutable caller state; finite gradients qua đủ gate/GRU/MLP/readout, 0 optimizer steps. Guard thứ tự query trước update cần test end-to-end, không chỉ signature. Không chạy tests/model trong research task này; đây là kế hoạch cho batch code bounded sau duyệt.

## 5. Phân định quyết định, không kéo S05 vào engineering mặc định

**Có thể đóng như quy ước kỹ thuật:** tensor layout, strict finite/dtype/device checks, response pairing/predict-before-update, padding no-op, bindings/hashes và caller-owned state. Chúng bảo vệ semantics đã chọn.

**Phải reviewer chấp nhận cho recipe, không giả là source unique:** unary erase/add specialization, GRU reset/bias, zero h0, MLP activation placement, omit BN/dropout0 fixture và sparse support operationalization. Những trường này thay đổi hàm dự báo; lưu recipe ID, không lựa chọn bằng metric pilot.

**Vẫn S05:** concept28 vs exercise/item vocabulary, simultaneous multi-tag representation, Dense/Transition/expert/learned graph và train-only graph construction, H/E/capacity, history full-prefix vs info-matched window, folds/seeds/optimizer/epoch selection/refit, model×environment allocation. **Vẫn S04/adapter:** score calibration/mastery interpretation, first-target/OOV coverage, controller bridge. [Proposal](../../docs/thesis_recovery/evidence/proposal.txt) giữ GKT comparator; [matrix E10](../../docs/thesis_recovery/05_EXPERIMENT_MATRIX.md) chưa cho phép lấy fixture recipe này làm final baseline.

**Đề xuất quyết định duy nhất cho parent:** cho phép full recurrent **engineering convention v1** ở §3–4, ghi rõ BN omission/EA mapping và giữ scientific use pending. Không cần chờ code unofficial hoặc dựng thêm graph model. Nếu parent chỉ chấp nhận exact author model thì trả trạng thái “gate specification chưa identified”, không lấp khoảng trống bằng identity gate hoặc tuyên bố paper parity. Không có technical blocker đối với recurrence đã đặc tả; có evidence blocker đối với exact reproduction.
