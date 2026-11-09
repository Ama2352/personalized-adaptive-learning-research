# Main selected-only A0–A3 — patch plan01 trước code

SOURCE-ONLY; không import/test/native/corpus/auth-artifact creation/Git. Giữ nguyên pilot và checkpoint/source đang freeze. MainStage mới77b7 có epoch_validation_inputs(), chỉ là NO_EXECUTION_AUTHORITY. Owner platform xác nhận chỉ sở hữu stage/puretests, không executionguard/producer.

## Hai file mới và guard thực

1. `akt/research_main_execution.py`: MainSelectedExecutionSpec + concrete MainSelectedExecution, factory `require_main_selected_authorization(...)`. Reuse typed SimulatorResearchSpec/ResearchRuntimeEvidence/ResearchResourceBudget, `_path/_hash_file/_read_json`, `_native_evidence` và `_corpus` của research_execution. Không gọi prepare_research_identity/require_research_authorization cũ vì chúng hardcode A0pilot+refit/calibration. Nguồn cũ không sửa.
2. `akt/research_selected_runner.py`: `run_main_selected_candidate(execution, *, read_limits, context_limits, checkpoint_limits)`. Exact typedguard được RECONSTRUCT/REVALIDATE từ actualauth file tại entry, không tin caller instantiate/token/MainStage/callable/boolean. Nhận A0–A3 family trước; SAKT/GKT reject unsupportedproducer trước model, không bị bỏ khỏi required9/allocation.

Auth schema mới đóng:

```text
schema_version=1
scope=simulator-research-main-selected-only-v1
decision=AUTHORIZE_BOUNDED_MAIN_SELECTED_ONLY
run_id, config_sha256, execution_spec_sha256, stage_spec_sha256
identity = actual protocol21/22/23/26/allocation + source/Gate/runtime/data/graph bindings
caps = exact declared budget/read/context/checkpoint/output limits
requested_phases = [select_train80, raw_selection10]
approval_reference = externally supplied ROOT/user instruction reference
```

Không tạo auth file trong implementation/preparation; không sử dụng auth của oldA0pilot. `execution_enabled=True` vẫn bắt buộc nhưng không đủ. Guard đọc/hash actualclosedauth và soexactschema/identity/caps; real runtime/schema2CPU +softwareGate+lock+source được `_native_evidence` kiểm, không syntheticreceipt. `_corpus` chỉ cố định publicpaths; actualpublicreader re-audit trước model, matchbank/plan/role/count/source. Reader audit cả3roles được Protocol22 cho phép; chỉ typedtrain/selection đi vào producer. Không oracle/final/Holdout/Junyi giả.

Context mapping phải cố định: domain=semanticbankidentity; bank=actualbank.json byteSHA; split=researchplanidentity; train/selection roleSHA=audited shardSHA (không nhầm raw JSONL byteSHA). Rawfile inventory vẫn bind riêng. Verify context này sau actualreader, trước constructor. Revalidate auth/source/Gate/runtime/corpus bytes tại stage/constructor boundaries; peakRAM/freeRAM/globalwall/train-time checks không reset qua epoch hoặc freshreload.

Graph request là concrete immutable data, KHÔNG callback: expert topology sourcepath+SHA hoặc Method24ArtifactRef/TrainingBinding/ReadLimits/expectedloadedidentity. Main guard/entry gọi actualload_method24_scores và condition factory, đối chiếu corpusTRAIN80/provenance/domain/source và expectedcondition; không dùng manufacturedLoaded/fakeVerified. Điều kiện expertA2/A3 cần scoreartifact đúng declaredgraph; thiếu thì STOP, không lấy learnedgraph scores/ones thay. A1expert không bắt buộc Method24. Binds declaredgraphkind→candidate trước model. Thêm byte/time caps graphinputs trong exactauth, không mở tự do theo payloadpath.

## Actual training và epoch validation

