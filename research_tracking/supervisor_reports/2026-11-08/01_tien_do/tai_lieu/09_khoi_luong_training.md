> Bản đọc kèm gói ngày08/11. Nội dung giữ nguyên; chỉ chỉnh đường dẫn tương đối. Nguồn gốc và SHA xem NGUON.json.

# Hạch toán lượt huấn luyện: điều kiện khác phase tối ưu

08/11/2026 · **Đính chính đơn vị dự toán, không đổi phương pháp hoặc cấp quyền chạy.** Giữ nguyên bytes protocol21 và các run đã đóng. Nguồn: [21, mục2–3](../../../../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), SHA `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6`, và [lifecycle22](../../../../../docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md). Root và reviewer độc lập đối chiếu cùng quy tắc train80→raw-selection10→fresh-refit90→calibration10 áp dụng ở cả hai môi trường.

Protocol21 ghi simulator “9neural fits” cạnh Junyi “18phases”. **Không được cộng9+18 thành27lượt tối ưu thực tế.** Số9 ở đây đếm điều kiện mô hình, trong khi18 đếm phase tối ưu trọng số. Allocation đủ lifecycle cho mọi điều kiện có số danh nghĩa:

| Đại lượng | Simulator | Junyi | Tổng |
|---|---:|---:|---:|
| Điều kiện neural: A0; A1/A2/A3×expert/learned; SAKT; GKT |9|9|18|
| Selected-fit80 (nhiều epoch, raw-selection10) |9|9|18|
| Fresh-refit90 tại selected epoch |9|9|18|
| **Phase tối ưu neural dự kiến** |**18**|**18**|**36**|
| Prediction trên calibration + fit temperature (không neural optimization) |9|9|18|

Đây là planned allocation, **không36lượt đã chạy, không36epoch và không GPU runtime/cost đã đo**. Pilot A0 chỉ được reuse như một ô của matrix nếu đúng cùng corpus/source/config/split/seed và freeze ordering; pilot trước khi có raw-selection mọi candidate không tự thành main winner/refit hợp lệ. Không mặc định cộng pilot thêm36, cũng không mặc định pilot thay được ô chính.

Không đếm lại A0 khi đổi estimator graph. A1–A3 expert/learned là sáu điều kiện độc lập; A3 graph-off cùng weights là ablation, không checkpointA0 train riêng. Hai môi trường vocabulary khác nhau nên không share checkpoint/optimizer. Shared initialization giữa variants không xóa phase train/refit. Checkpoint reload/resume không tự là phase mới nếu đúng lineage; restart fresh vì lỗi làm tăng actual cost và phải giữ receipt.

## Các khoản36phase chưa bao gồm

- GAM/Graph-GAM matched fits và native BKT/GAM simulator references; historical BKT không rerun EM.
- Learned-graph/confidence surrogate cross-fitting,200learner bootstraps, graph realizations và preprocessing.
- Epoch validation, best-checkpoint reload/export, calibration prediction/Tfit, inference reference84items/step, controller và closed-loop evaluation.
- Smoke/throughput/recovery/failed attempts, environment/image/storage/startup/CPU/RAM hoặc artifact transfer.
- Noise retraining/extra training seeds/learning curves. Frozen-checkpoint sensitivity không có neural refit nhưng vẫn tốn inference.

Vì vậy tổng giá không phải36×một fixed GPU giờ đoán. Mỗi phase có targets/windows/epochs/throughput/overhead riêng. Dự toán sau benchmark dùng `sum(rate_device × seconds_phase + CPU/RAM/storage/startup)`, gồm cả inference và failure reserve. Thời gian unknown ghi null, không0. Chỉ $30free credits, trả thêm0; không tự cấp GPU hoặc fallback trả phí.

Nếu budget không đủ, staged execution có thể chỉ hoàn thành một phần allocation và ghi rõ missing comparisons. Thay sang “refit chỉ winner” làm thay đổi evidence availability của comparator matrix; cần versioned decision trước chạy, không dùng đính chính này để âm thầm bỏ model/required evidence. FullCV/Holdout/paid runs vẫn cần quyền riêng.

[Allocation machine-readable](../../../../../docs/thesis_recovery/EXPERIMENT_ALLOCATION_V1.json) mô tả cùng36phase danh nghĩa, không lịch chạy đã phê duyệt. Mọi actual accepted phase cần checkpoint/source/target/optimization receipts, không suy từ JSON khai báo.
