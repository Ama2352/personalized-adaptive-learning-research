# Graph-GAM: isolated variant factory trên toy Junyi-shaped — 08/11/2026

**Đã có factory engineering riêng và 38 targeted tests pass, chưa có Graph-GAM research benchmark hoặc graph-enabled CV runner.** Factory tái dùng nguyên thuật toán native đã có, không viết lại KT, không chọn flags làm scientific defaults và không thay simulator wrapper. Native learner-state updates trong tests không phải global model fitting hoặc optimizer training.

## Phần được thêm và phần được giữ nguyên

Các files mới: [variant_factory.py](../../src/knowledge_tracing/gam_kt/variant_factory.py), [test_variant_factory.py](../../tests/gam_kt/test_variant_factory.py) và báo cáo này. Bundle [graph-gam-variant-engineering-20261108-01](../runs/graph-gam-variant-engineering-20261108-01/README.md) giữ snapshots, source provenance, pretest review, log/JUnit và native-update ledger. Parent quản lý chỉ mục/Git; không sửa source cũ hoặc bundles đã đóng.

[model.py](../../src/knowledge_tracing/gam_kt/model.py) vẫn là graph-free factory được [runner.py](../../src/knowledge_tracing/gam_kt/runner.py) gọi cho từng learner. [original_junyi.py](../../src/knowledge_tracing/gam_kt/original_junyi.py) đã có graph_source, graph_signal_enabled và graph_adaptation_enabled. Khoảng trống ở đây là cách tạo variants có identity và isolation, không phải thiếu phương trình Graph-GAM.

Simulator đã có [build_pathway_policy](../../src/knowledge_tracing/gam_kt/simulator_pathways.py) với signal/parent-adaptation/local-adaptation và [paper2_reference](../../src/knowledge_tracing/paper2_reference.py) tách graph environment/estimator/controller. Không làm thêm wrapper trùng hoặc lấy Junyi-shaped factory thay policy simulator có structured features và mastery semantics khác.

## Nguồn thuật toán và isolation

Factory đọc tối đa 64KiB của module native `original_junyi.py`, kiểm SHA caller khai báo rồi compile/exec **nguyên bytes** vào module namespace riêng. Không nhận source path/code tùy ý từ caller. Source module này chỉ có definitions/imports/integration metadata; factory không đọc notebook, catalog, CSV hoặc learner data. Temporary registration phục vụ dataclass annotations được gỡ ngay; namespace/functions còn được factory giữ để dùng riêng.

Để kiểm parity, test đọc source notebook JSON và chỉ compile/exec **cell11 definitions** của `junyi_cycle_corrected_ablation_confirmation.ipynb`; không chạy preprocessing hoặc notebook top-level khác. Cell SHA khớp certificate đang có trong parity test lịch sử:

`5fc0adbf8fcb454b73bbdd3294bb20e17c2a08ec9eb496b7383677f38b04a5fc`.

Module native và cell có SHA khác nhau vì module có phần integration/metadata bên ngoài definitions. Không dùng hai digest như thể cùng một payload. Source snapshots và cell text riêng trong bundle cho phép kiểm chính xác hai đối tượng.

| Nguồn trong lượt kiểm | SHA-256 |
|---|---|
| New variant factory | `6ab9615075f3a221841e6a8a87aeecc6fc8d4a75adeb4e004370fff82e0734b0` |
| New targeted tests | `d71153e8f3377b8c5070f378bb11d084c96c8c68753492cd1ae4a9bda2a38ae1` |
| Native original_junyi.py | `31aa877ca215f33cd7adb21bcf0fe8e82598a6b18042a965cdcc0fbdf63cfeb3` |
| Existing replay.py | `274046d3716a5c5659b7618136e9701aa904636faffeb878d9fbaac489b3535f` |
| Reference notebook bytes | `26270cc8e2c057d9c15b7070cc01304b2646b9575e632eaee8b5eeb3de357f3c` |

Mỗi factory có bản sao metadata readonly và `question_feature_vector` cache riêng. Không gọi `configure_metadata` của module native đang import chung; không đổi maps/cache của benchmark graph-free cũ. Mỗi `new_learner(id)` tạo model native với states rỗng, không chia sẻ learner state với session khác, kể cả khi dùng lại learner ID.

