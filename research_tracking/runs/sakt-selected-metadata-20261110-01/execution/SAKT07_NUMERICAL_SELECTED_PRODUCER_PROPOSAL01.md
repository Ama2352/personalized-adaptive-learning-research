# SAKT07 — đề xuất numerical recipe và selected-only producer

10/11/2026. SOURCE-ONLY, chờ ROOT duyệt trước code. Không sửa canonical, import Python/Torch, chạy model/tests hoặc Git. Giữ nguyên protocol21/22/23 và chín điều kiện bắt buộc. Bản này bổ sung quyết định hữu hạn còn thiếu cho `sakt_baseline_lifecycle_plan01.md`, không lặp lại toàn lifecycle.

## Kết luận và cấu hình khuyến nghị

Giữ core paper-equation một block đang có. Recipe đề xuất `sakt-paper-equation-d200-h5-hd40-c100-v1`, environment đầu `grade10_simulator`, CPU FP32. Chưa chọn recipe Junyi hoặc GPU từ đề xuất này.

| Trường | Giá trị đề xuất | Căn cứ và giới hạn |
|---|---|---|
| d_model / heads / head_dim |200 /5 /40 | d200 và5heads có căn cứ primary; width tổng200 là convention nhóm cần ROOT chốt |
| Dropout / layernorm eps |0,2 /1e-5 | Rate theo primary; epsilon theo core/fixtures hiện có, không paper-derived default |
| Context / max_length |100 past /101slots | Last100 observable interactions cộng query; đúng API hiện có, không gọi n100 của paper là cùng geometry |
| Position / padding |window_relative_interaction_rank /left | Giữ data/model convention đã kiểm |
| Target / cold / OOV |target_block1 /query_only /null+reason | Một terminal target mỗi window, cold theo21, giữ population đầy đủ |
| Item vocabulary |actual TRAIN80 encoding, num_items=N | Bank84/28 là registry; không ép84 embedding khi train chỉ quan sát Nitems |
| Adam |lr0,001; betas0,9/0,999; eps1e-8; weight_decay0 | lr theo primary; các settings còn lại là explicit group choice |
| Adam options |AMSGrad/foreach/fused/maximize/capturable/differentiable=false | Ordinary CPU Adam và checkpoint contract hiện có |
| Batch / clipping |128 terminal targets /norm1 | Batch không đồng nghĩa128learner subsequences; clipping là group choice |
| Init / epoch RNG |42 /epoch_seed=42+epoch−1 | Fresh CPU fork_rng; giữ trainer hiện có, không sửa thuật toán RNG |
| Maxepochs / patience / min_delta |50 /5 /0,0001 | Group choice, cùng stopping scale comparator GKT29; không quy cho paper |
| Epoch objective |native_torch_bce_float32_exported_supported_mean_v1 | Cùng criterion main AKT hiện hành trên raw p được xuất, khác reporting LL |