- Publicreader → train80/selection10 phases → encoding80 từ train → actualcondition → bounded sealed train/selection contextindices. MainStage.begin_selected_fit(); phase_inputs() chỉtrain. Mỗi epoch dùng epoch_validation_inputs() đọc selection trong fitstate, không chờ finalbeststage.
- Dùng ResearchGraphAKTAdapter cho mọiA*: A0 là independentfresh variantA0/nodes=edges=()/graph_mode='none', không A3off. Internalemptycondition identity vẫn bind checkpoint/implementation; externalMainSpec/SelectedClaim A0 graph_condition=None giữ nghĩa estimator-disabled. Không bỏ qua internalidentity để khớp schema.
- Reuse train_epoch(...batch_factory=GraphAdamParticipation.collate,progress_callback=tracker.progress,resource_callback=globalguard,recovery=None), begin/finish actualcompleteepoch. Tracker event_sink fsync reserve BEFORE Adam body và body-returned sau; runner giữ cumulative reserved/returned/complete counters+targets, sourcecap/globalclock. Không copy training loop hoặc native Adam/loss.
- Selectionprediction phải switch index đúngphase, audit trước/sau và invariantweights; reuse raw `_predict`/`_exports` primitives của runner cũ, không gọi old_execute/run_a0_lifecycle. Native EarlyStopping/maxepochs/patience/min_delta giữ nguyên; raw reportingLL không thay epoch nativeBCE objective.
- Khi save best completeepoch bằng CPf40, switch adapter VỀtrainindex trước save: receipt.phase_index làtrainindex, không save trong selectionindex. CPstate giữ flagfitted_research_model=False (statecontainer không certificate); actualauthorizedselectedterminal riêng mới gắn completefit evidence, không sửa CPmetadata cũ.
- Final best export: fresh adapter+ownedAdam/initialbackbone match, inspect/restore actualCPf40/trainindex vàsameidentity; close restoredtracker, không thêmoptimizer; switch selectionindex rồi finalrawpredict. Hai freshcontainers làsame-process reload, không lifecycle/sessionresume. Resource counters không reset vì reload.

## Terminal đúng bằng chứng

Sau actualfullcoverage/reload/rawbest/checkpoint/epoch/source/input/postelapsed readback: write actualterminalkind MAIN_SELECTED_ONLY_CANDIDATE_V1 vàArtifactClaims SHA/size từ actualfiles, MainStage.begin_raw_best_selection()→finish_selected(claim). Giữ outputselection CSV chronological nhưproducer hiện hành. Canonical sortedK chỉ statisticalview ở downstreamadmission, không reordertraining/logs/history. Terminal không winner/externalfreeze/refit/calibration. Không tự gọi fitted thành công từ typedclaim; incompleteepoch/budget/source/error giữfailure, không acceptedterminal hoặc fallbackA0.

## Hai tests mới, không chạy trong prep

`test_research_main_execution.py`: wrongpilotauth/extra refitphases/noapprovedfile/source-runtime-Gate-input mismatch→reject trước model; closedidentity conditionalfile checks bằng ownedmetadata fixtures, không fabricatedactualPASS.

`test_research_selected_runner.py`: typedNOAUTH/callable refused trước lazyTorch; tiny mocked eventorchestration verifies per-epochselectionwhilefit, train-onlyoptimization, graphcollate/complete receipt, trainindex beforeCPsave, freshreload/selectionfinal andneverrefit/Tfit/oldpilot; no declaredactualfit from mocks. Native4update checkpointproof đã có chỉ là dependency, không thay actualmainresearch acceptance.

Đây là routineengineering concreteguard+producer, không đổi phương pháp/hyperparameters/split/matrix. Guard/sourcecompile/test/realbudget/actualfit chỉ ROOT dispatch sau source review. Existingauth.gate2_build_hashes:96–113 glob allroot/native/sharedtests/scripts, nên newfiles làm sourceGate cần refresh sau freeze; không tái dùng Gate cũ để thực thi nguồn mới.

