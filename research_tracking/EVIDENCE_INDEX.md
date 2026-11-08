# Chỉ mục bằng chứng

## Hiện hành08/11 — Linux CPU audit riêng và Windows Gate22

Mục này cập nhật các snapshot Gate21/resolution-only/pending archive phía dưới, giữ nguyên verdict lịch sử. Đã kiểm **124output SHA**: [Linux install/audit80outputs](runs/akt-linux-isolated-install-20261108-01/README.md) và [tooling44outputs](runs/linux-gate-tooling-engineering-20261108-01/README.md). Đây là kỹ thuật/vận hành, không completed RQ hoặc fitted efficacy.

| Sự kiện | Kết quả được xác minh | Giới hạn/nguồn |
|---|---|---|
| Install controllers01/02 | **Cả hai vẫn FAILED**.01 dừng trước pip-install;02 pip-install/report44selected và pip-check exit0 nhưng controller fail metadata guard. | [Report](reports/akt_linux_isolated_install_20261108.md), [bundle80](runs/akt-linux-isolated-install-20261108-01/README.md). Không relabel failed02 hoặc lấy `packages_installed` của failed result làm44. |
| Audit event riêng, alias audit03/directory `post-install-audit01` | **EXISTING44_CPU_IMPORT_AUDIT_ACCEPTED_NOT_GPU_READY**,23.361956656s≤90s,1child;44versions/all RECORD-file origins trong venv,8CPUimports/1CPUscalar;Torch2.7.1+cu126, CUDA chưa initialize. |0pip/install/network/model/optimizer/Modal trong audit. CUDA12.6 là build metadata; không device/kernel proof hoặc full installed-byte attestation. |
| Tooling local, commit `7b07d61` |118targeted PASS; parent raw44outputs Git verified; publicpackaging/selectedlock/defaultWindows/strictguards. | [Report](reports/akt_linux_gate_tooling_readiness_20261108.md), [bundle44](runs/linux-gate-tooling-engineering-20261108-01/README.md); giữ RED107PASS/11FAIL,0optimizer. |
| **Current Windows Gate22** | **768PASS**,0fail/error/skip,**477.7091635s≤540s**. | [Report](../artifacts/akt/preflight/gate2-evidence-20261108-linux-tooling-22.json), [pointer](../artifacts/akt/preflight/gate2-current.json); snapshots report/log/XML/pointer trong bundle80. Host Windows dù run-id có `linux-tooling`; chưa Linux fullGate. |

Bundle80 manifest SHA`347961c3133ff4e2af4425c050e7ec31efb228888310671b08f2ed124a2ebbc1`, report SHA`e80a7757cd1b2c9ffe242734e4b202eaf1dd06ad6aeb01579dcf268770b99780`. Gate22 report SHA`f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd`; tooling manifest SHA`6dd95a9cf2982a8a4b7c073c49618509117bdfc93457146f7b3888f2f15d9365`. Raw38files=11FAILED01+20FAILED02+7audit riêng; không ba independent model experiments.

[Linux source kit](../artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/README.md) chỉ **chuẩn bị local**, ZIP980252bytes/161payload/120exactGate-source paths, chưa upload/extract remote. Bridge98978 hết hạn; startup kỹ thuật mới pending, **không kết luận user kết nối sai**. Actual Linux fullGate/main-worker/CUDA/image/throughput-cost vẫn thiếu; không suy quyền GPU/Modal hoặc S04/S05 từ audit CPU.

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

- [OfficialColabMCP/preflight](runs/colab-mcp-preflight-20261107-01/README.md):44outputs;actualagentT4cell execution/setup verified;CPU435pass/7fail/8errors,CUDAmodelstagesnotrun;noModal.

## Bổ sung bốn bundles local đã đóng — 07/11/2026

Đã đối chiếu trực tiếp manifest và SHA-256 của **114/114 outputs** trong bốn bundles dưới đây. Đây là kiểm integrity của hồ sơ đã lưu, không phải bốn thí nghiệm efficacy mới; verdict lịch sử phía trên giữ nguyên.

