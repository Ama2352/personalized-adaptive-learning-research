# Thiết kế readiness native A0 CPU — chỉ điều tra/chuẩn bị nguồn, chưa dispatch

Ngày08/11/2026. Không import/chạy module research/model/runtime validator, pytest, Git, teacher hoặc đọc raw Junyi/Holdout trong audit này. Đọc source và JSON metadata; tính SHA/số học geometry bằng stdlib. Không phê duyệt cap/runtime hoặc đổi frozen hyperparameters.

## 1. Kết luận admission hiện tại

**CHƯA được chạy A0 lifecycle.** Có corpus60learner đã nghiệm thu; chưa có current-source full Gate và schema2 CPU runtime phù hợp trong ROOT Windows hiện tại. Hai file Gate isolation đã sửa theo phạm vi ROOT giao; agent không chạy tests/Gate. ROOT đã dispatch targeted pure01 và giữ terminalRC1/noJUnit/noresult, chưa acceptance. Không dùng targeted pure PASS hoặc progress dots làm runtime/full Gate substitute.

`preflight.py` không tồn tại ở `src/knowledge_tracing/akt/` hoặc `scripts/akt/`; entry thực là `authorization.py:178 preflight`. Research entry duy nhất đang có là `research_runner.run_a0_research_lifecycle(execution, read_limits=...)`, không CLI. Dòng trong contract22 còn nói reader/trainer chưa triển khai là snapshot thiết kế cũ; actual corpus/report/runner source mới phải đọc riêng, không sửa contract snapshot để giả acceptance.

## 2. Gate hiện có và source binding phải làm mới

Current pointer `artifacts/akt/preflight/gate2-current.json` SHA `7ecd8067fd3f30b658867fd5540ec331653ec4a8d6a5d1d3a0a68f932fa7690f` vẫn trỏ **Windows Gate22**, report SHA `f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd`, historical768PASS/477,7091635s. Nó không chứng nhận runner và nguồn hiện tại. Linux Gate24 historical771PASS ở ROOT khác/lockLinux cũng không thể alias thành current Windows Gate.

Mirror metadata của đúng path-selection trong `authorization.gate2_build_hashes` cho **150source/input files**; canonical sorted compact JSON SHA của vector hiện tại `ee3fb080a7e81cdc25b3061d8a816c064108a62f246fc838bc61cecffd0af458`. So Gate22: **30added / 8changed / 0removed**. Đây là static hash comparison, không gọi validator/Git hoặc báo executed rejection. Corpus source13/13 hiện bằng pins đã publish; protocol21 `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6` giữ nguyên. Sau bất kỳ sửa source/tests nào, phải freeze/hash lại và chạy fresh Gate; không reuse digest trong note như approval.

```json
{
  "added_since_Gate22": [
    "scripts/research/build_thesis_evidence_notebook.py",
    "scripts/research/collect_development_corpus.py",
    "scripts/research/windows_owned_worker.py",
    "src/knowledge_tracing/akt/graph_training.py",
    "src/knowledge_tracing/akt/research_execution.py",
    "src/knowledge_tracing/akt/research_lifecycle.py",
    "src/knowledge_tracing/akt/research_runner.py",
    "src/knowledge_tracing/akt/research_simulator_data.py",
    "src/knowledge_tracing/edge_confidence.py",
    "src/knowledge_tracing/reference_controller.py",
    "src/knowledge_tracing/response_calibration.py",
    "src/knowledge_tracing/simulator_corpus_publisher.py",
    "src/knowledge_tracing/simulator_corpus_reader.py",
    "src/knowledge_tracing/simulator_research_collection.py",
    "src/knowledge_tracing/simulator_research_data.py",
    "tests/akt/test_batch_factory.py",
    "tests/akt/test_graph_lifecycle.py",
    "tests/akt/test_graph_training.py",
    "tests/akt/test_research_execution.py",
    "tests/akt/test_research_lifecycle.py",
    "tests/akt/test_research_runner.py",
    "tests/akt/test_research_simulator_data.py",
    "tests/shared_kt/test_development_corpus_worker.py",
    "tests/shared_kt/test_edge_confidence.py",
    "tests/shared_kt/test_reference_controller.py",
    "tests/shared_kt/test_response_calibration.py",
    "tests/shared_kt/test_simulator_corpus_publisher.py",
    "tests/shared_kt/test_simulator_corpus_reader.py",
    "tests/shared_kt/test_simulator_research_collection.py",
    "tests/shared_kt/test_simulator_research_data.py"
  ],
  "changed_since_Gate22": [
    "scripts/akt/refresh_gate2.py",
    "src/knowledge_tracing/akt/config.py",
    "src/knowledge_tracing/akt/graph_prototype.py",
    "src/knowledge_tracing/akt/simulator_engineering.py",
    "src/knowledge_tracing/akt/training.py",
    "tests/akt/test_gate2_refresh.py",
    "tests/akt/test_graph_prototype.py",
    "tests/akt/test_simulator_engineering.py"
  ],
  "removed_since_Gate22": []
}
```

