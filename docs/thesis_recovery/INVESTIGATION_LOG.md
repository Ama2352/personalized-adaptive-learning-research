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
