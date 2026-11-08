# GRAPH12/13 — main-nine admission core, SOURCE-ONLY01

## Kết luận từ source

Runner hiện vẫn là A0 pilot: `research_runner.py:529–540` export raw best80 rồi localfreeze và auto-refit; terminal633–637 là `COMPLETE_A0_RESEARCH_LIFECYCLE`, không main selected-only producer. `research_lifecycle.py:18,237–249` cũng chỉ giữ scope pilot. Không có envelope tương thích chín candidate để tái dùng như actual admission. Kernel `research_selection.py` đã có số học/statistics-only; không viết lại LL/bootstrap hoặc promote pilot.

Protocol21:30,36 / Recipe26:40–47 và allocation yêu cầu đủ9raw-selected terminals trước externalfreeze và mọi mainrefit. Protocol22:22–28 cho phép audit cả3publicroles; ranh giới là không dùng calibration để optimize/select. `SelectionFreeze` ở simulator_research_data:192–211 chỉ kiểm SHA/epoch/stage; graph condition:320–321 nói rõ SHA không là authority.

Vì vậy hai file mới chỉ làm **consistency core thuần**, không parser hoặc disk-admission:

- `src/knowledge_tracing/research_admission.py`
- `tests/shared_kt/test_research_admission.py`

Không import/chạy/test/native/data/Git trong lúc chuẩn bị. Checkpoint/online/pilot/kernel hiện hành không sửa.

## API hữu hạn

```text
MainSelectionContext(environment, protocol21, recipe26, allocation,
                     domain, bank, split, train_role, selection_role)
PopulationExpectation(context, full_targets, full_keys_sha, full_keys_labels_sha)
SelectedCandidateClaim(candidate, selected-only kind/status/phase,
                       complete epochs, artifact SHA+size claims, config/source/runtime,
                       phase/encoding/vocab/init/backbone/condition lineage, coverage)
RawSelectedRow(candidate, ModelNeutralKey, y, raw_p_or_null, support_reason,
               model_specific_phase_sha, model_specific_encoding_sha)
MainAdmissionAccumulator(expectation, explicit_limits)
  .add_candidate(claim) × exactly9
  .seal_candidate_claims()
  .add_row_group(exact9rows) × fullF, strict canonicalK ascending
  .finish() -> MainAdmissionStatistics
```

Stage chỉ `CANDIDATE_CLAIMS → SYNCHRONIZED_ROWS → STATISTICS_ONLY_COMPLETE`; mọi operation lỗi poison sangFAILED. Không có FROZEN/refit/authorize function. Kind mới `MAIN_SELECTED_ONLY_CANDIDATE_V1` là **blueprint của producer còn thiếu**, không format được coi tương thích với pilot hiện tại. Typed claims có thể do caller dựng; không chứng minh file tồn tại/đúng bytes/được chấp thuận. Return `NOT_FILE_ADMISSION_STATISTICS_ONLY`; `artifact_bytes_verified`, `nine_terminal_files_admitted`, `external_freeze_authority` đềuFalse.

Core giữ đủ A0,A1/A2/A3×EXPERT/LEARNED,SAKT,GKT. Chặn pilot/refit/calibrated/engineering stage bằng fixedclaimkind/status/phase; kiểm declared epochcomplete, model-specificconfig/phase/encoding, candidate→graphkind, TRAIN80condition binding và shared initialbackbone claim A0–A3. Không ép SAKT/GKT cùng architecture/backbone. Đây vẫn là kiểm claims; actual stagejournal/runtime/config/tensorinit proof cần diskdriver riêng.

## K/y và population

K đúng8fields: learner_id,item_id,timestamp,source_row,global_rank,history_hash_scheme,history_sha256,origin_role. Key yêu cầu observable-prefix-chain-v1/selection; y exactint0/1; rawp exactfinitebinary64[0,1] hoặcnull+explicitreason. Đủ9candidates cùngK/y ở mỗi group; model-specific phase/encoding hashes kiểm riêng, không thêm vào cross-model join. Không có calibrated_probability field; futureparser phải reject calibrated/extracolumns thay vì lặng lẽ strip.

`research_runner.py:292–297` đã có rawfields này; `research_scoring_targets:260–277` tạo chain từ observablepast trước currentlabel. **Không** suy querieditemp là latentmastery. `_population:194–198` hiện là role-shard+5queryfields với scheme khác; giữ SHA cũ như provenance, không relabel nó thành digest mới.

