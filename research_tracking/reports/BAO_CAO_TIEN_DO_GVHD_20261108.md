# BÁO CÁO TIẾN ĐỘ KHÓA LUẬN — 08/11/2026

**Đề tài:** Nghiên cứu và phát triển hệ thống học tập thích ứng cá nhân hóa dựa trên mô hình hóa tri thức và tối ưu hóa lộ trình.

**GVHD:** TS. Lê Văn Tuấn. **Sinh viên:** Phạm Triều Dương — 23520355; Hồ Nguyễn Minh Sang — 23521338.

**Bản cập nhật hiện hành:** các bằng chứng được dẫn bên dưới; cập nhật tiếp trên chính file này sau mỗi batch đã nghiệm thu. Lịch sử bản trước giữ trong Git, không sửa các run bundles. Chưa gửi báo cáo ra ngoài.

## 1. Tóm tắt để trao đổi với GVHD

Nhóm đã có baseline BKT/GAM-KT trên Development, kết quả chẩn đoán Paper1/Paper2 và một số pilot kiểm soát. Hiện đã chỉ ra các trường hợp thay đổi dự báo không truyền thành thay đổi quyết định; đồng thời xác định một giới hạn của phép đo retention và nhiễu do thứ tự luyện tập Junyi. Đây là bằng chứng chẩn đoán phục vụ RQ1/RQ2, chưa đủ để kết luận lợi ích nhân quả của graph.

Ở RQ3, đã có các thành phần AKT/graph-confidence/gate và kiểm lifecycle huấn luyện nhỏ. Công việc đang chuyển sang corpus nghiên cứu, selected-fit/refit, calibration và closed-loop có kiểm soát. **Chưa có kết quả research-fitted CG-AKT so với graph-free/fixed-graph, chưa RQ nào được đánh dấu hoàn tất.** Không dùng số tests hoặc số file để tính phần trăm hoàn thành nghiên cứu.

## 2. Bằng chứng nghiên cứu đã có

| Nội dung | Kết quả có thể báo cáo | Giới hạn bắt buộc |
|---|---|---|
| Baseline Development | BKT/GAM-KT mean5fold AUC tương ứng0,783413/0,774866; Log Loss0,375607/0,394881. Nguồn aggregate và snapshot kiểm trước nằm trong JSON đi kèm. | BKT native aggregate, GAM common-supported rows; không paired information-matched graph contrast hoặc final independent evaluation. Development đã tham gia chọn cấu hình. Không mở lại Holdout trong batch này. |
| RQ1: dự báo và quyết định | Fixed-stream graph package:964/1080event pairs đổiP,90/1080events đổi ít nhất một mastery classification,60/1080đổi ready set,22/1080đổi concept preview. Trong964P-changed events,944giữ concept preview. [C01–C03/C13](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md). | Không1080mẫu độc lập;3seed blocks×3profiles×120steps. Preview khác served action; graph package gồm adaptation ngoài cạnh. Các tổng không phải causal funnel hoặc calibration/mastery proof. |
| RQ1: giải thích first-break | Trên9common-prefix comparisons của full package,8trường hợp có cùng M/R/C/B nhưng B-score keys chọn CID khác;1membership khác. [C14/source-local reconstruction](rq1_closed_loop_reconstruction_20261108.md). | Post-hoc/current-source, không original runner recovery hoặc edge-only causal effect. Pserved tính sau selection; không paired loss sau histories phân kỳ. |
| RQ2: retention14 | Với no-practice sauT, forgetting đồng nhất0,06/ngày và nonnegative gain: retained net gain14=0,4317105234×final net gain. [Nguồn/fixture](../runs/cpu-rq12-20261107-03/retention.json). | Quan hệ của dynamics đã nêu; final vẫn phụ thuộc lịch luyện. Không nói mọi retention metric/model đều bất biến với thứ tự. |
| RQ2: ability/mechanism | Factorial10seed blocks/profile: mean interaction PG0; PY+0,034017; PYH+0,053529. PG không phơi nhiễm prerequisite deficit trong trạng thái đã đo. [Phân tích điều kiện](rq2_conditions_evidence_20261108.md). | Chưa ability-only DiD hoặc bằng chứng PG tương đương; initialization/profile còn confounding, signs/LOO chưa đủ kết luận bền. |
| RQ2: Junyi order confounding | Phân tích order-only256inner-train learners/12575events, có controls và common-population sensitivity. [Nguồn tổng hợp](rq2_conditions_evidence_20261108.md). | Không correctness/Holdout trong phân tích này; degree/topic/support matching chưa bảo đảm matched co-observation. Logged-order association không là causal instructional benefit. |

Nguồn diễn giải thống nhất: [bản thảo C01–C14](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.md) và [source map](THESIS_RQ12_DIAGNOSTIC_RESULTS_DRAFT_20261108.sources.json). Paper1 vẫn thiếu exact revision khớp PDF; không gọi current-source diagnosis là tái lập nguyên bản đã nộp.

## 3. Cài đặt và kiểm kỹ thuật mới — tách khỏi kết quả RQ

