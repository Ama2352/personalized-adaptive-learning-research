# Prototype hợp đồng residual graph và gate — 07/11/2026

## Phạm vi và mức bằng chứng

Đây là **kiểm kỹ thuật synthetic CPU**, chưa là CG-AKT hoàn chỉnh, mô hình graph đã train, kết quả RQ3 hoặc bằng chứng graph có lợi. Nguồn quyết định: `docs/thesis_recovery/06_AKT_CGAKT_ARCHITECTURE_PLAN.md`, `19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md`, `src/knowledge_tracing/graph_context.py` và adapter AKT hiện có. Không đọc dataset/Holdout, không benchmark thật, không instantiate native AKT, không optimizer/training/GPU/cloud.

S04/S05 và semantics của f/gate vẫn chờ review. Native adapter hiện expose probability, chưa có public latent/base-logit hook. Vì vậy gói này chỉ thêm kernel/hợp đồng có thể kiểm riêng, không tự chọn kiến trúc projection, feature transformation của learned gate hoặc sửa upstream/model/config/hyperparameters.

## Tệp và hợp đồng

- `src/knowledge_tracing/graph_augmentation.py`: `prepare_graph_context` và `apply_graph_residual`, cùng dataclasses typed cho binding, evidence và output.
- `tests/shared_kt/test_graph_augmentation.py`: 42 test cases synthetic.
- `prepare_graph_context` gọi thẳng `audit_graph_context`; không viết lại causal-window arithmetic hoặc thống kê parent. Chỉ expose effective window, giữ observed rows, scoped-history hash, graph/confidence/domain/vocabulary hashes và support từng parent concept. Không nhận current response hoặc oracle sidecar.
- Kernel cho **một query có fitted base**. `base_logit`/`gate` là scalar floating tensor; `edge_messages` có shape `[E,D]`, `readout` có shape `[D]`, `D>=1`. Dtype/device phải trùng base, mọi active input finite. Thứ tự E đúng thứ tự `evidence.parents`.
- Caller phải bind domain/vocabulary từ metadata của base model đã xác minh, thay vì suy từ numeric item IDs. Kernel kiểm binding bằng equality; không tự mở/check checkpoint.

Với `o_j=I(support_j>0)`, kernel dùng đúng normalization đề xuất:

`mass = sum_j c_j * o_j`; `normalizer = max(1, mass)`;

`m = sum_j c_j * o_j * edge_messages[j] / normalizer`;

`residual = gate * dot(readout, m)`; `logit = base_logit + residual`.

Khác với diagnostic weighted mean trong audit, mẫu số chặn dưới1 giữ absolute confidence khi tổng confidence nhỏ hơn1. Đây là arithmetic residual mới của kernel, không sửa giá trị audit cũ. Test kiểm cặp confidence(.25,.5),(.1,.2),(1,1), support mask và residual âm; không ép graph luôn làm tăng logit hay cải thiện metric.

`gate` phải trong[0,1]. Caller có thể cấp1 cho fixed/weighted influence; kernel không tự tạo sigmoid hoặc học gate. Gradient active đi qua base, gate, messages và readout; bộ kiểm chỉ backward một scalar synthetic, không cập nhật tham số.

## Fallback và ranh giới thông tin

Disabled/empty graph/no observed support/all confidence0 hoặc gate0 trả **cùng tensor object `base_logit`**, residual0, không sigmoid/logit roundtrip hay cộng zero vào base. Tests xác minh bytes giữ signed zero ở float32/float64 và gradient base bằng1. Khi bypass không inspect messages/readout, nên branch-off không chạy arithmetic graph. Guards domain/vocabulary/oracle/fitted-base vẫn chạy trước bypass.

Đây là branch-off parity của base được bên gọi cung cấp. Không phải system fallback sang checkpoint A0 độc lập; chưa có system selector hoặc manifest selection. OOV target bị từ chối kể cả branch-off vì không có fitted base hợp lệ để graph cứu; module không biến OOV thành dự đoán fitted.

Confidence reuse `EdgeConfidence`: estimated probability phải khai báo fitted_role=train; oracle labels chỉ binary reference. Oracle cần explicit `oracle_reference=True` khi prepare **và** khi apply, kể cả disabled. Provenance hash và train declaration là contract cần đối chiếu artifact bên ngoài; không chứng minh confidence đã được fit/calibrate hợp lệ. Structural score không tự là xác suất cạnh đúng. Gói này không học confidence từ true-edge/future labels.

