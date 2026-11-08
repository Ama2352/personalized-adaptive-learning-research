# Ledger lifecycle A0 — kiểm engineering thuần metadata

08/11/2026. **45 tests PASS; chưa có trainer, model fitted hoặc lifecycle research đã chạy.** Module [research_lifecycle.py](../../src/knowledge_tracing/akt/research_lifecycle.py) là phần đầu BATCH3B theo [hợp đồng22](../../docs/thesis_recovery/22_A0_RESEARCH_LIFECYCLE_CONTRACT.md). Nó không đọc corpus, consume authorization, tạo model/optimizer, chọn epoch hay lưu checkpoint.

`LifecycleInvocation` bất biến reuse actual `SimulatorResearchSpec`/`ResearchResourceBudget`; không tạo protocol/budget thứ hai. Invocation gắn corpus/DONE, plan/bank, từng role shard, full target-population, source inventory và authorization SHA do caller cung cấp. Purpose chỉ `a0_single_candidate_lifecycle_pilot`; không main-matrix winner. `PhaseInputs` chỉ trả refs role phù hợp: train; selection; train+selection sau actual `SelectionFreeze`; calibration sau refit. Không chứa toàn corpus, labels hoặc callable.

`LifecycleLedger` giữ một pending optimizer ticket và ba counter riêng: reserved, body-returned, complete-batch. Counter steps/targets/time dùng chung qua fit80 và refit90, không reset khi đổi phase. Fit epoch chưa đủ targets hoặc đang pending không được freeze; refit phải hoàn tất đúng số selected epochs trước calibration. Raw selection giữ full denominator và population identity; unsupported rows không được biến thành metric có dự đoán. Nếu body đã trả về rồi mới phát hiện vượt thời gian, `LifecycleBudgetExceeded.ledger` giữ counter vừa quan sát và trạng thái failed. Lỗi không rollback hoặc tự chứng minh không có weight update.

## Kết quả kiểm thực tế

| Bằng chứng | Kết quả |
|---|---|
| Lượt duy nhất, root chạy controller cùng process `.venv` | 45 tests,0 failure/error/skip |
| Controller elapsed | 0,7860216999542899s |
| Actual tool wall do root ghi | 1,2566407s; cap cộng dồn20s |
| Source pins trước–sau | 12/12 khớp; copies có SHA trước–sau |
| Neural/optimizer/corpus/subprocess trong controller | 0/0/0/0 |

Tests kiểm role separation, malformed tuple trước indexing, identity bất biến, pending/stale ticket, body-return failure, late-time accounting, cumulative caps qua refit, raw full-population, foreign freeze, exact selected epoch count và checkpoint/population mismatch. Fixture chỉ dùng metadata/SHA giả khai báo rõ; không có actual corpus hay bằng chứng data authority. Root đã source-review toàn source/tests và chạy actual suite; không gán thêm independent-agent execution.

Controller gọi `pytest.main` trực tiếp; không launcher lồng qua Windows redirector. Daemon Timer18s có thể self-exit124; phụ thuộc GIL, **không là hard OS quota hoặc native worker containment proof**. Timeout sẽ bỏ qua `finally` và chỉ có sentinel UNKNOWN; lần thực tế này terminalRC0/JUnit đầy đủ. Thời gian controller kết thúc sau parse JUnit/posthash, trước small receipt publication; tool wall root ghi bổ sung kiểm cap sau publication. Không áp dụng cách chạy này để nới native/model execution.

## Giới hạn và bước nối còn thiếu

Đây là consistency cho caller hợp tác: caller phải giữ duy nhất head hiện hành, fsync event trước Adam body và cung cấp clocks thật. Frozen dataclass/hash không ngăn caller fork/reset toàn ledger; raw SHA không chứng minh file đã được kiểm hoặc model/optimizer thực sự fresh. Epoch do existing `EarlyStopping` chọn; wrapper tương lai phải bind checkpoint/result đúng selected epoch, dùng model+Adam mới cho refit và thực thi source/runtime/corpus/resource guards trước lazy Torch. Module chưa gọi `train_epoch`, checkpoint, calibrator hay public run; `complete` trong ledger chỉ là metadata transition, không execution acceptance. Native Gate hiện hành không được suy từ suite này.

Reader vẫn giữ riêng lượt timeout01 UNKNOWN/noJUnit; archive ledger không biến reader hoặc corpus thành accepted. Không sinh corpus, mở final/Holdout, đổi frozen hyperparameters hay thực hiện GPU/cloud/training.

Bằng chứng portable: [receipt45](../runs/akt-research-lifecycle-ledger-engineering-20261108-01/trial01__receipt.json), [JUnit](../runs/akt-research-lifecycle-ledger-engineering-20261108-01/trial01__junit.xml), [nguồn và bản sao SHA](../runs/akt-research-lifecycle-ledger-engineering-20261108-01/copy_inventory.json). Bundle đóng giữ exact source/test/controller và12snapshot; không sửa sau closure.
