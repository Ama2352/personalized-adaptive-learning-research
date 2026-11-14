# Pipeline refit A0–A3 trên Junyi

## Phạm vi

Tiếp nối hồ sơ selected-fit đã niêm phong tại `../junyi-a3-selected-20261114-01/`. Đợt này hoàn thiện đường refit trên TRAIN90, giữ epoch9 của từng biến thể, seed42 và cùng recipe batch128. Confidence và topology tiếp tục giữ bản fit TRAIN80 theo Recipe26. Encoding và cache refit được dựng riêng từ hợp train/selection. Calibration và outer evaluation giữ ngoài tập tối ưu neural.

Epoch plan đóng băng số epoch của nhóm bốn biến thể expert trên fold4. Mỗi biến thể tiếp tục có kết quả riêng để so sánh. Plan giữ trạng thái chưa chọn mô hình thắng chung của hệ thống. Các baseline, learned-graph và thí nghiệm khác trong đề cương tiếp tục được theo dõi ở TASKS.

## Cách triển khai

- Tái dùng `train_epoch`, sampler, Adam và checkpoint/RNG hiện có.
- Model refit khởi tạo mới trên encoding90. Checkpoint selected chỉ cung cấp provenance và số epoch.
- Mở phase refit/calibration của adapter đồ thị qua lineage TRAIN80 riêng, giữ confidence theo tên cạnh. Cache90 phải khớp encoding90 và phase90.
- Tách chuẩn bị encoding/window/context cache trên CPU. Entrypoint chạy thật cần grant, Gate source mới, runtime CUDA và ngân sách của lượt chạy.
- Lưu checkpoint từng epoch và checkpoint partial cùng sampler để nối lại. Mỗi tranche có giới hạn thời gian, giữ phần chưa hoàn tất.

## Tình trạng hiện tại

Đang triển khai và kiểm local. `STATE.json` là điểm tiếp tục. Chưa training refit dữ liệu thật, chưa dùng thêm Modal. Kiểm native CPU dùng fixture tổng hợp và ghi rõ phần admission CUDA được mock. CUDA/Gate trên source mới cần nghiệm thu riêng trước thuê GPU.

## Mốc kiểm local đầu tiên

`tests04.log` đạt 78 ca, gồm hồi quy graph/adapter selected và kiểm refit tổng hợp mới. Với cả A0–A3, chạy liên tục và chạy gián đoạn/nối lại cho model, Adam, RNG Python/NumPy/Torch giống hệt nhau trên CPU. Đường refit giữ đủ target từng epoch và từ chối train trên phase calibration. Có kiểm lineage confidence TRAIN80 khi encoding chuyển sang90. Các fixture admission CUDA được mock riêng, math backbone và trainer chạy native thực trên dữ liệu tổng hợp.

Giữ các lượt chưa đạt. Lượt01 thiếu PYTHONPATH khi collection. Lượt02 bị Git chặn ownership dependency. Lượt03 phát hiện source-row0 trong fixture mới và thông báo lỗi phase chưa tương thích test cũ. Đã sửa fixture sang source-row dương, giữ thông báo có train80 và dùng safe.directory chỉ cho đúng dependency trong tiến trình kiểm. Checkout upstream vẫn được verify commit/remote/content, không thay Git global.

`epoch-plan.json` cùng receipt đã kiểm trực tiếp bốn gói model trên D và xác nhận 9 epoch mỗi model. Refit gồm 142.621 người học và 14.947.674 target mỗi epoch. Tập calibration và outer fold4 giữ riêng. Cache90 và kiểm entrypoint/grant còn tiếp tục.
