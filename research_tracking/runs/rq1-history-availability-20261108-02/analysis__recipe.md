# Availability revision02 — cached analysis trước khi đọc effect quantities

DESIGN/FREEZE ONLY. Native attempt02 đã terminalaccepted; không replay/retry.
Raw audit riêng kiểm25pins,108endpoint arms,54exact P/S/M/R/fulltuple controls,
216case reservation/terminal rows vàowned Job cleanup. Readonly probes chỉ có
một shared before/after statehash/record +assert đã chạy ở pinned source; không
claim có hai raw hidden-state dumps để independently reconstruct.

## Population và aliases

27targets cố định =3Hpast(10/50/100)×3seed families×3profiles; mỗi target giữ
actual query/label/timestamp cũ. Unique native available lengths: H10:{10},
H50:{10,50}, H100:{10,50,100}; tổng54unique target-window PAIRS/108arms.
Nominal labels10/50/full giữ đủ9H×window cells: L=min(k,H), full=L=H.
H10 label10/50 đều alias cùng full-historynativecase; H50 label50 aliasfull.
Expanded81paired labels là aliases, KHÔNG81new nativepairs/observations.

Validate all108nativecase IDs theo frozenplan, pair full/empty cùng target/y,
mọi window cùng targetH/query/y, no missing/duplicate/drop/unsupported rows.
Không pool chung acrossH/windows thành một grandmean vì targets lặp/aliases.
Mỗi H×label: pooled9targets; từngprofile3; seed3profiles; trajectory1target.
Giữ16contexts như các batchtrước (pooled/3profiles/3seeds/9trajectories), đủ144
summary rows, mọi signs/negative/null effects, không favourable subset.

## Metrics định trước

LL natural log clip1e−15/rawBrier như existing diagnostics; raw probability
signed mean Δp và mean|Δp|. Full preview tuple=(concept,question,difficulty),
exact equality, không actual served action. S/M/R chỉ full-control validation,
không thêm outcome/mastery/calibration estimator mới trong analysis này.

1. Trong cùng H/L/target: graph contrast full_estimator−empty_estimator cho
Δp/LL/Brier, Pchanged count và fullpreview-changed count/n.
2. Từng estimator arm riêng: window−full_history trên EXACT sameH/query/y,
cho Δp/LL/Brier và fullpreview-changed count/n.
3. Numeric availability interaction = graphcontrast(H,L)−graphcontrast(H,H),
cho Δp/LL/Brier; arithmetic crosscheck bằng fullarm_windowdelta−emptyarm_delta,
tolerance1e−12. Đây là algorithmic input-availability interaction, không timeDiD,
causal mediation/edge-quality hoặc learner outcome effect.
4. Khi L=H, mọi arm window−full và numeric availability interactions exact0,
preview-vs-full False; alias rows cùng output, không thêm computations/nativeN.

Không threshold search/calibrator/p-value/CI/ability-only effect; new independent
seed N=0, cùng3families đã xem. RNG uniforms/world labels cũ không regenerate.
Whole native policy + controller bookkeeping reset/reconstruct theo retained
records, không KT-only intervention. Absolute timestamps giữ; first-seen state
có native last_timestampNone; không gọi đây là world forgetting/practice effect.

## Bounded operation

ONE stdlib cached analysis≤10s cumulative, exclusive output directory,
source/plan/allinputs SHA trước=sau/log/receipt. Root review exactsource+planpins
trước dispatch. Native raw/oldfailure/C13/C14/historybins bất biến; không thêm
tests/native model/teacher/RNG/NNoptimizer calls. Nếu identity/alias/equation
checks fail: STOP retainfailure, không relax/retry/chọn favourable windows.
