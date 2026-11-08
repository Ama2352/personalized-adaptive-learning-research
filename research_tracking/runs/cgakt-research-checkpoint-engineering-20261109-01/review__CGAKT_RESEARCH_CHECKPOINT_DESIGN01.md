# GRAPH11 — checkpoint/owned restore cho CG-AKT nghiên cứu

09/11/2026. **SOURCE-ONLY DESIGN**, không production edit/import/execute/data/model/test/Git. Không thay generic AKT/pilot/SAKT formats. Graph10đang kiểm primitive optimizer, không là completed research epoch. Canonical reader audit cả3Developmentroles trước allocation được22:22–24 cho phép; chỉ phaseinputs đúng vai trò đi vào optimization. Không yêu cầu reader mới hoặc coi label deserialization trong provenance audit là scientific blocker.

## 1. Phần thiếu thực tế và scope nhỏ nhất

Đề xuất NEW `src/knowledge_tracing/akt/research_graph_checkpoint.py` + `tests/akt/test_research_graph_checkpoint.py`. Reuse existing filesystem `publish_new_file`, train_epoch/EpochStats, graph adapter/context và native Adam. Không clone train loop, thêm general framework/SGD/CUDA/mid-epoch cursor hoặc sửa historical genericcheckpoint.

Module đầu tiên chỉ lưu **complete-epoch training state**, không selected-fit certificate: role=`cgakt_research_complete_epoch_training_state_v1`, fitted_research_model=False, iterator_resume_supported=False, lifecycle_resume_supported=False. Không tự coi epochcheckpoint là main selector freeze, refit hoàn tất, calibrated backend hoặc independentA0 system fallback.

**Graph10không đủ epoch receipt:** contextfixture có8windows/48targets nhưng3entrycalls chỉ18targets. Không gán complete=True từ3Adamsteps. Nếu cần artifact cho những calls đó, phải là role KHÁC `completed_optimizer_step_state_not_epoch`, explicit partial/no selectedepoch; không mở format song song trong batch đầu. Khuyến nghị native acceptance mới dùng đủ8window/2batches của tiny cohort để tạo1complete epoch thật.

## 2. Exact API đề xuất

- `graph_checkpoint_identity(*, config, encoding, condition, index, profile) -> JSON-compatible dict`: static/data binding trước deserialization/constructor khi caller đã có typeddata. Không phụ thuộc process IDs. Profile bắt buộc protocol26+21 SHA, historicalproducer/current-runtime profile, seed/shared-initial-backbone SHA từ pre-update receipt, source pins, runpurpose/candidate allocation và phase/freeze evidence.
- `GraphAdamParticipation(adapter, optimizer, *, event_sink)` gắn **owned optimizer** pre/post hooks từ đầu training hoặc sau verified restore; không global monkeypatch. Snapshot trả global reserved/body-returned counters, pending mask và exact named-parameter participation counters. Event sink của lifecycle ghi/fsync, không thêm daemon/authority. Actual zero-gradient tensor vẫn là participation; gradNone không phải participation.
- `save_graph_epoch_state(new_directory, *, adapter, optimizer, participation, epoch_receipt, expected_identity, limits) -> GraphCheckpointRef`: chỉ complete epoch+no pending; full context audit trước/sau; saveCPU model+Adam+RNG+modes/counters, atomic no-clobber COMPLETE-last.
- `inspect_graph_epoch_state(directory, *, expected_identity, expected_complete_sha256, limits) -> InspectedGraphCheckpoint`: chỉ JSON/byteSHA/size/source/role/phase validation trước lazy Torch/deserialization hoặc fresh model constructor; không model factory/callablepickle. Inspected record không execution authority.
- `restore_graph_epoch_state(inspected, *, fresh_adapter, fresh_owned_optimizer, expected_identity, limits) -> RestoredGraphEpochState`: strict ownedstate validation trước mutation, restore model/optimizer/RNG/modes/progress; rebuild live accessseal/parameter IDs, không deserialize ticket/nativecall. Sameepoch p/loss/count/state parity và một controlled continuation có thể kiểm sau đó, không auto resume loop.

