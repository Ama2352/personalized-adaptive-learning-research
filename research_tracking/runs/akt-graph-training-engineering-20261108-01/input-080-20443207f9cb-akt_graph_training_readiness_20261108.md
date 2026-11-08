# GRAPH04: lifecycle train–selection graph-aware AKT, kiểm kỹ thuật toy

Ngày08/11/2026. **Đã kiểm chứng đường graph toy bằng một complete epoch và một partial epoch; chưa là fitted research CG-AKT hoặc PASS toàn Gate.** Bộ actual02 giữ nguyên kết quả45PASS/1FAIL; lỗi kỳ vọng inventory ở test base được sửa và gọi lại riêng trên artifact đã lưu, không fit lại. Báo cáo không đổi nhãn kết quả cũ thành46PASS.

## Thay đổi và phạm vi

[graph_training.py](../../src/knowledge_tracing/akt/graph_training.py) bổ sung adapter với `.native` là **toàn GraphAKTPrototype**. Adam, clipping và checkpoint vì thế gồm backbone, message, readout và gate. Callback hẹp trong [training.py](../../src/knowledge_tracing/akt/training.py) giữ nguyên default collator, từ chối kết hợp callback với recovery; callback nhận TrainingWindow thật trước khi mất learner/window/global metadata. Một ticket gắn đúng object batch, consume-once và weight version chặn foreign/stale/mutated input. [simulator_engineering.py](../../src/knowledge_tracing/akt/simulator_engineering.py) dùng chung một lifecycle cho base và graph, có purpose/domain/policy riêng; không thêm trainer chung thứ hai hay giả Junyi fold.

Graph setup chứa directed graph, variant, full EdgeConfidence/provenance và explicit Linear recipe/initial values. Helper identity JSON-compatible chạy trước deserialization/neural constructor. Loader kiểm source/config/recipe/input, actual payload SHA, bounded8MiB, `weights_only=True` và full state keys/shapes/dtypes/finiteness. Không pickle callable. Chỉ complete epoch được lưu; graph run xuất prediction CSV và target-label sidecar riêng sau prediction, rồi COMPLETE với resource guard sau publication. Marker một mình không chứng minh run accepted nếu có failure receipt.

Đây là handmade observables, CPU d32/dropout0, tối đa2 train learners/1selection learner/12events mỗi learner, graph≤4concepts/16edges/bank≤8items. Recipe message dùng mean observed correctness; gate bốn feature `S/(1+S)`, mean/variance confidence trên ALL declared query parents và observed-parent fraction. Confidence structural của fixture là0,25/0,75 do caller khai báo; không estimator hay calibration fit. Seed/model settings giữ config smoke hiện có; không chọn phương pháp S04/S05 từ pilot này.

## Bằng chứng thực tế, giữ cả failure

| Lượt | Kết quả thực | Controller | Neural/optimizer mới |
|---|---|---:|---|
| Adapter pure01 |19PASS/15FAIL: fixture trùng source_rows, guard chặn trước adapter |11,137144s |0 |
| Adapter pure02 |34PASS/0failure/error/skip |7,245419s |0; spies cấm constructor/Adam/load |
| Callback pure01 |0tests: SyntaxError ở inline harness |0,210127s |0 |
| Callback pure02 |8PASS/0failure/error/skip |17,488995s |0; raising spies |
| Actual01 |32PASS/3FAIL/11ERROR; available-RAM floor chặn |19,211556s |0reservations/returns;0run dirs |
| Actual02 |45PASS/1FAIL; **6graph tests đều PASS** |18,247347s |4global reservations/body returns |
| Inventory correction01 |PASS một test-function với stored base artifact, không pytest suite mới |9,229979s |0; constructor/load/Adam spies |

Adapter-pure ledger18,382563/30s; callback-pure ledger17,699122/30s độc lập. Actual gồm RAM failure, actual02 và readonly correction dùng **46,688882/60s**, đúng **4/4 optimizer reservations và body returns**: base happy1+base partial1+graph happy1+graph partial1. Không còn quota update trong gói này. Đây là thời gian kiểm thử, không training throughput hoặc chi phí benchmark.

