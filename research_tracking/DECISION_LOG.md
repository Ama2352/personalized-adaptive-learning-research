# Nhật ký quyết định nghiên cứu

Chỉ ghi quyết định rõ trong tài liệu/config/run evidence. Không suy đoán chủ thể và không gán ngày lịch sử nếu nguồn không ghi.

| ID | Ngày được chứng minh | Quyết định | Cơ sở | Hệ quả/giới hạn |
|---|---|---|---|---|
| DEC-001 | Chưa xác định trong _context | Standard CAHLR/pyBKT 1.4.3; one model/exercise; correct; num_fits=1, forgets=false, tol=.005, maxiter=100, seed 42. | _context/decisions.md, protocol, CV manifest. | Historical baseline; 11 refit hit maxiter vẫn báo riêng. |
| DEC-002 | Chưa xác định | Global split by user 80/20 seed 42; 5 Dev folds; time_done/source_row; predict-before-update. | _context/evaluation_protocol.md; manifests. | BKT/GAM comparability; không tune bằng Test. |
| DEC-003 | Chưa xác định | suggested chỉ subgroup; unseen BKT prediction null, loại khỏi fitted denominator. | _context notes, protocol, BKT JSON. | Không gọi suggested predictor hoặc causal treatment. |
| DEC-004 | Chưa xác định; documented trong GAM protocol tháng 10-2026 | GAM Junyi benchmark graph-free; graph/adaptation/time decay off; fallback tách khỏi supported/common-row. | docs/gam-kt-integration.md; CV JSON. | Không đại diện Graph-GAM-KT hoặc graph benefit. |
| DEC-005 | 2026-10-30 theo bootstrap metadata | GAM−BKT learner-clustered bootstrap, 1,000 draws, seed 20261030, unweighted fold difference. | reports/paired_cluster_bootstrap_bkt_gam.json. | Conditional CI; no AUC CI/Holm. |
| DEC-006 | 2026-11-01 theo retry report | Mỗi AKT smoke cần run ID/config/authorization riêng; smoke không đồng nghĩa CV/full fold. | docs/akt-task13-smoke-retry-20261101.md; experiments/akt/README.md. | Preserve failed attempts; không mở rộng auth ngầm. |
| DEC-007 | 2026-11-04 theo config/auth | AKT pilot bounded trên Development, caps cohort/targets/time/RSS/RAM; không holdout/CV. | docs/akt-pilot-readiness.md và pilot config/auth. | Run14-02 failed; authorization không phải result. |
| DEC-008 | 2026-11-04 | Agent 2 chỉ tạo tracking trong research_tracking; không sửa code/data/artifacts, không chạy experiment/test. | Yêu cầu audit và repo rules. | Gaps chuyển cho nhóm xử lý riêng. |

## DEC-CPU-20261107

User chấp thuận pilot factorial10seed/profile×120steps và Junyi32inner-train×120prefix. Runs đã completed. Catalog thô Junyi có self-loops/cycle, cần graph-version decision, không tự cắt cạnh. Confirmatory inference và final scope vẫn pending.