Preparation thừa hưởng kiểm chronology/current/future/duplicate row/domain/edge coverage/OOV barrier của audit. Perturb prefix ngoài effective window không đổi evidence; gọi context khác không làm đổi context trước vì kernel không giữ mutable cache. Tuy nhiên `Observation` không chứa learner_id, nên đây **không phải** chứng minh cross-learner isolation end-to-end: session bên gọi vẫn phải cô lập history theo learner.

Projected messages/gate là tensor caller cung cấp. Không thể chứng minh chúng chỉ dùng audited observable inputs bằng cách nhìn giá trị tensor. Khi tích hợp phải kiểm builder của f/gate, embeddings train-only, causal hidden-state hook và label-perturbation ở toàn bộ model path. Dataclasses cũng là hợp đồng trong process, không phải chứng thực chống caller giả mạo evidence. Không mở rộng claim kiểm leakage của context thành claim kiểm leakage toàn CG-AKT.

## Kiểm tra đã chạy và failure được giữ

Mọi invocation dùng `.venv\Scripts\python.exe`; không cài dependency. Không chạy full Gate2 vì source/tests đang được sửa song song; Gate2 cũ không nghiệm thu source mới.

| Lượt | Log/JUnit | Kết quả |
|---|---|---|
|01|`artifacts/akt/local-tests/parallel-graph-20261107-prototype-01/{pytest.log,junit.xml}`|2 collection errors trong8.45s: thiếu `PYTHONPATH=src`, không import được `knowledge_tracing`; giữ failure, không đổi dependency hoặc xóa cache|
|02|`artifacts/akt/local-tests/parallel-graph-20261107-prototype-02/{pytest.log,junit.xml}`|75passed,0fail/error/skip,4.23s:42cases augmentation và33cases graph_context|

Invocation PASS trong PowerShell, cùng `cache`/`tmp` mới dưới run02:

```powershell
$env:PYTHONPATH = 'src'
& .venv\Scripts\python.exe -m pytest tests/shared_kt/test_graph_augmentation.py tests/shared_kt/test_graph_context.py -q -o cache_dir=artifacts/akt/local-tests/parallel-graph-20261107-prototype-02/cache --basetemp=artifacts/akt/local-tests/parallel-graph-20261107-prototype-02/tmp --junitxml=artifacts/akt/local-tests/parallel-graph-20261107-prototype-02/junit.xml
```

Log thực tế được redirect cả stdout/stderr vào `pytest.log`. Thời lượng mỗi lượt dưới120s. Chưa kiểm CUDA, native AKT numerical parity hoặc full software gate. Không sửa shared state/tasks/index/manifests đã đóng; parent cần đưa báo cáo vào mục lục và archive cả success/failure sau review.

## Inventory SHA-256 trước handoff

Không di chuyển artifacts trong gói này. Hash raw bytes để parent đối chiếu khi archive:

| Tệp | SHA-256 |
|---|---|
|`src/knowledge_tracing/graph_augmentation.py`|`105aa918f1dc5d8fcfae22c9d8e7d2e13c1832b71d8b6a7ce8deed67d443ff08`|
|`tests/shared_kt/test_graph_augmentation.py`|`98d11d01cdf1e3e0412fa8f29c7d07b04be0db40e0975a0f49b33e1ace1cfc82`|
|`src/knowledge_tracing/graph_context.py` — dependency reuse, không sửa|`3db94ec43271d336898f61f81f12aeb569c6de52219eeed535af709711c97264`|
|`parallel-graph-20261107-prototype-01/pytest.log`|`f9c48ec2aff426b1c575e830eb9a785a5be1610b7534f1b9b6948a11e87703eb`|
|`parallel-graph-20261107-prototype-01/junit.xml`|`e5cc6f1443133682ab63b8c215cd0cf4b26b7ed6e8efbc167ab56d8ede4e44fe`|
|`parallel-graph-20261107-prototype-02/pytest.log`|`96fc4493c95b4d6315880e3004f8ac0ca3f1ab4d3deaa5f61409801a595ead67`|
|`parallel-graph-20261107-prototype-02/junit.xml`|`e2931a587179b18a6875a6a6a303c51022bdf01272a2e92cefd5b08e7b367bf1`|

Bốn đường dẫn log/JUnit rút gọn trong bảng hash đều tương đối với `artifacts/akt/local-tests/`.

## Điều kiện còn thiếu trước adoption

Cần review S04/S05 và chốt f(s,e_parent,e_query), gate features/mapping, train-only confidence artifacts và information-matched history; bổ sung native causal latent/logit hook mà giữ nguyên source upstream; kiểm toàn bộ current/future-label perturbation, session learner isolation, disabled parity trên cùng backbone và system A0 selection riêng. Sau đó mới xem xét training protocol và ablation A0/A1/A2/A3. Kernel PASS không trả lời các điều kiện nghiên cứu này.
