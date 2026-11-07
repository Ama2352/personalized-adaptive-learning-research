# GKT Batch A: kernel static message/readout — 08/11/2026

## Kết quả và ranh giới

**43 CPU tests passed trong1,96s**, controller2,827425s, timeout120s; JUnit0failure/error/skip. Đây là lần targeted đầu tiên, không có failed test trial trong batch này. Source/tests đã freeze sau PASS. Không optimizer step, train, model fit, simulator events, realdata/Holdout, GPU/cloud hoặc dependency install.

**GKT vẫn INCOMPLETE.** Chỉ có aggregation, static directed-message arithmetic và node readout. Không `G_ea`, h0, GRU/recurrence, normalization, MLP architecture, difficulty feature, trainer/checkpoint/export hoặc shared `SequenceKTModel`/`OnlineSession` bridge. Không xem43tests là efficacy hoặc tiến độ hoàn thành RQ. S04/S05 chưa được adoption từ implementation này.

Phạm vi do parent duyệt từ [source audit/core plan](gkt_source_and_core_plan_20261108.md), [provenance JSON](gkt_source_and_core_plan_20261108.json). Nguồn equation-level: [primary workshop manuscript](https://rlgm.github.io/papers/70.pdf), §2.1–2.2 Eq.(1)–(2), và [journal tác giả](https://journals.sagepub.com/doi/10.3233/WEB-210458), §3.2–3.3. Không port code/checkpoint `jhljx/GKT`, không gọi đây là author-code reproduction.

## Các tệp mới

| Tệp | Vai trò |
|---|---|
|[config.py](../../src/knowledge_tracing/gkt/config.py)|`GKTKernelConfig` yêu cầu explicit N, state/embedding/message dims, adjacency kind, node unit và zero-diagonal/nonnegative flags. `GKTBinding` giữ domain, declared vocabulary SHA, ordered unique node IDs; tính node-order SHA từ canonical JSON.|
|[core.py](../../src/knowledge_tracing/gkt/core.py)|`StaticGKTKernel`, Dense factory, actual adjacency digest; pure aggregation/message/readout với caller tensors.|
|[__init__.py](../../src/knowledge_tracing/gkt/__init__.py)|Chỉ export isolated GKT module; không sửa root/shared/native AKT exports.|
|[test_core.py](../../tests/gkt/test_core.py)|43 synthetic cases theo known-answer và negative contracts; không training loop/optimizer.|

Không có batch modules khác được tạo. Source/shared APIs, existing SAKT và native AKT không sửa trong gói này.

## Hành vi đã implement

1. **`dense_adjacency(N,dtype=...)`:** diagonal0, off-diagonal1/(N−1). N≤1 từ chối vì chưa có convention cho Dense singleton. Static matrix nhận nguyên weights caller, không tự normalize, symmetrize hoặc yêu cầu DAG. Batch A chỉ chấp nhận finite nonnegative zero-diagonal CPU FP32/FP64 và fixed adjacency không requires-grad.
2. **`aggregate_after_observation`:** state `[B,N,H]`, answered IDs `[B]`, observed responses binary `[B]`; lấy interaction embedding tại `i+r*N` cho answered node, concept embedding cho nodes khác rồi concatenate state. Không cập nhật state. Embeddings do caller đưa, không có random initialization hay fit bên trong core.
3. **`combine_messages`:** caller đưa `f_self`, `f_out`, `f_in` **đã tính** dưới dạng tensors. Kernel ghép `A[i,j]*out[i,j] + A[j,i]*in[i,j]`, thay answered-node message bằng self message. Trả values và support mask gồm answered node hoặc cạnh incident khác0. Mask này chỉ mô tả graph support, chưa chọn sparse recurrent-update semantics.
4. **`readout`:** caller state + query ID + common weight vector + per-node bias, trả logit và sigmoid. Signature không nhận current answer. Output role luôn `caller_tensor_kernel_no_fit_attestation`; không có fitted artifact claim/fit path.

Binding được so ở từng call: domain/vocabulary/node order/node-unit và expected actual adjacency SHA phải khớp constructor. Constructor copy A để original caller mutation không đổi graph đã bind; internal matrix drift bị hash check phát hiện. SHA matrix bao gồm dtype/shape/actual contiguous bytes. Đây là identity consistency, **không xác thực graph/vocab đã fit train-only** hoặc metadata do caller khai đúng nguồn.

IDs chỉ known0..N−1, không có padding/OOV/multi-concept convention; invalid IDs bị từ chối, không tự phát fallback score. Không thêm implicit difficulty hoặc map item84↔concept28. Caller chọn rõ `concept` hoặc `exercise_tag`; điều đó chưa tự duyệt representation cho benchmark.

## Bằng chứng targeted

| Kiểm | Kết quả và phạm vi |
|---|---|
|Incoming/outgoing asymmetric|3-node fixture answered node1: messages kỳ vọng **[27,5,102]**, từ hai trọng số chiều độc lập. Chặn nhầm transpose hoặc gộp hai chiều.|
|Dense|N2/3/5 đúng diagonal/off-diagonal/row mass; matrix “Dense” khác formula bị reject; không normalize âm thầm.|
|Aggregation|Hai learners, IDs/responses khác nhau: answered concept được ghép đúng response hiện đã quan sát; các neighbor giữ concept embedding.|
|Readout|Known answer logit2,5; current-response keyword bị `TypeError`. Đây là signature/state-local arithmetic, không chứng minh state caller chưa rò nhãn.|
|Batch independence|Aggregate/combine/readout trên B2 khớp hai calls B1; đổi state learner thứ hai không đổi score learner thứ nhất. Chỉ nghiệm thu arithmetic trong kernel.|
|Finite gradients|Backward qua caller state/embeddings, toy caller transforms, messages và readout có finite nonzero gradients; **0 optimizer steps**.|
|Immutability|Caller graph/state/embedding/IDs/responses giữ bytes sau aggregate/readout; original A đổi không tác động graph copy trong kernel. Source SHA trước/sau invocation giữ nguyên.|
|Negative contracts|OOV/negative/float/wrong-shape IDs; invalid binary responses; wrong geometry/dtype/nonfinite; self-edge/negative/trainable adjacency; domain/vocab/order/unit/graph mismatch; internal graph drift đều bị reject.|
|Disconnected/empty graph|Message không support bằng0; mask không đánh dấu node đó. Không chạy gate/GRU nên chưa là kiểm “unrelated recurrent state unchanged”.|

Positive numerical fixtures dùng **CPU FP64**, `torch.testing.assert_close` với default tolerance theo dtype. FP32 được validation/API hỗ trợ nhưng không có một bộ positive FP32 equivalence riêng trong lượt này; không claim bitwise/parity mọi dtype/kernel. Không CUDA/throughput/peak-RAM measurement. RNG fixture dùng forked seed42 và1CPU thread, trả caller thread setting sau test; đây là fixture convention, không training seed được chọn.

## Evidence, invocation và freeze

Lượt đã lưu: `artifacts/akt/local-tests/parallel-gkt-core-20261108-01/`.

- [pytest.log](../../artifacts/akt/local-tests/parallel-gkt-core-20261108-01/pytest.log), [JUnit XML](../../artifacts/akt/local-tests/parallel-gkt-core-20261108-01/pytest.xml), [run.json](../../artifacts/akt/local-tests/parallel-gkt-core-20261108-01/run.json) ghi exact command, timeout, duration, source SHA trước/sau và pre-copy/copied snapshot SHA.
- Bốn source/test snapshots nằm cùng attempt; không gán source thay đổi về sau cho kết quả43cases. Không sửa/xóa attempt đã PASS.
- Wrapper standard-library gọi project `.venv\Scripts\python.exe -B -m pytest tests/gkt -q -p no:cacheprovider --basetemp <attempt>/tmp --junitxml <attempt>/pytest.xml`, `subprocess.run(timeout=120)`, `PYTHONPATH=src`, `CUDA_VISIBLE_DEVICES=''`, `PYTHONDONTWRITEBYTECODE=1`, `OMP_NUM_THREADS=1`.

Khi chạy lại phải chọn attempt/output path mới; không ghi đè logs/JUnit/basetemp. Không chạy broad suite mới trong batch này; targeted source additions có thể cần parent refresh source-bound gate tùy inventory của gate, không tự đổi gate pointer.

## Những acceptance chưa có

Kernel stateless không thể chứng minh caller đã query trước observe, state thuộc đúng learner hoặc labels có training provenance đúng. **Caller phải điều phối readout trước khi cung cấp current response**, giữ history/metadata đúng learner/domain, và tính các input messages bằng transformations độc lập, không đọc oracle/current label khi query. Một caller transform có BatchNorm/peer aggregation có thể phá end-to-end isolation dù pure combine vẫn độc lập; kernel không attest transformation đó.

Chưa có sequence input wrapper, causal prefix/step-vs-sequence test, padding behavior, first-target accounting, fitted scores, selected epoch, optimizer/resume hoặc model/domain checkpoint proof. Không gọi readout độc lập này là complete online prediction adapter. Chưa implement full recurrence bằng cách thay G_ea identity, chọn h0 hoặc đưa support mask vào GRU. Các ambiguity trong source audit vẫn giữ.

Tiếp theo cần parent review Batch A; reviewer chốt explicit full-core convention hoặc lấy thêm author specification cho G_ea/h0/normalization/masking trước mức B. GKT tiếp tục là required comparator; thiếu author code không cho phép bỏ baseline hoặc tự dùng unofficial port làm standard. Training graph method, capacity, history information matching và model–environment allocation vẫn S05; mastery/calibration/controller vẫn S04.