Actual01 lỗi `synthetic engineering available RAM floor` ở guard trước outputmkdir/neural constructor. Floor production1GiB không đổi; **số available RAM chính xác tại failure không được ghi**. `ram_preflight01.json` sau failure ghi670912512bytes và WAIT/no child; không được dùng con số này thay cho RAM tại failure. Sau khi người dùng giải phóng RAM, root preflight02 đạt recommendation3GiB và actual02 mới chạy; không hạ floor hay tự reset budget.

Actual02 thất bại một test base vì expected inventory cũ chỉ liệt kê3 shared helpers, trong khi source chủ ý bổ sung `graph_context.py`/`graph_augmentation.py`. Source production không sửa sau actual02. Test fixture được sửa expected list, giữ snapshot SHA cũ và kiểm riêng bằng một direct call với stored artifact; không dựng JUnit giả, không rerun toàn46case. Pure01 và callback harness failure cũng giữ nguyên raw logs/source snapshots.

## Đường graph đã được kiểm chứng đến đâu

Complete A3 toy có1update/8train targets; backbone, message, readout và gate đều có parameter changes. Selection xuất đủ **4 unique learner/source_row/global_rank keys =3scored+1OOV**; OOV rank1 probability và toàn graph telemetry null. Labels thật nằm trong sidecar, không trong prediction input/rows. Prefix sau OOV giữ global rank và effective_start2. Target coverage không bị thu hẹp để chỉ báo metric trên phần thuận lợi.

Checkpoint graph SHA256 `b961323f18749985005dbcd38443a18d60f3a0b1b761e4ea760522911560592f`; actual strict reload có max probability delta0 và exact target/telemetry parity. Binary giữ tại run gốc; archive dự kiến chỉ lưu SHA/size references. Partial graph run đã thực hiện1update/4targets trước step cap: local/global events giữ được công việc đã xảy ra, failure receipt không claim rollback; không checkpoint, selected CSV, result hoặc COMPLETE. Không yêu cầu loss/metric cải thiện để PASS kỹ thuật.

Tất cả graph evidence dùng cùng effective causal window của backbone, không thêm full-history cache. Toy≤12events chỉ kiểm OOV reset/global anchors, chưa thực nghiệm rollover context100. Tắt graph trả cùng backbone của model đó; chưa có selector chuyển sang checkpoint A0 độc lập. Checkpoint có optimizer/RNG payload của helper hiện có, nhưng **resume_supported=False** vì chưa có graph sampler/recovery contract; lifecycle seed/restore RNG toàn cục, không hứa giữ nguyên RNG của caller. Dataclass/SHA/module provenance là consistency contract hợp tác, không chống caller giả toàn metadata và không chứng minh semantic mapping hay train-only confidence estimation.

## Hồ sơ và kết luận được phép

[archive_facts.json](../runs/akt-graph-training-engineering-20261108-01/input-017-40474f0286f1-archive_facts.json) đối chiếu XML, snapshots, global/local events, đủ CSV keys và binary hashes bằng stdlib, không chạy model. [Parent raw review](../runs/akt-graph-training-engineering-20261108-01/input-035-9b441f8aadc6-parent-raw-lifecycle-review.json) ghi review độc lập của root trên4run dirs và raw outputs. [Partial snapshot trước actual02](../runs/akt-graph-training-engineering-20261108-01/input-037-82b66ea743ff-partial-before-actual02.md) được giữ lịch sử, không thay báo cáo hiện tại. Log/JUnit/receipt từng lượt nằm trong hai prep được inventory bởi packager; source trước/sau copy sẽ được kiểm lại trước closure.

Có thể kết luận: **adapter đã nối actual optimizer step vào toàn graph model và hoàn thành train–selection–checkpoint/reload/export trên handmade CPU toy, với negative partial và ledger rõ**. Chưa thể kết luận: baseline CG-AKT nghiên cứu đã fitted/selected, confidence/gate đã calibrated, RQ3 có lợi ích, robustness đã chứng minh, S04/S05 đã adopt, hoặc full Gate/source hiện tại đã PASS. Source Gate24 đã stale; cần parent điều phối software Gate riêng. Không Junyi/Holdout/GPU/cloud/real-data benchmark hay scientific protocol adoption trong gói này.
