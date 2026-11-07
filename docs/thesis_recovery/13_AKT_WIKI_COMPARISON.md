# Đối chiếu DeepWiki và AKT KLTN — 07/11/2026

## Kết luận

KLTN sử dụng nguyên class AKT từ đúng upstream commit mà DeepWiki index, nhưng có runtime, data adapter, kiến trúc được cấu hình và training protocol riêng. Được mô tả là AKT-NonRasch exercise-level adapted for Junyi. Chưa có cơ sở gọi đây là reproduction nguyên xi command mặc định hoặc kết quả KDD2020.

## Nguồn đối chiếu

Đã đọc [Getting Started](https://deepwiki.com/arghosh/AKT/2-getting-started), [Installation](https://deepwiki.com/arghosh/AKT/2.1-installation-and-dependencies) và [Running Models](https://deepwiki.com/arghosh/AKT/2.2-running-models). Trang ghi index commit01b7e8, khớp local full commit01b7e8d7d7c862cabc9467108e3e7f2555653a88. Đối chiếu ưu tiên primary source tại checkout `artifacts/akt/dependencies/upstream/`, gồm README.md,akt.py,main.py,utils.py,run.py,load_data.py. Hash identity mới được kiểm trong evidence/akt-wiki-comparison-20261107.json.

## So sánh source và execution

| Hạng mục | Upstream | KLTN | Đánh giá |
|---|---|---|---|
|Core source |Class AKT trong akt.py |Import nguyên pinned akt.py |Khớp source, SHAbe2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d |
|Variant |akt_cid là NonRasch, utils gán n_pid=-1 |n_pid=0, separate_qa=False |Cùng tắt Rasch branch do điều kiện n_pid>0, khác metadata sentinel |
|Token semantics |Skill/concept ID ASSISTments |Exercise ID Junyi |Adaptation cần ghi rõ, không có explicit KC crosswalk |
|Main dimensions |d_model256,heads8,blocks1,dropout.05,finalFC512 mặc định |Các giá trị đó trùng |Cần phân biệt d_ff dưới đây |
|Runtime |README ghi Linux/Torch1.2.0 và libraries2020 |Windows Python3.13,torch2.7.1+cpu,.venv |Runtime khác, được kiểm CPU parity, CUDA chưa verified |
|Entry point |main.py trên data/assist* |knowledge_tracing.akt.cli và project configs |Project pipeline riêng, không copy command ASSIST vào Junyi |
|Encoding |q one-based,qa=q+y*n_question,padding0 |Cùng convention sau train-vocab mapping, loss mask-1 |Adapter giữ causal semantics, có OOV barrier riêng |
|Window |Chunk disjoint seqlen200 |H100/T100,target blocks với context, L≤200 |Max length giống nhưng target/history exposure khác |
|Training loss |Native summed BCE đưa thẳng backward |Chia native loss cho số scored targets |Gradient scale khác, không claim optimizer trajectory parity |
|Optimizer |Adam,lr1e-5,batch24,seed224,clip off mặc định |Adam,lr1e-4,batch4,seed42,clip1 |Khác protocol, không tự đổi cấu hình để khớp wiki |
|Selection |Best validation AUC,max300epochs,stop heuristic>40 |Inner validation LL,min_delta.0001,patience3,max20,outer refit |Khác model-selection design, giữ learner boundaries project |
|Checkpoint |main.py xóa checkpoints cũ và sau test |Immutable publish,identity/RNG,recovery APIs |Có engineering mở rộng, không chạy upstream main.py lên historical project artifacts |

## Phát hiện d_ff thực chạy

`main.py` khai báo --d_ff=1024 nhưng `utils.load_model()` không truyền d_ff vào constructor. `akt.py` constructor default2048. Vì vậy CLI upstream ở defaults dùng2048. Cờ n_head và final_fc_dim cũng không được truyền trong utils, dù defaults8/512 đang tình cờ trùng. KLTN `upstream.build_native()` truyền tường minh d_ff1024,heads8,finalFC512.

Đã khởi tạo hai models bằng vocabulary tổng hợp3tokens. KLTN có ba linear1 weight shapes[1024,256],2.567.705parameters. Tương ứng upstream CLI effective defaults có[2048,256],4.143.641parameters. Đây là initialization check, không training. Số parameter phụ thuộc vocabulary, không lấy các số trên làm model-size Junyi thực.

Phát hiện này hiệu chỉnh suy luận trước đây rằng parser default1024 chứng minh kiến trúc khớp. KLTN1024 vẫn là cấu hình hợp lệ của native AKT, nhưng khác default CLI effective architecture. Trước full experiments cần ghi architecture identity rõ và chốt protocol. Không tự sửa lên2048 hoặc đổi lr/batch/selection trong lần kiểm toán.

## Giới hạn parity

`tests/akt/test_upstream_parity.py` so wrapper với class upstream tại cùng cấu hình nhỏ CPU và cùng state_dict. Nó kiểm logits/probabilities/summed loss/gradients cùng source integrity. Không kiểm tương đương toàn bộ training recipe hoặc old PyTorch1.2 numerical behavior. Kết quả chạy mới nằm trong evidence/akt-wiki-parity-tests.log.

README chỉ liệt kê môi trường lịch sử, không đủ chứng minh mọi runtime mới đều sai hay đều tương đương. Wiki là tài liệu thứ cấp. Các suy luận mở rộng như tính bắt buộc của môi trường, roles của metadata và defaults phải được đối chiếu source. Không cài lại libraries2020 hoặc cài global để làm giống wiki.
