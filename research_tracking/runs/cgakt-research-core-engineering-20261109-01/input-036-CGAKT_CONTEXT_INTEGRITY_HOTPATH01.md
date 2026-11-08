# Khoảng trống readiness: integrity của context CG-AKT trên hot path

Ngày09/11/2026. Chỉ đọc source/kiểu dữ liệu và SHA; không import, test, model,
corpus, benchmark hay đo throughput. Giữ model/tests đang freeze nguyên bytes.

## Phiên bản đối chiếu

- `src/knowledge_tracing/akt/research_graph_model.py`: `7ed0878f844d67598a6b684be92e770ea98d9b57ebbdb6a67c89cfef65020150`.
- `tests/akt/test_research_graph_model.py`: `972ed185763e04d51435aaf496a8f9b5bb07fbe5a910b068ebd9121e7f846fce`.
- `src/knowledge_tracing/akt/research_graph_context.py`: `5a5ada91a78a5d7de2b4d5021dc3cf34e6c97de2e46931509b8f6faf5c56c4d5`.

Context đã sửa guard `inputs.labels` không tồn tại. Audit tĩnh model dùng các
field có thật của `CausalSequenceInputs` (`shared_kt.py:94`), `WindowInputs` và
`TrainingWindow` (`akt/types.py`), `AKTBatch` (`akt/tensors.py`) và research
encoding/index hiện hành. Model không truy cập `inputs.labels` hoặc
`PreparedGraphContext`. Đây không là kết quả chạy các branch.

**Fixture model còn blocker đã báo ROOT:** dòng41 của test đang tạo source_row0
cho event đầu. `ItemQuery.__post_init__` (`simulator_bridge.py:72`) yêu cầu>=1.
Cần sửa riêng fixture+1 trước native dispatch; global_rank vẫn0-based. Theo lệnh
freeze, note này không sửa source/test hoặc khẳng định18cases đã chạy.

## Số lần quét toàn cache theo source

Gọi C là kích thước payload context đầy đủ, W là tổng số indexed windows,
K là số windows được chọn cho batch, L là số token/window. C bao gồm mọi
audit/parents/observed_rows, không chỉ số target; không có số byte đo thực tế.

`ResearchGraphContextIndex._payload()` gọi `dataclasses.asdict(self)` trên toàn
index; `assert_integrity()` serialize JSON+SHA của payload và đọc lại source
inventory. `identity` gọi lại `assert_integrity()`. `for_windows()` vừa gọi full
assert vừa dựng lại dict lookup từ **mọi W windows**, rồi hash input K windows.
`identity_hash` (`simulator_bridge.py:16`) serialize JSON mỗi lần; chưa có cache
digest hoặc lookup chỉ đọc được dựng một lần tại attach.

`ResearchGraphAKTAdapter._integrity()` (`research_graph_model.py:248–255`) gọi
`index.assert_integrity()` rồi `index.identity`: **hai full payload hashes**,
không phải một lần so sánh SHA có sẵn.

| Đường chạy thành công | Full cache hashes | Full lookup rebuild |
|---|---:|---:|
| `set_context_index` | 2 | 0 |
| Một `collate_training` | 2 qua `_integrity` +1 qua `for_windows` =3 | 1 |
| Một `step` sau collate | 2 trước primitive +2 sau primitive =4 | 0 |
| Một batch train hoàn chỉnh | **7** | **1** |
| `predict_windows` chứa B groups | 2 đầu +B trong vòng lặp +2 cuối =**B+4** | B |

Caller gọi predict riêng từng batch thì mỗi batch chịu5full hashes. Các lần
caller đọc `adapter.identity` ngoài các đường trên còn thêm2full hashes/lần.
Condition, encoding và source inventory cũng được kiểm lặp; chúng chưa được gộp
vào C và không được coi là miễn phí. Batch ticket còn hash tensor/array payload
ở collate, step, native bind và native forward; đó là chi phí theo batch hiện
tại, khác với quét cả phase.

Với B batches, train hiện tại cần Θ(B·C+B·W) ngoài chi phí window/tensor/NN.
Khi geometry cố định và C,W tăng tuyến tính theo số event thì phần này có thể
tăng bậc hai theo quy mô phase. Đây là phân tích source, **không** là đo thời
gian, dự báo GPU cost hoặc khẳng định một kích thước corpus đã OOM/timeout.

## Sửa tối thiểu để ROOT xem xét trong batch sau

1. Full audit khi build/attach index và trước/sau epoch hoặc prediction pass;
   giữ expected root digest, condition/phase/encoding/vocabulary/source pins.
2. Dựng lookup immutable một lần; seal riêng mỗi record bằng hash bao gồm
   window ID, learner, input hash và **toàn bộ** QueryEvidence/audit của record.
   Bind map các record hashes vào root seal đã kiểm ở boundary. Không chỉ hash
   `WindowInputs` mà bỏ qua evidence được model thực sự dùng.
3. Hot path kiểm cheap header/binding và selected record evidence hash so với
   expected sealed map, cộng input hash và exact one-use tensor ticket. Không
   dựng lại W-entry lookup hay serialize C cho mỗi batch. Chi phí theo K window
   và evidence được chọn; geometry, OOV, confidence, source safeguards giữ nguyên.
4. Bỏ double-full-check chỉ sau khi API owner và ROOT thống nhất public audit
   boundary. Không thay `assert_integrity` bằng đọc self-declared content SHA.
   Full boundary check phải chặn nghiệm thu nếu một record không được chọn bị
   sửa trong epoch; giữ failed receipt và partial updates, không claim rollback.

Selected-only checks chuyển thời điểm phát hiện tamper ở record không được chọn
từ từng batch sang full boundary. Phải nói rõ điều này, không gọi là chứng thực
hostile-caller hoặc bảo toàn tức thời toàn-cache bằng magic O(1). Frozen tuple,
dataclass và private map chỉ là consistency contract hợp tác như hiện tại.

Acceptance của batch tối ưu cần negative controls cho selected evidence/input,
header/source/root-manifest drift, unselected tamper bị bắt tại final boundary,
và chứng minh hot path không gọi full serializer. Chưa cho phép thực hiện batch
đó hoặc benchmark trong công việc này.

## Kết luận phạm vi

Ngay cả tiny core kiểm đúng8forwards/5backwards/0optimizer sau này PASS, chi phí
integrity trên phase đầy đủ vẫn là **blocker main-training readiness**. Tiny
fixture không chứng minh throughput/RSS/cost, trainer/checkpoint/resume, selector
hay empirical research result. Không tối ưu source/API ở lần note này.
