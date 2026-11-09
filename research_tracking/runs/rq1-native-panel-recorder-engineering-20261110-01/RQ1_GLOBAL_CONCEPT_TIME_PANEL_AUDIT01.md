# RQ1 · Panel cố định khái niệm–thời điểm

## Kết luận nguồn

Có thể ghi đủ 28 trạng thái native trong mỗi quyết định mà không gọi thêm `predict`, `mastery_score` hoặc `is_mastered`. `CoverageAwareSelectorMixin.ready_set()` bắt đầu bằng vòng gọi `is_mastered` trên toàn bộ `nodes`, trước lọc frontier. Cần ghi ngay những lần gọi sẵn có này. Mỗi lịch sử 120 bước cho 3.360 cặp khái niệm–thời điểm. Đó là các phép đo lặp trong một lịch sử, chưa phải mẫu độc lập.

Phần latent toàn miền chưa có trong witness120. Cache CPU09 giữ `theta_before` cho concept đang hỏi, cùng `learning_gain` và `gap_days`, không giữ vector base 28 chiều hoặc snapshot toàn miền mỗi bước. Không thể điền latent của các concept chưa được hỏi bằng giá trị của concept đã chọn. Muốn đối chiếu toàn miền cần thêm sidecar từ trạng thái môi trường thật, hoặc một nguồn trạng thái toàn miền đã lưu đủ và được kiểm danh tính. Lượt audit này chỉ đọc nguồn và metadata, không đọc thêm oracle hoặc chạy policy/world.

## API và thời điểm chính xác

Notebook được nạp chọn lọc qua `src/knowledge_tracing/paper2_reference.py:28`. Cell11 chứa selector, cell13 chứa `MemoryState` và `GAMKTPolicy`, cell9 chứa môi trường. Các số dòng sau trỏ bản trích `docs/thesis_recovery/evidence/paper2_source.py.txt`.

- `ready_set`, dòng342–363, gọi đủ 28 getter ở dòng343. Những lần hỏi parent sau đó có short-circuit và lặp, nên không dùng tổng getter làm mẫu số concept.
- `is_mastered`, dòng460–462, trả `theta >= 1250.0 and pi_task <= 0.55`. Đây là π lưu trong state. Getter không nhận timestamp và không thay θ, π hoặc trạng thái.
- `MemoryState`, dòng434–444, nằm trong dict được tạo đủ nodes ở dòng450. Không có defaultdict sinh state khi đọc. `ConceptDAG.predecessors`, dòng167–168, dùng `.get` và trả tuple. Các Counter trong selector cũng không phải defaultdict. Observer không cần chạm Counter hoặc danh sách graph.
- `_decayed_pi`, dòng502–512, chỉ tính giá trị trả về từ gap thời gian và `_context`. Nó không ghi state. `predict` dòng527–537 dùng π suy giảm này, còn M vẫn dùng π lưu. Θ estimator không tự suy giảm khi đọc. Update dòng539–559 mới ghi θ/π, timestamp, memory, attempts và cờ quên.
- `_context` bản pathway ở `src/knowledge_tracing/gam_kt/simulator_pathways.py:17` đọc attempts, recent outcomes, parent states và times_forgotten. Không có RNG hoặc ghi state. Bật/tắt S/P/L phải giữ đúng nhánh nguồn, không thay bằng GAM Junyi hoặc factory toy khác.
- `LatentStudentEnvironment.theta_at`, dòng270–276, tính θ thực tại timestamp bằng suy giảm learned gain theo `TRUE_FORGET_RATE = 0.06`. Nó không ghi `theta` hay `last_seen`. `snapshot(t)`, dòng278–279, chỉ gọi getter này cho mọi node. `interact` dòng281–317 mới nhận uniforms, sinh Y và cập nhật môi trường.

Clock CPU09 được cộng trước `select` tại `scripts/research/run_approved_cpu_pilots.py:75–82`, bước đầu +6 giờ, các bước28/56/84/112 +72 giờ thay cho +6 giờ. Không gọi `now()` hoặc tự gán elapsed wall time làm scientific timestamp. Trong source này, `select` thay bookkeeping nhưng không đổi MemoryState. Panel phải ghi phase rõ ràng trước bookkeeping để giữ ranh giới controller.

## Hợp đồng instrumentation tối thiểu đề xuất

1. Chỉ một policy được quan sát tại một thời điểm. Giữ class thật, constructor thật và mọi đối số/kết quả gốc. Dùng restoration có kiểm absence/value như observer03. Không global profiler hoặc patch RNG.
2. Wrapper `ready_set` trên controller mixin mở ticket ngoài instance cho một lần select thật. Wrapper `GAMKTPolicy.is_mastered` gọi hàm gốc đúng một lần rồi ghi return cùng các scalar state đang có. Chỉ nhận 28 lần đầu đúng thứ tự nodes, không lấy thêm parent calls hoặc getter trong update. Thiếu, lặp, sai thứ tự, sai policy hoặc ngoại lệ đều làm panel chưa hoàn tất.
3. Ghi `concept`, θ, `pi_task_stored`, `pi_time_stored`, `attempts`, `last_timestamp`, getter M và hai gate θ/π. Kiểm M bằng predicate binary64 nguyên nguồn, không epsilon. Giữ riêng cờ queried concept. Timestamp và stream identity do caller đã đóng scope cung cấp. Ghi age khi có last_timestamp, giữ null cho chưa từng học. Không cần thêm `_decayed_pi` cho 28 concept trong bản tối thiểu này.
4. Native M ở đây là phân loại từ stored uncertainty tại thời điểm quan sát. Không gọi nó là xác suất thành thạo hoặc thay π lưu bằng π suy giảm. Các giá trị số có thể thay đổi dù M không đổi. Cờ `currently_mastered` cũng không thay cho getter M.
5. Nếu future operation có môi trường thật, evaluator gọi `environment.snapshot(t)` ngay trước current `interact`, lưu sidecar riêng đủ28. Đó là 3.360 lần getter latent bổ sung mỗi lịch sử, nhưng không có thêm response, RNG draw hoặc update. Tuyệt đối không truyền snapshot vào select/predict/context. Ghi latent criterion `theta_at(c,t) >= 1250.0` tách biệt native M. Ngưỡng1150 của learning deficit là đại lượng khác.
6. Existing CPU09 replay chỉ có estimator và cache, không có môi trường sống. Không được gọi lại persona generator, dựng thế giới mới hoặc nội suy vector base để giả vờ bước5 là cached join. Future world-side trace cần allocation và source review riêng. Không mở lại lane full replay đã dừng.

