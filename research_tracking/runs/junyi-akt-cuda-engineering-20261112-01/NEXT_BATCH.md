# Bước kế tiếp sau Junyi một epoch

## Phần được giữ

Giữ learner roles80/10/10 trên outer-train fold4, vocabulary chỉ train, AKT NonRasch và recipe CUDA. Cohort kỹ thuật không thay thế benchmark chính. Không chuyển trọng số Grade10 sang Junyi vì vocabulary khác. Kết quả selection không dùng để so winner với BKT/GAM lịch sử trên population khác.

## Thứ tự triển khai

1. Producer Junyi selected20epoch/patience3, dừng có checkpoint và counters. Dùng80%train để chọn epoch trên10%selection. Mọi epoch xuất cùng target keys và OOV. Giữ riêng cơ chế resume epoch và resume giữa epoch, chỉ công bố phần đã kiểm.
2. Đóng quyết định epoch bằng external freeze trước refit90 và vocabulary90. Calibration10 chỉ xuất/fit sau checkpoint refit đã ghim. Outerfold4 dùng đánh giá độc lập sau protocol freeze. Holdout giữ tách biệt.
3. Đo workload đại diện gồm chuỗi200token, dataloading/cache, validation batch4, checkpoint và phục hồi. Tái dùng checkpoint khi cùng architecture/data/optimizer/protocol. Đánh dấu rõ workload đã chạy để không trả tiền chạy lại.
4. Typedgraph Junyi dùng artifact `cpu-junyi-graph-reconstruction-20261107-01/graph.json`,835nodes/976edges, liên kết bằng tên exercise. Trong vocabulary320 hiện có336cạnh với cả hai đầu fitted. Giữ identity graph đầy đủ và báo riêng availability.
5. A1 expert dùng cùng math `ResearchGraphNative` và backbone khởi tạo chung. Context chỉ đọc prefix của đúng nativewindow trước vị trí target, giữ OOV barrier100/100. Kiểm graph-off/emptygraph bằng checkpoint cùng trọng số.
6. Confidence Junyi phải fit từTRAIN80, có provenance. Module Method24 hiện gắn48learner/28concept của Grade10. Cần candidatepool hữu hạn, sàng support chỉ TRAIN trước fit, giữ ba learner-fold/min20eligiblelearners/200bootstrap. Không quét835×834×3fits. Không gọi confidence dự báo là xác suất cạnh đúng.
7. Sau confidence, nối A2/A3, lưu alpha/gate/message/confidence/graph-off và noise sensitivity. Không đổi cấu trúc graph theo điểm selection để có kết quả đẹp.

## Dự toán từ phép đo và phần còn chưa đo

Phép đo A10 hiện có2,695624giây cho315window/79updates. Native train chính có232.662window, tương ứng58.166batch/epoch nếu giữ batch4. Nội suy tuyến tính theo window cho khoảng1.991giây train/epoch. Đây là phép tính từ cohort nhỏ, chưa là runtime fullJunyi đã đo. Chuỗi dài, padding, I/O và vocabulary khác có thể đổi tốc độ.

Ba hệ số thời gian1×/2×/4× cho training tương ứng khoảng0,55/1,11/2,21giờ/epoch. Chưa cộng validation/refit/calibration/storage hoặc failure reserve. Không dùng các con số này làm cam kết tổng chi phí.

Modal niêm yết A10=0,000306USD/giây, L4=0,000222, T4=0,000164; CPU Functions0,0000131/core/giây vàRAM0,00000222/GiB/giây. CPU/RAM SandboxVM có giá3×, cần dùng đúng hệ số khi cấp dự phòng. Với A10+trần2core/8GiB, nội suy train nói trên tương ứng khoảng0,70/1,39/2,79USD/epoch, chưa validation. Giá đọc ngày12/11/2026. [Nguồn Modal](https://modal.com/pricing)

Tổng phải tính bằng số epoch selected thực tế, epochrefit bằng epoch đã freeze, số variant/graph condition và chi phí đánh giá. Ví dụ minh họa5selected+5refit có trainrefit90 lớn hơntrain80, khoảng10,6đơn vị train80 trước validation. Một model có thể cần khoảng7,4USD ngay ở kịch bản tuyến tính thuận lợi. Bảy model Junyi theo ví dụ đó vượt30USD. Đây là cảnh báo dự toán có điều kiện, chưa xác định số epoch của Junyi.

Đo đại diện và tối ưu thực thi trước khi cấp full allocation. Giữ ma trận được phê duyệt trong sổ công việc. Mọi giảm condition/model hoặc thay protocol cần được ghi quyết định rõ. Kết quả chính RQ3 trong simulator tiếp tục là đường bằng chứng riêng, Junyi cung cấp đối chiếu dự báo trên dữ liệu thực.
