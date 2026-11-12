# Cache window Junyi trước training

## Mục tiêu và phạm vi

Gói12/11/2026 thêm `research_junyi_window_cache.py` và các ca kiểm tương ứng. Cache dùng lại kết quả encoding/windowing giữa các epoch, giữ nguyên geometry và quần thể target của pipeline hiện có. Không chạy model hoặc cloud, không sửa dataset hoặc artifacts lịch sử.

## Cách sử dụng

`build_junyi_window_cache(...)` nhận stream record từ phase đã chuẩn bị, `JunyiPhaseView`, `JunyiResearchEncoding`, SHA dữ liệu nguồn đã kiểm và `expected_target_rows` bắt buộc. Cache key ghim identity phase, encoding, nguồn, expected target count và geometry100/100/200. Train80 và refit90 có key khác nhau. Caller chịu trách nhiệm kiểm SHA và target count của nguồn thực trước khi cấp pin; hàm không tự mở dataset gốc để chứng thực pin do caller cung cấp. Nếu iterator kết thúc yên lặng nhưng learner cuối bị cắt thiếu target, builder từ chối công bố COMPLETE.

`iter_junyi_window_cache(...)` nhận thêm SHA manifest từ receipt builder. Có thể dùng trong factory `lambda: iter_junyi_window_cache(...)` cho từng epoch, hoặc đọc prediction windows. Stream đầu vào builder phải có learner theo thứ tự view, các target rank liên tục từ0; cache từ chối thiếu learner, thiếu/đúp target hoặc chronology sai.

## Lưu trữ và toàn vẹn

Cache mới nằm dưới `artifacts/akt/window-cache/`. Mỗi shard NPZ giữ numeric arrays, offsets và metadata JSON dạng uint8, không pickle hoặc object arrays. Default256records/51.200tokens mỗi shard, có trần hữu hạn. Loader chỉ giữ một shard cùng record hiện tại; caller có thể giữ buffer training riêng theo cấu hình hiện có. Có tùy chọn nén, không đổi dữ liệu khoa học.

Builder giữ nguyên `TrainingWindow`, `WindowInputs`, `UnseenTarget`, dtype, masks, source rows, ranks, history và OOV reset. Prediction window không có current loss labels. `UnseenTarget` giữ `KTEvent.correct` gốc phục vụ xuất/quản lý OOV, không được đưa vào model. Các nhãn target của training giữ nguyên trong `TrainingWindow.targets`.

Mọi shard có SHA và byte count. Chỉ sau khi source iterator đã kết thúc, coverage đạt và encoding/phase còn đúng, builder công bố manifest rồi marker COMPLETE theo thao tác không ghi đè. Lỗi giữ `failure.json`; cache chưa hoàn tất bị từ chối. Loader kiểm manifest pin, từng shard, dtype/shape và tổng count. Thay encoding giữa các lần yield bị phát hiện bằng content hash nhỏ, không hash lại toàn bộ learner roles mỗi record.

## Kiểm chứng

- `tests01.log/xml` ghi16ca ban đầu đạt.
- `tests02.log/xml` ghi78tests và11subtests đạt khi chạy cùng graph prefix, roles, phase data và cohort cache. Có19ca window-cache.
- `tests03.log/xml` ghi79tests và11subtests đạt sau khi thêm expected source target count bắt buộc, gồm20ca window-cache.
- Các ca bao gồm exact roundtrip training và prediction/OOV ở cả nén/không nén, giữ dtype/chronology, iterator có thể đọc lại, source interruption, shard thiếu/hỏng/cắt cụt, phase/encoding/source sai, integer overflow, target thiếu/đúp, giới hạn token và exclusivity.
- `import-check.json` xác nhận fresh import không nạp Torch. Chưa đo throughput hoặc dung lượng cache trên toàn Junyi.

## Đối chiếu cohort Junyi thật có giới hạn

`check_actual_bounded.py`, `actual-bounded.log` và `actual-bounded-result.json` giữ nguồn đã ghim từ lượt GPU A0 kỹ thuật trước. Cache train giữ315TrainingWindow,11.833target và17.733window tokens của256learner. Cache selection giữ50WindowInputs cùng125UnseenTarget, tổng1.530target và1.955window tokens của32learner.

Đã so sánh chính xác toàn bộ490record với native iterator, gồm dtype, target labels của training, prior responses, OOV events, masks, source rows, chronology, global ranks, history và reset. SHA của nguồn trước/sau giữ nguyên. Các shard/manifest/COMPLETE có SHA và byte count trong kết quả. Cache thực nằm tại `artifacts/akt/window-cache/bounded320-20261112-01/`, không commit dữ liệu phái sinh. Đây là kiểm kỹ thuật cohort, không có training hoặc kết luận chất lượng dự báo mới.

## Phép đo reader trên cohort có giới hạn

