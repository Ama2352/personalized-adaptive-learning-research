# Hợp đồng dữ liệu mô phỏng và ranh giới graph context

Engineering CPU tiếp SIM01–SIM05, ngày07/11/2026. Không thay split/protocol Junyi hoặc BKT, không generate/train dữ liệu thật, không chọn mastery/calibration hoặc adopt kiến trúc CG-AKT. S04/S05 vẫn pending. Tài liệu này là hợp đồng để chuẩn bị implementation, không là chứng cứ learning benefit.

## Gói DATA01–DATA04

| ID | Mục tiêu | Nghiệm thu |
|---|---|---|
|DATA01|Plan learner/seed-family cho train, selection, calibration, final|Counts/namespace/root seed khai báo explicit; IDs/seeds không giao role; reproducible khi đảo thứ tự cấu hình; tăng train count không làm đổi learner của roles khác|
|DATA02|Observable trajectory schema và role-bound audit|Reject wrong-role/duplicate/missing learner, chronology/row identity, wrong domain/plan, unknown item và oracle fields; validator chỉ nhận shard của role yêu cầu, không mở final để kiểm train|
|DATA03|Graph context audit trên cùng effective window|Dùng geometry thật của AKT, OOV barrier và global block; past-only, không current response; full-history sensitivity gắn nhãn riêng; confidence có provenance, oracle chỉ reference mode, disabled/empty graph không mang signal|
|DATA04|Bounded fixtures, nguồn/hash/log và handoff|Tiny fixtures, không NN training hoặc large simulation; test source-bound, update state/README, commit riêng; không sửa bundle đã đóng|

## Các điều không được tự suy ra

- Seed namespace tách biệt là invariant kỹ thuật, không là bằng chứng độc lập thống kê hoặc simulator đủ đa dạng. Counts/seed families ở fixture không là allocation được duyệt cho nghiên cứu.
- Calibration role phải tách khỏi selection/final; refit có dùng selection hay không cần protocol riêng, không tự gộp roles.
- `fold` của Junyi không dùng thay tên role simulator. Model-facing records chỉ có item/time/row và observed outcomes; chuyển sang AKT training runner có role-aware semantics là bước sau, không gán fold giả để qua guard.
- Oracle latent states/edge labels thuộc sidecar đánh giá riêng. Không đưa profile/ability/true probability/true edge label vào observable trajectory hoặc model input.
- Confidence ổn định hoặc association không tự là xác suất cạnh đúng. Gói này audit support/weighted evidence, không học graph gate hoặc tạo residual logit.
- Primary cùng effective history là đề xuất cần chốt trong S04/S05. Prototype cho cả audit effective-window và sensitivity full-history, nhưng không tự dùng sensitivity làm primary comparison.
- Split theo learner chưa bảo đảm graph-realization-disjointness. Nếu đánh giá confidence trên true/noisy edges mới, phải có graph-realization split/provenance riêng theo protocol.

## Ghi bằng chứng

Test logs/README/manifest của gói lưu trong `research_tracking/runs/<run-id>/`, báo cáo diễn giải ở `research_tracking/reports/`. Không thêm root folder mới. File tạm pytest dùng vùng existing `artifacts/akt/local-tests/`. Source changes làm Gate2 cũ stale; không lấy PASS296 cũ cho build mới. Suite trước mất292/300s: dự toán timeout CPU software gate explicit trước final refresh, giữ mọi test/failure/skip checks và không tăng caps của smoke/pilot/training.
