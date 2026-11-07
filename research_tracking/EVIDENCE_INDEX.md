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
| E-010 | research_tracking/reports/paired_cluster_bootstrap_bkt_gam.json | tracked | Paired learner bootstrap | VERIFIED | 1,000 resamples, seed, estimates/CI bốn metric; không AUC. |
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

## Đối chiếu common population07/11

`runs/cpu-junyi-common-20261107-01`: source/outputs SHA verified, reused all3controls,256learners12575events,2.39s. No correctness/Holdout/train. Interpretation và denominator rules tại `reports/cpu_common_population_20261107.md`.

## AKT recovery source-bound Gate2, cập nhật cuối07/11

`runs/cpu-akt-recovery-20261107-01` archive24outputs: Gate2-07 failure, Gate2-08 success274tests và `lifecycle_proof.json`. Model/Adam/RNG/predictions của2actual CLI synthetic cases khớp exact. Không real-data/GPU. Xem `docs/thesis_recovery/17_AKT_RECOVERY_ENGINEERING_LOG.md`.

## Simulator–KT interface07/11

`runs/cpu-sim-kt-interface-20261107-01` và `...-02`: complete synthetic engineering lifecycle,28concept/84item,168targets/1update, noJunyi/Holdout/GPU. Checkpoint ngoài bundle, source/output SHA trong manifest. Đọc `reports/simulator_kt_interface_20261107.md` về semantics, double-window bug và pending calibration/mastery protocol.

## Latest simulator bridge/batch gate07/11

`runs/cpu-sim-kt-batch-gate-20261107-01` có11outputs nguồn/source-bound Gate2-10 296tests, local source hashes; `runs/cpu-sim-kt-interface-20261107-03-batch` giữ measured call/tolerance/timing proof. Earlier gate09 và runs01/02 giữ nguyên. Read report simulator_kt_interface_20261107.md, không suy learning efficacy/GPU readiness.

## Simulator data/graph boundaries07/11

`runs/cpu-sim-data-context-20261107-01/02/03`: mỗi bundle7outputs, final70targeted tests khôngfail/error/skip,2learner×8events×4roles số học,0training steps. Split/observable schema và effective-window/full-history counterexample được lưu trong proof.json. Đọc `reports/simulator_data_graph_boundaries_20261107.md`. Không đánh đồng contract với simulated research dataset, calibrated confidence hoặc CG-AKT implementation.

`runs/cpu-sim-data-context-gate-20261107-01`: archive source-bound Gate2-11 mới361pass0fail/error/skip,152.84giây, explicit CPU-test timeout420s. SHA/logs/JUnit/current và previous pointer giữ nguyên bytes. Gate2-10 ở mục trên là snapshot lịch sử, không current source sau DATA01–04. Kitv9 chưa có source mới.

## Collector và KT simulator windows07/11

`runs/cpu-sim-collector-20261107-02`:60targeted tests/no fail/error/skip, Paper2-equation train-only2×12fixture, repeat/source replay exact,24target rows/12windows,0NN/optimizer. Observable/oracle/manifest tách riêng. `...-01` giữ failedpytestcollection vì trùng tên modules; không sửa historical bundle. Xem report simulator_collection_runner_20261107.md; corpus/training/calibration/refit/final research runner chưa hoàn thành.

`...-03-semantic` và `...-04-portable`: collectorv2,64/65tests, domain từsemantic definitions/constants/inputs/clock, giữ RNGnamespacev1. `cpu-sim-collector-trials-20261107-01` archive12outputs có failedlocaltrials/source/static domain audit. V10 source kit135files SHA db6b122df8297135db04ad63835b3d96909b403467456983b9c04b5082049eab; report colab_bundle_v10_verification_20261107.json chỉ ZIP integrity/source parity, không actual runtime execution. Registry mới backfill terminal manifest indices, không thêm claimed RQ experiments.

`runs/cpu-sim-collector-gate-20261107-01`:14outputs, Gate2-13 **401pass374.53s** nofail/error/skip, source-bound current;396gatev1 chỉsnapshot. V1/v2/finalfixture oracle/RNG exact, testsource v1snapshot đúnghash; runtime/CUDA chưa kiểm. Report simulator_collection_runner_20261107.md có giới hạn và nextscope.

## Modal access chỉ đọc07/11 — vận hành, không thí nghiệm RQ

`runs/cpu-modal-access-20261107-01`:5outputs gồm exact read-only probe và sanitized result; API xác nhận profilekltn/workspacehonguyenminhsang2005, environmentmain, builder2026.10, expiry14/11/2026 17:37:38 Asia/Saigon. Không lưu tokenID/secret/raw SDKoutput hoặc privateconfig hash; không compute/image/Volume/settings mutation. Đọc `reports/modal_access_readiness_20261107.md` về những gì API chưa xác minh: credit/spendlimits và actualCUDA/training readiness.

## Colab-first notebook07/11 — local guard evidence

`runs/cpu-colab-first-20261107-01`:8outputs,8mockguardcases và1actualbundlepytest; AST/CPUflag/JUnit/sourcechange guards pass, khôngactualColab/Linux/CUDA. NotebookCPUtimeout600s thay300s để chứa suite hiện tại, GPUprobe400targets/1step khôngđổi. Xem docs/akt-colab-synthetic-runbook.md;v10kit135files vẫnZIP/sourceparity-only. Không coi localguardPASS thànhmid-epochCUDAresume hoặcđượcquyềndùngModalcredits.

## Colab recovery readiness — 07/11/2026

- [Báo cáo](reports/colab_recovery_readiness_20261107.md): technical CPU evidence, không research improvement.
- [Regression/trials/probe/guards](runs/cpu-colab-recovery-20261107-01/README.md):31outputs vớiSHA, giữ failures/source cũ; actual CPU3processes exact,19mockcases.
- [Gate407](runs/cpu-colab-recovery-gate-20261107-01/README.md):7outputs,0fail/error/skip,169.05s; noCUDA/fulltraining/Gate4.

- [VS Code one-file notebook handoff](runs/cpu-vscode-colab-notebook-20261107-01/README.md):9outputs,20localchecks, embedded137file source parity and failure ZIP export; GPU/setup/CPU guards mocked, chưaactualremote.

- [Colab T4 device discovery](runs/colab-device-discovery-20261107-01/README.md): JSON cell01 do user cung cấp; Torch2.14.1+cu130/Python3.13.16/TeslaT4. Chưa model/lifecycle/recovery, không independently captured runtime.
