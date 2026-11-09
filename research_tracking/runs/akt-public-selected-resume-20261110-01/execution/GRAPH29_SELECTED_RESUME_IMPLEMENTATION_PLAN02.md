# GRAPH29 — patch plan complete-epoch selected resume

Ngày09/11/2026. SOURCE-ONLY, chưa sửa canonical/import/test/native/Git hoặc đọc actual corpus. Kế thừa contract01 SHA `555d1af8ed5e7ada238121bc9db274c85b3eab98feadf833f1a4882ddc5a5e98`. Chốt phạm vi triển khai đầu là intentional pause ở complete epoch, cùng candidate A0–A3, nguồn/runtime/Windows CPU FP32 và numerical identity. First implementation từ chối CUDA profile, Linux parent chưa có process-terminal verifier và parent legacy chưa có pause protocol. Giữ các RQ, train80/selection10, recipe26 và candidate population hiện hành.

## Batch canonical nhỏ nhất đề xuất

| File | Delta cụ thể |
|---|---|
|NEW `akt/research_selected_resume.py`|Closed request/pause metadata, kiểm paths/bytecaps/hashes/history/parent terminal, writer sidecar và immutable file references. Không top-level Torch/import model, callback factory hoặc execution grant.|
|`akt/research_main_execution.py`|Thêm public resume admission và nhánh authorization schema riêng có typed resume binding; reuse actual source/runtime/Gate/corpus/condition checks. Fresh factory và fresh authorization wire giữ nguyên.|
|`akt/research_selected_runner.py`|Factor loop/finalize từ entry hiện có; nhận internal verified resume state, seed cumulative counters/time, next_epoch và stopper/history; intentional pause và latest CP tại boundary. Default fresh path vẫn cùng behavior/wire.|
|NEW `tests/akt/test_research_selected_resume.py`|Pure tmpFS wire/lineage/budget/publication negatives.|
|`tests/akt/test_research_main_execution.py`|Closed resume authorization, actual common guard ordering và reject trước constructors/deserializer.|
|`tests/akt/test_research_selected_runner.py`|Mocked loop/state/stopper/finalization integration và fresh CPU compatibility.|

Giữ `research_graph_checkpoint.py`, graph math, `training.py`, MainStage, AKTConfig và old recovery/resumable nguyên trạng. Sidecar mới bọc CP hiện có; không đổi các low-level flags `selection_state_saved=False`, `global_budget_saved=False`, `lifecycle_resume_supported=False` hoặc CPU schema1. Các flags đó tiếp tục mô tả riêng tensor CP. Wrapper receipt mới mô tả selected lifecycle continuation.

## API và authorization

- Public fresh entry có optional keyword `pause_policy=None`; khiNone, trả SelectedCandidateClaim và giữ terminal behavior cũ. Typed policy chứa deterministic `pause_after_complete_epoch`, original allocation ID và finite lineage limits; nó là input, chưa là permission.
- Public `run_main_selected_resume(spec,evidence,*,resume_request,authorization_file,expected_authorization_sha256,pause_policy=None)` gọi genuine new resume factory một lần. Không nhận supplied execution token, verified bool, model/optimizer/corpus/sampler callback.
- `SelectedEpochResumeRequest` chỉ chứa fixed ROOT-relative parent boundary/marker/outer receipt references và external byte SHAs, original allocation identity cùng attempt ordinal. Không nhận serialized Python objects. New factory tự tạo internal verified pause object sau disk/current-state checks; caller không tạo được object này bằng constructor công khai.
- Existing fresh auth closed fields/decision giữ nguyên. Nhánh resume cần decision riêng `AUTHORIZE_BOUNDED_MAIN_SELECTED_COMPLETE_EPOCH_RESUME` và closed `resume` subrecord bind request SHA, exact parent accepted receipt SHA, original envelope SHA, child run/output, attempt ordinal, maximum attempts và cumulative caps. Không dùng approval_reference string hoặc một SHA đơn lẻ làm quyền resume.
- Reuse common actual admission implementation trong private internal function, không đưa callback ra public. Fresh public entry luôn truyền mode fresh và còn từ chối existing output. Resume public entry kiểm policy/request/auth rồi chạy cùng actual runtime/source/Gate/public reader/condition checks cho child output mới. Stage vẫn đi `begin_selected_fit` và `epoch_validation_inputs`, không thêm refit/calibration transition.

