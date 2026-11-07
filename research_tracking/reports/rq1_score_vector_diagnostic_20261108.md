# RQ1 — điểm số thay đổi có đi tới quyết định không?

Phân tích bổ sung ngày08/11 từ [pilot fixed-stream cũ](../runs/cpu-rq12-20261107-03/README.md), không chạy lại model/simulator hoặc thêm learner. [Bundle mới](../runs/rq1-score-vector-20261108-01/README.md) có7outputs/SHA; [analysis.json](../runs/rq1-score-vector-20261108-01/analysis.json) và [event_flags.csv](../runs/rq1-score-vector-20261108-01/event_flags.csv) cho phép trích dẫn từng trường hợp. Đây là mở rộng mô tả của [bảng PMRA](rq1_transition_evidence_20261108.md), không thay kết quả cũ hoặc protocol.

## Phân biệt đại lượng

P là xác suất cho câu hỏi đang có trong log. S là **vector mastery_score của nguồn** cho28concept, không tự được xem là xác suất đã hiệu chỉnh hoặc latent mastery. M là tập boolean `is_mastered` đã ghi, không lấy S≥0,5 để thay thế. R là ready set và A là **concept preview** từ bản sao policy; chưa phải hoạt động được phục vụ trong closed loop.

Mỗi comparison có1.080event pairs và30.240concept-score pairs. Thay đổi được tính bằng so sánh số đã lưu chính xác; không tự chọn ngưỡng epsilon theo kết quả. Các tổng theo snapshot và theo concept có mẫu số khác nhau.

| Đại lượng | Graph package − graph-free | Empty-graph package − graph-free |
|---|---:|---:|
| P đổi | 964 | 37 |
| Ít nhất một phần tử S đổi | 1.080 | 267 |
| Số concept-score pairs đổi | 27.017/30.240 | 454/30.240 |
| M đổi ở ít nhất một concept | 90 | 0 |
| R đổi | 60 | 0 |
| A concept preview đổi | 22 | 0 |
| S đổi nhưng M giữ nguyên | 990 | 267 |
| S đổi nhưng A giữ nguyên | 1.058 | 267 |
| Mean absolute delta S trên toàn concept-score pairs | 0,005283 | 0,00003716 |
| Max absolute delta S | 0,019699 | 0,006630 |

Kết quả trực tiếp hỗ trợ phát biểu có giới hạn: **trong pilot này, thay đổi điểm số thường không đi cùng thay đổi quyết định mastered hoặc concept preview**. Nó không chứng minh các bước tạo thành funnel nhân quả lồng nhau. S có thể chứa graph context trực tiếp; thay đổi S không đồng nghĩa mô hình đo knowledge state chính xác hơn.

Hai event có P giữ nguyên nhưng A đổi là seed20001/PY/event47 và seed20002/PG/event69. Cả hai có25phần tử S đổi. Vì P chỉ là câu hỏi đang log còn selector dùng thông tin rộng hơn, không được xem hai event này là bằng chứng mọi xác suất/trạng thái đầu vào policy đều giữ nguyên. Mọi snapshot của full package đều có S đổi, nên hai trường hợp này chưa phân biệt được nguyên nhân; quần thể S giữ nguyên rỗng cũng không cho phép kiểm tính cần thiết của S. Đồng biến S/A chưa chứng minh mediation.

## Dự đoán có cải thiện không?

Tính lại Log Loss/Brier trên cùng paired labels;18seed×profile×candidate aggregates khớp kết quả cũ trong tolerance1e-12. Không dùng S làm probability cho các metric này.

| Graph package, seed block | ΔLog Loss | ΔBrier | M đổi | A đổi |
|---|---:|---:|---:|---:|
| 20000, 360pairs | −0,000889 | −0,000443 | 0 | 0 |
| 20001, 360pairs | −0,000719 | −0,000361 | 18 | 17 |
| 20002, 360pairs | −0,000473 | −0,000290 | 72 | 5 |
| Pooled, 1.080pairs | **−0,000694** | **−0,000365** | 90 | 22 |

Các delta âm này là cải thiện mô tả nhỏ trong pilot; chỉ có3seed blocks với3profile lặp trong mỗi block, không có CI/p-value xác nhận hoặc tuyên bố hiệu quả thực tế. Pooled che khác biệt profile sau đây (mỗi profile360pairs, mean trên3seed cùng kích thước):

| Profile | ΔLog Loss | ΔBrier | M đổi | A đổi |
|---|---:|---:|---:|---:|
| PG | **+0,002558** | **+0,001165** | 86 | 20 |
| PY | −0,002998 | −0,001450 | 0 | 2 |
| PYH | −0,001641 | −0,000809 | 4 | 0 |

PG có predictive loss xấu hơn ở cả3seed-profile rows dù chiếm20/22action-preview changes; không được nói graph package cải thiện mọi profile. Đây là mô tả dị biệt điều kiện, chưa là causal effect của general ability: các profile có thể khác nhiều thành phần và chưa có controlled ability contrast.

Pooled empty-graph package cũng có delta âm nhỏ (Log Loss−0,00005660; Brier−0,00002603), nhưng seed20000 có delta dương. Không gọi empty-graph package tương đương graph-free: nó vẫn có các pathway không phụ thuộc cạnh. Exact float inequality chỉ đo khác giá trị số đã lưu, không tự chứng minh khác biệt S đủ lớn, có ý nghĩa học tập hoặc được calibration đúng.

## Có thể và chưa thể kết luận

- Đã có bằng chứng cụ thể cho một cơ chế RQ1: thay đổi score có thể chưa đủ đổi decision/action preview; seed20000 minh họa score và P đổi trong khi M/R/A không đổi.
- Empty-graph control tiếp tục cho thấy phải tách graph edges khỏi toàn bộ graph package. Không quy mọi delta thành lợi ích của prerequisite edges.
- Chưa đo calibration của S quanh ngưỡng mastery hợp lệ; điều này cần S04 định nghĩa reference/mastery/calibrator, không thể suy từ Log Loss của P hoặc score nhỏ hơn/lớn hơn0,5.
- Chưa có full closed-loop P/S/M/R/A trace hoặc learning-gain causal mediation. Fixed-stream log cũ thiếu item/time để kiểm độc lập shared-stream identity; provenance nguồn vẫn là cơ sở của điều kiện common stream.

Reanalysis dùng validator và bounded gzip reader đã có, kiểm SHA bundle nguồn, so paired identities và legacy loss/Brier; không thêm test/model run hoặc đổi seed. Source helper và copy inventory nằm trong bundle. Dataset Junyi, Holdout, checkpoints lịch sử và credit Modal không được truy cập/thay đổi trong phép phân tích này.
