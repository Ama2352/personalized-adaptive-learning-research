# Hợp đồng lifecycle A0: selected fit → refit90 → response calibration

08/11/2026 · **THIẾT KẾ ENGINEERING CHƯA TRIỂN KHAI TRAINER**. Áp dụng phương pháp đã adopt ở [21](21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md); không thay frozen AKT, quyền data/runtime/resource hoặc phạm vi thực thi. Đây là hợp đồng hữu hạn cho BATCH3B, không một kết quả fitted, pilot đã chạy, phê duyệt GVHD hay hoàn tất RQ.

## 1. Ranh giới pilot và main matrix

First lifecycle mang nhãn `a0_single_candidate_lifecycle_pilot`, allocation chỉ A0. Epoch tốt nhất được chọn bằng raw predictions trên selection10; đó **không** là conservative system selector giữa A0/A1/A2/A3. Trong main matrix, phải có raw best-epoch predictions của toàn candidate đã freeze rồi chốt system winner **trước bất kỳ refit90/calibration nào**. Không lấy A0pilot receipt để nói graph đã bị chọn/loại, không xem refit/calibration outcomes rồi đổi candidate.

Không gọi `select_checkpoint/refit_outer_train` với fold giả. Các hàm đó đang scope Junyi/InnerSplit; native full-fold workflow refit toàn outer-train và public entry còn disabled. Reuse [train_epoch](../../src/knowledge_tracing/akt/training.py), EarlyStopping, native checkpoint và AKTAdapter.predict_windows; không tạo training loop thứ hai hoặc nới simulator_engineering/SAKT/GKT toy guards.

## 2. Tiền điều kiện trước model

1. Actual current-source Gate/runtime/isolated interpreter, CPU device profile, source/lock/docs21 và exact authorization/caps theo [research_execution](../../src/knowledge_tracing/akt/research_execution.py). `execution_enabled`, GatePASS hoặc typed token một mình không cấp quyền. Token kiểm consistency hợp tác, không cryptographic authority.
2. Dùng [public corpus reader](../../src/knowledge_tracing/simulator_corpus_reader.py) với fixed `artifacts/simulator/corpora/<id>/`, external corpus/DONE SHA và explicit read limits. Chỉ9public modelinputs+DONE, không oracle/, final event file hoặc arbitrary source paths. Dựng ResearchSplitPlan từ stored recipe, bank, actual ResearchProvenance và ObservableTrajectory; re-audit roles/learner families/clock/global source rows/counts/provenance, kiểm raw SHA và no failure trước/sau.
3. **Reader hiện chỉ có source implementation, acceptance chưa đạt:** lượt thử01 timeout28,0125s, không JUnit. Root exact-argv scan sau đó không thấy process, nhưng không suy được final test counts. Không gọi 47PASS/42PASS; không retry trước ownedJob launcher/process proof. Reader sourcee582bf29/testb92ecab0 giữ nguyên. BATCH3B chưa được phép dùng reader trên actual corpus trước source/acceptance review.
4. Actual entry cần kiểm đủ bank84/28, support và two-class eligibility đúng phase, frozen profile/config, fresh output và job budgets trước lazy Torch/model import. Reader có thể trả missing-reference/two-class flags cho dữ liệu hợp schema; không được biến các flags này thành calibration/trajectory success hoặc drop các event bất lợi.

Root đang đóng băng first-development corpus/config riêng; tài liệu này không ghi đè [các báo cáo tiến độ](../../research_tracking/reports/README.md), không generate corpus, không mở final. Counts/caps cụ thể lấy từ exact approved config khi chạy, không từ d32smoke/H_dev30 hoặc ví dụ trong note này.

## 3. Data flow và giới hạn dùng nhãn

Public reader có thể **đọc và audit schema/nhãn binary của cả ba roles** trước allocation để xác minh corpus, class/support counts. Không được diễn giải điều này là calibration labels chưa từng được đọc. Ranh giới khoa học cần chứng minh là **không dùng calibration labels/predictions/loss để optimize weights, chọn epoch/candidate/hyperparameters hoặc winner**.

Phase function nhận input hạn chế: fit80/epoch selector chỉ train+selection; refit chỉ train+selection union và immutable freeze; calibration predictor chỉ frozen refit checkpoint và calibration observations. Không truyền full corpus/callback có thể truy cập oracle/final vào model/training step. Corpus audit/support checks là declared admission rule chung; không thử seed/corpus khác cho đến khi thấy loss đẹp.

