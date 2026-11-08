# Gap map main CG-AKT: selected-only → external freeze → refit90 → calibration10

**Static source review, SOURCE-ONLY.** Không import/execute/test/model/data/Git; không sửa production hoặc shared docs. Snapshot source hiện tại có hotpath đang ROOT freeze/chờ test, không dùng74outputs/core18 cũ để chứng nhận revision hotpath mới. Quyết định phương pháp là Recipe26 đã adopt; gap dưới là wiring/authority/coverage, không lý do chờ lại GVHD cho routine engineering.

## 1. Ranh giới không được nhầm

Recipe26 dòng40–47 yêu cầu graph/confidence fit TRAIN80 rồi giữ nguyên qua neural90; mỗi candidate selected-fit80/raw-best-selection10 **dừng**; tất cả candidate trong allocation hoàn tất trước external selector freeze; chỉ sau freeze mới fresh model/optimizer/encoding90 vàcalibration10. A0 độc lập là fallback, A3 graph-off không thay A0 (dòng26).

Runner hiện tại cố ý là **pilot A0 đơn-candidate**:

- `research_execution.py:22–25,387–394`: scope A0; permitted phases gồm selection_fit/refit90/calibration/Tfit; purpose `a0_single_candidate_lifecycle_pilot`, candidate allocation `['A0']`, system selector deferred.
- `research_runner.py:495–536`: train80, EarlyStopping, reload/export best raw selection, tạo local `SelectionFreeze`.
- `research_runner.py:537–550`: **refit ngay** trong cùng call; `603–640` chỉ có entry `run_a0_research_lifecycle`, terminal nhãn A0/pilot/main_matrix_complete=false.

Không gọi pilot này nhiều lần rồi gọi đó là main matrix. Không đổi tên auth/purpose/COMPLETE cũ để promotion. Raw artifact pilot chỉ có thể được xét reuse bằng một admission riêng đầy đủ source/config/split/init/population/ordering; không tự thành selected-only receipt hợp lệ.

## 2. Dependency map tối thiểu

| Ranh giới | Đã có để reuse | Gap chính xác / output tối thiểu cần thêm |
|---|---|---|
|Main stage/candidate authority|Guard revalidate actualdisk/runtime/Gate/source tại `research_execution.py:97–109,174–197,371–434`|Main spec/stage binding riêng: candidateID+variant/graph mode+Recipe26SHA+allocationSHA+conditionSHA+phase entitlement. Selected-only token **không được refit/calibrate**. Refit token phải consume externalfreeze thật trước constructor. Giữ oldA0scope/API hành vi cũ|
|Role-aware public data access|Audited roles/plan/encoding tại `research_simulator_data.py:66–100,174–209`; public reader validation sẵn|Current reader `simulator_corpus_reader.py:298–330` parse cả3roles; `_admit:118–125` còn xemcalibration two-class support trướcfit. Hợpwholepilot, **không là isolation boundary selected-only**. Cần public role-scoped entry/type; xem mục3|
|Selected candidate epoch/terminal|Reuse `_train_epoch:325–370`, `EarlyStopping:357–373`, bestrestore/export `runner:495–528`|Cắt selected-only terminal sau rawbestexport; không chạm refit90/calibrationevents. Receipt bind candidate/condition/initialbackbone/encoding80/checkpoint/epoch/rawpredictions/targets/fullcoverage/metric/source/runtime; incomplete epoch không accepted|
|Graph epoch integration|`ResearchGraphAKTAdapter.collate_training:307–315`, `step:317–348`, `set_context_index:276–285`, boundary audit:287–295|Currentrunner collate `research_runner.py:332–336` dùng plain collate_windows, không tạo graphticket. Chỉ thay constructor sẽ fail tại graphmodel320. Batch factory phải gọi graph collate_training; attach index đúng train/selection/calibration phase và audit trước/sau pass. Giữ optimizer reservation/body-return accounting|
|Initialization fairness|Graph nativeconstructor `research_graph_model.py:119–137` buildbackbone trước alpha/gate; A3fork_rng/zero-init|Runner `_new_model:314–321` chỉ tạo AKTAdapter. Cần typed factory nhỏ cho A0–A3, shared **initial backbone tensor identity** và freshAdam từngcandidate; không warm-start từ A0 đã train. Hash toàn `.native` không so sánh được backbone equality vì graph có prefix/alpha/gate thêm. Encoding90 identity vẫn phải khác80 do lineage mới; chỉ **initial backbone tensor hash**80/90 có thể bằng nhau nếu vocab/seed trùng, không ép weights khác để giảfresh|
|External selector/freeze|SelectionFreeze dataobject `simulator_research_data.py:192–213`; GraphNeuralPhaseBinding `research_graph_condition.py:280–342`|Các SHA/type checks chỉ consistency, không xác minh allcandidate receipts hoặc quyềnfreeze. Cần evaluator cached-only + closedfreeze artifact chứa đủallocation/eligibleIDs/commonkeys/draws/statistics/winner/A0fallback và source/inputSHAs. Mọi mainrefit đều kiểmreceipt này thực sự, không chỉ nhận64hexstring|
|Graph-aware checkpoint/reload|Generic payload `checkpoint.py:23–53` đã lưu `.native.state_dict`+Adam+Python/NumPy/TorchRNG; boundedreadonce/strictrestore `runner:393–423`|Bổ sung semantic identity: recipe/variant/condition/initialbackbone/graph-confidence TRAIN80/phase/externalfreeze/vocab/bank/source/runtime. `runner:373–377`/`online.py:25–37` hiện là upstreamAKT A0 identity, không tự thành graph checkpoint. Strict restore phải có backbone+alpha+gate và legitimate missing/per-paramAdam state; không điền state giả hoặc ép mọi step bằng globalstep|
|Fresh refit90 + calibration10|`prepare_refit_view:236–258` union train+selection đúngrole; encoding scopes/checks; currentfresh `_new_model` ởrunner540; responsecalibration API|Entry refit-after-external-freeze tách riêng, dùng selectedepoch của đúngcandidate và **fresh** model/Adam/encoding90; graph/confidence TRAIN80 khôngrefit (condition320–342). Fit T chỉ calibration10 sau weightsfinal; không chọn lại winner bằngrefit/temperature metrics|

