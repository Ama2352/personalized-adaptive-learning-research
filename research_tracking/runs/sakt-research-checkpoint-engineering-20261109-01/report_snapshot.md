# SAKT: kiểm thu persistence trạng thái huấn luyện cuối epoch

09/11/2026 · **Kiểm kỹ thuật CPU; chưa selected research fit.**

Một lượt targeted native do ROOT chạy đã đạt **31 tests,0failure/error/skip**. Gói mới lưu và khôi phục model, Adam, RNG và cumulative counters ở **ranh giới một epoch hoàn chỉnh**. Nó bổ sung khả năng persistence cần cho lifecycle SAKT về sau; không triển khai mid-epoch cursor, model selection, fresh refit90, response calibration hoặc full-corpus resume. Không sửa model, research-data, research-training hay checkpoint engineering cũ.

## API và ranh giới

Hai file mới là `src/knowledge_tracing/sakt/research_checkpoint.py` và `tests/sakt/test_research_checkpoint.py`. Caller cung cấp `SAKTCore`, optimizer, typed research view/spec, profile/protocol/runtime hashes, byte limits, actual epoch receipt và previous cumulative progress. `research_checkpoint_identity` loại object IDs khỏi portable identity nhưng giữ exact model config, optimizer class/groups/parameter names/settings, role/phase, encoding/vocabulary/bank, recipe/spec và source bytes. Profile protocol phải khớp protocol của view.

`save_research_training_state` chỉ nhận receipt complete với đúng population/order/counters, không pending optimizer update; model digest phải còn khớp receipt. Snapshot ở thư mục mới độc quyền, file được công bố không overwrite, `COMPLETE.json` viết cuối. Lỗi publication giữ `failure.json` và phần đã ghi, không rollback hoặc biến partial thành complete.

`restore_research_training_state` yêu cầu external COMPLETE SHA, expected identity và caller-owned CPU FP32 containers. Identity/source/role/metadata/byte caps/SHA được kiểm trước `torch.load(weights_only=True,map_location='cpu')`; model/optimizer tensor keys, shape, dtype, finiteness, cumulative state coverage, counters, RNG và modes được kiểm trước mutation. Module không tạo neural constructor, không đọc oracle/corpus paths hoặc gọi CUDA RNG. Restore có chủ đích thay Python/NumPy/CPU-Torch RNG bằng state đã lưu; không hứa giữ RNG hiện tại của caller hoặc rollback nếu native restore phát sinh lỗi.

Metadata giữ `restore_scope=completed_epoch_boundary`, `iterator_resume_supported=false`, `fitted_research_model=false`. Flag `resume_supported=false` của epoch API hiện có không bị sửa. Caller vẫn phải chọn explicit next-epoch spec/seed, giữ global budget, admission/runtime proof, phase/selection freeze và ownership; các hash/counter seals là consistency contract hợp tác, không chứng thực chống caller giả toàn metadata.

## Những gì đã chạy

Fixture in-memory dùng typed public-corpus/view từ test helper, với publication/protocol/profile hashes giả có nhãn; không đọc corpus thật hoặc chứng minh trained-vocabulary provenance từ file. Model kiểm có width4,1head,head_dim4,max_length3,dropout0,2; mỗi training call xử lý32handmade targets trong một batch. Đây là lựa chọn fixture, không research hyperparameters mới.

Một prefix epoch được chạy và lưu; model ban đầu chạy tiếp epoch2. Một container mới có parameter objects tách biệt khôi phục epoch1 rồi chạy cùng suffix epoch2. Tổng thực tế là **3 optimizer bodies**, do hai nhánh dùng chung prefix đã chạy; không đếm thành4updates hoặc4research fits. Tests đối chiếu exact model/Adam tensors, loss/ledger, restored RNG/modes và frozen prediction rows. Các negative cases không tạo thêm optimizer updates.

| Chỉ số quan sát | Actual |
|---|---:|
| SAKTCore constructors |2|
| Forward calls |5|
| Logical `torch.autograd.backward` calls |3|
| Adam constructors / step bodies |2 /3|
| `torch.save` / `torch.load` calls |11 /20|
| Model-state / optimizer-state restore calls |1 /1|
| JUnit cases |31PASS,0failure/error/skip|
| Pytest XML duration |18,096s|
| Child controller elapsed |25,9935879707s|
| Outer stored prepublication elapsed |27,7268235000s /90s|
| ROOT-reported terminal elapsed |27,729151999985334s /90s|
| Observed peak RSS / minimum free RAM |289.452.032 /4.483.698.688bytes|

