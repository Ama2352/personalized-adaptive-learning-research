# AKT research data BATCH1: nối roles vào causal windows

Đã thêm [research_simulator_data.py](../../src/knowledge_tracing/akt/research_simulator_data.py) và [tests](../../tests/akt/test_research_simulator_data.py) để nối RESDATA01 vào geometry AKT hiện có theo [protocol21](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md). **25kiểm tra thuần NumPy đạt,0model/optimizer calls**; chưa có research trainer, generated corpus, checkpoint fitted hoặc execution authority.

## Bốn scopes, không giả fold

`ResearchAKTShard` reuse actual `audit_research_shard` và original observable schemas, kiểm complete requested role/provenance/plan/bank/clock/support với caller limits. Final events bị từ chối trước iteration. `prepare_research_phase` chỉ nhận đúng inputs cho từng scope:

| Scope | Dữ liệu | Vocabulary/lineage |
|---|---|---|
| `select_train80` |train role |Fit encoding80 chỉ từ train learners |
| `raw_selection10` |selection role |Chỉ dự đoán bằng encoding80, từ chối encoding refit |
| `refit_union90` |train+selection giữ origin roles |Reuse prepare_refit_view với matching raw SelectionFreeze; fit encoding90 mới |
| `calibration_predict` |calibration role |Chỉ dự đoán bằng encoding90 có cùng SelectionFreeze lineage |

Không relabel calibration thành selection/train; không tạo LearnerEvents.fold hoặc gọi native fullfold. Encoding ghim optimization scope/phase, origin shard hashes, plan/domain/freeze, support và source identity. Support là **unique learner count/item**; selection item có thể xuất hiện trong refit vocabulary, calibration item không được rescue. Field `trained_item` của truth sidecar chỉ nghĩa item có trong vocabulary của optimization split; không chứng minh model đã được train.

`iter_research_windows` compose nguyên `iter_window_slices/slice_causal_inputs`, CausalSequenceInputs, encode_exercises và TrainingWindow. Prediction xuất typed OOV target với learner/query/globalrank, không embed−1. Suffix known giữ original OOV barrier/reset/global anchors. Model inputs không chứa unshifted current labels; labels của optimization nằm trong TrainingWindow, truth sidecar xuất riêng bằng `research_scoring_targets`.

## Full targets và danh tính lịch sử

Mọi real event còn trong full truth sidecar, gồm learner/query(item,timestamp,source_row)/globalrank/originrole/scope/phase/encoding/support/history identity. Không drop unknown target khỏi denominator. Fixture raw selection có5targets=3known+2OOV, globalranks0..4; điều này là kiểm coverage, không fitted prediction.

History scheme ghi rõ `observable-prefix-chain-v1` trong phase manifest, encoding và target. Genesis gắn bankdomain+learner; mỗi bước hash previouschain+previousobservable. Current response chỉ thay chain sau currentrow. Cùng observablepast giữa models/vocabularies/scopes có cùng chain. **Không ghép chain này như thể OnlineSession.history_sha256**, vì session hash có model binding và công thức khác; downstream joins phải kiểm cả hash scheme. Wholephase/corpus hashes có thể đổi khi sửa futurelabels, còn causality test so đúng currentinput/pastprefix.

Phase/encoding kiểm source/input seals tại iterator boundaries trước/sau, không fullaudit mỗi window. Một số nested identity getters vẫn lặp audit trong preprocessing; chưa đo research workload. Trainer sau có thể cache verified preprocessing theo exact hashes và kiểm boundary, không bỏ source/target guards. Không sửa native/shared/config/authorization hoặc old engineering caps trong batch này.

## Kiểm chứng thực tế

| Lượt | Kết quả không sửa lịch sử | Controllerelapsed | Source |
|---|---:|---:|---|
| pure01 |24PASS/1FAIL/0error/skip |1,780566200031899s |Test nối tuple+list gây TypeError sau assertion crossencoding prefixparity đã qua |
| pure02 |25PASS/0failure/error/skip |1,739560604095459s |Chỉ sửa test right thành tuple; production source không đổi |

Cumulative3,520126804127358/30s. Console02 `25passed in1.30s`; JUnit02 suite1,304s. Không cộng24+25 thành49independent tests và không gọi timing này training throughput. `.venv`, CUDAhidden, thread2, pytest plugin autoload tắt; actual per-test importcanaries và `torch not in sys.modules` trước/sau đều qua. Không optimizer/model/environment/data/GPU/remote/Git execution.

Controls gồm: exactlegacy train-window parity ở cả train/prediction; full OOV population/globalrank/reset; e80/e90 và freeze lineage; wrongrole/calibration optimization/finalcanary/source drift/encoding drift/type negatives; currentlabelperturbation giữ currentinput/prefix và đổi nextprefix; crossmodelprefix bất biến qua encoding/scope. Cả hai trial giữ13inputSHA trước=sau và26physical source snapshots/trial.

[Raw trial01](../runs/akt-research-data-engineering-20261108-01/trial01__receipt.json), [raw trial02](../runs/akt-research-data-engineering-20261108-01/trial02__receipt.json), [JUnit02](../runs/akt-research-data-engineering-20261108-01/trial02__junit.xml) và [copy inventory](../runs/akt-research-data-engineering-20261108-01/copy_inventory.json) được lưu byte-exact, có alias cho snapshots trùngSHA để tránh nhân bản. ModuleSHA `9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b`; finaltestSHA `bee16620e1bdc2c98dd66e65b2ddddd82160098582b83b53a34120b50fb3645b`. Parent review qua source/messages xác nhận data-only scope, không phải independent agent/model execution acceptance.

## Ranh giới trước BATCH2

**Fixture dùng protocolSHA giả `a…a` một cách có chủ đích**, vì đây là kiểm metadata/geometry, không source-execution authority. Bank đủ84items/28concept nhưng train fixture chỉ observed2items để kiểm OOV, không đạt full-reference support cho research trajectories. Không coi positive oracle-access flag/hash declarations là bằng chứng generator thật đã đúng; provenance vẫn hợp đồng nhất quán hợp tác, không chống caller giả metadata đồng bộ.

Actual runner bắt buộc kiểm docs21 **bytes SHA và protocol ID hiện hành**, actual role manifest/collection sources, **G_env/collection recipe đồng nhất crossroles**, learner/seed-family separation và full support/resource policy trước model allocation. BATCH1 kiểm từng role và plan/bank/freeze, **chưa tự thực thi toàn bộ cross-role G_env/recipe/execution policy**. Không đổi old engineering guards để tránh các checks này.

BATCH2 chưa triển khai: explicit simulator-research phase/config/authorization, frozen hyperparameters, complete epoch/selected raw checkpoint, fresh refit90 optimizer/vocabulary, calibration prediction/export, actual fitted checkpoint/domain attestation và frozen online loader. Không mượn phasepreflight/fold hoặc nới d32smoke. Newsource chưa có fresh kit/Gate coverage; parent xử lý source freeze/Gate/commit. Batch này không chứng minh calibrated research model, full baseline hoặc RQ completion.
