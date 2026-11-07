# Collector mô phỏng và adapter KT theo role — 07/11/2026

## Mức hoàn thiện

DATA05–07 completed CPU engineering với **65targeted tests** ở [run04](../runs/cpu-sim-collector-20261107-04-portable/README.md) và **401tests source-bound Gate2-13**, khôngfail/error/skip. Đây là collector/adapter fixture và compatibility fix, chưa là full training runner hoặc corpus nghiên cứu được duyệt. Không đọc Junyi/real Holdout hoặc dùng GPU/cloud. Collector proof không instantiate NN/optimizer; software suite có các bounded native synthetic tests sẵn có. Run02 với60tests là snapshotv1, chi tiết các lần thử bên dưới.

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

## Review bổ sung và sửa domain portability

Static audit dùng chính bundler xác nhận code cells unchanged nhưng raw notebook SHA353f487a... thành53c2c814... do strip outputs/metadata. Domainv1 khác nhau vì hash full storage provenance. Đây là incompatibility của collector mới cần sửa trước remote training, không là lỗi Paper2 và không sửa historical checkpoints. [Archive trials](../runs/cpu-sim-collector-trials-20261107-01/README.md) giữ12outputs gồm local failed logs/source và audit JSON.

Collector **v2** dùng semantic identity của allowlisted definition hashes/constants/immutable input hashes/clock; full notebook storage SHA vẫn ở integrity provenance. RNG namespace giữv1. [run03-semantic](../runs/cpu-sim-collector-20261107-03-semantic/README.md) đạt64tests; [run04-portable](../runs/cpu-sim-collector-20261107-04-portable/README.md) đạt**65tests,0fail/error/skip,7.48s**, thêm trường hợp checkout đã strip outputs (transform idempotent). Các negative controls thay equation/constant/true-graph input đều làm domain đổi. Chưa chạy actual Linux/CUDA từ các tests này.

Đối chiếu v1run02 vớiv2run03: **oracle sidecar gồm RNG states/uniforms và learner queries/labels identical**. Domain/policy/recipe identities đổi có chủ đích theo version; không tự migrate model cũ. Fixture vẫn22observed/62unobserved items,24targets và0optimizer steps.

Gate2-12 của sourcev1 đạt396tests,0fail/error/skip374.84giây (wall378.92s), timeout420s. Sau semantic fix phải coi gate này là snapshot; source mới cần Gate2-13. Dự toán software suite mới540s (hard maximum600s ở runner) vì measured runtime biến động lớn so với gate361/152.84s trước; không đổi smoke/pilot/training/cloud budgets hoặc bỏ tests.

## Gói chuyển runtime và cập nhật chỉ mục

V10135files SHA `db6b122df8297135db04ad63835b3d96909b403467456983b9c04b5082049eab` đã kiểm ZIP/hash/source parity, có collectorv2/adapter/unique test module names; không kèm dataset/checkpoints/oracle JSON. [Bản kiểm](colab_bundle_v10_verification_20261107.json) ghi notebook-copy transforms. Chưa extract/execute suite trong bundle hoặc chạy Linux/Colab/CUDA; Windows CPU wheel lock chỉ là fixture hash, không dùng install Linux image. V9 giữ nguyên như snapshot lịch sử.

Registry bổ sung16terminal run manifest indices đã có từ các batch recovery/interface/data/collector; đây là backfill chỉ mục, không phải16thí nghiệm mới hoặc nâng mức kết luận RQ. Failed run giữ statusFAILED; execution hoàn tất archive không làm trialfailed thànhpass. `CLAIM_EVIDENCE_MATRIX`, ledger và reportsREADME được nối để sau này trích đúng loại bằng chứng.

## Nghiệm thu source cuối

**Gate2-13:401passed,0failed/error/skipped,374.53giây**, explicit CPU suite budget540s; source/lock/upstream ổn định và current pointerverified. Report SHA `fddb2fe0e8efb15002f35a2079ebada2bace12aacfbf21d3cefde8ce9df6c546`. [Archive14outputs](../runs/cpu-sim-collector-gate-20261107-01/README.md) giữ report/log/JUnit401 và396, current/previous pointer, v1test snapshot đúngSHA, v1/v2RNG parity và v10verification. Chỉ2sourcefiles đổi từ gate396 sang401; prior snapshots được kiểm với hashes report396, không thay report cũ.

DATA05–07 complete trong phạm vi engineering đã nêu. Registry42entries sau khi thêm gate archive mới. Các con số này không đổi trạng thái RQ: chưa có CG-AKT trained/evaluated hoặc accepted full simulator experiment. Không phải mọi phần cài đặt mô hình đã hoàn thành.
