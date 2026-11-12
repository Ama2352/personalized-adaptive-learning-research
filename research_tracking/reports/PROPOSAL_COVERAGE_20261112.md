# Đối chiếu mức bao phủ đề cương — 12/11/2026

## Căn cứ và cách đếm

Đối chiếu PDF đề cương5trang do người dùng cung cấp. File Desktop hiện tại khớp SHA của bản đã đọc08/11, bản trích cũng khớp inventory. Nội dung mục tiêu cụ thể ở trang2, phương pháp trang3–4 và kết quả mong đợi trang4–5. Không phát sinh training hoặc thực nghiệm trong lần đối chiếu này.

Đếm theo đúng sáu mục tiêu cụ thể. Cả6 mục đã có công việc hoặc bằng chứng, chưa mục nào được đóng nghiệm thu toàn phạm vi. Đây là độ bao phủ công việc, không chuyển thành phần trăm hoàn thành KLTN. Mã chạy, pilot, fit trên selection và kết quả đánh giá độc lập có mức bằng chứng khác nhau.

## Sáu mục tiêu cụ thể

| Mục tiêu trong đề cương | Đã đạt đến hiện tại | Còn thiếu để nghiệm thu | Trạng thái |
|---|---|---|---|
| 1. Tái lập kết quả đối chứng trên cùng dữ liệu, tiền xử lý và giới hạn thông tin | Có kết quả BKT/GAM-KT Development đã lưu, shared evaluator, split learner-disjoint và kiểm train-only vocabulary. Grade10 có7selected fits AKT. Junyi A0 có2epoch full train | Chốt bảng đối chứng đầy đủ AKT/SAKT/GKT/GAM/Graph-GAM, common target population, đánh giá độc lập và phạm vi tái hiện paper | Một phần |
| 2. Phân tích chuỗi dự báo → thành thạo → lựa chọn | Fixed-stream1.080paired snapshots, tái chạy observer giữ parity, định lượng thay đổi dự báo và hành động. Có phân tích ready/exposure và native mastery trên28concepts | Khép calibration quanh ngưỡng, kiểm độ đúng mastery ở phạm vi rộng hơn và nối kết quả học dưới intervention kiểm soát | Một phần, đã có phát hiện |
| 3. Đánh giá chất lượng đồ thị, lịch sử và đặc điểm người học | Có đối chứng ability×cơ chế,120world trên10block mới, so expert/learned, bootstrap thăm dò và kiểm order-controls Junyi | Ma trận nhiễu cạnh, lịch sử ngắn/dài, khái niệm thưa/dày và nội/liên chương theo kế hoạch xác nhận | Một phần, đã có phát hiện |
| 4. Xây CG-AKT gồm confidence và fallback | Có A0–A3, bảy điều kiện expert/learned đã fit chọn epoch trên Grade10, checkpoint/predictions được giữ. A1 Junyi có kiểm producer CPU | Junyi confidence/topology và A2/A3 producer, CUDA graph fits, freeze/refit/calibration và fallback được đánh giá theo protocol chính | Một phần, có mô hình đã train |
| 5. Đánh giá dự báo, calibration, robustness, lộ trình, closed-loop và thống kê | Có metric baseline, thống kê pilot, chẩn đoán retention/controller, factorial và bootstrap theo block. Hợp đồng benchmark đã xác định metric/figure | Bảng so sánh độc lập mô hình hiện đại, robustness/ablations, closed-loop chính và kiểm định theo family đã định trước | Một phần |
| 6. Demo minh họa và đối chiếu cấu hình | Demo xem evidence và quỹ đạo đã lưu có kiểm API/UI, báo cáo HTML có figure nguồn | Nối checkpoint fitted và chọn bài cho hồ sơ mới, calibration/mastery, so sánh đầy đủ cấu hình, hoàn thiện bản thảo KLTN | Một phần |

Các nguồn gồm [bảng training AKT](AKT_TRAINING_STATUS_20261112.md), [chuỗi quyết định RQ1](rq1_transition_evidence_20261108.md), [native mastery toàn miền](rq1_fixed_time_ability_native_panels_20261110.md), [120world mới](rq2_fresh_graph_source_replication_20261110.md), [bootstrap theo block](rq2_fresh_block_uncertainty_20261110.md), [demo](demo_closed_loop_readiness_20261108.md) và [hợp đồng benchmark](AKT_BENCHMARK_CONTRACT_20261112.md).