| Thành phần | Đã kiểm | Chưa đạt |
|---|---|---|
| Research data contract | Split80/10/10, seed-family/role separation, provenance/support và refit90 giữ origin roles;76kiểm tổng hợp đạt. [Báo cáo](simulator_research_data_contract_20261108.md). | Chưa chứng minh corpus đủ diversity hoặc neural model đã train. |
| Calibration/reference/controller | Temperature response, probe84item, common reference criterion và trace M/R/C/B/action. Có kiểm tích hợp cached inputs và guard missing support. [Calibration](response_calibration_readiness_20261108.md), [guard bổ sung](response_calibration_boundary_20261108.md), [controller](reference_controller_readiness_20261108.md). | Response calibration không là calibrated latent mastery. Chưa outer runner với research-fitted model. Targeted suites có overlap và source versions, không cộng thành independent experiments. |
| AKT research data | Nối đúng4scopes: train80/raw-selection10/refit90/calibration-predict; reuse causal window geometry, OOV ledger, full target sidecar;25kiểm đạt. [Báo cáo](akt_research_data_readiness_20261108.md). | Chưa execution phase/trainer/selected refit thật; không fake Junyi fold hoặc đổi role checkpoint toy. |
| Collector research |45mock kiểm đạt và một native smoke12interactions=8train+2selection+2calibration;13source pins giữ nguyên, observable/oracle lưu riêng. [Báo cáo](simulator_research_collection_readiness_20261108.md). | Smoke thiếu reference coverage theo thiết kế, **không là corpus nghiên cứu đủ dùng**;0NN/optimizer/final calls. |
| Demo và notebook | Demo đọc artifact hỗ trợ common-prefix/first-break. [Notebook báo cáo](../../notebooks/thesis_evidence_report.ipynb) dựng bảng/sơ đồ và liên kết C01–C14 từ28inputs/104pointers. | Demo chưa live fitted personalization; notebook chưa Jupyter-kernel/visual QA, chưa plot khoa học xuất bản. |

## 4. Phương pháp hiện hành và các ràng buộc

Theo quyền người dùng giao, nhóm đã chọn [ProtocolV1 Development](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md): ba reference items thật/concept, train80/selection10/calibration10, selected epoch/model trước refit90, calibration riêng sau refit; staged model allocation vẫn giữ required models, hai môi trường và expert/learned graph. Đây là lựa chọn của nhóm, **không phải biên bản GVHD phê duyệt giảm phạm vi đề cương**.

Junyi và Grade10 có vocabulary khác nhau, phải train riêng. Một fold/seed development hoặc horizon30 không thay full required evidence; history>50, final horizon/replicates, graph confidence và statistical families vẫn phải được kiểm đủ trước kết luận cuối. Các kết quả âm hoặc graph-disabled được giữ và diễn giải đúng.

Ngân sách hiện hành: chỉ30USD free credits, trả thêm0USD. **Chưa sử dụng Modal trong các batch này.** Current full software Gate/CUDA/throughput/recovery chưa đủ để duyệt full training. Colab source transfer đang dừng do automatic approval review yêu cầu quyền xuất bộ mã cụ thể; local work tiếp tục, không paid fallback.

## 5. Việc đang làm và mốc tiếp theo

1. Đóng gói collector/native smoke; chọn trước exact first-corpus counts, profiles, policy, clocks và resource caps; sinh corpus đủ coverage rồi kiểm role leakage/support. Không dùng12events smoke làm training cohort.
2. Thêm execution phase AKT research có authorization/resource/output contract riêng, giữ frozen architecture/hyperparameters; nối train→epoch-selection→fresh refit90→calibration10→full-target export.
3. Sau A0 lifecycle được nghiệm thu, nối A1/A2/A3 và SAKT/GKT theo allocation; confidence train-only, independentA0 fallback, graph-noise controls và paired simulator evaluation. Các phần diagnostics RQ1/RQ2 tiếp tục song song.
4. Freeze estimands/seed blocks/comparison families, CI/Holm và coverage trước evaluation; viết kết quả kèm negative/inconclusive interpretations. Không Holdout-informed selection.
5. Tiếp tục cập nhật notebook, demo và chương phương pháp/kết quả từ artifact, không chờ mọi model train xong mới viết.

**Tiêu chí mốc kế tiếp:** một corpus nghiên cứu có manifest/coverage đạt và một A0 research lifecycle đầy đủ; không đặt mục tiêu bằng số tests. Kết luận RQ3 chỉ sau so sánh graph-free/fixed/confidence/gated trên dữ liệu và simulator phù hợp, còn RQ1/RQ2 cần đối chứng cơ chế/conditions đủ mạnh.

## 6. Cách kiểm chứng và sử dụng báo cáo

Mở [mục lục](README.md), [chỉ mục bằng chứng](../EVIDENCE_INDEX.md) hoặc notebook; mỗi run có README/manifest/logs, giữ cả failure quan trọng. [JSON đi kèm](BAO_CAO_TIEN_DO_GVHD_20261108.json) lưu source hashes, revision và giới hạn. Hash xác nhận bytes, không tự xác nhận kết luận khoa học. Bản này phục vụ trao đổi tiến độ, chưa là luận văn hoàn chỉnh hoặc xác nhận hoàn tất đề cương.