Đây là vài ranh giới cần nối, không cần một trainerframework mới hoặc gộpAKT/SAKT/GKT thành class chung. Shared candidate-export contract đủ cho selector; baseline adapters khác có thể triển khai riêng theo allocation.

## 3. Public reader nhỏ nhất, không forged CompleteCorpus

Giữ `read_public_research_corpus(...)` hiện tại cho wholepilot và tests cũ. Thêm **public role-aware entry** với requestedroles chính xác và result type thể hiện scope (ví dụ role-scoped validated view), tái dùng cùng manifest/role/provenance/observable validators. Không gọi private reader/construct object bằng `object.__new__`, không tạo CompleteCorpus giả thiếuroles.

- Selected stage chỉ materialize train+selection trajectories. Có thể kiểm/hash metadata/byte bindings cácrole khác để bảo vệdisjointness; không deserialize calibrationevent labels hoặc kiểm outcome class để hướng chọncandidate. Không đọc final/oracle.
- Refit stage materialize train+selection sau actualexternalfreeze; calibration stage mới materializecalibration, kiểmtwo-classsupport vàfitT. Metadata plan/assignments vẫn kiểmseedfamily disjoint nhưcũ; không relabel selection thànhtrain bằngshardgiả.
- Một candidate run có thể preload train/selection đầyđủ và dùng phase-bound views cho train vsrawselection; labels chỉ join vào loss/evaluator tươngứng. Shape/sourcehash toàntrajectory không phải chứng minh không leak: actual graph evidence vẫn phải past-only theo effectivewindow/OOVreset.

Current `_admit` đọccalibration trướcfit không tự chứng minh pilot đã dùng sai gradient; finding là **API chưa cưỡng chế mainstagevisibility**. Cần regression kiểmactualopen paths cho selected-only, không chỉ assert tênrole trongmetadata.

## 4. Selector: những chi tiết phải giữ đúng, tránh metric drift

