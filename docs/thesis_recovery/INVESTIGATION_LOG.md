# Nhật ký điều tra append-only

## 06/11/2026 — Pass1 tái dựng nguồn

Đọc Git status/log, đề cương5trang, Paper1 5trang, Paper2 v21 6trang, source/specs và artifact summaries Development. Phát hiện proposal và simulator trong paper2, sửa kết luận tracking cũ thiếu tài liệu. Evidence trong source_inventory, PDF texts và3 notebook extracts. Paper1 notebook khác PDF về latent/controller/seeds. Không có independent advisor feedback file, dùng user message làm binding context. Không đọc Holdout rows/metrics mới.

## 06/11/2026 — Pass2 phản biện khoa học và kiến trúc

Hypotheses graph edge benefit vs local adaptation kiểm bằng P2 source/spec. Root có effect dù parent signal0, cần factorial. Retention hypothesis order-invariant được thu hẹp thành post-T linear gain scaling, không khẳng định whole route irrelevant. Continuity zero-reentry chưa được proof toàn graphs, cross-chapter counterexample planned. Junyi và Grade10 vocabulary khác, train riêng và reference mastery adapter bắt buộc. DiD High/Low không hợp lệ nếu thiếu counterfactual, thay paired λ×graph simulator design. Cập nhật04–06.

## 06/11/2026 — Pass3 critical path và tài chính

Đọc AKT checkpoint/config/training/windows/tensors/model/runner/watchdog, runtime CPU-only. Gate2 latest05/11 là164passed,40source/test hashes audit khớp. Task14 results chỉfailed14-02, no new successful pilot. Checkpoint complete-epoch only, chưa resumable mid-epoch. Tra official Modal pricing, timeouts, budgets và volumes, tách usage cap/spend limit, không gọi credits guaranteed. Cost formula bao gồm selection+refit và multiple variants. Thiết lập PlanA/B/C và deadline milestones có writing/demo/article từ sớm. Verdict tạm conditionally designed, full execution blocked.

## 06/11/2026 — Pass4 runtime và adversarial gate

Combined test collection failed4modules vì pyBKT.models thiếu trong .venv. AKT/shared/GAM attempt61pass34fail81errors liên quan basetemp/Git ownership/old notebook path. Retry theo giả thuyết mới, writable unique basetemp và per-process exact safe.directory, kết quả161pass15fail65.89s. Remaining failures checkpoint/export os.link WinError5 và GAM parity hardcoded missing original download path. Logs được giữ, chưa sửa source hoặc persistent Git config. Gate2 historical164pass còn nguyên, không tuyên bố current test green. Cập nhật readiness NOT READY và T07 highest engineering blocker. Dừng retry theo bounded investigation.

## Trạng thái đóng phiên

Tạo10tài liệu yêu cầu, TASKS25items, STATE và LOG. Evidence references bổ sung, source architecture/hyperparams chưa thay. Cần verify JSON/DAG/output completeness trước kết thúc. Next batch T01/T03/T04/T07 review và engineering sau chỉ thị, rồi contracts T02/T05. Stage1–7 không tự chạy. Không commit/stage/push.

## 06/11/2026 — Kiểm tra cuối

JSON parse PASS,25task dependency DAG PASS,13output bắt buộc tồn tại và không rỗng. Synthetic algebra retention fixture PASS. Input graph advanced31 gồm28intra/3cross, baseline25intra/0cross, không missing endpoint hoặc isolated node trong inputs P2. Map36IDs unique bao phủ đủ28nodes và8extraIDs, không duplicate. Đây là kiểm tra dữ liệu đầu vào nhỏ, không real-data benchmark rerun. Kết quả trong evidence/planning_validation.json. git diff --check exit0, chỉ có line-ending warnings cho2file đã modified trước phiên. Verdict NOT READY giữ vì scientific approvals, Paper1 revision và current filesystem/GPU recovery blockers.

## 07/11/2026 — Thiết kế Engineering Loop theo yêu cầu mới

Đọc lại AGENTS, state/task, current checkpoint source, latest Gate2 pointer và results inventory. Chưa tìm successful Task14 mới.161pass15fail là evidence06/11, không rerun lần này. Tạo11_ENGINEERING_LOOP.md với B0–B6, nghiệm thu model/lifecycle/scientific evidence tách biệt, diagnosisRQ1/RQ2 song hành engineering. User yêu cầu hoàn thiện model, local engineering được ghi nhận requested, paid execution và methodological decisions vẫn cần phạm vi xác nhận. Liệt kê input Modal/budget/cloud data rights/advisor/Paper1/team/template. Chưa sửa model hoặc launch cloud.

