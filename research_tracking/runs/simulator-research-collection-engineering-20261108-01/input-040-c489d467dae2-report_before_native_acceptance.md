# Collector research-mode theo requested role — 08/11/2026

Đã triển khai [simulator_research_collection.py](../../src/knowledge_tracing/simulator_research_collection.py) riêng để sinh observable trajectories từ phương trình environment Paper2, nối trực tiếp [research input contract](simulator_research_data_contract_20261108.md) và [ProtocolV1](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md). **Collector fixture cũ, RNG cap12, validators/native/source Paper2 và artifacts lịch sử giữ nguyên.** Batch hiện mới có kiểm mock; chưa sinh research cohort, train/calibrate model, mở final events hoặc gọi remote.

## Hợp đồng thực thi

- `collect_research_role` chỉ train/selection/calibration; final bị từ chối trước source/memory/environment access. Plan/counts/profiles/recipe/clock/limits/source pins do caller truyền đầy đủ, không defaults corpus/neural/scientific horizon.
- Nạp allowlisted definitions của Paper2 bằng loader hiện có, không notebook top-level; không estimator/controller được thực thi để chọn item. G_env giữ source graph; world/semantic bank/recipe/profile-metadata/source hashes có identity riêng.
- Hai logging implementations là uniform item sampling và cyclic items với per-learner seeded offset. Chỉ dùng bank/rank/behavior RNG; không đọc theta/current outcome để chọn item. Đây là source implementations cụ thể, không suy oracle-free từ tên metadata bất kỳ.
- Tách outcome/learning/behavior PCG64 channels trong RNG namespace riêng; scalar draws không cấp phát vector lớn theo requested count. Profiles/base theta/uniforms/state chỉ ở **oracle sidecar**, observable schema chỉ query và correct. Không fitted-role promotion.
- Source row `global_plan_learner_ordinal×1.000.000+rank+1`, dùng cả registry metadata để giữ IDs disjoint giữa roles và prefix ổn định khi đổi event cap. Slot limit1.000.000/learner là operational address ceiling, không default trajectory length; kiểm signed-int64 ceiling trước sinh events.
- Recipe kiểm UTC Unix-second range trước pandas conversion. Limits bắt buộc gồm learners/events/total, wall≤600s, RSS64MiB–2GiB và freeRAM≥1GiB. Kiểm trước load, mỗi learner/event, sau native interact, sau telemetry và final elapsed/source hashing. Đây là **cooperative checks**, không hardkill hay OS peak-allocation attestation.
- Expected13source pins ngoài collector được so trước load; loaded native provenance, protocolSHA, bank/G_env/recipe được bind vào `ResearchProvenance`; source hash lại cuối run. Audit đầy đủ requested role, full84reference coverage và support/null semantics. Missing support được báo, không tự chọn thêm samples hoặc rescue bằng calibration.
- Failure terminal có reservations/call returns/completed events/learners và source snapshots; không trả usable partial corpus, không hứa rollback native work hoặc tự retry. Function không tự ghi output files; runner phải lưu result/failure riêng trong directory mới.

## Bằng chứng mock thực tế, giữ failure

| Lượt | Kết quả | Controller / cumulative | Actual Paper2/model calls |
|---|---|---|---|
| Mock01 |42PASS/1FAIL/0error/skip |3,3686239s |0 |
| Mock02 |**45PASS/0fail/error/skip** |2,4327523s; **5,8013762s≤60s cumulative** |0 |

Failure thật: pandas `to_datetime` nhận unsigned-sized Unix timestamp2^63 thay vì raise như guard dự tính. Sửa **new collector** bằng upper Unix-second bound từ `Timestamp.max` trước converter; thêm signed-boundary và exact-upper/next-second controls. Không sửa fixture cũ hoặc suy artifact lịch sử hỏng; snapshot source/test42/1 giữ nguyên. Mock0215source/inputSHA trước=sau.

Pure tests chặn actual reference loader bằng autouse guard, dùng mock environment rõ tên. Kiểm requested roles, no-final, policy/sidecar boundary, prefix/RNG, global source-row disjointness, profile không đổi logging/channels, missing/foreign profiles, source/protocol/loaded-reference/bank drift, caller caps, pre-load RAM, post-interact timeout/RSS/floor, telemetry overrun, invalid native outcome và global NumPy RNG isolation. Mock interactions không là observations từ Paper2 hoặc evidence học tập.

Final sourceSHA `bdbe74581a13ca03c726a6cf69a3a8354f0350b12d5ab6ba93283368bbb5a289`; testSHA `3b403377d5976295ef2a17de5481984abb8a7b59ec9429403c67105bcc845865`. Logs/XML/receipts nằm trong `artifacts/akt/local-tests/simulator-research-collection-20261108-01/mock01` và `mock02`; chỉ source bytes notebook/CSV được hash, không raw learner events.

## Native smoke đã chuẩn bị, chưa thực thi

Sau root source review, driver chuẩn bị **một batch tối đa12 actual environment attempts**, không NN/final: train8learners×1event, selection1×2, calibration1×2; plan10development+1final metadata. Global cap30s/RSS512MiB/freeRAM1GiB. Private subclass chỉ reserve/log trước gọi original `interact`, trả nguyên kết quả; không thêm teacher/RNG calls. Source driver/pins/command đã gửi root, chưa có quyền dispatch từ việc lập note này. Missing84reference support là expected và **không research-ready**.

## Giới hạn và next substantive step

Source checks là consistency guard trên trusted/quiescent workspace, không chứng thực chống concurrent A→B→A replacement hay caller giả metadata. Environment/source wrappers phải được ghi cùng driverSHA; sidecar không được đưa vào trainer features. Corpus diversity, profile allocation, empirical independence và calibration support chưa được chứng minh bởi mocks hoặc planned12events. Không runtime forecast từ test timings, không RQ completion/current fullGate/CUDA/GPU/paid authority.

Next riêng sau acceptance native integration: root chọn exact numerical first research-corpus counts/events/clock/policies/caps và output contract theoV1; lưu requested-role observables/sidecar/manifest riêng, kiểm đủ reference/support trước actual research fit. Không dùng tiny smoke như corpus nghiên cứu, không tăng cap cũ hoặc thêm toy-only milestones để thay train→selection→refit90%→calibration10%→export.