- Recipe26:47 chốt2000learner-cluster draws, seed42, sortedlearnerIDs, same draws choeligible candidates; upper quantile.975 của95%two-sided percentile; eligible khi upper(LL_graph−LL_A0)<0; chọn meanLL nhỏnhất, stablecandidateIDtie; noneeligible→independentA0.
- Protocol21:36 nêu A1/A3 soA0. Recipe26 nói “eligible candidate” nhưng chưa cómachine-readable ID list. **Không tự cho A2/SAKT/GKT thànhfallbackeligible.** Root cần freeze finiteallocation+eligibleIDs/common-support universe trướcfits, theo ruleđãadopt; A2/SAKT/GKT vẫn giữ requiredcomparison rows, không bị bỏ vì không thuộcselector. Không cần mởlại protocol hoặc xinadvisor cho mapping IDs routine.
- Join rawbest80 exports bằng samelearner/query/source_row/globalrank/history-prefix, verifylabels/population/fullcoverage; OOV vẫnnull, không graph-rescue. Common-supported target universe phải cốđịnh cho so sánh eligible+A0; không đổi pairwiseintersection theo candidate hoặc bỏcandidates chưacomplete để lấywinner.
- PrimaryLL response-pooled trêncommon-supported targets, không meanlearnerLL hoặc fold-macro. `paired_bootstrap.py:70–96` hiện **average fold estimates**, default1000/seed20261030; không drop-in choRule26 dù nó dùngcluster vàquantile. Có thể reuse sufficient-stat arithmetic sau đúngpopulation/draws/aggregation, không đổiestimand ngầm.
- Epochselection `runner:507` dùng frozen nativefloat32 BCE/`EarlyStopping`objective; externalLL dùng canonical reporting evaluator trên raw exportedfloat32 probabilities. Không substitute `native_bce_mean` hoặc Tfit logit-clipped objective vào selectorLL. Currentrunner đã tách `OBJECTIVE:27`, `METRICS:28`, reporting `475–479`, calibrationexport `590–597`; giữ nhữngnhãn này.
- Calibration reporting hiện ghi **in_sample_calibration_partition_not_external_quality**. Không dùng Tfit partition metric gain để đổiwinner hoặc gọi responsecalibration làlatentmasteryaccuracy. `PredictionBinding` hiện55–70 cần finalcheckpoint/domain/vocab/source binding; thêm graph/freeze lineage vào modelidentity/checkpoint và boundartifact, không đổi ý nghĩaT.

## 5. Small implementation order để tiến actual research

1. **Stage contracts + public roles:** mainphase/candidateallocation identity, selected-only terminal, public role-scoped reader; preserve wholepilot A0. Acceptance: selected cannot open calibrationevents/refit, refitcannotconstruct beforeactualclosedexternalfreeze/allselectedreceipts.
2. **Candidate epoch wiring + checkpoint boundary:** typed graphfactory/index/`collate_training`, reuse nativeepoch+ledger+EarlyStopping/prediction/export; phase-specificinitialbackbone equality+freshAdam; graphcheckpoints strictsemanticidentity/restore. Graphadapter328 hiệnchỉnhận optimizerfresh ởfirststep: restoreoptimizernonempty vào mộtadapter mới rồi tiếp tụctrain cần explicitownedrestore support, **không xóa Adamstate để qua guard**. Refit fresh khôngwarmstartselected. Resume hiện vẫnfalse nếu chưa cócontract.
3. **Cached externalselector:** consume completebestexports/allocation, exactcommonkeys/LL/draws/freeze artifact. Receipt phải bind allinputs/stats; không cần modelcalls để kiểmselector. Mọifalseauthority/missingcandidate/latecalibratedselection rejected.
4. **Refit-after-freeze + calibration:** same frozen graph/confidence80, freshencoding90 andexactselectedepochs, strictreload+fullcalibrationexport/temperature binding; không đổi winner. Theo23, fullplannedmatrix vẫn9neuralconditions/environment và36optimizationphases hai môi trường; stagedmissingphases báothiếu, không âmthầm refitonlywinner.

Đây là đề xuất scope/code contracts đểROOT review, chưa requestthực thi hoặc đềxuất thay hyperparameters/epochs. Không một configmặcđịnh/fixture đãPASS thay selectedterminal thật. Source/test batching nên freeze trước currentruntime/Gate; `authorization.gate2_build_hashes:96–113` bao toànakt/shared/scriptpaths, nên source mới sẽ yêu cầu buildbinding/Gate phùhợp; review này không xác nhận currentGatefreshness hoặc tự chạyGate.

## 6. CPU-only ≠ GPU/paid readiness

Graphconstructor `research_graph_model.py:126` tạo parameters trongCPU; `_batch_sha:80`, `_collate:305`, `step:338` vàprediction path hardcodeCPU. Config `config.py:162–171` giữ simulatorresearch CPU frozen geometry; runner `_execute:483–492` yêu cầuCUDA hidden/unavailable. `config.graph=False` cùng `n_pid=0` là ràng buộc admission của pipeline AKT hiện có, không côngtắc Recipe26residual. AKT upstream không có prerequisite graph; NonRasch chỉ bỏ thành phần difficulty/Rasch. Không bật `graph=True` để “chạyA1”. Variant nằm trongtypedcondition.