Reuse [research_simulator_data](../../src/knowledge_tracing/akt/research_simulator_data.py): `select_train80`, `raw_selection10`, `refit_union90`, `calibration_predict`. Vocab80 chỉ từ train; vocab90 fit mới từ union90. Khi đủ84support, values có thể giống nhau nhưng support/phase/source lineage vẫn khác. Không dùng calibration để mở vocabulary hoặc cứu OOV.

Mọi target giữ learner/query(item,timestamp,source_row)/globalrank và `observable-prefix-chain-v1`. Current label chỉ ảnh hưởng chain sau row; chain này **khác OnlineSession model-bound history hash**. Join phải kiểm cả scheme/query/history, không source-row-only. Unsupported/OOV là null+reason trong full population, không0,5 và không âm thầm bỏ row. Scalar p của served query, reference-vector S và criterion/controller là các đại lượng/phase khác nhau.

## 4. State machine và artifact bắt buộc

Tất cả paths dưới một `experiments/akt/results/<run_id>/` mới, không overwrite/auto retry/resume. Tên dưới đây là proposed contract, chưa có output thật.

| Stage / artifact | Nội dung, identity và điều kiện chuyển tiếp |
|---|---|
| `invocation.json` | Exact spec/config/authorization reference+SHA, source inventory/Gate/runtime/lock, docs21,9corpus/DONE SHA, counts/caps, purposeA0pilot. Không raw credentials/persona/oracle. |
| `events.jsonl` | Durable phase/epoch/step events, UTC+monotonic clock, actual job/worker ownership receipt, cumulative reserved/body-returned counters. Không reset qua epoch hoặc refit. |
| `fit80/encoding.json` | Vocab/support, actual train shard/phase/domain/source identity. Chỉ fit80, không calibration or selection statistics. |
| `fit80/epochs.json` | Complete epoch stats, raw selection loss/coverage/population SHA, sampler seed42+epoch. Partial epoch có failure receipt, không selected success. |
| `fit80/best-epoch-<n>.pt` | Complete best checkpoint theo existing EarlyStopping: max20, patience3, min_delta0,0001, giữ earliest trong tie. Native exact model/Adam recipe, không yêu cầu metric cải thiện để nghiệm thu phần mềm. Mỗi path mới độc quyền. |
| `selection/predictions.csv` + `selection/targets.jsonl` | Best-epoch raw full selection predictions và truth sidecar tách riêng; hash query/history/coverage, labels chỉ join sau prediction. Không temperature ở epoch/system selection. |
| `selection/result.json` | Selected epoch/checkpoint/prediction/target/source/input SHA và raw epoch policy; kind=`single_candidate_A0_epoch_selection`, system selector deferred. File được freeze trước refit. |
| `selection/freeze.json` | Actual SelectionFreeze gắn train/selection shard hashes, plan/bank, selected epoch và SHA của result.json; stage=`raw_selection_before_refit`. Không fake system winner. |
| `refit90/encoding.json` | Actual union train+selection giữ origin roles, encoding/vocab/support mới và cùng freeze. Không gán union thành legacy train để vượt guard. |
| `refit90/checkpoint.pt` | Model **và Adam mới từ seed42**, không load bestweights để tiếp tục. Optimize đúng selected epoch count; không chấm lại selection để earlystop/rerank. Complete refit progress/identity; source/domain/vocab/phase/freeze/epochs đầy đủ. |
| `refit90/reload.json` | ByteSHA/size trước load; expected identity/role, keys/shapes/dtypes/finiteness, strict state load và prediction/loss/count parity cùng CPU threads/batch/window geometry. Không constructor trước identity/size checks. |
| `calibration/predictions.csv` + `calibration/targets.jsonl` | Frozen refit predictions cho **toàn calibration10**, trước join response labels. Weights/source/input không đổi,0optimizer steps. Prior responses của chính calibration learner đã quan sát được dùng, current/future label không làm input. |
| `calibration/calibrator.json` | Existing TemperatureCalibration bound refit checkpoint/model ID/vocab/split/partition/reference bank/source. T∈[0,05;20],clip1e−6,≤200objective evaluations. Thiếu supported two-class → unsupported/Tnull, không fallbackT1success. |
| `calibration/export.json` | Raw/calibrated response outputs và coverage riêng; in-sample calibration loss không là external calibration quality hoặc latent mastery calibration. Không chọn lại model sau Tfit. |
| `run.json` + terminal `COMPLETE.json` | Chỉ sau allSHA/readback/coverage/parity/budget/postelapsed acceptance, no failure. Chỉ ghi A0pilot lifecycle complete; không matrix/RQ completion. |
| `failure.json` / failure log | Stage, original error, exact started/reserved/body-returned/completeepoch counts, retained files/checkpoint references/source/caps. Lỗi sau Adam body không rollback; late publication bị failure/outer controller override. |