## API và identity tường minh

Không có preset scientific flags hoặc tham số recipe mặc định. Caller phải cung cấp:

- `GAMVariantRecipe`: synthetic domain, label, hai boolean native flags, graph_weight, time_decay_rate và expected native source SHA.
- `GAMGraphBinding`: canonical nodes/edges, direction `prerequisite_to_dependent`, origin `caller_declared_synthetic_fixture`, provenance ID/SHA và structure SHA.
- Topic/area dict bao phủ đúng nodes; `synthetic_only=True`.

Factory binding chứa recipe, graph/provenance, metadata snapshots, **materialized graph nodes/parent tuples thực sự được model dùng**, cùng hashes của native core/new factory/replay. Parent tuple order được giữ vì source lấy mean theo iteration order. Before/after mỗi step kiểm binding và native settings; binding trả về là copy. Graph là frozen dataclass với tuple/mapping-proxy; forced private attribute drift có negative control phát hiện trước native call. Đây là integrity guard trong repository tin cậy, không sandbox chống mã Python độc hại hoặc certificate nguồn dữ liệu do caller khai báo.

Hard engineering caps: **1–16 exercise nodes, tối đa64 edges, DAG, tối đa32 attempted interactions/session**. Query có known exercise, template, finite difficulty, aware timestamp và positive source_row; response là exact integer0/1. Metadata identifiers/values có độ dài tối đa128 và không rỗng. Đây là **accepted toy subset**: native source/runner có thể giữ topic/area trống, còn factory này từ chối; không tuyên bố thay thế toàn bộ input range của Junyi.

`session.step(query,correct)` gọi existing `predict_then_update`: source predict nhận exercise/template/difficulty/time trước source update nhận current response. Query không chứa label field. Wrapper từ chối duplicate source_row hoặc chronology đảo theo `(timestamp_ns,source_row)`; source native tự clamp negative elapsed days về0, nên guard chronology là contract của wrapper, không claim native có cùng rejection behavior.

Predict native có thể lazily tạo prior state của current exercise và parents. Không tuyên bố predict là state-readonly hoặc đã có transactional candidate-query semantics. `state_snapshot()` trả copies phục vụ kiểm parity, không checkpoint/resume artifact. `as_online_backend()` từ chối; score role là `synthetic_online_state_engineering_only`, không shared fitted OnlineScore.

## Flags và giới hạn diễn giải

Native adaptation flag **ghép parent adaptation và local adaptation**: parent uncertainty/deficit đi vào q/decay, local struggling và times_forgotten đi vào negative-response noise/decay. Vì vậy full-package difference không là pure edge effect. Empty graph với adaptation bật vẫn có thể khác all-off.

Các recipe dưới là **fixtures để bao phủ branches**, không cấu hình được chọn cho phương pháp nghiên cứu:

| Fixture label | Signal / adaptation | Graph | Weight / base decay trong test |
|---|---|---|---|
| Source-free endpoint | False / False | Empty | 0 / 0 |
| Signal-only fixed | True / False | Toy fixed | 0,35 / 0,02 |
| Coupled adaptation only | False / True | Toy fixed | 0,35 / 0,02 |
| Coupled full package | True / True | Toy fixed | 0,35 / 0,02 |
| Flags-off nonempty control | False / False | Toy fixed | 0 / 0 |
| Empty-graph package | True / True | Empty | 0,35 / 0,02 |

Source-free endpoint chỉ được kiểm bằng cùng scalar settings với factory graph-free hiện có. Tắt hai graph flags không tự bảo đảm bằng benchmark graph-free nếu caller đổi time_decay hoặc các thông tin khác. Các labels không suy ra flags trong API; behavior do recipe tường minh quyết định.

## Kiểm thực tế

Source/tests đã được reviewer đọc trước lượt đầu. Review tìm thấy materialized graph ban đầu còn cho phép attribute rebinding trong khi identity chỉ hash graph declaration. Đã giữ **2 source/test snapshots và review note trước sửa** tại `artifacts/akt/local-tests/graph-gam-pretest-review-20261108-01/`; ở thời điểm đó có **0 tests/0 native updates**. Sau sửa frozen graph + actual-parent binding, reviewer static fix PASS. Không tạo một red-test run giả; không có failed targeted suite trong batch này.

