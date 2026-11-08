# Review độc lập A2/A3 engineering — 08/11/2026

Kết luận scoped PASS: không thấy P1/P2 còn mở trong source `9fc6b827…` và tests `17cdfe58…`. Reviewer chỉ đọc mã và đối chiếu bằng chứng đã có; không chạy lại model, test, optimizer hay cloud. JSON đi kèm ghi đầy đủ SHA input trước/sau, counts từ XML và source snapshots.

Hai điểm pretest đã sửa: native control và backbone gradient dùng cùng thread context, vẫn giữ `torch.equal` và khôi phục ambient1/2; constructor A2/A3 bắt buộc confidence caller-explicit, còn uniform-control được khai báo rõ. Attempt03 có 43 tests, không failure/error/skip; stdout xác nhận 11,92 giây pytest. Controller15,340583 giây; cả ba attempt39,650895/120 giây, 0 optimizer. Attempt01 giữ lỗi Git ownership (3 pass/16 failure/24 error); attempt02 giữ41 pass/2 failure do fixture đổi train shard đã bind encoding. Final fixture dùng selection riêng để perturb và window train gốc để đối chiếu peer/padding; guard train-hash vẫn nguyên.

## Nhân quả, thông tin và arithmetic

Batch builder lấy prefix đầy đủ `observations[:rank]`, rồi dùng `prepare_graph_context`/window geometry sẵn có để giới hạn đúng effective history; OOV reset vẫn giữ global rank. Không dùng latent simulator, current answer hay future answer làm message/gate feature. Source-row, window, domain/vocab, graph, confidence/provenance và gate recipe đều nằm trong consistency binding. Cạnh concept không được coi là item index; native vẫn dùng encoding train-only thật. Toy tối đa12 events chưa chứng minh runtime rollover context100.

Message vẫn chỉ nhận mean observed correctness của parent. A2 dùng gate1; A3 nhận module trainable của caller, sigmoid scalar từ `S/(1+S)`, mean confidence, population variance confidence và observed-parent fraction. Mean/variance tính trên ALL declared parents của query, gồm parent chưa quan sát; các giá trị này không được gọi mastery/calibrated confidence. Kernel dùng `sum(c*observed*message)/max(1,mass)`, giữ absolute-confidence effect và signed residual. Test kiểm công thức signed residual riêng; backward tới backbone/message/readout/gate, weights không được optimizer cập nhật.

Disable, graph-empty, no-support và zero observed-confidence mass đi thẳng native tuple trước branch ops. Mixed inactive dùng base logits của chính forward đó; không chạy backbone lần hai để tạo control. Six-op path vẫn khớp pinned NonRasch n_pid0/separate_qaFalse. Oracle bị reject tại normal boundary ngay cả ý định disable. Estimated probability vẫn chỉ mang train-role/provenance do caller khai báo: chưa có estimator, kiểm chứng artifact fit hay calibration. Gate còn là tham số khởi tạo nối được gradient, chưa là gate đã học; gate thấp không chứng minh cạnh causal false.

## Giới hạn kết luận

Đây là software engineering toy A0–A3, không adoption S04/S05, nghiên cứu fitted CG-AKT, epoch trainer/collator hay selected checkpoint. Tắt nhánh chỉ trả backbone cùng model; không thay bằng checkpoint A0 độc lập. System checkpoint fallback vẫn chưa triển khai. SHA/dataclass binding phát hiện drift hợp tác trong process, không chống caller giả toàn metadata/module.

Hai target-file SHA hiện khác raw Gate24 build_hashes. Gate24 lịch sử không bị sửa; không được dùng PASS đó để chứng nhận source A2/A3 hiện tại. Cần refresh software evidence do parent điều phối. Controller attempt03 lưu pre/post hai target files; các helper SHA được reviewer ghi hiện tại, không tái tạo certificate trước khi test.
