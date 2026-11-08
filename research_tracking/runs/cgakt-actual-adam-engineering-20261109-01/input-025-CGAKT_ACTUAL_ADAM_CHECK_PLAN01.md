# GRAPH10 — kế hoạch tối thiểu kiểm Adam thật (SOURCE-ONLY)

Chỉ đề xuất test mới `tests/akt/test_research_graph_optimizer.py`; platform_fixture_compat sở hữu file đó, ROOT review/dispatch. Không sửa production hoặc4file đang freeze; không import/execute/test/model/data/Git từ note này. Không checkpoint/resume, không framework mới và không fitted/RQ claim.

## Fixture và trần công việc chốt trước chạy

Reuse **normal import** `handmade()` của `tests/akt/test_research_graph_model.py`, không reload/alias module/classes. Fixture bank84items, observedvocab3,6events/window; ordinal0 là supportedc01 active, ordinal1 là unsupportedc02 confidence0 inactive. Typed artifacts là manufactured, không Method24actualfit hoặc corpus research.

Một A3adapter + một nativebackbone + một fresh `torch.optim.Adam`, rồi đúng ba minibatches:

| Thứ tự | Entry | Branch tham gia | Điều cần kiểm sau bước |
|---|---|---|---|
|1|`entries[1]`|Inactive/no observed confidence mass|Backbone gradient/update thật; alpha/gate grad **None**, chưa có Adamstate cho cả3branchparameters|
|2|`entries[0]`|Active lầnđầu, alpha vẫn0|Alpha finite/nonzero gradient và Adam làm alpha khác0; gate grad là **zero tensor** (khôngNone), weights/bias giữ0; Adam có thể/tại primitive hiện hành phải tạo gate-state|
|3|`entries[0]`|Active lần2, dùng alpha do Adam bước2 tạo|Gate weight có ít nhất1nonzero gradient/changed element, gatebias nonzero gradient và thayđổi; alpha/backbone finite; không manual `alpha.fill_`/assign để tạo signal|

Global native ceilings: **1adapter /1ResearchGraphNative /1upstreambackbone-Architecture constructor /1Adam constructor;3accepted `.step`;3forward và3Architecture.forward;3logical meanloss.backward;3clip_grad_norm_;3Adam.step;3×6=18validtargets**. Mỗi batch1×6; không extra prediction/native control/forward/backward hoặc inference model. GateLinear là1branch constructor bên trong A3; không đếm nó thành backbone mới. Logicalbackward không cộng trùng Tensor.backward và autograd.backward cùngcallchain.

`handmade.config.max_steps` đang1: test phải explicit `replace(...,max_steps=3)` cho resourceceiling; **không âm thầm bỏ qua cap1**. Không đổi d_model/heads/lr/betas/eps/dropout/batch/context/targetblock/maxepochs hoặc objective. Giữ `config.graph=False` validator guard; A3residual do typedcondition, không dùng field này làm côngtắcgraph. NonRasch nói về difficulty/Rasch parameterization, không giải thích graphmechanism.

## Assertions không được nhầm