## 07/11/2026 — B0 engineering và chuẩn bị Colab

User giao Codex implementation toàn bộ, có thể dùng Colab bounded trước Modal. User yêu cầu commit mỗi thay đổi có phạm vi rõ. Fix GAM parity source path giữ original cell hash,1test pass,commit73b999d. Fix checkpoint/export publish dùng Windows no-overwrite rename và POSIX link+unlink,3regression tests bảo vệ existing output/concurrent publisher/permission propagation.53related tests pass41.09s,commita0bf1a7. Vì các AKT source đó có sẵn nhưng chưa track, commit tạo toàn file, không stage các module hoặc artifacts khác.

Full AKT/shared/GAM suite179pass50.98s. BKT runtime/import chưa retest. New synthetic_device_probe CPU1complete synthetic epoch/1optimizer step/400targets đạt finite update/checkpoint prediction reload/export/current-future label invariance. Đây không là mid-epoch resume hoặc Gate4. Gate2 pointer cũ không sửa, source changes cần fresh evidence trước execution real-data.

Tạo notebook Colab,builder allowlist66files,config fixtures và synthetic probe. Bundlev2 SHA64103e1c5d6895d7af38bdce2ddcf5e603710c4233f234855675610f9c5decb3. Notebook code cells compile, bundle hashes verified local. Colab CPU suite deselect đúng1test đòi Windows .venv/lockfile, ghi rõ trong runbook. Chưa có actual remote CUDA execution hoặc Colab connection. User nói quota GPU có thể4h, officialFAQ không có fixed4h cho mọi account, dùng observed quota làm operational bound. Bộ probe có timeout10phút GPU và5phút CPU suite.

Bộ Colab synthetic đã commit6ff0532. Lưu tracking/evidence scoped trong commit tiếp theo. Working tree còn nhiều nguồn và tài liệu có trước, chưa bulk-stage hoặc commit chúng.

## 07/11/2026 — Loop T11, recovery checkpoint API

Triển khai save/load/restore recovery checkpoint riêng với kind training_recovery_v1, validation epoch/step/state, giữ định dạng complete-epoch và bảo vệ output cũ. Recovery checkpoint bị từ chối bởi loader/restore dùng model selection. Test actual AKT+Adam với dropout so optimizer update tiếp theo sau restore, exact weights/loss và RNG draws CPU. Existing checkpoint tests vẫn đạt. Fullsuite186passed46.89s, evidence/recovery-suite-20261107.log. Lần đầu setup test lỗi do parent basetemp chưa có, đã tạo parent và rerun bằng directory mới, không thay implementation vì lỗi môi trường. T11 vẫn IN_PROGRESS, sampler/trainer loop và CLI chưa tích hợp, chưa khẳng định full mid-epoch lifecycle. Không thực thi cloud, dữ liệu thật hoặc Holdout.

## 07/11/2026 — Phiên engineering từ chỉ thị đính kèm

Đọc chỉ thị, AGENTS và durable state. Xác minh sys.executable/sys.prefix/pip đúng.venv, không cài dependency. Gói1 paired trace diagnostics source +9tests mới, shared suite19pass,commit40b61a6. Gói2 paired factorial identities+6tests và AST historical theta_at fixture, shared25pass,commit88db625. Actual source method hash và notebook hash trong paper2-retention-source-fixture.json, factor.43171052342907973,error1.7053e-13. Không rerun historical experiment.

Gói3 replayable shuffled-window cursor+13tests,20checks sampler/recoverypass,commit1d63b35. Bảo toàn original shuffle order, đọc/hash prefix O(prefix), no optimizer replay. Gói4 DAG delete/add/reverse +9tests,shared34pass,commit161b66b. Không gọi các graphs này degree-matched null controls.

Gói5 resumable epoch Python entrypoint+2integration tests,commit7048419. Interrupt sau step2 và resume khớp original train_epoch exact weights/loss,17targets,9windows,5updates. Caps cộng dồn, changed stream reject. Chưa nối gated CLI/selection/refit hoặc early-stopper history, chưa GPU/realdata. Intermediate fullsuite223pass41.42s, final225pass44.55s.

Source/architecture phương pháp chưa được approved giữ pending. Thêm runbook12 nêu inputs/acceptance/limitations. T06,T11,T13 còn IN_PROGRESS đúng scope. Phiên có nhiều gói được commit, chưa chạy đủ3giờ và chưa hoàn tất KLTN. Next ready batch là selection/refit/stopper integration và paired trace adapter, không có cloud spend/Holdout access.

