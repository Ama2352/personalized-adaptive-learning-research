# Thu gọn metadata parent evidence Junyi

Ngày12/11/2026. Gói này tối ưu metadata của Junyi A1 trước lượt nghiệm thu nguồn tiếp theo. Chỉ thay `research_junyi_graph.py` và `test_junyi_graph.py`. Source snapshot trước thay đổi nằm trong bundle này. Các bundle lịch sử được giữ nguyên.

## Thay đổi và ranh giới

`audit.observed_rows` giữ các source rows góp vào support/mean của declared parents, theo thứ tự vị trí trong native prefix. Mỗi item có danh sách `(local_position,source_row)` khi đã được quan sát. `heapq.merge` hợp các danh sách của parent đang xét. Parent support, mean, confidence, message và gate features giữ phép tính hiện có.

Condition payload có `audit_schema=junyi_declared_parent_support_rows_v2`, vì vậy context/condition identity mới khác phiên bản trước. Native model/batch hashing giữ nguyên source. Các tensor q/qa, target/mask, source rows của toàn bộ batch vẫn thuộc kiểm full batch hiện có. Việc thu gọn này chỉ tác động danh sách provenance lặp trong graph evidence.

Chi phí metadata chuyển từ lặp toàn bộ prefix cho mọi query sang lưu các row thật sự góp vào parent stats. Trường hợp mọi prefix row đều thuộc declared parents vẫn cần giữ đủ các row đó. Kết quả đo bên dưới áp dụng graph Junyi có835nodes/976edges trên cohort kiểm kỹ thuật.

## Kiểm xác nhận

`tests01.log/xml` ghi77tests đạt khi chạy graph prefix, window cache và phase data, gồm34ca graph. Bốn ca mới xác nhận row không liên quan được loại, parent rows hợp theo chronology thay vì sort giá trị source row, thống kê parent/gate giữ nguyên, và schema thay condition identity. Các ca current/future invariance, OOV barrier, context rollover và frozen phase guards tiếp tục đạt.

`benchmark_parent_rows.py` đối chiếu snapshot trước với source sau trên cùng315train windows và50selection windows. Có13.238fitted target với parent support/mean/confidence, graph message và bốn gate features khớp chính xác. Source dữ liệu trước/sau giữ cùng SHA. Selection125OOV được giữ trong cache nguồn, không đưa thành model windows.

## Phép đo metadata

`benchmark-result.json` và `benchmark.log` giữ ba lượt xen kẽ cho từng phiên bản, source/input pins và từng sample. Digest dùng cùng dataclass conversion, canonical JSON và SHA256 của native evidence hashing, mỗi group tối đa4windows.

| Đại lượng trên365windows | Trước | Sau |
|---|---:|---:|
| Query evidence dataclasses |13.238|13.238|
| Observed-row references |956.950|61.508|
| Serialized evidence bytes |15.445.154|7.772.451|
| Median build + digest |0,430875giây|0,262730giây|
| Tổng kích thước các observed-row tuple |8.185.120bytes|1.021.584bytes|
| Kích thước các integer object riêng được observed_rows tham chiếu |26.794.600bytes|162.176bytes|

Tỉ số wall time sau/trước bằng0,60976 trong phép đo local này. Hai hàng kích thước Python dùng `sys.getsizeof` cho riêng phần observed rows và đã đếm integer object theo identity để tránh đếm lặp cùng object. Chúng chưa đo toàn bộ process RAM.

## Giới hạn và bước tiếp

Đây là đo CPU metadata trên cohort nhỏ Windows, một digest pass/group. Chưa đo Torch forward, full batch hashing, GPU throughput hoặc chi phí full Junyi. Nguồn Native model và các math primitives được giữ nguyên; lượt Gate/CUDA source mới vẫn cần nghiệm thu trước chạy A1 tiếp theo. Gói này không phát sinh cloud run hoặc model training, và chưa tạo kết luận chất lượng dự báo/RQ mới.

Bundle đang mở để nhánh chính review, cập nhật chỉ mục và commit.
