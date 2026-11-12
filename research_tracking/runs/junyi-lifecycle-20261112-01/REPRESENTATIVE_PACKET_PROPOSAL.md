# Đề xuất packet đo throughput TRAIN80

**Trạng thái đề xuất, chưa tạo payload hoặc chạy model.** `representative-packet-selection.json` ghim lựa chọn1024native windows từ full TRAIN80 cache bằng seed42, độc lập correctness. Script metadata mất11,81giây, chỉ đọc offsets, target masks và metadata record của các shard được chọn. Có16strata theo vị trí shard, mỗi stratum lấy một shard và64record. Giữ nguyên lựa chọn đầu, không redraw theo histogram.

## Quần thể và hình học đã đo

| Độ dài window | Full232.662windows | Packet1.024windows |
|---|---:|---:|
|1–10|64.576|290|
|11–50|30.592|146|
|51–100|31.606|151|
|101–199|21.304|104|
|200|84.584|333|

Packet chứa56.332training targets,100.032valid tokens của755learners. Độ dài trung bình97,6875 so với102,8794 của full cache. Total variation theo năm strata bằng0,03835, theo từng độ dài chính xác bằng0,12424. Packet có đủ kernel dài200 nhưng tỷ lệ độ dài200 thấp hơn full khoảng3,84điểm phần trăm. Mức đại diện này chỉ áp dụng geometry đã đo. Learner ability/profile và label distribution chưa được đánh giá.

Mô phỏng shuffle buffer1024/seed43/batch4 bằng đúng metadata lengths cho full có42.944.232padded tokens, packet186.128padded tokens. Đây là workload hình học tính từ masks/lengths, chưa đo GPU time. Báo riêng targets/sec, valid/padded tokens/sec và overhead; dự toán full fit sau này cần xét chênh lệch strata/padding.

## Packet thực thi nhỏ nhất đề xuất

Giữ16original NPZ shards và encoding717exercise đã fit từ full TRAIN80. `record_indexes` trong JSON xác định1024windows được dùng. Toàn bộ16shard SHA đã đối chiếu khi lập metadata. Các window giữ original source rows, user IDs, global ranks, target masks, context100/targetblock100 và causal prior. Artifact là engineering packet có tham chiếu full source identity, với `full_role_coverage=false` và expected workload56.332targets. Source full role vẫn có13.347.331targets.

Worker tương lai cần entry packet riêng, dùng bounded decoded records từ các shard đã ghim. Giữ điều kiện full-cache/phase hiện có để các loader nghiên cứu từ chối subset bị gắn nhãn full. Không đổi phase view hoặc key full cache thành56.332targets. `train_epoch` có thể dùng factory packet trong lượt engineering có scope rõ ràng, tối đa256updates cho một pass. Một pass packet hoàn tất chưa là một epoch full TRAIN80. Checkpoint phải gắn packet identity và trạng thái engineering.

Khởi tạo fresh A0 theo recipe hiện hành, encoding717 và cùng source/runtime profile. Đo CUDA memory, train targets/sec, batching/padding, data loading, checkpoint/reload và counters thực. Đầu ra gồm manifest/source pins, geometry, tiến độ từng phần, model/Adam/RNG checkpoint và resource receipt. Dự kiến inference/evaluation scope được chốt riêng, tránh biến workload throughput thành selected model result.

## Vấn đề full-cache admission

`JunyiWindowCacheSession` bắt buộc strict-admit toàn bộ232.662records trước hot iterator. Full strict admission time hiện chưa được đo. Worker có watchdog400giây cần dự toán cả admission, nên dùng full Session ngay có thể tiêu hết thời gian trước training.

Bước CPU rẻ cần chuẩn bị là tiêu thụ strict iterator toàn full cache, đúng role/encoding/source/13.347.331target pins, CUDA ẩn và không Torch/model. Ghi elapsed/RSS, counts, SHA verification và failure nếu dừng. Lượt này cung cấp chi phí admission thực. Process GPU dùng full Session vẫn phải thực hiện admission của chính process đó, receipt CPU là bằng chứng đo, không tạo quyền bỏ admission.

Đối với packet1024, cần strict admission riêng cho đúng packet đã xác định và kiểm SHA/bytes selected shards trước model. Đó là một scope engineering được khai báo, không phải full-cache admission. Source cache nguyên được giữ nguyên. ROOT cần freeze worker nhỏ, kiểm local/synthetic, chốt tranche/timeout/output acceptance rồi mới dispatch trong lượt tiếp theo. Gói hiện tại chỉ chuẩn bị metadata và proposal.

## Các mức kiểm của metadata hiện có

Manifest full cache đã khớp pin trong receipt. Geometry offsets/masks của909shards được kiểm bounds/counts và đối chiếu tổng với full manifest. Chỉ16selected shards được rehash toàn file trong bước này, các shard còn lại được đọc geometry và đối chiếu byte count. Toàn bộ source targets/prior responses/model tensors chưa được đọc. Chưa có payload mới, optimizer update hoặc cloud use.
