# AKT A0/A1 graph prototype engineering — 08/11/2026

**23CPU tests passed,0failure/error/skip,4,35s**; controller5,3095642s, timeout90s. Không optimizer step, fit, checkpoint import, collector/simulation event, raw Junyi/Holdout, GPU/cloud hoặc dependency install. Đây là prototype **forward/backward thật** nối loss với native backbone và branch parameters, không phải detached inference residual; chưa full CG-AKT, chưa trained A1 hoặc kết quả RQ3.

## Phạm vi được duyệt và source

Chỉ thêm `src/knowledge_tracing/akt/graph_prototype.py`, `tests/akt/test_graph_prototype.py` và báo cáo này. Không sửa upstream/baseline AKT, graph kernel/context, trainer/config/shared interfaces hay artifacts cũ. Source mới làm Gate19 stale; parent review/refresh Gate20 riêng, không dùng targeted23cases làm current full gate.

Spec bắt buộc variant **A0 hoặc A1**, tag `engineering-observed-parent-mean-v1`, approval reference, `history_scope=effective_window`, `weight_role=engineering_only`. A2/A3 bị từ chối rõ ràng; không confidence estimator, gate network, calibrator/mastery threshold/controller/default research features. Message module/readout do caller cấp, trainable CPU FP32, nhỏ và không running buffers/stochastic dropout; A0 yêu cầu cả haiNone.

Chỉ CPU d32/head4/block1/d_ff64/final_fc32/dropout0, context100/target_block100/max_length200 của smoke hiện có; batch≤4. Bounds thực tế:≤8bankitems,4concepts,16edges,2learners/shard,12events/learner. Config/bank/encoding/graph có identity string/hash explicit; bank mang prefix `synthetic-akt-graph-engineering-`; chỉ train/selection observables. Không fake Junyi fold hoặc vào calibration/final/refit. CUDA available/initialized bị từ chối trước construction/forward; explicit CPU device context bảo vệ cả native constructor khi caller default làmeta, trả caller device/thread-count scope sau call.

## Đường forward và loss

Native pinned NonRasch `forward` chỉ trả loss/probability/count, không expose h/logits. Prototype **không** inverse-sigmoid, clamp probabilities để giả logit, detach loss, forward hooks, replace native head hoặc copy attention implementation. Active bridge gọi đúng sáu operations đã đối chiếu static với upstream:

```text
q_embedding = native.q_embed(q)
response_index = (qa - q) // native.n_question
qa_embedding = native.qa_embed(response_index) + q_embedding
h = native.model(q_embedding, qa_embedding)
concatenated = cat(h, q_embedding)
z = native.out(concatenated).reshape(-1)
```

Chỉ `n_pid=0`, `separate_qa=False`; loss active dùng masked BCEWithLogits sum/count đúng NonRasch, mask theo label>-0,9 sau kiểm label/mask hợp lệ. Không Rasch regularizer khác0. Đây là adapter cho **pinned revision**, không API chung mọi phiên bản AKT. Actual native source/commit/tree/remote/license/content được native constructor kiểm qua existing `verify_upstream`; không mock source/runtime cho positive native calls.

Whole A0/disabled/empty/no-parent-support gọi untouched `native.forward` và giữ nguyên native tuple values trước branch arithmetic. **No-parent-support khác OOV**: target ngoài base vocabulary được iterator xuất `SimulatorUnseenQuery`, không đưa embedding−1 vào model và graph không rescue. Mixed active batch dùng một bộ h/z; inactive positions chọn `base_p` từ **cùng forward**, không chạy backbone lần hai hoặc sigmoid(z+0) để thay base probability. Dropout0 là giới hạn prototype, không tuyên bố stochastic parity.

