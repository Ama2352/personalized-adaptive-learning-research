# Bản đồ repository và bằng chứng cho báo cáo KLTN

Đối chiếu ngày07/11/2026 từ cây thư mục, entrypoints trong `src/`/`scripts/`, README và manifest hiện có. Tài liệu này là điểm bắt đầu để tìm nội dung; không thay thế protocol hoặc kết quả gốc. Không di chuyển/xóa artifact trong lần lập mục lục này.

## Khi viết báo cáo, mở gì trước?

| Cần viết/kiểm tra | Đọc bản diễn giải | Đối chiếu bằng chứng gốc |
|---|---|---|
| Kết quả baseline BKT | [BKT results](bkt-baseline-results.md) | [BKT Development CV](../experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/); vị trí refit/Test lịch sử xem README của [BKT experiments](../experiments/bkt_baseline/README.md) |
| So sánh BKT–GAM-KT | [Bản ngắn](bkt-gam-kt-benchmark.md), [bản nghiên cứu chi tiết](research/bkt-gam-kt-baseline-benchmark-report.md) | [BKT CV](../experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json), [GAM CV](../experiments/gam_kt/results/wsl_cpp/cv/cv.json), [bootstrap JSON](../research_tracking/reports/paired_cluster_bootstrap_bkt_gam.json) |
| RQ1/RQ2: prediction → decision, graph package, retention/re-entry | [Chẩn đoán nguồn](../research_tracking/reports/cpu_rq12_20261107.md), [factorial/pilot](../research_tracking/reports/cpu_pilots_20261107.md) | [Các run CPU](../research_tracking/runs/); đặc biệt [factorial](../research_tracking/runs/cpu-factorial-20261107-01/) và [closed-loop diagnostic](../research_tracking/runs/cpu-closedloop-20261107-01/) |
| RQ2: thứ tự Junyi và graph controls | [Matched controls](../research_tracking/reports/cpu_matched_controls_20261107.md), [common population](../research_tracking/reports/cpu_common_population_20261107.md) | [Cohort mở rộng](../research_tracking/runs/cpu-junyi-controls-20261107-02-expanded/), [common-population run](../research_tracking/runs/cpu-junyi-common-20261107-01/) |
| Kỹ thuật AKT: recovery, simulator interface, batching | [Recovery log](thesis_recovery/17_AKT_RECOVERY_ENGINEERING_LOG.md), [báo cáo interface](../research_tracking/reports/simulator_kt_interface_20261107.md) | [Recovery proof](../research_tracking/runs/cpu-akt-recovery-20261107-01/), [interface/batch gate](../research_tracking/runs/cpu-sim-kt-batch-gate-20261107-01/) |
| Collector/KT simulator và semantic domain | [DATA05–07](../research_tracking/reports/simulator_collection_runner_20261107.md), [hợp đồng](thesis_recovery/19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md) | [Gate401/source/parity](../research_tracking/runs/cpu-sim-collector-gate-20261107-01/) — engineering fixture, chưa full corpus/trainer |
| Modal, credentials local và ngân sách30USD/tháng | [Hướng dẫn kết nối](akt-modal-setup.md), [costplan](thesis_recovery/07_GPU_TRAINING_AND_COST_PLAN.md) | [Local SDK proof](../research_tracking/runs/cpu-modal-client-20261107-01/) — chưa auth/GPU/cloudspend |
| Đề cương/RQ, kế hoạch và phần còn thiếu | [Truy vết yêu cầu](thesis_recovery/02_RESEARCH_TRACEABILITY.md), [experiment matrix](thesis_recovery/05_EXPERIMENT_MATRIX.md), [backlog](thesis_recovery/TASKS.json) | Đây là quản lý/thiết kế nghiên cứu; không dùng làm bằng chứng một thí nghiệm đã thành công |

Baseline prediction, pilot chẩn đoán và kiểm thử phần mềm là ba loại bằng chứng khác nhau. Các tests AKT hoặc fixture train168targets không chứng minh CG-AKT cải thiện học tập. Các phân tích Junyi order chưa chứng minh lợi ích nhân quả của graph. Chưa có báo cáo kết quả đầy đủ trả lời cả ba RQ hoặc bản luận văn hoàn chỉnh trong những đường dẫn này.