Checkpoint có thể reuse native full model/Adam/RNG container; **không đồng nghĩa public resume supported**. Scope đầu recovery=None/resumeFalse. Identity phải JSON-canonical trước save/load để tuple/list/Path không gây drift. Refit checkpoint role/domain certificate chỉ xuất khi actual complete optimization receipts tồn tại; không promote toy/unverified/Junyi weights bằng sửa metadata. Calibrator là artifact riêng sau refit, không backdate T vào weight-training identity.

## 5. Reuse actual step và resource accounting

`train_epoch(adapter,windows_factory,optimizer,epoch,budget,progress_callback,resource_callback,batch_factory)` đã có đầy đủ primitive forward/backward/clip/Adam. Existing `batch_factory` gọi cùng collate_windows, binds phase/epoch/fulltarget IDs và pending batch; **Adam pre-hook reserve/fsync trước body**, post-hook ghi body-returned. Không monkeypatch global optimizer hoặc viết lại loss/backward. Hai optimizers selection/refit chia một ledger; native counters bổ sung, không thay durable events khi exception xảy ra.

Mỗi epoch nhận **remaining** step/target/train-time và global wall/RAM guard; không reset cap ở refit. Cần phân biệt initial reservation, body returned, parameter actually updated và complete epoch. Selection/calibration inference nhận0optimizer. Model/Adam lazy state/save/reload trong explicit CPU context, đúng dtype/profile, no device fallback. Trước actual constructor cần memory floor/current-runtime proof; reload giữ cùng thread/batch/window geometry, không so từ hai ambient thread settings khác nhau.

Model initial/re-fit seed42 và native epoch sampler giữ nguyên. Training có thể thay global Python/NumPy/Torch RNG trong owned process, phải ghi rõ; không hứa caller RNG preservation. Online evaluation loader sau này cần fork/restore RNG khi tạo container. Không dựa vào generic helper có CUDA seeding/RNG calls để giả CPU-hidden proof.

Cache preprocessing theo exact corpus/source/phase/encoding/geometry hashes, freeze arrays và kiểm boundaries. Không full source audit từng window. Nếu drift thì STOP, không rebuild dữ liệu mới giữa candidate/epochs. `max_epochs=20` không tự là quyền chạy đủ20; config phải reserve whole declared work hoặc run là resource-probe/partial, không accepted lifecycle.

Arithmetic minh họa **không default/forecast**: nếu fit48 và union54 learners đều210events, known-item geometry targetblock100 tạo3windows/learner; batch4 →36fitbatches/epoch,41refitbatches/epoch. Worst20+20epochs →1.540steps. Không lấy d32test time để forecast native256; actual measurements/caps/root authority quyết định admission. Không hạ maxepochs, kích thước hoặc bỏ calibration chỉ để gói vừa budget rồi gọi protocol-complete.

## 6. Source/runtime/process và nghiệm thu

Research kit phải giữ **exact raw producer dependency bytes**: Paper2notebook69KB/sourceSHA353f… cùng CSV/Python/docs21 đã nằm trong corpus.source_inventory. Engineering builder cũ strip/rewrite notebookJSON dù cell equations tương đương vẫn làm source/Gate mismatch. Không rebase/relabel corpus source hashes để nhận stripped copy; oldc934kit giữ lịch sử, new research kit/Gate là bước riêng.

Windows `.venv` redirector khiến timeout của Popen wrapper không đủ chứng minh real pytest/worker descendants đã dừng. Future test/run cần shared ownedJob launcher/process ownership proof: actualargv/interpreter/parent-child IDs/job, final process state/cleanup và outerpostelapsed. Không retry vì chỉ observation timeout, không gán0exit cho process chưa có terminal proof. Reader trial01 retainedUNKNOWN không dùng làm acceptance.

Source review/tests phải chứng minh: exact public roundtrip+nooracle/final; raw fit/selection factories không nhận calibration labels để lựa; fresh refit optimizer/parameter instances+encoding lineage; selected epoch frozen trước refit; fulltargetkeys/null/OOV/cold coverage; weights unchanged trong calibration; checkpoint identity trước deserialization/constructor; global budgets/partial/late failure không success; temperature không neural update; negative/no-effect metrics vẫn hợp lệ. Pure stubs/source checks trước actual neural validation; actual optimizer cap phải được root duyệt riêng sau source/Gate/runtime/data/resource proof.

Tài liệu này không cấp implementation scope BATCH3B. BATCH3A reader acceptance còn chờ owned process proof và full source review. Mainmatrixselector, graph research-mode wiring, SAKT/GKT research lifecycles, learned confidence, final/audit evaluation và scientific conclusions vẫn là các deliverables riêng.