A1 fixed confidence c=1/g=1, source/provenance riêng cho declared graph; oracle/estimated confidence không được nhận ở prototype này. Message feature chỉ scalar `ParentEvidence.mean_observed_correctness` của parent đã quan sát. Unsupported parent có dummy input0 nhưng weight observed0 theo kernel; toàn bộ parent không support thì bypass trước message module. Reuse `prepare_graph_context` và `apply_graph_residual`, không viết lại phép cộng/normalization graph. Fixture message là Linear1→2, readout2, tổng **6extra trainable parameters**; weight/bias/readout constants ghi trong test để kiểm gradient, không là hyperparameters/main method đã chọn. Readout được phép0 hoặc signed, không bắt graph tăng score/benefit.

## Domain, causality và graph-aware batch

`prepare_graph_batch` nhận exact role-bound `SimulatorShard`, train-only `SimulatorEncoding`, config/graph và optional window IDs. Builder dùng actual `iter_simulator_windows` + collator; mỗi target lấy **full learner prefix[:global_rank]** cho existing context audit. Không re-anchor sliced prefix, không lấy qa[t] làm graph response feature, không ghép candidates thành fake practice. Native qa vẫn có response tại slot của nó theo existing collator; current slot được native strict-causal attention mask che. Target labels cho loss đi riêng, không vào message features.

Batch kiểm/bind actual q/qa, valid/target masks, source rows, global ranks/window IDs, query item, one learner/window, bank/item→concept mapping, vocabulary/graph/confidence/recipe/source identities. Graph nodes là **concept strings**, backbone IDs là **item vocabulary strings**: Grade10 đề xuất28concept/84items, còn toy chỉ4bankitems/3concepts (3items known). Không coi numeric indices hoặc shared tensor cardinality là Junyi↔Grade10 semantic crosswalk. Constructor tạo fresh native model, không có supported checkpoint import/transfer API; foreign domain/vocab/graph batch bị reject.

Model và batch có before/after source-identity checks: dynamic native AKT `.py` + root simulator_data/simulator_bridge/shared_kt + graph_context/graph_augmentation + actual pinned upstream `akt.py`, hiện **30+5+1=36files**. Batch identity gắn source digest; forward kiểm trước/sau native path. Payload/hash/dataclass binding là **consistency trong process**, không chống caller sửa toàn bộ metadata rồi reseal, không chứng thực nguồn history/weights/caller code độc lập hay atomic filesystem attestation.

## Những gì đã kiểm thực tế

Toy manually declared: train2learners×sequences6/4events =10targets, graph2edges A→C/B→C; selection có OOV itemz để kiểm suffix reset. Không gọi simulator environment để tạo outcome. Models là fresh random engineering containers, không có fitted metric/effectiveness claim.

| Nhóm kiểm | Bằng chứng và giới hạn |
|---|---|
| Pinned bridge | Native cloned initialization hashes giống nhau. Probabilities/loss/count khớp untouched native trong CPU/dropout0; full-off backbone gradients exact và branch gradientsNone. h/z chỉ kiểm source contract/shape/autograd, **không có native h/logit reference được bịa**. |
| Joint backward | Active loss có finite nonzero gradients tới actual native parameters, message weight/bias và readout. Backward không đổi parameter bytes vì0optimizersteps; không frozen/detached backbone. |
| Same-forward fallback | Mixed inactive probabilities bit-equal với base probabilities của cùng forward. A0, empty và graph-no-parent-support wholebatch khớp native và không gọi message module. |
| Causality | Đổi current/future outcomes không đổi probabilities≤current target; đổi loss labels chỉ đổi loss. Positive past-outcome perturbation làm subsequent score đổi. Không suy thành causal efficacy. |
| Mapping/independence | Explicit concept renaming + graph/bank remapping equivariant trong toy; foreign batch bị từ chối. Singleton/batched/padding so bằngabs1e−7; đảo windows kiểm exact trong fixture, không hứa bitwise batch equality mọi runtime. |
| OOV/global ranks | OOV query không vào native window; suffix globalranks4/5 giữ effective_start4 và chỉ history sau barrier. **Max12events<context100**: chưa empirical rollover qua full100 boundary hoặc overlapping100-step blocks. Existing window/context source được reuse; không nâng fixture cap để giả full-history proof. |
| Neutral condition | Zero readout được phép và giữ base probabilities; không test yêu cầu benefit/AUC tăng. Linear/readout có thể signed; không có research metric inference. |
| Negatives | Source/payload tensor/context/domain/vocab/graph drift, oracle metadata, unsupported A2/A3, dropout/history/device/domain mismatch và A0 branch params bị từ chối. Source mismatch được inject tại inventory reader, không sửa frozen dependencies. CUDA availability chỉ mock reject,0GPU. |
| CPU/meta | Real prototype constructors chạy dưới enclosing ambientmeta nhưng actual parametersCPU; batch/forward override metacontext và restore caller scope. Không CUDA/multi-platform acceptance. |

