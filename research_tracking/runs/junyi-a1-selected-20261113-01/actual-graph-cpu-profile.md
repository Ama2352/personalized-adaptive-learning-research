# Profile CPU phần ngữ cảnh đồ thị A1 trên Junyi thực

Ngày 13/11/2026. Lượt này đọc cache TRAIN80 đã ghim trong request05, không dựng model, không forward/backward, không dùng GPU hoặc Modal. Source tại năm module liên quan khớp source02 của lượt training A1. Kết quả là PASS_ACTUAL_TRAIN80_SHARD_CPU_PROFILE.

## Dữ liệu và giới hạn

Đọc manifest cache cùng một shard `shard-000000.npz`, kiểm SHA và giới hạn giải nén bằng reader hiện có. Chọn 128 trong 256 window bằng seed43 tại shard đó, được 102 learner, 5.527 target và 9.327 token. Dựng đúng TRAIN80 view, vocabulary717 và đồ thị corrected976cạnh từ các file đã ghim trong request05. Kiểm kiểu/geometry và quyền learner của từng window mẫu bằng logic cache hiện có.

Đây là mẫu trong shard đầu tiên. Không gọi đó là thứ tự shuffle seed43 của toàn epoch hoặc benchmark đại diện toàn Junyi. Không đọc events calibration/Holdout. Không chạy lại strict admission của mọi shard, nên không thay thế bằng chứng nghiệm thu cache đầy đủ.

## Số đo không bật profiler

| Công việc cho cùng 128 window | Thời gian |
|---|---:|
| Dựng prefix evidence, gồm các `_light_check` của session | 0,13463 giây |
| Tính lại evidence SHA bốn lần như train batch | 0,18809 giây |
| Tổng hai phần | 0,32272 giây |

Evidence có 5.527 query, 7.019 parent record và tổng 32.681 observed-row reference. Median số observed rows/query là0, cao nhất81. Không chỉ là fixture dữ liệu tổng hợp với parent support bằng0.

## Điểm tốn CPU theo cProfile

| Hàm | Số lần gọi | Cumulative time |
|---|---:|---:|
| `asdict` | 22.108 | 0,43436 giây |
| `_asdict_inner` | 558.508, gồm đệ quy | 0,41854 giây |
| `fields` | 72.292 | 0,13724 giây |
| `prefix_evidence` | 128 | 0,15178 giây |
| `_light_check` | 256 | 0,05285 giây |
| `_prefix_evidence` | 128 | 0,07985 giây |

Cumulative time của hàm cha/con chồng nhau, không cộng các hàng thành tổng hoặc suy tỷ lệ tiết kiệm trực tiếp. Profiler làm phép đo chậm hơn, vì vậy dùng thêm bảng unprofiled ở trên. Snapshot `actual-graph-cpu.pstats` và bảng35hàm tại `actual-graph-cpu-top.txt` cho phép kiểm lại số đo.

Đã định vị chi phí CPU thật ở việc dựng/kiểm ngữ cảnh và chuyển dataclass thành payload hash nhiều lần. Phép đo chưa bao gồm `_batch_sha`, GPU→CPU tensor copies, các kiểm của adapter ngoài session, đọc nhiều shard, checkpoint hoặc telemetry. Chưa đủ để phân bổ toàn bộ thời gian của run H100 cho từng nguyên nhân, hoặc bảo đảm một sửa hash sẽ nâng GPU utilization đến một mức cụ thể. Không áp dụng projector/cache hoặc thay source từ bằng chứng này.

## Tài nguyên và lưu giữ

Toàn chương trình 3,88giây wall, 3,28giây process CPU, peak RSS đo khoảng223MiB. Cap của lượt kiểm là120giây CPU/wall và2GiB RSS, không chạm cap. Giữ script, log, JSON kết quả và pstats trong bundle này. Không thay đổi cache, model, source production hoặc run GPU đang chạy.