**Không chạy lại monolithic Gate as-is.** Pytest collection import Torch ở20testmodules (ROOT static receipt); sáu module pure kiểm `torch not in sys.modules`. `test_development_corpus_worker.py:140` còn kiểm không NumPy/Pandas/Torch, nên chỉ chia noTorch/Torch hai nhóm vẫn sai vì publisher imports collector→NumPy/Pandas và research_simulator_data import NumPy ở collection.

Source revision tối thiểu đã chuẩn bị trong đúng `scripts/akt/refresh_gate2.py` + `tests/akt/test_gate2_refresh.py`:

| Fresh process | Các module được giao đúng một lần | Purity |
|---|---|---|
|A `stdlib`|`tests/shared_kt/test_development_corpus_worker.py`|Không NumPy/Pandas/Torch; không pha chung publisher helper.|
|B `no-torch`|`test_research_execution.py`, `test_research_lifecycle.py`, `test_research_runner.py`, `test_research_simulator_data.py` dưới tests/akt; `test_simulator_corpus_publisher.py`, `test_simulator_corpus_reader.py` dưới tests/shared_kt|Sáu modules giữ nguyên noTorch assertions; reader helper import publisher trong cùng process.|
|C `remaining`|Toàn phần còn lại của dynamic inventory **67testmodules**|Cho phép existing neural synthetic tests; không loại test nào.|

`test_context_recovery.py` có noTorch check **trong code của fresh subprocess riêng**, không là parent-module assertion cần tách thêm. Không bỏ/markskip/xfail hoặc sửa purity assertions của sáu modules; không clear sys.modules hay spoof process đã nạp Torch thành pure.

Các nhóm có riêng log/XML; merged JUnit giữ nguyên testcase identities và từ chối duplicate cross-group/count mismatch. File inventory đủ, disjoint/exactonce, required7paths failclosed nếu thiếu hoặc groupempty. Không `-k`, deselection, oldPASS counts hoặc totalcount giả. Chưa dự đoán passcount của Gate mới; cần actual full inventory0fail/error/skip.

Một clock bắt đầu đầu `refresh`, mỗi child chỉ nhận remaining budget; aggregate/checksource/lock/actualreader/publication đều kiểm cùng deadline. Default300/max600 giữ nguyên. Late reader/publication deadline từ chối report mới của chính invocation; nếu pointer vừa thay thì restore exact previous bytes. Không sửa old Gate20/22/24. Schema1/suite=`tests/akt tests/shared_kt` giữ nghĩa alltests, report thêm process groups/inventory, không đổi native validator thành synthetic stub.

**Cần ROOT review/tests trước chạy:** mockpublisher dựng8dummy module/cases không actual Gate. ROOT targeted pure01 ghi `gate_isolation01/terminal_unknown.json`: terminalRC1,52progress dots nhưng khôngJUnit/result, không claim52PASS hoặc0tests; timer16/cap20, conservativecharge20s. Có thể filesystem/teardown nhưng chưa chứng minh nguyên nhân; source5b7/tests9a0 giữ nguyên, agent không retry. Per-group subprocess.run không phải tự nó proof Windows descendants đã dừng: ROOT phải chạy controller trong owned Job và giữ actualworker/job/cleanup receipt; không coi shimRC0 là cleanup toàn cây. Deadline còn phải chừa dispatch/cleanup/finalization trong outer cap đã chọn; không600cho từng group. Không triển khai thêm framework trong note này.

