# Input contract cho corpus simulator research-mode — 08/11/2026

Đã thêm [simulator_research_data.py](../../src/knowledge_tracing/simulator_research_data.py), dùng trực tiếp observable schemas/validators hiện có để chuẩn bị **80/10/10 development roles và explicit90% refit input** theo [ProtocolV1](../../docs/thesis_recovery/21_ADOPTED_DEVELOPMENT_PROTOCOL_V1.md). Không sửa `simulator_data.py`, collector fixture, native AKT, checkpoint hoặc artifact lịch sử. **Chưa sinh corpus nghiên cứu**, không fit/calibrate/model/simulator/remote trong batch này.

## API và ranh giới sử dụng

| API | Hợp đồng |
|---|---|
| `ResearchSplitPlan(namespace,root_seed,development_learners,final_learners,protocol_sha256)` | Chỉ exact80/10/10: development count chia hết10, không rounding; final count riêng. Dùng `SimulatorSplitPlan` cũ để tạo learner/seed-family/stream identities disjoint. `manifest()` chỉ metadata, không đọc final events. Tổng plan≤10.000 learners là allocation guard cho metadata, **không default kích thước corpus khoa học**. |
| `ResearchProvenance` | Bind role/plan/bank/environment-graph/source/collection-recipe/policy/clock; caller phải đưa expected provenanceSHA bên ngoài vào audit. Policy name tùy ý, kiểm explicit `logging_policy_oracle_access=False`; không reject scientific policy chỉ vì khác tên fixture. |
| `audit_research_shard` | Chỉ một requested train/selection/calibration role đầy đủ và caller caps rõ. Final bị reject **trước khi iterate events**. Giữ original validator checks role/domain/source-row/chronology/OOV; exact observable type chặn subclass có oracle fields. |
| Reference/support output | Exact28concept×3difficulties1050/1200/1350, đủ84declared references, không subset renormalization. Per-item event count và **unique learner count** tách biệt; missing reference items explicit. `train_vocabulary` chỉ có ở train role, không rescue bằng calibration. ReceiptSHA bind audit/provenance/limits/support. |
| `SelectionFreeze` / `prepare_refit_view` | Freeze raw-selection-before-refit artifact/selected epoch gắn đúng train/selection shard hashes, plan/bank. Union train+selection đủ90% với origin roles, source rows không collision. Role mới `refit_train_plus_selection`; **không** giả nhãn legacy train để vượt validator. Không nhận calibration/final vào refit. |

Ví dụ luồng dùng trực tiếp cho collector/trainer research tiếp theo: tạo plan → collector xuất đúng requested observable role cùng provenance → audit role/support → epoch/model selection sinh artifact thật → bind `SelectionFreeze` → prepare90% refit view → trainer nhận explicit refit role → calibrator chỉ dùng calibration shard. Module mới không tự sản xuất selection artifact hoặc thay API training để giả rằng luồng này đã chạy.

## Kiểm chứng thực tế

**Trial01:76 PASS,0 fail/error/skip**, gồm **51 tests mới +25 frozen observable-schema tests**. Pytest console0,49s, JUnit suite0,335s, controller **1,0936313s ≤60s cumulative**; giữ đúng các loại timing, không training throughput. Không failed trial hoặc RED giả. `.venv`, plugin autoload tắt, CUDA hidden, OMP/MKL/OpenBLAS2; không cài dependencies.

Meaningful controls: exact80/10/10/no rounding/bool/oversized-plan rejection; disjoint learner/seed-family/streams; final-event canary; arbitrary policy name với explicit provenance; oracle-access/source/recipe/plan/domain drift; calibration leakage; incomplete/duplicate/foreign learners, OOV/clock/source-row/caps; thiếu/duplicate reference items hoặc sai bank; events vs unique learners; oracle subclass; stale selection freeze/post-refit stage; calibration-as-selection; cross-role refit row collision và legacy validator từ chối fake train union. Tất cả outcomes trong fixture **được dựng bằng tay**, tối đa102 observable targets/fixture, không gọi environment để sinh đáp án.

Command thật: `.venv\Scripts\python.exe -B -m pytest tests/shared_kt/test_simulator_research_data.py tests/shared_kt/test_simulator_data.py -q -p no:cacheprovider --basetemp artifacts/akt/local-tests/simulator-research-data-20261108-01/trial01/t --junitxml artifacts/akt/local-tests/simulator-research-data-20261108-01/trial01/pytest.xml`. Receipt lưu argv tuyệt đối, controller cap và8sourceSHA trước=sau.

New source SHA `51eb7275a6a4a6b26b763a21a8fe6dc15b0973fc19b3c5557175eaa298db7e53`; test SHA `61f64e9e8efc7126ed645b3a078bbf48496833583f8c2fd3c4d766c447e3fdaa`. [Bundle immutable](../runs/simulator-research-data-engineering-20261108-01/README.md) giữ snapshots/source bindings, run receipt/log/XML và copy SHA trước/sau; không copy pytest temp folders.

## Điều chưa được chứng minh và việc tiếp theo

Provenance/oracle-access/freeze SHA là **caller declarations và consistency binding**, không chứng thực generator đã thực thi đúng policy, bytes nguồn thực tế hay selector đã thật sự freeze trước fit. Caller có thể giả metadata đồng nhất; không cryptographic authority. Missing-item check chỉ chứng minh coverage quan sát≥1 learner/item, không đủ diversity/calibration support hoặc edge reliability20learners. Final registry IDs/seeds disjoint về danh tính, không empirical independence/generalization proof. Audit role đọc đúng role; chưa có aggregate whole-corpus/source-blob attestation hoặc IO runner.

Collector hiện vẫn **train-only≤2learners×12events**, RNG helper cũng giữ cap12. Next engineering objective riêng là **role-aware research collector** với actual Paper2 environment provenance, clock/RNG/behavior/outcome channels và source-row namespaces, caller explicit numerical corpus/caps, oracle sidecar tách biệt; không sửa/nới fixture cũ. Sau đó mới nối existing trainers/refit/calibration/controller theoV1. Module này không đủ để gọi corpus generated, research training-ready, fitted baseline, current fullGate/CUDA ready hoặc RQ completion. Không raw learners/Holdout, model training, network/spend hoặc Git/index/state/tasks changes.
