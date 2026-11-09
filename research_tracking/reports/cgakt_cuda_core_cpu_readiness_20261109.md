# Chuẩn bị core CUDA và kiểm tương thích CPU của AKT/CG-AKT

Ngày 09/11/2026. BatchA bổ sung hợp đồng thiết bị cho core theo quyết định28. Root và reviewer độc lập đọc nguồn trước khi chạy hai lượt kiểm local trong `.venv`.

## Thay đổi đã kiểm

`ResearchCUDAExecutionProfile` quy định một CUDA device0, FP32, seed42, allocator budget tường minh và các backend flags đã chọn. Validator chỉ nhận config research CUDA khi caller truyền đúng typed profile qua keyword. Lời gọi validator mặc định tiếp tục dùng hợp đồng CPU. Các fields và defaults của AKTConfig được giữ như trước. [Quyết định thực thi](../../docs/thesis_recovery/28_CUDA_EXECUTION_PROFILE_V1.md).

Core có explicit device cho tensor, collate và seals. Backbone vẫn đi qua loader upstream thật, khởi tạo trong CPU context rồi chuyển theo config CUDA. Toàn wrapper được đặt đúng device trước khi lưu parameter ownership. Adam dùng CPU ambient context để scalar step phù hợp với hợp đồng noncapturable/nonfused. Inference có bảo toàn RNG của đúng CUDA device và đồng bộ tại boundary. Các kiểm backend/allocator này còn cần xác nhận trên máy GPU đích.

CPU identity tiếp tục bỏ field profile khi giá trị None. Danh mục source được bổ sung dependency `device_budget.py`, vì vậy source identity mới cần software Gate mới.

## Kết quả local thực tế

| Lượt | Population | Kết quả | Thời gian | Trần |
|---|---|---|---:|---:|
| Metadata/config |13unittest methods|13đạt, Torch/NumPy/Pandas chưa import|0,4977573giây|10giây|
| Model compatibility |26pytest cases|26đạt,0failure/error/skip|27,7877699giây toàn outer|90giây|

Lượt mô hình quan sát một backbone, một wrapper, một gate, tám forward và năm logical backward. Có0Adam constructor/step. Dữ liệu kiểm được dựng tay, batch tối đa2×6 với geometry research hiện hành. Child đo26,0589449giây, log pytest12,17giây. Các clock lồng nhau có scope khác nhau.

Source31 trước/sau trùng nhau. Genuine upstream loader được gọi một lần, dùng đủ mười lệnh Git local theo allowlist và EOL proof hiện hành. Cleanup đã đưa owned Job về0, monitor dừng và các method/runtime/environment được khôi phục. Torch thực tế là2.7.1+cpu, CUDA chưa khởi tạo.

Peak RSS lấy mẫu là280629248bytes. Mức RAM khả dụng thấp nhất là1850941440bytes, cao hơn floor1536MiB của allocation unit CPU này. Root chọn floor riêng dựa trên lượt trước cùng geometry có peak277712896bytes. RSS cap vẫn1GiB, child80/owned87/whole90giây và cleanup reserve3giây.

## Bằng chứng và bước kế tiếp

[Bundle theo run](../runs/cgakt-cuda-core-cpu-engineering-20261109-01/README.md) giữ source trước/sau, allocation, reviews, logs, JUnit, native counters và raw receipts của hai lượt. Inventory kiểm SHA trước copy và so lại nguồn/bản sao sau copy.

Core đã qua kiểm tương thích trên CPU. Checkpoint CUDA schema2, Main CUDA wiring, source/runtime/Gate trên Linux/GPU thực tế, recovery và throughput là các bước tiếp theo. Chưa có run Modal trong batch này. Các kết quả trên phục vụ mức sẵn sàng phần mềm cho RQ3, còn so sánh mô hình fitted và kết quả học vòng kín cần thí nghiệm riêng.