Tests chỉ mới `tests/akt/test_graph_prototype.py`, không chạy lại toàn existing graph/native suites hoặc full gate. Runtime positive paths dùng real pinned upstream; Git safe.directory là **process-only exact pinned path**, không global/repo config hoặc wildcard. Thời gian4,35s là software test wall time, không throughput/training cost estimate.

## Review, evidence và freeze

Pretest reviewer đọc source, không chạy model: xác nhận six-op path/current-future mask/full-prefix OOV geometry, phát hiện P2 thiếu behavior-source inventory và A0 cho đăng ký branch params chưa kiểm. Cả hai sửa **trước first test invocation**: source guards như trên và A0 yêu cầuNone. Không có observed pre-fix failed tests; không biến static finding thành red-test proof. Reviewer scoped pretest PASS trên final source/test trước run.

Evidence: `artifacts/akt/local-tests/parallel-akt-graph-prototype-20261108-01/` có `run_targeted.py`, physical source-before-trial01, pytest log/XML và receipt. Command: `.\.venv\Scripts\python.exe artifacts/akt/local-tests/parallel-akt-graph-prototype-20261108-01/run_targeted.py`; actual pytest `-B -q -p no:cacheprovider`, own basetemp, CPU hidden CUDA, timeout90s. Wrapper36file SHA before/after giống nhau (includes test, excludes upstream); model/batch identity36file set khác: includes upstream, excludes test. Không nhầm hai tập bằng nhau vì cùng count36. Không failed pytest trial hoặc failure bị bỏ; source/readiness freeze sau targeted PASS, parent handles archive/Gate20/index/Git.

| Final source | SHA-256 |
|---|---|
| `src/knowledge_tracing/akt/graph_prototype.py` | c7e9ce13a6225d60c550640b48c173275a6d5b353959eec133cd20b8c08afc84 |
| `tests/akt/test_graph_prototype.py` | 5e2aae220d1b862c337951182efab417a3ed81dd5eb6899f84af710a3cfd76ae |
| Pinned upstream `akt.py` | be2788c20cac602e86ef3a51e5294b37dd7b200f818be4e173dbd69069a3ec6d |

## Phần còn thiếu không được tự suy đã hoàn tất

Chưa `train_epoch` integration: existing collator `AKTBatch` không giữ đủ learner/global-rank/window/context metadata cho graph-aware step; prototype không registry-lookup/fake-fold để ép trainer dùng graph. Chưa optimizer/update, selected artifact/checkpoint/export, complete graph-aware simulator trainer hoặc production online backend. S04/S05 và architecture06 vẫn cần chốt feature/message/gate/normalization/primary history fairness, confidence operationalization/train-only estimator, calibration/mastery/controller, corpus/allocation/budget.

Chỉ A0/A1 engineering. A2 confidence/A3 learned gate và system selector chưa implement. g=0 trong một jointly trained A3 tương lai chỉ là same-backbone branch-off, **không** independently trained A0 checkpoint. System fallback cần selected A0 riêng/Dev criterion/provenance. Negative graph result không fail implementation acceptance, và forward/backward23tests không chứng minh learned graph/CG-AKT giúp người học thật.
