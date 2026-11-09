# GPU, artifact và ngân sách

## Trạng thái hiện hành09/11 — CPU admission đã đạt, CUDA còn thiếu

Nguồn177 và81module hiện hành đã qua1.748ca kiểm Windows CPU, không failure/error/skip. Runtime schema2 được đo mới trong .venv, explicit index dẫn đúng Gate05 và globalpointer lịch sử giữ nguyên. [Gate đã đóng](../../research_tracking/reports/akt_windows_gate_accepted_20261109.md), [runtime và index](../../research_tracking/reports/akt_windows_runtime_gate_index_20261109.md).

Main A0 guard đã được thực hiện qua public factory trên corpus mô phỏng đã lưu, dùng cấu hình frozen20epochs và resource envelope chỉ dành cho guard. Outer ghi10,9232783giây,20Git provenance commands thật, source/data trước=sau, lỗi rỗng và Job0. Không gọi mô hình, optimizer hoặc teacher. Trước đó prepare và materialize cũng đã đạt. [Gói53outputs đã đóng](../../research_tracking/reports/akt_main_guard_admission_20261109.md) và commit8e2ffc5 giữ đủ raw logs của ba operation. Đây là admission proof, chưa có selected-fit hoặc prediction export từ public producer.

Chuỗi chốt tiếp theo gồm corpus engineering10×84 được sinh bằng collector thật, một vòng selected lifecycle hoàn chỉnh trên CPU, port và kiểm Linux/CUDA, checkpoint recovery trên GPU, rồi benchmark targets/s và chi phí. Config đầy đủ của nghiên cứu giữ nguyên. Vòng dữ liệu nhỏ chỉ phục vụ kiểm tích hợp trước nghiên cứu, không được đưa vào bảng so sánh mô hình như kết quả fitted chính thức.

Audit nguồn bổ sung chỉ ra đường selected-fit thực hiện nhiều lần xác minh provenance đầy đủ. Đường thành công có15+4E+2Sdispatch metadata, vớiE là số epoch vàS là số checkpoint tốt nhất được lưu. Đủ20epochs với patience3 có109–135dispatch, tương ứng1.090–1.350Git calls riêng cho metadata. Rà soát tiếp trước actualfit xác nhận hai constructor còn gọi upstream.load_upstream, mỗi lần thêm10Git commands. Tổng đường thành công vì vậy là10N+20, tương ứng1.110–1.370Git calls nếu đủ20epochs. Đây là đính chính phạm vi của audit đã đóng, không sửa hồ sơ cũ và chưa đo thời gian hoặc chi phí riêng. Tiny lifecycle phải đo tách provenance, đọc dữ liệu, neural work và checkpoint để tính cost/target. Envelope16MiB của guard không chứa được cả reserve66MiB trước một checkpoint, nên fit phải có allocation mới. Chưa áp dụng đề xuất đổi mức kiểm integrity. [Audit metadata gốc và cách đo](evidence/main_revalidation_cost_source_audit_20261109.md).

Kit cũ đã có tiny T4 lifecycle/recovery được lưu bên dưới. Các kết quả đó giữ giá trị cho đúng phiên bản và dữ liệu synthetic đã chạy. Pipeline nghiên cứu mới có adapter, context và checkpoint CPU riêng nên cần nghiệm thu CUDA tương ứng trước đề nghị chạy Modal. Chưa dùng credit Modal trong các lượt hiện hành, chưa có throughput đại diện để ước lượng chi phí full matrix. Số dư30USD vẫn là thông tin người dùng cung cấp, chưa readback tài khoản trong lượt này.

## Trạng thái mới nhất08/11 — chưa cho phép paid/full training

