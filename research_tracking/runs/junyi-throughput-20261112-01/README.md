# Packet đo throughput AKT trên hình học Junyi TRAIN80

## Payload đã chuẩn bị

`prepare_packet.py` đã tạo `artifacts/akt/modal/junyi-throughput-20261112-01/packet.zip`,3.346.994bytes. `packet-preparation.json` giữ SHA archive, packet identity, source reader và toàn bộ22payload files. ZIP có MANIFEST riêng cho extraction kiểm hash theo đường dẫn tương đối repository.

Payload giữ16NPZ shards nguyên byte, full source cache manifest, frozen role metadata, encoding717exercise cùng receipt fitTRAIN80 và lựa chọn record đã ghim. Các original shards chứa thêm TRAIN80 records. Worker chỉ lấy đúng `record_indexes` đã chọn. Các event calibration/outer-validation/Holdout không nằm trong packet.

Nguồn lựa chọn và phép đối chiếu histogram nằm trong [gói lifecycle](../junyi-lifecycle-20261112-01/REPRESENTATIVE_PACKET_PROPOSAL.md). Packet có1.024windows,56.332training targets,100.032valid tokens và755learners. Có333windows dài200, giữ toàn bộ native source rows, ranks, target masks, context và prior responses của từng window.

## Reader và kiểm CPU đã đạt

API `packet_reader.JunyiTrainingPacket(root, expected_packet_sha256=pin)` kiểm manifest/files, source lineage, source fullTRAIN80 view và encoding717. `iter_training_windows()` dùng `_load_shard` để kiểm SHA/bytes/format, rồi `_parts` kiểm từng selected record bằng membership của source fullTRAIN80. Target source rows được kiểm trùng, counters phải khớp1.024/56.332/100.032/755.

`verify()` đã tiêu thụ toàn bộ packet trên CPU và trả `VERIFIED_PARTIAL_TRAIN80_PACKET`. `packet-prepare.log` cùng `packet-preparation.json` ghi output xác nhận. Fresh process không import Torch, không có training hoặc cloud use từ bước chuẩn bị này.

Packet có identity và scope engineering riêng, `full_role_coverage=false`, `full_train_epoch_complete=false`. `source_train_view` giữ nguyên full role identity để kiểm nguồn và membership. Reader không chạy full SequenceAudit trên các rank được lấy mẫu và không đổi full phase/cache key thành quần thể subset.

## Phạm vi phép đo GPU

Nhánh chính kiểm soát dispatch, hạn mức và theo dõi GPU. Worker dùng fresh model với vocabulary717 và recipe hiện hành. Một pass của packet tối đa256updates, phục vụ đo training targets/sec, padded tokens, memory và checkpoint/reload có giới hạn. Artifact checkpoint của lượt này cần giữ nhãn engineering packet.

Một pass packet hoàn tất chỉ chứng minh lifecycle của subset được khai báo. Các selected/refit/calibration fits toàn Junyi có quần thể và acceptance riêng. CPU verification của packet cũng có phạm vi riêng với strict admission toàn232.662windows của full-cache Session. Các receipt GPU/telemetry do nhánh chính bổ sung mới xác nhận kết quả execution.

## Giới hạn về tính đại diện

Mẫu dùng seed42, một shard trong mỗi16strata theo shard index,64record/shard, không redraw theo số liệu. Mean length97,6875 so với102,8794 của full cache. Tỷ lệ window200 thấp hơn full khoảng3,84điểm phần trăm. Histogram hỗ trợ đánh giá geometry; learner ability/profile và label distribution chưa được đối chiếu. Dự toán full training cần xét strata/padding, validation, admission và checkpoint overhead từ bằng chứng thực.

Trong thời gian GPU chạy, `packet_reader.py` và payload được freeze theo pin đã cấp. Bundle tiếp tục mở để nhánh chính bổ sung receipts và quyết định nghiệm thu.

## Kết quả đã nghiệm thu

T4 hoàn tất256optimizer updates trên56.332targets trong7,84684giây. Checkpoint28.902.583bytes đã nạp lại cho dự đoán khớp, lưu durable và tải archive26.164.866bytes về kiểm SHA/CRC. Dự đoán tuần tự trên cùng packet mất8,62170giây. Đây là đo tốc độ trên dữ liệu đã dùng train, không dùng để báo cáo chất lượng dự báo.

Kiểm strict toàn TRAIN80 trên local đã tiêu thụ232.662records/13.347.331targets trong87,08giây, sampledRSS tối đa khoảng64MiB, không import Torch hoặc chạy model. Kết quả này xác nhận đầy đủ cache và cung cấp mốc CPU local. Thời gian strict admission trên CPU gắn GPU còn phải đo trong lượt chính.

`cost-forecast.json` tính ba kịch bản từ số đo thực. Ngoại suy tuyến tính cho khoảng31phút train và4,1phút prediction mỗi epoch. Các hệ số chậm/I/O trong kịch bản là giả định. Chưa bảo đảm toàn ma trận Junyi nằm trong30USD, đặc biệt khi cộng selected, refit, seed và graph overhead. Bước tiếp là một tranche A0 chính riêng có hạn mức.

Dữ liệu đầu vào full selected đã đóng gói riêng315.632.042bytes, chỉ có TRAIN80/selection10, chưa upload trong gói throughput. `full-main-data-packet.json` giữ toàn bộ inventory và hash. Không có event calibration, outer validation hoặc Holdout.

Đơn giá tham chiếu kiểm ngày12/11 là T4 0,000164USD/giây, CPU Functions 0,0000131USD/core/giây và RAM 0,00000222USD/GiB/giây. Forecast dùng cận request2core/8GiB, cộng startup. Giá storage và thất bại phải được dự phòng riêng. [Nguồn chính thức Modal](https://modal.com/pricing).

## Figure lưu cùng bằng chứng

`junyi-throughput-geometry.svg`, PDF/PNG và `figure-data.csv` giữ đối chiếu tỷ lệ độ dài cửa sổ. Dựng lại bằng `build_figure.py` trong .venv. Đã xem PNG và kiểm nhãn rõ, không chồng lấn. Áp dụng palette và quy ước vector của figures4papers, commit e78584f4c1432fb9f9a10f021a2e3f8fa4dfcb15. License CC BY-NC4.0 và tài liệu nguồn được giữ tại bundle `figures4papers-akt-20261112-01`. Hình thể hiện geometry, không đo chất lượng học hoặc lợi ích đồ thị.
