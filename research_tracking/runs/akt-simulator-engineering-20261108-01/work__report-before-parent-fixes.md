# Lifecycle AKT simulator engineering-only — 08/11/2026

Đã triển khai helper độc lập cho **một complete epoch train/selection trên observable toy khai báo thủ công**, checkpoint reload và kiểm coverage. Final targeted suite: **36pass,0fail/error/skip,17,40s**; wrapper19,9176115s, timeout90s. Đây là nghiệm thu plumbing kỹ thuật trước S04/S05, **không complete simulator research trainer, selected scientific model hoặc kết quả RQ3**.

## Source/API và giới hạn đã áp dụng

Chỉ thêm `src/knowledge_tracing/akt/simulator_engineering.py`, `tests/akt/test_simulator_engineering.py` và báo cáo này. Không sửa các module khác, CLI, native/upstream, config/main runner, source paper, index/state hay Git. Thêm native source/test làm Gate18 cũ stale; parent review rồi refresh Gate19 riêng. Không chạy full gate ở đây.

API chính:

```python
run_engineering_epoch(config: AKTConfig, *,
    train: SimulatorShard, selection: SimulatorShard,
    budget: SyntheticEngineeringBudget) -> EngineeringEpochResult
```

`SyntheticEngineeringBudget` bắt buộc `approved=True`, `approval_reference`, expected train/selection SHA; hard caps ≤2train learners,1selection learner,12events/learner,4optimizersteps,1epoch,60giây,2GiB process RSS và floor1GiB available RAM. Config phải `execution_enabled is True`, CPU `smoke`, existing d32/head4/block1/d_ff64/final_fc32/context100/target_block100 geometry và không recovery. Config caps phải nằm trong explicit engineering budget. Thêm giới hạn toy item bank36items, threads≤2, seed phù hợp NumPy; không là hyperparameter research được chọn. Fixture dùng nguyên smoke recipe hiện có, dropout0/seed42/batch2, không đổi model defaults.

Output chỉ direct fresh `artifacts/akt/synthetic/<run-id>/` hoặc `experiments/akt/results/<run-id>/`, không overwrite, nested/ngoài scope/device-name/symlink/junction output bị chặn. Domain phải mang prefix `synthetic-akt-engineering-`, collection policy `handcrafted-observable-fixture-v1`; chỉ exact observable schemas, đúng roles/plan/bank và input hashes. Origin/approval markers là khai báo in-process của caller, không chứng thực mật mã rằng dữ liệu thực sự được gõ tay. Authorization hiện tại chỉ cho toy này, không mở rộng sang collector/research corpus hoặc dữ liệu thật.

Không tạo `LearnerEvents`, `KTEvent`, `InnerSplit` hoặc fake Junyi fold. `outer_fold`, `inner_val_fraction`, `patience`, `min_delta` vẫn hiện trong snapshot cấu hình legacy nhưng được ghi **unused_legacy_fields**, không dùng để chia roles/chọn epoch. Không gọi `select_checkpoint`, `evaluate_inner`, refit, calibration/final hoặc production prediction exporter.

## Primitives tái dùng và hợp đồng đầu ra

1. `fit_simulator_encoding(train)` tạo vocabulary/support train-only; `iter_simulator_windows` giữ actual AKT geometry/OOV barriers và labels ở `TrainingWindow` riêng. Ledger train chứa learner/source_row/global_rank, không lặp/thiếu target.
2. Native `AKTAdapter`, Adam theo config, `training.train_epoch` với recoveryNone và budget thật. Chỉ complete epoch + exact optimized target count + parameter update mới đi tiếp; partial epoch không publish checkpoint.
3. Selection dùng prediction windows **không targets** qua `predict_windows`; `scoring_targets` đọc riêng, join learner/source_row/global_rank. Chỉ chấm target mask; OOV giữ None/reason riêng. Prediction/eval kiểm weights checksum và observable input identity không đổi; có deadline/RSS/available-RAM checks quanh inference. Engineering log loss chỉ là diagnostic arithmetic, không benchmark/fitted efficacy.
4. Reuse atomic `save_checkpoint` và `restore_checkpoint`. Own loader đọc một payload bounded8MiB, hash chính bytes được `torch.load(BytesIO(...),weights_only=True,map_location='cpu')` deserialize; kiểm identity/completeepoch/role/config inference recipe/encoding và selected module source hashes. Serialized byte cap không là chứng nhận peak allocation với checkpoint không tin cậy; helper chỉ dùng checkpoint toy do chính run tạo, không mở untrusted-file service.
5. Identity có `purpose=simulator_engineering_only_v1`, `weight_role=engineering_only`, engineering bank/plan/train/selection/encoding/recipe/budget/source/upstream hashes. **Không cấp `training_domain` certificate**, không trả `OnlineScore(kind='fitted')`. Production `load_online_akt` được test từ chối checkpoint toy. Complete engineering epoch không trở thành selected research model chỉ vì weights đã thay đổi.
6. Reload lại checkpoint, đối chiếu parameter hashes, coverage và probabilities trong tolerance1e−7. Failure giữ `failure.json`, traceback `failure.log` và stats đã có; không che partial run bằng success result. Source/input drift trước completion bị từ chối. Hash inventory trong invocation ghi đúng subset module được kiểm, không tự là full Gate/build attestation.