Module top-level stdlib+TYPE_CHECKING; Torch/NumPy/model imports lazy sau metadata admission. Caller actual research entry vẫn phải consume runtime/data/execution guard trước constructor; checkpoint identity không cấp quyền chạy.

## 3. Identity/phase bắt buộc

Bind recipe26 exactSHA/name, A0/A1/A2/A3 +graph mode, full condition identity **và unsupported flags/null source scores**, graph/topology/sourceartifact/train80 lineage, bank semantic domain và item-bankSHA, vocabvalues/supportSHA, encoding80/90 optimization origin roles, full indexroot/neuralbinding/phaseSHA/geometry, actual optimizer config và stable named-param ordering. Graph/confidence train80 giữ nguyên qua neural refit90; không gọi toàn estimator đã refit90.

`ResearchGraphAKTAdapter.identity` hiện bind condition/encoding/config/source nhưng **không phase indexroot**, vì adapter đổi train→selection index cùng encoding. Vì vậy checkpoint phải bind thêm exact indexroot/neuralbinding và chỉ cho optimization scope select_train80/refit_union90; không save selection/calibration predictor như training epoch.

Local SelectionFreeze.identity của data và external main-system-freeze artifact là hai bindings riêng. Refit checkpoint cần expected externalfreeze/candidate-result/selectedepoch được lifecycle admit; SHA-shaped field riêng không xác minh authority. Prefixrefit completeepoch chưa phải final refit: completed_epochs≤selectedepoch, chỉ full completion đúng số epoch mới có downstream fit receipt. Không tái chọn winner bằng refit/calibration outcomes.

Portable identity loại process/Python object IDs, outputdirectory/runworker IDs; bind numerical config+source/profile thay vì absoluteRoot tùy máy. Historical producer runtime receipt và compatible restorer profile lưu riêng, không sửa sourceSHAs theo host mới. Format CPU FP32 portable không tự nghĩa cross-OS/source-line-ending profile đã được nghiệm thu. Seed/initial-backbone identity phải capture trước bất kỳ update; không lấy trained-stateSHA rồi đặt tên initial.

## 4. Adam participation — khác SAKT

Native installed Adam `_init_group` chỉ xử lý parameter có `p.grad is not None`. Zero tensor gradient vẫn initialize moments và increment step; không đòi nonzero gradient/weight movement/positive benefit. Whole graph-off/mass0 bỏ branch nên alpha/gate có thể gradNone, chưa có state, hoặc đã có state từ batch cũ với step nhỏ hơn global.

Pre-hook sau backward capture exact ordered named params có gradTensor và globalreservation; post-hook sau body return kiểm state-step deltas rồi commit **participation per param**. Pending prehook/exception/latecontextfailure không complete epoch và không rollback. Cần phân biệt native bodyreturn, hook return và accepted adapter/epoch; posthook error không được suy0updates.

Quy tắc payload cho MỖI owned named parameter:
- participation_count=0: native state **absent** hoặc exact empty dict nếu actual optimizer đã tạo empty entry; preserve representation trong manifest. Không điền fake moments/step0 để làm đủ coverage.
- participation_count>0: initialized native Adam dict exact{step,exp_avg,exp_avg_sq}, shapes/dtypes/deviceCPU/finite đúng; `step == participation_count`, có thể<globalbodyreturns. Không chỉ kiểm1≤step≤global: như vậy authenticated stale positive counter vẫn lọt. Required initialized set chính là setpositiveparticipation, không mọiparam.
- exp_avg_sq≥0; hiện graphadapter rejects amsgrad/foreach/fused/capturable/differentiable/maximize/decoupled behavior, nên không tự mở support các flags này. Exact state/group/parameter-name ownership +lr/betas/eps/weight_decay phải khớp.
- **Phân biệt gradNone với literal optimizer.state[param]=None**: latter không là native Adam state hợp lệ vì implementation gọi len(state); reject literalNone thay vì gọi đó là legitimate absent. Metadata có thể dùng null để mô tả KHÔNG có state, nhưng không restore null thành state entry.

Perparamledger không tự là attestation chống caller forge toànmetadata. Nó phải được actual trusted wrapper ghi từ hooks, pinned source/orderedbatch/epoch receipts và counters trước/sau; không suy participation từ moment bằng0 hoặc branchweight bằng0.