- Trước constructor: kiểm entries[0]/[1] bằng sealedindex evidence, support/mass đúng và targetmask/validtarget mỗi entry6; domain/vocab/phase khớp. Nếu fixture changed thì STOP, không tìm entry khác theo gradient. Cùng trainindex và frozenA3condition qua cả3bước.
- Mỗi bước gọi `adapter.collate_training((entry,))` để tạo đúng ticket rồi `adapter.step(batch, sameAdam)`. Adam sở hữu mọi registeredparameter đúng mộtlần và đúng config lr/betas/eps/weight_decay; native `.train()`/CPUFP32. Ticket và nativecontext phải tiêu thụ/clear sau mỗi bước. Không gọi plaincollate thay graphticket.
- Inactive-first rất quan trọng: nếu chạy active trước rồi mới inactive thì không thể đòi branch Adamstate “absent”. Sau inactive alpha/gate vẫn constructorzeros, gradNone và key chưa có trong `optimizer.state`; không tự điền hoặc clear state để qua assertion.
- Sau active1, zero gategrad vẫn là tensor nên Adam tạo state/step cho gate dù weights không đổi (weight_decay0). Ghi rõ None/zero/nonzero; không gọi “gate chưa được optimizer thấy”. Sau active2 cần actualgradient và actualweight update, không yêu cầu mọi4gateweights nonzero vì feature variance có thể0.
- Ledger mỗiparameter: expectedAdamstep = số bước có `grad is not None`, **kể cả zero tensor**. Với3branchparams dự kiến counts0→1→2 qua ba bước, globalAdamsteps1→2→3; không đòi cùngmộtbackboneparameter tham gia cả3; chỉ đối chiếu participation thực tế và ít nhất1backbone update ởmỗi bước. So actual `.state['step']` với participationcount; missingstate chỉ hợp lệ khi participation0, tensors/moments finite và đúngshape. Không ép mọiparameterstep=3.
- Độc lập snapshot/compare backbone weights trước/sau từng bước để chứng minh ít nhất1backboneparameter thực sự đổi; `stats['parameter_updated']` chỉ probe mộtparameter có thể làalpha, không tự chứng minhbackboneupdate. Không đòi loss giảm hoặc metric cải thiện.
- Spy `clip_grad_norm_` chỉ record rồi gọi **original** đúng1lần/bước, restore trongfinally. Ghi đủ registeredparameterIDs, config max_norm/error_if_nonfinite, actualpre/post gradientnorm. Không chỉ tin `post_clip_norm=min(pre,limit)` trong returnstats vì đó không phải postnorm đo thật. Require finitepostnorm≤configthreshold+tolerance float32 định trước (ví dụ1e-5); **không đòi pre_norm>limit**, không scale loss/grad để ép clipping.
- `valid_targets=6`, `stepped=True`, finite loss/count/timing theo native primitive cả3bước; actualAdamcall/returned count3. Reserve3steps/18targets trướcbody; timeout/failure giữ attempts/returned/unknownpartial, không gọi0 hoặc rollback. Hooks không thay loss/optimizer/gradvalues; dùng no_grad/detach cho readouts, không tạo thêm backward.

Không thêm negativecase đòi constructorAdam/model thứ2 hoặc extra forward để kiểm quyền. Có thể kiểm source/data preconditions trước native trong cùngtest; mọi negativecall mới ngoài ceilings trên phải xin ROOT điều chỉnh scope **trước dispatch**, không tự tăng work để làmgreen.

## Tài nguyên và bằng chứng

ROOT đề xuất **một boundedwhole90s** gồm imports/fixture/construction/3steps/checks/persist/ownedcleanup; RSS≤1GiB và freeRAM≥2GiB (caps ROOT mới nhất chuyển qua author trước khi freezeplan) trước heavyimports và cácstage. Đây là protectivecap, không forecast. ExternalRSS1GiB/free2GiB chặt hơn fixtureconfigRSS2GiB/free1GiB; record cảhai và không đổi scientificgeometry để vừaRAM. Giữ config.max_seconds60 cho nativework bên trong whole90, không âm thầm nâng thành90. CPU/CUDAhidden; TorchCPU RNG/dropout theo seed42 là native initialization/training được đo, không teacher/world RNG. Có thể `fork_rng(devices=[])` để restorecallerCPU RNG; không CUDAquery/allocate/Modal/network/realdata.

Sourceauthor gửi testSHA + exactwork/counters/CLI cho ROOT trước run. Giữ failure/sourcebeforeafter/JUnit/log/ownedreceipt và batchparameterparticipation/clipping ledger. Nếu không đạt assertion hãy giữ nguyên, không thêm forward/retry/optimizerupdate. Completion chỉ nói actualAdam/kernel engineering, khôngselectedepoch/refit/calibration/mainmatrix. **Checkpoint ownership/restore là batch kế tiếp riêng**, chưa save/load checkpoint ở GRAPH10.

## Source pins đã đọc (không chạy)

- `tests/akt/test_research_graph_model.py`: `579359ff7b8ac64a75f9a343200724091d0d5b78af9a87e3d33ad023f1742ffc`; `handmade()` dòng30–94.
- `src/knowledge_tracing/akt/research_graph_model.py`: `77e365e4ffc6861f34a9ae05cbca947f057be967389f74f75bf5caacc7ee2397`; graphcollate307–315/ticket-Adamstep317–348.
- `src/knowledge_tracing/akt/model.py:24–65`: zero_grad(set_to_none=True), meanloss.backward, originalclip, actualAdam.step; parameter_updated làsingleprobe.

Pins mới của production/hotpath phải được ROOT/author xác nhận nếu khác; không tự gán PASS cũ cho nguồn mới hoặc sửa file hiện đang freeze.

