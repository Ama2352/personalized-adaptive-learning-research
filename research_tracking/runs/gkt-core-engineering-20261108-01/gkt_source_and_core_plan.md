# GKT: nguồn sơ cấp và phương án core tối thiểu — 08/11/2026

## Kết luận để review trước implementation

GKT bắt buộc trong đề cương là **Graph-based Knowledge Tracing của Hiromi Nakagawa, Yusuke Iwasawa và Yutaka Matsuo**. Đã đọc bản tác giả tại workshop RLiGM 2019 và bài journal 2021 trên trang publisher. Chưa xác minh author-official code; không gọi `jhljx/GKT` là mã của ba tác giả paper. Trong phạm vi inventory tên/targeted text chưa tìm được core hoặc PDF GKT; chưa lập full-text index mọi PDF tên khác. Không sửa native AKT, source/tests, indices, state hoặc Git trong audit này.

**Đề nghị chia implementation thành hai mức:** (A) kernel static adjacency + causal readout/message equations có nguồn rõ; (B) full recurrent GKT chỉ sau review công thức erase–add, initialization và update mask. Hiện **chưa đủ để gọi full core là exact author reproduction**. Parent review phương án trước khi tạo `src/knowledge_tracing/gkt/` và `tests/gkt/`; chưa train hoặc tự chọn benchmark variant/capacity/S05.

## 1. Nguồn thực sự tìm được

