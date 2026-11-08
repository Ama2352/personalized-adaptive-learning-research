# GKT epoch pipeline engineering: train→selection→export — 08/11/2026

**38 pure tests và một actual hai-epoch toy run đạt acceptance;2 optimizer body returns, chưa fitted baseline nghiên cứu.** Mỗi epoch xử lý đủ6 eligible train targets của cùng2learners; selection giữ4original rows,2scored+2unsupported/0research_fitted. Epoch2 được chọn bởi policy caller khai báo trong fixture, không acceptance condition bắt metric phải cải thiện. Không realdata/Holdout, corpus/generator, GPU/cloud, install/network hoặc old88/45/40/32-case rerun.

## Phần mềm và ranh giới roles

Chỉ thêm [training_data.py](../../src/knowledge_tracing/gkt/training_data.py), [pipeline.py](../../src/knowledge_tracing/gkt/pipeline.py), [test_pipeline.py](../../tests/gkt/test_pipeline.py). GKT03/04/05, recurrent/core/config/exports, shared và AKT giữ nguyên trong tiểu tác vụ. Root đã review toàn source/command/pure38 trước khi cho phép **một** model01 phase. [Pre-update freeze](../../artifacts/akt/local-tests/gkt06-pipeline-preparation-20261108-01/pre_update_freeze.json) giữ exact source/helper pins và command contract.

`GKTObservableShard` reuse `ObservableTrajectory`, `SimulatorSplitPlan`, `validate_role_shard` thật; chỉ intake train/selection và learner/source-row-disjoint, không giả Junyi folds. Input là observables item/time/source/correct, không latent/profile/oracle features. Role plan có assignments calibration/final nhưng không đọc/generate observations của hai roles đó. Train-only item vocabulary và learner support được derive từ train; selection không mở rộng vocabulary/map/support.

Ordered node registry/unit/graph và item→node registry do caller cấp explicit. Node vocabulary SHA tách với train item vocabulary SHA; mọi train item phải map đúng1boundnode, reject missing/multi-tag/foreign/concept mismatch trước optimization. Registry có thể chứa static bank item chưa quan sát ở train, nhưng training projection chỉ gồm train-observed items. Vì vậy selection item `c` vẫn OOV dù nodeC tồn tại trong static graph. Graph provenance là caller-declared static; không graph learner hoặc data-trained semantics certificate.

`run_gkt_epochs` reuse nguyên GKT03 step trên whole-learner batches, fresh zero state bind current parameter digest; full BPTT trong accepted sequence, local seeded learner order, không shuffle events/chunk/reset để vượt cap. Real target mask tách computational-valid prefix; cold-excluded event vẫn là real observation. V1 từ chối input có learner không có loss target thay vì silent filtering. Step objective là explicit mean BCE trên eligible mask.

Selection dùng `torch.inference_mode` và native sequence logits để tính stable sum BCE/n, không log/clip adapter probabilities và không freeze live training model. Cùng population fingerprints cho mọi epoch; all expected rows vẫn có probability hoặc None/reason. Native recurrence dự đoán trước observe response_t; CSV correct label được ghép sau prediction capture, không validation gradient/optimizer. Caller module flags và Torch CPU RNG được actual driver kiểm giữ nguyên; owned budget/event hooks được gỡ trước successful publication.

Epoch complete chỉ sau đủ unique train eligible rows và complete selection audit. Caller cung cấp epoch/batch/order/selection/min_delta/tie/budgets không default research recipe. Fixture:2epochs/B2/seed42, min_selection_mean_bce/min_delta0/tie-earliest. Pure selector có equal/worse/min_delta/incomplete/population-change cases, không ép positive benefit. GKT04 weights-only checkpoint giữ format/role cũ; new run manifest liên kết checkpoint SHA với actual batch source rows/mapped node IDs/encoding/map hashes và selected CSV. **Chứng minh mapping khai báo đã thực dùng**, không chứng minh mapping ngữ nghĩa đúng. GKT05 vẫn ghi `caller_declared_inference_mapping_NOT_training_attested`; không đổi claim cũ bằng metadata mới.

General API chỉ biết initial parameter/optimizer hashes và `caller_owned_initial_parameters_NOT_fit_attested`. Actual fixture dựng fresh model trong CPU/fork_rng/seed42 nhưng không tạo fitted-initialization certificate hoặc scientific warm-start policy. Output role `synthetic_selected_engineering_only`; checkpoints vẫn không lưu optimizer/RNG/hidden state, không resume/research-fitted/OnlineSession promotion.

## Hai phases thực tế

| Phase | Kết quả | Compute/evidence |
|---|---|---|
| Pure01 |**38PASS/0fail/error/skip**,0neural constructors/optimizer calls qua forbidden guards | Pytest8,27s/controller10,778306s; data/roles/map/vocab/masks/selector/CSV-format tests portable, không untracked model dependency |
| Model01 |**2complete epochs,2step reservations,2Adam body returns/posthooks,2complete GKT batches** | Controller17,475941s≤remaining46s, native44s; exact owned-process escalation chỉ cho existing GKT04 hard-link publication.2plannedsteps/hardtotal4; không fallback overwrite |

