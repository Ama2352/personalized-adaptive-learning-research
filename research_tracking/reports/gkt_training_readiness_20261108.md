# GKT train-batch engineering: 45 CPU tests, chưa trainer nghiên cứu — 08/11/2026

**Một train-batch explicit trên recurrent candidate đạt45/45 tests, với4 Adam updates thực tế.** Pytest8,21giây; controller9,844604giây, không timeout. Mã mới chỉ ở [training.py](../../src/knowledge_tracing/gkt/training.py) và [test_training.py](../../tests/gkt/test_training.py); GKT recurrent/core/config, shared KT, AKT và protocol không sửa trong tiểu tác vụ này. Không corpus, dataset/Holdout, GPU/cloud, network/install hoặc full88-case GKT rerun.

## Hành vi có thể dùng ở bước kỹ thuật kế tiếp

[Plan trước code](../../artifacts/akt/local-tests/gkt03-training-preparation-20261108-01/PLAN.md) đã được parent duyệt. `bind_train_batch` nhận caller-owned IDs/responses/state, event mask và loss mask riêng, learner/source-row/global-rank identity, domain/vocabulary/node order/graph/recipe/source hashes. Không dataset loader, implicit vocab fit hoặc learner cache. Binding không chọn node=concept hay exercise_tag cho benchmark; toy binding khai báo domain riêng, không transfer Junyi→Grade10.

`train_gkt_batch` dùng nguyên `GKTStaticRecurrentCandidate.sequence.logits`: dự đoán query_t từ state trước khi observe response_t. Mục tiêu duy nhất được khai báo là `mean_bce_on_explicit_loss_mask`: cộng BCEWithLogits trên loss_mask rồi chia đúng số target được chọn. Loss mask phải là subset không rỗng của event_valid_mask; event chỉ nằm trong history vẫn được observe nhưng không thành target loss. Không tự chọn cold-target denominator hoặc OOV fallback; active node không biết bị reject. Các global ranks hợp lệ phải liên tiếp, bắt đầu ở caller history count; không tự sort/reconstruct missing history.

Model, native Adam và settings do caller cấp; tất cả optimizer fields được kiểm khớp. Một param-group phải chứa đúng toàn bộ registered trainable parameters một lần. Helper chỉ thực hiện tối đa1 update/call, không chọn epoch/best checkpoint, không shuffle, không khởi tạo model, không seed lại RNG và không đổi bất kỳ caller module training flag. CPU context bao forward/backward/Adam lazy state; FP32 hoặc FP64 phải được khai báo và khớp dtype. Default-device meta được thử trong happy update và không tạo model/state trên meta/GPU.

Giới hạn helper: B≤2 learners, N≤4 nodes, T≤12 events/learner, các widths≤8; caller budget≤8 updates/192 cumulative targets/60giây, một batch≤24 selected targets. Kiểm deadline trước forward, trước update, sau update và cuối hàm. Nếu vượt sau step, result là bounded, ghi đã tiêu thụ update/targets và không complete. Các trần này chỉ phục vụ toy engineering.

**State cuối là detached diagnostic snapshot được tính bằng weights trước update**, có `state_computed_with_model_sha256`. State đầu phải bind đúng current parameter digest; state cũ sau update bị reject cho đến khi caller recompute prefix hoặc reset phù hợp. Không tự carry stale hidden state, không implicit truncated BPTT hoặc gradients xuyên batch. Digest/state/source/budget là kiểm tra nhất quán cooperative do caller khai báo, **không nonresettable authorization**, không attestation learner history/synthetic origin/train-only graph. Caller có thể khai lại budget; helper không cung cấp run registry hay scientific data authorization.

## Bằng chứng thực tế và giới hạn test