| Bundle | Phạm vi bằng chứng và báo cáo | Giới hạn diễn giải |
|---|---|---|
| [parallel-graph-diagnostics-20261107-01](runs/parallel-graph-diagnostics-20261107-01/README.md), 32 outputs | [Graph residual/gate prototype](reports/graph_gate_prototype_20261107.md): 75 synthetic CPU cases; [factorial uncertainty](reports/factorial_pilot_uncertainty_20261107.md): 10 paired seed blocks, 10.000 joint resampling draws, giữ failure và reproduction. | Kernel phần mềm chưa hook native AKT hoặc train CG-AKT; post-hoc empirical envelopes không là formal population CI/significance. PG deficit 0/2.400 không chứng minh equivalence. |
| [cpu-portability-gate-20261107-01](runs/cpu-portability-gate-20261107-01/README.md), 38 outputs | [Platform fixtures](reports/colab_platform_fixtures_20261107.md), local Windows Gate15 462 pass; notebook v12 harness 20 cases/dependency 4 mocked cases, actual one-row DuckDB 1.3.2 error → 1.5.6 pass; snapshot [RQ1/RQ2 synthesis](reports/rq12_evidence_synthesis_20261107.md). | Gate15 là software gate Windows tại source snapshot; harness mocks và one-row API contrast không thay actual runtime/full-suite acceptance. Synthesis từ aggregates/pilots không là confirmatory graph benefit hoặc phê duyệt S04/S05. |
| [paper1-revision-audit-20261107-01](runs/paper1-revision-audit-20261107-01/README.md), 14 outputs | [Paper1 revision reconciliation](reports/paper1_revision_reconciliation_20261107.md): 33 input hashes, PDF/source/AST/Git/archive audit; một Git notebook blob và chín source-kit copies cùng source. | Chưa tìm exact PDF revision trong local scope; Q01 chỉ thu hẹp, S01 chưa duyệt. Current-source counterexample không tự bác bỏ finite tested-run claims của PDF. |
| [sakt-core-engineering-20261107-01](runs/sakt-core-engineering-20261107-01/README.md), 30 outputs | [SAKT core readiness](reports/sakt_core_readiness_20261107.md): paper-equation single-block core; giữ 35-pass intermediate và source-bound 37-pass final CPU synthetic evidence, 0 optimizer steps. | Random weights chưa là fitted baseline; adapter/trainer/epoch selection/refit/export/resume/calibration còn thiếu. Gate15 và kit v12 không chứa SAKT; attention không tự là prerequisite graph. |

Số outputs là inventory snapshot của các bundles, không chỉ số hoàn thành RQ. Không bổ sung runtime/GPU verdict từ thông tin chưa có bundle đã đối chiếu.

## Actual AKT CUDA trên Colab T4 — 07/11/2026

- [Nghiệm thu](reports/colab_cuda_acceptance_20261107.md), [phản biện độc lập](reports/colab_cuda_adversarial_review_20261107.md) và [bundle68outputs](runs/colab-cuda-synthetic-20261107-01/README.md): agent tự chạy setup/CPU505pass/GPU400target1update và fresh-process recovery17targets5vs2+3; delta0 trong tolerance1e-5.44original outputSHA,144chunk receipts và139source-file hashes đã kiểm; CSV400rows là bản trích từ synthetic Parquet.
- Checkpoints/binary giữ trong `experiments/akt/results/colab-actual-cuda-20261107-01/`, ZIP gốc28.657.701bytesSHA64392c70... ở artifacts/akt/colab. Không sửa historicalfailure435/7/8; bản mới có source/workspace/manifest riêng.
- Gate4false, không realdata/fulltraining/RQ efficacy, không hardkill/preemption/ModalVolume proof hoặc representative cost forecast. Runtime thử nghiệm đã chấp nhận unassign sau nhận đủ artifacts; bridgeclosed. Không dùng credit Modal. GPU06/runtime-phase contract còn trước mainworker training.

## Runtime Linux, main worker CPU và SAKT inference — batch bắt đầu07/11

- [Runtime contract](reports/akt_linux_runtime_contract_20261107.md), [main worker](reports/akt_main_worker_lifecycle_20261107.md), [bundle](runs/cpu-linux-worker-20261107-01/README.md): targeted63cases và2newworker cases; fullGate513pass/269.98s, source-bound WindowsCPU. Linuxbranches mocked, chưa actualLinux/CUDA worker.
- [SAKT adapter](reports/sakt_adapter_readiness_20261107.md), [bundle ban đầu](runs/sakt-inference-engineering-20261107-01/README.md), [checkpoint followup](runs/sakt-checkpoint-payload-20261107-01/README.md):89CPUcases=37core+52adapter,0optimizersteps; random/unverifiedweights không fitted benchmark hoặc completeOnlineSessionbridge.

## Thành quả RQ1/RQ2 và báo cáo GVHD — 08/11/2026