## 07/11/2026 — Đối chiếu DeepWiki AKT theo yêu cầu

Đọc GettingStarted/Installation/RunningModels qua link từ DeepWiki home sau directopen failure. Wiki index01b7e8 khớp pinned upstream. Source/hash check và khởi tạo2models xác nhận d_ff effective upstreamCLI2048 vì utils không truyền parser d_ff1024, adapter KLTN truyền1024. Có sai khác loss reduction/lr/batch/seed/window/epoch selection. Đây là native NonRasch adaptation, không full recipe reproduction.4upstream paritytests pass8.50s. Không sửa hyperparameters/source upstream, không cài dependencies hoặc run realdata. Báo cáo13 và evidence mới ghi đầy đủ.

## 07/11/2026 — Mở rộng đối chiếu chín trang và nested pages AKT

Đọc20trang yêu cầu/liên quan,3trang con fetch failure được ghi rõ và dùng pinned source để kiểm cơ chế. Xác nhận wiki có sai lệch QA formula, event-table schema, skill/problem và header/split interpretations. DATA trả3arrays gồm student index, PID_DATA trả3arrays gồm pid. Thêm4synthetic loader/adapter contract tests, cùng native parity/causality đạt17pass11.28s. Không thay architecture/hyperparameter hoặc chạy dữ liệu thật/GPU. Báo cáo14 và JSON inventory/hash ghi chi tiết. Giữ next dependency là architecture identity, CLI recovery integration và CUDA lifecycle.

## 07/11/2026 — Sáu nested pages và tiếp tục AKT recovery

Ba trang AKT/Architecture/Attention tải được, ba trang TransformerLayer/Rasch/NonRasch tiếp tục lỗi qua direct/TOC/query. Source pinned xác minh mechanisms, report14 bổ sung gamma và zero_pad errata, commit e7144ff. Selection API thêm snapshot sau validation và restore history/early stopping/model/Adam/RNG, config/budget/best-artifact identity guards. Actual dropout AKT CPU interruption sau epoch2 khớp continuous và cùng dừng epoch3,34tests pass27.55s,commit5da4966. training.py đã có sẵn nhưng untracked, commit ghi toàn module cùng phần sửa có phạm vi. Batch recovery thêm cumulative target cap, committed-prefix state và cadence/final flush.24tests pass13.54s,commit8a9a14a. Lệnh test đầu sai tên module, giữ log rồi sửa command. Combined regression đang chạy. CLI/refit/mid-batch selection integration và cloud lifecycle còn pending. Không đổi model architecture/hyperparameters hoặc chạy dữ liệu thật/GPU.

Combined regression hoàn tất223passed114.80s, gồm tests/akt, tests/shared_kt và GAM model parity. Evidence akt-nested-wiki-engineering-final-tests.log. Đây là phạm vi collection khác full GAM suite trước, không so số test như số regression. Checkpoint cadence và epoch selection hiện là Python APIs riêng, chưa claim full CLI recovery hoặc GPU readiness.

## 07/11/2026 — Engineering CPU và bằng chứng để trích dẫn

User cho phép local CPU engineering, tổ chức files và commit changes hoàn thiện. Kiểm kê419untracked đầu phiên, gom3pytest temp trees về artifacts/akt/local-tests và đối chiếu480SHA hashes, relocation manifest giữ tại research_tracking/reports. Adapter AST nguồn Paper2, explicit mastery trace, matched degree/chapter swap và evidence verifier có tests. Fixed-stream03 có1080events paired, full package964probability/90concept mastery/60ready/22preview action changes. Empty-graph package37probability changes nhưng0decision changes. Replay04 trùng logical outputs. Closed-loop01 pilot27trajectories3240events, profile effects mixed, không CI/causal graph-only claim. Run01 superseded cho selector history, artifact giữ nguyên.239regressionpass59.38s,52shared/GAMpass3.13s sau helper closed-loop. Bổ sung CPU01–11 vào backlog, các phần method/Junyi/CLI còn mở. Không đánh dấu toàn bộ CPU scope hoặc RQ1/RQ2 hoàn tất.

Raw PDF/source extracts giữ whitespace gốc, git whitespace warnings không được sửa vào evidence lịch sử. Source inherited AKT và frozen configs đã được ghi nhận trong commit5623108 sau regression. Cấu hình/auth lưu Git không cấp quyền execution mới.