| Kiểm có output xác nhận | Kết quả |
|---|---|
| Targeted suite | **38 passed,1,41s**,0fail/error/skip; controller2,114884s,timeout60s,returncode0 |
| Native update ledger | **97 calls** gồm candidate và independent source reference, dưới hard cap512; mỗi session tối đa32; **0 optimizer steps/0 global fit calls** |
| Source stability | 10 source files SHA before=after, gồm own2files, native/replay/model/runner/evaluation/simulator-pathways/reference-loader và notebook |
| Copy stability | Source/test snapshots khớp SHA trước/sau copy; bundle đóng giữ inventories riêng |

Sáu variants đều so **exact prediction và toàn bộ state fields** sau4events với cell nguồn: theta, memory, pi_task/pi_time, attempts, last_timestamp, recent_outcomes và times_forgotten. Fixture state cố ý nonneutral gồm hai parents khác nhau, memory khác0, struggling, forgotten count, elapsed gaps và downward threshold crossing. Đây là manually seeded state kiểm source behavior, không phải learning outcome của người học.

Positive/negative controls còn kiểm parent-state perturbation làm signal-on prediction đổi; empty-graph local adaptation khác all-off; cùng recipe flags-off cho empty/nonempty graphs khớp; current response0/1 cho cùng pre-update prediction rồi post-update states khác; ordering spy predict→update; metadata caller mutation không lọt vào captured maps; crossfactory cache/metadata và freshlearner isolation; returned-binding copies; source/settings/actual-graph tamper; invalid flags/types/domain/direction/SHA/cycle/size/query và call33 bị chặn trước native predict.

Lệnh đã chạy trong project `.venv`, wrapper `subprocess.run(...,timeout=60)` ghi log/JUnit/run receipt và chỉ định basetemp riêng:

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/gam_kt/test_variant_factory.py -q -p no:cacheprovider `
  --basetemp artifacts/akt/local-tests/parallel-graph-gam-variant-20261108-01/t `
  --junitxml artifacts/akt/local-tests/parallel-graph-gam-variant-20261108-01/pytest.xml
```

`GRAPH_GAM_UPDATE_LEDGER` trỏ tới `toy_update_ledger.json` cùng attempt. Khi tái chạy cần ID mới, không overwrite evidence. Không broad/full suite rerun ở tiểu tác vụ này; parent xử lý integrated gate nếu phù hợp.

## Chưa được nghiệm thu

1. Chưa graph-enabled Junyi CV/pilot wiring, train-only graph/difficulty artifact contract, common fitted-target coverage, export/resume hoặc strict checkpoint training provenance. Current runner/evaluation/model factory cũ giữ graph-free; không lấy toy parity làm research benchmark.
2. Chưa complete simulator/shared OnlineSession backend, read-only candidate-query/ticket semantics, mastery reference/calibration/threshold hoặc controller adoption. Numeric IDs/domain giữa Junyi và Grade10 không được ghép tạm.
3. Chưa chốt S04/S05 hoặc học confidence/graph từ dữ liệu. Caller-declared synthetic origin/provenance SHA không xác thực rằng một graph thật được học đúng train-only scope. Không tự adopt các fixture values, graph/noise controls hoặc allocation.
4. Chưa có predictive/learning efficacy, uncertainty/Holm hoặc kết luận RQ1/RQ2/RQ3. Chưa Linux/CUDA/large-resource acceptance; caps/session và suite timeout không là production throughput, hard process isolation hoặc peak-RAM certificate.

Không query dataset/Holdout, cài dependencies, global model fit, GPU/cloud/network, sửa original_junyi/model/runner/evaluation/shared/native AKT, notebook nguồn, root tracking/state hoặc Git. Simulator pathways có sẵn giữ nguyên. Bước tiếp theo là adapter/artifact/orchestration contract được review theo allocation; không viết lại mô hình hoặc tự mở corpus để lấp completion matrix.
