# Hợp đồng benchmark AKT phục vụ KLTN — 12/11/2026

## Kết luận audit hiện tại

Đã kiểm độc lập bảy lượt selected-fit80 trên Grade 10 bằng cấu hình và CSV trong archive thực. Cả bảy dùng đúng recipe256d/8heads/batch4/seed42, cùng backbone khởi tạo, cùng48 người train, cùng6 người selection và1.260 target. Đã tính lại AUC, Log Loss, Brier, ECE 15 vàaccuracy từ raw probabilities/nhãn. Đã replay quy tắc min_delta/patience để kiểm epoch được chọn và điểm dừng. Các artifact này dùng tiếp được cho mục đích selected đã ghi.

Kết quả này chứng nhận phạm vi đã audit. Junyi chưa có lượt training nghiên cứu. Matrix chính còn thiếu refit/calibration, comparator SAKT/GKT và đánh giá độc lập. Những phần thiếu dưới đây là điều kiện triển khai tiếp, không được xem là đã đạt chỉ vì có checkpoint hoặc lệnh trả mã0.

## Cơ sở phương pháp

Đề cương bản người dùng cung cấp, trang3–4, yêu cầu Junyi và mô phỏng, chia theo người học, dự báo trước cập nhật, các baseline, bốn chỉ số dự báo, kiểm nhiễu, chỉ số vòng kín, bootstrap và Holm. Phần phương pháp của bản này yêu cầu kiểm ổn định qua nhiều phép chia hoặc bootstrap, không ghi rằng mọi mô hình bắt buộc chạy5fold. Giữ full 5-fold lịch sử của BKT/GAM làm reference và ghi đúng giới hạn của staged fold 4.

Nhận xét GVHD do người dùng gửi lại ngày12/11 giữ baRQ. RQ1/RQ2 tập trung vào ba bẫy thiết kế, kênh năng lực và thứ tự Junyi. RQ3 dùng confidence từng cạnh và gate, đánh giá chính trong mô phỏng có groundtruth cạnh/noise. Junyi vẫn là môi trường bắt buộc theo đề cương. Kết quả gate giảm ảnh hưởng đồ thị được đánh giá theo số liệu. Mọi công việc ở hợp đồng này phục vụ KLTN.

Nguồn phương pháp đã adopt là Protocol21, Recipe26, Accounting23 và CUDA28. Ngưỡng, phép chia hoặc họ so sánh mới cần version và lý do trước đánh giá tương ứng. Selection đã được xem, vì vậy mọi bảng từ selection giữ nhãn development. Không gọi phân tích viết sau khi xem selection là đăng ký trước kết quả đó.

## Ba benchmark cần giữ riêng phạm vi

| Benchmark | Train / chọn epoch / calibration | Dữ liệu đánh giá | Kết luận được hỗ trợ |
|---|---|---|---|
| Grade 10 dự báo cùng luồng | Selected48/6/6 hiện có. Sau external freeze, refit54 và calibration6 | Luồng cố định độc lập theo nhóm seed đã chốt, mọi model cùng target và lịch sử | Dự báo, calibration và độ nhạy đồ thị trong môi trường mô phỏng |
| Junyi Development staged fold 4 | Outer-train158468, inner roles126774/15847/15847. Refit142621, calibration15847 | Outer fold4 gồm39616 người, không dùng chọn model/epoch | Dự báo trên log quan sát. Cần đối chứng thứ tự, không suy lợi ích dạy học nhân quả |
| Grade 10 vòng kín | Model/checkpoint vàtemperature đã freeze trước chạy | Cùng seed-block, profile và world. H_dev30, final horizon chưa được duyệt chạy | Tác động lên quyết định, hành động và latent learning theo giả định world đã công bố |

Holdout Junyi tiếp tục tách khỏi chọn model, epoch, graph, confidence, temperature và threshold. Model đã fitted có thể cập nhật trạng thái online từ đáp án quá khứ trong luồng đánh giá theo đúng định nghĩa KT. Neural weights và các tham số đã freeze không được tối ưu bằng đáp án đánh giá.

