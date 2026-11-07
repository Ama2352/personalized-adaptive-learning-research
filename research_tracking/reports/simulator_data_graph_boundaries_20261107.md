# Hợp đồng dữ liệu mô phỏng và ranh giới graph context — 07/11/2026

## Kết quả và mức bằng chứng

Đã cài `src/knowledge_tracing/simulator_data.py` và `graph_context.py`. Đây là kiểm kỹ thuật bằng dữ liệu số học tổng hợp; chưa sinh cohort nghiên cứu, chưa train model hoặc chứng minh CG-AKT cải thiện learning. Không đọc Junyi/real Holdout, không đổi simulator lịch sử, không sử dụng GPU.

Nguồn hợp đồng: [19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES](../../docs/thesis_recovery/19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md), kế thừa interface [18_SIMULATOR_KT_INTERFACE](../../docs/thesis_recovery/18_SIMULATOR_KT_INTERFACE.md). S04/S05 về calibration/mastery/controller và model×environment allocation chưa được coi là đã duyệt.

## Các invariant đã kiểm

- Bốn roles train/selection/calibration/final có counts, namespace, root seed explicit. Đảo thứ tự cấu hình không đổi danh tính; tăng train count giữ các learner của roles khác. RNG streams latent/response/behavior có namespace riêng, không trùng trong fixture. Đây không là chứng minh độc lập thống kê hoặc generator thật đã dùng đúng seeds.
- Trajectory chỉ nhận item/time/source row/observed outcome, learner key và provenance. Reject oracle/unknown fields cả ở mức trajectory, observation, query và subclass có field bổ sung. Policy chỉ metadata, không là model feature.
- Audit train chỉ nhận shard train, không cần đọc shard final. Reject wrong-role, missing/duplicate learner, domain/plan mismatch, row collision, chronology, item lạ và vượt cap. Source rows unique trong mỗi shard; exporter sau này phải cấp row IDs theo contract này.
- Training projection không gán fold Junyi giả. Nó chưa là simulator training runner; calibration/refit allocation cần protocol riêng. Learner-disjoint chưa bảo đảm graph-realization-disjoint.
- Graph audit dùng `akt/windows.py::iter_window_slices`, cùng global target blocks/OOV barriers với AKT. Query không có outcome; current/future observation bị từ chối. Target OOV không được graph rescue thành fitted score.
- Confidence tách fixed-uniform, structural score, estimated probability (chỉ train provenance), oracle labels (reference mode). Metadata không chứng minh estimator được calibrate. Disabled/empty/zero-confidence/unobserved-parent trả không có weighted signal.
- Mean observed correctness và support không phải latent mastery, calibrated probability hoặc CG-AKT residual/gate. Chưa thay kiến trúc AKT.

## Counterexample về lượng thông tin

Fixture có tám prior events, H=3/T=2, query rank8. AKT effective start=5: graph audit chỉ dùng rows6–8. Đảo labels ở prefix rows1–5 giữ nguyên toàn bộ audit effective-window. Full-history sensitivity dùng rows1–8: mean đổi từ0.75 thành0.625. Hai phép so sánh dùng lượng thông tin khác nhau; lợi thế full-history không được tự quy cho edges. Số này chỉ là counterexample xác định, không là estimate trên learners.

Test riêng ở rank7 xác nhận global block có thể giữ bốn prior events khi H=3/T=2; dùng last-H slice sẽ sai. OOV ở rank5 đẩy start lên6. Default H100/T100 được kiểm ở ranks0/99/100/199/200/204.

## Run artifacts bất biến

| Run | Kết quả | Khác biệt |
|---|---|---|
| [cpu-sim-data-context-20261107-01](../runs/cpu-sim-data-context-20261107-01/README.md) | 65 tests pass, 0 fail/error/skip | Bản fixture ban đầu |
| [cpu-sim-data-context-20261107-02](../runs/cpu-sim-data-context-20261107-02/README.md) | 69 tests pass, 0 fail/error/skip | Thêm query/config/vocabulary provenance và kiểm weighting nhiều parent |
| [cpu-sim-data-context-20261107-03](../runs/cpu-sim-data-context-20261107-03/README.md) | 70 tests pass, 0 fail/error/skip | Chặn trực tiếp subclass mang oracle fields |

Mỗi bundle có README, manifest source/output SHA-256, execution log, proof JSON, test command/log/JUnit/result. Mỗi role có2learner×8events; tổng64events số học. Tên final trong fixture không là Holdout Junyi. Không sửa các bundle phiên bản trước. Muốn chạy lại phải chọn run ID mới:

```powershell
./.venv/Scripts/python.exe -B scripts/research/check_simulator_data_boundaries.py --run-id <NEW_RUN_ID>
```

## Software gate và giới hạn còn lại

Gate2 cũ296tests không áp dụng cho source mới. Runner cho phép ngân sách CPU suite explicit1–600giây, mặc định vẫn300; dự toán420giây cho suite mở rộng (lần trước292giây). Không đổi budget training/smoke/pilot; vẫn reject zero tests, failure/error/skip. Gate2 mới chỉ được công nhận sau source-bound report kiểm thành công.

Để có evidence RQ3 vẫn cần generator có manifest/seeds thật, trajectory coverage theo policy, simulator role-aware trainer/evaluator, graph residual/gate, confidence estimator/controls và protocol đã chốt. Hợp đồng mới chỉ loại bớt rủi ro leakage/incompatible history trước các bước đó.

## Nghiệm thu cuối

Gate2-11 (`20261107-simulator-data-11`) **361passed,0failed/error/skipped**, pytest152.84giây, source/lock/upstream stable, current pointer kiểm lại thành công. Timeout420giây chỉ cho CPU software suite. Report SHA `1d29261a5716368c71fd3da1cbbee7806a5f259af308cdc33a5691e785e78628`. Archive nguyên bytes ở [cpu-sim-data-context-gate-20261107-01](../runs/cpu-sim-data-context-gate-20261107-01/README.md), không thay Gate2/bundles lịch sử.

Inspection bổ sung trước collector (notebook Paper2 cell9/15/17/19): initial ability được parent-smoothing, replay chọn difficulty theo latent theta, closed-loop dùng paired uniforms theo timestep. Chi tiết và điều kiện giữ nguyên latent realization/oracle sidecar/clock unit ở mục collector của19. Đây là source evidence về thiết kế, chưa là kết quả chạy collector mới.

Để giữ evidence qua Git, bundle giữ bytes gốc kể cả CRLF; whitespace attribute chỉ công nhận CRLF hợp lệ tại runs. Logs bị ignore mặc định phải add explicit theo manifest; không normalize hoặc sửa logs đã đóng để qua kiểm tra. Portable kitv9 vẫn là snapshot trước gói này, không đại diện source361tests và chưa chạy Colab/CUDA.