Các báo cáo có ngày cũ là snapshot lịch sử. Ví dụ bản benchmark30/10 từng ghi chưa tìm thấy proposal; điều đó không mô tả inventory hiện tại. Dùng tài liệu truy vết yêu cầu ở trên cho phạm vi KLTN hiện hành, không lấy mục tiêu baseline trong `_context/` làm toàn bộ đề tài.

## Vai trò của từng thư mục

| Thư mục | Lưu gì? | Còn dùng không? |
|---|---|---|
| `research_tracking/` | Chỉ mục tiến độ, claim→evidence, hạn chế khoa học, diễn giải các đợt nghiên cứu và bundles bằng chứng | **Đang dùng**; điểm tra cứu nghiên cứu hiện hành |
| `research_tracking/reports/` | Markdown phân tích/audit theo chủ đề, JSON kiểm integrity/coverage/portability và một số draft protocol | **Đang dùng**; không phải mọi file là kết quả thực nghiệm hoặc chương luận văn |
| `research_tracking/runs/` | Một thư mục/run ID: README, manifest, log, kết quả nhỏ và SHA của nguồn/outputs | **Đang dùng**; bằng chứng có thể đối chiếu khi viết; có cả pilot, replay, reconstruction và archive kiểm thử |
| `reports/` ở gốc — vị trí cũ | Đã chuyển JSON bootstrap vào research_tracking/reports; folder cũ đã bỏ sau khi rỗng | Xem [relocation manifest](../research_tracking/reports/report_relocation_20261107.json); không tạo lại |
| `docs/` | Hướng dẫn chạy, protocol/data semantics, provenance, báo cáo baseline và thiết kế | **Đang dùng**; phần viết cho người đọc, không phải toàn bộ là kết quả |
| `docs/thesis_recovery/` | Kế hoạch tổng thể, audit, kiến trúc, quyết định, backlog và state để tiếp tục engineering/research | **Đang dùng**; phương án đề xuất không tự thành methodology đã được duyệt |
| `docs/thesis_recovery/evidence/` | Bản trích tài liệu/audit và các log kiểm kỹ thuật từ quá trình điều tra | **Giữ lịch sử**; với đợt đã đóng gói, ưu tiên trích run bundle có manifest thay vì tìm giữa mọi log rời |
| `_context/` | Mục tiêu, quyết định và evaluation protocol của **baseline BKT ban đầu** | **Còn giá trị tham chiếu/ràng buộc BKT**; không là dashboard hoặc protocol chung mới cho RQ1–RQ3 |
| `artifacts/` | Dữ liệu phái sinh/splits, sidecar, source phụ thuộc, runtime/gate evidence, kit Colab, cùng cache/temp | **Đang được code sử dụng**; không thể coi toàn bộ là cache để xóa |
| `experiments/` | Config/authorization và kết quả đầy đủ theo model/run: metrics, models, checkpoints, predictions, logs | **Đang dùng**; nhiều kết quả gốc nằm ở đây, phần lớn giữ local |
| `notebooks/` | Hiện có notebook kiểm synthetic CPU/CUDA trên Colab | **Đang dùng cho kiểm runtime**, không phải bằng chứng đã train GPU hoặc notebook tổng hợp cả luận văn |
| `scripts/` | Entry points chạy/audit/build/verify; xem nhóm bên dưới | **Đang dùng**; script không tự là kết quả đã chạy |
| `src/` và `tests/` | Implementation và kiểm thử tương ứng | **Đang dùng**; kết quả test cần log/manifest đi kèm |
| `paper1/`, `paper2/` | Source/artifacts/PDF từ nghiên cứu trước; một số notebook và simulator inputs vẫn là dependency của adapter/audit | **Đang được tái sử dụng**; không chuyển cả hai sang archive hoặc chỉnh source lịch sử |
| `ref-papers/` | Tài liệu tham khảo | Tham chiếu học thuật, không phải kết quả của nhóm |
| `third_party/` | Dependency vendored, gồm pyBKT đã vá và provenance/license | Dependency, không phải dữ liệu hoặc báo cáo |