Kiểm Git byte portability phát hiện CRLF normalization của JSON đã commit. Thêm -text cho evidence/source snapshots, re-add scoped paths, commit8fd0275 giữ nguyên workspace historical bytes. Verification36output blobs và source/input snapshots PASS, JSON task IDs/dependencies PASS. Tài liệu tham khảo có sẵn được track, chỉ kiểm PDF signature/metadata, không tuyên bố đọc lại nội dung. Minimal source notebook/simulator CSVs đã track chọn lọc tại path gốc để tests tái lập. Working tree sạch trước ghi log cuối. Các open CPU tasks vẫn ghi partial/planned, không đánh dấu xong toàn scope.

## 07/11/2026 — Tiếp loop, refit và approved pilots

Refit epoch-boundary recovery thêm config/scope/selected-epochs/budget identity và actual dropout parity32tests. Gate2 generator lưu log/JUnit, reject fail/error/skip/zero-tests và source drift, snapshot pointer cũ. Pass235test cho build đầu; sau root evidence/pilot changes pass237test cho build cuối, current pointer xác minh. Prototype pathways000/111 parity và local-without-edges fixture, mechanismlambda.55 exact-source parity vàlambda0 one-step isolation,21GAMtests. User chấp thuận CPU09/10 pilot trong chat trước execution. Factorial10seeds×3profiles×4cells×120steps=14400events,62.05s. Junyi32inner-train learner,1211events,9.31s, không correctness/Holdout. Reports ghi conditional interpretation và low support. PG0effect giải thích bằng0positive-deficit/2400mechanism-on events trong pilot, không extrapolate.

Raw Junyi catalog981entries gồm2self-loops;979edges còn cycle. Truy source Paper2 và certificate tìm SCC rule đã có, AST selective source cell23 tái dựng835nodes976-edge DAG, removed3edges, test1pass. Counts consistency không chứng minh identical historical input bytes. Không sửa source/dataset/historical graph hoặc tự adopt graph mới. Lưu5run mới có README/manifest/hashes/logs và report, tổng10bundles. RQ1/RQ2 và CLI/CUDA readiness còn chưa hoàn tất.

## 07/11/2026 — Loop tiếp, support-matched controls và exact step boundary

Đọc state hiện hành và Git sạch. Thêm optional node_strata cho degree/chapter rewiring, bảo toàn joint topic/area/prefix-support-bin counts. Shared/GAM70passed9.22s. Run32inner-train×120 thực hiện3controls×10swaps, cùng1211events với pilot trước. Exposure child changed10/6/0, co-observed same-learner changed0/2/0, không diễn giải zero differences như graph-neutral. User giao chọn mức mở rộng sau proposal256×300/180s. Chọn mức đó, run completed256learners12575events5.99s; limit tests10passed13.68s, không correctness/Holdout. Corrected base649pairs575parent-first, controls650/576,644/568,645/574; degree/bin matching không giữ learner co-observation.

Sửa resumable epoch bị incomplete khi exact required steps==max_steps, thêm peek không commit cursor/hash.19sampler/resume tests passed17.30s. Gate2support-cap03failed239pass1fail do lifecycle fixture dùng actual available RAM dưới1GiB, giữ log/JUnit và khôngpublish. Inject deterministic training memory snapshot riêng trong lifecycle fixture, không sửa production guards;35pilot/training tests passed25.66s. Gate2support-cap04pass240 nhưng sau đó script mở rộng đổi build nên cần final refresh. REC01–06 contract lưu trong16_AKT_CLI_RECOVERY_CONTRACT.md, public CLI recovery chưa implemented.

## 07/11/2026 — Colab kit dependency reconstruction

Phát hiện builder cũ thiếu shared-test Paper1/2 fixtures và diagnostic scripts. Schema2 thêm allowlisted scripts/tests/small simulator inputs, notebook copies bỏ outputs/execution metadata và giữ source cells, raw source giữ nguyên. V4 được kiểm integrity nhưng suite đầu chạy khi clone chưa sẵn,66fail175pass, giữ log. Local clone2elevated attempts gặpownership,.git safe-directory không giải quyết; default clone gặpMSYSerror. Chuyển sang copy source104files có SHA trước/sau, original giữ nguyên. V4 saucopy235pass5fail1deselected do missing lock/runtime host artifacts và watchdog fixture RAM thật. Sửa unit authorization/preflight dùng synthetic dependencies, watchdog memory snapshot test-only;38targeted pass18.10s. V5AKT/shared240pass1deselected113.50s. V5GAM30pass2fail do real assignments dependency. Chuyển test-order thành no-I/O/input-immutability fixture, chỉloại frozen-assignment integration trên Colab. V6 source/dependencies AKT/shared byte-identical v5, chỉtest_core.py khác; V6GAM31pass1deselected17.92s. Kit113files, source-only notebooks, venv project dùng runtimeTorch system-site-packages, CPU worker hidesCUDA. KhôngactualColab/CUDA execution.