Cập nhật theo handoff ROOT sau lượt02: terminal bị từ chối vì thiếuJUnit/receipt sau khoảng34s; ROOT dừng mục tiêu ở cumulative khoảng54,055/60s. Không có fullGate hoặc actualfit; không suy PASS từdots, không tự retry/nới cap. Đây là thông báo vận hành của ROOT, không phép tính lại timing từ raw của agent. Failure và cleanup evidence do ROOT giữ riêng; source revision không tự trở thành accepted chỉ vì có partition đúng.

Các điểm platform phải kiểm bằng fixture đúng scope: testsresearch_execution/lifecycle thay `subprocess.Popen` nên Windows/Pandas platform metadata fallback có thể cần fixture lấy actualWinAPIversion; không patch production OS/runtime hoặc gọi mockmetadata là runtimeproof. Historical WinError5/hardlink hay MAX_PATH không tự chứng minh quyền/path hiện tại. AKT `filesystem.publish_new_file` Windows dùng rename, POSIX dùng link; không chuyển global filesystem/ACL hoặc skip path guards. Basetemp phải fresh/exclusive và path-length bounded; currentGate staging path dài là risk cần tính trước dispatch, không thử lại mù.

## 3. Runtime thật tối thiểu — không đổi lock/môi trường

`artifacts/akt/preflight/runtime-v2.json` hiện có tênv2 nhưng **không có runtime_schema_version/platform_id/python_prefix/project_root/lock_file**, là legacy Windows report. `research_execution._native_evidence:193–195` đòi explicit **schema2/deviceCPU/cuda_availableFalse**, nên không đủ. `_runtime_report_matches` còn kiểm current interpreter `.venv/Scripts/python.exe`, prefix/ROOT, selected lock, module origins và actual verify_upstream source dict. Đổi tên/copy legacy JSON không sửa thiếu evidence.

Lệnh **chỉ đề xuất, chưa chạy**, sau ROOT chọn/freeze source/runtime stage:

```powershell
.venv\Scripts\python.exe -B scripts/akt/check_runtime.py --upstream artifacts/akt/dependencies/upstream --device cpu --lock-file requirements-akt.lock.txt --output artifacts/akt/preflight/runtime-a0-research-20261108-01.json
```

Output exclusive, trực tiếp dưới preflight như research guard yêu cầu. Runtime script thực import Torch/NumPy/upstream và query CUDAavailable (CPU hidden), nên không được thực thi trong audit đọc này hoặc thay bằng mocks. LockWindows SHA `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`; không chọn Linux44lock cho hostWindows. Không globalinstall hoặc clone/fetch. `verify_upstream` phải chứng minh actualHEAD `01b7e8d7d7c862cabc9467108e3e7f2555653a88`, cleanstatus, publicorigin/tree/blob của3files; note chỉ hash raw3files theo sourceinventory, không chứng nhận Git state.

Gate command sau khi framework/tests/frozen-source admission đạt, **không dispatch trong note**:

```powershell
.venv\Scripts\python.exe -B scripts/akt/refresh_gate2.py --run-id 20261108-a0-research-current --publish-current --timeout-seconds 600 --lock-file requirements-akt.lock.txt
```

600 là max đã có, không forecast runtime hay cap đã được ROOT chọn cho actual Gate. Có thể chọn thấp hơn theo resource admission; không raise600/reset shard cap khi fail. Host RAM/peak/floor cần đo riêng ngay trước dispatch; note không đo RAM hiện tại.

Fresh runtime và Gate nên ở cùngphysicalROOT/interpreter/selectedlock/upstream pin. ResearchRuntimeEvidence phải ghim runtime path+SHA, lock path+SHA, Gatepointer path+SHA, GatereportSHA và combinedlogSHA. Reader kiểm actual build vector mỗi lần; không chỉ `status=PASS` hoặc typed token.

Research preflight reject inherited `GIT_*`/`GH_*` trừ5safeguards có giá trị exact tại research_execution:187–190. Env `GIT_CONFIG_COUNT/KEY/VALUE` do refresh tự đặt không được carry sang researchworker; nếu upstream dubiousownership cần reviewed read-only argv safe.directory mechanism hoặc actual ownership hợp lệ, **không nới guard và không fakeGit metadata**. CUDA_VISIBLE_DEVICES hidden, NVIDIA_VISIBLE_DEVICES none/void/empty; Windows worker_gate phải chạy trước knowledge_tracing/NumPy/Pandas/Torch imports.

