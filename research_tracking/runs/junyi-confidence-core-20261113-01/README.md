# Lõi confidence Junyi theo cửa sổ AKT

Ngày13/11/2026. Đã triển khai API phát feature theo target và fit từng child trên CPU, phục vụ A2/A3. Chưa fit confidence trên Junyi thật, chưa xuất artifact được model A2/A3 nhận và chưa train neural model mới.

## Cơ chế đã triển khai

`src/knowledge_tracing/akt/research_junyi_confidence.py` nhận native TrainingWindow và JunyiGraphPhaseSession train80. Tại target, feature chỉ lấy đáp án quá khứ trong đúng cửa sổ. Base gồm mean correctness Laplace của child, mức hỗ trợ child, mean correctness chung và mức hỗ trợ chung. Augmented thêm hai feature mean/support của parent. Có giữ declared parent chưa quan sát với count0. Câu trả lời hiện tại chỉ làm nhãn học surrogate.

Iterator phát từng target, giữ bộ đếm của một cửa sổ và feature của các parent cần dùng. API cho phép worker tương lai spool theo child trên D. Chưa có worker spool trong gói này. Fitter chỉ giữ dữ liệu một child trong max_rows tường minh. Có caps target/window/fit count và thời gian hợp tác. Khi chạy fit thật vẫn cần watchdog ngoài tiến trình cho timeout/RAM.

Solver, probability, Log Loss và learner bootstrap tái dùng các primitive của `edge_confidence.py`. Giữ recipe Method24 gồm3fold người học, C1/tol1e-6/max_iter200, bootstrap200 và tối thiểu20eligible learners. Confidence là tỷ lệ bootstrap mà mean chênh lệch Log Loss theo learner dương, thể hiện predictive stability. Không gán thành xác suất cạnh đúng hoặc hiệu quả dạy học nhân quả.

Adapter dùng feature_recipe `junyi-effective-native-window-surrogate-v1`, thay full-history mô phỏng bằng cùng cửa sổ của model Junyi. Chia fold dùng `junyi-train80-surrogate-learner-rank-v1`, fingerprint tập learner một lần rồi hash từng learner. Thuật toán có phiên bản riêng để xử lý quy mô lớn, không sửa hàm Method24 lịch sử. Các learner của selection/calibration/outer-validation bị từ chối ở ranh giới view và membership của fitter.

## Kiểm đã đạt

tests02 ghi51ca đạt và11kiểm phụ khi chạy cùng graph/roles. Sau bổ sung lưu summary và kiểm ledger, tests03 ghi8ca confidence đạt trong2,39giây. Các ca kiểm gồm vocabulary717, label hiện tại/tương lai, OOV reset, rollover loại lịch sử cũ, chia fold ổn định, target trùng/caps, schema đầu vào và solver crossfit thật trên dữ liệu giả.

`crossfit-summary.json` giữ kết quả thực của kiểm solver, bao gồm500child targets,50learner tổng hợp,12fit slots,1.500OOF rows và summary cho3parent. Ledger ghi digest đúng các hàng fit đã loại fold người học đánh giá. Parent UNFIT có0eligible targets và confidence null kèm reason. Đây là kiểm chức năng, các score trong file không được dùng làm kết quả nghiên cứu hoặc artifact confidence Junyi chính.

Summary được chuyển từ thư mục test sau khi inventory SHA và đối chiếu lại. transfer-receipt.json giữ nguồn/đích/hash. Logs và JUnit giữ ở cùng bundle. Không dùng GPU hoặc Modal trong gói này.

## Điều kiện còn thiếu trước A2/A3

1. Worker spool theo child từ cache train80 đã ghim, dùng lại fold index đã bind để tránh tính lại cho từng child, kiểm đủ target và giới hạn RAM/CPU/D.
2. Manifest nguồn, runtime, encoding, view, graph và recipe cùng ledger/OOF/score xuất đầy đủ. Chỉ complete artifact mới được nạp.
3. Loader confidence giữ unsupported/null/reason và phân biệt supported score0, kiểm mọi declared edge, thiếu/thừa/duplicate và oracle contamination.
4. Nối artifact vào JunyiGraphCondition/PhaseSession/adapter/selected producer A2/A3, giữ cùng geometry và tham chiếu A0. Cập nhật candidate ID/status đúng từng condition.
5. Kiểm native gradient/gate/graph-off/checkpoint trên CPU, kiểm source mới trên T4 rồi tính chi phí cả ma trận trước H100.

Trạng thái gói là CONFIDENCE_FEATURE_AND_CHILD_CROSSFIT_CPU_VERIFIED. A2/A3 Junyi chưa được cấp trạng thái training-ready từ các kiểm này.
