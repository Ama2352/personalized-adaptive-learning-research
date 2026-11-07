# Công cụ nghiên cứu local và phạm vi nghiệm thu

Cập nhật07/11/2026. Các công cụ dưới đây tạo nền tảng cho thực nghiệm. Các fixture nhỏ không phải bằng chứng về hiệu quả giáo dục hoặc benchmark trên Junyi. Implementation mới nằm riêng với notebook và artifacts lịch sử.

## Môi trường và lệnh kiểm

Chạy trong `D:\Dev\KLTN`, dùng `.venv\Scripts\python.exe`. Phiên đã xác minh interpreter/pip cùng thuộc `.venv`. Không cài thêm dependency hoặc sửa môi trường global.

```powershell
$env:PYTHONPATH='src;third_party'
.\.venv\Scripts\python.exe -B scripts/research/check_simulator_assumptions.py
.\.venv\Scripts\python.exe -B -m pytest tests/shared_kt -q -p no:cacheprovider --basetemp artifacts/akt/local-tests/<new-unique-name>
```

Parent `artifacts/akt/local-tests` phải tồn tại. Mỗi lần chạy dùng tên base directory mới. Với upstream AKT có ownership khác user, dùng Git safe.directory chính xác trong môi trường tiến trình kiểm tra, không sửa Git global.

## RQ1 paired decision trace

`knowledge_tracing.diagnostics.DecisionTrace` lưu event/learner identity, correctness, probability của item hiện tại, mastery scores của toàn concept set, ready set và selected concept. Mastery scores là output từ adapter được khai báo, không mặc nhiên bằng xác suất đúng của item hiện tại. Caller chịu trách nhiệm predict-before-update, chronology, threshold/calibration fit và model/graph provenance.

`compare_decision_traces` so đúng paired events cùng labels/concepts. Nó đo probability/LL/Brier delta, mastery crossings, ready Jaccard, action disagreement và threshold-local correctness calibration gap. `probability=None` được tính coverage riêng, không thành fitted prediction. Quyết định vẫn được đếm kể cả khi probability pair thiếu. Đây là mô tả paired trace, chưa có CI hoặc kiểm định theo event độc lập. Learner/seed-level inference là lớp tiếp theo. Threshold-local calibration dựa trên correctness, không phải calibration của latent mastery.

Các tests bao phủ prediction tốt hơn nhưng decisions giữ nguyên, mastery/ready/action đổi, OOV/null, duplicate/mismatched identities và probabilities ở0/1. Chưa tích hợp export trace vào Graph-GAM hoặc AKT controller, vì mastery interface còn cần chốt.

## RQ2 assumption và counterfactual controls

`scripts/research/check_simulator_assumptions.py` trích đúng method `LatentStudentEnvironment.theta_at` và literal `TRUE_FORGET_RATE` qua AST của notebook Paper2. Chỉ method này được compile, không execute toàn notebook hoặc chạy lại experiment. Report ghi notebook/cell/method hashes, actual rate, scaling factor và numerical error.

Fixture hiện xác nhận post-T retained gain sau14ngày tỷ lệ `exp(-.06*14)` khi không practice và decay đồng nhất. Trạng thái ở T vẫn phụ thuộc lịch sử trước đó. Không suy kết quả retained soft-mastery nonlinear hoặc dynamics mới từ identity này. Chưa kiểm zero-reentry trên đúng revision Paper1.

`experimental_controls.paired_mechanism_contrasts` tính interaction graph-on/off × prerequisite-mechanism-on/off, tách từng seed/profile. Nó từ chối thiếu/duplicate condition, khác latent identity hoặc random-stream identity. Identity strings phải đại diện nội dung thực do harness cung cấp. Đây là guard kỹ thuật, không tự chứng minh counterfactual assumptions hoặc causal interpretation.

`graph_controls.perturb_graph` hỗ trợ delete/add/reverse với số cạnh tường minh và local seed. Giữ toàn node set, bao gồm isolated nodes, chỉ trả DAG hợp lệ, ghi requested/applied counts và before/after hashes. Nếu không đủ thay đổi hợp lệ, nó raise thay vì hạ noise âm thầm. Chưa cung cấp degree/chapter/support-matched null graph, learned graph hoặc Junyi order-control analysis. Không gọi các perturbations hiện tại là gold graph hoặc matched negative controls.

## AKT recovery

