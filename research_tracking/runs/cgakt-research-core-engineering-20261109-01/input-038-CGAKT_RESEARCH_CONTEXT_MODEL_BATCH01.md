# Batch context/model CG-AKT theo26 — thiết kế file/API, chưa thực thi

Đọc26 SHA13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a.
Không sửa current154/source/test/Git, không Torch/model/data run. Condition do
graph agent sở hữu, đã freeze source6678f04c3c0b3655aa797edd3e491877d17ac3f0fa12f7dfc9971f637d875cf0,
chưa có executionreceipt trong audit này. Reuse ResearchGraphCondition,
prepare_research_graph_condition và bind_graph_neural_phase, không viết converter
confidence lần2. condition.kernel_confidence_kwargs() cung cấp legacykwargs;
consumer tạo EdgeConfidence ở data-context boundary có NumPy, giữ condition.identity
và edge_weights/support-null metadata riêng. A0/A1expert không giả Method24artifact.

## 1. File data context: research_graph_context.py + test tương ứng

API đề xuất:

```text
prepare_research_graph_context(phase: ResearchPhaseData,
    encoding: ResearchAKTEncoding, condition: ResearchGraphCondition,
    limits: explicit caller-supplied context cache limits) -> ResearchGraphContextIndex
index.for_windows(tuple[WindowInputs,...]) -> tuple[per-target QueryEvidence,...]
index.assert_integrity()
```

Data-only NumPy được phép, không import graph_prototype/graph_training hoặc
Torch. Dùng public iter_research_windows(training=False), không tự slice/re-anchor.
bind_graph_neural_phase nhận đúng phase_scope,encoding_sha256,vocabulary_sha256,
fit80_encoding_sha256,encoding_fit_scope,neural_shards_sha256 vàfreezeSHA nếu có.
Giữ hash vocabulary tách encodingidentity; refit90 encodingidentity mới dù item
values giống80. Fixed train80binding chỉ chứa hashes/corpus/domain/rolelineage,
không mất calibration separation vì có hash calibration_shard.
Index giữ source/phase/encoding/condition identities và immutable per-window,
per-query contexts; **không giữ phase/shards/trajectories/truthsidecar/fullcorpus**.
Các bảng số/readonly arrays và shared window rows có thể giảm nhân bản metadata;
không hứa memory/time trước đo. Limits về targets/parentrecords/bytes phải rõ,
không copy giới hạn toy4nodes/12events. Audit nguồn/phase ở cache boundaries,
không audit toànsource mỗi target/forward.

Mỗi query key gồm learner_id, source_row, global_rank, window_id. Lấy đúng
trajectory cùnglearner và observations[:global_rank], gọi existing pure
graph_context.audit_graph_context để lấy parent support/mean/observedrows,
effective_start và scoped_observations_sha256; không implement window geometry
hoặc aggregate nghĩa khác. Consumer model chuyển audited record sang existing
PreparedGraphContext/kernel sau lazyTorch. Không import graph_augmentation trong
purecontext vì module đó importTorch.

Bắt buộc match effective_start == global_rank − window.history_used[local],
source_row/query/item/window targetmask/encoding. Không dùng min(rank,context)
hoặc history_available thay history_used: sau OOV, hai trường có thể khác nhau.
WindowInputs.global_ranks/localpositions/canonical OOV barrier giữ nguyên. Query
OOV là ResearchUnseenTarget/null+reason trong fulltarget ledger, không graphrescue
và không đi vào native tensors. Current/future y không vào context của query đó;
past y có thể ảnh hưởng context các query SAU nó, đúng causal contract.
Fullphase SHA có thể đổi khi futurelabels đổi; numerical-prefix/p_t invariance
không đồng nghĩa toàn bộ phase hash phải invariant.

## 2. File model: research_graph_model.py + test tương ứng

Owned builder nhận validatedconfig/encoding/condition/index và expected initial
backbone identity, lazy build_native sau data/admission. **Không** khởi tạo qua
GraphAKTPrototype/_scope hoặc lấy engineeringcheckpoint. config.graph=False vẫn
đúng cho native NonRasch backbone; composition metadata phải ghi variant/26recipe,
không vì backboneflagfalse mà export nhãnA0. Không warmstart fittedA0.

ResearchGraphAdapter.native là registered nn.Module chứa backbone + scalaralpha
(A1–A3) +Linear4→1 gate(A3). Vì current runner hash/save/Adam/clip dùng
adapter.native.*, mọi branch parameters phải nằm trong subtree này. Alpha0,
gateweights/bias0, fixed centered messages không parameter. Constructbranch trong
forked CPU RNG hoặc constant-allocation path để không đổi native initialization/
dropout stream; native initialtensorSHA phải same recipe A0.

Active forward reuse pinned NonRasch six operations của graph_prototype._features:
q_embed →qa_embed(response)+q_embed →native.model →concat →native.out →logits.
Không hook upstream/detach/inverse-sigmoid, không rewrite attention. Dùng existing
apply_graph_residual với message[E,1]=(mu−0,5), readout alpha.view(1), gate1 hoặc
sigmoid gate4. Wholeoff/mass0 gọi native backbone trực tiếp trước branch math;
activealpha0 KHÔNG bypass. Mixedinactive lấy cùng-forward base probabilities;
không forwardnative lần2 dưới dropout. Return native(loss_sum,p,count) và optional
details chỉ cho telemetry. Training BCEWithLogits/targetmask/count giữ nguyên.

