# Chẩn đoán hai công trình

## Pass 1 — tái dựng và competing hypotheses

Giả thuyết H1 tracking thiếu nguồn, H2 simulator chưa tồn tại. Source inspection xác nhận H1 cho Paper2. Paper1 có notebook nhưng thiếu hành vi theo PDF, vì vậy status reproduction unresolved. P2 inputs đã kiểm đếm 28 nodes, 31 advanced edges, 25 baseline edges, 84 items, map 36 rows. Map dư 8 dòng phải kiểm uniqueness/coverage với nodes trước reuse. Kiểm kê trong evidence/audit_checks.json.

Paper1 PDF trang2–3 mô tả graph advanced thêm 3 intra và 3 cross so baseline, không thể quy toàn delta cho cross-chapter. PDF dùng latent persona riêng và 50 seeds. Notebook CELL3 khởi tạo strong1200, weak800 và function-weak800 đồng nhất, CELL5 graph chỉ add_edges làm mất isolated nodes, CELL13 seed time+hash và dùng expected_p từ estimator hiện tại sinh y. Conditional E[ΔElo|history]=K(E[y]−p)=0. Mastery crossing trong notebook có thể là stochastic drift chứ chưa phải learning gain độc lập. Đây là scientific assumption với latent/estimator bị đồng nhất, thêm defect provenance và omission isolated nodes. Chưa kết luận PDF experiment cũng mắc cùng lỗi.

## Trap 1 — invariant và counterexample

Paper1 PDF continuity ưu tiên current chapter nếu ready còn, không có closed-chapter set trong notebook tìm thấy. Không đủ cơ sở tuyên bố mọi graph đều bảo đảm zero re-entry. Khi mastery absorbing, không forgetting và graph intra-chapter được hoàn tất liên tiếp, zero re-entry có thể theo induction từ frontier. Cross edge có thể mở lại chapter sau khi học chapter khác. E02 cần tạo DAG A1→B1→A2 với A1,A2 cùng chương, B1 chương khác, cùng threshold/latent phù hợp, chứng minh A→B→A dù continuity đúng. Nếu controller thực có closed-chapter ban thì re-entry zero by construction, ghi đó là invariant. Phải tìm đúng source Paper1 trước adjudication.

Paper2 `LatentStudentEnvironment.theta_at` và snapshot (CELL9) decay gain quanh fixed base bằng rate .06/ngày. Với no practice sau T, mọi concept có nonnegative gain và cùng rate. Do đó G14=exp(-.84)G_T≈0.4317105G_T và paired delta14 cùng factor, ranking retained mean gain không độc lập ranking final mean gain. Absolute retained state vẫn phụ thuộc order thông qua state tại T và last-practice. Không được nói retention hoàn toàn không nhạy order. Soft mastery nonlinear threshold có thể đổi ranking. Gross immediate mean_learning_gain cũng khác net final gain.

E02 kiểm algebra và fixture equality với tolerance1e-10, rồi diagnostic-v1 rate phụ thuộc practice/stability hoặc heterogeneous rates đã đóng băng trước results. Tách variant theo environment_id, báo original reference. Đây là sensitivity assumption, không gọi sửa bug nếu code khớp thiết kế. Primary learning outcome dùng net latent gain và time-to-mastery censored, giữ retained14 bắt buộc nhưng nêu redundancy.

## Paper2 package

Source CELL13 và CONTEXT_ADAPTATION_SPEC xác nhận graph on đồng thời parent logit, parent-conditioned q/decay, local struggling và forgotten modifiers. Root vẫn có effect do local history. Phải tách factorial signal, parent adaptation, local adaptation, giữ local adaptation bằng nhau khi contrast edges. Null empty graph với local flag on là negative control. Junyi `(s,alpha,w)=(1,0,0)` bằng graph-free algebraically, test xác nhận identity. Frozen Junyi chọn all-pathways-off hỗ trợ quyết định gate-off, không ước lượng nonzero graph advantage.

P2 selector CELL11 dùng mastery-or-six-exposures, anti-drill3, balanced visits, rồi mastery_score trước chapter tie. Nó là soft continuity khác hard chapter filter Paper1 PDF. Mọi estimator kể cả graph-free dùng graph-aware selector. Tách G_env, G_estimator và G_controller. Thay graph estimator không được vô tình thay latent initialization, learning parents và selector.

## Trap 2 — kiểm soát ability

Ưu tiên paired randomized factorial, cùng base θ, items, clock, outcome/learning uniforms cho graph treatment on/off và prerequisite mechanism λ∈{0,.55}. Không regenerate initial base bằng candidate graph. Với persona a, estimand ψ_a=E[(Y_on,.55−Y_off,.55)−(Y_on,0−Y_off,0)|a]. Đây là interaction difference giữa hai world simulator có kiểm soát. Baseline pre-outcome nếu dùng DiD thời gian là ΔY_post-pre, cùng latent baseline giúp cancel. Causal interpretation chỉ conditional simulator và intervention specification. λ=0 là negative control cho learning prerequisite, vẫn có graph-correlated initial abilities nên ψ không mặc nhiên toàn bộ causal graph effect.

Ability profiles High/Low/Function-weak phân tầng, không lấy High làm untreated của Low rồi gọi DiD, parallel trends không được đảm bảo. Nếu không xây được matched no-prereq environment, báo factorial graph×ability interaction descriptive, bỏ causal DiD claim và xin advisor duyệt thay thế.

## Trap 3 — logged-order

Junyi practice order do nền tảng tác động. Real-edge alignment có thể dự báo exercise exposure/learner progression, không phải instructional benefit. E05 tính edge temporal precedence trên train-only, degree/chapter/support matched rewiring, order-derived placebo graph train-only, empty graph, reversed-edge sensitivity với cycle audit. Tách exercise identity, frequency và future answers. Không permutation y độc lập khỏi exercise rồi coi natural data. History block permutation là stress test distribution shift, báo riêng, không dùng làm causal intervention estimate. Cross-fit graph learner và difficulty trong outer train, không dùng validation/Test để học graph.

## Reproduction / diagnosis / new research

Giữ historical source/results và hash nguyên. Reproduction chạy sau approval, đầu tiên P2 deterministic fixtures/claims hash audit, sau đó bounded quick seeds để kiểm hành vi, full50 chỉ khi cần exact tables và đủ ngân sách CPU. Paper1 source missing revision là blocker cho exact reproduction, có thể đưa vào thesis như limitation sau advisor xử lý. Diagnosis dùng trace và mathematical derivation. New research dùng diagnostic-v1, paired factor experiments và CG-AKT. Bugfix alone không hoàn tất RQ.

Quyết định nhỏ nhất là A+B+C, giữ nguồn, extract adapters có golden parity, thêm variant có version. Rebuild D bị loại vì chi phí và thay nhiều semantics. Share graph schema, item IDs metadata, manifests, RNG/trace/statistics APIs. Không share latent dynamics/mastery/controller implementation nếu chưa parity vì P1 self-Elo và P2 latent gain khác nhau. Hai simulator có environment_id riêng.

Kiểm chứng cuối Q09 đã giải quyết. `evidence/planning_validation.json` xác nhận map36ID duy nhất, đủ28nodes,8extraIDs, không missing/duplicate. Advanced31edges=28intra+3cross, baseline25intra, không missing endpoints/isolated nodes trong inputs P2. Không suy provenance Paper1 từ việc graph counts giống PDF.