## 4. Corpus và geometry có thể tính trước, không đọc labels

Corpus ID `grade10-development-lifecycle01-20261108`, corpusSHA `555ed695c7c7121af474edb542fa3eef664b340162ced46cdfc001a5d7a4ad72`, DONE SHA `66232663868baafd2f012b4d79afad373e2fd5e831d30622153163b94e1b733f`.48train/6selection/6calibration×210; bank84items/28concepts. Source metadata/QA đã xác nhận đủ84support train và hai lớp mỗi role. Read-only thiết kế này không mở JSONL hoặc oracle/final events. Các counts lấy từ closed QA và corpus metadata, không manufactured fixture.

| Phase | Learners | Targets/epoch | Windows/learner | Windows/epoch | Batch4 steps/epoch |
|---|---:|---:|---:|---:|---:|
|fit80|48|10.080|3|144|36|
|raw selection10|6|1.260|3|18|5inference batches|
|fresh refit90|54|11.340|3|162|41|
|calibration10|6|1.260|3|18|5inference batches|

Với all-known items và native context100/targetblock100: target chunks100,100,10; input lengths100,200,110 =410input slots/learner, không630targets. First target vẫn nằm fullpopulation; currentlabel chỉloss. Shuffle không đổi số windows/targets; không OOV trong optimization theo currenttrain support. Runtime reader/data bridge phải re-audit actual encoding/masks trước model, không dùng phép tính này thay actual counters.

Gọi E số fit epochs thực hoàn tất (1..20), e selected epoch (1..E). Optimization **36E+41e**steps, targets **10.080E+11.340e**; worst20+20 = **1.540Adam steps / 428.400optimized targets**. Hai phase dùng fresh parameters/Adam và shared cumulative ledger; không reset ở refit. Đây là work bound, không1.540steps đã chạy, không forecast seconds/RAM/price và không tự cấp quyền runworstcase.

Raw-selection inference5batches/epoch +5best-checkpoint-export +5calibration. Hai reload probes có tối đa4native windows mỗi lần; với currentgeometry4đầu=100+100+10+100=310targets/probe,620target predictions/2probes, không hai full-refit inference passes. Vì vậy model inference invocations ngoài optimization ≤**5E+12=112**batches/probe calls tạiE20; target response positions26.460(selection20+best)+1.260calibration+620probes=**28.340**. Không cộng inference targets vào optimized target ledger. Đây là logical work geometry; không latency guarantee, không independent sampleN hoặc closed-loop84probe throughput.

Cumulative budget native config phải match EXACT: max_train_users54, max_val_users6, max_targets_per_side11.340, max_total_targets12.600; budget roles48/6/6 +10080/1260/1260 +max_events210. max_steps/max_optimized_targets phải đủ planned fullwork để muốn đạt lifecycle; nếu chọn thấp hơn phải gọi resource-probe/partial và STOP khôngcomplete, không giảm20epochs/modeldims cho vừa tiền. Time/RSS/checkpoint/prediction caps chưa được actualfit đo/chọn; không lấy toy d32/tests throughput làm forecast d256.

Public9inputs+DONE hiện **1,507,656B**, largest public file1.135.792B; max_input_bytes/readlimitstotal phải chứa đủbytes và auth/Gate metadata theo đúng guard. Reader đã có accepted256KiBline cap trong collector source; việc reuse phải pin explicit limit, không đọc oracle để cứu support. max_trajectories_per_role48, max_events_per_learner210, max_total_events12600; reader max_wall≤600 và≤global lifecyclewall. Checkpoint cap là serializedbytes, `_save` chỉ phát hiện sauwrite, không hard disk/peakRAM guarantee. Không derive exactcheckpoint/outputbyte cap từ parameter count nếu chưa measured.

## 5. Chuỗi tối thiểu để ROOT chuẩn bị một actual CPU attempt