Observer ghi reservation trước native body và body-return sau; started/returned khớp ở cả9counter fields. Chỉ logical autograd được đếm, không cộng lặp `Tensor.backward` dispatch. Owned Job đã cleanup, active processes sau cleanup0, handle đóng, terminal code0. CPU wheel `torch2.7.1+cpu`, NumPy2.5.4, thread2; nguồn/origins và env/method/thread restoration có raw receipts. Memory bounds là cooperative telemetry, không hard OS quota. Thời gian này không là throughput forecast.

**Chỉ Adam roundtrip đã chạy.** Source cũng kiểm format native SGD (momentum>0 cần đủ buffers, momentum0 dùng empty state), nhưng không có genuine SGD save/restore trong lượt này. Không suy SGD numeric equivalence hoặc cross-version/cross-platform replay từ31cases.

## Review trước chạy và hồ sơ lịch sử

ROOT source review phát hiện optimizer-state validation ban đầu có thể chấp nhận payload bị xóa toàn bộ Adam moments hoặc second moments âm. Sửa trước execution: với exact SAKTCore/all-trainable parameters, mọi parameter tham gia computational graph; Adam state phải phủ đủ mọi owned parameter, SGD momentum state phải khớp groups; second moments không âm và AMSGrad maximum không nhỏ hơn current second moment. Thêm missing-all/missing-one/negative-moment authenticated-payload regressions, không thêm update. Old module `7ab0c25f…` và tests `15e4f1cd…` được snapshot byte-exact; chúng **chưa được chạy**, không có failure test/runtime bị dựng lại.

Một STOP ở bước chuẩn bị packet trước đó phát hiện historical154-source reference không còn khớp hai file Gate do ROOT thay đổi. STOP này có0child/test/model. ROOT sau đó chỉ định `gate_collection02_packet.ROOT.json` SHA `04a4b8c0a0b860973b79e09f60e64515ba204be7ee3c15fe173bb526219d6192`, có cùng154members nhưng truthfully ghi hai source chưa commit. Controller targeted giữ154source bytes trước/sau; hai file SAKT mới được pin riêng. Đây là **source identity**, không fresh Gate approval. Reference154 là snapshot bảo vệ thời điểm targeted31, không yêu cầu worktree154 bất biến mãi: sửa CI của full Gate sau terminal31 được giữ riêng, không rebase allocation cũ hoặc chạy lại31 để đổi lịch sử. Gói chỉ kiểm child frozen-before==after==allocation;30component pins của SAKT giữ riêng. Verdict full Gate và sửa CI tiếp theo không thuộc kết quả ở đây.

Source đã kiểm: module SHA `1b0745951636ff967df0aed2a519cef153fe4aaa2dd5c3d4f8ecee6baf8cc4d3`; tests SHA `0d9c4942fb66671f37979fe355b3deacad4a3bff27df6e6884061b1bfef71466`. Source/training math/config cũ giữ nguyên; allocation bind30sources, lock và fixture helper. Không có actual research-corpus fit, selected baseline, calibration orchestration, GPU/cloud, Holdout hoặc RQ completion; **FES mới0**.

## Bằng chứng và phần còn thiếu

Bundle dự kiến [`sakt-research-checkpoint-engineering-20261109-01`](../runs/sakt-research-checkpoint-engineering-20261109-01/README.md) giữ source đúng từng revision, raw JUnit/log/journal/count/resource/owned receipts, STOP và freeze metadata. [Outer receipt](../runs/sakt-research-checkpoint-engineering-20261109-01/native_owned__final.json), [child receipt](../runs/sakt-research-checkpoint-engineering-20261109-01/native_child__result.json) và [ROOT terminal transcription](../runs/sakt-research-checkpoint-engineering-20261109-01/root_terminal_observation.json) có scope phân biệt. Links là alias dự kiến để materialize khi ROOT duyệt closure; báo cáo này không tự đóng bundle. Checkpoint binary không copy/commit; chỉ metadata/COMPLETE và SHA references của fixture gốc được giữ, không đóng gói cache hay mọi negative-payload duplicate.

Để có baseline SAKT dùng trong nghiên cứu vẫn cần actual admitted corpus/profile/source/runtime/Gate và finite execution budget; selected-fit/raw-selection/freeze→fresh-refit/calibration lifecycle cùng global accounting. Nếu cần resume giữa epoch phải thiết kế/kiểm actual sampler cursor và pending-step semantics riêng; khả năng restore cuối epoch ở đây không đủ để tuyên bố điều đó. Protocol tham chiếu: [lifecycle22](../../docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md).