`benchmark_bounded.py` thực hiện ba lượt cho mỗi reader theo thứ tự xen kẽ, cùng315training windows/11.833target/17.733tokens. `bounded-reader-benchmark.json/log` giữ từng thời gian và source pins. Median native là0,26965giây, NPZ0,28295giây, tỉ số NPZ/native1,0493. Lượt NPZ thứ ba0,78853giây được giữ nguyên. Phép đo này chưa xác nhận tăng tốc.

Profile bổ sung chạy riêng có overhead instrumentation, tách khỏi ba lượt timing. Trong profile, validation `_parts`315calls chiếm0,22761giây, `_encoding_guard`0,10072giây và đọc/giải mã shard `_load_shard`0,07977giây. Có thể nghiên cứu tránh kiểm geometry lặp lại sau khi shard SHA đã khớp artifact builder nghiệm thu, nhưng chưa áp dụng hoặc xác nhận tác dụng. Full role key chỉ kiểm ở đầu/cuối iterator. Cohort nhỏ này dùng cache JSONL hiện có làm native source trên Windows; chưa đối chiếu reader Parquet13triệu target hoặc GPU dataloader và không được dùng để dự báo tốc độ toàn Junyi.

## Session opt-in cho nhiều epoch

Sau phép đo trên, bổ sung `JunyiWindowCacheSession`. Constructor bắt buộc tiêu thụ strict iterator tới cuối và xác nhận toàn bộ record, shard, key và count trước khi trả session. Không có tùy chọn nạp receipt PASS từ file. Caller tạo session một lần rồi dùng `session.iter_windows` làm factory cho nhiều epoch.

Hot iterator kiểm file manifest/COMPLETE, phase/role tuple headers và phần encoding mutable ở boundary. Những tuple frozen đã admission được giữ tham chiếu để phát hiện thay thế mà không hash lại toàn bộ learner IDs. Mỗi shard vẫn kiểm SHA/bytes và format/dtype trước khi reconstruct các record. Iterator giữ nguyên arrays/masks và kiểm lại tổng record/token/target cuối lượt; không gọi lại `_parts` hoặc `_SequenceAudit` theo từng record đã nghiệm thu. Strict API mặc định được giữ nguyên.

`tests05.log/xml` ghi87tests và11subtests đạt cho phiên bản session đầu. Phép đo `bounded-reader-session-benchmark.json/log` khi đó vẫn cho median hot/strict1,0312 do chi phí full role hash ở mỗi boundary. Giữ snapshot nguồn `session-boundary-before-optimization.py` khớp SHA của phép đo này. Sau khi chuyển boundary sang immutable tuple guards cùng small encoding hash, `tests06.log/xml` ghi89tests và11subtests đạt, gồm30ca cache. Các ca xác nhận admission strict thực sự chạy, hot epochs không lặp `_parts`/full role hash, và từ chối shard hỏng, file alias, cache chưa hoàn tất, role/encoding/control file bị thay.

`bounded-reader-session-benchmark02.json/log` đo ba lượt strict và ba lượt hot trên315windows. Median strict0,82138giây và hot0,08766giây, tỉ số0,10673. Admission ban đầu được ghi riêng trong JSON. Đây là tốc độ reader của cohort nhỏ trong môi trường Windows tại thời điểm đo, chưa là tốc độ training hoặc mức tăng tốc fullJunyi. Không dùng các thời gian khác đợt để suy tăng tốc bổ sung.

`check_actual_session.py` và `actual-session-roundtrip.json/log` đối chiếu thêm toàn bộ490record train/selection của hot session với native iterator. Dtype, labels training, prior responses, masks, ranks/history và125OOV events khớp chính xác; source SHA trước/sau giữ nguyên. Không có Torch, training hoặc cloud run trong bước này.

Bundle đang mở để nhánh chính nghiệm thu và tích hợp. Chưa commit hoặc tạo cache toàn Junyi trong gói này.


## Nghiệm thu nhánh chính

Bundle đóng sau rà soát nhánh chính. Kiểm CUDA thực và nguồn Linux hiện hành được theo dõi tiếp ở `research_tracking/runs/junyi-gpu-optimization-20261112-01/`. Kết quả ở đây là bằng chứng engineering theo phạm vi từng phép kiểm.

Cache train chính đã tạo tại `artifacts/akt/window-cache/full-train80-20261112-02/`,232.662windows/13.347.331targets/126.774learners. Receipt tại `research_tracking/runs/junyi-lifecycle-20261112-01/full-cache-receipt02.json`. Lượt600giây đầu giữ trạng thái thiếu COMPLETE; lượt sau dùng encoding đã fit và hoàn tất. Các benchmark đọc nhóm nhỏ giữ cả kết quả âm và dương, chưa là tốc độ GPU toànJunyi.
