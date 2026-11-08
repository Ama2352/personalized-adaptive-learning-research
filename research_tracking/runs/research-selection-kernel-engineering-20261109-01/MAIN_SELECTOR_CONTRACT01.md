# GRAPH13 — hợp đồng cached main selector V1 (SOURCE-ONLY)

Bản chuẩn bị để ROOT review trước implementation; không import/execute/test/model/selection-data/Git và không sửa production/shared docs. Thực hiện quy tắc đã adopt tại Protocol21:30,36 / Recipe26:40–47; không chọn rule từ kết quả. `EXPERIMENT_ALLOCATION_V1.json` là allocation, không execution authority.

## 1. Candidate IDs, eligible set và barrier

Một selector request chỉ xử lý **một environment**: `grade10_simulator` hoặc `junyi_development_outer_fold4`; không gộp LL/learners/checkpoint hai domain. Logical candidate identity là cặp `(environment_id,candidate_id)`.

```json
{
  "candidate_ids": ["A0", "A1_EXPERT", "A1_LEARNED", "A2_EXPERT", "A2_LEARNED", "A3_EXPERT", "A3_LEARNED", "SAKT", "GKT"],
  "baseline_id": "A0",
  "eligible_graph_ids": ["A1_EXPERT", "A1_LEARNED", "A3_EXPERT", "A3_LEARNED"],
  "comparison_only_ids": ["A2_EXPERT", "A2_LEARNED", "SAKT", "GKT"],
  "common_support_ids": ["A0", "A1_EXPERT", "A1_LEARNED", "A3_EXPERT", "A3_LEARNED"],
  "required_selected_terminal_count": 9
}
```

Giữ A2/SAKT/GKT trong required comparison matrix và checkpoint/epoch/export lineage; không tự làm chúng eligible fallback. A0 phải là model train độc lập đúng initial-backbone contract, không A3 tắt graph. Source BKT/GAM comparisons nằm ngoài nominal9 và không bị xóa bởi selector này.

Barrier của environment: **cả9** selected-fit80/raw-best-selection10 terminals đã complete/durable, sau đó external freeze, rồi mới **bất kỳ main refit90/calibration** của environment đó. Environment còn lại có barrier/freeze riêng, requirements vẫn pending nếu chưa chạy; không dùng kết quả/domain này thay nó. Không loại candidate chưa xong để tạo winner. Old `run_a0_research_lifecycle` tự refit sau local freeze không là main orchestrator/terminal hợp lệ chỉ nhờ đổi tên.

## 2. Input contract và ranh giới dùng nhãn

Reuse existing whole public reader/audit theo **Protocol22:22–28**: có thể audit schema/binary labels/support của cả3roles trước allocation. Không yêu cầu rewrite reader hoặc forged partial `CompleteCorpus`. Trusted internal runner chỉ truyền typed train/selection vào fit/epoch/selector; không calibration loss/predictions/labels cho optimization, epoch/candidate/hyperparameter/winner. Không full-corpus/oracle callbacks vào model; Tfit chỉ sau final refit. Không diễn đạt sai rằng calibration labels chưa từng được deserialize. Public role-scoped API là optional hardening, không critical path GRAPH13.

Selector chỉ consume closed **raw best-epoch selected80** exports/targets/coverage của9candidates; không mở corpus/oracle/final hoặc gọi model. Mỗi candidate manifest tối thiểu:

- candidate/environment/protocol/recipe/allocation/source/runtime/domain/bank/split/selection-role identity; `weights_phase=selected_fit80`, `prediction_phase=raw_selection10`, selected epoch và checkpoint SHA/size;
- accepted selected-only terminal/COMPLETE SHA, best-epoch predictions/targets/coverage SHA; epoch objective ID tách reporting LL; phase/encoding80 lineage; graph/confidence TRAIN80/condition hash khi applicable;
- full target key manifest/coverage, unsupported reasons, model initial identity; shared initial **backbone** identity cho A0–A3 (không ép SAKT/GKT cùng tensor architecture). Không engineering checkpoint/fake fit.

Dùng canonical query key:

`K=(learner_id,item_id,timestamp,source_row,global_rank,history_hash_scheme,history_sha256,origin_role)`.

Require `origin_role=selection`, `phase_scope=raw_selection10`; history scheme `observable-prefix-chain-v1`, timestamp unit/domain đã bind. Kiểm unique/full expected K và y giống nhau giữa9exports. `phase_sha256/encoding_sha256/window_id` là provenance riêng từngcandidate, **không** thêm vào join key model-neutral để làm mất common population. Không join source_row-only, không coi OnlineSession model-bound hash là cùngscheme.

Raw `probability` phải finite trong[0,1], hoặc null+explicit unsupported reason; không0.5 rescue, không drop unsupported rows, không `calibrated_probability` ở input selected. Null không làLL0. SHA/size/strictschema phải kiểm trước parse; reject duplicateJSONkeys, duplicateK, NaN/Inf/bool-as-number, foreignrole/domain/candidate, missing/extracandidate/row và postwritefailure marker.

