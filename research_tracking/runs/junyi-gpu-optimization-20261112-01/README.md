# Junyi GPU — Gate CPU02 và probe T4 chưa nghiệm thu

Bundle đang mở. Trạng thái hiện tại là **GPU probe FAILED tại kiểm parity**, giữ nguyên các checkpoint và logs để chẩn đoán số học. Các số liệu trong gói là kiểm kỹ thuật trên cohort Junyi có giới hạn.

## Diễn tiến đã xác nhận

1. CPU01 gặp hai lỗi fixture dependency. `cpu01-review.json`, XML và logs giữ các ca lỗi. App đã được đối chiếu trạng thái stopped; phần stop idempotent và fixture được sửa trước CPU02.
2. CPU02 đạt **2.197tests,0failure/error/skip** trong106,06giây. `cpu-execution02.log` và receipt trong `experiments/akt/results/modal-junyi-optimization-cpu-20261112-02/` ghi Gate PASS, archive tải về và inventory đã kiểm. Gate này gắn snapshot `source02.zip` của lượt probe.
3. Lượt L4 không được cấp task/container. `l4-no-container-proof.json` giữ callgraph trống task ID, App stopped/tasks0 và watchdog đã xác nhận dừng sau queue deadline. Worker GPU chưa bắt đầu ở lượt L4.
4. Lượt T4 thực sự training A0 trên256train learners của cohort320,11.833target/epoch. Đã hoàn thành **5epochs,395optimizer updates,59.165training target exposures**. Mỗi validation có1.530target,1.405supported và125OOV.
5. Terminal của fit là `PARTIAL_SELECTED_ONLY_NOT_FINAL`, selected epoch còn null, external freeze false. Lượt5epoch là workload kiểm có giới hạn, chưa hoàn tất early stopping envelope của selected fit chính.
6. Sau fit, worker nạp checkpoint epoch5 và so legacy prediction với batched prediction trên cùng1.530target. Kiểm metadata và OOV được thực hiện trước guard xác suất. Worker dừng ở `assert maximum_delta<=1e-6`; receipt tổng là `FAILED`.

`t4-fit-terminal.json` và `t4-training-observed.json` giữ counters/validation/resource đã đọc từ artifact. Các BCE của cohort selection phục vụ chẩn đoán kỹ thuật, chưa được dùng như benchmark Junyi chính hoặc kết luận RQ3.

## Checkpoint và artifact được giữ ở đâu

- Archive local tại `experiments/akt/results/modal-junyi-optimization-t4-20261112-01/artifacts.zip`,380.459.327bytes. `receipt.json` bên cạnh xác nhận hash/size/inventory tải về khớp.
- Receipt có **15checkpoint transfers** của cùng lượt fit, gồm5snapshot inner-batch,5snapshot train-epoch và5snapshot post-validation epoch. Mỗi checkpoint có `state.pt`, `metadata.json`, `COMPLETE.json` cùng SHA trong receipt.
- Bản durable thuộc Modal Volume `kltn-akt-modal-junyi-optimization-t4-20261112-01`, thư mục run/checkpoints. Receipt và manifest của bundle cung cấp danh sách tên checkpoint; archive local là đầu mối đọc độc lập hiện có.
- Logs failure nằm trong archive ở thư mục `...-operation/failure.log` và `...-driver/failure.log`. Worker source snapshot `gpu_worker.py` ghi guard parity và vị trí gọi recovery.

Các file checkpoint đã được lưu và đối chiếu khi tải artifact. Kiểm phục hồi CUDA của lượt này **chưa được gọi**, vì `verify_native_recovery(...)` nằm sau guard parity đã thất bại. Con số giới hạn553updates/82.831targets trong request gồm phần recovery dự kiến; counters thực đã quan sát là395/59.165.

## Vấn đề đang chờ giải quyết

Ngưỡng1e-6 đã bị vượt tại parity legacy/batched. Giá trị maximum cụ thể chưa được ghi vào result terminal vì assertion xảy ra trước bước ghi kết quả thành công. Nguyên nhân số học đang do nhánh chính chẩn đoán trên checkpoint có sẵn. Bundle được giữ mở để bổ sung bằng chứng, không đổi nhãn probe thành PASS.

Gate CPU02, code recovery đã triển khai hoặc các unit tests chưa chứng minh recovery thật của T4 đã thành công. Full Junyi selected/refit/calibration và các graph fits vẫn cần artifact thực thi riêng. Các thay đổi nguồn tiếp theo cần Gate đúng snapshot trước GPU.

## Hạn mức và bước tiếp

`allocation.json` giữ trần tranche0,50USD, dự phòng CPU0,12USD và hai GPU attempts mỗi lượt0,18USD, tổng reservation0,48USD. Các file billing-before là snapshot trước lượt. Chi phí cuối cần đối chiếu metering cập nhật của nhánh chính. Tổng dự án tiếp tục chịu trần30USD free credits và các tranche nhỏ theo ủy quyền hiện hành.

Bước tiếp là xác định parity mismatch từ artifact đã giữ, nghiệm thu nguồn sửa cần thiết, rồi kiểm recovery có giới hạn. [Gói lifecycle và full train-window cache](../junyi-lifecycle-20261112-01/README.md) ghi riêng chuẩn bị dữ liệu quy mô lớn. [Gói numerical diagnostic](../junyi-numerical-diagnostic-20261112-01/) là nơi nối tiếp chẩn đoán; trạng thái của nó do nhánh chính cập nhật.
