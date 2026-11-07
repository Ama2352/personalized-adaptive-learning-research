# Mục lục báo cáo và phân tích KLTN

Đây là nơi thống nhất cho báo cáo/phân tích tổng hợp. Bằng chứng theo run nằm ở [../runs](../runs/); dữ liệu/models/predictions lớn giữ ở artifacts/experiments theo [bản đồ repository](../../docs/REPOSITORY_MAP.md). Các file dưới đây có vai trò khác nhau, không phải tất cả đều là kết luận nghiên cứu hoặc chương luận văn.

## Baseline đã có kết quả

| Nội dung | Báo cáo đọc được | Số liệu tổng hợp |
|---|---|---|
| BKT Junyi | [BKT results](../../docs/bkt-baseline-results.md) | Nguồn CV/refit lịch sử trong experiments, xem báo cáo |
| BKT–GAM-KT Development CV | [Bản ngắn](../../docs/bkt-gam-kt-benchmark.md), [bản chi tiết](../../docs/research/bkt-gam-kt-baseline-benchmark-report.md) | [Paired bootstrap JSON](paired_cluster_bootstrap_bkt_gam.json) |

JSON bootstrap chuyển từ root `reports/` với bytes/SHA giữ nguyên. [Hồ sơ relocation](report_relocation_20261107.json) lưu vị trí cũ/mới và hashes; số liệu không được tính lại. Bootstrap hai baseline graph-free không chứng minh graph hoặc chính sách học có ích.

## RQ1/RQ2 — Chẩn đoán và pilot

- [cpu_rq12_20261107.md](cpu_rq12_20261107.md): chuỗi prediction→decision, graph package, retention/re-entry và giới hạn nguồn.
- [cpu_pilots_20261107.md](cpu_pilots_20261107.md): approved bounded factorial và Junyi order pilots.
- [cpu_matched_controls_20261107.md](cpu_matched_controls_20261107.md): graph controls và độ phủ của thay đổi cạnh.
- [cpu_common_population_20261107.md](cpu_common_population_20261107.md): so sánh trên cùng learner/child opportunities, missingness và weak exposure.

Đọc run IDs/manifests được mỗi báo cáo chỉ ra. Pilot không tự trở thành confirmatory result; không suy lợi ích nhân quả từ logged Junyi order.

## Kỹ thuật và tính tái lập

- [Agent chạy Colab MCP](../../docs/akt-colab-mcp.md): kết nối/thực thiT4 đã xác nhận trực tiếp; [44outputs](../runs/colab-mcp-preflight-20261107-01/README.md) giữ failedpreflight435pass/7fail/8errors, chưa CUDAmodel/Gate4.

- [Colab recovery readiness](colab_recovery_readiness_20261107.md): sửa CUDA RNG restore từ source/regression, CPU recovery qua3processes exact,19mockguards và Gate407. Kitv11; cập nhật notebookVSCode mộtfile/20localchecks, chưa actualColab/CUDA, không dùng Modal credits.
- [Modal setup](../../docs/akt-modal-setup.md): kết nối local và trần30USD/tháng; [SDK proof](../runs/cpu-modal-client-20261107-01/README.md) chỉ kiểm projectvenv/CLI/dependencies, chưa auth hoặc cloud execution.
- [Modal access readiness](modal_access_readiness_20261107.md): token/workspace/environment đã kiểm bằng API chỉ đọc; vẫn chưa chạy compute hoặc xác minh CUDA/budget bằng API.
- [Colab-first runbook](../../docs/akt-colab-synthetic-runbook.md): ưu tiên kiểm CUDA trênColabfree; [local notebook guard proof](../runs/cpu-colab-first-20261107-01/README.md) chỉ8mockcases và1packagingtest, chưa actualremoteGPU.
- [simulator_collection_runner_20261107.md](simulator_collection_runner_20261107.md): collector Paper2 train-only và role-aware KT windows/collation; fixture engineering, chưa là corpus/full trainer hoặc research benefit.
- [simulator_data_graph_boundaries_20261107.md](simulator_data_graph_boundaries_20261107.md): split/schema cho dữ liệu mô phỏng và graph-context history scope; fixture kỹ thuật, chưa là CG-AKT efficacy.
- [simulator_kt_interface_20261107.md](simulator_kt_interface_20261107.md): typed session/query/checkpoint bridge, export fix, frozen inference và independent batching. Đây là engineering evidence, không là CG-AKT efficacy.
- `git_evidence_verification_*.json`: đối chiếu output hashes với bytes trong Git.
- `colab_bundle_*_verification_*.json`, `colab_upstream_*_inventory_*.json`: kiểm bundle/dependency/portability; không tự chứng minh đã chạy Colab/CUDA.
- Các JSON có tên `coverage`, `followup`, `diagnostics_verification`: số liệu kiểm tra hỗ trợ; đọc scope trong file và báo cáo tương ứng, không lấy tên file làm verdict nghiên cứu.

## Draft, lịch sử và hồ sơ vận hành