| Nguồn | Định danh/đã đọc | Giá trị và giới hạn |
|---|---|---|
| [Workshop accepted list](https://rlgm.github.io/papers/) và [PDF tác giả](https://rlgm.github.io/papers/70.pdf) | RLiGM, **ICLR 2019 Workshop**; PDF 8 trang, §2.1–2.2, Eq.(1)–(2), Appendix B trang 6–7. | Primary manuscript tại website workshop; header PDF không phải căn cứ gọi đây là ICLR main-track. Không xác nhận byte-equivalence với camera-ready WI2019. |
| [WI2019 DOI](https://doi.org/10.1145/3350546.3352513) | Tên paper “Graph-based Knowledge Tracing: Modeling Student Proficiency Using Graph Neural Network”. Publisher request trả403. | Không truy cập được full text WI qua publisher trong lượt này; không gán page/equation của bản khác sang WI. |
| [Journal của cùng tác giả](https://journals.sagepub.com/doi/10.3233/WEB-210458) | *Web Intelligence*19(1–2), 87–102, 2021; §3.1–3.3, §4.3, §5.4. | Primary expanded specification; dùng section anchors vì HTML không cho page mapping tin cậy. Không trộn mọi chi tiết training với workshop. |
| [DKVMN tác giả, arXiv1611.08108v2](https://arxiv.org/html/1611.08108) | Zhang, Shi, King, Yeung; §3.2.3 Eq.(6)–(9). | Primary reference mà GKT viện dẫn cho erase–add; chưa tự xác định đầy đủ phép chuyển sang message tensor của GKT. |
| [Repository `jhljx/GKT`](https://github.com/jhljx/GKT/blob/master/models.py) | Search trả source header ghi code-author `jhljx`; README chỉ gọi là implementation. | Chỉ dùng để kiểm provenance của candidate. Không xác minh liên hệ tác giả GKT; không dùng thuật toán/weights của repo này làm author specification, không clone/chạy/cài dependencies. |

Local inventory bằng `rg --files`/targeted searches tại `ref-papers/`, `paper1/`, `paper2/`, `docs/`, `src/`, `tests/` chỉ tìm nhắc GKT trong survey, architecture và experiment matrix. [Architecture hiện tại](../../docs/thesis_recovery/06_AKT_CGAKT_ARCHITECTURE_PLAN.md) mới đề xuất concept28 + difficulty; **đó chưa là đặc tả GKT đã duyệt**. [Đề cương](../../docs/thesis_recovery/evidence/proposal.txt) yêu cầu GKT comparator nhưng không định variant/hyperparameters. Search không chứng minh không có nguồn ngoài phạm vi này.

Đọc qua web text/HTML, chưa có SHA của bytes PDF/HTML gốc. Download PDF bằng PowerShell thất bại DNS; web screenshot không trả image bytes để xem. Vì vậy **không claim visual PDF verification, downloaded source hash hoặc author checkpoint parity**. [Provenance JSON](gkt_source_and_core_plan_20261108.json) ghi nguồn, reads và failures; không cài dependency.

## 2. Đồ thị nào được gọi là GKT?

Tóm tắt nguồn: workshop §2.2 nêu **Dense**, **Transition**, **DKT-derived**, **PAM**, **MHA**, **VAE**. Dense dùng `Aij=1/(N−1)` ngoài đường chéo; Transition lấy tần suất concept j xuất hiện ngay sau i. PAM học adjacency, MHA/VAE suy trọng số/loại cạnh. Concept-state update dùng hai chiều thông điệp; journal §5.4 cảnh báo hướng phụ thuộc/nhân quả của learned edges không được bảo đảm. [Nguồn phương trình/variants](https://rlgm.github.io/papers/70.pdf), [thảo luận tác giả](https://journals.sagepub.com/doi/10.3233/WEB-210458).

**Diễn giải và lựa chọn của khóa luận, chưa adoption:**

| Candidate | Ý nghĩa cần ghi | Phạm vi core đề nghị |
|---|---|---|
| Dense | Graph đầy đủ, không dùng expert prerequisites; benchmark graph neural architecture. | Kernel fixture đầu tiên: đơn giản, không cần fit graph hoặc corpus. Không mặc định primary variant cuối. |
| Transition | Association của logging order, không phải causal prerequisites. | Sau core: dựng chỉ từ learner training; phải freeze chronology, repeated/self transitions và zero-row convention. |
| Expert/prerequisite adjacency | Đồ thị ngoài được đưa vào họ static-adjacency GKT, cần nhãn variant và orientation riêng. | Cho caller truyền matrix + metadata, không tự đổi `PrerequisiteGraph` thành normalized A. Đây là extension/allocation cần review, không gọi Dense nguyên bản. |
| DKT-derived/PAM/MHA/VAE | Các graph-generation/learning mechanisms khác nhau, có chi phí/protocol khác. | Chưa implement trong batch tối thiểu. Không coi static kernel là đã đáp ứng learned-graph requirement của toàn KLTN. |

GKT không phải GIKT hay CG-AKT. Dùng expert graph không tự làm GKT thành prerequisite-constrained controller; GKT vẫn trả dự báo correctness. Cạnh/cổng learned không tự là calibrated edge confidence hoặc bằng chứng tiên quyết nhân quả.

## 3. Phương trình rõ và những chỗ chưa rõ

Ký hiệu `H_t` là state **trước** response t, node được hỏi i, response r_t. Viết lại theo causal indexing của repo:

```text
p_t = sigmoid(w_out @ H_t[i] + b_i)                 # chưa nhận r_t
z_i = concat(H_t[i], interaction_embed(i, r_t))       # sau observe
z_j = concat(H_t[j], concept_embed(j))               # j != i
m_i = f_self(z_i)
m_j = A[i,j] f_out(concat(z_i,z_j))
    + A[j,i] f_in (concat(z_i,z_j))
H_(t+1)[j] = GRU(G_ea(m_j), H_t[j])                 # recipe/mask còn review
```

Đây là reindexing Eq.(1)–(2) workshop/trình tự journal §3.2: output sau observation t dùng để dự báo **bước kế tiếp**, không chấm với r_t vừa nhập. Prediction head dùng state node đích; `w_out` chung, bias theo node được nêu trong paper. Chưa đổi score thành P(K). [Nguồn gốc](https://rlgm.github.io/papers/70.pdf).

| Điểm chưa xác định duy nhất | Vì sao quan trọng | Hành động nhỏ nhất |
|---|---|---|
| `G_ea` | GKT ghi một unary erase–add operator rồi dẫn DKVMN. Đã đọc DKVMN Eq.(6)–(9): `e=σ(Eᵀv+b_e)`, `a=tanh(Dᵀv+b_a)`, erase prior memory bằng `1−w·e` rồi cộng `w·a`. Chưa có mapping duy nhất từ prior-memory/write-weight này thành GKT message-only gate. | Để `erase_add_recipe` unresolved; không âm thầm thay identity hoặc copy gate third-party rồi gọi exact paper core. |
| Initial H và cold target | Không tìm được initialization specification đủ để chốt h0 zero/learned trong phần GKT đã đọc. | Caller explicit; cold-score inclusion/unsupported và learned initial state nếu dùng phải review trước fit. |
| Node ngoài neighborhood | Text nói chỉ update related concepts, nhưng zero adjacency message qua biased gate/GRU vẫn có thể làm unrelated H đổi. | Core proposal dùng explicit support mask; kiểm graph-empty/self-only và ghi convention. Dense fixture chưa phân giải sparse semantics. |
| MLP/BatchNorm geometry | Journal §4.3 thêm two-layer ELU, dropout0,5 và BN output; axis/placement chi tiết chưa đóng bằng author code. | Không chọn default BN geometry gây phụ thuộc peers/future. Eval freeze thống kê; kiểm causal prefix và independent learner scores. |
| Revision/training recipe | Workshop Appendix B ghi lr0,01; journal §4.3 ghi0,001. Hidden/embedding32 là mô tả nguồn. | Những số này không phải hyperparameters được duyệt cho KLTN. Chọn citation/recipe rồi công khai khác biệt; không tự chạy grid. |

[Journal specification](https://journals.sagepub.com/doi/10.3233/WEB-210458) và [DKVMN write process](https://arxiv.org/html/1611.08108) giúp thu hẹp nhưng chưa loại hết ambiguity. Nếu cần full core ngay, phải đặt tên **documented GKT reimplementation convention**, ghi mọi deviation; không hứa checkpoint/metric reproduction của tác giả.

## 4. Input, graph và training boundaries đề nghị

Đây là thiết kế riêng cho repo, chờ review:

- **Node vocabulary:** một schema domain-specific có ordered vocabulary/hash và graph-node order đồng nhất. Shared IDs0..N−1 phải chuyển có kiểm sang tensor IDs nếu dành padding; không reuse numeric IDs giữa Junyi và Grade10. Concept28 và item84 là hai semantics khác; chưa thêm difficulty feature hoặc item decoder dưới tên paper-faithful GKT. Unknown/multi-concept queries chưa có rule thì từ chối/unsupported rõ ràng, không chọn concept đầu tiên.
- **Causality:** API `predict(state, query)` không nhận current response; `observe(state, concept, response)` mới cập nhật. Sequence wrapper phải update bằng prior event rồi query current event, không dùng current concept với prior response sai pairing. Candidate probing không update state; learner histories tách biệt.
- **Graph fitting:** Dense không dùng outcome; Transition chỉ từ training learners/prefix chronology. DKT-derived/learned graph chỉ fit trên training tương ứng, inner-selection/refit provenance tách rõ. Validation/outer fold/Test và simulator oracle không được dùng để fit graph/vocabulary. Graph học từ initialization/order có thể proxy policy; cần controls độc lập trong thiết kế RQ2.
- **History:** recurrent state có thể chứa toàn bộ prefix, khác AKT effective window. S05 phải chốt full-prefix vs fixed-window replay/info-matched comparator; không coi cùng target rows là cùng history budget.
- **Resources:** static A lưu O(N²), mỗi learner state O(Nh); một update có thể lấy row/column A và xử lý O(N) nodes, không cần O(N²) messages mỗi bước. Đây là complexity plan, chưa runtime/RAM measurement. Không thêm framework GNN mới nếu PyTorch đã có đủ primitives.
- **Shared interface:** [SequenceKTModel](../../src/knowledge_tracing/shared_kt.py) yêu cầu fit/predict; isolated kernel chưa đáp ứng fitted training API. Không nới shared `OnlineScore`, không gắn random outputs là fitted. Adapter/trainer/export/checkpoint binding là batch sau, có provenance riêng.

## 5. Implementation-ready scope và acceptance để parent review

**Batch A, có thể xây sau parent review:** `gkt/config.py`, `gkt/core.py`, `tests/gkt/test_core.py`; chỉ explicit module imports, không sửa native AKT/shared/root exports. Config yêu cầu N, hidden/embedding widths, graph metadata/domain/vocab/node-order hashes. Không chọn optimizer, training seeds hoặc scientific defaults.

1. Validate finite nonnegative square A, diagonal policy và node order; không yêu cầu DAG vì Dense/Transition có thể có chu kỳ. N=1 Dense phải có convention riêng, không chia cho0; chưa định thì reject. Không tự row-normalize expert weights.
2. Pure aggregation/message/readout kernel theo equations trên, state do caller truyền; incoming/outgoing direction kiểm bằng asymmetric 3-node fixture và hand-computed expected messages. Không training/checkpoint loader.
3. G_ea/recurrent closure giữ explicit unresolved nếu chưa chốt recipe; không trả object mang tên full fitted model. Nếu reviewer chọn convention, bổ sung recipe ID, h0/mask/MLP/BN geometry vào config/output provenance trước implementation mức B.
4. CPU tests có current-label independence, prefix-causal agreement, immutable input state, no inter-learner leakage, graph/node-order/domain mismatch rejection, empty/disconnected masking, padding no-op và finite gradients cho kernel. Random fixtures ghi **0 optimizer steps, no fitted efficacy**. Suite bounded≤120s, logs/JUnit và fail-before quan trọng giữ theo attempt riêng; không source/test nào đã được tạo trong audit này.

**Cổng lên mức B:** công thức gate có equation-level specification được reviewer chấp nhận; initialization/mask/normalization rõ; known-answer numerical recurrence tests và sequence-vs-step equivalence pass. Sau đó mới xem trainer/selected-fit/vocab construction, S04 calibration/mastery/first-target, S05 variant/capacity/model–environment allocation. Unit tests không thay đủ baselines, fitted efficacy hoặc nghiệm thu RQ3.

## 6. Những quyết định còn chờ và kiểm đã làm

Parent cần review chọn **Batch A-only** hoặc một documented full-core convention; chọn đúng source revision và cách giải ambiguity ở mục3. **S05** vẫn giữ graph method, input representation, capacity, history budget, seeds/folds và môi trường đánh giá; **S04** giữ mastery/calibration/controller. Không cần tự bỏ GKT, đổi RQ hoặc cài thêm stack để đóng audit.

Đã inventory local, đọc targeted source/shared contracts và nguồn sơ cấp trực tuyến; kiểm JSON/links/SHA của local documents sẽ ghi trong companion. Chưa code/test/train GKT, benchmark, truy cập raw Junyi/Holdout, chạy cloud/GPU hoặc cài packages. External primary source retrieval không đồng nghĩa có source code/weights official. DOI403 và PDF download DNS failure được giữ như giới hạn provenance, không được thay bằng SHA bịa.