## Kiểm thực tế, output và failure proof

Không gọi collector/simulator environment, không query real dataset/Holdout, không GPU/cloud hoặc cài packages. Toy bankA/B/Z, train2learners×ABAB = **8targets**; selection1learner×AZBA = **4targets:3known,1OOV**. Observables được tạo trực tiếp trong test, không dùng latent ability/oracle/true-edge inputs. Split-plan seed families chỉ cấp identity cho fixture, chưa chứng minh independent scientific samples.

| Lượt | Kết quả | Optimizer steps thực tế |
|---|---|---:|
| trial01 | 33pass/16,44s; controller18,9093408s | happy1 + partial1 =2 |
| trial02 final | 36pass/17,40s; controller19,9176115s | happy1 + partial1 =2 |

Tổng hai invocations **4steps**, mỗi suite2steps, dưới hạn16; không failed pytest invocation. Giữ source-before/log/JUnit/receipts của cả hai lượt. Trial02 thêm threads/seed/device-path negatives và siết source binding loader/giữ original failure khi inventory không đọc được; không đổi native model/method.

Final actual outputs:

- `artifacts/akt/synthetic/simeng-20261108-complete-53aff99f/`: một optimizer update thật,8optimized targets; selection known/unseen đúng; reload max absolute delta **0**. `epoch1.pt` SHA `37756d5d01a67b7670aeba3b9b3d6a98b473b67d54c3ddff40fe618b7572ceb2`; checkpoint giữ tại run, không đưa .pt vào bundle/Git.
- `artifacts/akt/synthetic/simeng-20261108-partial-57a1a715/`: intentional maxstep1 với batch1 chỉ tối ưu4/8targets; `IncompleteEngineeringEpoch` được giữ trong failure JSON/log. **Không epoch1.pt/result.json**; đây là positive failure-path proof, không lỗi test bị bỏ qua.
- Trial01 historical outputs: complete `simeng-20261108-complete-0aae5289`, partial `simeng-20261108-partial-7f450361`; exact paths và mọi output SHA được giữ trong trial01 receipt. Không gán final source hash cho trial01.

Kiểm nguồn upstream là **real** pinned checkout/commit/tree/remote/license/content qua `verify_upstream`, kể cả native construction. CPU/RAM là real `memory_snapshot`, không mock trong actual happy/partial lifecycles. Runtime report final ghi torch2.7.1+cpu; process peak337.453.056bytes, available RAM5.975.830.528bytes tại sample cuối happy run, dưới caps. Đây là measurement của fixture process, không extrapolate full corpus. Không gọi unmocked full runner/runtime-origin/lock/Gate preflight; không tuyên bố full worker/CUDA readiness.

Deadline60giây và RSS guard trong helper là kiểm cooperative trước/sau primitives; không là OS hard-kill/memory isolation trong một native call đang chạy. Outer targeted subprocess có timeout90giây. Không publish complete result nếu deadline đã hết ở guard cuối; actual invocations đều dưới20giây. Đây không thay watchdog contract hoặc đo durability của process interruption.

Negative tests dùng spy `AKTAdapter` để chứng minh invalid scope bị từ chối trước native construction, và inject memory snapshots chỉ để kiểm nhánh RSS/floor; không nới source/runtime authorization. Cases bao gồm approval/execution/budget, CPU/source, roles/calibration/final/refit, input/plan/domain/policy, learner/events caps, output scope/no-overwrite, invalid checkpoint SHA/encoding/source binding và oracle payload rejection. Existing causal-window/model tests không được rerun trong lượt này; chỉ suite mới có log xác nhận.

## Bằng chứng và freeze

Thư mục evidence làm việc: `artifacts/akt/local-tests/parallel-simulator-engineering-20261108-01/`, gồm `run_targeted.py`, `run_targeted02.py`, source-before-trial01/02, pytest logs/XML và receipts chứa source/dependency/output SHA. Wrapper dùng project .venv, `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=''`, cache tắt/temp riêng, exact **process-only** Git safe.directory cho pinned upstream; không config Git global/repository hoặc wildcard. Source trước/sau mỗi run và9existing dependency files khớp.

Source final:

| File | SHA-256 |
|---|---|
| `src/knowledge_tracing/akt/simulator_engineering.py` | 5ae344b34bfecc8d7e574d33fac67f941a4df5a8d3bf7c3d817b8017e25b07d9 |
| `tests/akt/test_simulator_engineering.py` | 795498ef5726cf054098079b04ba3bfe0310babd34d4d31c033ec1302ecc8feb |

Lệnh final: `.\.venv\Scripts\python.exe artifacts/akt/local-tests/parallel-simulator-engineering-20261108-01/run_targeted02.py`. Wrapper tạo receipts/run dirs độc quyền; tái chạy cần wrapper/run/test-output names mới, không ghi đè evidence. Parent review/archive/commit và Gate19 sau freeze; không cập nhật chỉ mục ở tiểu tác vụ này.

S04/S05 vẫn pending: corpus mixture/coverage/allocation, train/selection/calibration/refit/final exposure, scientific epoch selection, reference/mastery/threshold/controller, learned graph/confidence, CG variants và modern comparator results. Helper này chỉ chứng minh mechanical train→selection→complete checkpoint→reload/coverage có thể làm bằng typed toy roles trước khi adopt các quyết định đó.
