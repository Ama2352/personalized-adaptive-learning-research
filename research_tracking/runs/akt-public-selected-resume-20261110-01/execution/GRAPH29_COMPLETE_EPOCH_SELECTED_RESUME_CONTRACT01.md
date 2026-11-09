# GRAPH29 — hợp đồng đề xuất tiếp tục selected-fit ở ranh giới complete epoch

Ngày09/11/2026. SOURCE-ONLY / PROPOSED_API_NOT_APPROVED. Chưa triển khai canonical, import, test, đọc dữ liệu thực, fit hoặc Git. Phạm vi đầu là cùng candidate A0–A3, simulator select_train80 CPU FP32 và cùng numerical/source/runtime identity. Không main refit, calibration, winner, mid-epoch hoặc CUDA resume. CPU proof không chuyển thành GPU proof.

## 1. Khoảng thiếu thật trong đường chạy hiện tại

`research_selected_runner.py:210–220` gọi actual authorization một lần rồi tạo `_Run` với counter/time bằng0. Loop `:255–274` tạo stopper/history mới và chạy epoch1. Chỉ best epoch có checkpoint, nonbest record checkpoint=null. `research_graph_checkpoint.py:775–848` khôi phục native/Adam/participation/RNG/modes ở complete epoch nhưng nói rõ không sampler/stopper/budget; identity ghi selection_state_saved=False, global_budget_saved=False, lifecycle_resume_supported=False (`:167–179`). GRAPH19 chứng minh next full epoch ở fresh OS, chưa khôi phục quy trình epoch-selection này.

Một checkpoint best cũ không phải last optimization state. Resume epoch E+1 từ best B<E sẽ đổi quỹ đạo. Không suy E từ số Adam steps hoặc metadata của checkpoint tốt nhất. Phải có cả last complete optimization checkpoint và best-selected checkpoint độc lập khi B≠E.

## 2. Public input tối thiểu đề xuất

NEW `SelectedEpochResumeRequest` là closed metadata, không permission. Truyền parent-boundary directory + external marker byteSHA, parent attempt/owned receipt path+SHA, original allocation/context SHA, new exclusive run/attempt ID và new authorization file+byteSHA. Không nhận caller model/optimizer/corpus/loader/RNG callback hoặc boolean verified.

API đề xuất `run_main_selected_resume(spec, evidence, *, resume_request, authorization_file, expected_authorization_sha256)` dựng genuine disk/runtime/source/resource guard trước lazy model như entry hiện có. Fresh entry giữ nguyên mặc định. Có thể thêm request pause_after_complete_epoch đã freeze trước execution cho producer; đây là kiểm khôi phục, không giảm max_epochs hoặc chọn điểm dừng theo loss đẹp.

Original matrix allocation/context/candidate và checkpoint profile giữ nguyên. Child attempt authorization riêng ghi output mới và remaining envelope; không dùng old token như quyền chạy mới. Per-attempt metadata khác output/run ID được lưu riêng, không bỏ scientific fields khỏi comparison để làm identity khớp. Stage config SHA/actual spec và original numerical identity đều được ghi rõ; không sửa receipt cũ. Runtime/Gate/source hiện hành vẫn phải thực kiểm, không fake metadata hoặc sửa expectedSHA để nhận nguồn drift.

## 3. Một resume boundary gồm những gì

Dưới attempt output mới, publisher tạo thư mục boundary-E độc quyền. Dữ liệu nhỏ JSON cùng CP đang có, không format tensor mới:

- Latest complete CP reference, state/meta/COMPLETE SHA+size, identity, exact GraphEpochReceipt completed_epochs=E; model/Adam SHA và named participation. CP phải là state sau train E và raw selection E đã hoàn tất, adapter trả về train index, không pending ticket/hook/callback, counters không đang reserve. CP save không đổi RNG/state.
- Best CP reference B≤E, selected raw prediction semantic SHA/summary/count/population, epoch B và history row B. Nếu B=E tái dùng cùng CP, không nhân đôi tensors. Mọi epoch complete cần latest state để có thể pause, nên thêm nonbest checkpoint có chi phí storage/time phải reserve. Không giả bestweights bằng lastweights hoặc lưu20CP mà không cấp quota.
- History liên tục1..E, mỗi row bind complete train receipt, raw selection objective ID/finite loss/coverage/population/prediction SHA, epoch record byteSHA và checkpoint ref nullable đúng meaning cũ. Không tạo lại selection bằng calibration labels. Đọc lại các row gốc đã ghim, không đặt stopper từ một best_loss được caller khai đơn lẻ.
- Stopper patience/min_delta/best_epoch/best_loss/stale_epochs/last_epoch và max_epochs. Recompute bằng đúng `EarlyStopping.observe` trên history1..E, kiểm exact equality stored state, earliest-tie rule và completed epochs. Nếu đã đạt early stop hoặc max_epochs thì chỉ finalize raw-best export, không thêm epoch.
- Logical cumulative reserved/body-returned/committed steps và targets; training time đã dùng, wall time đã charge, output bytes/checkpoint refs, actual per-attempt resource/work receipt. Không chỉ lưu optimizer step count. Low-level receipt không có các budget/loss/history fields này, phải có runner sidecar thực.
- Parent invocation/config/source/runtime/authorization/journal-prefix byteSHA, original initial-model/backbone SHA, corpus/DONE/bank/plan/roles, encoding80/support, context/window/phase identity, recipe26/condition/graph-confidence TRAIN80 provenance. Không calibration/final artifacts trong selection state.

