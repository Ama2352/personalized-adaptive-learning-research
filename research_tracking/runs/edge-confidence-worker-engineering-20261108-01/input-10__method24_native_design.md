# Method24 native CPU — thiết kế worker/dispatch hữu hạn, chưa triển khai/chạy

Ngày 08/11/2026. Chỉ đọc source, JSON/installed metadata và hash files để lập thiết kế này; không import NumPy/sklearn/Torch, không test/fit/probe process, không sửa corpus. ROOT review rồi mới cho phép viết worker/config/request/outer; note này không cấp quyền thực thi. Recipe Method24 đã có ở `research_tracking/reports/edge_confidence_method24_plan_20261108.md` (train-only optimization, unary OOF không bị loại, randomization label-free).

## 1. Một operation và population cố định

Input là corpus canonical `grade10-development-lifecycle01-20261108`, đã có 17 files/6.985.213B; không generate/copy/relabel. Metadata evidence manifest SHA `cbd81b65363b2d50c62fb1d145793375cb44e523410d2aea2a062ba974624c9c`; external canonical inventory `artifacts/akt/local-tests/development-corpus-20261108-01/canonical-corpus-inventory01.json` SHA `794781989ba26d5be9142df996fcbb71db5e8f880e4b90d3c0681a5a2c43d19f`.