## Những điều kiện phải khớp trước training

| Thành phần | Điều kiện kiểm |
|---|---|
| Phạm vi dữ liệu | Environment, corpus/canonical source, outer fold, roles và ngày/version phải có trong manifest |
| Chia người học | Không trùng giữa train/selection/calibration/outer-eval. Seed-family mô phỏng không đi qua nhiều role |
| Vocabulary | Selected fitTRAIN80. Refit tạoencoding90 mới. OOV/null được ghi cùng lý do vàcoverage |
| Đồ thị/confidence | FitTRAIN80 và giữ bản này qua neural refit90 theo Recipe26. Không dùng selection/calibration/outer-eval hay oracle edge labels để fit confidence |
| Backbone và tối ưu | A0–A3 dùng cùng initial backbone, fresh optimizer riêng, geometry/seed/lr/batch/stopping đã chốt. Giữ artifact khởi tạo để đối chiếu |
| Timeline và masking | Per learner theo time_done/source_row của Junyi. Target chỉ được chấm một lần. Current/future responses không được ảnh hưởng p_t |
| Lịch sử | Context100 + targetblock100 tạo effective history0–199 tùy vị trí trong block. Graph dùng đúng prefix này, gồm OOV reset |
| Chọn epoch | Native BCE trên cùng exported FP32 probability, min_delta0,0001/patience3/maxepochs20. Metric báo cáo canonical tính riêng |
| Thứ tự lifecycle | Tất cả selected candidates hoàn tất, selector freeze, fresh refit90, temperature bằngcalibration10, rồi đánh giá độc lập |
| Tài nguyên | CUDA/backend/lock/source đúng run. Có target/windows dự kiến, trần runtime/chi phí và checkpoint contract |

`outer_fold=0` trong config Grade 10 là field legacy còn mặc định. Identity authoritative của các lượt này ghi environmentGrade 10 và no_junyi_fold=true. Field này không tạo một lượt Junyi fold0. `config.graph=False` giữ native AKT NonRasch, còn biến thể graph được xác định bằng typed condition A1/A2/A3.

## So sánh nào được ghép cùng bảng

- Main A0/A1/A2/A3, SAKT/GKT cần cùng domain, role assignment, evaluation queries và checkpoint phase. Khác cơ chế nhớ/capacity của SAKT/GKT phải công bố.
- GAM/Graph-GAM mới trên Junyi cần matched partition, cùng query keys và cùng phạm vi fit. Graph package phải giữ local adaptation khớp khi kiểm hiệu ứng edges.
- BKT/GAM 5-fold lịch sử dùng toàn outer-train. BKT là reference hợp lý theo đề cương và được giữ nguyên. Các số này cần một bảng historical/reference riêng. Chưa xếp hạng trực tiếp bằng bảng matched final của pipeline mới dành riêng calibration.
- Native full-population metrics đi cùng coverage. Khi còn OOV và null, full metric của model có thể không xác định. Common-supported comparison cần cùng target keys, labels và denominator, kèm số target bị loại. Không gán0,5 cho bài chưa có model fitted.
- Fold-macro mean từ5fold và một metric pooled của fold4 là hai đại lượng khác nhau. Giữ nhãn và denominator riêng.

## Chỉ số và dữ liệu bắt buộc