`MainSelectedExecution.revalidate()` hiện gọi hardcoded fresh `_auth`. Nhánh mới phải giữ internal resume binding do factory tạo và revalidate đúng resume auth/parent immutable refs mỗi boundary; không tạo object rồi để lần revalidate sau quay về fresh schema. Common resource checks cũng phải áp parent charges trước và sau actual source/data admission, không đợi `_Run` tạo xong mới biết remaining wall đã hết. Các internal fields mới không đổi public spec serialization hoặc fresh default wire.

Parent và child giữ cùng matrix context/candidate, TRAIN80 condition/confidence, corpus/DONE/bank/plan/roles, encoding/support, geometry, optimizer/seed, checkpoint profile và source map. Whitelist chỉ khác run_id/output_dir cùng các metadata trực tiếp dẫn xuất từ hai trường này, như child config/spec SHA. Runtime receipt/profile phải compatible exact CP identity. Có thể dùng genuine Gate index mới cho cùng actual build nếu common public Gate reader xác nhận full source map bằng nhau; không loại Gate fields theo tên rồi bỏ kiểm build. Parent tạo từ nguồn trước patch resume không được migrate hoặc sửa metadata để nhận.

Giữ `config.recovery=None`. Không tận dụng trường generic recovery vì nó vẫn nằm trong numerical CP identity và dùng payload/collator khác. Linux CPU cần verifier cho genuine owned-process terminal riêng trước khi mở scope; không chuyển nhãn Windows Job0 thành Linux cleanup proof.

## Latest, best và storage

Latest là optimization state sau complete trainE và raw selectionE. Best là checkpoint của B được actual EarlyStopping chọn, B≤E. Resume E+1 chỉ từ latestE. Final raw export reload bestB. Không suy latest từ best, mtime/glob hoặc optimizer step number.

Giữ checkpoint-on-improvement như hiện tại. Bản đầu chỉ nhận pause tại epoch đã khai trước entry. Khi tới pauseE, dùng CP bestE nếu E vừa cải thiện; nếu bestB<E thì lưu thêm latestE đúng một lần. Không lưu thêm latest tensor checkpoint ở mọi nonbest epoch khi chưa có pause yêu cầu. Vẫn ghi durable complete-epoch metadata mỗi epoch. Đây là phần thu hẹp contract01 để giới hạn IO; nó không cung cấp unexpected-crash recovery giữa các pause points.

Pause chỉ xảy ra nếu E<max_epochs và stopper chưa dừng. Nếu pause point trùng natural early-stop/max_epochs thì chạy existing finalize path, trả terminal selected claim và không tạo resumable parent. Consumer từ chối history đã dừng nhưng tự nhận pause. Không cần thêm finalize-only resume mode trong batch đầu.

Latest và best có thể trỏ cùng ba CP files. Parent paths bất biến. Nếu inherited best vẫn được chọn khi child finalize, copy đúng ba file state/metadata/COMPLETE sang directory mới của child bằng byte-preserving existing helper sau path/cap checks, giữ relocation inventory before/copy/after. Không serialize lại để thay producer/run metadata. Nếu child đã tạo best mới thì dùng CP child đó. Output quota phải reserve cả copy best và latest-at-pause; parent retained bytes và child new bytes có scope riêng, cumulative retained quota vẫn cộng cả hai.

## Boundary wire đề xuất

Một owned directory `selected-pause/epoch-E` gồm ba small JSON files và marker cuối, mỗi file exclusive, có bytecap/hash/readback/fsync. Tensor CP nằm trong `checkpoints/epoch-E` như hiện tại.