- [Báo cáo có thể dùng cho GVHD](reports/BAO_CAO_TIEN_DO_GVHD_20261108.md), [kiểm nguồn/claims](reports/BAO_CAO_TIEN_DO_GVHD_20261108.json): tổng hợp proposal, baselines Development và evidence mới; không tự gửi, không fullresearch/fittedCG-AKT claim. S01/S04/S05 và allocation còn cần chốt.
- [RQ1](reports/rq1_transition_evidence_20261108.md), [run12outputs](runs/cpu-rq1-transitions-20261108-01/README.md): join stored synthetic snapshots;944/964 scalar-P-changed giữ concept preview,2/116 scalar-P-same đổi preview; conditional co-occurrence không causal mediation. Empty graph-package37Pchanges/0MRA; closed-loop thiếu M/R nên không suy fullchain.
- [RQ2](reports/rq2_conditions_evidence_20261108.md), [primary6outputs](runs/rq2-conditions-evidence-20261108-01/README.md), [validation21outputs](runs/rq2-conditions-validation-20261108-01/README.md): paired-profile contrast/LOO và Junyi control exposure/denominator decomposition. Mean PYH−PY không robust sign dưới LOO; controls chỉ thay20/976baseedges,40removed/addedentries. Không causal benefit/equivalence hoặc populationCI.
- Cả hai reuse stored artifacts, không train/simulator rerun hoặc query Junyi/Holdout outcomes mới;52newsynthetic analyzer tests pass. Analysis primary và validation archive không là các thí nghiệm độc lập.

## Batch engineering08/11 — context, GKT, demo và môi trường

- [gkt-core-engineering-20261108-01](runs/gkt-core-engineering-20261108-01/README.md): GKT pure static kernel; 20 outputs SHA verified; software_partial_kernel_not_fitted.
- [gpu08-environment-proposal-20261108-01](runs/gpu08-environment-proposal-20261108-01/README.md): Linux CUDA environment metadata; 25 outputs SHA verified; proposal_only_not_full_lock_or_runtime.
- [cpu-worker-context-20261108-01](runs/cpu-worker-context-20261108-01/README.md): AKT context and bounded CUDA phase; 113 outputs SHA verified; actual_guard_Windows_CPU_synthetic_only.
- [demo-readonly-engineering-20261108-01](runs/demo-readonly-engineering-20261108-01/README.md): Read-only synthetic evidence demo; 93 outputs SHA verified; partial_demo_no_live_fitted_personalization.

GKT archive force_add_paths.json rỗng do check-ignore stdin sai; danh sách explicit đúng là execution.log và trial01_pytest.log. Chỉ sửa locator ở chỉ mục này, không sửa bundle đóng. GPU08 dùng argv từng path. Source/code/testing hoàn tất không thay quyền thực thi nghiên cứu.

## RQ1 bổ sung vector S08/11

- [rq1-score-vector-20261108-01](runs/rq1-score-vector-20261108-01/README.md):7outputs verified, reanalysis cùng1.080pairs/candidate, không thêm samples. [Narrative](reports/rq1_score_vector_diagnostic_20261108.md) tách P/S/M/R/A, score-change không bảo đảm mastery/action change; pooled loss che PG worse. Không causal/CI/finalRQ.

## Bổ sung08/11 — trainer synthetic, variants và Gate21 hợp lệ ngân sách

Đã kiểm trực tiếp SHA-256 **472/472 outputs của sáu bundle** dưới đây và mục Linux tiếp theo. Đây là bằng chứng kỹ thuật/vận hành; số outputs và tests không phải số thí nghiệm nghiên cứu hoặc mức hoàn thành RQ. Parent đã đối chiếu raw Git cho27/68/196outputs ở các mốc Graph-GAM/budgetfix/graph prototype tương ứng; lần cập nhật này không chạy Git. Giữ nguyên các verdict lịch sử phía trên.

