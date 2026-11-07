# Chỉ mục bằng chứng

Git class dựa trên repo-local ignore và status trong lượt audit. Ignored artifact vẫn là bằng chứng local; metadata không đồng nghĩa checksum. Dataset lớn, model binary và prediction shards không được hash lại.

| ID | Tham chiếu repo-relative | Git class | Loại/mục đích | Xác minh | Ghi chú |
|---|---|---|---|---|---|
| E-001 | dataset/junyi_ProblemLog_original.csv; dataset/junyi_Exercise_table.csv; dataset/relationship_annotation_training.csv; dataset/relationship_annotation_testing.csv | ignored | Junyi source data | VERIFIED tồn tại/metadata | ProblemLog 2,668,566,436 bytes; nội dung không sao chép. |
| E-002 | experiments/bkt_baseline/results/wsl_cpp/cv_cpp/cv/cv.json | ignored | BKT 5-fold metrics | VERIFIED | Raw JSON aggregate/folds đã mở. |
| E-003 | experiments/bkt_baseline/results/wsl_cpp/cv_cpp/run_manifest.json | ignored | BKT protocol/runtime/identity | VERIFIED | Status complete; backend/config/split hashes. |
| E-004 | experiments/bkt_baseline/results/wsl_cpp/final_cpp/final.json; run_manifest.json | ignored | Development final refit | VERIFIED key status/config | 720 exercise fits; report ghi 11 maxiter; model payload không duyệt hết. |
| E-005 | experiments/bkt_baseline/results/wsl_cpp/test_cpp/test.json; run_manifest.json | ignored | Holdout Test metrics | VERIFIED | Exact JSON metrics; 9 unseen rows. |
| E-006 | docs/bkt-baseline-results.md; experiments/bkt_baseline/relocation_summary.json | tracked / ignored | BKT interpretation/integrity summary | VERIFIED report; relocation REPORTED | Full relocation manifest ignored/local-path; không chép. |
| E-007 | experiments/gam_kt/results/wsl_cpp/cv/cv.json | ignored | GAM fold/common-row metrics | VERIFIED | Completed, 5 folds, 194 fallback, no holdout. |
| E-008 | experiments/gam_kt/results/wsl_cpp/cv/report_vi.md; pilot/report_vi.md | ignored | GAM reports | VERIFIED đối chiếu JSON | Fold/runtime/pilot summaries. |
| E-009 | docs/gam-kt-integration.md; src/knowledge_tracing/gam_kt/; tests/gam_kt/test_model_parity.py | tracked | Protocol/model parity refs | VERIFIED | Test không chạy lại. |
| E-010 | reports/paired_cluster_bootstrap_bkt_gam.json | tracked | Paired learner bootstrap | VERIFIED | 1,000 resamples, seed, estimates/CI bốn metric; không AUC. |
| E-011 | docs/research/bkt-gam-kt-baseline-benchmark-report.md | tracked | Research interpretation | VERIFIED đối chiếu result/bootstrap JSON | Kết luận giới hạn ở Development/stored folds. |
| E-012 | artifacts/akt/preflight/gate2.json; gate2-tests.log | ignored | AKT technical Gate 2 | VERIFIED từ report/log | PASS; 155 pass, source/build/lock/log hashes. |
| E-013 | experiments/akt/results/smoke-task13-20261101-03/manifest.json | ignored | AKT smoke | VERIFIED | Status completed; caps/summary. |
| E-014 | experiments/akt/results/smoke-task13-20261101-03/predictions/manifest.json | ignored | Smoke output coverage | VERIFIED | 549 predicted/expected, 441 fitted, 108 unseen; shards không mở. |
| E-015 | experiments/akt/results/smoke-task13-20261031-01/manifest.json | ignored | AKT incomplete smoke | VERIFIED | Status incomplete; partial export. |
| E-016 | docs/akt-task13-smoke-retry-20261101.md; experiments/akt/README.md | untracked | AKT run chronology | REPORTED, summary cross-check | Diễn giải run-01/-02/-03. |
| E-017 | artifacts/akt/preflight/task13-run02-cli.log | ignored | Resource-blocked retry | REPORTED | Diagnostic ghi guard chặn trước cohort. |
| E-018 | docs/akt-pilot-readiness.md; experiments/akt/configs/pilot-task14-20261104-01.json; pilot-task14-20261104-02.json; authorizations tương ứng | untracked | AKT pilot controls | VERIFIED refs/config docs | Authorization không chứng minh kết quả. |
| E-019 | experiments/akt/results/pilot-task14-20261104-02/manifest.json; pilot.json; pilot-progress.json; artifacts/akt/preflight/pilot-task14-20261104-02-cli.log | ignored | AKT failed partial pilot | VERIFIED | Stable metadata, failed PermissionError; không có prediction. |
| E-020 | dataset/junyi_problem_log_profiling.html; docs/bkt-data-readiness-audit.md | ignored / tracked | Data profiling/duplicates | REPORTED trong audit; existence verified | HTML không re-parse; audit báo 25,925,992 rows/duplicate lineage. |
| E-021 | artifacts/bkt_baseline/; experiments/bkt_baseline/relocation_manifest.json | ignored | BKT derived/CV/refit/Test trees | Metadata + named JSON | Nhiều file; không mở hết/hash lại. |
| E-022 | artifacts/gam_kt/; experiments/gam_kt/results/wsl_cpp/ | ignored | GAM sidecar/integrity/pilot/CV | Metadata + key JSON | Prediction payload không re-read. |
| E-023 | artifacts/akt/preflight/; artifacts/akt/tmp/; experiments/akt/results/ | ignored | AKT preflight/temp/run outputs | Metadata; terminal manifests | Temp may contain partial output. |
| E-024 | experiments/akt/authorizations/; experiments/akt/configs/ | untracked | AKT authorization/configs | Metadata và selected config | Caps không phải execution evidence. |
| E-025 | src/knowledge_tracing/bkt_baseline/; gam_kt/; akt/; tests counterparts | tracked except AKT currently untracked | Model/test source | VERIFIED tồn tại | AKT files untracked theo status. |
| E-026 | papers/; drive-download-20261018T084013Z-1-001/ | ignored | Literature/RIVF local artifacts | Metadata/path only | Copyright/local-only; không duplication. |
| E-027 | scripts/; tests/; _context/; docs/; reports/ | mostly tracked; some untracked | Pipeline/contracts/notes | Paths và selected content | Không sửa ngoài tracker. |
| E-028 | .wsl/JunyiBKT-Ubuntu/; venv/; .venv/ | ignored | WSL disk/environments | Metadata only | VHDX/env internals không traverse. |

