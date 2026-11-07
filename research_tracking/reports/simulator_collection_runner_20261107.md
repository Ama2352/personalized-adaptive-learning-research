# Collector mô phỏng và adapter KT theo role — 07/11/2026

## Mức hoàn thiện

DATA05/06 đã có code và **60targeted tests pass,0fail/error/skip**,8.85giây, trong [run02](../runs/cpu-sim-collector-20261107-02/README.md). Đây là collector/adapter fixture, chưa là full training runner hoặc corpus nghiên cứu được duyệt. Không train NN, không đọc Junyi/real Holdout, không GPU/cloud. Gate2 toàn source cần refresh sau gói này.

Chi tiết API/contract tại [19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES](../../docs/thesis_recovery/19_SIMULATOR_DATA_AND_GRAPH_BOUNDARIES.md), phần DATA05–06.

## Những gì đã kiểm được

- Phương trình Paper2 unchanged: supplied identical base/uniforms/items/time tái hiện exact từng oracle output và final snapshot. Không chạy notebook top-level, không thay historical results.
- Collector chỉ train,2learner×12events/call,<=30giây/call. Integration gọi2lần để kiểm repeat; cả observable và oracle khớp exact. Không generate các roles khác. Profile PY/PG chỉ ở metadata/oracle.
- Item selection `uniform_items` trong integration không đọc theta/graph; `cyclic_items` được kiểm riêng. Hai policy này là fixture version mới, không tự tương đương logging/replay policy lịch sử hoặc đại diện deployment.
- RNG NumPy PCG64 explicit, response channels tách outcome/learning, behavior riêng; các prefix uniforms giữ nguyên khi tăng fixture cap. Legacy NumPy global RNG không bị đổi. Không chứng minh learner independence chỉ từ các seed namespaces.
- Clock Unix seconds UTC, event đầu start+gap; raw timestamp được chuyển đúng sang pandas timestamp cho forgetting dynamics. Latent state và true probabilities không có trong observable payload.
- Vocabulary fit train-only, learner support immutable, bind plan/domain/data hash. Cùng bank nhưng không có train support phải là OOV; không fake fitted prediction. Current/future labels không đổi causal input prefix của target.
- AKT windows/collation giữ global target anchors, OOV barriers và đúng population; dùng native window geometry, không giả folds Junyi. Prediction không có unshifted labels; OOV query không có correctness field. Labels ở scoring contract riêng.
- Calibration/final prediction và selection optimization bị chặn. Không gộp roles để refit hoặc tự chọn mastery threshold/epoch.

## Bằng chứng và các lần thử không thành công

[run02](../runs/cpu-sim-collector-20261107-02/README.md) có observable.json, oracle_sidecar.json, collection_manifest.json, split_plan.json, proof.json, tests.log/JUnit/result cùng source/output hashes. Oracle file chỉ cho replay/evaluation; không dùng nó làm features. Proof ghi24targets,12windows, batch shape12×5 và0optimizer steps.

[run01](../runs/cpu-sim-collector-20261107-01/README.md) có status failed: collector/window proof tạo được nhưng pytest collection thất bại vì hai modules `test_simulator_data.py` trùng basename. Đổi test AKT thành `test_simulator_role_windows.py`, giữ nguyên bytes test; không sửa bundle cũ hoặc xóa cache. Không đọc status failed này như kết quả model kém hay collector output sai.

Trial local trước đó (`artifacts/akt/local-tests/collector-01.*`) có2failed/8passed/3errors do input paths từ reference dùng backslash Windows; đã lưu source snapshot và sửa canonical provenance paths trong collector mới, không sửa source Paper2. Trial02 đạt14tests; trial03 đạt34tests trước khi thêm collator test. Các logs quan trọng sẽ được archive cùng final gate. Shell lỗi đọc output chưa tồn tại không được tính là thí nghiệm khoa học.

## Giới hạn và bước tiếp theo

24events rất ít so với84items: đây chỉ là kỹ thuật, chưa kiểm đủ history/profile/item coverage cho AKT. Counts/profiles/policy/gap của fixture không là protocol train chính thức. RQ1/RQ2 cần confirmatory controls/interpretation; RQ3 còn graph variants, confidence/gate training và controlled evaluation. S04/S05 về calibration/controller/model-environment scope vẫn pending.

Các phần không tự nối vào Junyi runner: simulator selection/epoch rule, refit policy, artifact/checkpoint authorization và final evaluation runner. Source compatibility của windows không tự cấp quyền chạy các bước đó. Kitv9 cũ chưa có collector/adapter mới; chưa chạy Linux/Colab/CUDA.