Không có cơ sở để bỏ nguyên một trong sáu thư mục `_context`, `artifacts`, `experiments`, `notebooks`, `scripts`, `research_tracking`. Việc chỉ dùng ở giai đoạn tái lập/historical cũng là một vai trò cần giữ.

## Những chỗ trong artifacts đang quan trọng

| Đường dẫn | Công dụng đã đối chiếu |
|---|---|
| [artifacts/bkt_baseline/derived/canonical](../artifacts/bkt_baseline/derived/canonical/) | Interaction data đã xử lý; được pipeline KT/diagnostic dùng làm đầu vào |
| [artifacts/bkt_baseline/splits](../artifacts/bkt_baseline/splits/) | Learner assignments/split identity dùng chung; không tự chia lại hoặc xóa |
| [artifacts/gam_kt/derived/source_map](../artifacts/gam_kt/derived/source_map/) | Sidecar phục vụ GAM-KT và đối chiếu lineage |
| [artifacts/akt/dependencies/upstream](../artifacts/akt/dependencies/upstream/) | Source AKT ghim commit, được wrapper load trực tiếp; không là cache tải xuống có thể bỏ tùy ý |
| [artifacts/akt/preflight](../artifacts/akt/preflight/) | Runtime/source/software gate reports và logs. `gate2-current.json` trỏ evidence hiện hành, phải kiểm cả hashes trước execution |
| [artifacts/akt/colab](../artifacts/akt/colab/) | Các kit ZIP source/fixture và kiểm portability; build ZIP không đồng nghĩa đã chạy Colab |
| [artifacts/akt/local-tests](../artifacts/akt/local-tests/), [tmp](../artifacts/akt/tmp/), [pip-cache](../artifacts/akt/pip-cache/) | File làm việc/test/cache; ứng viên dọn có kiểm soát **sau** khi xác định file cần tái lập và đã lưu inventory/evidence |

Một số kết quả BKT đã được relocation sang `experiments/bkt_baseline/results/wsl_cpp/`. Vì vậy không lấy tên `artifacts/` để suy rằng mọi kết quả BKT chính thức đều còn ở đó. Xem [relocation summary](../experiments/bkt_baseline/relocation_summary.json); không di chuyển lần nữa chỉ để đồng nhất tên thư mục.

## Scripts và notebooks được dùng ở đâu?

- [scripts/research](../scripts/research/): source/simulator diagnostics, bounded CPU pilots, Junyi controls và simulator–KT interface fixture.
- [scripts/akt](../scripts/akt/): kiểm runtime, refresh Gate2, đóng gói source Colab và synthetic device probe.
- [scripts/wsl2](../scripts/wsl2/): runner/reproduction của BKT C++ trên WSL. Có script đánh giá Test lịch sử; không chạy lại chỉ để xem báo cáo.
- [scripts/bootstrap_bkt_gam_cv.py](../scripts/bootstrap_bkt_gam_cv.py): thống kê paired learner bootstrap trên predictions Development đã lưu; JSON bootstrap đã lưu tại research_tracking/reports. Script nhận `--output`; lần tái lập mới cần output riêng, không ghi đè JSON lịch sử hoặc tạo lại root reports.
- [notebooks/akt_colab_synthetic.ipynb](../notebooks/akt_colab_synthetic.ipynb): giao diện chạy kiểm trên Colab; log/outputs sau execution mới là bằng chứng. Notebook nguồn Paper1/2 nằm trong hai thư mục paper riêng, không phải root `notebooks/`.

Một số script nằm bên trong run archives là bản lịch sử, có thể chứa đường dẫn cũ. Ưu tiên entrypoints tại `scripts/` và runbook hiện hành, không tự chạy script bất kỳ trong folder kết quả.

## Đọc một bundle và trích vào KLTN

Ví dụ [cpu-junyi-common-20261107-01](../research_tracking/runs/cpu-junyi-common-20261107-01/):