| Bằng chứng đã đóng | Kết quả được xác minh | Phạm vi và phần chưa hoàn tất |
|---|---|---|
| [SAKT synthetic trainer](runs/sakt-training-engineering-20261108-01/README.md), **51 outputs**, mốc commit `9952bc7`; [báo cáo](reports/sakt_training_readiness_20261108.md) | 139 PASS; CPU training/validation và raw-state checkpoint có sidecar ràng buộc; giữ failure ambient-meta trước sửa. | `synthetic_trained_engineering_only`, chưa fitted nghiên cứu, epoch selection/refit/resume/calibration hoặc complete Grade10 role-aware bridge. |
| [AKT toy role trainer](runs/akt-simulator-engineering-20261108-01/README.md), **93 outputs**, mốc commit `000ea22`; [báo cáo](reports/akt_simulator_engineering_readiness_20261108.md) | 40 targeted PASS; Gate19 lịch sử701 PASS; complete checkpoint/reload và intentional incomplete path được giữ. | Plumbing một epoch CPU toy có train/selection roles; không full corpus, scientific epoch selection hoặc benchmark. Gate19 không thay Gate21 ở nguồn sau sửa ngân sách. |
| [Graph-GAM isolated variants](runs/graph-gam-variant-engineering-20261108-01/README.md), **27 outputs**, commit `96004e2`; [báo cáo](reports/graph_gam_variant_readiness_20261108.md) | 38 PASS, **97 native online state updates**, 0 optimizer/global fit; parity nguồn và cô lập session/cache/graph. | Adaptation kết hợp parent/local; empty graph vẫn có local pathway. Không graph-edge-only causal effect, fitted CV hoặc hiệu quả học tập. |
| [Sửa elapsed Gate2](runs/gate2-budget-fix-20261108-01/README.md), **68 outputs**, commit `4af8f85`; [báo cáo](reports/gate2_elapsed_budget_fix_20261108.md) | 47 targeted PASS; giữ actual RED19 PASS/25 FAIL. Publisher và reader từ chối overtime/malformed resource fields ngay cả khi rehash. | Operational bugfix, 0 optimizer ở targeted tests. Snapshot pointer trong bundle còn rejected; không tự là full Gate cho nguồn mới. |
| [A0/A1 native graph prototype](runs/akt-graph-prototype-engineering-20261108-01/README.md), **196 outputs**, commit `6377265`; [báo cáo targeted](reports/akt_graph_prototype_readiness_20261108.md) | 23 targeted PASS sau dependency rebind, **0 optimizer**; bundle kèm accepted Gate21 **757 PASS**, elapsed **467.1361735s ≤540s**. | Parent-mean observed correctness, fixed `c=1,g=1`, same-backbone fallback/gradient và OOV guards; chưa A2/A3/confidence/gate/trainer integration hoặc fitted CG-AKT. Max12events không chứng minh full100-step rollover. |

[Gate21 report](../artifacts/akt/preflight/gate2-evidence-20261108-elapsed-guard-21.json) SHA-256 `b74f4b96fe6a288f380b3ec69cfba2c01f95c089a8f8d98cdadc0aeb5f8d9c8e`; reader xác minh [current pointer](../artifacts/akt/preflight/gate2-current.json), source/lock và ngân sách hợp lệ tại lần cập nhật này. **Gate20 vẫn bị loại vì1083.995106s >540s dù724 chức năng PASS**; [audit thu hồi](../artifacts/akt/preflight/gate2-resource-audit-20261108-graph-prototype-20.json) và bytes lịch sử nằm trong hai bundle liên quan. Gate21 là CPU software acceptance, không CUDA/main-worker GPU readiness, Gate4 hoặc chấp thuận train nghiên cứu.

Suite Gate21 là `tests/akt tests/shared_kt`; SAKT139 và Graph-GAM38 có targeted receipts riêng, không mặc nhiên nằm trong757tests này.

### Dependency Linux thực tế — archive chuyên biệt đã đóng

[Báo cáo canonical](reports/akt_linux_dependency_resolution_20261108.md), [bundle37outputs](runs/akt-linux-dependency-resolution-20261108-01/README.md) đã kiểm đủ output SHA; manifest SHA `eae752b3c04516020d0671167853acd5a3d55fc35e57ef992c6b960f1eb2d0ed`. [Raw manifest đã nhận](../artifacts/akt/colab/gpu08-linux-20261108-01/received/manifest.json) có **14/14 files khớp SHA/size**. Actual Colab CPU/Linux x86_64 phân giải **44 packages/14 NVIDIA**, **0 cài đặt**; kiểm offline46active dependency constraints và tái dựng candidate lock, không là runtime experiment thứ hai. “Site unchanged” là probe/danh sách tên theo source, chưa full content-hash attestation. Candidate index hashes chưa chứng minh wheel bytes, install/image/runtime CUDA; không GPU/Modal hoặc thay đổi readiness nghiên cứu.

**Làm rõ bước tương lai, chưa thực hiện:** [bổ sung acceptance](reports/akt_linux_dependency_resolution_20261108_addendum.md) làm rõ khả năng dùng pip `--require-hashes` cài trực tiếp từ44URLs trong [candidate lock](runs/akt-linux-dependency-resolution-20261108-01/candidate-linux-cuda.lock.txt), với stage/budget/isolated target được chấp thuận; giữ wheelhouse là lựa chọn lưu trữ riêng, không bắt buộc phải tạo trước. Wording future-step trong report gốc không là bằng chứng install hoặc runtime mới.

### Đính chính thuật ngữ demo

Trong [report demo lịch sử](reports/demo_readiness_20261108.md), “12/120 nodes” của visual QA là số phần tử timeline DOM **`#route li`**, không phải số concept của miền. Miền vẫn **28 concepts**; [bundle demo93outputs](runs/demo-readonly-engineering-20261108-01/README.md) và report gốc giữ nguyên bytes. Replay concept preview chưa phải served action hoặc live fitted personalization.