1. Review/freeze isolation2files + runner/lifecycle/reporting source; bounded pure tests riêng bởi ROOT, giữ failures. Sau đó actual fullGate A/B/C và cleanup/rootresource acceptance; không monolithic retry hoặc substituted purePASScert.
2. Actual fresh schema2CPU runtime trong cùngROOT/lock/source; source không đổi giữaGate/runtime và authorization. Runtime checker/verify_upstream không được monkeypatch. Freeze 13corpus source hashes và docs21; không dùng kitstrip notebookJSON đổi corpuspins.
3. Tạo **một native AKTConfig phase simulator-research execution_enabledTrue** và SimulatorResearchSpec/ResearchResourceBudget exactcounts/caps; giữ frozen256/8heads/1block/dff1024/final512/dropout.05/batch4/Adam1e-4/maxepochs20/patience3/min_delta.0001/seed42/context100/target100/maxlen200/graphFalse/n_pid0/recoveryNone. Hiện chưa có actual A0research config/auth/dispatch file đã selected trong các paths đã kiểm; collectorconfig60×210 không là trainerconfig.
4. `prepare_research_identity(spec,evidence)` chỉ chuẩn bị consistency, không authority. Closed authorization11fields: schema_version1, decisionAUTHORIZE_BOUNDED_SIMULATOR_RESEARCH, scope`simulator-research-a0-selected-refit-calibration-v1`, run_id/configSHA/specSHA/identity/caps/requested_phases/approval_reference. Requested phases đúng selection_fit/refit90/calibration_predict/temperature_fit. Path dưới experiments/akt/authorizations hoặc artifacts/akt; fullspecSHA/diskSHA externalpins, fresh results/<runid>ABSENT. Không dùng legacy authorization_identity/identity mặc địnhBKT hoặc watchdog default data fallback.
5. Review source-bound owned worker/outer driver: worker_gate trước heavy imports; require_research_authorization thật→run_a0_research_lifecycle với CorpusReadLimits explicit. Native entry revalidates auth→publictypedreader/source/roles/support/classes trước lazyTorch. Không monkeypatch validators/token/source/corpus. Public QA có đọc binarylabels để admission; không nói calibrationlabels chưa từngđọc, chỉ không dùng chọn epoch/optimize.
6. Outer cùng global resourceledger/Job, no retry/resume. Acceptance phải có allstep/target counters, raw-selection freeze trước freshrefit, strictcheckpoint/reload, calibratedmetrics đúngsource, fulltargetnullcoverage, allSHA/budget/COMPLETE/no failure +actual ownedcleanup. COMPLETE nội bộ một mình chưa accepted outer. Latefailure giữ artifacts, không rollback optimizer hoặc relabel partial success.

A0 chỉ single-candidate lifecyclepilot, không mainmatrix winner/CG-AKT superiority/RQcompletion. RequiredSAKT/GKT/learnedgraph/Junyi và independent final evaluation không bị loại; không Junyi/Holdout/final events/cloud/paid run từ note.

## 6. Exact sources/hash của lần đọc này

Bảng chỉ pin những inputs đã đọc/hash; không fake currentGit commit hoặc actualvalidator. Gate vector snapshot và listdelta ở trên bao quát dynamic buildinputs; Gate fresh phải lưu fullvector thực của nó. Nguồn đang được ROOT review có thể đổi sau note, khi đó cần pin mới chứ không sửa cohort/history để khớp.

