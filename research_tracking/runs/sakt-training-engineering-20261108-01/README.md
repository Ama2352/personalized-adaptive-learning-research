# SAKT synthetic trainer engineering — 08/11/2026

Immutable archive, không model/test rerun. Final tests/sakt139PASS/17,32s;
trial01 giữ138PASS/1meta-defaultAdamfailure/18,11s. Hai controllers cộng39,980828s
<120s. Ledger charge18Adam.step calls gồm1calllỗi, không18committed updates;
trial02 có9calls thànhcông. Global engineering cap32 không reset giữa retries.

## Phạm vi

3trainer modules +2test modules mới; existing core/adapter/config/__init__,
native AKT/shared giữ nguyên. Train-only vocab/disjoint chronology/target_block1,
loss chỉ terminal eligible query, OOV/cold masks và explicit CPUFP32/optimizer.
Không chọn best epoch, training hyperparameters, refit/fullCV hoặc S04/S05.
Artifact role synthetic_trained_engineering_only, chưa fitted research baseline
hoặc OnlineSession. LearnerEvents/KTEvent có fold chỉ là fixture input contract;
chưa role-aware Grade10 simulator training bridge, không fake folds để adoption.
Ceilings geometry là engineering bounds, không scientific defaults.

## Failure và source versions

Pretest review snapshots là static findings,0tests/0optimizer; không red log giả.
01failure có log/XML/source thật: model ctor CPU chưa bảo vệ Adam lazy state
khi caller default meta.02bọc whole training scope CPU, giữ meta regression.
Read-only reviewer đã đối chiếu source và actual139PASS receipts, không rerun.

[Readiness report](sakt_training_readiness.md), [verification](archive_verification.json),
[copy before](archive_copy_inventory_before.json), [copy after](archive_copy_inventory.json),
[binary inventory](training_binary_inventory.json), [review](reviewer_note.json),
[selected links](selected_links.json), [ignored paths](force_add_paths.json).

## Checkpoint và tái lập

Raw state_dict + canonical JSON sidecar chỉ khi requested engineering epoch
hoàn tất; bound source/config/vocab/domain/input/geometry/cold/counters/hash.
Single bounded hashed BytesIO load; không optimizer/RNG resume/selected-fit
promotion. Valid sidecars của1optimizerstep/4targets được snapshot;20selected
new-training/negative-control .ptfiles chỉ SHA inventory, không copy binaries.
Không inventory toàn bộ old random fixtures hoặc pytest temp tree.
Source bindings và snapshots cần repo/runtime tương thích; không standalone kit.
Report relative links được check từ canonical directory, giữ originalbytes.
Lượt tái lập phải dùng run/budget/attempt paths mới; không append ledger hiện có.

Deadlines là cooperative stage/operator checks + outer invocation timeout;
không hard interrupt/peakRAM attestation. Serialized byte cap không bảo đảm
PyTorch peak allocation. Synthetic origin là caller declaration, không certificate.
Toy validation loss không efficacy; correctness không tự là mastery/calibration.
Không GPU/realdata/Holdout/cloud/install, không source edits sauPASS. Archive
chỉ copy/hash/XML; helper verify kiểm integrity, không scientific validity.
Rawfailure whitespace giữ byte-exact; parent xử lý integration nếu cần.
Không sửa index/state/tasks/Git; không sửa bundle sau closure.