## 3. Common-supported population và LL số học đã chọn

`F` là full selection key universe đã freeze; all9 phải export đủ F. `U=intersection(supported_K[m] for m in common_support_ids)` **một lần chung** cho A0+4eligible graphs, không pairwise U riêng từngcandidate. A2/SAKT/GKT vẫn báo full/supported coverage và comparison outputs; chúng không làm đổi universe selector hoặc bị biến thành eligible vì LL đẹp.

Giữ full/unsupported counts và per-learner counts của F/U cho từngcandidate. Clusters bootstrap là learner IDs có **ít nhất1row trong U**, sorted bằng Unicode-codepoint ascending; learner0contribution chỉ ghi attrition/coverage, không lấy vào draw rồi resample khi denominator0. Nếu U rỗng hoặc không contributing learner: **INCONCLUSIVE/REJECTED_SELECTOR_NO_FREEZE**, không eligibility/acceptedA0 claim. n=1 được tính đúng algorithm nhưng ghi degenerate conditional cluster uncertainty, không độc lập seed/generalization proof; không invent minimum sample threshold mới.

LL implementation ID đề xuất: `binary64-two-class-eps-clip-mathlog-fsum-v1`:

1. Parse exported p thành Python binary64, giữ nguyên giá trị export (không float32 recast/decimal rounding).
2. Tạo hai class probabilities **trước clip**: `(1.0-p,p)`; clip mỗi class vào `[eps,1-eps]`, `eps=2**-52`. Loss row là `-math.log(clipped_class_probability[y])`.
3. Không renormalize sau clip, không dùng Tfit clip1e-6 hoặc native float32 BCE. `LL_m=math.fsum(loss_m[K] for K in sorted(U))/len(U)`; canonical K sort lexicographic theo tuple với đúngschema types.

Công thức bám `gam_kt/evaluation.py:13–21` chuyển p sang np.float64 rồi sklearn.log_loss(labels=[0,1]); actual local sklearn `_classification.py:285–290,3449–3458` tạo complement trước clipf64, không postclip normalization. Dùng `log1p(-p)` thay complement có thể khác rounding gần0; giữ thuật toán nêu trên. stdlib libm/fsum không tự là bitwise-identical NumPy/sklearn: cần known-answer fixture parity (kể cả0/1 vànear-boundary) trước actual selection; không sửa clip/rule sau xem real scores. Source/runtime/library versions ghi rõ; không tolerance/rounding để biến một bound≥0 thành eligible.

Epoch choice vẫn native frozen EarlyStopping objective của từngcandidate; selector dùng **raw reporting LL** trên U. Calibration-fit objective, in-sample calibrated reporting, full-target native BCE và mean learner LL không thay primary này.

## 4. Bootstrap/RNG và quyết định winner

Freeze RNG ID: `cpython-random-MT19937-randrange-v1`; dùng **private** `random.Random(42)`, không global seed/state và không NumPy/model RNG. Source Python/runtime version được bind. R=2000, không thay số draws theo loss/support. n contributing learners; mỗi replicate gọi `rng.randrange(n)` đúng n lần. Một draw index vector dùng cho **tất cả** A0+4eligible graphs; không tạo RNG riêng theo candidate, không resample đến khi thuận lợi. Số public index requests=2000×n; implementation có mandatory finite byte/learner/row/time/operation caps từ ROOT, thiếu/không đủ cap thì STOP, không giảmR.

Đã chuẩn bị per-learner `(n_i, S_mi=sum loss rows learner i)` trên U bằng math.fsum. Với multiplicities w_i của replicate:

`N_b=sum(w_i*n_i); LL_m,b=fsum(w_i*S_mi)/N_b; Delta_m,b=LL_m,b-LL_A0,b`.

N_b phải>0 vì clusters đều contributing. Đây là **response-weighted** cluster bootstrap: denominator tính lại mỗi draw; không average per-learner LL hoặc fold-macro. Point delta là pointLL_m−pointLL_A0. Giữ cùngdraws, full learner IDs/counts và point/full/common coverage.

Quantile ID `linear-type7-v1`: sort2000deltas; h=(R−1)q, i=floor(h), nội suy x_i+(h−i)(x_{i+1}−x_i). Ghi intervalq.025/.975 và dùng **upperq.975<0** (strict) để eligible. Duyệt mọi4graph candidates; chọn eligible có pointLL nhỏ nhất, exact numeric tie theo stable candidateID lexical. Noneeligible sau đủ input/draws hợp lệ→A0 với reason `NO_GRAPH_UPPER975_LT_ZERO`. Không thêm practicaleffect/mean-delta filter hoặc Holm/p-value vào Dev selector chưa quy định.

