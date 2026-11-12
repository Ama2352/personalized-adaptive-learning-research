# Junyi — chuẩn bị lifecycle selected và full train-window cache

Bundle đang mở để nối tiếp nghiệm thu selected workflow và numerical diagnostic. Gói này ghi các kiểm hợp đồng, data preparation và bằng chứng lỗi đã giữ. Chưa có full Junyi training từ việc tạo cache.

## Đầu vào và ranh giới

`actual-selected-inputs.json` xác nhận full frozen roles của lượt Junyi Development outer4, gồm13.347.331train targets và1.600.343selection targets. Role tách learner, encoding fitTRAIN80, selection dùng kiểm epoch. Các phần refit90/calibration cần workflow freeze tương ứng của protocol hiện hành.

`full-encoding-independent-check.json` ghi vocabulary717exercise và support của native fitted encoding khớp phép kiểm SQL TRAIN độc lập. Encoding file cùng SHA nằm tại `artifacts/akt/window-cache/full-train80-20261112-02.encoding.json`. Phép kiểm này không mở Holdout.

## Diễn tiến tạo full window cache

1. Attempt01 bị timeout sau600giây. Encoding đã fit trong137,43giây, còn581shards/852.547.851bytes của cache chưa có COMPLETE. `full-cache-attempt01-failure.json` giữ nguyên chẩn đoán. Cache partial được giữ ngoài đường training.
2. Attempt02 tái dùng encoding sau đối chiếu support độc lập. Controller có cap1.800giây và giữ source SHA trong `full-cache-attempt02-controller.json`.
3. `full-cache-receipt02.json` xác nhận hoàn tất preprocessing sau **675,67giây**, giữ232.662TrainingWindow,13.347.331targets,23.936.131window tokens và126.774learners. OOV train bằng0.
4. Cache hoàn chỉnh nằm tại `artifacts/akt/window-cache/full-train80-20261112-02/`, với manifest, COMPLETE và inventory shard. Receipt ghim manifest SHA và encoding identity. Đây là cache training đầy đủ của TRAIN80, chưa có optimizer update hoặc model checkpoint từ thao tác chuẩn bị này.

`full-cache-prepare.log` giữ attempt đầu, `full-cache-prepare02.log` giữ lượt hoàn tất. Không cộng thời gian tạo cache thành thời gian training AKT.

## Kiểm phần mềm đã có output

- `contracts01.log/xml` ghi36tests đạt cho hợp đồng selected/authorization.
- `combined01.log/xml` ghi109tests đạt cho gói kiểm kết hợp lúc đó.
- `lineage-contracts.log/xml` ghi35tests đạt về lineage/hợp đồng bổ sung.
- `telemetry-tests.log/xml` ghi9tests đạt cho policy telemetry.

Các file này là bằng chứng tại snapshot tương ứng. Gate Linux CPU02 của [gói optimization](../junyi-gpu-optimization-20261112-01/README.md) sau đó đạt2.197tests. Lượt T4 của gói đó có5epochs thực trên cohort nhỏ, nhưng probe tổng dừng vì parity vượt1e-6 và recovery thật chưa được thực hiện.

## Bảo toàn log lịch sử

`late-log-reconciliation.json` và `late-gpu-startup-full.log` giữ phần log nhận muộn sau khi bundle engineering trước đã đóng. Record giải thích nguồn byte được bảo toàn và vị trí bản muộn riêng. Không dùng startup crashloop nhận muộn để thay trạng thái của một lượt hoàn tất khác.

## Phần còn thiếu

Nhánh chính cần giải quyết parity legacy/batched bằng checkpoint đã giữ, hoàn tất recovery thực và đối chiếu throughput/resource trên workload phù hợp trước full selected fit. Full train-window cache giúp tái sử dụng preprocessing; chi phí và kết quả neural fit vẫn cần được đo riêng. Các điều kiện AKT graph-free/fixed/confidence/gated, refit/calibration và đánh giá độc lập tiếp tục giữ trong backlog KLTN.

Checkpoint/GPU artifacts lớn nằm ở native output của run; hồ sơ này giữ logs, counters, nguồn và tham chiếu. Bundle tiếp tục mở trong thời gian chẩn đoán, chưa có quyết định nghiệm thu final.
