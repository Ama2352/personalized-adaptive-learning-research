# Main60 — đã bind sáu điều kiện bằng artifact Method24 có sẵn

## Kết quả kiểm thực tế

Lượt binder02 được nghiệm thu với trạng thái `ACCEPTED_SIX_MAIN60_CONDITION_BINDINGS_NO_MODELS`. Outer lưu 5,905733600025997 giây trên cap60; thời gian terminal Root ghi nhận khoảng5,9196giây. Hai lần loader đọc cùng artifact đã fit trước đó, một lần bind expert graph và một lần bind learned graph. Lượt này không fit lại surrogate, không tạo model/optimizer và không dùng oracle.

Corpus là `grade10-development-lifecycle01-20261108`. Canonical public reader đã audit đủ ba Development role cho provenance. Graph/confidence gắn đúng train48/10.080 target, selection6/1.260 và calibration6/1.260. Logical plan identity được giữ riêng với raw SHA của `plan.json`. Condition tiếp tục frozen train80 khi neural refit90 được thực hiện trong tương lai.

| Điều kiện | Actual condition identity |
|---|---|
| A1_EXPERT | `07884ad099952958d2105f51850e2e191db8495f732e72881b5cce875f08d157` |
| A1_LEARNED | `a866858d50c81128a9d6182183445bfb89915dbabe1ce2ffa5d44255f702e00c` |
| A2_EXPERT | `dd2912735febb3458f53a76ea2813d204790209ac360907fa21d66da2cf10b3e` |
| A2_LEARNED | `03aa363b4df1b72b97ab7d69534bdaa8e383a27a301e62dcb4ac3059dffbbdd2` |
| A3_EXPERT | `00ae3d0342ca5ffbde43c6848184fec9efc3f78bad02591e0ce59b11d4b8a665` |
| A3_LEARNED | `de3139ae58a8f8d535b32ee246a0ec1ac319c18513dc7c28f47664cd2f8c66df` |

Nguồn actual nằm ở `main60-graph-conditions02/result.json`, sáu JSON cùng thư mục và `main60-graph-conditions02-owned/final.json`. Các manifest chứa actual `MainGraphInput` wire, train80 binding và support/reason ledger. Chúng chưa cấp training authority hoặc chứng nhận fitted CGAKT.

## Những hợp đồng đã đi qua

- Public reader, `GraphTrain80Binding`, `load_method24_scores` và `prepare_research_graph_condition` là các API thật đã được gọi. Kiểm negative metadata đổi sang corpus engineering10 bị từ chối ở lineage corpus_id.
- Expert giữ đủ28concept/31edge từ public CSV. `expert-topology.json` mới lưu nodes/edges, có thể tái dùng như dữ liệu topology cho A1 hoặc GKT nếu entry tương ứng bind lại domain/role theo contract riêng.
- Learned topology giữ đúng accepted31-edge DAG. A1 dùng trọng số1. A2/A3 trên mỗi topology dùng cùng predictive-stability scores. Support/null/zero và reason được bảo toàn. Đây không phải xác suất cạnh đúng hoặc bằng chứng true-graph recovery.
- Actual full owned-Job monitor có29samples, peak family75.530.240byte, peak worker61.759.488byte và minimumfree4.468.162.560byte. Worker/monitor/queryhandle/environment đã đóng và ownedJob0. Đây là sampled resource evidence.
- Tất cả211source/26input/25runtime pins trước–sau khớp. Không thay production source hoặc refit2352solver calls lịch sử.

## I/O và failure được giữ

14producerfiles có69.519.761byte được giữ ở `method24-native01`. Hai loader cùng cap160MiB mỗi lần, aggregate cap320MiB, không copy các CSV lớn. Public reader có cap4MiB riêng. Result không ghi actual byte throughput của loader, nên không suy ra tốc độ I/O từ các cap này.

Binder01 bị từ chối trước loader vì thiếu exact metadata-helper path trong packet allowlist. Binder02 chỉ bổ sung pin `prediction_mastery_trace_worker03.py` và namespace mới. Không nới quyền đọc project. Failure01, source01 và raw receipts được lưu cùng bundle để truy vết.

## Readiness của bước selected tiếp theo

Các condition Main60 đã sẵn cho bước chuẩn bị cấu hình MainSelected. Entry phải dùng `MainGraphInput` actual từ từng manifest, `max_graph_input_bytes` ít nhất160MiB cho các điều kiện dùng loader, current runtime/Gate và closed authorization riêng cho allocation được Root duyệt. `_actual_condition` vẫn tái kiểm qua factories thật. Boundary revalidation còn hash các graph files, vì vậy allocation neural cần tính chi phí I/O lặp lại.

Một positive A1_EXPERT tiếp theo trên corpus engineering10 có thể tái dùng topology public. Nó cần condition train8 riêng, initial backbone fresh cùng seed với A0 và allocation riêng. Sáu condition vừa tạo gắn train48. Learned/confidence train48 không được chuyển thành realization train8 bằng relabel.

Matrix vẫn gồm A0, sáu graph conditions, SAKT và GKT. A2 tiếp tục là ablation. Main system freeze cần toàn bộ raw selection trước mọi main refit/calibration. Lượt bind này chỉ hoàn thiện liên kết dữ liệu cho bước đó, không tăng mẫu nghiên cứu hoặc kết luận hiệu quả dự đoán/học tập.