## Phạm vi/giới hạn discovery

Đã kiểm tra filesystem roots dataset, artifacts, experiments, reports, drive-download-20261018T084013Z-1-001, papers, _context, src, scripts, tests, docs và metadata .wsl/venv/.venv. Đã đọc .gitignore, .gitignore lồng tìm thấy, .git/info/exclude, Git status, ignored/untracked listings và check-ignore cho đường dẫn chính.

Git global exclude tại C:\Users\AmaDev\.config\git\ignore không đọc được (Permission denied), có thể còn rule toàn cục. Không tải toàn bộ ProblemLog 2.67GB, WSL virtual disk, environments, caches, mọi parquet predictions hoặc toàn bộ khoảng 9,765 BKT result files. AKT pilot mới chỉ đọc sau khi last-write metadata ổn định và manifest terminal failed. Không phát hiện external storage khác ngoài path local được manifest tham chiếu.

## Cập nhật CPU07/11/2026

Điểm vào cho evidence CPU mới là [báo cáo CPU](reports/cpu_rq12_20261107.md). Run03 fixed-stream, run04 replay, closed-loop01 pilot downstream. Run01 superseded cho selector history, artifact giữ nguyên.

## Pilot CPU09/10 và refit07/11/2026

User chấp thuận bounded pilot trước execution. Xem reports/cpu_pilots_20261107.md về factorial và Junyi order, gồm cơ chế PG không hoạt động trong cohort và cycle witness của catalog thô. Engineering snapshot ở runs/cpu-readiness-pathways-20261107-01, không đồng nghĩa GPU/full-training acceptance.

### Bổ sung cuối batch CPU07/11

SCC reconstruction ở runs/cpu-junyi-graph-reconstruction-20261107-01 tái dựng976-edge DAG từ current catalog theo source Paper2; không chứng minh identical historical edge bytes. Gate2 hiện hành237test ở runs/cpu-pilots-gate2-20261107-02. Report cpu_pilots_20261107.md ghi cả kết luận thay đổi sau truy nguồn.

## Matched-control exposure07/11/2026

Run32learner và run mở rộng256learner có notes/manifests riêng. Xem reports/cpu_matched_controls_20261107.md. Source controls giữ degree/topic/area/prefix-support-bin counts, còn learner-level co-observation thay đổi. Không suy graph neutral từ controls thiếu exposure. Mở rộng256×300/180s do user giao lựa chọn sau proposal cụ thể.

## Portable-kit và Gate2 cuối batch07/11

Kitv6 có113source/fixture files, source-only notebook copies và project venv. Manifest comparison chỉ ra AKT/shared v6 giống v5 đã kiểm240passed1deselected; GAMv6 đạt31passed1deselected. Hai local integration exclusions được ghi rõ. Actual Colab/CUDA chưa chạy. Main Gate2 đạt241test khôngskip. Tất cả log thành công/thất bại của batch ở runs/cpu-controls-portability-20261107-01.
