# GPU, artifact và ngân sách

Ngày tra cứu official Modal 06/11/2026. Chưa xác minh account, credit eligibility hoặc quota của nhóm. Runtime local `artifacts/akt/preflight/runtime-v2.json` là torch2.7.1+cpu, CUDA false. Full GPU readiness BLOCKED đến khi có image Linux pinned và ladder đạt. Synthetic CPU success không chứng minh CUDA readiness.

## Nguồn giá và giới hạn nền tảng

Theo [Modal pricing](https://modal.com/pricing), GPU Functions giá USD/s là T4 .000164, L4 .000222, A10 .000306, L40S .000542, A10040 .000583, A10080 .000694, H100 .001097. Tương ứng USD/h .5904,.7992,1.1016,1.9512,2.0988,2.4984,3.9492. Physical CPU core .0000131/s, GiB RAM .00000222/s. Starter niêm yết30 USD credit/tháng, không đưa credit vào budget guarantee. Volume .09 USD/GiB/tháng với allowance1TiB ghi trên pricing, egress .04 USD/GiB sau included allowance theo plan. Điều kiện account và allowance phải xác minh trước upload. Không trừ credit hai lần khi lập tổng chi phí.

Với2 physical cores+8GiB, CPU/RAM .222336 USD/h, rate tổng L4 1.021536 USD/h, A10 1.323936, L40S2.173536. Đây là request ví dụ để so sánh, chưa cấu hình đã duyệt. Giá training GPU Functions, không áp Sandbox CPU premium. Chọn L4/A10 khởi đầu, L40S chỉ nếu measured cost/target tốt hơn. Chưa có VRAM benchmark để khẳng định batch nào đủ.

[Timeouts](https://modal.com/docs/guide/timeouts) ghi mặc định300s, tối đa24h/attempt, timeout mỗi retry reset, user code cần tự deadline vì platform có thể quá vài giây. [Volumes](https://modal.com/docs/guide/volumes) hỗ trợ persistent storage, flush và commit trước exit, không coi temp container là checkpoint durable. Volume v2 recommended trong docs hiện hành, cần fs behavior test riêng. [Budgets](https://modal.com/docs/guide/budgets) phân biệt workspace usage cap trước credits với spend limit net sau credits, có dừng workloads khi reach spend limit. Environment budgets dành Team/Enterprise và chỉ compute. Không thay bằng alert. User/account owner cấu hình workspace cap và net spend limit, local ledger còn cần reserve cho jobs và storage.

## Artifact contract trước mỗi run

Input manifest immutable chứa run_id, experiment_id, environment_id, protocol_id/version, source commit và dirty-source SHA inventory, upstream commit, dependency lock/image digest, CUDA/PyTorch/driver versions, model and graph variant, architecture/hyperparams, exact train/inner/calibration/outer learner hash lists, dataset canonical and split hashes, vocabulary/concept/item mappings, graph direction/hash, edge confidence provenance/calibrator fit IDs, seed/RNG, initialization checkpoint and parent hash, expected fitted/OOV/targets/windows/optimizer updates, budget seconds/USD/RAM/VRAM/steps. Không include secrets hoặc nguyên learner IDs nếu artifact public.

Training outputs model weights, optimizer, scheduler state hoặc explicit null nếu không dùng, Python/NumPy/Torch/CUDA RNG, epoch/global_step, sampler epoch seed cùng buffer/order/cursor hoặc deterministic replay position, data cache fingerprint, consumed target/window IDs checksum, scaler nếu AMP, early-stopper best_loss/best_epoch/stale/history, best và latest checkpoint tách tên, complete/partial flag, logs train/validation loss và count, selection evidence, wall/phase timings, RAM/VRAM peaks, throughput scored targets/s, resource termination reason, hash inventory và completion certificate.

Evaluation outputs Parquet một row mỗi expected target, source_row/event_id, learner privacy-safe ID với salt/version hoặc private mapping, timestamp/tie order, exercise/concept, y,p,fitted/OOV/null reason, fold/split, model/checkpoint hash, history length/effective history, coverage. Summary canonical AUC/LL/Brier/ECE15/accuracy và calibration quanh mastery, CI, paired common-row table, OOV riêng. No finite p ngoài[0,1], duplicate/missing IDs fail artifact gate. Null OOV không metric như fitted. RQ3 thêm graph hash, c values/source, gate values, graph residual influence, off/fixed comparator identity, action traces/ready sets, latent states chỉ evaluation side, net/gross/retained outcomes.

Acceptance không yêu cầu metrics vượt BKT hay graph-free. Cần expected target accounting, no overlap/future labels, checkpoint reload predictions tolerance, all hashes và completed epochs đúng, cancellation/recovery và cost within caps. Failure trước contract completion là incomplete/failed dù exit0. Không xuất partial epoch thành selected model.

Existing supports model/optimizer/RNG/encoding, complete-epoch checkpoint, source/config identity, inner validation/selection, OOV/export, wall/RSS caps và progress. Missing mid-epoch sampler/stopper recovery, full CLI resume chứng minh, scheduler/scaler contract, CUDA image/telemetry/phase authorization, Volume durability, graph/gate outputs, simulator export contract. Exact fields cần engineering test schema ở T07/T08.

## Ladder và entrypoints

Hiện tại chỉ có `python -m knowledge_tracing.akt.cli preflight|smoke|pilot|fold-readiness --config ...`, smoke/pilot khóa CPU. `fold0.json` là readiness execution_enabled=false. GPU commands bên dưới là **proposed entrypoint**, chưa tồn tại, phải implement tại T08 trước launch. Không copy chạy như command hiện hành.

Stage0 command hiện hành `PYTHONPATH=src;third_party`, `.venv/Scripts/python.exe -B -m pytest tests/akt tests/shared_kt -q -p no:cacheprovider --basetemp <new-writable-unique-dir>` và `python -m knowledge_tracing.akt.cli preflight --config experiments/akt/configs/fold0.json`. Preflight chỉ metadata, GPU preflight cần pinned image tests/source snapshot riêng. Logs phiên này trong evidence, environment failures phải giải quyết trước regenerate Gate2.

Proposed common command `modal run scripts/akt/modal_plan_runner.py --stage S --run-spec <signed-json>`. Required spec contains hard work caps, artifact expected counts, source identities và auth. Stage CLI phải từ chối stage không approved, không tự chuyển stage sau exit0. File chưa được tạo trong planning task.

| Stage | Input và max workload | Budget đề xuất / GPU time ceiling | Output/acceptance | Failure/recovery/approval |
|---|---|---|---|---|
|0 local | Synthetic, hashes, schema, image import static, no data query |0 USD, test suite≤5phút |Tests/import pass, config mapping/source manifests |Mismatch stop, sửa environment, autonomous safe engineering |
|1 CUDA smoke |d256 synthetic B4,L200, forward/backward/step≤5 |L4 one GPU,5phút, ≤.086USD compute, allocation cap1USD |Finite grads/update, causal masks, VRAM peak, CUDA event timings |OOM/nonfinite stop, diagnose image/batch, explicit smoke approval |
|2 short |≤100 optimizer batches, validation≤10, synthetic initially |10phút, ≤.171USD, cap1USD |Train+val+checkpoint save/load+hash on Volume |No artifacts/latency excessive stop, no automatic retry, approval |
|3 recovery |Continuous20steps vs10+interrupt+resume10, sample ledger |15phút, ≤.256USD, cap1USD |No duplicate/skipped committed samples, model/optimizer parity, durable committed checkpoint |Mismatch blocks larger jobs, repair cursor/RNG, approval |
|4 small lifecycle |Bounded Dev ≤100k targets, max1 complete epoch, complete val/export |30phút, ≤.511USD, cap2USD |All target IDs coverage, selection/reload/export and persisted manifest valid |Cap before epoch end=incomplete, smaller approved cohort next, new auth |
|5 throughput |Representative length distribution ≤1m targets, val subset, 3 timing repeats within cap |30phút, ≤.511USD, cap2USD |Scored train/val targets/s median and p10, startup/load/checkpoint overhead, cost/target |Telemetry unsynchronized invalid, explicit bounded approval |
|6 representative |≤10% fold, max1epoch and val, memory/loader scaling |2h, ≤2.044USD, cap3USD |Projection conservative within total approved budget and deadline, checkpoint resume validated |Projected cost/runtime excess stop and revise plan, new approval |
|7 full Dev |One approved fold/variant at a time, E≤20 existing cap pending protocol |≤6h invocation with recovery continuation, projected USD before auth |Full artifact contract and final review before next fold |No retry when data/numeric/identity failure. Full CV/hyperparam scope need human approval |

Ceilings above are compute examples at L4+2core8GiB, startup+storage+egress extra. Stage caps1/1/1/2/2/3 sum10USD reservation proposal, stage7 excluded. Images build/data preparation run CPU where possible, avoid GPU idle loading. One GPU and one active training job global initial max. Full epoch may exceed invocation6h, need time cap checkpoint handoff and explicit continuation auth in total budget.

## Recovery semantics

Checkpoint every5 minutes or500 optimizer steps, whichever first, at optimizer-step boundary. Latest records next unconsumed window, shuffled buffer and RNG. Persist temp→fsync→publish unique immutable name→close→Volume.commit→separate process reload+SHA certificate. Recovery reads only committed certificate. Crash after step before checkpoint allows replay work since latest checkpoint, metrics/sample ledger discarded for uncommitted steps. Exactly-once accepted training ledger from recovered checkpoint, no counting aborted optimizer updates twice. Compare same-image deterministic CUDA continuous/resumed max absolute prediction tolerance1e-6 and weights1e-6 proposed, first test calibrates whether kernel nondeterminism requires documented relaxed tolerance before scientific runs. Match consumed IDs exactly even if numeric tolerance differs. No scheduler currently, null state explicitly.

Retry limit0 automatic. One manual infrastructure retry per stage after cause and budget recheck, new run attempt ID linked to immutable failed attempt. Resume does not reset total run-dollar/time allowance. On loss of durable checkpoint stop full training until storage fixed. Parent/worker kill must be tested on Modal, no assumption from Windows process result.

## Công thức cost và scenarios

Measured GPU throughput hiện UNKNOWN. CPU pilot32 batches/7.346 targets không chuyển sang CUDA forecast. Let Ntr,Nval,Nout actual targets from accepted preflight, rtr,rval targets/s incl padding/data overhead, Es epochs selection, Er refit. Per outer fold seconds = startup+load + Es*(.9Ntr/rtr+.1Ntr/rval) + Er*Ntr/rtr + Nout/rval + checkpoint+export. Không double-count val mỗi selection epoch. Actual support/OOV lấy manifest. 5 folds là tổng từng fold, không luôn5×fold0.

Để kiểm độ nhạy, dùng report Dev total D=20.706.208, approximate Ntr=.8D,Nout=.2D. Nếu Es=Er=E, rtr=rval=r và overhead chưa tính, work/fold≈(2E*.8+.2)D, work5fold≈(8E+1)D. Đây là phép tính target-equivalent, chưa đo runtime. Inner validation .1 training được tính trong E*.8D. Training4 models Junyi xấp xỉ4 lần nếu equal E/r, cộng ablations/SAKT/GKT và simulator, không báo một AKT là toàn nghiên cứu.

| Scenario giả định để stress-test | E, r giả định | AKT Dev5fold GPU giờ / L4 compute USD |4 variants Dev5fold | Ý nghĩa |
|---|---|---|---|---|
|Optimistic |E3,r20k |7.19h /7.34USD |28.76h /29.38USD |Chưa measurement |
|Expected planning |E10,r5k |Work=81D, giờ93.18, USD95.18 |372.7h,380.7USD |Chưa measurement |
|Conservative |E20,r1k |Work=161D, giờ926.03, USD945.99 |3704h,3784USD |Một GPU vượt thời gian thực nghiệm |

Kiểm tra số học. Optimistic work25D/r20k =25.883s≈7.19h,7.34USD, 4variants28.76h,29.38USD. Expected81D/r5k=335.441s≈93.18h. Conservative161D/r1k=3.333.699s≈926.03h. Dấu chấm trong số giây ở đây phân tách nghìn. Các throughput giả định chỉ là axes sensitivity, không dự báo AKT. Es/Er có thể khác, phải thay bằng history pilot. Overhead10/25/50% là reserve scenario, không measured overhead.

Một epoch outer train 16.565m/rtr seconds, val1.6565m/rval seconds, outer eval4.141m/rval. Refit allDev E*D/rtr. Additional final Holdout inference chỉ nếu authorized, tách cost. Simulator4variants×3training seeds×E×Nsim/r + val + closed-loop query count/rinfer. Confidence calibration/graph learning CPU và ablation retrains thêm theo actual manifest. Learned/noisy train graph thay mỗi condition đòi fit riêng. Same-checkpoint gate-off/shuffle confidence inference không fit lại nhưng khác question so với trained ablation.

Đơn giá storage 100GiB một tháng nếu chargeable toàn bộ là9USD trước allowance, egress10GiB chargeable .40USD. Không tính allowance khi chưa biết shared usage. Startup time phải đo từ billed allocation, không dùng timeout execution bỏ startup ra khỏi cost. Ngân sách đề xuất PlanA envelope150USD, B300USD, C600USD đều **chưa được duyệt**, phải thay bằng measured projections trước stage7. Nếu conservative projected vượt envelope thì không launch full matrix.

## Efficiency với validity

| Tối ưu | Lợi ích dự kiến/độ khó | Verification và ảnh hưởng protocol |
|---|---|---|
|Cache deterministic windows |Giảm DuckDB/materialization lặp, vừa |Exact target/order/mask/vocab hashes, không train on cached cross-fold features |
|Length bucket |Giảm padding, vừa |Coverage exact, seeded order/loss weighting, batch schedule thay cần protocol review |
|GPU batch tuning |Tăng utilization, thấp |Finite causal parity, optimizer batch semantics thay phải approve, không tự tăng effective batch |
|Async loaders/pin memory |Giảm idle, vừa |No duplicate windows/workers, resource telemetry |
|Resume |Tránh fit lại, cao |Stage3, scheduler/RNG/cursor parity |
|Inner holdout thay innerKfold |Giảm K lần model selection |Giữ outer boundaries, advisor duyệt interpretation |
|Same initialization |Giảm variance so sánh, thấp |Separate fits, no unequal pretraining exposure |
|AMP |Có thể nhanh hơn, vừa |DEFER đến sau FP32 CUDA lifecycle, numerics/calibration tests và protocol approval |

Stop khi source/data/graph identity mismatch, NaN/Inf, duplicate targets, coverage mismatch, RAM/VRAM ceiling, no progress heartbeat quá120s, quota/cost cap reached hoặc projected remaining spend vượt allocation. Reserve cost trước mỗi job, deduct elapsed telemetry, stop sớm đủ margin để checkpoint. Người dùng duyệt full budget và exact experiment config, advisor duyệt methodology. Alerts chỉ supplementary.
