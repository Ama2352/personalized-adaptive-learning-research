> Bản đọc kèm gói ngày08/11. Nội dung giữ nguyên; chỉ chỉnh đường dẫn tương đối. Nguồn gốc và SHA xem NGUON.json.

# RQ2 — năng lực nền × cơ chế tiên quyết trong simulator có kiểm soát

**Phạm vi:** thí nghiệm hữu hạn Development trên world Paper2 có phiên bản, đã nghiệm thu một lần native; không phải nghiên cứu người học thật, benchmark neural hoặc kết luận hoàn tất RQ2. Ba block21000–21002 được tái sử dụng; **new independent seed blocks=0**. [Manifest](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/manifest.json) và [kết quả gốc](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__run.json).

## 1. Câu hỏi và đối chứng

Pilot factorial cũ giữ latent vector trong mỗi profile nhưng các profile dùng các vector/persona khác nhau; không tách được ability scalar khỏi residual/cấu trúc profile. Lần này giữ cùng residual28chiều và cùng hai chuỗi uniform trong từng block, chỉ thay scalar năng lực a∈{1000,1150,1300}. Đây là recipe mới `paper2-centered-bounded-residual-v1`, không giả là tái lập persona lịch sử. [Protocol nguồn đã đóng băng](../../../../reports/rq2_controlled_ability_prerequisite_protocol_DRAFT_20261108.md), [plan thực thi](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/plan.json).

Mỗi block lấy đúng anchor PY lịch sử một lần; z=anchor−mean(anchor), r=60×[z/max(1,max|z|)], base(a,c)=a+r(c), không clipping/resampling. Ba residual và U[120,2] được ghi SHA trước world đầu tiên; identities khớp anchor/U cũ. Residual còn cấu trúc/correlation từ anchor gốc, không là một population residual độc lập với graph.

Ma trận3blocks×3abilities×2estimator graphs×2world strengths=36trajectories. Hai graph arms đều S=1/P=1/L=0: cùng enabled package, node/features, model initialization1200; chỉ estimator edge set full31cạnh hoặc empty0cạnh thay đổi. G environment và G controller vẫn full trong cả hai. World strength λ=0 hoặc0,55 thay đúng coefficient penalty trong `interact`, giữ các phương trình khác. Không so off/on cả package như factorial cũ; không suy khác dấu giữa hai thiết kế là lỗi tái lập. Native `select` tự bookkeeping, rồi `predict` served query → world response → model update với predictedP/observedY. Oracle chỉ ở sidecar evaluator, không vào select/predict/update.

## 2. Đại lượng và đơn vị

Với block b và hai U step-index cố định, gọi Y_b(a,g,λ) là mean_c[θ_c(T)−base_c], T=41ngày sau120lượt theo lịch6h/72h đã chốt. **Y, Δ, Ψ, Ω đều có đơn vị điểm Elo net trung bình trên28concepts**; không nats, phần trăm, calibrated mastery hoặc retention14.

Δ_b(a,λ)=Y_b(a,full,λ)−Y_b(a,empty,λ).
Ψ_b(a)=Δ_b(a,0,55)−Δ_b(a,0).
Ω_b(a₂,a₁)=Ψ_b(a₂)−Ψ_b(a₁).

Đây là các contrast potential outcomes của đúng versioned simulator/whole-policy, có can thiệp điều kiện explicit trong ma trận hữu hạn; không mechanical observational DiD hoặc suy nhân quả về ability ngoài simulator. Các arms có thể chọn concept/question và nhận label khác nhau. Common U được ghép theo step, không giữ exposure hay label chung sau phân kỳ; không paired prediction/loss trên khác query. Δ âm chỉ là **ít net gain hơn empty**, không mặc định học thụt xuống dưới base.

## 3. Tất cả36endpoints và9tương tác