Các files được flush/fsync/readback trước marker COMPLETE_EPOCH_SELECTED_PAUSE cuối cùng. Parent outer phải terminal/reaped/Job0, verify marker và không postwrite-rejection trước child GO. Marker không tự chứng nhận OS cleanup. Existing low-level CP flags vẫn giữ nghĩa của CP; wrapper mới mới được mô tả selected-epoch-resume proof.

## 4. Counter và ngân sách không được reset

Tách logical committed state tại E khỏi actual physical work qua các attempts. Restore tracker bắt đầu bằng cumulative participation/steps/targets của CP (`research_graph_checkpoint.py:833–840`). Seed `_Run` cumulative logical counters trước khi tracker phát optimizer events, để `optimizer_event` hiện có không so restored tracker>0 với run0. Đồng thời ghi child-local started/returned separately; parent E không được đếm thêm lần nữa là new physical updates.

Remaining steps/targets/training/wall lấy original envelope trừ toàn bộ charged parent attempts, kể cả failed construction, selection, saving/hashing/cleanup. Child deadline là min new finite attempt cap và cumulative remaining. RSS/free floor/device checks được đo mới, không lấy peak cũ làm current resource proof. New output bytes và cumulative retained quota có scope tách rõ, không charge lại read-only parent CP như file mới nhưng phải charge hashing/read/restore time. Không trừ các monotonic timestamps giữa hai process; dùng durations được outer/worker thực ghi và conservative external charge nếu cần.

Phạm vi đầu **chỉ nhận intentional complete-epoch pause có terminal accounting sạch**. Có pending reservation, body-returned chưa commit, partial epoch hoặc optimizer activity sau boundary thì từ chối parent này. Crash sau marker mà không có authoritative final/cleanup/counter evidence là UNKNOWN, không suy0work. Không rollback/replay một partial epoch trong batch này. Một extension rollback-to-last-complete có thể thiết kế sau với extra physical-cost accounting, không tự cấp từ đây.

## 5. Restore và iterator đúng đường thật

Rebuild audited public corpus/phase/encoding/train+selection indexes qua API hiện hành, không đọc oracle. Guard có thể audit ba Development roles theo22, nhưng optimize chỉ train80 và epoch choice chỉ raw selection10. Kiểm metadata/state bytecaps/hash trước deserialization và constructor theo CP API. Fresh adapter+ownedAdam, same initial backbone, restore bằng `inspect_graph_epoch_state` + `restore_graph_epoch_state`, không gán `_optimizer` ngoài loader đã được review.

`train_epoch` gọi `_shuffle_windows(seed=config.seed+epoch)` và private `random.Random` buffer1024 (`training.py:94–109,326`). Bắt đầu next_epoch=E+1 với factory order/count/window/query/input/target SHA như source, không loader RNG/cursor tưởng tượng. Reuse sampler, không materialize permutation khác để giống fixture. CPU Python/NumPy/Torch RNG và modes restore từ CP sau constructors; không gọi `_construct` hay reseed nữa trước next optimization. Logging/revalidation sau restore phải RNG-neutral; nếu không thì đặt đúng trước final restore hoặc lưu/kiểm RNG thật. No pending ticket được rebuild từ byte metadata.

Sau continuation, chọn best trên toàn history inherited+new. Fresh best reload/export như hiện tại, parity với đúng best row, counters logical/physical/attempt ancestry cùng terminal. Parent files chỉ đọc, final claim/output thuộc child với explicit parent lineage. Không tạo claim selected success từ pause marker. System selector/refit vẫn chờ toàn matrix và external freeze.