| File | Nội dung đóng |
|---|---|
|`state.json`|schema/version/kind, candidate/context/semantic identity, current invocation/root allocation, epochE và next_epochE+1, latest/best CP references, initial model/backbone, phase/encoding/condition bindings, stopper fields và parent lineage.|
|`history.json`|Continuous rows1..E với exact original epoch JSON path/SHA, complete receipt, raw selection summary/objective, semantic prediction SHA, selected epoch và checkpoint meaning. Inherited rows giữ nguồn gốc, không tính lại selection từ calibration.|
|`accounting.json`|Logical committed prefix steps/targets, actual child-local deltas/constructor counts, charged training duration, cumulative retained/new bytes, whole allocation caps; journal exact byte length/SHA và final counter snapshot.|
|`COMPLETE.json`|Status `PAUSED_MAIN_SELECTED_COMPLETE_EPOCH`, epoch, hashes của đúng ba JSON files và latest/best CP refs. Marker được viết sau mọi durable input/output checks. Chưa là selected success hoặc execution grant.|

Producer trả typed pause reference rồi chạy cleanup bình thường. Parent outer sau terminal/reap/Job0 mới ghi authoritative accepted pause receipt, bind marker/directory/full journal hashes, actual source/runtime pre/post, no postwrite rejection, final worker counters và charged elapsed. Consumer cần external ROOT SHA của receipt này. Journal có optimizer reservation/body/commit sau boundary, tail bytes, pending ticket/tracker, failure.json, incomplete CP hoặc thiếu terminal cleanup đều reject. Marker tự nó không đủ.

Stopper replayer dùng chính `training.EarlyStopping.observe`, không viết công thức chọn best khác. Pure first-pass metadata validation kiểm order1..E, finite values, objective/fields/caps trước lazy tools; replay actual class sau genuine admission và trước model constructor/deserializer. So exact patience/min_delta/best_epoch/best_loss/stale_epochs/last_epoch. Giữ strict `< best_loss-min_delta`, tie giữ epoch sớm. Do training.py import Torch, không quảng bá stopper integration là stdlib-only.

## Loop và cumulative accounting

Factor internal loop nhận fresh-state hoặc verified resume-state. `_Run` fresh vẫn khởi tạo0. Resume seed ba steps và ba targets bằng equal clean parent prefix; seed training_spent bằng charged parent training duration. Event vẫn dùng cumulative tracker counters. Child-local reserved/returned/committed được tính bằng cumulative minus immutable parent offset, không đếm parent prefix thành work mới.

Restore tracker từ CP có cumulative participation/steps/targets (`research_graph_checkpoint.py:835–840`). Seed `_Run` trước khi event sink được attach/restore phát event. Không gọi tracker.begin_epoch(E) hoặc gán `_optimizer` ở runner. Sau genuine construct, inspect/restore bằng existing CP API; restore đặt3RNG+modes cuối. Trước next optimization, không reseed hoặc construct thêm model. Các input/index/source/history checks phải hoàn tất trước restore; sau restore chỉ cho RNG-neutral guard/logging và phải có witness test.

Restore phát trực tiếp `verified_epoch_state_restored` với `optimizer_body_returned`, khác `_emit` events có `started/body_returned`. Cần sink bridge riêng cho đúng event restore này, kiểm count bằng seeded prefix rồi ghi `latest_reload`; mọi `_emit` optimizer/complete-epoch events tiếp tục vào `_Run.optimizer_event`. Không truyền thẳng sink cũ cho restore vì nó sẽ truy cập missing `started` key. Bridge phải tồn tại suốt tracker lifetime và không đổi counters cho restore event.

Iterator tiếp tục existing `train_epoch` và `iter_research_windows` với epochE+1. `training.py:94–109,326` dùng private Random(seed+epoch), buffer1024. Complete epoch không cần cursor hoặc loader RNG mới. Giữ custom `batch_factory`; không truyền `recovery` vì `train_epoch` từ chối kết hợp đó.