Đã đọc lại đúng primary arXiv1907.06837v1, trang4 §3.2 và trang6 phần ablation. Bài thử d50/100/150/200, Adam0,001, batch thường128, dropout0,2 và mặc định5heads. Không lấy kết quả chọn theo dataset của bài thành kết quả hoặc tuning budget của khóa luận. [SAKT primary PDF](https://arxiv.org/pdf/1907.06837v1)

**Điểm cần ROOT adopt rõ trước code recipe** là head_dim40. Core hiện cho head width độc lập. Chọn40 để tổng projection width200, nhất quán head splitting đã được mô tả ở source-provenance tác giả. Literal cách viết WO∈R^(hd×d) của phương trình có thể dùng head_dim200. Hai cách đều biểu diễn được bằng core hiện có nhưng khác capacity. Khuyến nghị40 và công bố convention, không thử cả hai rồi chọn theo selection. Với N84 và101slots, phép đếm từ source cho312.401parameters, chưa là actual native count. Không claim author TensorFlow/checkpoint parity. [Core và provenance đã có](../../../../research_tracking/reports/sakt_core_readiness_20261107.md)

Sliding terminal-only loss của local trainer khác partition subsequences và train nhiều timestep mỗi sample trong paper. Không thay core/trainer để giả exact reproduction. Rate/dimension nêu trên vượt vai trò fixture d4/context2, còn core research không bị ceiling d64 của engineering trainer.

## Phạm vi tách biệt

Engineering8/1/1 hiện có là typed handmade corpus/test evidence, không actual main population hoặc fit grant. Không đổi role/caps cũ, không dùng `train_synthetic_sakt` hoặc toy checkpoint cho full research. Pure stubs có thể kiểm orchestration, còn native fixture phải có allocation engineering riêng và không phát main claim.

Main selected-only nhận corpus công khai có byte-pinned corpus/DONE và đúng actual roles. Reader canonical có thể audit cả train/selection/calibration theo22, nhưng train/predict callbacks chỉ nhận phase view tương ứng. Không tuyên bố raw labels chưa từng được deserialize. Forward không nhận current/future label. Không cho calibration metric hoặc final events vào lựa epoch.

Recipe50epochs không tự cấp quyền chạy50. Khi finite allocation không đủ reserve toàn declared work, run là probe/partial và không phát SELECTED_ONLY_COMPLETE. Corpus10learner×84 và corpus60×210 là các allocations khác nhau, không thay counts hoặc gọi tiny fixture là full research.

## Closed producer contract đề xuất

NEW `sakt/research_execution.py` giữ stdlib-only trước admission. Hai type chính là `SAKTSelectedExecutionSpec` immutable và `AuthorizedSAKTSelectedExecution` do factory tạo. Public entry tự gọi `require_sakt_selected_authorization`, không nhận boolean `authorized` hoặc object caller tự dựng thay bằng chứng file.

Spec đóng đúng các nhóm sau. Không field None cho budgets hoặc authority.

1. `schema_version`, `scope=sakt_main_selected_only_v1`, `candidate_id=SAKT`, `environment_id=grade10_simulator`, run_id và output path mới dưới experiments/sakt/results.
2. Recipe numerical đã adopt, model config với N declared và kiểm lại actual vocabulary, data recipe, seed schedule/stopping/objective ID. Không chứa A0 config hoặc graph condition.
3. Shared `MainSelectionContext` có actual bank/domain/split/train-role/selection-role hashes. Recipe26 trong context chỉ là matrix identity chung, không biến SAKT thành graph model. Phần model graph ghi disabled, initial_backbone=None.
4. Corpus ID/external corpusSHA/DONESHA, public bank/plan/role file pins, expected counts/support, exact read limits. Canonical reader và verify_after vẫn bắt buộc. Không oracle/final event path.
5. Exact source/lock/protocol/recipe inventory, actual interpreter/runtime/device receipt và current Gate membership cùng current SAKT targeted acceptance. Gate không chứa SAKT không tự cover SAKT bằng một chữ PASS. Không dùng mock evidence thành live grant.
6. Cumulative wall/train time, steps/optimized targets, selection passes/rows, constructors, bytes/leaf counts/checkpoint/output, RSS/free/admission/threads. Tách counters reserved/body_returned/completed, toàn run không reset theo epoch.

Auth JSON đóng chính xác schema_version/scope/decision/run_id/spec_sha256/recipe_sha256/identity/caps/requested_phases/approval_reference. Requested phases chỉ select_train80 và raw_selection10. External auth byteSHA và toàn identity/caps phải khớp file ROOT review. Decision string một mình không cấp quyền. SAKT guard kiểm genuine current evidence trước lazy Torch và trước constructor. Không gọi AKT `MainSelectedExecutionSpec` vốn từ chối SAKT, không gắn nhãn A0 authorization và không dùng `MainSelectedStage.status=NO_EXECUTION_AUTHORITY` làm permission.

`MainSelectedStageSpec` có thể giữ vai trò consistency metadata. Terminal chỉ phát shared `SelectedCandidateClaim(candidate_id=SAKT, estimator_graph=disabled, initial_backbone_sha256=None, graph_condition_sha256=None)` sau khi actual file/checkpoint/export đã được xác minh. SAKT vẫn là comparator bắt buộc của matrix, không bị rule graph-vs-A0 loại để bỏ huấn luyện.

## Runner và primitive tái dùng

NEW `sakt/research_runner.py` cung cấp `run_sakt_selected_fit(spec, evidence, *, authorization_file, expected_authorization_sha256)`. Không thêm trainer toán học hoặc public CLI tự launch. Guard → canonical public reader → support/count/resource checks → typed view/encoding80 → lazy Torch → fresh seed42 model và owned Adam. Từng epoch dùng `train_research_epoch`, frozen `predict_research_sakt`, raw label join và `EarlyStopping`. Cùng float32 exported p/y cho native BCE objective, canonical `_metrics` báo AUC/LL/Brier/ECE15/Accuracy0,5 riêng. `binary_row_log_loss` vẫn là shared system-selector metric với clip2^-52, không tráo thành epoch criterion hoặc Tfit clip1e-6.

SAKT view chỉ giữ selected phase. Run context của optimizer/predictor không giữ full corpus/calibration shard. Full observable-prefix hash từ sidecar là model-neutral join, khác feature context100 và khác OnlineSession hash. Full selection export giữ mọi key/item/time/source_row/rank/origin/history/phase/encoding, null và reason. Supported rows chuyển support_reason thành `supported` cho shared RawSelectedRow, đồng thời lưu original input reason riêng. `trained_item` không đồng nghĩa eligible khi OOV-history suffix bị loại.

Advance `SAKTEpochProgress` qua mọi complete epoch. Best save dùng previous counters đúng trước epoch đó. Nonbest checkpointSHA=null. Checkpoint identity bind epoch spec/seed, nên best reload phải dùng spec của best epoch, không spec epoch cuối. Giải phóng fit model/Adam trước fresh best reload; không giữ hai optimizer states không cần thiết. Kiểm actual full-state strict load và full selection prediction parity. Một extra selection pass cho best reload, không extra training update.

Các primitives hiện có là source dependencies, không authority riêng. `research_checkpoint` lưu ambient Python/NumPy/Torch RNG, còn trainer reset private epoch seed trong fork_rng. Không nhầm checkpoint RNG đó với advanced dropout stream kiểu GKT. Native epoch-boundary persistence đã có33cases, chưa main selected producer resume.

## Artifacts, counter arithmetic và acceptance

Fresh output giữ invocation/profile/source-runtime-input references, durable events, encoding80, epochs, best epoch checkpoint, full raw predictions và truth sidecar, metrics/coverage, selected terminal và COMPLETE-last. Failure/late/resource verdict phủ định COMPLETE. Model binaries/CSV ở experiments/sakt/results, archive giữ small receipts và binary SHA refs. Không refit/calibration/SystemFreeze ở entry này.

Nếu train eligible target count=N và selection supported count=S, max Eepochs, train steps≤E×ceil(N/128), optimized targets≤E×N, selection passes≤E+1 và supported predictions≤(E+1)×S. Full selection rows còn có nulls nên byte/input caps dùng full count. Với48×210 fully-supported, N10.080 cho79steps/epoch và max3.950steps/50epochs. Đây là arithmetic reserve, không forecast thời gian. Cần đo representative d200/B128/T101 trước actual allocation, không lấy tiny d4 test time suy throughput.

Acceptance cần genuine guard trước import/model, complete epoch/full population, earliest tie/min_delta, nullable nonbest checkpoint, saved-spec best reload, full raw parity/coverage, calibration-label permutation không đổi epoch, partial/pending/late failure không COMPLETE, và all actual counters/source/runtime/Job cleanup. Không đặt điều kiện loss phải tốt hơn A0 hoặc epoch2 phải thắng.

## Critical path nhỏ nhất

1. ROOT adopt recipe cùng head_dim40 và stopping/sampler choices, đóng recipe ID/hash trước data outcome. Chưa cần full matrix run.
2. Source candidate `sakt/research_execution.py` với focused stdlib negatives, actual evidence schema và closed authorization. Không thay current AKT guard/MainC hoặc core/data/training/checkpoint.
3. Source candidate `sakt/research_runner.py` và focused orchestration tests reuse primitives. Sau Root review mới cấp bounded native allocation/normal-entry acceptance. Engineering terminal không được route thành shared main claim.
4. Actual selected-only research allocation sau source/runtime/Gate/resources acceptance. Sau đủ cả chín raw selected artifacts mới external system freeze rồi batch refit90/calibration10 riêng. Fitted online adapter và Junyi/GPU port là bước sau.

Hai code candidates cùng tests là phạm vi đề nghị, chưa được viết hoặc apply trong task này. Không cần mid-epoch resume hoặc persistence framework mới trước selected-fit.

## Source map tối thiểu

| Nguồn | Điểm cần giữ |
|---|---|
| sakt/config.py6–29; model.py34–57 | Explicit config, một block, head width độc lập |
| sakt/research_data.py38–92,144–190 | InitVar corpus, phase-only views, target_block1/full keys/null reasons |
| sakt/research_training.py26–64,96–123,194–218,228–310 | Typed CPU spec/budget, exact optimizer ownership, current terminal-only train/predict semantics |
| sakt/research_checkpoint.py105–120,173–201,286–382 | Optimization phase binding, complete epoch progress, saved spec, CPU weights_only restore |
| akt/research_main_execution.py288–307 | Actual AKT-only producer rejection của SAKT/GKT |
| akt/research_main_stage.py18–24,43–80 | Matrix9 metadata có SAKT, không execution authority |
| research_admission.py86–137 | Shared selected claim với SAKT graph disabled/initial_backboneNone |
| akt/research_selected_runner.py313–375 | Actual epoch objective, best reload, selected terminal ordering |

SHA hiện hành từ PowerShell, không module imports. SAKT config3e18b3ac…, modelf3979c4d…, datada64bc5b…, trainer3c9b7856…, checkpoint40fa69b8…. Protocol21c0d6e8a6…,2296858efc…,236f9e5adc…. Primary provenance cũ `parallel-sakt-20261107-02/primary-source-provenance.json` SHAcd1360bd5cef41953eb3cb83a0af907e12011516475e848392143ba338351b0f chỉ ghi đọc§2 và author commit98510c58…, không giả nó đã chứa numerical§3.2. Lần này đọc bổ sung đúng primary PDF URL ở trên, không lưu/khẳng định byteSHA của PDF chưa tải vào repo.