- Linux CPU mainworker đã chạy thật2optimizer updates/48train targets/8validation predictions và checkpoint reload exact; Gate24 đạt771PASS trên source kit lúc đó. [Bằng chứng đã đóng](../../research_tracking/reports/akt_linux_worker_readiness_20261108.md). Đây không CUDA/Modal proof.
- A2/A3 confidence/gate mới đã commit `4a256a4`,43targetedCPUtestsPASS/0optimizer; [source và giới hạn](../../research_tracking/reports/akt_graph_confidence_gate_readiness_20261108.md). **Gate24 cũ không chứng nhận current source sau thay đổi này**; không dùng test số ít để cho full training.
- Tiny T4 lifecycle/recovery v12 bên dưới vẫn là lịch sử hợp lệ cho kit cũ; actual current CUDA mainworker, durable Modal Volume và representative throughput chưa được kiểm. Warm/cold GPU-host preparation mới chỉ có source/mocks/static review, không phải đã tạo GPU runtime hoặc cài trên GPU host.
- Còn phải freeze kit/source/lock và kiểm gate mới; kiểm actual CUDA + recovery/artifact return; đo targets/s và overhead; dự toán toàn experiment matrix theo protocol S04/S05; kiểm persistent storage/account guardrails và xin duyệt **một run cụ thể có trần chi phí**. Graph-aware train/export lifecycle cho A2/A3 vẫn chưa nối, không gọi prototype là CG-AKT đã train.
- **Modal chưa được sử dụng trong batch này.** Giữ user-reported30USDfreecredits, trả thêm0USD; auth thiết lập trước không là quyền chi tiền hoặc bằng chứng số dư hiện tại. Các giá/scenarios dưới là snapshot planning có ngày nguồn, không số giờ training đã đo. Không đưa ra runtime/cost chính xác trước benchmark.

Trạng thái phục hồi authoritative: [INVESTIGATION_STATE](INVESTIGATION_STATE.json), trường `modal_training_readiness_20261108`; backlog hiện93tasks là toàn bộ lịch sử/phần việc, không93tasks còn lại.

Ngày tra cứu bảng giá official Modal: 06/11/2026; các giá/scenarios dưới đây là planning snapshot, chưa là authorization. Cập nhật07/11: đã có actual Colab/T4 CPU portability và bounded CUDA lifecycle/controlled recovery nhận về local, không còn chỉ CPU synthetic. Main Linux runtime-origin/image contract, Modal Volume durability, full training và research acceptance vẫn chưa đạt từ các kiểm nhỏ này. Runtime Windows `artifacts/akt/preflight/runtime-v2.json` với torch2.7.1+cpu/CUDA false là snapshot môi trường khác, không phủ định kết quả Colab.

## Bằng chứng actual Colab và ngân sách hiện hành — 07/11

Nguồn [verification local](../../artifacts/akt/colab/actual-cuda-verification-20261107.json) và [44 outputs gốc](../../experiments/akt/results/colab-actual-cuda-20261107-01/). Kitv12 gồm139files, SHA `ddb35b8eb39906eea6ca6d1ad629d849d398ce4111ee95f3eca64ed9d369155b`; local Windows Gate15 đạt462pass,0fail/error/skip,294,17s. Actual Colab CPU đạt **505pass/2declared exclusions**,0fail/error/skip,117,23s; đây không là cùng acceptance population với Gate15 hoặc main real-data Gate2.

| Kiểm actual trên Tesla T4 | Số liệu đã nhận về và giới hạn |
|---|---|
| CUDA lifecycle | 400synthetic targets/1optimizer step;0,916326s; peak VRAM187.200.000bytes; checkpoint reload/export/causal checks đạt. Không dùng timing rất nhỏ này dự báo full-fold cost/throughput. |
| Controlled fresh-process recovery | 17targets mỗi branch; continuous5steps so interrupted2+resumed3, tổng10updates;28,943933s; target ledger/RNG/sampler exact; maxstate/predictiondelta0 với declared `atol=rtol=1e-5`. Chỉ optimizer-boundary interruption cùng runtime, không hard-kill/preemption hoặc persistent Volume. |
| Artifact transfer | Browser download dispatch chưa là local receipt. Đã nhận tự động qua144MCPchunks, tối đa200.000bytes/chunk; ZIP28.657.701bytes, SHA `64392c70b03162b923740dbe73c0b991a0e7f3f03eea31e6912172db2158f188`; CRC và outputSHA đã kiểm. Heavy artifacts giữ theo output run, không source kit. |

Cả lifecycle và recovery đều **`gate4_pass=false`**; chưa full training, realdata/Holdout hoặc RQ efficacy. Không compute Modal hoặc mua Colab compute units trong lượt này. Ràng buộc user vẫn30USDfree credits/gross ceiling30 và net trả thêm0USD; không tự nâng budget hoặc coi synthetic PASS là quyền chạy ladder lớn hơn. [Modal access audit](../../research_tracking/reports/modal_access_readiness_20261107.md) chỉ xác nhận API auth/workspace, chưa readback balance/spend limits. [Runbook Colab](../akt-colab-synthetic-runbook.md) ghi đầy đủ workloads và hai CPU exclusions.

## Nguồn giá và giới hạn nền tảng