Observer03 hiện ghim một lịch sử `(21000, PG, graph_on=False, mechanism_on=False)`, wrapper năm method và queried capture. `replay_rq1_cpu09_native_mastery01.py:66–80` đọc thêm `_decayed_pi` cho concept đang hỏi. ON có 360 lần `_decayed_pi` vì predict/capture/update. Đếm này không chứng minh đã đọc 28 uncertainties mỗi bước. Không sửa các output đã nghiệm thu để bổ sung metadata mới.

## Kiểm tối thiểu cần có trước một phép đo thật

- Fixture selector có parent calls lặp và fallback. Panel vẫn đủ28 đúng thứ tự ở first pass, không nhân mẫu số theo số lần getter. Kiểm số native calls trước/sau observer bằng nhau.
- Fixture state ở θ ngay dưới/bằng1250 và π ngay dưới/bằng/trên0,55. Getter M khớp bit/type và không bị thay bởi predicate decayed hoặc cờ historical.
- Fixture timestamp chưa học, gap dương và gap âm. Đọc không đổi dict keys, θ, memory, π, attempts, timestamps, deque, quên hoặc RNG. π decayed có thể khác stored trong khi native M giữ nguyên.
- Fixture môi trường có learned gain và lâu không luyện. `snapshot(t)` khớp getter từng concept, kể cả concept chưa từng được chọn. Snapshot không đổi base, theta, last_seen, RNG hoặc số interact. Không gọi response để tạo nhãn panel.
- Fixture install lỗi giữa chừng và body exception đi cùng cleanup error. Khôi phục toàn bộ class attributes, giữ lỗi gốc và ghi cleanup riêng theo pattern observer03.
- Pilot minh bạch OFF/ON sau review cần cùng source, initial state, uniforms và query/action/P/Y/update trace cùng endpoint states. Native constructor/select/predict/update và scientific RNG draws giữ nguyên. Sidecar chỉ được diễn giải khi toàn bộ timeline và phục hồi observer đạt. Chưa có allocation hoặc phép chạy này trong audit.

Panel cố định giải quyết việc chỉ quan sát concept do policy chọn. Nó vẫn nằm trên lịch sử do policy tạo, các concept/thời điểm phụ thuộc nhau. Chưa cho phép ghép loss sau divergence, causal mediation, hiệu quả dạy học, calibration bằng nhãn item hoặc kết luận trên con người.

## Nguồn ghim khi audit

| Nguồn | SHA-256 |
|---|---|
| Notebook `paper2/.../source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb` | `353f487a3d6ed3826f2546d03c0aa2ad2279cf5c4b7fe8e375f4cafb0408280f` |
| `docs/thesis_recovery/evidence/paper2_source.py.txt` | `5f936e5908bfc2ee9a7c7b750917c7fac52bbaef44be67557e69f6408062f2f8` |
| `src/knowledge_tracing/paper2_reference.py` | `a12edc72a00ad980799ec50ff26f0cb68f2529e3699e8a57e4f11295693c2cd1` |
| `src/knowledge_tracing/gam_kt/simulator_pathways.py` | `33ad34140f7b08eb22f86e6cc3caf7b0e7c98f09e4fd74945a6f7e9718b07560` |
| `src/knowledge_tracing/gam_kt/simulator_mechanisms.py` | `0cbfaf1b4735c188e04ed822197121118dcb65849b582af7413e157fd8d847fa` |
| `scripts/research/run_approved_cpu_pilots.py` | `55e8e3c74c8daa92d572c809353da5546fa435b55e18b8ab30fdcf46e8413e8e` |
| `P/pilot_rq1_cpu09_targeted_observer03.py` | `1c84c3271556d2aa7b5d0ae709122504c2a4a008e8e9c4aa524d0345a10f5baf` |
| `P/replay_rq1_cpu09_native_mastery01.py` | `337677c160f56da0d1454785cb18cbe5eae6ac9019db76a6b59a9eb187e0ebad` |
| `P/rq1_cpu09_targeted_observer_contract03.json` | `0280db8bfcaf844f2646a2c60c2f7cdac3808ba54e6c94ea476b815dcb5bdb90` |
| `P/analyze_rq2_cached_mechanism01.py` | `8590381c85fe1e58df4a305c8bf4a33ebd9900d0fa8ffb1f1a93868fb56f1311` |

`P` là `artifacts/akt/local-tests/akt-research-runner-20261108-01`. Notebook đầy đủ nằm dưới `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/`. Đây là source audit và contract đề xuất, chưa triển khai observer hoặc thay methodology.
