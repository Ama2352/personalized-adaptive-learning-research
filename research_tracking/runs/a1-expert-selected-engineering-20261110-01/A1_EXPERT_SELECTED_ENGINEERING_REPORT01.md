# A1 expert đã hoàn tất selected-only trên corpus engineering10

10/11/2026. Đây là nghiệm thu positive normal entry CPU của A1_EXPERT theo recipe26. Lượt accepted chạy native `main-a1-expert-engineering10x84-20261110-01`, bằng request03 và operational namespace03. Không chạy lại mô hình trong quá trình kiểm và lưu bằng chứng.

## Config, data và graph

Numerical config giữ nguyên accepted A0 continuous. Chỉ run_id/output_dir và allocation RSS1GiB→2GiB khác. Giữ seed42, d_model256,8heads,1block, d_ff1024, final_fc512, dropout0,05, context100/target_block100, batch4, Adam0,0001, max20epochs, patience3/min_delta0,0001 và CPU2threads.

Corpus engineering10 có8train/1selection/1calibration với672/84/84targets. Graph condition mới `2555ffbc1657f37d27aae331f99e4575869e952c0c307a111f0909e60385c744` bind đúng train8. Topology expert public28/31 dùng unit confidence và fixed gate. Không dùng Method24/confidence train48. Source public topology SHA `a10d1a78631b442f4b65c3ddb67b01d198e09a83bf659277cf04c25258099b48`.

Actual claim có initial-backbone SHA `d80de4e015d4673a714be76468078de4f168709fb2aa41bc5c6771f78af2bf63`, khớp A0 control. Full model SHA khác vì A1 có thêm scalar alpha. Không load trained A0 làm initialization.

## Kết quả thực thi

Lượt selected fit hoàn tất7epochs, best epoch4,14Adam steps và4.704train-target exposures. Có2model constructors,2Adam constructors,22native forwards gồm14training và8selection; tổng672selection-target evaluations. Fresh-best reload xuất full84raw selection, tất cả supported, không refit/calibration hoặc external freeze.

Checkpoint save4, inspect2, restore1. Metadata/auth/native-evidence/corpus audit mỗi loại51calls, revalidate50; Git provenance530calls gồm hai constructor. Native journal khớp14started/body-returned/committed và7complete epochs. Observer giữ targeted passthrough, không global profiler hoặc patch Adam.step/backward.

Nguồn actual là `a1-expert-engineering03/actual-completion-check.json`, `result.json`, `observer.json`, `outer-final.json`, owned receipt và native selected terminal/claim. Source trước–sau, request/config/auth/native outputs và runtime/Gate bằng chứng thật đều được public entry cùng outer kiểm. Đây là selected-only engineering proof, không suy ra hiệu quả đồ thị từ một selection learner.

## Resource và tiến trình đã thoát

Stored outer138,40406769997207giây, owned136,970623254776giây và worker135,64639040001202giây. Profile terminal Root ghi khoảng138,5387giây. Các khoảng đo được giữ riêng.

Actual1223samples có worker high-water559.652.864byte, family sampled peak558.084.096byte, minimumfree4.060.610.560byte và maximum5Job members. Worker high-water dùng cả peak_wset, còn family peak là tổng RSS tại các thời điểm lấy mẫu, nên hai đại lượng không cần có cùng thứ tự. Monitor/queryhandle/observer được đóng, ownedJob0 và không có CUDA initialization.

Guard ghi15process exits trong lúc lấy mẫu, trong đó13có exact opened-handle Wait0 cùng exitcode. Không cộng RSS hiện tại của process đã được xác nhận thoát. Điều đó không mô tả peak lịch sử của process đó. Live/unknown errors và PID/creation-time mismatch vẫn fail closed.

Admission03 từ chối trước NN vì ba mẫu chưa đồng thời vượt4GiB+128MiB. Admission04 có ba mẫu4.757.913.600/4.757.876.736/4.744.691.712byte và được Root duyệt. Canonical caps giữ4GiBadmission,2GiBworker/family/free2GiB, main540/training300/worker560/owned580/outer600 cùng cleanup3. Không giảm cohort, epoch cap hoặc hyperparameters.

## Bằng chứng trước retry

Attempt01 dừng do monitor Win5, trước native allocation/model update. Source public runner tạo native directory trước lazy NN; directory vắng, source giữ nguyên và Job0 là cơ sở0NN. Chi phí vận hành failure được giữ riêng, không reset thành chưa từng chạy.

Bundle `owned-job-resource-exit-guard-20261110-01` có58outputs và manifest SHA `46e9b64d1066667e9ac974db8d5236dc67934df0050f5b37e58fb69f6ba8cff7`. Gói mới tham chiếu bundle đó, không nhân đôi failure/probes/canaries. Hai probe có8operational Git children, mỗi lần image query sau known exit đều gặpWin31, IsProcessInJob vẫntrue. Win5 ban đầu chưa có traceback để xác nhận nguyên nhân. Chín canaries và trace logging của guard mới được giữ tại bundle guard.

## Phạm vi còn lại

A1 đã có fitted selected-only checkpoint và full raw selection export trên engineering10, cùng verified fresh initial backbone đối chứng A0. Bốn checkpoint nhị phân giữ tại native paths, bundle chỉ lưu SHA/size refs. Không Torch-load khi archive.

Chưa có full Main60/Junyi matrix, system selection freeze, refit90, calibration10, inference thống kê, human learning-gain experiment hoặc actual CUDA. Không có claim graph superiority hay thêm mẫu nghiên cứu độc lập. Cloud/Modal mới bằng0.