## 5. Complete epoch, không chỉ complete iterable

Receipt phải reconcile existing EpochStats.complete/stop_reason, windows_processed/targetcounts/batches với **full index expected window IDs và fulltarget keyset**, iterator/cursor exhausted, no duplicate/drop/unknownOOVtraining, all started/bodyreturned steps và no pending TrainingTicket/native._call. Stats.complete chỉ từ short supplied iterable chưa chứng minh toàn phase. Full context boundary audit thành công trước checkpoint; unselected tamper phát hiện sau update làm failed/partial, không checkpoint success.

Persist completed_epoch_count, global optimizer body/reservation counters, perparameter counts và epoch coverage/ordered-window ledger hash. Không persist earlystop/systemselection/global remainingbudget như thể module đã khôi phục lifecycle; fields này do mainwrapper quyết định. Nếu chưa kiểm restore sampler/EarlyStopping/globaldeadline/outputownership thì `lifecycle_resume_supported=False` giữ nguyên.

## 6. Owned restore có một junction phải xử lý công khai

Current graphadapter step yêu cầu `self._optimizer is optimizer or (self._optimizer is None and not optimizer.state)`. Fresh adapter `_optimizer=None`; load nonempty Adam state rồi gọi step sẽ bị từ chối. **Chỉ torch.load/load_state_dict chưa tạo usable restore.**

Khuyến nghị một narrow adjacent model API sau ROOTscopeapproval: `_adopt_verified_restored_optimizer(optimizer, *, restore_receipt)` hoặc method tương đương owner-reviewed, gọi duy nhất sau toàn bộ checkpoint validation/mutation thành công. Nó kiểm exactownership/settings/currentnative digest/pending/failure state và bind fresh live optimizer. Không mở arbitrary “already_trained=True” bool để bypass freshness. Nếu giữ onlynewmodule scope, loader có thể final-bind private `_optimizer` trong cùng trusted implementation contract, nhưng phải Root/modelowner review rõ; không giấu bypass trong test. Không sửa production trong note này.

Restore requires freshhealthy adapter, no training ticket/nativecall, freshowned Adam stateempty trước load, exact everyregisteredparameter once, new process IDs, no reuse failed adapter/foreign optimizer. Validate all payload/RNG/modes/state trước load. Nếu load_state_dict fail giữa mutation, discard owned containers/failreceipt; không rollback claim. Reset gradients=None, rebuild local seal/parameter ownership, restore saved per-module modes and RNG LAST sau constructor/validation, giữ actual named-state exactness.

## 7. Format và publication tối thiểu

Fresh `experiments/akt/results/<run>/checkpoints/epoch-N/` only: state.pt +metadata.json +COMPLETE.json; metadata/failure/logs smallarchive, binary giữexperiments/hashrefs. Files mới exclusive, no symlink/junction/traversal; publish_new_file/fsync/readback, marker last; failure/pending/extra files khiến reject. External COMPLETEbyteSHA mandatory.

JSON metadata closed schema/boundedbytes/checkpointSHA+size/tensor-shapes inventory/sourceidentity/role/phase/epoch/participation. Inspect trước modelallocation khi có thể; checkpointbytecap+SHA trước torch.load(weights_only=True,map_location='cpu'). Tensorbytescap trước/save và sau/load; weights_only không tự là RAM/security guarantee cho arbitrary hostile archives. Chỉ trusted ownedproducer format, không general untrustedpickleAPI. Không pickle module/callable/fullindex/phase/trajectories/truth/corpus/tickets/accessseals.

Full registered state_dict gồm backbone+alpha+gate; strictkeys/shapes/dtypes/finite, nativeAdamgroups/nameordering. Python RNG, NumPy encodedstate và CPUtorch byte RNG +module modes snapshot giống safeCPU pattern; không gọi generic save/restore helper vốn kiểm CUDAavailable và get_rng_state_all. Không device fallback hoặc thêm GPU support. Limits bắt buộc finite, ROOT chốt từ actualtensor inventory; không bê8MiBtoycap sang model256/Adam. Có thể đề xuất64MiBfile/64MiBtensors/1MiBmetadata cho boundedprobe, chưa chứng minh feasibility hoặc đặt defaultresearch.

