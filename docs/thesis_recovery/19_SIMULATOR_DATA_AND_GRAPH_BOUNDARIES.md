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

## Điều kiện cho gói collector kế tiếp — source inspection, chưa implementation

Nguồn: notebook `paper2/rivf2026_gam_kt_artifact_v20/rivf2026_gam_kt_artifact_v20/source/adaptive_lms_bkt_gam_graph_gam_kt_research_ready_v2_1.ipynb`, cell9/15/17/19 (zero-based, chỉ parse AST/source, không chạy notebook).

1. `persona_base_abilities` (cell9) có graph-smoothing: mỗi concept phụ thuộc0.28mean(parent raw) và0.72raw local. Đổi graph khi sinh base theta sẽ đồng thời đổi cấu trúc ability. Khi cần isolate graph estimator/controller hoặc prerequisite learning mechanism, phải giữ base-state realization cố định trong paired comparison; phương án factorial chính thức vẫn cần duyệt. Không gọi mỗi graph condition một lần rồi giả định cùng seed là đủ.
2. `LatentStudentEnvironment.interact` nhận hai uniforms từ ngoài, trả `y` cùng `p_true`, theta_before, learning_gain và prerequisite_deficit. Collector phải xuất observable projection từ whitelist, oracle sidecar riêng; không serialize toàn bộ dict return vào training record. Không đổi source environment.
3. `generate_replay_events` (cell17) dùng topological concept order; chọn item bằng `choose_question(cid, env.theta_at(...), Counter())`. Đây là logging policy có oracle access vào latent ability để chọn difficulty. Fixed-stream predictive comparison có thể dùng nếu ghi đúng giới hạn; không coi nó là coverage ngẫu nhiên, deployment-like policy hoặc causal graph evidence. Generic AKT training corpus không được tự kế thừa điều này mà không ghi behavior-policy provenance/sensitivity.
4. `run_closed_loop` (cell19) tạo outcome_uniforms và learning_uniforms theo timestep trước vòng model, rồi reuse cùng base/uniforms cho mọi policy. Collector version mới cần khai báo rõ cách lấy hai channels từ response seed và behavior RNG; lưu uniforms/initial-state hash ở oracle provenance nếu cần paired replay. Common random numbers giảm variance, không tự bảo đảm causal estimand hoặc tương đương lịch sử.
5. Khóa clock unit/timezone/start và gap rule trước khi xuất `ItemQuery.timestamp` integer. Schema hiện kiểm thứ tự/số nguyên, không tự chứng minh unit là seconds hay milliseconds. Dùng unit nhất quán giữa generator/session/environment; AKT gốc không dùng elapsed calendar time không có nghĩa timestamp unit không quan trọng với forgetting environment.
6. Generator manifest phải gắn split-plan/domain/source hashes, profile allocation (metadata riêng), RNG states/mapping, logging policy, clock semantics, cap và role. Sinh shard train trước; không đọc/sinh final audit cohort để thiết kế train/calibration. Feature support và history coverage theo behavior policy phải được báo riêng.

Đây là prerequisite cho collector và role-aware trainer, không phải approval chạy full simulator hoặc tự đổi training distribution. Không gọi các64arithmetic fixture events là simulated learner training data.

## Kết thúc gói DATA01–04

70targeted tests và Gate2-11 mới361tests đều khôngfail/error/skip, source/lock/upstream stable. Bundle gate và report tại `research_tracking/` ghi log/hash/proof; TASKS có DATA05/06planned cho collector fixture và role-aware runner. S04/S05 vẫnpending; chưa có generated research cohort, trained graph model hoặc GPU result. Git raw-byte verification24bundles/225outputs và task DAG53PASS; xem `research_tracking/reports/git_evidence_verification_simulator_data_20261107.json`.

## DATA05–06 — Collector và adapter đã cài trong phạm vi fixture

`src/knowledge_tracing/simulator_collection.py` có `CollectionRecipe` explicit và `collect_training_fixture(plan, profiles=..., recipe=...)`. Entry point chỉ sinh train shard, tối đa2learners×12events/call,30giây/call. `cyclic_items` hoặc `uniform_items` chọn từ84items mà không đọc oracle. Phương trình environment/base ability giữ nguyên nguồn Paper2; RNG collector riêng có version, không claim reproduction published runs. Outcome/learning channels được derive riêng từ response seed, ổn định prefix khi tăng cap; behavior RNG riêng. Clock cố định Unix seconds UTC, event đầu start+gap.

Return tách trajectories observable, oracle sidecar và manifest. Oracle lưu initial state/hash, profile/seed mapping, response/behavior RNG states, uniforms, per-event latent diagnostics và final state để replay. Latent RNG nằm trong `persona_base_abilities`: lưu seed/function-source identity và actual base state, không giả ghi internal RNG state mà hàm nguồn không expose. Source/input paths canonical POSIX để domain identity không đổi chỉ vì Windows/Linux path separator. Môi trường/cross-platform numerical execution chưa được xác minh chỉ bằng canonical paths.

`src/knowledge_tracing/akt/simulator_data.py`:

- `SimulatorShard`: kiểm exact observable schema, learner role/coverage/domain, budget và data hash.
- `fit_simulator_encoding(train)`: train-only vocabulary/support theo learner; bind plan/domain/train shard, immutable support và fresh `ExerciseEncoding` cho native AKT.
- `iter_simulator_windows`: reuse `iter_window_slices`/`slice_causal_inputs` thật; train trả `TrainingWindow`, prediction trả `WindowInputs` hoặc `SimulatorUnseenQuery` không có correctness label. Không tạo `KTEvent.fold` giả.
- `scoring_targets`: ground truth/identity riêng cho kiểm coverage. Prediction windows chỉ có shifted history. Calibration/final và optimize selection bị chặn; không tự refit/train selection.
- Adapter này chưa là complete training/epoch-selection/checkpoint runner. Native CPU collator nhận được windows và đúng24unique target rows trong integration fixture; không instantiate NN/optimizer.

Fixture `cpu-sim-collector-20261107-02` và60targeted tests kiểm exact source-environment replay, repeat observable/oracle, profile-independent logging/RNG, global RNG invariance, caps/clock/role/oracle guards, OOV, source-bound vocabulary, target accounting và existing-window/collator parity. `...-01` failed vì tên hai pytest modules trùng nhau: giữ cả failed bundle, đổi tên test mới, không xóa cache để che lỗi. Trial local đầu lỗi Windows provenance path cũng được lưu source/log riêng. Software gate361 cũ stale sau source changes; cần Gate2 mới trước final acceptance.