Global wall charge lấy duration từ authoritative parent outer, không hiệu monotonic timestamps giữa process. New `_Run.guard` kiểm parent charged wall + actual child wall≤original cap, parent training + current training≤original cap, cùng remaining steps/targets/output quota. Existing actual guard vẫn đo RAM/fresh invocation, không dùng snapshot cũ. Parent outer duration bao gồm reads/construct/selection/save/hash/cleanup; không cộng trùng child duration vào outer duration. Nếu chỉ có conservative cap charge đã được ROOT approve thì ghi rõ cap-charge, không giả nó là measured elapsed.

Một intentional pause thêm fresh constructors. Với một parent pause và một resume-finalize, physical lineage cần1parent+2child=3model/Adam constructors, trong khi continuous fresh run cần2. New authorization phải khai finite attempt/constructor caps đó, không reset hardcoded2 per attempt thành global2. Bản đầu giới hạn một resume child, attempt ordinal2 và explicit child run/output. Hai Root-approved children khác nhau là hai physical branches, không tự nhận là một trajectory hay hứa nonresettable authorization. Chỉ một request không tạo được quyền fork.

## Existing recovery tái sử dụng được đến đâu

Reuse `filesystem.publish_new_file` cho exclusive final publication và `recovery.preserve_checkpoint` cho opaque byte copies sau strict ROOT alias/cap/destination checks. Parent được giữ read-only, chỉ cleanup temporary owned files theo pattern đã review.

Không gọi `recovery.validate_source/publish_envelope` trực tiếp. Chúng chấp nhận failed/incomplete/bounded parent, có input projection bỏ Gate refs và schema single recovery checkpoint; chưa mang selected history/stopper/best/latest/named GraphAdamParticipation. Không dùng `resumable.train_resumable_epoch` hoặc generic recovery checkpoint payload cho graph tracker. Chúng đổi collator/sampler/recovery path trong khi current train_epoch cấm custom batch factory+recovery. Không sửa chúng để mở một generic infrastructure layer.

## Tests và finite native proposal

Trước canonical implementation, ROOT chốt đúng sáu file ở bảng đầu và source snapshots. Gói test dự kiến khoảng24–32physical cases, exact count chốt sau source freeze. Không gọi con số dự kiến là PASS.

1. Pure tmpFS wire cases kiểm missing/extra/duplicate epoch, wrong latest/best epoch, bytecaps/hash/aliases, tail journal, marker/failure conflict, partial reservations, fake terminal/Job, source/runtime/corpus/profile mismatch, exhausted wall/training/step/target/disk quota và attempt/child run mismatch. Constructor/deserializer spies phải0 ở negative paths.
2. Runner metadata integration dùng actual EarlyStopping cho improvement/tie/min_delta/patience/best≠latest, inherited prefix+nextE và no counter reset/double-count. Batch này có thể import Torch qua training.py nhưng0NN constructors/backward/optimizer; cần ROOT profile riêng. Fresh default entry compatibility và authorization schema cũ vẫn có regressions.
3. Failure injection trước CP marker, trước state/history/accounting, trước pause marker và sau marker nhưng trước outer acceptance. Giữ owned partials/failure receipt. Chỉ clean intentional pause+authoritative final có thể nhận; unexpected crash, missing final/cleanup hoặc activity sau boundary vẫn UNKNOWN/non-resumable.
4. Native lower-level regression sau metadata acceptance dùng fixture hiện có8train windows/48targets, two24target batches/epoch. Continuous pauseE2 so với parent pauseE1→fresh-process child pauseE2 cho4physical epochs,8Adam/backward/clip bodies và192train target exposures. Ba fit containers/Adam; không fresh-best reload ở các pause terminals. Mỗi epoch có một selection pass trên handmade raw-selection phase; với1learner×6events dự kiến thêm4forward passes, tổng12Architecture forwards, nhưng exact shape/count phải được controller source freeze xác nhận trước allocation. Bốn latest/best checkpoints tối đa, một successful latest restore; so model/Adam/participation/RNG/modes/stopper/history/ordered batches tạiE2. Không ép loss direction hoặc native best≠latest. Pure branch fixture kiểm best≠latest nếu native losses cùng cải thiện.