Main Gate2portable-kit06pass241, nofail/error/skip, current pointerverified. Archives giữ cảfailed/support-cap03 và successful04/05/06 cùngkitv4/v5/v6 manifests. PublicCLI recovery vẫn chưaimplemented, contract16 cóREC01–06.

Kiểm cuối batch:13bundles/123Git output blobs khớpSHA, require_gate2_evidence PASS_CPU241tests. TASKS bổ sungREC01–REC06 vớideps,42task DAG được kiểm khôngcycle. Working tree sạch trước ghi verification cuối. Kitv6 được xác minh local theo hai suite, actualColab/CUDAfalse. RQ và publicCLI recovery chưa complete.

## 07/11/2026 — Recovery schema và source contract

Tiếp loop theo user authorization 1–2 giờ. RecoveryOptions default off, source envelope SHA/path/semantic/input/cumulative-wall validation không import Torch. 21contract tests và 48contract+runner tests pass. Log/giới hạn trong17_AKT_RECOVERY_ENGINEERING_LOG.md. Chưa nối CLI; Gate2 build cũ stale. Không real-data training/Holdout/cloud.

## 07/11/2026 — Recovery nối public CLI trên synthetic CPU

Selection/refit dùng cùng train_epoch accounting, cursor/RNG/Adam/early-stopping snapshot, fresh attempt và terminal parent envelope. CLI04 2passed83.91s sau3lần sửa harness (giữ logs); prediction export/weights bit-identical với continuous, source immutable. Regression02 94passed36.54s sau default-off compatibility fix; snapshot01 16passed27.35s sau giảm duplicate Torch loads. Chưa Gate2 refresh cho build mới, chưa real-data/GPU. Runbook docs/akt-recovery-runbook.md.

## 07/11/2026 — Common-population sensitivity cho Trap3

Kiểm10pure order tests, rồi45GAM tests6.29s. Tái dùng nguyên3controls; đọc lại đúng approved256×300prefix,12575events,2.39s, reproduces original control summaries. Fixed incoming-degree opportunities + equal learner weights, missing/ties riêng;239eligible learners1361opportunities. Prior fraction chỉđổi1/7/1learners, common coverage569/564/566opportunities96/96/95learners. Identitycontrol0. KhôngCI/p-value/causalclaim, khônggraphgeneration/training/Holdout. Artifact bundle và report cpu_common_population_20261107.md.

## 07/11/2026 — Nghiệm thu cuối recovery và lưu bằng chứng

Gate2-07 271pass2fail do Windows long temp path, khôngpublish; sửa short temp names. Review sửa early-failure budget lineage;51parent/runner pass14.68s. Gate2-08 final274pass0fail/error/skip217.71s, source/lock/upstream stable, pointerverified. Archive cpu-akt-recovery-20261107-01 có24outputs và exact model/Adam/RNG/prediction proof cho2CLI cases. V7 kit120files SHA018888bbee3718f0c9ce9222ae079315aefca67d176e4d2be8ec49d78f69c9cc verified ZIP only. REC01–06/CPU11 complete trong phạm vi CPU synthetic; khôngreal-data AKT/GPU/Holdout. RQ1/2 PARTIAL, RQ3 chưatraining/evaluation. Next: simulator/mastery interface and confirmatory protocol, remote lifecycle when runtime ready.

## 07/11/2026 — Simulator interface bắt đầu

Đọc state và source KT/window/selector. Không lấy Junyi checkpoint gán sang simulator, không chọn threshold. SIM01 có domain/bank identity, predict ticket→observe, pure probes, snapshot/reset, missing-reference coverage;10contract tests pass0.18s. SIM02 native tests đang chạy; fixture đầu14pass1fail vì shared strict vocabulary rejects OOV trong test setup, sửa fixture dùng explicit AKT OOV encoding, không nới production vocabulary. Source mới làm Gate2 cũ stale; full refresh sau stable batch.

## 07/11/2026 — Native online parity và double re-anchor bug

