# Đề xuất đo chi phí observer trên một history CPU09 đã có

Ngày09/11/2026. Đề xuất riêng sau khi nhánh replay năm lượt đã dừng. Chưa triển khai worker/controller, chưa import hoặc chạy phép đo. Ghi chú này không thuộc selected inputs của bundle failure hiện tại.

## Câu hỏi hữu hạn

Lượt native05 không hoàn tất dưới173giây worker khi dùng global `sys.setprofile`. Nó chưa tách được chi phí profiler khỏi selector/Pandas, readout và guard. Phép đo nhỏ tiếp theo chỉ hỏi phần chênh chi phí vận hành giữa bật và tắt đúng callback profiler hiện có, trên **cùng một** history120events. Không lập confusion, chấm mastery hoặc điều chỉnh mô hình theo kết quả timing.

Chọn trước world đầu theo canonical order của CPU09, `(seed=21000,profile=PG,graph_on=False,mechanism_on=False)`. Không chọn seed theo tốc độ, accuracy hoặc effect. Stream đầy đủ120events giữ q/y/P gốc và source-derived time. Cache reader vẫn audit toàn bộ120worlds/14.400rows theo contract đã nghiệm thu trước khi lấy stream này, tránh một private partial reader hoặc metadata giả.

## Điều giữ nguyên và điều được đổi

Hai fresh estimator containers dùng cùng initialization nguồn, S=P=off/Loff và graph môi trường/controller lịch sử. Mỗi container nhận cùng120query/y/time theo thứ tự select → exactquery/P → native readout → update. Không khởi tạo world/teacher, không sinh response hoặc RNG mới, không có NN/Adam. So exact P bits, selected queries và final native state identity giữa hai lượt cùng với archived P trước khi chấp nhận timing.

Chỉ thay trạng thái profiler, một lượt OFF rồi một lượt ON theo thứ tự công khai. ON dùng chính callback ở worker04, gồm quan sát native calls và các nhánh cấm world/RNG. OFF bỏ callback toàn cục, vì đó là biến cần đo. Các file/source/input/owned/RAM/deadline guards và direct invocation counters giữ ở cả hai. OFF không được gọi là có cùng mức quan sát callback về world/RNG. Entry chỉ dựng estimator từ source đã review, và giới hạn thực hiện được đối chiếu bằng direct constructor/select/predict/update counters. Không gắn nhãn một receipt profiler-verified cho lượt OFF.

Hai lượt tuần tự có thể khác warm caches và thứ tự thực thi. Với thiết kế sàng lọc nhỏ này, báo từng thời gian và thứ tự, chưa suy một speedup ổn định. Nếu cần ABBA hoặc repeated timing thì phải duyệt allocation riêng, không tự thêm lượt.

## Source boundary cần giải quyết trước code

`matched_replay` hiện yêu cầu đủ bốn arms cho mỗi seed/profile. Không đưa một world vào bằng forged buckets hoặc đổi tên nó thành full-grid parity. Cần review một one-stream operational adapter nhỏ dùng cùng native primitives, hoặc tách cơ học phần vòng lặp một stream sang helper prep mới. Giữ source replay lịch sử và các receipts pure12 nguyên vẹn. Không viết lại phương trình GAM hoặc dựng một trainer khác.

Nguồn cần pin gồm replay `337677c1…e0ebad`, worker04 `f2622ab4…8640bd`, Paper2 notebook `353f487a…8280f`, loader `a12edc72…c2cd1`, pathways `33ad3414…b07560`, raw bank4files, accepted cache contract `23c182f6…e24fa4`, gzip `2a136fbf…65dcc` và module-import adapter đã qua canary5. Sourcecompiler phải tiếp tục đọc exact `.py` bytes dưới real module names, không nới project PYC allowance. Native05 final `67563ec9…c59d0` là động cơ của phép đo, không phải bằng chứng overhead đã biết.

## Allocation đề xuất để Root review

- Whole60giây, owned57giây gồm cleanup3, worker53giây. RSS1GiB, available RAM ít nhất2GiB, source/input/log byte caps cố định.
- Hai estimator constructors,240select/predict/readout/update calls tổng, cùng120event identities được dùng hai lần. Các native nested `_decayed_pi` calls dự kiến720 nếu giữ capture hiện tại. Mỗi call counter phải có scope bắt đầu/trả về rõ, không đồng nhất return event của profiler với body thành công khi lỗi.
- Gzip dưới1MiB, decoded dưới8MiB, toàn14.400rows chỉ đọc để audit provenance. Outputs nhỏ gồm phase timings, exact parity/state hashes, counts và owned/resource receipts. Không xuất truth/accuracy và không copy gzip hoặc dependencies.
- Sau timeout hoặc mismatch giữ verdict thất bại và dừng, không retry/reset hoặc tăng cap. Toàn bộ việc chạy vẫn cần Root review source/packet và dispatch riêng.

Nếu phép đo được chấp nhận, nó chỉ hỗ trợ chọn cách quan sát hoặc thiết kế bounded shards cho lần replay sau. Nó chưa chứng minh full120streams khả thi, chưa làm native M đúng hơn và chưa tạo kết quả khoa học RQ1. Các histories, seedclusters và đáp án đều dùng lại, independent N mới bằng0.