Mỗi hàng chứa đủ bốn Y; không bỏ block hoặc chọn metric theo dấu. Các số làm tròn9chữ số; raw JSON giữ float gốc. [36Y](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__outcomes.json), [18Δ](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__graph_deltas.json), [9Ψ](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__interactions.json).

| Block | a | Y full λ0 | Y empty λ0 | Y full λ0,55 | Y empty λ0,55 | Δ λ0 | Δ λ0,55 | Ψ |
|---|---|---|---|---|---|---|---|---|
| 21000 | 1000 | 4.172464987 | 4.100602725 | 3.182809903 | 3.103386648 | 0.071862262 | 0.079423256 | 0.007560994 |
| 21000 | 1150 | 13.077750247 | 13.539702768 | 12.937801222 | 13.456104863 | -0.461952521 | -0.518303640 | -0.056351119 |
| 21000 | 1300 | 17.583633741 | 17.340974789 | 17.583633741 | 17.340974789 | 0.242658952 | 0.242658952 | 0.000000000 |
| 21001 | 1000 | 3.825573633 | 3.809557212 | 2.764494572 | 2.799554113 | 0.016016421 | -0.035059541 | -0.051075962 |
| 21001 | 1150 | 12.745650212 | 12.763925290 | 12.615429299 | 12.672819077 | -0.018275078 | -0.057389778 | -0.039114700 |
| 21001 | 1300 | 17.630417287 | 17.575257045 | 17.630417287 | 17.575257045 | 0.055160242 | 0.055160242 | 0.000000000 |
| 21002 | 1000 | 3.969114224 | 3.920253161 | 3.022394319 | 2.952912387 | 0.048861063 | 0.069481932 | 0.020620869 |
| 21002 | 1150 | 11.772160955 | 12.676409167 | 11.726052282 | 12.642435050 | -0.904248211 | -0.916382769 | -0.012134557 |
| 21002 | 1300 | 17.899359456 | 17.896638057 | 17.899359456 | 17.896638057 | 0.002721399 | 0.002721399 | 0.000000000 |

| a | Ψ21000 | Ψ21001 | Ψ21002 | Mean3blocks |
|---|---|---|---|---|
|1000|+0,007560994|−0,051075962|+0,020620869|**−0,007631367**|
|1150|−0,056351119|−0,039114700|−0,012134557|**−0,035866792**|
|1300|0|0|0|**0 — design-known negative**|

Ởa1000, hai Ψ dương/một âm; mean âm nhỏ. Ởa1150 cả ba âm, nhưng chỉ ba block cố định và độ lớn nhỏ; không chứng minh tính bền, equivalence hay ý nghĩa thực tiễn. Không CI/p-value hoặc suy độc lập từ36worlds/4320events.

| Block | Contrast ability | Ω |
|---|---|---|
| 21000 | 1000→1150 | -0.063912113 |
| 21000 | 1150→1300 | +0.056351119 |
| 21001 | 1000→1150 | +0.011961262 |
| 21001 | 1150→1300 | +0.039114700 |
| 21002 | 1000→1150 | -0.032755426 |
| 21002 | 1150→1300 | +0.012134557 |

Ω(1150,1000) có dấu−/+/−, không cho monotone ability effect. Ω(1300,1150) dương trong ba block vì highΨ đã biết bằng0, không là phát hiện rằng năng lực cao được lợi từ graph. [Cả6Ω](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__ability_moderation.json).

## 4. Kiểm soát và điều gì thật sự được phân biệt

**High-ability negative:** base1300+r≥1240>1150, gain không âm và decay hướng về base, nên prerequisite deficit D=0 theo cấu trúc nguồn. Sáu cặpλ được chạy trước main:720paired events semantic exact và6final endpoint/state records exact. Tất cả highΨ=0 là kiểm tra implementation/coupling theo thiết kế, không empirical proof rằng graph không giúp học sinh giỏi. [Control traces](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__high_controls.json).