Cumulative conservative **31,254267/60s**, lấy max monotonic/wall mỗi controller cộng3s static reserve.0retry/actual failures trong batch; không dựng RED hoặc failure case đã chạy nếu chỉ là source reasoning. Official Adam pre/post hooks ghi/fsync step-started trước body và step-returned sau body; reservation không tự được tính là successful body/batch. Trong run này cả ba tầng đều2; max optimizer parameter step2 và parameter delta hiện diện. Exception/partial-update bookkeeping là thiết kế giữ evidence, **chưa actual fault-injection/recovery proof**; không hứa rollback.

| Epoch | Unique train optimized targets | Selection population | Checkpoint manifest SHA |
|---|---|---|---|
|1|6 (`1,2,3,11,12,13`)|4expected=2scored+2unsupported/0research_fitted|`2f9d7451b1db041647977845fa778e5238219e0bcd3174084be8264d1e42d082`|
|2 (selected)|Cùng6rows, thêm1update của epoch2; không independent samples|Cùng4rows/eligibility fingerprints|`4a4234d1f70384231b30bd4184960961d0f90b8730e34f037c11162f91a34c9d`|

Selected CSV có đủ source rows101–104/global ranks0–3: `cold_query_only`, `known_history`, `oov_item`, `unsupported_history`. Unknown/history-blocked rows không bị xóa hoặc chấm finite0; history_available vẫn0–3, history_used=0/1/0/0. Header giữ learner/source/item/node/time/rank/role/correct/probability/logit/support/history/context/score_kind/weight_role/research_fitted/checkpointSHA. Chọn epoch2 chỉ là kết quả fixture theo criterion đã khai báo, không efficacy/RQ finding.

Selected checkpoint được load qua **public GKT05 strict loader**, rồi parity với complete exported selection population, không freeze hoặc thay caller live weights. `selected_predictions.csv` byte-exact với epoch2CSV, SHA `87fc639fed1c94f5cac8ad1e6d182e2d57d44d669f60599f28b38aa0b50b8f54`. `run.json` candidate metadata được bind bởi root COMPLETE marker; `failure.json` hoặc external resource rejection phải override marker, không lấy marker một mình làm accepted lifecycle. Deadline kiểm lại sau publication; actual controller postelapsed đã trong cap.

## Frozen provenance và giới hạn

| Source/evidence | SHA-256 |
|---|---|
|Training data|`db5a9c41d29eaf5ccb834965cfe1e7952a3b9dfe2a4dca573d91791909403339`|
|Pipeline|`59c256fbcde715934041f911fb3ad5a6b6ae9bd63d2304cacd3ae4d0c4e235ec`|
|Pure tests|`465b371aa0064c2f83d755716ce31c5621ad982cf0365b97eb31272a9d10e651`|
|Actual model result|`44f6427ccc2f0a88f0fd7903dc45a58edd01135dc6c6ad31414df72836f8111b`|
|Run manifest|`42636a5862e9215073d47a2d3fc31eae311c8027ec71d9bbac0f74c266d83435`|
|Frozen acceptance|`9f99136cfe1ba4cd6bf9cdedb177ce15b70c7fc0e23939e646cb5451600cf3e7`|

[Acceptance/inventory](../../artifacts/akt/local-tests/gkt06-pipeline-preparation-20261108-01/acceptance.json) và [parent raw review](../../artifacts/akt/local-tests/gkt06-pipeline-preparation-20261108-01/parent-review.json) đối chiếu38XML/52source snapshots/current13SHA, events, both epochs/CSV, checkpoint markers/binary SHA và mapping-use. Root không rerun/load/train trong review. Đây là parent actual review, không dựng independent-agent PASS. [Bundle dự kiến](../runs/gkt-epoch-pipeline-engineering-20261108-01/README.md) giữ mọi selectedCSV/epochCSV/metadata/manifest/events và binary SHA references; `.pt` giữ tại output artifact gốc. Archive chỉ copy/hash, không sửa old bundle hoặc rerun model.

Đây là bounded engineering lifecycle, **chưa corpus trainer scientific-ready/final GKT baseline**. Hard caps B2/N4/T12/width8, bank8, steps/targets/time và checkpoint1MiB là engineering limits; không đổi bằng chunk/reset hoặc coi chúng là nghiên cứu defaults. Chưa authorization realdata, selected-refit/calibration/final, learned graph/multi-tag/node→item scientific decoder, journal recurrence parity, information/capacity matching hoặc S04/S05 allocation/optimizer/seeds/selection adoption. Static caller mapping usage không chứng nhận causal prerequisites; correctness logits/node probabilities không là calibrated mastery. Không suy benefits/RQ completion từ38tests,2epochs hoặc2scored selection rows.