SIM02 actual AKT fixture train8events≤2updates, SHA/domain/recipe/vocab/selected-checkpoint guards; frozen model and RNG, snapshot/reset/crosslearner verified. New regression xác nhận export double-window bug H3/T2,3/11predictions maxabs0.00178698. Direct predict_window sửa semantics, default H100/T100205events+OOV legacy/direct parity1e-6.36tests pass24.80s sau fake adapter API update; failed logs giữ. Không realdata/GPU/Holdout hoặc sửa historical artifacts.

## 07/11/2026 — Paper2 bank lifecycle và architecture boundary

SIM03 dùng28concept/84item, arithmetic labels,168targets1epoch1update d16CPU. Run01 11.99s, run02 11.07s sau metadata/binding hardening, cả2complete. Native state và reference scores trùng exact; full JSON khác vì checkpoint SHA/telemetry/provenance, repeat proof tách đúng layers.19native/contract tests pass19.86s gồm delayed-query invariance: original AKT không nhận elapsed time. Không dùng raw reference score làm mastery/retention. Report simulator_kt_interface_20261107.md. Gate2-09 đangchạy, không claimPASS sớm.

## 07/11/2026 — Interface gate293 và bước hiệu năng có kiểm soát

Gate2-09 293passed0fail/error/skip264.44s, pointerverified. Archive20outputs, sourcev1script khôi phục bỏ metadata bổ sung và verify exact recordedSHA; dependencies refGit3c3d5a5. SIM04 complete. Kitv8 125files43f6a091888e75fccaf875c464b60e4bb4c6747c004c9a47f49eba06734dbea8, ZIPintegrityonly. NextSIM05: batch independent reference windows under existing batchcap, same history perquery, no fabricatedevents; target equivalence before performanceclaim.

## 07/11/2026 — Independent batching và final software gate296

SIM05 native predict_windows/predict_many và generic probe_many giữ samehistory riêng cho mỗi candidate, OOV/null đúngvịtrí, nofakeevents.41targeted tests pass29.45s. Run03-batch train168targets1update,84coldqueries84→42nativecalls cap2, maxabsdelta5.96e-8,0.815→0.393s d16fixture; khôngGPUextrapolation. Gate2-10 final296pass0fail/error/skip292.02s, source/lock/upstream stable, pointerverified. Archive cpu-sim-kt-batch-gate-20261107-01 có11outputs, gate09archive20outputs giữ riêng. Kitv9 125files7e8caab24cb7b2b92cf46fa04f37109a9419146d94b313152cee5de8e3a955fd ZIPintegrityonly. SIM01–05completeCPU, S04/S05 và simulatedtrainingdataquality còn mở.

## 07/11/2026 — Hợp nhất báo cáo và chốt quy ước cấu trúc

User duyệt dọn giới hạn và duy trì cấu trúc. Di chuyển JSON bootstrap rootreports→research_tracking/reports, rawSHAe7c89371429068b9cbe6c3b0029dd9f531417425e510823fa84336087f68c017 trước/sau trùng, không tính lại. Relocation manifest lưu cả raw/Git SHA trước do EOL khác; -text giữ bytes gốc ở path mới. Rootreports bỏ sau khi rỗng; pytestcache accessdenied nên giữ, không đổiACL/retry. Phân loại bằng mục lục reports/README, cập nhật109links/registry2refs và thêm quy ước AGENTS.20bundles196outputs nguyênhash; sourceGatePASS vẫngiữ. Không sửa source/model/dataset, không mở Holdout hoặc chạy thí nghiệm.

## 07/11/2026 — DATA01–03: simulated split/schema và graph information boundaries

Tiếp theo state sau SIM05, không lặp cleanup. Thêm explicit4-role split với namespace/RNG families, immutable observable schema/role-shard audit/train projection (không giả Junyi fold). Graph audit reuse đúng AKT window geometry, past-only và OOV; confidence provenance/oracle-reference guard, graph-off/empty/zero/no-support controls. Fixture01/02/03 lần lượt65/69/70pass,0fail/error/skip; mỗi bundle7outputs,64arithmetic events,0NNsteps. Prefix counterexample: effective context unchanged; full-history mean0.75→0.625. Review thêm query/config/vocab hashes, multi-parent normalization và chặn oracle subclass. Không empirical benefit/independence claim. Gate2 cũ stale; explicit CPU software-suite timeout tối đa600/default300, dự toán420s cho refresh; không thay training caps. DATA04 đang chờ full source-bound gate/archive/commit.