Native lower-layer fixture chưa chứng nhận public file admission hoặc final selected export. Sau đó cần một ROOT-reviewed bounded normal public entry test từ existing accepted engineering10×84 corpus, không recollect teacher. Giữ20max_epochs/patience recipe và predeclared pause1/2 thay đổi operation schedule. Continuous2 + parent1 + resumed1 là4physical epochs,8updates nếu actual8train windows vàbatch4,2.688training targets nếu train8×84. Chỉ dùng con số này khi actual public reader/window enumeration xác nhận đầy đủ; không suy từ tên corpus. Các pause terminal chưa là selected claim. Full natural finalize/raw-best export parity của admitted resumed producer còn phải có kiểm riêng trước long paid readiness; không dùng eight-update prefix proof thay thế.

Wall/RSS allocation native chưa được duyệt trong plan. Existing checkpoint CPU06/GKT compute nguồn đang pending RAM/Root review. Không tự cộng native quota hoặc suy throughput từ tiny core. Fresh current Gate và actual guarded inputs vẫn bắt buộc cho public admitted run sau source change.

## Giới hạn còn lại

Patch này không giải quyết replay/rollback partial epoch, unexpected crash after marker without final accounting, source-version migration, device/CPU→CUDA transition, full producer CUDA resume hoặc refit/calibration. Một pause marker có thể tồn tại trên đĩa sau failure nhưng không tạo quyền chạy. Chỉ sau complete-epoch selected continuation, budget lineage và fresh-process/public-entry evidence được kiểm mới có thể thu hẹp các gap tương ứng; không đóng toàn GRAPH29 từ metadata tests.

## Phase2 tối thiểu trước Stage7 long paid training

**Crash recovery và failure-credit accounting vẫn là blocker cho long paid GPU readiness**, kể cả khi phase1 intentional pause đã được nghiệm thu. Ngân sách GPU30USD đòi cơ chế giữ công việc hữu ích khi worker bị ngắt ngoài kế hoạch; phase1 chưa cung cấp điều đó. Đây là backlog tiếp theo, chưa release code hoặc actual run.

Phase2 thêm fixed complete-epoch cadence đã khai trong allocation. Tại mỗi epoch thuộc cadence, sau train và raw selection hoàn chỉnh, lưu latest CP cùng stopper/history/accounting/journal prefix, rồi publish marker epoch bất biến cuối cùng. Nếu epoch vừa cải thiện thì latest/best dùng chung CP. References cũ giữ nguyên; chưa áp dụng rotation/deletion ngầm. Worker có thể tiếp tục epoch sau marker, nên marker này chưa có whole-attempt terminal authority. Khi worker dừng, outer phải reap/cleanup, seal actual final journal/tail/source/runtime và physical-cost evidence trước khi consumer quyết định epoch nào thật sự dùng được.

Với Ecomplete epochs, Iimprovement epochs và cadence k, số tensor CP writes là số phần tử của union improvement epochs, cadence epochs và terminal boundary; luôn≤E nếu mỗi epoch dùng chung một CP. Cadence1 tại E=20 cho20writes tổng, thêm20−I so với best-only, tối đa19 nếu I≥1. Vì vậy “không20extra CPs” của phase1 chỉ nói scope intentional pause; long paid workload có thể cần cadence1. Host/GPU CP size S và timing hiện chưa được đo cho target paid profile. Giới hạn storage bảo thủ là E×S cộng metadata, hơn nữa khi giữ immutable parent attempts/copy best.