Đã cóCPUcore18/74closed tạicommit1ec4b87 theoROOT, không trainer/fittedefficacy; hotpathrevision hiệnchờROOTtests. FutureGPU cầnport explicitdevice/batch/context/checkpoint/execution/runtime/resource guards vàactualadmission tươngứng, không đổi `device` trongJSON rồi suyready; không cấp paidpermission từ review/code. Simulatorresearch entry hiện `input_domain='simulator'/junyi_fold_used=False`; không coi đó làJunyi pipeline đãwired. SAKT/GKT/learnedgraph/twoenvironment requirements vẫn giữ.

## Source snapshot đã đọc

Các SHA dưới là currentbyte snapshot khi lậpnote; không phải test verdict, không copy/move nguồn. Không đọc corpus events/oracle/final/Holdout/checkpointpayload.

- `docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md`: `13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a`
- `docs/thesis_recovery/25_MINIMAL_GRAPH_AKT_RESEARCH_RECIPE_DRAFT.md`: `7b478d584820351ac3ff118c8856b4afa935f4bf1a4137b6d82ef3037adea080`
- `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md`: `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6`
- `docs/thesis_recovery/23_TRAINING_MATRIX_ACCOUNTING_V1.md`: `6f9e5adc2f075cb9c0c43ebbf1852e2365dd1baf5ff7c59dd8630561b3d72567`
- `src/knowledge_tracing/akt/research_runner.py`: `19627a1aa1bbf76069f1a07e0b56a3b5c79a1651863a31c37ac1c08c6cf62092`
- `src/knowledge_tracing/akt/research_lifecycle.py`: `cf16402f26d27732cedce83aa01bb46a84537c21cdbed11b80c5fb920fad0fff`
- `src/knowledge_tracing/akt/research_execution.py`: `5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6`
- `src/knowledge_tracing/akt/research_simulator_data.py`: `9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b`
- `src/knowledge_tracing/simulator_research_data.py`: `51eb7275a6a4a6b26b763a21a8fe6dc15b0973fc19b3c5557175eaa298db7e53`
- `src/knowledge_tracing/simulator_corpus_reader.py`: `e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90`
- `src/knowledge_tracing/akt/research_graph_condition.py`: `6678f04c3c0b3655aa797edd3e491877d17ac3f0fa12f7dfc9971f637d875cf0`
- `src/knowledge_tracing/akt/research_graph_context.py`: `8bfe0dca095d1de6c898fd849be6c5d1ee7033dffc13c20b24c7857de92bb029`
- `src/knowledge_tracing/akt/research_graph_model.py`: `77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397`
- `src/knowledge_tracing/akt/checkpoint.py`: `bc1a6fbdcaa55c864cb9f18d531dcede440f9cf364dc9025420615520394fc91`
- `src/knowledge_tracing/akt/online.py`: `f41c9c5835a2d3bd8406ea83855a608f0d7d8fa794e4de56b655acb02381ffbb`
- `src/knowledge_tracing/akt/training.py`: `ca074a15dd5e45d016fd29d78b0b5ddbb0ccee3555b194699464d4cded6bf979`
- `src/knowledge_tracing/akt/config.py`: `beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f`
- `src/knowledge_tracing/akt/authorization.py`: `bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0`
- `src/knowledge_tracing/response_calibration.py`: `c7849654eff35862e61602a4f95e401ed88b9070a77832e05d6a7173e72ebacb`
- `src/knowledge_tracing/paired_bootstrap.py`: `52c2bd06edf980c6a8f3a94a849a47dedaf2a91e19d74dfc33febf0f4efc8559`
- `research_tracking/reports/cgakt_research_core_20261109.md`: `1ec976ea4b54af5b04a613759e7e0a304e19a4c471d5c40855eb114bc3089148`



## Ghi nhận ROOT sau review

09/11: note nguồn ban đầu SHA `d608ab0963f515c42233052950eaf450e313a0e60e0486ec201fd4140460fd4f`; kiểm đủ21source/report pins trước xuất bản. Đã làm rõ câu config.graph để tránh gán prerequisite graph cho AKT upstream. Các dòng “hotpath chờ test” ở review là thời điểm đọc nguồn: sau đó ROOT đã thực chạy135pure và25native cases trên chính các source pins này, chưa actualAdam hoặc researchfit. Không coi việc này là main-stage readiness.

Kế hoạch này cụ thể hóa Recipe26, chưa thay đổi runner/pilot cũ, không chọn cấu hình hoặc bỏ bất kỳ baseline/dataset/deliverable nào. Bước gần nhất sau hotpath là actualAdam hữu hạn rồi checkpoint/ownedrestore; main-stage contracts và public scoped reader có thể chuẩn bị song song với cached external selector. Cần đóng toàn bộ các ranh giới trước main training. Chưa chi Modal; không truy cập Holdout hoặc tự phê duyệt fullCV.