Theo [Modal pricing](https://modal.com/pricing), GPU Functions giá USD/s là T4 .000164, L4 .000222, A10 .000306, L40S .000542, A10040 .000583, A10080 .000694, H100 .001097. Tương ứng USD/h .5904,.7992,1.1016,1.9512,2.0988,2.4984,3.9492. Physical CPU core .0000131/s, GiB RAM .00000222/s. Starter niêm yết30 USD credit/tháng, không đưa credit vào budget guarantee. Volume .09 USD/GiB/tháng với allowance1TiB ghi trên pricing, egress .04 USD/GiB sau included allowance theo plan. Điều kiện account và allowance phải xác minh trước upload. Không trừ credit hai lần khi lập tổng chi phí.

Hiệu chỉnh số học07/11 theo cùng unit rates: với2 physical cores+8GiB, CPU/RAM **.158256 USD/h** (.09432+.063936), rate tổng L4 **.957456 USD/h**, A10 **1.259856**, L40S**2.109456**. Con số.222336 ở bản trước cộng sai, không phải đổi giá hoặc số liệu experiment. Đây là request ví dụ để so sánh, chưa cấu hình đã duyệt; bill theo request/actual usage thực tế và còn startup/idle/storage. Giá training GPU Functions, không áp Sandbox CPU premium. Chọn L4/A10 khởi đầu, L40S chỉ nếu measured cost/target tốt hơn. VRAM187.200.000bytes của400-target synthetic probe chưa là representative benchmark để chọn batch cho training thật.

[Timeouts](https://modal.com/docs/guide/timeouts) ghi mặc định300s, tối đa24h/attempt, timeout mỗi retry reset, user code cần tự deadline vì platform có thể quá vài giây. [Volumes](https://modal.com/docs/guide/volumes) hỗ trợ persistent storage, flush và commit trước exit, không coi temp container là checkpoint durable. Volume v2 recommended trong docs hiện hành, cần fs behavior test riêng. [Budgets](https://modal.com/docs/guide/budgets) phân biệt workspace usage cap trước credits với spend limit net sau credits, có dừng workloads khi reach spend limit. Environment budgets dành Team/Enterprise và chỉ compute. Không thay bằng alert. User/account owner cấu hình workspace cap và net spend limit, local ledger còn cần reserve cho jobs và storage.

## Artifact contract trước mỗi run

Input manifest immutable chứa run_id, experiment_id, environment_id, protocol_id/version, source commit và dirty-source SHA inventory, upstream commit, dependency lock/image digest, CUDA/PyTorch/driver versions, model and graph variant, architecture/hyperparams, exact train/inner/calibration/outer learner hash lists, dataset canonical and split hashes, vocabulary/concept/item mappings, graph direction/hash, edge confidence provenance/calibrator fit IDs, seed/RNG, initialization checkpoint and parent hash, expected fitted/OOV/targets/windows/optimizer updates, budget seconds/USD/RAM/VRAM/steps. Không include secrets hoặc nguyên learner IDs nếu artifact public.

Training outputs model weights, optimizer, scheduler state hoặc explicit null nếu không dùng, Python/NumPy/Torch/CUDA RNG, epoch/global_step, sampler epoch seed cùng buffer/order/cursor hoặc deterministic replay position, data cache fingerprint, consumed target/window IDs checksum, scaler nếu AMP, early-stopper best_loss/best_epoch/stale/history, best và latest checkpoint tách tên, complete/partial flag, logs train/validation loss và count, selection evidence, wall/phase timings, RAM/VRAM peaks, throughput scored targets/s, resource termination reason, hash inventory và completion certificate.

Evaluation outputs Parquet một row mỗi expected target, source_row/event_id, learner privacy-safe ID với salt/version hoặc private mapping, timestamp/tie order, exercise/concept, y,p,fitted/OOV/null reason, fold/split, model/checkpoint hash, history length/effective history, coverage. Summary canonical AUC/LL/Brier/ECE15/accuracy và calibration quanh mastery, CI, paired common-row table, OOV riêng. No finite p ngoài[0,1], duplicate/missing IDs fail artifact gate. Null OOV không metric như fitted. RQ3 thêm graph hash, c values/source, gate values, graph residual influence, off/fixed comparator identity, action traces/ready sets, latent states chỉ evaluation side, net/gross/retained outcomes.

Acceptance không yêu cầu metrics vượt BKT hay graph-free. Cần expected target accounting, no overlap/future labels, checkpoint reload predictions tolerance, all hashes và completed epochs đúng, cancellation/recovery và cost within caps. Failure trước contract completion là incomplete/failed dù exit0. Không xuất partial epoch thành selected model.

Đoạn audit06/11 từng ghi missing mid-epoch sampler/stopper và full CLI resume. REC01–06 sau đó đã có CPU synthetic CLI/selection/refit recovery proof; nay có thêm controlled fresh-process CUDA recovery nhỏ như bảng trên. Vẫn phải nghiệm thu đúng scheduler/scaler contract nếu dùng, Linux runtime/image/phase authorization, durable Volume, graph/gate outputs và complete simulator training/export contract trước research run. Không suy complete pipeline hoặc storage durability từ checkpoint parity trong cùng runtime.

## Ladder và entrypoints

CLI nghiên cứu `python -m knowledge_tracing.akt.cli ... --config ...` và `fold0.json` readiness không tự cấp quyền GPU/real-data execution; smoke/pilot có resource/authorization guards riêng. `synthetic_device_probe.py` và `synthetic_recovery_probe.py` đã chạy bounded CUDA trên Colab, tách khỏi research CLI. Modal commands/ladder bên dưới vẫn là **proposed entrypoint**, không copy chạy như launcher đã được triển khai/nghiệm thu.

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

Khung recovery cho Modal/research còn là đề xuất: checkpoint every5 minutes or500 optimizer steps, whichever first, at optimizer-step boundary. Latest records next unconsumed window, shuffled buffer and RNG. Persist temp→fsync→publish unique immutable name→close→Volume.commit→separate process reload+SHA certificate. Recovery reads only committed certificate. Crash after step before checkpoint allows replay work since latest checkpoint, metrics/sample ledger discarded for uncommitted steps. Exactly-once accepted training ledger from recovered checkpoint, no counting aborted optimizer updates twice. Tolerance1e-6 cho prediction/weights là mục tiêu planning của Modal, chưa được coi đã nghiệm thu; actual Colab probe khai báo `atol=rtol=1e-5` và đo maxdelta0. Không đổi declared tolerance của evidence hoặc extrapolate sang kernel/image khác. Match consumed IDs exactly even if numeric tolerance differs. No scheduler currently, null state explicitly.

Retry limit0 automatic. One manual infrastructure retry per stage after cause and budget recheck, new run attempt ID linked to immutable failed attempt. Resume does not reset total run-dollar/time allowance. On loss of durable checkpoint stop full training until storage fixed. Parent/worker kill must be tested on Modal, no assumption from Windows process result.

## Công thức cost và scenarios

Representative GPU throughput/cost per target vẫn UNKNOWN. Timing0,916326s của1synthetic update và CPU pilot32batches/7.346targets không chuyển thành CUDA full-fold forecast. Let Ntr,Nval,Nout actual targets from accepted preflight, rtr,rval targets/s incl padding/data overhead, Es epochs selection, Er refit. Per outer fold seconds = startup+load + Es*(.9Ntr/rtr+.1Ntr/rval) + Er*Ntr/rtr + Nout/rval + checkpoint+export. Không double-count val mỗi selection epoch. Actual support/OOV lấy manifest. 5 folds là tổng từng fold, không luôn5×fold0.

Để kiểm độ nhạy, dùng report Dev total D=20.706.208, approximate Ntr=.8D,Nout=.2D. Nếu Es=Er=E, rtr=rval=r và overhead chưa tính, work/fold≈(2E*.8+.2)D, work5fold≈(8E+1)D. Đây là phép tính target-equivalent, chưa đo runtime. Inner validation .1 training được tính trong E*.8D. Training4 models Junyi xấp xỉ4 lần nếu equal E/r, cộng ablations/SAKT/GKT và simulator, không báo một AKT là toàn nghiên cứu.

| Scenario giả định để stress-test | E, r giả định | AKT Dev5fold GPU giờ / L4 compute USD |4 variants Dev5fold | Ý nghĩa |
|---|---|---|---|---|
|Optimistic |E3,r20k |7.19h /6.88USD |28.76h /27.54USD |Chưa measurement |
|Expected planning |E10,r5k |Work=81D, giờ93.18, USD89.21 |372.7h,356.86USD |Chưa measurement |
|Conservative |E20,r1k |Work=161D, giờ926.03, USD886.63 |3704h,3546.52USD |Một GPU vượt thời gian thực nghiệm |

Kiểm tra số học sau hiệu chỉnh rate. Optimistic work25D/r20k =25.883s≈7.19h,6.88USD, 4variants28.76h,27.54USD. Expected81D/r5k=335.441s≈93.18h. Conservative161D/r1k=3.333.699s≈926.03h. Dấu chấm trong số giây ở đây phân tách nghìn. Các throughput giả định chỉ là axes sensitivity, không dự báo AKT. Es/Er có thể khác, phải thay bằng history pilot. Overhead10/25/50% là reserve scenario, không measured overhead.

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

## Chi phí inference sau interface07/11

Training GPU không là toàn bộ compute matrix. Reference bank3items×28concepts cần84counterfactual queries mỗi lần đo đầy đủ. Workload inference xấp xỉ learner×steps×conditions×seeds×reference_queries, cộng action queries chưa reuse trong cùng revision. Stage5 phải benchmark query throughput và controller/serialization overhead, tách train/validation/export. SIM05 giữ training batchcap, gom independent windows; fixture d16CPU84queries giảm84→42native calls,0.815→0.393s, không ngoại suy GPU. Không nối candidates thành fake history hoặc cache qua observe để tiết kiệm; global AKT history có thể đổi mọi concept scores. S04 reference-bank choice và numerical threshold convention ảnh hưởng cả scientific estimand lẫn cost, phải freeze trước train/evaluate.

## Readiness engineering cập nhật07/11 — không thay bảng giá snapshot06/11

Các mục missing của audit đầu đã được cập nhật theo scope: REC01–06 có CPU synthetic sampler/model/Adam/RNG/CLI selection/refit proof, archive `cpu-akt-recovery-20261107-01`; v12 nay có actual Colab/Linux portable CPU và controlled CUDA lifecycle/recovery. Main Linux runtime-origin/image contract và Modal Volume durability vẫn chưa được chứng minh. DATA05/06 có collector train-only fixture và simulator role-aware windows/collation, không là complete simulated training runner hoặc full research corpus. [Report collector](../../research_tracking/reports/simulator_collection_runner_20261107.md) ghi scope và trials.

Ba chốt còn phải giữ trước main research worker/Modal, dù bounded Colab lifecycle đã đạt:

1. `requirements-akt.lock.txt` chứa Windows cp313 wheels và CPU Torch. Không dùng nó để install Linux/CUDA image. Cần lock/image digest riêng theo runtime thật trong project environment; không sửa dependency global hoặc thay file lock lịch sử để làm hash trông hợp lệ.
2. `scripts/akt/check_runtime.py::inspect_runtime` yêu cầu Torch/NumPy origin bên trong project venv. Colab notebook dùng `--system-site-packages` để tận dụng Torch sẵn có: hai chế độ này có contract khác nhau. Không lấy Colab probe thay cho main pipeline runtime authorization; cần explicit remote-runtime contract và provenance trước real-data worker. Không nới origin check âm thầm.
3. Portable bundle strip notebook outputs/metadata: full notebook storage SHA khác dù source equations giống nhau. Collectorv2 đã tách semantic definitions/constants/input/clock khỏi storage integrity và giữ parity fixtures; vẫn phải kiểm đúng version/domain khi handoff. Không tự sửa domain cũ trong historical checkpoints/bundles hoặc coi việc ZIP source parity là complete trainer/checkpoint acceptance.

`synthetic_device_probe.py --device cuda --output-dir <new>` đã đạt bounded400targets/1step trên Colab; lifecycle report riêng giữ `mid_epoch_resume_verified=false`. `synthetic_recovery_probe.py` riêng đã đạt controlled fresh-process CUDA resume17targets/branch,5vs2+3steps. Cả hai vẫn `gate4_pass=false`; chưa real-data/full training, hard-kill hoặc Volume. Lượt cập nhật tài liệu này chỉ đọc evidence, không chạy lại probes/provision hoặc tiêu credits.

## Ràng buộc user mới07/11:30USD/tháng

User xác nhận Modal30USD **free credits only**, net trả thêm0USD; workspacehonguyenminhsang2005. Các envelope150/300/600USD phía trên là proposal cũ, **không được dùng thay hạn mức30USD hiện tại**. Không tự cộngcredits hoặc giả có60USDthángsau. Colab synthetic proof không tiêu Modal credits hoặc cấp quyền exact paidrun.

LocalSDK1.6.3 đã cài bằng pinned supplemental wheel lock trongprojectvenv, không đổi30existingversions/AKTlock. Sau setup/version/help/pipcheck đã có [API auth/workspace audit chỉ đọc](../../research_tracking/reports/modal_access_readiness_20261107.md), chưa compute/image/Volume hoặc balance/spend-limit APIreadback. Handoff, dashboardusage/netspendcap và ngân sáchđềxuất2+3+20+5USD ở [akt-modal-setup](../akt-modal-setup.md). Cost/target vẫnUNKNOWN; không hứa fullCV hoặc complete matrix vừa30USD. Lưu costplan arithmetic correction07/11:2CPU+8GiB=.158256USD/h,L4combined=.957456USD/h trước overhead/actual usage; actual price/account access kiểm trước mỗilaunch.

Cập nhật câu trả lời user07/11: còn30USDfree credits,bắt đầu07/11/2026/reset tháng kế,không trả thêm tiền; grossceiling30USD/net0USD là binding. API xác nhận auth/workspace riêng; balance/cycle do user báo, chưa readback balance/spendlimits. Reset day/time cụ thể chưa biết, không suy ngày07/12 hoặc tự cộng30USDthángsau. Thông tin “chưa biết loạicredits/workspace” trong hồ sơ cũ là snapshot trước câu trả lời này. Cácstageallocations vẫnproposed, không là permissionlaunch.

## Cập nhật nguồn09/11 — CG-AKT chưa sẵn đường chạy GPU nghiên cứu

Đã lưu [rà soát device/checkpoint/launcher](evidence/cgakt_gpu_device_source_review_20261109.md) cùng inventory đối chiếu trước/sau sao chép. Đây là kiểm nguồn; các SHA mô tả snapshot lúc review, không chứng nhận runtime hiện tại hoặc thay kiểm CUDA. TASKS/index đã được cập nhật sau snapshot đó.

Đường chạy CG-AKT nghiên cứu hiện còn khóa CPU ở guard, model, training context và checkpoint. Probe CUDA tổng quát đã đạt trước đây không chứng minh đường chạy này dùng được GPU. Public full-fold entry vẫn bị khóa; chưa có Modal training app/launcher hoàn chỉnh. Không gọi private helper để vượt khóa hoặc đổi riêng tên device thành cuda.

Thứ tự cần làm tiếp: nghiệm thu selected-only lifecycle CPU → port device/runtime guard, tensor placement, CPU+CUDA RNG và Adam state đúng semantics → finite CUDA forward/backward/update → save/reload/fresh-process recovery → benchmark có đồng bộ CUDA → image/Volume/budget Modal và lượt chạy được duyệt riêng. Không blanket chuyển mọi tensor Adam sang GPU; step scalar và moment buffers có quy tắc khác nhau theo backend/config.

Kiểm CPU fresh-process ngày09/11 đã khớp full epoch tiếp theo nhưng chưa chứng minh CUDA/cross-host, global-budget resume hoặc sampler giữa epoch. Trạng thái GPU nghiên cứu vẫn **CHƯA SẴN SÀNG**. Chưa có throughput GPU cho pipeline này nên chưa thể chốt giá một fold; tiếp tục dùng công thức theo scored-target throughput đã đo trong stage5, không suy runtime từ CPU fixtures hoặc số testPASS. Giữ30USD free credits/net0 và không tự phát sinh chi phí.

## Ưu tiên Colab trước Modal theo user07/11

Thứ tự hiện tại: localCPU → Colabfree cho CUDA smoke/checkpoint reload và các kiểm CUDA tổng quát đã chuẩn bị → Modal cho revalidation đặc thù image/Volume cùng pilot/training có kế hoạch. Không tiêu credits Modal chỉ để chạy lại các kiểm CUDA có thể làm trên Colab trước. Budgetreadiness2USD cũ chỉ là reserve cho platform-specific revalidation nếu cần, không autoallocation. Balance30free/net0 giữ nguyên. Colabunavailable/hếtquota không tự cấp quyền fallback sang paidcompute.

Notebook/kitv12 hiện có actual400synthetic targets/1step và controlled fresh-process CUDA resume, với44outputs đã nhận/kiểm như đầu tài liệu; vẫn chưa fullDev/Gate4 hoặc hard-kill/Volume. CPU notebook timeout600s/JUnit/nonempty/noerrors/noskips và GPUsource/gate guards giữ workload bounded, không tự mở rộng sau PASS. Runtime availability Colab không có bảo đảm cố định4giờ; nhận và kiểm artifacts trước giải phóng runtime. [FAQ chính thức](https://research.google.com/colaboratory/faq.html). Modal vẫn cần test Linux image/runtime-origin/Volume riêng ở giới hạn nhỏ; không tự chuyển sang Modal khi Colab thiếuquota hoặc coi Colab proof thay authorization đó.