**Null mechanism không đồng nghĩa graph-null:** ởa1300/λ0, cả ba Δ vẫn dương (+0,242658952;+0,055160242;+0,002721399). Vì penalty tiên quyết đã inactive, không thể quy toàn bộ graph advantage cho cơ chế prerequisite thật. Estimator state/update pathways, residual–graph structure, controller/challenge và exposure paths vẫn có thể tạo contrast; chưa tách riêng đóng góp từng đường.

**Main mechanism interaction:** trong đúng9điều kiện block×ability, thay λ đã làm graph-relative net gain khác nhau; meanΨ ởa1000/a1150 âm nhỏ thay vì bắt buộc dương. Đây là bằng chứng điều kiện/âm hữu ích cho RQ2: không nên mặc định cơ chế tiên quyết mạnh hơn sẽ tăng lợi ích graph. Không chứng minh luật population ability, individual-edge quality, causal mediation, general teaching benefit hoặc required-model efficacy. SAKT/GKT/AKT/CG-AKT research-fitted chưa được thay thế bởi native GAM update này.

## 5. Bằng chứng thực thi, kiểm độc lập và giới hạn

Root dispatch một lần, outer12,361254454s≤60; worker11,757589600s. Durable reserve đủ120trước mỗi cell; tổng4320reserved=4320attempted=4320returned. Không retry/reset/partial acceptance. Direct select/predict/interact/update đều4320, snapshot36;3anchor/3U generation;0NNoptimizer. Với hardkill thiếu terminal, actual phải UNKNOWN≤reserved, không0. Owned Job cleanup accepted, active0/handles closed. 510samples có max RSS/peak94.793.728B<512MiB, min free3.038.347.264B>1GiB; đây là telemetry/cooperative guard, không hard OS memory quota.

Kiểm độc lập **chỉ đọc raw bằng stdlib**:34.314assertions/0,116095900s;25source/input pins trước/sau và22rawfiles giữ nguyên; unique4320keys; all36endpoint net gains; all18Δ/9Ψ/6Ω; exact cached float64 U bytes/historical identities; reserved/terminal coverage;720high semantic pairs và6final pairs; logged probability/label/learning equations; T41d closed-form snapshot từ state đã lưu. Không import/chạy native world/policy, NumPy/RNG hoặc tạo thêm trajectory. [Verifier nguồn](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/verify_saved_results.py), [receipt](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/independent_verification01.json).

Call chronology/không oracle leak dựa trên frozen source callsites cộng actual counters; không tuyên bố có independent runtime tracer cho từng native subcall. Readonly evaluator probes có worker assertion before/after state hash, raw lưu shared verified fingerprint; không full dual-state dump. Policy final state lưu SHA; environment endpoint lưu float-hex state, không cryptographic external attestation. [Worker nguồn](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/worker.py), [raw observable](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__observables.jsonl), [evaluator-only trace](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__oracle.jsonl), [endpoints](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/native__oracle_endpoints.jsonl).

Root tool observation không phải raw stdout bytes, không ghi whole tool outer wall; thời gian12,361s là receipt outer measured scope, worker stdout/log riêng giữ nguyên. Phiên bản normalization trước thực thi giữ riêng: đổi `60*z/scale` thành `60*(z/scale)` tránh floating overshoot của bound60, không fake failed run. Native formulas/methods/input notebooks không sửa. [Provenance nguồn](../../../../runs/rq2-controlled-ability-prerequisite-20261108-01/source_provenance.json).

Kết luận hữu hạn: kiểm soát scalar ability/residual và world prerequisite penalty đã rõ hơn pilot profile cũ; kết quả không ủng hộ phát biểu đơn giản “penalty mạnh hơn luôn tăng lợi ích graph”. Chưa hoàn tất RQ2, chưa independent-validation/population evidence hoặc fitted research model. Không truy cập real learner/Holdout, teacher cohort ngoài36worlds này, GPU/cloud/Modal trong batch.