## Tái hiện hai paper đến đâu

### Paper1

PDF là nguồn chuẩn thiết kế và kết quả kế thừa theo xác nhận của tác giả. Đã cài phiên bản nghiên cứu theo đặc tả PDF, kiểm28concepts/84items và hai graph25/31edges. Hai continuity episodes B1/GA dùng cùng một profile US, seed42 và coupling concept-local đã chạy, cùng hoàn tất172feedback và trạng thái latent cuối bằng nhau. Đây là kiểm tích hợp prospective có provenance riêng. B0, toàn bộ policy/profile/seed matrix và toàn bộ bảng PDF chưa được chạy tái hiện.

Đã có kết quả chẩn đoán mới. Với DAG nội chương, không forgetting/reset và controller liên tục theo đặc tả, có chứng minh điều kiện đủ để re-entry bằng0. Có phản ví dụ liên chương cho ranh giới điều kiện. Cùng local tape/update và cả hai branch hoàn tất cũng có kết quả bất biến terminal có điều kiện. Các kết luận có điều kiện này bổ sung lý giải cho KLTN, không thay các kết quả công bố.

Nguồn gồm [kiểm episode domain28](paper1_seeded_domain_smoke_readiness_20261109.md), [cơ chế re-entry](paper1_reentry_mechanism_20261109.md) và [bất biến concept-local](paper1_concept_local_invariance_20261109.md).

### Paper2

Đã tìm được source, frozen results, cấu hình và chứng nhận của artifact công bố. Đã kế thừa các bảng replay/closed-loop/Junyi và giữ phạm vi protocol gốc. Có tái chạy fixed-stream diagnostic3seeds×3profiles×120steps với observer, giữ exact probabilities/state/mastery/ready/action/labels của pilot cũ. Đây là parity của pilot chẩn đoán KLTN dựa trên nguồn Paper2. Chưa có bằng chứng đã rerun toàn bộ quy mô paper và tái lập mọi bảng công bố từ đầu.

Đã có kết quả nghiên cứu tiếp nối. Trong1.080paired snapshots,964lần scalar prediction khác nhưng chỉ22lần action preview khác. Với luật quên đồng nhất đang xét, retained net gain14ngày bằng exp(−0,84) nhân final net gain, nên hai chỉ tiêu không tạo thứ hạng độc lập trong điều kiện đó. Đối chứng mới120world/10block và các kiểm Junyi order-controls tiếp tục tách vai trò đồ thị, ability và cơ chế môi trường. Những kết quả này có giới hạn simulator, graph cố định và đơn vị block như các báo cáo nguồn đã nêu.

Nguồn gồm [artifact Paper2](../../paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/README.md), [tái hiện fixed-stream diagnostic](rq1_query_observability_reproduction_20261108.md), [tổng hợp cơ chế](rq12_evidence_synthesis_20261107.md) và [đợt120world mới](rq2_fresh_graph_source_replication_20261110.md).

## Kết luận quản lý

Đã có kết quả nghiên cứu RQ1/RQ2 có thể trình bày và mô hình CG-AKT đã train trên Grade10. Chưa RQ nào đủ toàn bộ bằng chứng để nghiệm thu hoàn tất. RQ3 hiện thiếu so sánh độc lập, ablation và closed-loop của mô hình đã fit. Việc A0 Junyi đã chạy2epoch là tiến độ training có artifact, chưa hoàn tất mục tiêu RQ3.

Mục Sprint1 yêu cầu tái lập kết quả chính hai paper còn mở theo nghĩa chạy tái hiện đầy đủ. Đường ngắn là chốt danh sách bảng/kết luận chính cần kiểm, đối chiếu từ frozen artifact khi đủ và chỉ rerun phần có vai trò trực tiếp trong lập luận KLTN. Không tự đánh dấu Sprint1 hoàn tất hoặc bỏ yêu cầu. Bản thảo bài báo là deliverable có ghi ở trang5 nhưng người dùng hiện ưu tiên KLTN và tạm hoãn nhánh bài báo, trạng thái này cần được ghi khi chốt phạm vi với GVHD.
