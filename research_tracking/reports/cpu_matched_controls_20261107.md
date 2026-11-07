# Đối chứng graph khớp strata trên cohort pilot

## Run và giới hạn

Run cpu-junyi-controls-20261107-01 dùng cùng32inner-train learners, prefix120events và1211events của pilot trước. Order comparisons gốc trùng lần trước. Graph đầu vào là current-catalog reconstruction976edges bằng SCC rule Paper2. Dataset và artifacts trước được giữ nguyên.

Node strata gồm topic, area và learner-support bin trong chính prefix được duyệt. Các bins0,1–2,3–5,6+ là lựa chọn chẩn đoán coarse, không phải full-training support. Mỗi control dùng10double-edge swaps, giữ node set, in/out-degree và joint topic/area/support-bin pair counts. Three seeds0/1/2 cố định, không lấy mẫu đều mọi DAG. Mỗi control đổi20cạnh cũ thành20cạnh mới, symmetric difference40entries.

| Seed | Applied swaps | Changed entries có child quan sát được | Changed entries co-observed cùng learner | Parent-first edge–learner pairs |
|---|---|---|---|---|
|0|10|10|0|48|
|1|10|6|2|47|
|2|10|0|0|48|

Base graph có48parent-first trong52coobserved edge–learner pairs. Cả ba controls vẫn có52pairs. Giữ tất cả control, kể cả seed2 không thay cạnh tác động vào child được quan sát. Không dùng null differences của controls ít exposure để kết luận graph neutral. Có child được quan sát khác với cả hai endpoints co-observed cùng learner.

Counts đối chiếu từ matched_controls.json, order_summary.json, corrected_graph.json. Hash inputs và phép tính coverage dẫn xuất ở cpu_matched_control_coverage_20261107.json.

## Quyết định mở rộng được user giao

Sau khi hỏi về mức mở rộng tối đa256inner-train learners×300events,180s, user giao chọn phương án hợp lý. Chọn đúng mức đó, giữ outer-fold0, hash-ranking cohort và không correctness/Holdout. Đây là descriptive order/control analysis, không train hoặc chọn model. Giữ bins và số swaps/seeds như pilot để biết thay đổi exposure do cohort mở rộng. Run mới sẽ có ID/config/manifest riêng, không thay bảng32learner.

## Cohort mở rộng đã hoàn tất

Run cpu-junyi-controls-20261107-02-expanded dùng256inner-train learners, prefix tối đa300events và tổng12575events, elapsed5.99s trong giới hạn180s. Raw graph sau bỏ self-loops có199supported edges,650edge–learner pairs và576parent-first pairs. Corrected graph976edges có198supported edges,649pairs và575parent-first pairs. Không so controls trên corrected graph với denominator của raw graph.

| Graph | Supported edges | Coobserved edge–learner pairs | Parent-first pairs | Changed entries có child quan sát được |
|---|---|---|---|---|
| Corrected base |198|649|575|—|
| Control seed0 |198|650|576|14|
| Control seed1 |198|644|568|20|
| Control seed2 |194|645|574|14|

Cả ba controls thực hiện đủ10swaps, giữ cùng degree/topic/area/support-bin constraints và graph hashes. Support-bin matching không giữ nguyên learner-level co-observation, nên denominator khác nhau. Aggregate alignment gần nhau chưa đủ kết luận graph quality hoặc causal benefit. Cần estimator theo learner với coverage/common-population rule được chốt trước inference. Không chọn seed tốt hơn hoặc loại control ít exposure.

Lựa chọn bins0/1–2/3–5/6+ và10swaps giữ nguyên giữa hai cohort để khảo sát feasibility/exposure. Đây là coarse pilot specification, cần xem lại độ mạnh perturbation và strata trước confirmatory experiments. Không tự mở rộng thêm ngoài256×300.

## Engineering AKT đi cùng batch

Bounded resumable epoch trước đây báo incomplete khi max_steps đúng bằng số update cần thiết. Đã thêm peek không commit cursor/digest để nhận biết stream exhausted ở step cap. Kiểm exact5steps/17targets và resume từ step5, cùng sampler/resume suite19passed17.30s. Chưa đồng nghĩa public CLI recovery đã tích hợp.

Gate2 attempt support-cap-03 có239passed1failed do lifecycle fixture còn đọc RAM khả dụng thật ở nhánh training. Ngưỡng production1GiB đã chặn khi máy xuống khoảng1.048GB. Đã giữ log/JUnit, không phát hành pointer cho attempt thất bại. Test lifecycle chuyển sang deterministic memory snapshot, trong khi production guards và các resource-failure tests riêng giữ nguyên. Targeted pilot/training suite35passed25.66s. Gate2 tiếp theo phải chạy lại theo source đã sửa.