| Kiểm | Kết quả trong fixture |
|---|---|
| Independent control | Cùng initialization; loss từ `logaddexp(0,z)−y*z`, norm clipping và công thức Adam first-step độc lập; so loss/count/parameter update FP64 đến1e−12. Control không gọi lại helper hoặc Adam.step |
| Happy update |1 actual update;6 selected targets/8 observed events; finite nonzero grad norm và parameter delta; không ép loss giảm hay hiệu quả dương |
| Caller contracts | Module flags hỗn hợp, Torch RNG, input/state/graph bytes giữ nguyên; state trả về detached/preupdate-bound; stale state reject trước forward |
| Padding control |2 actual updates, padded sentinel vs compacted events cùng6 selected targets; loss và parameter updates khớp đến1e−12 |
| Post-step timeout |1 actual update với clock stub; ghi bounded_after_update/counter1, không giả complete hoặc rollback |
| Negative guards | Role/synthetic/domain/vocab/graph/recipe/source/tensor drift, node/label/mask/row/rank/state/optimizer/settings/precision/geometry và exhausted budgets reject; spies kiểm trước forward/step ở các guard cases |
| Causality | Đổi current/future response không đổi score đến current timestep; không training corpus hoặc causal-learning inference |

Actual trial `parallel-gkt-training-20261108-01`: **45pass,0failure/error/skip**, JUnit và raw stdout/stderr giữ nguyên. Ledger ghi TRƯỚC mỗi Adam.step, tổng4, fail trước update thứ9. Five source/test hashes trước/sau invocation bằng nhau. Không independent reviewer agent cho gói này: **parent đọc source/tests và actual receipts rồi chấp nhận engineering contract**, không gọi đó là independent agent review.

Trước trial có controller-only compilation error: thiếu khoảng trắng trong `else0`, `SyntaxError` trước khi import/test/model/output directory chạy;0updates. Giữ failure JSON và stderr text ở `parallel-gkt-training-20261108-controller00`; không có full preexecution controller snapshot, không dựng lại bản đầy đủ. Controller sửa whitespace, source/test model không đổi. Tool shell wall diagnostic0,639312giây; dự trữ bảo thủ1giây, cộng trial9,844604giây thành **10,844604/60giây** cho ngân sách cumulative, không coi đây là thời gian training/throughput. Không có failed model/test invocation trong batch.

Command actual: project `.venv\Scripts\python.exe -B -m pytest tests/gkt/test_training.py -q -p no:cacheprovider`, exclusive basetemp/JUnit; CUDA hidden, OMP/MKL/OpenBLAS2. Full command/controller/runtime timings nằm trong [run receipt](../../artifacts/akt/local-tests/parallel-gkt-training-20261108-01/run.json). Archive chỉ copy/hash evidence, không rerun test/model.

| Tệp | SHA-256 frozen |
|---|---|
| `src/knowledge_tracing/gkt/training.py` | `6def666d82cf02dfefcf8980c2670ac24f3a137a86e9093e66cb87bc2cabc4e5` |
| `tests/gkt/test_training.py` | `1d4a9869d6b167e972c719df637b593171343e6d93fd55395925c7e0268392e0` |
| Actual run receipt | `aa48d1b448e989b9440688fec4553ece1437abee679528daa45693634aa407cc` |
| JUnit | `fb28194da01d7d4253075f1f9bfb6172a63b66fb5605a83472ad58e6667cca53` |

## Chưa được kết luận

Kết quả có role `synthetic_trained_engineering_only` sau actual optimizer step; đó không phải fitted research baseline hoặc chứng nhận predictive efficacy. Helper chưa có epoch/corpus runner, selection/refit, checkpoint/load/resume, fitted inference adapter, simulator bridge hoặc S05 adoption. Không serialize trained weights trong gói này. Exception sau step **không hứa rollback/checkpoint**; caller phải giữ failure evidence, model/optimizer có thể đã đổi. Cumulative counters/source bindings chỉ là cooperative contracts.

Recipe vẫn `gkt_static_recurrent_convention_v1`: unary erase-add specialization, Cho reset-before bias-free, normalization none/dropout0 là engineering convention đã khai báo; không tự nâng thành journal-BN/author parity. S04/S05 còn chờ node/item/multi-tag semantics, graph construction/training provenance/variants, history/capacity matching, cold/OOV/calibration, research optimizer/seeds/splits/selection/refit. Checkpoint weights-only và full optimizer/RNG recovery cần acceptance riêng; gói này không đóng các mục đó.

[Bundle bất biến](../runs/gkt-training-engineering-20261108-01/README.md) giữ plan, source/test, actual logs/JUnit/4-update ledger,10 before/after snapshots, controller00 failure và parent-review provenance. Manifest/input/output inventories kiểm SHA trước/sau copy; closure chỉ chứng minh integrity và engineering evidence trong phạm vi trên.
