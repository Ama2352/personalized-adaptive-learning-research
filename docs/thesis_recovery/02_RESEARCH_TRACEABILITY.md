# Truy xuất yêu cầu nghiên cứu

Nguồn ràng buộc là đề cương PDF trang 2–5, bản trích `evidence/proposal.txt`. Feedback bổ sung do người dùng cung cấp trong phiên, cần advisor xác nhận biên bản thiết kế mới. Bảng này thay cách diễn giải tracking cũ về tài liệu bị thiếu. Không chỉnh đề cương.

| Yêu cầu đề cương | Feedback | RQ/giả thuyết | Experiment | Implementation | Metric và bằng chứng |
|---|---|---|---|---|---|
| Chẩn đoán dự báo–mastery–lộ trình | Ba trap | RQ1 graph effect bị calibration/policy che | E01,E02,E03 | Historical adapters và trace harness | ΔLL/Brier, crossing, Jaccard, action disagreement, outcome paired |
| Hiệu lực theo graph/history/profile | Ability và logged order | RQ2 phụ thuộc noise và latent profile | E04,E05,E06 | Diagnostic-v1, graph perturbations | Interaction contrasts, CI learner/seed, Holm |
| Confidence từng cạnh + gate + fallback | Minimal CG, graph-off hợp lệ | RQ3 gate giảm harm khi edges sai | E07,E08,E09 | AKT fixed, weighted, gated residual | Prediction/calibration, gate distribution, closed-loop retained gain |
| AKT, SAKT, GKT, GAM, Graph-GAM, BKT | Giữ phạm vi | Comparator capacity và graph package | E10 | Chuẩn hóa adapters | Same population, coverage, predictive metrics |
| Graph chuyên gia, học dữ liệu, xóa/thêm/đảo | False positive Junyi | RQ2 graph metadata có thể proxy order | E05,E06 | Train-only graph learner và null matched graphs | Generalization, order sensitivity, edge-noise |
| Chia theo learner, predict-before-update | Giữ proposal | Tất cả | E01–E10 | shared_kt, split identities | Zero overlap, no future labels, exact target accounting |
| CI/bootstrap, Holm | DiD có điều kiện | Tất cả | E02–E10 | Paired learner/seed statistics | Effect size, CI, corrected p, family manifest |
| Demo hồ sơ/model/graph, route và confidence | Giữ proposal | Minh họa nghiên cứu | E11 | Read-only verified artifact viewer và causal replay | Trace replay parity, provenance visible |
| Mã, cấu hình, seed, báo cáo, bản thảo bài báo | Giữ proposal | Tái lập và bảo vệ | E12 | Packaging, thesis claim ledger | Hash inventory, independent reproduction instructions |

## Bằng chứng tối thiểu

RQ1 bắt buộc có E01 reconciliation, E02 structural proof/counterexample, E03 trace trên frozen replay và closed loop. Ít nhất một trường hợp prediction đổi nhưng action giữ nguyên và một trường hợp action đổi, nếu simulator cho phép. Nếu không tìm thấy phải báo tỷ lệ và giới hạn CI, không tạo ví dụ giả làm empirical result.

RQ2 bắt buộc E04 factorial ability, E05 logged-order controls, E06 xóa/thêm/đảo tại nhiều mức cùng history/profile/sparsity và intra/cross strata. Oracle simulator cho phép xác định ground truth, Junyi chỉ predictive association. Graph học từ dữ liệu không được quên vì đây là đề cương trang 3.

RQ3 bắt buộc E07 unit parity và causal graph branch, E08 bốn variants trên simulator train riêng, E09 closed loop và fallback selection stability. E10 giữ đủ baseline đã nêu. Độ rộng model×dataset×noise không có định lượng trong proposal, cần advisor duyệt ma trận phân bổ. Bỏ SAKT/GKT hay graph-learned cần phê duyệt điều chỉnh phạm vi.

Strongly recommended gồm 3 training seeds simulator, matched Junyi CG comparison và hidden synthetic audit seeds sau freeze. Optional gồm dataset thứ ba, learned edge-confidence neural module, nhiều GPU, policy học tăng cường. Omit proposal-required deliverables luôn cần advisor duyệt.

## Quy trình lựa chọn và đánh giá

**Chỉ dẫn hiện hành15/11.** Đoạn5fold bên dưới là kế hoạch lịch sử, đã được ProtocolV1 ngày08/11 thu thành development mộtfold4. Đề cương trang4 cho phép nhiều phép chia hoặc bootstrap, không bắt buộc5fold. Xem [đối chiếu phạm vi](../../research_tracking/reports/TRAINING_SCOPE_RECONCILIATION_20261115.md) trước dự toán training. Các model và baRQ giữ nguyên.

5 outer Dev folds đã frozen được giữ cho benchmark Junyi tương thích. Trong mỗi outer-train có một inner learner holdout 10% để chọn epoch, rồi refit outer-train ở E đã chọn. Đây là ordinary outer K-fold evaluation với inner holdout selection, không phải nested K×K CV. Không cần thêm inner 5-fold. Mỗi model được dùng optimizer/stopping phù hợp nhưng cùng ranh giới thông tin và budget search công khai.

Chi phí selection + refit xấp xỉ gấp 1,9 lần một lần train nếu epochs tương đương. Phương án tiết kiệm giữ inner-trained model để outer evaluation có ít dữ liệu fit hơn, phải ghi tên protocol khác và xin duyệt. Fixed-E lấy từ một development selection cohort rồi báo các folds đã dùng selection là development results, không gọi independent CV. Không tự chuyển E=3.

BKT pilot chọn num_fits trên fold0 rồi đánh giá CV có fold0 gây optimism và dependence trên dữ liệu Development đã tham gia selection. Các fold khác cũng có train overlap, không coi bốn fold còn lại là independent untouched test. Giữ kết quả descriptive, báo sensitivity fold0-excluded nếu chỉ đọc stored Dev summaries được cho phép về sau, không rerun EM. Holdout BKT đã accessed theo historical protocol và marker, không mở lại phiên này. Cần access ledger, freeze model/threshold/calibration/graph trước final approval, tách model selector khỏi người xem Test nếu khả thi, báo residual analyst adaptation. Không tạo split mới âm thầm.
