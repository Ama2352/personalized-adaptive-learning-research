# Recipe GKT nghiên cứu V1

Ngày 09/11/2026. Nhóm chọn recipe `gkt-grade10-static-expert-r32-bn-d5-v1` trước khi fit mô hình nghiên cứu. Quyết định này chốt đặc tả để triển khai theo nhiệm vụ người dùng đã giao. Phê duyệt từng lượt chạy, ngân sách và nghiệm thu mô hình dùng các hồ sơ riêng.

## Căn cứ lựa chọn

Protocol21 yêu cầu comparator GKT với 28 khái niệm, đồ thị chuyên gia và lịch sử đầy đủ. Core engineering hiện có cung cấp các phép toán graph và GRU có thể tái sử dụng. Recipe nghiên cứu bổ sung batch normalization và dropout để giữ các thành phần được mô tả trong bản journal. Chất lượng dự báo của comparator cần được đo sau khi fit.

Bản journal dùng hidden/embedding32, MLP hai lớp ELU, dropout0,5, batch normalization và Adam0,001. Các thiết lập khác của bài gồm batch16, tối đa50epochs và training bằng đoạn được lấy mẫu dài100. Khóa luận chọn batch4 và whole-prefix training cho corpus Development hiện có dài210events/learner. Hai khác biệt này được ghi trong model manifest và phần phương pháp. [Nguồn sơ cấp, §4.3](https://journals.sagepub.com/doi/10.3233/WEB-210458)

Phép gán erase–add, GRU reset convention và các trục normalization dùng quy ước triển khai được nêu dưới đây. Độ tương đương với code/checkpoint của tác giả chưa được xác minh. Tên model khi báo cáo là **GKT static-expert, recipe BN-D5 V1**.

## Đặc tả cố định

| Thành phần | V1 |
|---|---|
| Domain | Grade10, sorted28concepts, public registry84items |
| Graph | Directed static expert, zero diagonal, TRAIN80 provenance và actual topology bytes được kiểm trước allocation nghiên cứu |
| Representation | Concept state32, concept/interaction embedding32, message32, MLP hidden32 |
| H0 | Zero riêng cho từng learner |
| MLP | Linear → ELU → dropout0,5 → Linear → ELU → BN32 |
| BN | Feature axis32, eps1e-5, momentum0,1, affine và running statistics |
| Erase–add | Unary convention `m*(1-sigmoid(W_e*m+b_e))+tanh(W_a*m+b_a)` |
| GRU | Cho reset-before, bias-free, sáu shared affine matrices |
| Update mask | Answered node và incident neighbors, áp sau GRU |
| Response | Readout concept đích trước khi dùng đáp án hiện tại |
| Objective | Mean BCE-with-logits trên eligible targets, đồng thời xuất full-population coverage |
| Optimizer | CPU FP32 Adam, lr0,001, betas0,9/0,999, eps1e-8, weight_decay0, clip norm1 |
| Adam options | AMSGrad/foreach/fused/maximize/capturable/differentiable đều false |
| Batch | Tối đa4learner trajectories, events theo đúng thứ tự trong từng learner |
| Shuffle | Private Python Random(seed42+epoch) chỉ đổi thứ tự learners |
| Epoch selection | Max50, patience5, min_delta0,0001, raw selection response-pooled Log Loss, tie giữ epoch sớm |
| Initialization | Seed42, CPU RNG riêng, khôi phục RNG của caller sau constructor |

Các con số của optimizer, batch và stopping được đóng trước fit. Thay đổi recipe sau này cần ID mới cùng lý do và ranh giới thông tin được phép sử dụng. Các quy ước singleton/masking dưới đây là lựa chọn của khóa luận.

## Normalization theo thời điểm

Mỗi timestep xử lý các learner còn valid. Self MLP có một row cho mỗi learner valid. Out/in MLP có 27 nonself node-pairs cho mỗi learner valid, gồm cả các cặp có adjacency bằng0. Weight graph được áp sau MLP. Các trục BN chỉ gồm rows ở thời điểm hiện tại và feature dimension32.

Khi có ít nhất hai rows, dùng BN training của PyTorch. Một row dùng running statistics hiện có, giữ dropout training và ghi sự kiện singleton fallback vào receipt. Nhánh không có row valid bỏ qua cả MLP, dropout và BN. Padding không đổi state hoặc chạy thêm RNG. Eval dùng running statistics đã đóng, dropout tắt và cần chứng minh batch/singleton prediction parity. [Hành vi BN của PyTorch2.7](https://docs.pytorch.org/docs/2.7/generated/torch.nn.BatchNorm1d.html)

Training có coupling giữa learners trong cùng normalization pool. Causal tests phải kiểm future-label perturbation và việc xử lý từng timestep. Các phép kiểm row-independent của prototype C0 có phạm vi riêng. Predict trước observe giữ nguyên thứ tự response targets.

## RNG, state và checkpoint

Constructor dùng CPU fork_rng, seed riêng và lưu trạng thái CPU RNG sau initialization để trainer nhận quyền sở hữu. Trainer phải dùng stream dropout đã sở hữu và khôi phục stream của caller khi kết thúc. Một model/trainer chạy trong một luồng điều phối, tránh dùng fork_rng đồng thời giữa các threads.

Checkpoint nghiên cứu phải lưu parameters, adjacency binding, BN running mean/variance/counters, Adam state/participation, RNG thực đã tiêu thụ, module modes, epoch và các counters. Validation trước mutation và khôi phục trong fresh container là điều kiện nghiệm thu. Partial forward có thể đã đổi BN/RNG dù chưa có optimizer step, cần ghi đúng khi xử lý failure.

## Data và evaluation

Tái dùng `gkt/research_data.py` cùng role split80/10/10 và refit90 theo protocol21. Public bank registry khác vocabulary items được optimization quan sát. Inference giữ null cho OOV và unsupported history suffix. Field `trained_item` của truth sidecar không thay cho eligibility thực của predictor input.

NN xử lý một sequence cho mỗi learner batch. Chi phí biểu diễn expanded prefix trong bridge vẫn cần reserve, còn recurrent NN cần duyệt tuyến tính theo chiều dài sequence. Manifest ghi full-prefix training210 và batch4. Junyi cần mapping và recipe domain riêng trước triển khai thực nghiệm đó.

Tại cùng state, ba items cùng concept có cùng raw GKT probability. Reference controller chỉ được gộp readout sau khi kiểm actual parity và đủ84support keys. So sánh GKT với AKT là so sánh kiến trúc, các contrast graph riêng của RQ3 dùng A0–A3 theo recipe26.

## Nghiệm thu implementation

1. Đúng graph orientation, registered parameters và BN buffers. Đối chiếu native parameter count với phép đếm nguồn.
2. Prediction t bất biến khi sửa current/future answers. Sequence khớp manual predict→observe.
3. Padding/all-invalid không đổi state, RNG hoặc BN statistics. Singleton fallback được kiểm riêng.
4. Eval singleton/batch khớp trong tolerance FP32 1e-6. BN training peer coupling được đo đúng tên.
5. Full coverage, OOV suffix, role/refit và origin_role khớp data bridge.
6. Checkpoint/Adam/RNG/BN roundtrip và complete epoch counters có bằng chứng native riêng.

GKT08 tiếp tục theo model → trainer → checkpoint → admitted producer → adapter. Các bước model/trainer là compute APIs. Research fit cần runtime, source, resource và authorization đúng lượt.

## Nguồn đối chiếu

- [Protocol Development V1](21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md).
- [Báo cáo nguồn và core GKT](../../research_tracking/reports/gkt_source_and_core_plan_20261108.md).
- [Quy ước recurrent engineering](../../research_tracking/reports/gkt_recurrence_specification_20261108.md).
- [Cầu nối dữ liệu đã kiểm](../../research_tracking/reports/gkt_research_data_readiness_20261109.md).
- Review alternatives được giữ tại `artifacts/akt/local-tests/akt-research-runner-20261108-01/GKT_RESEARCH28_NUMERICAL_AND_LIFECYCLE_REVIEW01.md` và `GKT_RESEARCH28_BN_D5_ALTERNATIVE_SPEC01.md`.
