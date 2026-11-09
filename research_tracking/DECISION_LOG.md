# Nhật ký quyết định nghiên cứu

Chỉ ghi quyết định rõ trong tài liệu/config/run evidence. Không suy đoán chủ thể và không gán ngày lịch sử nếu nguồn không ghi.

| ID | Ngày được chứng minh | Quyết định | Cơ sở | Hệ quả/giới hạn |
|---|---|---|---|---|
| DEC-001 | Chưa xác định trong _context | Standard CAHLR/pyBKT 1.4.3; one model/exercise; correct; num_fits=1, forgets=false, tol=.005, maxiter=100, seed 42. | _context/decisions.md, protocol, CV manifest. | Historical baseline; 11 refit hit maxiter vẫn báo riêng. |
| DEC-002 | Chưa xác định | Global split by user 80/20 seed 42; 5 Dev folds; time_done/source_row; predict-before-update. | _context/evaluation_protocol.md; manifests. | BKT/GAM comparability; không tune bằng Test. |
| DEC-003 | Chưa xác định | suggested chỉ subgroup; unseen BKT prediction null, loại khỏi fitted denominator. | _context notes, protocol, BKT JSON. | Không gọi suggested predictor hoặc causal treatment. |
| DEC-004 | Chưa xác định; documented trong GAM protocol tháng 10-2026 | GAM Junyi benchmark graph-free; graph/adaptation/time decay off; fallback tách khỏi supported/common-row. | docs/gam-kt-integration.md; CV JSON. | Không đại diện Graph-GAM-KT hoặc graph benefit. |
| DEC-005 | 2026-10-30 theo bootstrap metadata | GAM−BKT learner-clustered bootstrap, 1,000 draws, seed 20261030, unweighted fold difference. | research_tracking/reports/paired_cluster_bootstrap_bkt_gam.json. | Conditional CI; no AUC CI/Holm. |
| DEC-006 | 2026-11-01 theo retry report | Mỗi AKT smoke cần run ID/config/authorization riêng; smoke không đồng nghĩa CV/full fold. | docs/akt-task13-smoke-retry-20261101.md; experiments/akt/README.md. | Preserve failed attempts; không mở rộng auth ngầm. |
| DEC-007 | 2026-11-04 theo config/auth | AKT pilot bounded trên Development, caps cohort/targets/time/RSS/RAM; không holdout/CV. | docs/akt-pilot-readiness.md và pilot config/auth. | Run14-02 failed; authorization không phải result. |
| DEC-008 | 2026-11-04 | Agent 2 chỉ tạo tracking trong research_tracking; không sửa code/data/artifacts, không chạy experiment/test. | Yêu cầu audit và repo rules. | Gaps chuyển cho nhóm xử lý riêng. |

## DEC-CPU-20261107

User chấp thuận pilot factorial10seed/profile×120steps và Junyi32inner-train×120prefix. Runs đã completed. Catalog thô Junyi có self-loops/cycle, cần graph-version decision, không tự cắt cạnh. Confirmatory inference và final scope vẫn pending.

## D-20261107-CUDA — Probe đạt, chưa cấp quyền training chính thức

**Bằng chứng:** [CUDA acceptance](reports/colab_cuda_acceptance_20261107.md), [independent review](reports/colab_cuda_adversarial_review_20261107.md), kitv12 và returned44outputs. Quyết định kỹ thuật: không rerun các probe đã đạt hoặc dùng Modal đểdebuglại; ưu tiên GPU06/Linuxruntime+boundedmainworkercontract và explicitnegativecontrols. Không đồng nhất controlledoptimizer-boundaryresume với hardkill/Volumeproof; không dự báo fullCV từ một synchronizedstep. Không thay approvedscientificmethodology, S04/S05 hoặc requiredmodels. Paidallocation/fullCV/Holdout vẫn gate riêng; 30free/net0 giữ nguyên.

## D-GPU06-LOCAL — Không dùng probe PASS để nới runtime/main-worker guards

Đã sửa interpreter/schema2 để hỗ trợ Linux đúng cách và kiểm actualParquetworker trên CPU, không đổi CPUphase/hypers/splits hoặc cho inheritedColabvenv thành runtime chính thức. Gate16fail do deepfixturepath được giữ riêng, Gate17PASS513 sau controlledcontrast vàfixture-onlyfix. SAKTcheckpointloader dùng một boundedpayload đãhash; giữ regressionfail/pass trongrunriêng. Các xác nhận chỉ là software contracts. Tiếp GPU07 bằng immutable worker-context và explicit dispatch/caps; không monkeypatch production globals, không tựapprove budget/fullCV hoặc bỏbaseline. Xem20_LINUX_CUDA_WORKER_CONTRACT.md và các báo cáo mới.

## D42 — recipe GKT nghiên cứu BN-D5 được chốt trước fit

Root chọn recipe29 theo quyền triển khai người dùng đã giao. GKT static-expert dùng domain28, hidden/embedding32, MLP hai lớp ELU với dropout0,5 và batch normalization. Batch4, whole-prefix210 và normalization theo timestep là các lựa chọn triển khai của khóa luận, được công bố trước fit. Chưa xác minh tương đương code tác giả. Thiết kế C0 được giữ như phương án engineering đã cân nhắc. [Đặc tả và nguồn sơ cấp](../docs/thesis_recovery/29_GKT_RESEARCH_NUMERICAL_RECIPE_V1.md)

Model, trainer, checkpoint, admitted producer và adapter là các bước riêng. Data bridge đã đạt20tests, còn model candidate mới ở bước review source. Quyết định này chốt công thức để triển khai, chưa là bằng chứng baseline fitted hoặc quyền chạy research training. Giữ nguyên RQ, model bắt buộc, protocol21, nhánh AKT và ngân sách cloud. Các phép kiểm native cần allocation riêng.