Hash shared draws: canonical UTF8 header gồm RNG ID/seed/R/sortedlearners rồi newline; tiếp2000canonical JSON index arrays, mỗiarraynewline (`sort_keys=True,separators=(',',':'),ensure_ascii=False`). Có thể stream+SHA, không cần giữ matrix lớn; multiplicities áp cùng một lượt cho5models. Candidate records dùng chung `draws_sha256`. Không chạy `paired_cluster_bootstrap` cũ như drop-in: nó default1000/seed20261030 và average folds (`paired_bootstrap.py:70–96`).

## 5. External freeze authority và proposed machine fields

Các dòng dưới là **schema blueprint**, không runnable manifest/giảSHA:

```json
{
  "schema_version": 1,
  "status": "SYSTEM_SELECTION_FROZEN_RAW80_BEFORE_MAIN_REFIT",
  "environment_id": "enum: grade10_simulator | junyi_development_outer_fold4",
  "protocol21_sha256": "actual64hex",
  "recipe26_sha256": "actual64hex",
  "allocation_sha256": "actual64hex",
  "candidate_inputs": "exact9: id -> selected_terminal, checkpoint, selected_epoch, raw_predictions, targets, coverage, source and condition bindings",
  "population": "full_K_sha256, common_U_sha256, learner_ids, row_counts, unsupported/zero-contribution coverage",
  "numerics": "LL_id, RNG_id, seed42, draws2000, draws_sha256, quantile_type7, q_upper.975",
  "candidates": "all4eligible graph stats: pointLL/delta/ci025/ci975/eligible + independentA0 pointLL",
  "winner_id": "A0 or one eligible graph ID",
  "reason": "eligible_min_LL_stable_tie | valid_noneeligible_A0",
  "selected_epochs": "all9 id -> own selected epoch and selected-terminal SHA",
  "source_inventory_sha256": "actual64hex",
  "completion_proof": "all9terminals verified, no missing/partial/postfailure, trusted stage journal head",
  "execution_scope": "cachedselector only; not optimizer/GPU/paid authority"
}
```

Trusted ROOT request supplies expected allocation/source/input SHA vector; selector verifies actual disk receipts/bytes, typedphase/coverage/epoch bindings, completes all2000shared draws then publishes exclusive immutable result/freeze+COMPLETE. Refit entry receives **externally pinned freezeSHA**, validates that closedartifact/all9barrier and owncandidate/epoch/condition lineage **before any90constructor/optimizer**, then fresh90weights/encoding. Hash-shaped `SelectionFreeze` (`simulator_research_data.py:192–213`) và graphneuralphase SHA binding chỉ consistency, không tự cấp mainauthority. Có thể tạo per-candidate low-level SelectionFreeze bằng epoch riêng và `selector_artifact_sha256=externalfreezeSHA` **sau** actualauthority checks; không chỉ trustcaller object/string/boolean.

Không reselect bằng refit90 predictions, calibration T/loss hoặc final results. Sauwinnerfreeze, refit/calibrationfailure ghi unsupported/failed downstream, không tự thửwinner khác/nhậnT1. Không âm thầm refitonlywinner thay required allocation23; stagedmissing phases phải báo đúng. Freeze này không cấp execution paid/GPU/realdata/Holdout/fullCV.

### Error cases tối thiểu cho implementation

Missing/extra/duplicate candidate; A3-off giảA0; localA0auto-refit COMPLETE bị promotion; engineering weights; wrong selected epoch/checkpoint/phase or postrefit/calibrated P; inconsistent labels/history/domain/keys/support reason; nonfinite/out-of-range P; emptyglobalU; per-candidate/differentdraws/incorrectdenominator; insufficientdrawcount/resources; corruptlatefailure receipts; forgedfreezeSHA without actualauthority; refit beforebarrier. Mọi trườnghợp này reject/inconclusive, **không** tự chọnA0 để che input/operation failure. Validnoneeligible fallback là nhánh khác.

## Nguồn đã đọc (không actual prediction data)

- Protocol21 SHA `c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6`.
- Protocol22 SHA `96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1`: audit3roles hợp lệ, phase-use boundary.
- Recipe26 SHA `13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a`.
- Allocation SHA `e939d24e35b66e7da19751fb51e8f9fd696a2aca50442d421c7f3188729644a5`.
- `research_runner.py:291–311,432–436,529–540`; `gam_kt/evaluation.py:10–23` SHA `c39b6ca9c87dc92f9e3a6dc7636f5249c7c33f69549284bdcf844c4958acaa65`; `paired_bootstrap.py:70–96`; `simulator_research_data.py:192–213`.
- Actual local sklearn source `.venv/Lib/site-packages/sklearn/metrics/_classification.py`, SHA `d1f99780a70c29387b68d486b9d2b041f7570a72291e3406b25fc79ab52fa792`; source read only, không importlibrary hoặc chạyLL.

ROOT review schema/algorithm before new stdlib code/test. Không cần thêm framework/reader rewrite hay chờ GVHD cho routine detail đã giao; source/resource execution vẫn ROOT-owned. Chưa có winner, calibratedmetric hoặc sciencefinding từ note này.