## 6. Atomicity, crash và negative cases bắt buộc

1. Pure lifecycle fixtures replay stopper trên improvement/tie/nonbest/patience stop, bestB<E, changed min_delta/patience/objective hoặc missing/duplicate history epoch đều reject. Stored bestCP/current CP sai epoch dù scalar counter có vẻ hợp lệ phải reject.
2. Pre-mutation negatives cho source/recipe/condition/train-vocab/role/window/corpus/runtime drift, wrong initial backbone, CP truncated/hash/size, wrong parent manifest/marker, pending/partial/late activity, unsupported parent purpose, exhausted cumulative budget, existing child directory. Kiểm lazy constructor/deserializer chưa được gọi khi metadata sai.
3. Pure budget fixtures seed restored counter>0, next pre/body/commit exact; parent charges không reset và không double-count committed prefix. Failure sau body không0-update/rollback. Fork reuse một parent thành hai children không được tự nhận là một physical trajectory; initial owned-parent allocation chỉ cho một reviewed consumer, không hứa nonresettable authorization.
4. Publication crash injection trước CP marker, giữa sidecar writes và trước/ sau pause marker. Chỉ nhận closure có toàn hashes + authoritative terminal/cleanup; orphan files không tự resume. Files cũ được byte-compare trước/sau, không overwrite/delete.
5. Native proposal sau pure/source acceptance là continuous vs intentionally paused fresh-OS continuation, same complete factory/seed+epoch, actual ordered windows/batches/targets, same next-epoch loss/state/Adam/participation, direct3RNG+modes và selected epoch/stale/best-CP/raw export parity. Không dựa vào dropout0 để chứng minh RNG. Numeric acceptance không yêu cầu loss tăng/giảm đẹp hoặc actual nonbest xuất hiện. Pure fixture riêng bắt best≠latest nếu native trajectory không đi qua branch đó.

Native allocation chưa chốt trong note này. Để test full wrapper với3epochs, continuous3 + paused2 + resumed1 là6 lượt thực thi epoch vật lý, không3. Nếu mỗi epoch2batches thì12Adam bodies; thêm fresh best reload ctor/save/load/inference phải khai đầy đủ trước dispatch. Có thể chọn fixture nhỏ hơn mà vẫn full exact epoch, không gọi Graph10partial3batches là complete. Không suy chi phí từ CPU tiny proof thành GPU forecast.

## 7. Scope file nhỏ nhất cho implementation sau review

Đề xuất NEW `akt/research_selected_resume.py` chứa closed sidecar/parent admission và public resume entry; reuse runner `_epoch/_predict/_save/_claim`, CP và EarlyStopping. Narrow adjacent `research_selected_runner.py` cần factor phần continuation loop/state initialization + complete-pause publication; `research_main_execution.py` chỉ sửa nếu cần typed resume authority/actual sidecar admission mà existing guard chưa biểu diễn. Không sửa graph math/CP tensor schema/legacy generic recovery hoặc SAKT. NEW focused tests riêng; exact file scope phải Root duyệt trước canonical edits. Tài liệu này không cấp quyền model selection mới/fullCV/training/paid execution.

## SHA nguồn inspection

- `src/knowledge_tracing/akt/research_selected_runner.py` — `b9a9876a536964920e64ffac354c467ec8da9776e52b7a88b51d81e0b963848c`
- `src/knowledge_tracing/akt/research_main_execution.py` — `0b3b671acf0601b3e84be9439187cf4a7f15bd0e6bd36470a576697bd2147ddb`
- `src/knowledge_tracing/akt/research_main_stage.py` — `77b7dbfd75f715f3a4179286cd742780581151dc39c39748213c9c55c25b13c1`
- `src/knowledge_tracing/akt/research_graph_checkpoint.py` — `e17e14199bc2179794a017303344ff1b67e27cdfa9035cb2a18eb85237513992`
- `src/knowledge_tracing/akt/research_graph_model.py` — `997fe9191388738954c0f4aeb1f7062c9c1e3cf6646a5b2486d2618b5c02c177`
- `src/knowledge_tracing/akt/training.py` — `ca074a15dd5e45d016fd29d78b0b5ddbb0ccee3555b194699464d4cded6bf979`
- `src/knowledge_tracing/akt/research_execution.py` — `df39d898f80efbe0cb43f5ff6d8f0bb64e2302a3353ba8023b3ed88cf9242001`
- `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md` — `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6`
- `docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md` — `96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1`
- `docs/thesis_recovery/26_ADOPTED_MINIMAL_CGAKT_RECIPE_V1.md` — `13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a`