| Mục tiêu | Chỉ số | Đầu ra cần lưu | Hiện trạng |
|---|---|---|---|
| Chất lượng xác suất | Log Loss, Brier là primary. AUC, ECE 15, accuracy0,5 vàprevalence hỗ trợ | Rawp, y, learner/query/source_row/rank, split/fold/phase, supportreason, history_available/history_used, checkpoint ID | Đủ cho bảy selectedGrade 10. Đã tính lại cả năm metric |
| Calibration | Reliability15bins, count mỗi bin, raw/calibrated LL/Brier/ECE | Rawp hoặc raw logit, T đã fit, logits clip convention, checkpoint/vocab/role binding | Córaw p. FittedT và independent calibrated exports còn thiếu |
| Phân nhóm | History1–10/11–50/>50, support train, profile, nội/liên chương | Các field query/history, support chỉ từ train, item→concept/chapter vàgraph mappings | Có phần lớn dữ liệu đểjoin từcorpus/encoding. Cần join audit trước vẽ |
| Độ bền vững | ΔLL/ΔBrier vàΔnet gain theo add/delete/reverse0/20/50% | Perturbedgraph + seed/noiseedges, nguồnconfidence choaddededges, basecheckpoint ID vàevaluation condition ID riêng | Chưa có actual fitted-checkpoint sensitivity run |
| Ảnh hưởng đồ thị | α, gate, message, Δlogit, graphenabled, bypassreason, observedconfidence mass | Telemetry theo query trên cùng prehistory, per-edge confidence/provenance | Confidence/checkpoint đã giữ. Export telemetry chưa nối |
| Thành thạo và quyết định | ReferenceS_c, thresholdcrossings, falsepositive/falsenegative so với latent criterion, ready/action differences | Ba item reference mỗi concept, S/M/R/C/B, action/item vàlatentstate evaluator riêng | Main inference/controller wiring vàactual logs còn thiếu |
| Vòng kín | Net latent gain primary, retention14, time-to-mastery và censoring, violations, chuyển/re-entry chương | Seed-block/profile/world, trạng thái đầu/cuối, response/actiontimeline, horizon vàstopreason | Chưa có main closed-loop evaluation |
| Tài nguyên | Trainingtargets/s, valtargets/s, walltime, VRAM/RAM, padding/windowtokens, checkpoint/exportcost | Phase-specifictelemetry vàbudget ledger | Có Grade 10runtelemetry. Chưa benchmarkJunyi |

ECE đo response probability. `S_c` là mean của ba response probability đã calibrated trên reference bank, so với tau_ref≈0,563715. `P(K)` của BKT và latenttheta1250 cần giữ ý nghĩa riêng. Không dùng cùng nhãn “mastery” để ghép các đại lượng này thành metric trực tiếp.

Gate nhỏ và nhánh graph ít tác động cần đọc cùng α vàmessage. Gần0 củaΔlogit, explicitgraphdisabled và bypass vì chưa quan sát parent là các trường hợp có nguyên nhân riêng. A3 graph-off dùng backbone A3. Fallback hệ thống dùng checkpoint A0 độc lập.

## Artifact tối thiểu mỗi run

1. Trước chạy giữ run manifest cùng exactconfig, source/runtime/lock, role/vocab/graph/confidence IDs, initialization, expected target/windows counts vàbudget.
2. Trong selectedfit giữ epoch history, nativeobjective, reportingmetrics/coverage, optimizerstep/target counters, bestcheckpoint marker vàtrace chọn epoch.
3. Checkpoint giữ model+alpha/gate, optimizer/RNG/counters, metadata vàCOMPLETE. Chỉ mục ghi savedepochs vàselectedepoch. Model-state restore cuối epoch chưa là fullworkflow/preemption resume.
4. Dự báo giữ raw p không làm tròn, y sidecar riêng, exactquerykeys, learner/fold/role/phase, support/OOVreason vàhistorygeometry. Truth chỉjoin sau prediction pass.
5. Refit/calibration/evaluation giữ các artifact riêng, không sửa selected predictions. Temperature bind đúng checkpoint90/vocab90/calibrationrole vànumericalconvention.
6. Inference graph-off/noise/gate export cần basecheckpoint vàevaluation condition độc lập. Thiếu đầu ra có thể bổ sung bằng inference từ checkpoint hợp lệ. Chưa có lý do chạy lạitraining chỉ vì thiếu một bảng metric có thể tái tính.

## Khoảng tin cậy và multiple comparisons