`sampler.ReplayableWindowCursor` tái tạo shuffle bằng cùng seed và kiểm prefix digest. Tests so trực tiếp với `_shuffle_windows` hiện hành ở buffer1/3/1024 và các vị trí cut. Replay không chạy lại optimizer và không dùng global Python RNG. Chi phí đọc/hash là O(prefix), memory bounded theo buffer, cần benchmark trước large-data runs. Factory phải xác định và không dùng model-global RNG.

`resumable.train_resumable_epoch` là entrypoint Python cho bounded epoch, chưa thay CLI selection/refit. Nó dùng native `AKTAdapter.step`, cùng batch size và shuffle seed. Khôi phục counters và RNG, kiểm stream identity và giữ step/time/target caps cộng dồn. `max_targets` giới hạn số scored targets, không cắt batch để đạt cap. Cursor trả về chỉ bao gồm windows đã optimizer-update. `checkpoint_every_steps` mặc định1, có thể tăng để giảm số lần ghi. Khi dừng bình thường, batch cuối chưa lưu được flush thành checkpoint. Nếu process bị kill giữa hai lần ghi, khôi phục từ snapshot durable gần nhất và chạy lại tối đa một khoảng cadence. Overhead/durable cloud storage chưa đo.

Tests CPU ngắt sau step2, nạp checkpoint vào model mới và tiếp tục. Weights/loss khớp chính xác với original `train_epoch`, đủ17targets/9windows/5optimizersteps. Giới hạn khi resume không reset. Đây là correctness trên fixture nhỏ, chưa có CUDA/real-data interruption, process kill/Volume durability, early-stopper history integration hoặc full CLI recovery.

Kiểm thêm target cap qua resume xác nhận pending batch chưa update không bị skip, rồi tiếp tục đủ epoch khớp original weights/loss. Cadence2 với stop ở step3 lưu steps2 và3. Suite resumable/sampler/recovery-checkpoint đạt24passed13.54s, `evidence/akt-recovery-budget-verified-tests.log`. Lệnh đầu gõ sai tên test module không collection được, log riêng được giữ tại `evidence/akt-recovery-budget-tests.log`.

## Việc tiếp theo

### Khôi phục selection sau epoch đã validation

`training.select_checkpoint(..., save_recovery=True)` ghi `inner-recovery-epoch-N.pt` sau mỗi epoch hoàn chỉnh đã validation. Truyền `resume_checkpoint=Path(...)` cùng config, identity và budget để tiếp tục. Snapshot chứa model/Adam/RNG, toàn history, selected epoch và hash của best checkpoint. Early stopping được dựng lại từ history theo đúng thứ tự, kể cả các epoch không cải thiện. Best checkpoint phải còn nguyên cùng thư mục snapshot. Snapshot đã đạt patience trả kết quả mà không train thêm.

Config hash bao gồm output_dir và budget được khóa trong recovery identity. Resume dùng cùng thư mục run. Tên best checkpoint ở chế độ recovery có UUID để lần chạy lại sau crash giữa best-save và recovery-save không đè artifact cũ. Mặc định `save_recovery=False` giữ contract tên file và hành vi callers hiện tại. Snapshot epoch hoàn chỉnh là nhánh riêng với recovery giữa batch.

Kiểm actual AKT CPU có dropout so continuous với interruption sau validation epoch2. Weights, Adam state, torch RNG, validation losses và selected epoch trùng chính xác, cùng dừng epoch3 theo patience2. Có kiểm config drift, best checkpoint corruption và default artifact contract. Suite selection/training/checkpoint đạt34passed27.55s trong `evidence/akt-selection-recovery-tests.log`.

Giới hạn hiện tại là Python selection API. CLI watchdog/authorization chưa nhận tùy chọn recovery, refit và giữa batch chưa nối vào selection. Checkpoints được giữ immutable, cần tính dung lượng và cadence trước chạy lớn.

1. Nối resumable epoch với selection/refit orchestration và early-stopper/best-checkpoint state, giữ full authorization/resource gates.
2. Thêm export paired trace vào adapter đã chốt mastery, rồi chạy bounded synthetic integration.
3. Bổ sung graph triple identity manifests và degree/chapter/support-matched controls.
4. Kiểm controller invariant/counterexample với đúng Paper1 revision.
5. Thực thi GPU lifecycle và measurement sau khi runtime/authorization sẵn sàng.

RQ3 model augmentation, confidence construction và final comparison vẫn chờ accepted method contract. Các thay đổi local ở đây không cấp quyền cloud, real-data benchmark, Holdout hay final model selection.