- [CPU09_CPU10_PROTOCOL_DRAFT.md](CPU09_CPU10_PROTOCOL_DRAFT.md): protocol pilot/draft; phạm vi được duyệt và confirmatory design là hai việc riêng.
- [initial_audit.md](initial_audit.md): snapshot audit ban đầu; không dùng inventory cũ thay trạng thái mới.
- [report_relocation_20261107.json](report_relocation_20261107.json), `temporary_relocation_*.json`, `uncommitted_inventory_*.json`: hồ sơ sắp xếp workspace, không phải kết quả mô hình.

## Quy ước duy trì

1. Bản diễn giải theo chủ đề có tên rõ và ngày; thêm vào đúng mục ở đây. JSON tổng hợp đi cùng báo cáo hoặc bundle có provenance.
2. Một execution mới dùng run ID mới trong `research_tracking/runs/`; không tạo thêm một root `reports/` hay thư mục tên chung chung để chứa cùng loại file.
3. Không đổi số liệu, seed hoặc protocol khi di chuyển file. Ghi inventory trước, so SHA sau và cập nhật chỉ mục; manifests/models/predictions/bundles lịch sử giữ nguyên.
4. Bản luận văn sau này trích nhận định có scope, bảng/số liệu và run ID; không đưa toàn bộ debug logs vào thân báo cáo.

## Bổ sung từ các bundles local đã đóng — 07/11/2026

Đã kiểm SHA-256 đủ 114 outputs của bốn bundles được dẫn dưới đây. Báo cáo tổng hợp, exploratory analysis và kiểm phần mềm có mức bằng chứng riêng; các mục lịch sử phía trên giữ nguyên.

- [Graph residual/gate prototype](graph_gate_prototype_20261107.md) và [factorial pilot uncertainty](factorial_pilot_uncertainty_20261107.md), [bundle 32 outputs](../runs/parallel-graph-diagnostics-20261107-01/README.md): 75 CPU synthetic cases cho kernel; 10 seed blocks/profile với joint resampling post-hoc. Chưa native CG-AKT/training, chưa formal population CI hoặc efficacy.
- [Platform fixtures](colab_platform_fixtures_20261107.md) và [RQ1/RQ2 evidence synthesis](rq12_evidence_synthesis_20261107.md), [bundle 38 outputs](../runs/cpu-portability-gate-20261107-01/README.md): Windows Gate15 462 pass, v12 mocked harness/dependency checks, one-row DuckDB version/API contrast và snapshot aggregates. Không suy full runtime acceptance hoặc confirmatory graph benefit từ các kiểm này.
- [Paper1 revision reconciliation](paper1_revision_reconciliation_20261107.md), [bundle 14 outputs](../runs/paper1-revision-audit-20261107-01/README.md): source/PDF/Git/candidate inventory thu hẹp local provenance; chưa exact reproduction, Q01/S01 vẫn mở.
- [SAKT core readiness](sakt_core_readiness_20261107.md), [bundle 30 outputs](../runs/sakt-core-engineering-20261107-01/README.md): source-bound final 37 CPU synthetic cases, random weights và 0 optimizer steps. Chưa fitted baseline/adapter/trainer; Gate15 và kit v12 không chứa SAKT.

Chỉ mục này không thêm GPU/runtime verdict khi chưa có evidence bundle đã đối chiếu; không tự thông qua S04/S05 hoặc bỏ required baselines.

## Nghiệm thu GPU thực tế07/11

- [colab_cuda_acceptance_20261107.md](colab_cuda_acceptance_20261107.md): actual ColabT4 CPU505pass,400target lifecycle và controlled fresh-process CUDA recovery; trả đủ44outputs/SHA, không fulltraining/Gate4.
- [colab_cuda_adversarial_review_20261107.md](colab_cuda_adversarial_review_20261107.md): kiểm độc lập source/coverage và các blockers Linuxruntime, mainworker lifecycle, throughput, Modal durability/budget.
- [Bundle CUDA68outputs](../runs/colab-cuda-synthetic-20261107-01/README.md) giữ raw receipts/logs/JUnit/manifests/source snapshots, không heavy checkpoints trong Git. Các failures preflight vẫn giữ nguyên trong bundle lịch sử.

## Runtime Linux, main worker CPU và SAKT inference — batch bắt đầu07/11

- [Runtime contract](akt_linux_runtime_contract_20261107.md), [main worker](akt_main_worker_lifecycle_20261107.md), [bundle](../runs/cpu-linux-worker-20261107-01/README.md): targeted63cases và2newworker cases; fullGate513pass/269.98s, source-bound WindowsCPU. Linuxbranches mocked, chưa actualLinux/CUDA worker.
- [SAKT adapter](sakt_adapter_readiness_20261107.md), [bundle ban đầu](../runs/sakt-inference-engineering-20261107-01/README.md), [checkpoint followup](../runs/sakt-checkpoint-payload-20261107-01/README.md):89CPUcases=37core+52adapter,0optimizersteps; random/unverifiedweights không fitted benchmark hoặc completeOnlineSessionbridge.