1. Đọc `README.md` để biết câu hỏi, dữ liệu, phạm vi và giới hạn.
2. Đọc `manifest.json` để lấy run ID, loại run, nguồn/input SHA và outputs SHA.
3. Đọc `common_population.json` để đối chiếu số liệu; đọc [báo cáo diễn giải](../research_tracking/reports/cpu_common_population_20261107.md) để hiểu estimand/coverage.
4. Khi viết: dẫn bảng/kết luận của báo cáo, ghi run ID và phiên bản/source hash trong phụ lục tái lập. Không đưa mọi debug log vào thân luận văn.

Ví dụ câu diễn giải phù hợp: “Trong pilot giới hạn này, graph controls chỉ thay đổi prior-order score của một số ít learner; kết quả chưa đủ kết luận graph trung tính.” Không đổi thành “graph không giúp học” vì pilot này không đo causal instructional benefit.

`runs/` hiện có20bundles với196outputs được kiểm hash trong Git tại [báo cáo kiểm chứng](../research_tracking/reports/git_evidence_verification_simulator_20261107.json). Đây **không phải20thí nghiệm khoa học độc lập**: có replay, phiên bản kiểm thử và archive. Trạng thái `completed` không tự chứng minh giả thuyết nghiên cứu đúng. Số lượng là snapshot ngày07/11, không phải chỉ tiêu hoàn thành.

## Quy ước lưu tiếp theo

- Bản phân tích/bảng diễn giải mới: `research_tracking/reports/`; cập nhật [mục lục phân loại](../research_tracking/reports/README.md).
- Bằng chứng một lượt chạy nhỏ: `research_tracking/runs/<run-id>/`, có README/manifest/hash; run cũ giữ bất biến.
- Models/checkpoints/predictions/logs lớn: output theo run trong `experiments/<model>/results/`; bundle chỉ tham chiếu đường dẫn/hash và kết quả nhỏ cần review.
- Đầu vào phái sinh, source phụ thuộc và runtime working files: `artifacts/<model>/` theo vai trò rõ ràng.
- Protocol/runbook/thiết kế: `docs/`; kế hoạch và state liên tục của đợt recovery ở `docs/thesis_recovery/`.
- Không mở thêm các thư mục top-level kiểu `reports_new`, `results_latest` hoặc `final_v2` để lưu cùng loại nội dung. Root reports đã được hợp nhất; quy ước này cũng được ghi trong AGENTS.md để các vòng engineering tiếp theo duy trì.

## Thư mục môi trường/công cụ

`.venv/` là Python environment đang sử dụng. `venv/`, `dataset/`, `artifacts/bkt_baseline/` và `.wsl/JunyiBKT-Ubuntu/` là các vùng được AGENTS bảo vệ; không dọn khi chưa có yêu cầu rõ. `.pytest_cache/`/`__pycache__/` là cache, không là evidence. `.superpowers/` là metadata công cụ hỗ trợ; `docs/superpowers/` giữ specs/plans của các giai đoạn trước. Không dùng những kế hoạch đó thay thế [backlog hiện hành](thesis_recovery/TASKS.json). Đây không phải một đợt kiểm toán để xác nhận mọi file cache hoặc metadata đều có thể xóa.

Nguồn đối chiếu chính: [AKT config](../src/knowledge_tracing/akt/config.py), [authorization](../src/knowledge_tracing/akt/authorization.py), [GAM runner](../src/knowledge_tracing/gam_kt/runner.py), [Paper2 reference loader](../src/knowledge_tracing/paper2_reference.py), các README experiments và manifests trong research_tracking/runs. Chỉ kiểm mục lục/nguồn và báo cáo đã lưu; không chạy lại thí nghiệm hoặc mở prediction-level Holdout trong lần này.

## Đợt sắp xếp07/11

Chỉ di chuyển JSON bootstrap về nơi thống nhất, cập nhật locator/index, ghi quy ước trong AGENTS và bỏ root reports sau khi xác nhận rỗng. .pytest_cache giữ nguyên vì quyền truy cập bị chặn, chưa xác minh nội dung; không thay ACL hoặc retry xóa. Trước/sau có inventory SHA; nội dung thống kê và bundles/manifests/models/predictions cũ giữ nguyên. Không dọn artifacts/akt/local-tests hoặc tmp vì một số file còn được evidence/resume inventory tham chiếu.
