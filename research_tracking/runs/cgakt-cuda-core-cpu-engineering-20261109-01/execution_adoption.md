# Quyết định triển khai CUDA cho AKT và CG-AKT

Ngày 09/11/2026. Root chọn hợp đồng thực thi dưới đây trong phạm vi engineering người dùng đã giao. Nguồn thiết kế là `CUDA_EXECUTION_IMPLEMENTATION_SPEC02.md`, SHA `eae36e67aa4799f3704370ba0418d49bc8686f033fcd1b51c78b6d96d4edd393`, tại prep AKT hiện hành. Các kết quả chạy máy đích sẽ được nghiệm thu riêng theo ladder trong kế hoạch GPU.

## Công thức thực thi được chọn

CUDA dùng đúng một thiết bị `cuda:0`, FP32 và seed 42. Giữ geometry, loss, learning rate, batch, dropout, clipping, stopping và các vai dữ liệu của recipe26. Backbone được khởi tạo bằng CPU default generator, genuine loader nhận config CUDA và chuyển backbone sang thiết bị đó. Toàn wrapper được chuyển trước khi lưu identity của các parameter.

Adam CUDA dùng foreach=False, fused=False, capturable=False, differentiable=False, amsgrad=False, maximize=False và decoupled_weight_decay=False. Scalar step giữ CPU, các moment theo device của parameter. Quy tắc clipping giữ default hiện có của primitive, gồm foreach=None. Đây là lựa chọn backend có phiên bản. Sai khác số học với CPU được xem xét bằng kiểm riêng trên đúng backend.

Đặt deterministic algorithms ở chế độ nghiêm ngặt, tắt TF32, matmul precision highest và cudnn benchmark=False. Owned caller đặt `CUBLAS_WORKSPACE_CONFIG=:4096:8` trước CUDA context. Nếu operation không được backend hỗ trợ theo hợp đồng, lượt kiểm dừng và giữ lỗi để xem xét.

## Ranh giới API và tương thích

Thêm profile typed trong config và tham số keyword-only optional cho validator/model. `validate_config(config)` tiếp tục giữ hợp đồng CPU hiện tại. Config CUDA trong simulator-research phải được kiểm qua `validate_config(config, cuda_profile=profile)` và profile đúng kiểu. AKTConfig giữ các fields/default hiện có. CPU identity giữ đúng cách serialization hiện hành, CUDA bổ sung execution profile vào identity tương ứng.

Batch đầu chỉ sửa config, graph model và tests tương ứng. Main, runner và checkpoint được nối ở các batch sau, khi các hợp đồng trước đã kiểm. Trước constructor CUDA, core kiểm device, các backend flags, environment và allocator fraction đã được caller cấu hình. Core dùng snapshot tài nguyên đã có và đồng bộ tại các boundary hoàn tất. Caller quản cấu hình và khôi phục flags, cấu hình budget một lần cho operation.

## Checkpoint và kiểm chứng kế tiếp

CPU schema1 tiếp tục là hợp đồng cũ. CUDA dùng schema2 có execution identity riêng, CPU snapshots tường minh cho serialization, CUDA RNG của đúng device0 và kiểm live Adam step/moment theo device. Kiểm fresh restore cùng runtime phải đối chiếu state, RNG, input và bước tiếp diễn.

Trước actual CUDA cần source/runtime/lock/Gate đúng máy đích, allocation hữu hạn, checkpoint durability và chi phí được duyệt cho từng run. Bước triển khai local của quyết định này chỉ chuẩn bị phần mềm. Những bằng chứng còn thiếu được ghi riêng trong kế hoạch GPU và task backlog.