### Interface để train_epoch và runner reuse, không trainer thứhai

- `collate_training(tuple[TrainingWindow,...]) -> AKTBatch` phải trả **exact**
  existing AKTBatch: training.py:275 dùng type(batch) is AKTBatch. Lưu ONE-use
  sealed context ticket theo batchpayload/window IDs trong adapter, không trả
  GraphBatch thay type rồi nới validator.
- `step(batch,optimizer)` consume/check ticket; bind explicit per-call contexts
  vào native.forward(q,qa,targets) trong scope được finallyclear, rồi reuse
  **AKTAdapter.step** unbound để giữ loss/backward/clip/allparameters/optimizer
  primitive. Trước primitive phải verify optimizer sở hữu exact toàn bộ registered
  params/settings/instance, không suy ownership từ việc có param_groups.
  Không monkeypatch global/native method. Reject stale/foreign ticket;
  optimizerhooks/cumulative ledger vẫn do lifecycle sở hữu.
- `predict_windows(windows)` giữ signature hiện có: thin chunkcollate +explicit
  index lookup/bound per-call contexts, inference_mode/eval, restore modes,
  trả same-shaped arrays cho research_runner._predict. Không truthsidecar vào
  predictor; _predict vẫn join labels sau predictions và giữ nullOOV/fullkeys.
- Selecttrain/rawselection indices dùng encoding80; refit/calibration dùng90.
  Mỗi index chỉ của đúngphase, có thể attach một typed predictionindex khi đổi
  phase sau khi runner đã authorize; model không giữ fullphase. Refitdata dùng
  read-only bounded reloadprobe cũng hợp lệ, không nhầm thành rawselection mới.
- `_state_hash`/fullstate save tự bao branch nếu registered đúng. Adamstate vắng
  khi branchinactive là hợp lệ; participation không đồng nhất globalstep. Core
  này chưa promote fittedcheckpoint/OnlineSession hoặc cấp mainrefit authority.

Sau này publicphase split chỉ thay adapterconstructor/batch_factory/predictor
dispatch trong selected-only và refit-only entrypoints. Giữ existing train_epoch,
EarlyStopping, rawexport/rowkeys/evaluator/cumulative ledger; external systemfreeze
admission ở execution/lifecycle layer, không suy từ condition/index presence.
Checkpoint researchschema/strict reload là batch riêng sau core, không reuse tag
engineering hoặc gọi sourcecore xong là complete mainmatrix.

## 3. Fixture/native inventory đề xuất để ROOT duyệt SAU code

Puredata tests không model: canonical globalranks99/100/199/200, OOV tại102 để
kiểm t200 history_used khác available; current/future/peer perturbations, readonly
inputs, wrongkeys/phase/encoding/condition reject. Dùng existing typedpublicphase
fixtures; không fake Junyi folds hoặc đọc actualcorpus. Có thể có>2learners trong
metadata plan nếu existing publicvalidator cần, nhưng model chỉ nhận≤2learners.

Một nativefixture: researchconfig frozen geometry256/8/100+100, CPU FP32/thread2,
≤2windows/call, mỗiwindow≤200tokens; không tự dùng d32/dropout0 để gọi research
parity. Tạo **1 logical nativebackbone +1graphwrapper +1gate**, không duplicateA0
fittedmodel. Samebackbone controls, reset grad vàCPU RNG snapshot giữa pairedcalls:

| Thao tác | Forward backbone | Logical backward | Optimizer |
|---|---:|---:|---:|
| Nativecontrol |1|1|0|
| Graphoff, sameinputs/RNG; exact p/loss/count/backbonegrads |1|1|0|
| Allmass0, samecontrol; branchgradNone hợp lệ |1|1|0|
| Activealpha0, nondegenerate parentmessage; alpha finite nonzero, gategrad0 |1|1|0|
| Alpha assigned1 bằng fixture/no_grad, mixedactive/inactive; gategradient positivecontrol |1|1|0|
| Perturb current+future labels của một target, chỉ kiểm p_t/context_t |1|0|0|
| Perturb peerlearner, kiểm row còn lại độc lập |1|0|0|
| predict_windows inference/mode/weights read-only parity |1|0|0|
| **Tổng proposed** |**8**|**5**|**0**|

Assignment alpha1 là fixture mutation, không optimizer/training receipt. Không
đòi actualdatasets luôn nonzero gategrad/alpha hoặc lossimprovement. Native step
acceptance/Adam participation/checkpoint chưa chạy; không thêm optimizer trong
batch này nếu chưa ROOT cấp riêng. Ledger phải đếm logicalautograd.backward,
tách rawTensor dispatch entries, tránh lỗi observer doublecount cũ. Số constructor
nêu là model-level, không giả rằng chỉ3 nn.Module.__init__ nội bộ upstream.

Proposed resource: một ROOT-owned≤60s cumulative CPU check, minfree1GiB và
observedRSS cap do ROOT chốt trước chạy (512MiB chưa đo feasibility). Không GPU/
cloud/modelrun hiện tại. Exactinventory chỉ freeze sau source/tests thực sự tồn
tại và được review, không dùng bảng này làm actualreceipt hoặc authority.

Nguồn code đã đọc: research_simulator_data9596c2dc…092b;
windows e8d00ea0…2068; tensors688fb915…4867; model e40b068b…e9f;
trainingca074a15…f979; research_runner19627a1a…2092;
graphcontext3db94ec4…7264; kernel105aa918…ff08; prototype9fc6b827…157a.