| File | SHA-256 |
|---|---|
| `src/knowledge_tracing/akt/research_execution.py` | `5ea3d7283f6d8da6eab712d4e4fedb48cd41717f99cd3ae51fb7b8651b16c7b6` |
| `src/knowledge_tracing/akt/research_runner.py` | `dce052064d438d4cd98f91e1ddbbc4dbd325f5994b5978e716190249719e64c0` |
| `src/knowledge_tracing/akt/research_lifecycle.py` | `cf16402f26d27732cedce83aa01bb46a84537c21cdbed11b80c5fb920fad0fff` |
| `src/knowledge_tracing/akt/research_simulator_data.py` | `9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b` |
| `src/knowledge_tracing/akt/authorization.py` | `bd6be914e3b5049927ba6358ee4872097a46469fede9ad1b71ee63df951ac7f0` |
| `src/knowledge_tracing/akt/config.py` | `beb2f8830c9d411fa1c00f0acf81ffe0c5200d6c09045d949b9cebade30dc85f` |
| `src/knowledge_tracing/akt/provenance.py` | `493d82af749baefcacec9ece0a7abe3297e64398eb4cd93c1d639ca41752cb59` |
| `src/knowledge_tracing/akt/windows.py` | `e8d00ea0f8b9d07bdc979575109c1f1fc22498d55410bff05a12559bebdb2068` |
| `src/knowledge_tracing/akt/training.py` | `ca074a15dd5e45d016fd29d78b0b5ddbb0ccee3555b194699464d4cded6bf979` |
| `src/knowledge_tracing/akt/checkpoint.py` | `bc1a6fbdcaa55c864cb9f18d531dcede440f9cf364dc9025420615520394fc91` |
| `src/knowledge_tracing/akt/filesystem.py` | `695cdb730534eed48a4b42a0595090237282fd3333254785348e122d831417bb` |
| `src/knowledge_tracing/simulator_corpus_reader.py` | `e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90` |
| `src/knowledge_tracing/response_calibration.py` | `c7849654eff35862e61602a4f95e401ed88b9070a77832e05d6a7173e72ebacb` |
| `scripts/research/windows_owned_worker.py` | `0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1` |
| `scripts/akt/check_runtime.py` | `4f5be1c58db40cd8875865275bb50f0b8171dc781615d4ce9f862ca598c1f795` |
| `scripts/akt/refresh_gate2.py` | `5b7e60d342f8c2ab27536d3ec02d208a9bdb04728ca5ccdf7371b13d784fa31b` |
| `tests/akt/test_gate2_refresh.py` | `9a0a41ffde24d0d12996f7294d000d50d9cbc8c1adced6853a0abf2c0c7de758` |
| `tests/akt/test_research_runner.py` | `260e75ae2bb01bcc1250da4ec078edc94bccbab2398f71f5f65304d2c9ab3b55` |
| `tests/akt/test_research_execution.py` | `9289f3aa4c8948f3e62344d11f01ea596764f78a42f1e2291aafc92178f72ba4` |
| `tests/akt/test_research_lifecycle.py` | `47f776e6dea4a8e123546d336e367219610f7b84b05660743755fb2bc9f22961` |
| `tests/akt/test_research_simulator_data.py` | `bee16620e1bdc2c98dd66e65b2ddddd82160098582b83b53a34120b50fb3645b` |
| `tests/shared_kt/test_development_corpus_worker.py` | `f2d80a0a2e29f86bc42d8ccc68d8e1709f8d7202f16723697a803d36c959fbb0` |
| `tests/shared_kt/test_simulator_corpus_reader.py` | `b92ecab03a1bbcef58406cd6e3cf53628a76181511497a446ee9c44753e0e2fb` |
| `tests/shared_kt/test_simulator_corpus_publisher.py` | `3f890563ee346b3196a1ee41fb1ba10cc47ad9bb5c1a4c07f88a2d5432d16fd0` |
| `requirements-akt.lock.txt` | `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a` |
| `docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md` | `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6` |
| `docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md` | `96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1` |
| `artifacts/akt/preflight/runtime-v2.json` | `259c171fe63e39a14d9bdf42793bd854a5be73ded19a7a800a2e8a982906f1b4` |
| `artifacts/akt/preflight/gate2-current.json` | `7ecd8067fd3f30b658867fd5540ec331653ec4a8d6a5d1d3a0a68f932fa7690f` |
| `artifacts/akt/preflight/gate2-evidence-20261108-linux-tooling-22.json` | `f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd` |
| `artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_collection_conflict01.json` | `25f4aa27d9abe31666e1589ce7fb803576f052eabfbc13181b5a392c09e58a61` |
| `artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/corpus.json` | `555ed695c7c7121af474edb542fa3eef664b340162ced46cdfc001a5d7a4ad72` |
| `artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/DONE.json` | `66232663868baafd2f012b4d79afad373e2fd5e831d30622153163b94e1b733f` |
| `artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/bank.json` | `4ef02907ee9071ba2ed6b4bba4d4dab728d390e9bbff8218a4e39bbb32f48034` |
| `artifacts/simulator/corpora/grade10-development-lifecycle01-20261108/plan.json` | `b48c3657eac3c04cbad5e3b7864021e5860eef8ef01ba8808cc9161deaa8b2f6` |
