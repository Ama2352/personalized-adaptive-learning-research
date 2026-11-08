# AKT research data BATCH1 — scope/encoding/windows, chưa trainer

Thêm hai file được root giao: `src/knowledge_tracing/akt/research_simulator_data.py` và `tests/akt/test_research_simulator_data.py`. Không sửa old engineering guards, native model/upstream, config/authorization, dataset/collector hoặc source đã đóng. Đây là nối RESDATA01 vào geometry hiện có, **không model allocation/train/GPU/remote/Git**.

## API frozen và cách nối tiếp

- `ResearchAKTShard` gọi lại `audit_research_shard` với provenanceSHA/callerlimits/completebank; chỉ development role, final reject trước iteration. Nó không generate corpus hay xác thực generator đã chạy đúng declaration.
- `prepare_research_phase(scope,shards=...,selection_freeze=...)` đòi exact scope/role mapping: `select_train80→train`;`raw_selection10→selection`;`refit_union90→train+selection`;`calibration_predict→calibration`. Refit gọi actual `prepare_refit_view`, giữ original roles/receipts và raw-selection freeze; không fakefold/legacy train union. Calibration cần cùng plan/bank freeze nhưng không nhận train/selection labels trong phase đó.
- `fit_research_encoding` chỉ hai optimization scopes; support là số uniquelearners/item. e80 và e90 khác optimizationphase/scope/shard/freeze lineage; item selection có thể vào e90, item calibration không được rescue. Rawselection từ chối e90, calprediction đòi e90 với cùng freeze. `trained_item` trong target là **item có trong vocabulary của optimization split**, chưa chứng minh neural fit đã chạy.
- `iter_research_windows(...,context=...,target_block=...,training=...)` chỉ compose exact existing `iter_window_slices/slice_causal_inputs`, encode_exercises/CausalSequenceInputs/TrainingWindow. Không viết lại causal geometry, không nhập model/training/Torch. Optimization từ chối selection/calibration. Prediction giữ OOV thành `ResearchUnseenTarget` với learner/query/globalrank và phaseidentity, không embed−1/rescue; suffix known dùng existing OOVbarrier và global anchors.
- `research_scoring_targets` xuất full truth sidecar mọi realevent, tách khỏi WindowInputs. Key thực tế gồm learner/query(item,timestamp,source_row)/globalrank/originrole/phase/encoding/support/historyhash+scheme. Đây là labelledger sau model-input preparation, không là argument cho predictor. Scope manifest/encoding/sidecar ghi `observable-prefix-chain-v1`: genesis gắn domainbank+learner, mỗi bước hash priorchain+previousobservable; currentresponse chỉ đổi hash sau currentrow. Nó **không phải OnlineSession model-bound historyhash**; downstream phải giữ scheme trong join, không trộn hai namespace. Cùng observablepast giữa model/vocab/scope cho chain giống nhau.

Phase/encoding kiểm lại exact source/input/lineage seal khi dùng; sourceinventory10files gồm actual geometry,encoding,schemas,RESDATA và config/provenance dependencies. Đây là consistency guard hợp tác, không cryptographic data/execution authority hoặc chống caller cố tình forge đầy đủ metadata. Full source/trainphase hashes có thể đổi khi sửa futurelabels; causality test chỉ so **current modelinput/pastprefix** đúng đại lượng, không đòi wholecorpusSHA bất biến.

## Actual validation

| Lượt | Kết quả | Controller | Scope |
|---|---:|---:|---|
| pure01 |24PASS/1FAIL/0error/skip |1,780566200031899s |Test tuple+list concatenation TypeError, production source chưa đổi |
| pure02 |25PASS/0failure/error/skip |1,739560604095459s |Chỉ sửa test `right` thành tuple; giữ prefixparity assertion |

Cumulative **3,520126804127358/30s**,0neuralcalls/optimizerupdates. Raw01 giữ đúng24+1; không relabel thành25PASS. Mỗi lượt13inputs trước=sau, có26snapshots/source/trial. Console02 `25 passed in1.30s`, JUnit02 suite1,304s; không lấy làm trainingthroughput. ExactNN/training import canaries và `torch not in sys.modules` trước/sau từng test thực tế đều qua; chỉ NumPy geometry và observable records dựng tay, không Paper2environment execution.

Controls: originaltrain windows exactparity với legacy API ở cả train/prediction; rawselection đủ5targets=3known+2OOV/globalranks0..4; suffixreset; explicit freshrefit90 vocabulary và source-used originroles; currentlabelperturbation giữ currentinputs/prefix nhưng đổi nextprefix; crossencoding sameprefix; finalcanary/role/freeze/source/encoding/geometrytype negatives. Bank fixture đủ84items/28concept nhưng train chỉ observed2items có chủ đích để kiểm OOV, **không đủ support cho research trajectory/reference readiness**.

Source final SHA `9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b`; test final `bee16620e1bdc2c98dd66e65b2ddddd82160098582b83b53a34120b50fb3645b`. Raw receipts/logs/XML ở `trial01/` và `trial02/`; controllers riêng `run_pure01.py/run_pure02.py` ghi cumulative không reset. Không broad oldsuite/rerunmodel.

## Pending BATCH2

Chưa explicit simulator-research execution phase/authorization/config, trainer/epochselection/refit optimizer, checkpoint/online attestation, calibration-prediction export trên fitted model hoặc actual corpus. Root đã tách BATCH2 để guard trước allocation; không dùng preflight/fold alias hay nới cap simulator_engineering. Data wrapper không tự cho phép execution. Source mới làm oldkit/Gate không bao phủ currentcode; parent quản lý freshsource/Gate/commit. Không kết luận fittedbaseline/calibration efficacy/RQcompletion.
