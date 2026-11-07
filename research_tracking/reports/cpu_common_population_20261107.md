# Junyi: đối chiếu order trên cùng quần thể quan sát

## Câu hỏi và nguồn

Run `cpu-junyi-common-20261107-01` tái dùng đúng base976edges và ba graph controls của `cpu-junyi-controls-20261107-02-expanded`. Không sinh graph mới, không chọn lại seed. Đọc lại256inner-train learners của outer-fold0, tối đa300events/learner,12.575events. Frozen catalog/split/assignment/canonical-manifest SHA giữ nguyên. Cohort hash trùng nguồn; cả ba order summaries gốc được tái lập chính xác. Analysis2.39s, giới hạn180s. Không correctness, Holdout, training hoặc p-value/CI.

Đây là sensitivity chẩn đoán Trap3/RQ2, không phải estimand xác nhận cuối đã được advisor duyệt. Artifact và source hashes trong `runs/cpu-junyi-common-20261107-01/manifest.json`; số liệu trong `common_population.json`.

## Vì sao cần phép tính mới

Bảng trước gộp edge–learner pairs co-observed, denominator649/650/644/645 tùy graph. Người học có nhiều concepts và graph có nhiều parent được quan sát sẽ có trọng số lớn hơn. Matching degree/topic/support-bin không giải quyết hết điều đó.

Phép tính bổ sung giữ cùng observed `(learner,child)` có incoming edge ở cả graph; incoming degree theo child được giữ bằng nhau. Với mỗi child chia số parent thuộc từng category cho toàn bộ incoming degree: xuất hiện trước child theo timestamp, xuất hiện sau, cùng timestamp, chưa quan sát trong prefix. Sau đó trung bình qua child trong learner và cho mỗi eligible learner trọng số bằng nhau. Missing trong prefix là thiếu quan sát, không là prerequisite sai/chưa mastery.

Sensitivity thứ hai chỉ giữ learner–child có ít nhất một incoming parent co-observed ở cả graph, và báo rõ attrition. Đây vẫn là tập chọn theo khả năng quan sát của graph, không biến thành counterfactual instructional experiment. Các controls có intersection khác nhau; không gộp hay xếp hạng chúng như cùng target population. Ties không bị source-row tie-break ép thành before/after; pilot này không có timestamp tie trong các cơ hội được tính.

## Kết quả chẩn đoán

239/256learners có ít nhất một observed child có prerequisite. Có1.361learner–child opportunities chung. Base learner-weighted prior-parent fraction0.1658617 và unobserved-parent fraction0.8208524. Đây là trung bình phân cấp theo learner/child, không phải82% tổng số prerequisite của toàn Junyi bị thiếu. Không so trực tiếp với575/649parent-first pairs ở bảng cũ vì khác estimand và denominator.

| Control seed | Opportunities có parent set đổi | Δprior fraction, control−base | Learners thay đổi prior fraction | Common-coobserved opportunities | Common learners | Δprior trên common subset |
|---|---:|---:|---:|---:|---:|---:|
|0|43|+0.00069735|1/239|569|96|0|
|1|42|−0.00117904|7/239|564|96|−0.00308262|
|2|12|−0.00083682|1/239|566|95|0|

Identity negative control cho tất cả239learners có contrast đúng0 trên cả bốn categories. Synthetic tests kiểm learner weighting, missingness, timestamps, sign reversal, no-label access và scope/caps. Không loại seed0/2 dù common prior contrast0.

## Ý nghĩa và việc còn thiếu

Controls hiện tại chỉ làm thay prior score của1–7learners trong mỗi comparison. Độ nhạy thấp là một hạn chế của thiết kế pilot; không đủ kết luận graph trung tính, tốt hơn hoặc kém hơn. Missing observation chiếm phần lớn estimand mới, và intersection chỉ giữ khoảng41–42%opportunities. Zero contrast có thể do ít cơ hội chịu thay đổi, không phải bằng chứng hệ graph không tác dụng.

Trước confirmatory Junyi comparison cần chốt estimand/coverage rule, phân tầng history/support chỉ từ training, kiểm exposure perturbations và không chọn control theo correctness hoặc kết quả mong muốn. Tăng số swaps/targeting theo exposure hoặc thay constraints cần protocol riêng; chưa thực hiện trong run này. Kết luận nhân quả về sequencing vẫn phải dựa controlled simulator, không suy từ order alignment của logs.

RQ2 hiện có bằng chứng chẩn đoán ba bẫy, chưa hoàn tất bằng chứng xác nhận điều kiện hiệu quả. RQ1/RQ3 không được đánh dấu hoàn thành từ phân tích này.