Scheme mới `model-neutral-selection-K-y-jsonl-v1`: canonical UTF8JSON mỗiKtuple, LF; labeldigest mỗi`(K,y)`, LF; stream theo tupleK Pythonascending. Không header ngoài schema đã bind trong expectation. CommonUhash dùng cùngKwire chỉ trên U. ExpectedFdigests/count phải được trustedcaller dựng từ actualselectionuniverse trước admission, không lấy từ9exports đang cần kiểm. Core không tự chứng minh chain hay nhãn đối chiếu corpus; nó chỉ kiểm đúng claims/expectedF.

Đếm full/support/unsupportedreasons choall9 vàperlearner. U là intersection đúng5 A0+A1/A3, không pairwiseU; thiếu SAKT/GKT/A2support không tự xóa target khỏiU. U rỗng→reject/inconclusive, không fallbackA0. Học viên không gópU được coverage riêng. Chỉ buffer5losslists của currentlearner có cap; fsum một lần/learner rồi dùng nguyên `CandidateLossSum`, `LearnerCommonStatistics`, `CommonPopulationCoverage` của kernel đã có. Không giữ9fulltables hoặc đổi summation sang incrementalroundedtotal. Không gọi bootstrap/tạowinner.

## Resource và tám ca dự kiến

Caller cung cấp maxlearners/rows/rows-per-learner/rowchecks/time. Rowchecks chính xác9×F; kiểm đủcap trước nhậnrows. Time≤120 chỉ là hardmaximum engineering cho cooperativeguard, không quyền chạy120s. Buffer bound không là peakRSSattestation; ROOTownedprocess tạo harddeadline riêng. Không tự giảmrows/R hoặc retry/partialclaim.

Tám unittest methods, chưa chạy: full/common/perlearner/all9coverage→typedstats/noauthority; terminal/role/epoch/graphkind/foreignenv và missingGKT; duplicatecandidate/rows poison; fullK/y và riêngphase/encoding mismatch; missing/duplicate/reordered/sharedwronglabel soexpectedF; emptyU/coverage mismatch khôngA0; sharedbackbone/resourcecaps; clock vượtcap sau resultconstruction bịreject. Fixtures chỉ4manufacturedkeys/3learners/9models; không CSV/corpus/NN. Không biến8cases thành independentresearchN.

## Phần actual vẫn cần ROOT nối

1. Main selected-only producer dừng sau rawbest80, không auto-refit/Tfit; terminal thực có acceptedstage/caps/body/completeepoch/source/runtime/Gate/initialproof và closedartifactSHA vector.
2. Trusted diskdriver kiểm actualbytes/sizes/JSON/CSVschema, absencefailure, exactall9terminal authority và expectedF; parse thành typedclaims/rowgroups. API thuần không thay thế các bước này.
3. Sau core→kernelstatistics, driver publish immutableexternalfreeze+COMPLETE với actualsource/input/statistics binding và all9barrier. Mainrefit kiểm externallypinnedclosedfreeze trướcconstructor; không trusthash-shapedSelectionFreeze/string/bool.

Không cần readerrewrite hay trainerframework mới. Source-level core này làm reusablejoin/coverage boundary trước actualmainproducer, chưa một selectedterminal/winner/refit mới.

## Source pins đã đọc

- Protocol21 c0d6e8a698d7d5083986e9848898a643390fc5e76100fc0b8c6286c306e6bea6
- Protocol22 96858efc6d99915390d841f45144d2e2be29e244e825b58cee993a148f05f3d1
- Recipe26 13a81ad6a5173e1f215e3df01f3917fcbc1cce128c87c93985b57af76faa353a
- Plan27 7794963246fc958a3b6f3c4d685d3ec977d96c82b19746f6a5a0f7dcb5edecbc
- Allocation e939d24e35b66e7da19751fb51e8f9fd696a2aca50442d421c7f3188729644a5
- research_selection.py 0e3cf12d15626a76000c6cdc04779ac769806aae2a5e52f769d4c70f3580a348
- akt/research_runner.py 19627a1aa1bbf76069f1a07e0b56a3b5c79a1651863a31c37ac1c08c6cf62092
- akt/research_lifecycle.py cf16402f26d27732cedce83aa01bb46a84537c21cdbed11b80c5fb920fad0fff
- akt/research_simulator_data.py 9596c2dc5ae86cdf89e5f68c15224a6794b6056093dabee6b26502dfabdf092b