Cần benchmark riêng S, CUDA sync/CPU-clone peak, serialize/fsync/readback/hash time, restore+construction latency và chi phí validation trước khi chọn cadence. Overhead gần đúng là số saves×measured save time; đổi lại cadence k giới hạn số logical epochs cần recompute khi lỗi sau latest checkpoint, nhưng chưa chặn physical work đã tiêu trước crash. Chi phí GPU phải tính cả save/restore/replay theo rate thực đã được duyệt; chưa có rate/throughput mới trong plan. Fsync trên local disk chưa chứng minh bền qua VM/disk loss. Stage7 cần storage persistence đã kiểm và authority phù hợp, không tự mở remote/export/cloud route từ note này.

Trước forward/backward cần durable batch-compute reservation; pre-Adam reservation hiện có còn cần được reconcile với counter body-returned/committed. Khi quay lại latestE, suffix partialE+1 có thể bị replay từ RNG/state ởE. Logical trajectory giữ E rồi replay E+1, còn physical exposures/Adam attempts/time đã mất phải cộng vào cumulative ledger. Không reset lost steps/targets/GPU credit khi rollback. Nếu chỉ biết upper bound thì charge conservatively theo reservations/allocation; thiếu chứng cứ đủ để bound thì reject resume, giữ UNKNOWN. Không suy0work từ missing final hoặc launcher return code.

Một native failure-injection fixture hữu hạn có thể so continuous2epochs với parent completeE1 rồi một batchE2 body đã chạy nhưng chưa commit, sau đó fresh child replay toànE2. Nếu2batches/epoch thì control4 +parent3 +child2 =9physical Adam bodies, trong khi mỗi completed trajectory có4logical steps. Đây là quota mới cần ROOT review; không gộp vào8bodies phase1. Kiểm exact/tolerance đã khai trước cho states/Adam/RNG/selection history, không tự nới sau failure. CPU evidence chưa chứng minh deterministic replay của CUDA backend. Lỗi ngẫu nhiên, stale/torn marker và unknown partial optimizer mutation cần admission riêng dựa trên durable tail evidence, không mở rộng schema phase1 bằng một boolean.

Phase2 reuse chính ba production touchpoints trên cho cadence/seal/rollback accounting, không tạo daemon hoặc recovery infrastructure chung. Chưa có implementation, benchmark, fault proof hoặc đề nghị đóng blocker. Stage7 full training chỉ tiến sau khi crash-resume/credit rules và actual target-device proof tương ứng được nghiệm thu.

## Pins nguồn đã đọc

| Nguồn | SHA-256 |
|---|---|
|research_selected_runner.py|b9a9876a536964920e64ffac354c467ec8da9776e52b7a88b51d81e0b963848c|
|research_main_execution.py|0b3b671acf0601b3e84be9439187cf4a7f15bd0e6bd36470a576697bd2147ddb|
|research_main_stage.py|77b7dbfd75f715f3a4179286cd742780581151dc39c39748213c9c55c25b13c1|
|research_graph_checkpoint.py|e17e14199bc2179794a017303344ff1b67e27cdfa9035cb2a18eb85237513992|
|training.py|ca074a15dd5e45d016fd29d78b0b5ddbb0ccee3555b194699464d4cded6bf979|
|recovery.py|93eed09fa9962a1c54bccda2ce9985317c20faeb7397758b652eb0a48709f900|
|resumable.py|bc979222ab166297abb5dd2efa8e50fd7f5c2a1c6ed92b8d938da2ac0a4aa2b1|
|checkpoint.py|bc1a6fbdcaa55c864cb9f18d531dcede440f9cf364dc9025420615520394fc91|
|filesystem.py|695cdb730534eed48a4b42a0595090237282fd3333254785348e122d831417bb|

Các file trong bảng nằm dưới `src/knowledge_tracing/akt/`. Exact reviewed batch và compute inventory cần ROOT release riêng trước code; plan không cấp execution authority.
