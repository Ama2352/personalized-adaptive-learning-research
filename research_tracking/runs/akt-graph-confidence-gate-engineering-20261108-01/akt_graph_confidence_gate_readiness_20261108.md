# AKT A2/A3: confidence theo cạnh và gate — kiểm kỹ thuật08/11

## Kết quả và giới hạn

Prototype hiện có A0 graph-free, A1 fixed-uniform, A2 confidence-weighted và A3 confidence-weighted với gate trainable do caller cấp. **43 targeted CPU tests PASS**, không fail/error/skip trong lượt cuối; **0 optimizer steps**, không realdata/Holdout/GPU/Modal. Đây là forward/backward engineering trên domain tổng hợp, tối đa2learners/4concepts/12events mỗi learner, hidden32/dropout0. Chưa là CG-AKT đã train hoặc evidence trả lời xong RQ3.

Nguồn: [module](../../src/knowledge_tracing/akt/graph_prototype.py), [tests](../../tests/akt/test_graph_prototype.py), [bundle](../runs/akt-graph-confidence-gate-engineering-20261108-01/README.md), [manifest](../runs/akt-graph-confidence-gate-engineering-20261108-01/manifest.json). Khi report được freeze trước closure, links bundle là tên đích đã định; chỉ mục nghiệm thu sau closure phải kiểm tồn tại/hash, không sửa snapshot để giả timestamp khác.

Source SHA-256: `9fc6b8271da503ce16d25147a320bf0ffb9312e5416abae40fbb034f26d3157a`.
Test SHA-256: `17cdfe58dfdbb2e3c4eaba05f62020e3b1289e6a06a69b35b9eddca9af5e09bd`.

## Kiến trúc tối thiểu đã cài

Giữ nguyên upstream AKT NonRasch và six-operation bridge lấy hidden/logit; không monkeypatch, inverse-sigmoid hoặc detach loss. Residual dùng kernel hiện có:

`z_aug = z_base + g * dot(readout, sum(c_edge * observed * message) / max(1, observed_confidence_mass))`.

- A0 gọi native backbone; A1 confidence uniform1, gate1.
- A2 bắt buộc caller cấp `EdgeConfidence` cùng provenance; có thể cấp explicit uniform để làm control so với A1. Không tự chọn confidence khi thiếu input.
- A3 thêm caller-owned trainable gate, `sigmoid(gate_module(features))`, yêu cầu output finite FP32 CPU `[1,1]`. Recipe gate phải khai báo tên explicit.
- Message giữ một feature là mean observed correctness của prerequisite trong cùng effective history window. Không mở rộng history cho graph model.

Recipe gate **engineering-parent-support-confidence-v1** chưa được chọn làm phương pháp cuối. Bốn feature theo thứ tự: `S/(1+S)` với S tổng support, mean confidence, population variance confidence, fraction parents có support. Mean/variance dùng **toàn bộ declared parents của queried concept**, kể cả parent chưa quan sát; không dùng current/future label hoặc latent simulator. Không có parent trả vector0.

Confidence và gate feature recipe được seal vào model/batch binding; contexts dựng từ full observable prefixes qua geometry hiện có. A0/A1 vẫn dùng fixed-uniform. `structural_score` khác `estimated_probability`; loại estimated chỉ nhận declaration train-role. **SHA/role là consistency contract, chưa xác minh artifact estimator thực tồn tại, đã fit train-only hoặc calibrated**. Handmade fixture không được gọi là fitted confidence. Oracle labels bị từ chối kể cả khi disable; nghiên cứu oracle reference riêng vẫn chưa tích hợp prototype.

## Bypass và độ công bằng

Disable toàn batch, graph-empty, không có support hoặc observed confidence mass bằng0 gọi nguyên native tuple **trước branch operations**. Trong batch hỗn hợp, inactive query giữ base probability của chính forward đó. Gate telemetry trả các gate đã tính và mass; inactive slots0 không phải gate được model đánh giá, whole-native bypass trả `gate_values=None`.

Disable A3 tái hiện **backbone của cùng A3 checkpoint**. Nó chưa chuyển sang checkpoint A0 độc lập. Không được gọi hai cơ chế này là cùng một graph-free fallback, và chưa có checkpoint selector hỗ trợ system fallback.

## Kiểm chứng actual và failure giữ nguyên

| Lượt | Kết quả actual | Diễn giải |
|---|---|---|
| attempt01 | 43tests:3PASS,16FAIL,24ERROR; controller8,0816403s | Upstream Git checkout bị dubious ownership trong child. Không sửa global Git config hoặc bỏ provenance check. |
| attempt02 | 41PASS,2FAIL; controller16,2286716s | Child-only safe.directory cho hai checkout đã kiểm. Hai test mới cố perturb shard train đã seal; guard đúng từ chối `train data changed after vocabulary fit`. |
| attempt03 | **43PASS/0FAIL/ERROR/SKIP**; pytest11,92s/controller15,3405831s | Sửa fixture để perturb disjoint selection histories; giữ train binding, peer-independence và native equality. Cache output chuyển vào attempt. |

Tổng controller ba lượt **39,650895s ≤ 120s**, child đều được reap; không reset budget sau failure. Controller01 không được snapshot riêng trước sửa harness; receipt/argv/log/source snapshots01 vẫn giữ. `controller_postattempt02.py` được lưu sau lượt02, không giả là pre-execution snapshot. Lượt03 có snapshot controller actual. Không tuyên bố resource telemetry hoặc native call-count instrumentation mà harness chưa đo.

Các acceptance đã kiểm: A2 uniform khớp A1 cùng backbone/branch weights; signed residual bằng công thức độc lập; finite/nonzero gradients tới backbone/message/readout và gate A3; whole disable/all-c0 outputs/count/loss/backbone gradients **bitwise equal** native; thread1/2 được khôi phục, control/backward cùng thread contract; mixed inactive parity; confidence provenance drift bị reject; current/future perturbation không đổi current probability; peer/padding isolation; OOV barrier giữ global anchor và không graph rescue; wrong gate output bị reject. Tests A0/A1 và upstream/source checks cũ vẫn nằm trong targeted suite.

## Phần còn thiếu trước nghiên cứu và GPU

1. Graph-aware train/validation/checkpoint/export lifecycle; hiện `train_epoch` vẫn dùng native AKT batch/adapter, không tự train A2/A3 này.
2. Confidence estimator/calibration artifacts hoặc explicit oracle-reference experiment; gate recipe, item mapping, mastery/reference và experiment allocation cần S04/S05 quyết định.
3. Full simulator corpus, context rollover100 và final comparison protocol; toy T≤12 chưa phủ runtime rollover.
4. Fresh full software/source gate và source kit mới trước actual GPU. Linux Gate24 771PASS là snapshot **trước thay đổi module/tests này**, không chứng nhận current source. Các warm/cold GPU-host preparation mới vẫn chỉ mock/static review.
5. Actual CUDA mainworker/recovery, measured throughput/cost và explicit bounded Modal authorization. Không dùng targeted CPU PASS để tự cho phép spend hoặc full CV.

Đóng gói lưu raw failure, source/test snapshots, JUnit và peer review để trích báo cáo; integrity PASS không là model efficacy hoặc methodology approval.