## 8. Meaningful acceptance và callcaps đề xuất, CHƯA chạy

Pure negative: wrongrecipe/engineeringtag/oracle/confidenceartifact/phase/vocab/source/freezes/role/missingCOMPLETE/failurepending/bytecap reject trước deserialization; no constructor khi inspect identity fail. Authenticatedpayload: drop positiveparticipation state, stale/overcount oneparamstep, negative secondmoment, foreign/duplicate groups, malformedRNG/modes =>reject trước model/opt mutation. Correct gradNone/absent/empty/count0 và initializedstep<global **với exactparticipation proof** phải accept. SGD/AMSGrad không được silently mở.

Native proposal đầu: handmade complete8trainlearners×6events=8windows/48targets, frozen256geometry/CPUFP32/thread2, noactualcorpus/teacher/GPU. Dùng existing train_epoch+batch_factory, verify fullcoverage2batches; fixture support groups được predeclare theo fixedsampler, không chọn theo loss. Có inactive và active graph batch để expose absent/tardy branchstate; alpha0gategrad có thể zeroTensor, không giả nó làNone.

OwnedprocessA: completeE1 bằng2updates, checkpoint thật; capture same-input E1 inference p/loss/count và RNG/state digests. Có thể chạy1explicit active minibatch continuation để tạo control. OwnedprocessB: freshctor/Adam/data/index +strict E1restore, E1parity, cùng minibatch continuation1update từ restoredRNG, compare allnative+Adam state digests/counters. Tổng đề xuất **2graphconstructors,2Adamconstructors,6forwards(4train+2parity),4logicalbackwards,4Adam bodies**. Không claim completeE2 hoặc nextsampler resume từ một controlled continuation; chỉ E1checkpoint+onestepstate consistency. Nếu ROOT chỉ muốn persist/reloadfirst thì2updates/2parity đã đủ và phải bỏ continuation claim.

Prefix train_epoch cần EXACT8windows/48targets; Graph10threepartialcalls không được reuse bằng đổi completeflag. Numeric no-effect vẫn hợp lệ; không lossimprovement/alpha>0 threshold. Serialization testcaps tạm≤8torch.save/≤16torch.load cho cảvalid/negative cases,0additional optimizer frommalformedtests; ROOT review statically before allocation.

Đề xuất wholeCPU90s cumulative qua cảhaiownedprocesses inclcleanup3s, RSS512MiB/free1GiB là probe caps chưa feasibility guarantee; remainingbudget truyền sang processB, không90s mỗiprocess/reset. Metadata guard/tests trước, actualallocation riêng sau Rootsource/runtime/Gate/input/resource review. Existing generic recovery_v1 CPUstate không chứng minh graphcursor/ownership/participation; mid-epoch và fullresearch resume chưa trong batch.

## Nguồn inspection

- akt/checkpoint.py:16–68/91–115 — generic save/load/restore và CUDA RNG path; SHAbc1a6fbdcaa55c864cb9f18d531dcede440f9cf364dc9025420615520394fc91.
- sakt/research_checkpoint.py:105/173/209/333 — portableidentity, completeepochreceipt, SAKTallparticipation validation, inspect-beforemutation; SHA40fa69b861fb93d565fb2a37a0f126509c5239e681fdf3a3c5ae022f3b6cb3c7. Không copy allAdamstep==global.
- akt/research_graph_model.py:255–295/317–348 — adapteridentity/fullboundary, currentfreshoptimizer ownership andoneuseticket; SHA77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397.
- akt/training.py:33–59/112 — EpochStats/train_epoch; SHAca074a15dd5e45d016fd29d78b0b5ddbb0ccee3555b194699464d4cded6bf979. akt/model.py:24–67 zero_grad(set_to_none=True)/backward/clip/optimizer primitive.
- installed torch/optim/adam.py:148–188 — skipgradNone/lazyemptydict/moments; SHAdca23a7bfdf3a086292528269b815df7fba9f0cf764a18e84b26b3fee2c7147c. Chỉ đọc sourcefile, không importTorch. Protocol21/22/26 giữ nguyên.