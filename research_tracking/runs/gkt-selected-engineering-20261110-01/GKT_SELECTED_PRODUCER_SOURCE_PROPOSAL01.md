# GKT08, producer selected-only tối thiểu theo recipe29

Chỉ đề xuất và chuẩn bị nguồn candidate. Không apply, import, chạy test/model hoặc tạo authorization. ROOT đã chốt giữ response-pooled binary64 Log Loss của GKT29, tách criterion native FP32 của SAKT30.

## Ba file mới

- gkt/research_execution.py với GKTSelectedRecipe, FilePin, GKTComponentAcceptance, GKTSelectedEvidence, GKTSelectedBudget, GKTSelectedExecutionSpec và factory require_gkt_selected_authorization. Scope/decision riêng GKT, candidate_id GKT, Grade10 CPU FP32. Runtime schema2/lock/physical interpreter, public shared current Gate, actual component model11/trainer8/checkpoint28 và own GKT critical sources đều bắt buộc. prepare_gkt_selected_identity chỉ inspection, không grant. Existing Main/SAKT authorization không nhận thay.
- gkt/research_runner.py với public run_gkt_selected_fit và helpers orchestration/export thuần metadata. Actual authorization được kiểm trước public reader/phase construction và lazy NN. Dùng model/train/predict/save/restore hiện có, không viết lại math hoặc legacy pipeline. Output dưới experiments/gkt/results/run_id mới độc quyền.
- tests/gkt/test_research_selected.py kiểm lạnh metadata/joins/negative admission, không Torch/NumPy/Pandas hoặc successful fake grant. Candidate giữ ở P cho ROOT review trước apply.

## Hai điểm khác SAKT cần giữ

1. Epoch GKT là toàn bộ learner trajectories, batch4, private shuffle42+epoch. Mỗi target dự đoán trước observe. H0 bằng0, concept28, registry84 ánh xạ3items/concept. Graph input là actual pinned JSON nodes/edges, static expert directed, sorted28 nodes, zero diagonal, domain/TRAIN80 bound. Không tạo exercise-node84 hoặc query-window101.
2. TRAIN progress và EVAL progress tách riêng. CP _boundary dòng237–278 yêu cầu epoch_result.counters bằng TRAINprogress và model/BN digest còn nguyên. Prediction thay counters nhưng phải giữ model/BN/RNG caller không đổi. EVAL có progress và whole-wall budget riêng, TRAIN budget origin và SHA giữ nguyên qua epochs/save/fresh restore. Global producer ledger độc lập không reset khi load best checkpoint có counters cũ hơn epoch cuối.

## Luồng thật

Genuine file admission → public role/schema audit → typed train/selection views dùng cùng TRAIN encoding và expert graph → lazy Torch CPU → seed42 model/Adam1 → epoch đầy đủ → frozen raw selection → score_raw_predictions binary64 response LL → genuine EarlyStopping50/patience5/min_delta0,0001 → save nếu best → natural stop/max50 → fresh model/Adam2 cùng initialization → restore actual best model/BN/Adam/owned dropout RNG → full nullable raw selection parity → model-neutral CSV/truth sidecar/coverage/SelectedCandidateClaim → COMPLETE sau cleanup và revalidation.

Không refit90/calibration/winner/resume hoặc fitted OnlineSession. Full corpus chỉ ở orchestrator, compute nhận phase-selected view. Public reader có thể audit calibration schema/labels như contract22, không dùng để optimize/stop/select. Unknown/OOV và unsupported-history suffix giữ null, không đổi denominator thành toàn bộ scored population.

## Ledger và hạn mức phải có trước run

Với Ltrain learners/Ttrain events, Strain bằng tổng n(n−1)/2. Reserve50×ceil(Ltrain/4) actual optimization batches,50×Ttrain targets và50×Strain expanded prefix events. Mỗi selection pass reserve toàn bộ labels/keys nhưng scoring chỉ eligible. Có tối đa51passes và tối đa2×ceil(Lselection/4) model calls/pass, gồm prefix sequence và tail query. Từng bước Adam có owned pre/post hooks, target count là tổng chiều dài những learners trong đúng shuffled batch, không dùng chunk128targets.

Với corpus48×210, train tối đa600steps/504000target exposures/52668000expanded-prefix events. Selection6×210 có tối đa204model calls,64260full targets và6715170prefix events trên51passes. Hai model constructors và hai owned Adam constructors. Đây là reservation nguồn, chưa đo runtime/RSS/feasibility và chưa cấp quyền chạy.

Primitive GKTResearchBudget có một started_at cố định và kiểm elapsed của cả wall. Producer dùng max_wall_seconds cho budget này, đồng thời kiểm cumulative actual training_seconds riêng từ các train API calls. Không reset started_at mỗi epoch để lách giới hạn. Fresh restore dùng chính training budget/origin đã save. Những caps cụ thể thời gian/RAM/output sẽ do ROOT review theo workload, không lấy default AKT/SAKT.

## Nghiệm thu sau nguồn

Cold fixtures kiểm recipe/types/role/topology/runtime/Gate/component/schema/source/closed auth rejection, finite full/null joins, duplicate/missing/foreign keys và incomplete predictions. Không fake actual accepted admission. Native positive sau này phải actual genuine GKT authorization, all-population epoch, BN/RNG readonly eval, save sau selection, fresh-best parity và failure receipts/poison. Component11/8/28 hiện có không thay cho producer positive. Không bắt full Main resume hoặc CUDA vào batch này.

## Nguồn hiện hành đã đọc

| Nguồn | SHA-256 |
|---|---|
| recipe29 | 059c98909c38856afd830d1cd296ce8875682ba9c7c226ad923c432e4328ce64 |
| gkt/research_data.py | 1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873 |
| gkt/research_model.py | 4b866ca058c281faa8d69671d118758a31f982d68628da853f15f613e6c6c861 |
| gkt/research_training.py | 305fccf1038f41751a1137444cb2be469baf6f15090e27dc1595334ce3cb19cc |
| gkt/research_checkpoint.py | d877dfebac8ad626902995c1627a855c3073be2638aaa061a0a2a692c8a9aa4b |
| sakt/research_execution.py, pattern | 183d37545e1aa87144aaab2c21efef000bda658ecc2d707670f0f4c7b623ff57 |
| sakt/research_runner.py, pattern | 2d6ec4f6f0be78013c610964479ee085d9effecace83259ba525bd066ae8de7f |