Junyi resample theo learner, mô phỏng resample theo seed-block. Ba profile của cùng block đi cùng nhau. Protocol dùng2.000 replicates vàHolm theo family đãfreeze. Selection selector dùng cùng draws vàupperquantile0,975 theo Recipe26. Selection bootstrap là cơ chế chọn development, không là final significance.

LL/Brier trong bootstrap tính response-pooled lại sau khi lấy cụm người học. Không resample từng interaction như các quan sát độc lập, không âm thầm đổi sang trung bình loss theo người học. Ghi clusterN, responseN, seed, familyID, contrasts vàendpoints trong kết quả thống kê.

Trên fixed-stream có thể so pairedprediction/actionshadow cùng prehistory. Sau khi hai policy tạo lịch sử khác nhau trong vòng kín, rawresponse khác query không tạo pairedtarget contrast. So outcome theo pairedworld/seed-block đã thiết kế.

## Bộ figure cần tạo từ bảng phân tích chung

| Figure | Câu hỏi nghiên cứu | Dữ liệu |
|---|---|---|
| F01 | Model nào dự báo tốt hơn trên cùng tập độc lập? | LL/Brier với clusterCI, bảngAUC/ECE/coverage |
| F02 | Xác suất có được hiệu chỉnh, nhất là vùng quyết định? | Reliabilitybins/counts, raw/calibrated vàreferenceS riêng |
| F03 | Đồ thị sai làm suy giảm ra sao? | Noiselevel×type, checkpoint đã freeze, ΔLL/Δnet gain |
| F04 | Hiệu ứng mất ở prediction, mastery, readiness hayaction? | Pairedcommon-prefixtransition records vàđịnh nghĩa từngdenominator |
| F05 | Quyết định có thay đổi kết quả học không? | Netgain/trajectory theo seed-block/profile. Retention14 ghi rõ khi là phép biến đổi của gain |
| F06 | Khi nào graph giúp, trung tính hoặc hại? | Tập phân nhóm hữu hạn vềability/history/support/intra-cross cùngcontrols |
| F07 | Confidence/gate có thực sự điều tiết nhánh graph? | Gate/α/Δlogit theo noise/support, confidence từng cạnh vànhãn cạnh thật/nhiễu chỉ ởevaluator |

Mỗi figure giữ SVG/PDF/PNG, nguồn số liệu, script và caption nói rõ phase/quần thể. Nguồn bảng chính cần cùng query/cluster identity để figure có thể dựng lại. Không lấy metric selection thay ô independent evaluation đang thiếu.

## Các điểm chưa sẵn sàng cần giải quyết trước lượt tương ứng

- Junyi có derivative learnerroles đã kiểm nhưng producer nghiên cứu chưa nối. Legacy full fold workflow dùng90/10 rồi refit toànoutertrain, không được đổi tên thành protocol80/10/10 mới.
- Main stage hiện chủ động từ chối refit vì chưa có externalfreeze verifier nối vào đường thực thi. Cần hoàn tất phần này trước mainrefit.
- Core có graphdisable nhưng wrapper prediction hiện bind enabled=True. Chưa có đường export graph-off/noise/gate telemetry hoàn chỉnh từ checkpoint đã fit. Cần nối inferenceadmission riêng, giữ checkpoint training condition vàevaluation condition đúng nguồn.
- Full Gate1994 thuộc imageGrade 10 đãfreeze. SourceJunyi mới cần Gate/runtime tương ứng trước paid training.
- ThroughputGrade 10 chưa đủ dự toán Junyi. Benchmark Junyi phải giữ recipe/targetpopulation, đo validation/checkpoint vàước lượng cảselected/refit/inference trong phần credit được duyệt.

## Nguồn kiểm chứng

[Hồ sơ audit và mã kiểm](../runs/akt-protocol-audit-20261112-01/README.md), [đề cương chuẩn](../../docs/thesis_recovery/evidence/user_documents_20261108_proposal.txt), [Protocol21](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md), [Recipe26](../../docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md), [checkpointindex](../runs/modal-akt-graph-selected-20261112-01/checkpoint-index.json).
