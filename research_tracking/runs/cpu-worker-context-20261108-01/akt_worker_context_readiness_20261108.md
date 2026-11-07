# AKT — context bất biến, phase CUDA có giới hạn và lifecycle CPU thật

Ngày 08/11/2026. **Phần mềm CPU đã kiểm; CUDA mới chưa chạy.** Đây là bằng chứng kỹ thuật, không là kết quả so sánh mô hình hay quyền chạy Junyi/full CV/Modal. Tái sử dụng source AKT NonRasch pinned commit `01b7e8d7d7c862cabc9467108e3e7f2555653a88`; không thay kiến trúc hoặc hyperparameter nghiên cứu.

## Thay đổi đã thực hiện

- Context sidecar có SHA riêng đi từ watchdog sang worker, preflight, Gate2, authorization, loader và recovery. Chỉ nhận input nhỏ khai báo synthetic trong `artifacts/akt/`, không đổi defaults của pipeline CPU lịch sử. Không thêm trường vào dataclass cấu hình hoặc cách tính config hash.
- Phase `cuda-smoke` có tên riêng, bắt buộc context synthetic + đúng một GPU + giới hạn bộ cấp phát VRAM 64MiB–2GiB. Architecture/caps lấy từ smoke kỹ thuật hiện hữu; không cho CPU smoke/pilot tự chuyển device. Chưa có actual hardware test của phase này.
- Kiểm quyền chạy trong tiến trình con trước khi import Torch/runner/data. Mismatch nguồn, context, input hoặc giới hạn bị từ chối. Resume không được đổi context hoặc CPU sang CUDA.
- Tạo output directory/manifest trước CUDA initialization để lỗi thiết bị không bị che bởi lỗi ghi file. Callback tài nguyên đo allocator khi CUDA phase thực thi; unit tests hiện dùng thiết bị giả.
- Từ chối `inner_val_fraction` khác 0,1: implementation split hiện hành vốn cố định 10%; trước đây trường khác giá trị này không được thực thi đúng. Không đổi split 10%, seeds hoặc config mặc định.

Nguồn: [context](../../src/knowledge_tracing/akt/context.py), [watchdog](../../src/knowledge_tracing/akt/watchdog.py), [runner](../../src/knowledge_tracing/akt/runner.py), [device budget](../../src/knowledge_tracing/akt/device_budget.py), [builder input](../../scripts/akt/prepare_synthetic_context.py).

## Kiểm chứng

| Bằng chứng | Kết quả xác nhận | Giới hạn |
|---|---|---|
| Focused context/CUDA-budget/runner/worker/watchdog/CLI-recovery | 78 PASS, 89,33s | Windows CPU; CUDA API giả trong unit tests |
| Full Gate18, `tests/akt tests/shared_kt` | **661 PASS, 177,08s**, 0 failure/error/skip | Không bao gồm SAKT/GKT/demo suites riêng; không phải GPU Gate4 |
| Context recovery negative controls | 11 PASS, 4,23s | Validator/envelope fixtures; không thêm một hardware recovery run |
| Synthetic builder | 53 PASS, 6,50s | Chỉ chuẩn bị input, execution ban đầu false |
| Public watchdog → subprocess worker, real runtime/source/lock/Gate/auth/data guards | **PASS**, child lifecycle 11,46s, worker phase 4,93s | Dataset hoàn toàn giả, d_model32, 2 optimizer steps; không refit hoặc research benchmark |

Gate18 report SHA `8d51380ed58b104aea0c0de37bdeb097d12e45071252ec973a696dc1fc7ac66d`; [report](../../artifacts/akt/preflight/gate2-evidence-20261108-context-18.json). Các counts có phần giao nhau; không cộng để tạo số thí nghiệm độc lập.

Lifecycle thật dùng 8 dummy learners × 8 tương tác, loại outer-fold0 sentinel; 6 inner-train learners/48 targets, 1 inner-validation learner/8 predictions, hai batches và hai lần cập nhật. Checkpoint tốt nhất epoch1 được reload đúng state; tám dòng fitted khớp user/source_row/exercise/time/label của input giả, history_available chính xác 0..7, không OOV. Split hash gắn trong checkpoint; final smoke manifest hiện không giữ lại field cohort của bản ghi tạm, nên không suy counts từ field không có. Đã đối chiếu deterministic split, checkpoint identity/support và exported rows riêng.

Checkpoint SHA `e8db14d76f852e88e25c48861fffc2f57ed62156f8f219ed86b593837cf98c08`; [outputs gốc](../../experiments/akt/results/ctx0801/), [acceptance](../../artifacts/akt/local-tests/context-real-cpu-20261108-01/acceptance.json), [alignment](../../artifacts/akt/local-tests/context-real-cpu-20261108-01/alignment.json). Run này chỉ kiểm selection/validation/export, không phải đầy đủ outer refit. Không dùng toy loss/AUC để kết luận mô hình tốt.

## Lần thử lỗi được giữ

- Focused trial03: 70 PASS/1 failure do Git upstream ownership guard trong môi trường chạy. Trial04 dùng exact upstream `safe.directory` chỉ trong môi trường tiến trình, đạt 71 PASS; không sửa Git global hoặc bỏ provenance guard. Trial05 mở rộng watchdog/CLI recovery đạt 78 PASS.
- Builder trial01 có lỗi CLI fixture; giữ cùng trial02 PASS và trial03 chuẩn bị input.
- Alignment verifier attempt01 giả định `split_hash` có trong final manifest, gặp `KeyError`; sửa verifier đối chiếu checkpoint và subset hash thực tế. Không sửa model outputs hoặc chạy lại training. Source verifier trước/sau được giữ; ghi chú này tường thuật output đã quan sát, không giả làm raw stderr log.

## Giới hạn và bước kế tiếp

Hash pre/post của đường dẫn input không bảo đảm một atomic snapshot khi có tác nhân khác sửa Parquet rồi phục hồi bytes giữa lúc đọc. Bản thử này dùng input dummy bất biến trong phiên; không coi hash là sandbox/chứng thực an ninh. CUDA allocator cap không là toàn bộ VRAM driver/process hay hard cap hóa đơn. Watchdog cap thời gian/RAM không thay ngân sách cloud.

GPU08 mới là [proposal môi trường](../../docs/akt-linux-cuda-environment.md): chưa có full Linux transitive hash lock/image digest. Actual CUDA kitv12 dùng Torch2.14.1 khác candidate2.7.1+cu126 và mã worker mới, nên không chứng nhận phase mới. Cần Linux isolated runtime, source-bound tests và lifecycle CUDA thật trước throughput đại diện/Modal. Chưa chi credit; không tự chấp thuận S04/S05, Holdout, full CV hoặc thay protocol.

Bundle bất biến của batch: [cpu-worker-context-20261108-01](../runs/cpu-worker-context-20261108-01/README.md). File lớn giữ tại experiments; bundle lưu code/log/XML/manifests/hash và bản dự đoán dummy nhỏ để báo cáo có thể trích dẫn.