New worker và outer **không mở/list/parse/hash oracle/**; chỉ ghim external17-file inventory và prior acceptance bằng SHA. Nếu cần kiểm lại full17 opaque hashes, đó là verification riêng có scope truy cập rõ, không lẫn thành zero-oracle-access của fit. Current public reader mở đúng9modelinputs+DONE, gồm schema/labels selection/calibration; sau audit chỉ project TRAIN48×210=10080events. Không dùng hai vai kia để fit/tune/rank/bootstrap. No final events/teacher calls/latent truth/profile/difficulty features. Bank28concepts/84items, toàn756ordered nonself candidate edges.

Bindings exact cho worker: corpus SHA `555ed695c7c7121af474edb542fa3eef664b340162ced46cdfc001a5d7a4ad72`, DONE `66232663868baafd2f012b4d79afad373e2fd5e831d30622153163b94e1b733f`, plan `7222b7c34051f41d99648421b940167c2da705efa604070957a23812273e02ed`, bank file `4ef02907ee9071ba2ed6b4bba4d4dab728d390e9bbff8218a4e39bbb32f48034`, TRAIN JSONL `e2f3d7c0e1cf1fefa8b3c952d21a0531436f86259d6a7c8a07699cc0435fc07b`, TRAIN manifest `37101c7d6d1d1a74310c58179455cd844c47d5d4cba9d4878ac6316127bf6f49`, TRAIN provenance `10287bccb20804a1504981c5a5d6551e280369fac283df74a4eabf5aed15e9e5`. Public9+DONE actual total1.507.656B; hash before/after, failure marker absence, không sửa canonical.

Reserve trước heavy imports, một attempt/no retry:

- 2352 statistical fit slots:84baseline +2268augmented; actual public solver calls tối đa2352, chưa biết đến khi thực thi. Unary FIT/failed fit có flags riêng; reservation không giả actual0 nếu hardkill.
- 272160 edge OOF rows,756edge summaries;10080unique baseline OOF target identities sau dedup27copies; tối đa36288eligible-learner deltas. Không coi các edge-row copies là independent N.
- 200bootstrap replicates/supported edge, không refit;31learned-DAG edges yêu cầu, thiếu thì `UNSUPPORTED_EDGE_BUDGET`, không filler/forced positive.
- CPU only;0teacher/collector/NN optimizer steps/remote/GPU/Modal. Surrogate logistic fit là model fit, **không ghi model_calls=0 cho operation này**.

## 2. Entrypoints và schema nhỏ cần viết sau approval

Hai nguồn mới trong chính prep này, chưa tồn tại/chưa có SHA: `method24_worker01.py` và `run_method24_native01.py`. Output `method24-native01/` + `method24-owned01/` exclusive dưới prep; từ chối existing/partial attempt hoặc symlink/junction/traversal, không tự retry. Không export arbitrary project_root/data path. Worker CLI bắt buộc `--request`, `--request-sha256`, `--active-deadline-perf`, `--active-deadline-wall`; outer CLI bắt buộc `--request-sha256`. Một pure argparse contract test phải chứng minh outer-generated argv đủ worker requiredflags trước bất kỳ actual dispatch.

Request JSON exact top-level fields đề xuất: `schema_version=1`, `purpose='method24_train_only_conditional_surrogate'`, `approval_reference`, `config_sha256`, `source_sha256` (exact10paths dưới đây), `dependency_profile_sha256`, `corpus_id`, `corpus_sha256`, `done_sha256`, `prior_corpus_inventory_sha256`, `output_relative`. Không accepts unknownkeys/extra source path trước source opens. Config mới, fixed recipe đầy đủ và explicit caps; không lấy counts/geometry từ production defaults. Ghim config/request/source trước và sau operation. Không tái dùng old collection config như fit authority.

Python-source population chính xác10paths (8đã đọc +2pending). Protocol/lock/runtime/input files là inventory riêng, không âm thầm đếm vào10:

| Nguồn | SHA256 hiện đã đọc |
|---|---|
| `src/knowledge_tracing/edge_confidence.py` | `a91aec2558d1fa63c18212aadda265e2dd0e01f369756447022b21bacfc235e9` |
| `src/knowledge_tracing/simulator_corpus_reader.py` | `e582bf293e7699f1dc98096fcc693437610f2253bddb11ba4fff8952a35f6a90` |
| `src/knowledge_tracing/simulator_research_data.py` | `51eb7275a6a4a6b26b763a21a8fe6dc15b0973fc19b3c5557175eaa298db7e53` |
| `src/knowledge_tracing/simulator_data.py` | `79e28c1a8fc9b3bd5f3283868d7aba1a5bbc7c76764725a8b01098b2ae33cd9f` |
| `src/knowledge_tracing/simulator_bridge.py` | `b29105acd8de84b060ca27573bb7f7cf8e85599a4596e50e4a21ab63c82329d2` |
| `src/knowledge_tracing/akt/resources.py` | `8c1e5970efb6aa9966a8f583e11172632426f3318d396c3e28d24b5d16b9c5ba` |
| `scripts/research/windows_owned_worker.py` | `0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1` |
| `src/knowledge_tracing/__init__.py` (docstring-only hiện tại) | `b84a9a4118d8b3476daae25a7981c97909524ace7ef93860bba7e6ec9e5bccb8` |
| `artifacts/akt/local-tests/akt-research-runner-20261108-01/method24_worker01.py` | PENDING_IMPLEMENTATION, không placeholder64hex |
| `artifacts/akt/local-tests/akt-research-runner-20261108-01/run_method24_native01.py` | PENDING_IMPLEMENTATION, không placeholder64hex |

Worker phải bắt đầu stdlib-only, `.venv` lexical entry/prefix physical, gọi `worker_gate()` trước mọi `knowledge_tracing`/NumPy/sklearn imports. Owner exact token/Job/nonce từ helper; source/argv/hash kiểm và actual worker inJob trước GO. Venv shim intermediate là hợp lệ khi chain được helper xác nhận. Không PPID==outer-only guard, không base-Python launch, không broad PID/name cleanup.

## 3. Runtime packet đã quan sát tĩnh, chưa import-acceptance

Windows lock `requirements-akt.lock.txt` SHA `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a`; protocol21 SHA `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6`. Local entry `.venv/Scripts/python.exe` SHA `935016795f3e6908e75acbc2040a01e2e4cdb494a57c42f63a0d6eedb2372256`; `.venv/pyvenv.cfg` SHA `e6ce18340141206a9176f045f8dce3d0da8de284d916dccfa4279c445f87ea33`. Chỉ hash/read, không khẳng định actual current-import ABI/origin từ việc này.

Đọc installed METADATA/RECORD tại `.venv/Lib/site-packages/<distribution>.dist-info/`:

| Distribution/version | METADATA SHA256 | RECORD SHA256 |
|---|---|---|
| numpy2.5.4 | `e2b909d6a37d76c2bc130f528d7fed0c517322bce16dc7846b6a6df30e200403` | `93c39ea75948c53a86da219e67e4775db845e0d1f1678a40b44266b03335c605` |
| scikit-learn1.9.1 | `32e503c710a61e4e04be4edb450f9f8141233ac6af3f3db59a877667538fa4ec` | `02979e0e85d8b021871c47e54d417d00a108c2d016bd440cb63e241c346b3c59` |
| scipy1.18.1 | `c8313d18ca0168ff291fe0a3b50532f3a18b14547695e9aa7ca1c1ce6eca92dc` | `d0350965cceed1dfc69c1261b8f87a02845bf01f1b55e18cf7d426b5e3588e03` |
| joblib1.6.0 | `c5fd6509906c5795fd6724d97bc1709d1f266b78aff92c0156d6cf5ad7c045e3` | `8afc819ab0ca1981144bea4ac64ee3a4043f577f9fd3d01037909b3ea246898f` |
| threadpoolctl3.7.0 | `09b19e721560cd12246402d44e53c1ede5194b8398ef60822f02cab86ccf8d1f` | `04201bedd765fa1852bc41735c6764e362cc156e5fd0bb92ef9eb22d8403dd57` |
| psutil7.2.2 | `a263a40220d921d9cb963fc636d34f817aa2eb72c2696e3e3465d088cdb1976b` | `6dbb9a261c6a358d5d37f84ca6bd2ac4f10f600376c038538e2685a95d2cb2a3` |

Public sklearn `_logistic.py` SHA `80fb5439089025c955f032464d5c9540c5e1f2c0f0d31f80c7d8417b0169806f`, đọc constructor/fit: giữ penalty defaultdeprecated và explicit `l1_ratio=0.` để dùng L2 không FutureWarning; no `n_jobs`. Solver exactC1/lbfgs/tol1e-6/maxiter200/float64 theo module. Installed metadata và RECORD hashes **không** thay việc hash mọi installed payload byte, verify compiledABI hay actualmoduleorigin; không gọi packet này full-site attestation.

Worker phải record actualversions, sys.executable/prefix/baseprefix và module.__file__ cho NumPy/sklearn/SciPy/joblib/threadpoolctl/psutil, tất cả origin physical trong repo `.venv` (không cho inherited globalsite). Validate metadata/profile SHA trước import và actualorigins sau import. Public module hiện kiểm exactNumPy/sklearn versions từ `EdgeRuntimeBinding`; các nguồn/lock/ABI/origin guard còn thuộc worker/outer. Không import Torch để kiểm CPU; cấm Torch/pandas/nativecollector và network/subprocess sau gate (ngoại trừ process duy nhất do owned launcher tạo).

**Thread mismatch đã xác định:** helper hiện hardsets OMP/MKL/OPENBLAS=2. Không sửa helper; NEW worker set cả3='1' ngay postGO, trước NumPy/SciPy/sklearn, rồi dùng public `threadpoolctl.threadpool_limits(limits=1)` quanh fit và lưu bounded `threadpool_info()`/actualcounts. Outer giữ CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', plugins/addopts sanitized. Không tự coi inheritedenv từ outer đủ vì helper overwrite2.

## 4. Một global deadline, RAM và cleanup

Outer bắt đầu monotonic+wall trước metadata setup; total120s gồm mọi validation/import/read/prepare/fit/bootstrap/serialize/hash/cleanup/receipt. Active cutoff =outerstart+110s;10s reserve gồm ownedcleanup3s và outerfinalization7s. Helper `max_seconds =120-outerelapsed-7`, `cleanup_reserve_seconds=3`, startupgate vẫn tối đa10s, oneJob/oneworker. Worker bound active deadline bằng **min(requested outer active deadlines, owned launch.active_deadline)**; không reset120 tại worker/reader/prepare/fit. Args deadline được launcher argv SHA và dispatch receipt bind.

Đề xuất dành **8s export reserve bên trong active110**: fit limit truyền `min(110, remaining_active-8)` sau reader/prepare, phải >0; prepare/reader cũng truyền phần còn lại. Toàn bộ fit source có guard trước/sau solver và cuối outputidentity hash. Không truyền fresh110 sau imports. Nếu không còn đủ phần reserve thì STOP; không auto-stage tiếp hoặc đổi counts/C/iterations vì hết thời gian. `EdgeConfidenceResult.elapsed_seconds` hiện lấy trước final identity seal; outer full elapsed và posthash check mới là authoritative, không dùng field này làm end-to-end runtime proof.

RSS cap worker **536870912B**, available floor **1073741824B**. Parent preflight cũng cần floor+valid telemetry trước GO; worker kiểm trước/sau heavy imports, sau reader, sau prepare, trước/sau fit/export. **Gap hiện hữu:** fit module chỉ check cooperative wall, không RAM callback mỗi solver; helper có owned timeout/Jobcleanup nhưng không RSS monitor. Minimal proposed worker watchdog thread, poll0,1s, sample process RSS+Windows peak_wset và systemavailable, bounded counters/peaks (không unbounded trace). Khi vi phạm: ghi failure/resource snapshot best-effort, exit125; ROOT helper reap/Job0. Thread không được fit/refit/publish; nếu hard-exit thì actualfitcounts có thể unknown, giữ reservation2352, không ghi actual0. Poll/GIL/OS latency có overshoot: **đây là observed resource guard, không hard512MiB OS quota**. Cần ROOT review/finite mocktest của thread shutdown/failure trước actual; không thêm background service/process hoặc sửa helper đã frozen.

Worker completed chưa đủ: outer yêu cầu helper accepted+cleanupaccepted, jobactive0, popenhandleclosed, returncode0, workerowner/ready/GO/source/argv exact; failure.json/failure.log/resourcefailure/postbudgetfailure đều override success. Capturedprocess cleanup chỉ cho ownedJob, không whole-host claim. Outer checks clocks lại sau copyhash/receipt và terminalRC0; trên failure không sửa prior reports/markers thành PASS. No retries/resume/pointer publication.

## 5. Artifacts, publication và acceptance

Tất cả output mới, không pickle/checkpoint/model serialization bằng Python objects. Reservation `actual_solver_calls=null` trước imports; finalactual solver count tính `sum(record.solver_called)` từ hoàn chỉnh ledger, báo riêng2352processed slots. OOF ledger đúng272160rows ngay cả khi unsupported cóprobability/delta null; không rút denominator để xanh.

Output filenames cố định đề xuất: `reservation.json`, `runtime.json`, `resources.json`, `input-source-inventory.json`, `recipe.json`, `folds.json`, `fit-ledger.jsonl`, `baseline-oof.csv`, `edge-oof.csv`, `learner-deltas.csv`, `edges.jsonl`, `graph.json`, `worker_result.json`, `DONE.json`; failure giữ riêng. Fullfit2352records coefficient/intercept hữu hạn hoặc empty/None+reason;200bootstrap positives/count và seeds/eligibility/denominators trong756summaries. Derived baseline10080targets phải exactdedup từ27edgecopies: identity/fold/y/baseP giống nhau, không average khácprobabilities. FullOOF có cả ineligible/null rows/reasons. Graph `SUPPORTED_DAG`31 hoặc `UNSUPPORTED_EDGE_BUDGET` với partialdiagnostic, không cấpgraphbinding nếu thiếu31.

Streamwrite perrow/finiteJSON/17digitfloats; không `asdict(result)` cả272160OOF vào một bigJSON tạm. Filecap OOF96MiB, totaloutput128MiB, stdout/stderr64KiB; validate bytes ở mỗi chunk và postexit. Fsync/readbackSHA inventory trước DONE (logical marker, không crashtransaction). Worker result status `COMPLETE_CONDITIONAL_SURROGATE_PENDING_OUTER_ACCEPTANCE`; DONE không acceptance. Worker outerstatuscomplete không imply mỗi edge supported hoặc graph đủ31; missingconfidence/graph là kết quả unsupported phải công bố, không run lại cho đến đẹp.

Acceptance toàn stage: request/config+10Python sources+runtimepacket+public10input hashes before=after; exacttarget/fit/OOF/summary populations; pairedeligiblelearner estimator+label-freefold/bootstrap seed invariant; learnerfold disjoint; currentmodule recipe/source hash đúng; allfloatfinite/null reasons; noforbiddenimport/oracleaccess; resourceobservations trongcap; helperJob0/RC0/owner; terminalposthash elapsed≤120; nofailure override. Thành công chỉ là acceptedconditionaltrain-only surrogate artifacts, không calibratedP(edge true)/causalgraphtruth/OOFconfidenceNN/mainexperimentcompletion.

## 6. Blockers trước actualfit — hữu hạn

1. Chưa có hai nguồn worker/outer/config/request/runtimepacket materialized/frozen/tested; source10 còn2pendingSHA. Note này chỉ thiết kế.
2. Chưa actual NumPy/sklearn/SciPy import+ABI/origin/resource proof cho stage; metadata hashes không đủ. Purestub tests dù PASS không chứng minh publicsolver path/convergence/throughput.
3. Chưa measured 2352fits+272160OOF export có vừa active110/outer120 và RSS512MiB/free1GiB. Oldcollection8,77s không forecast fit. Nếu không hoàn tất, retainfailure/reservation, không gọi partialscores COMPLETE hay tăngcap tự động.
4. Worker observedRAM watchdog và thread1 override/helper2 mismatch cần được implement/review; không giả currenthelper tự cung cấp RAMquota.
5. Actualpublication/export code chưa có, exportreserve8s là proposal trước run, chưa đo đủ. Root phải freeze exactoutputcontract và terminalacceptance trước execution, không thông qua DONE đơn lẻ.

Không có blocker khoa học yêu cầu privilegededge labels hay thêmNN model để triển khai recipe hiện tại; blocker là finite runtime/wiring/acceptance chưa được thực thi. Không suy trước rằng có31positive eligible acyclicedges; thiếu support/budget là kết quả hợp lệ phải báo, không filler.
