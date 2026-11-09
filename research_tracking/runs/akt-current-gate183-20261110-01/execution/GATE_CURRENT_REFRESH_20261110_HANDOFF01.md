# Chuẩn bị Gate hiện hành — 10/11/2026

SOURCE-ONLY, chưa import Python, chạy collection, test, preflight/Git hoặc Gate. Chưa có packet ROOT finalized, actual nodeIDs, report hoặc PASS mới. Không đổi source production, global pointer hay hồ sơ cũ.

## Inventory và phần reuse

Snapshot hiện có183 build members và85 test modules. Ba ordered groups có1/6/78 modules. Không suy số cases từ những số này. Map ghim đúng phạm vi native `gate2_build_hashes`, không thêm nested GKT/SAKT. Các thay đổi tương lai chỉ ở nested GKT/SAKT không tự làm thay đổi map AKT này. Những nguồn dependency riêng vẫn cần proof riêng của consumer tương ứng.

Snapshot được liệt kê bằng file metadata và ordinal string sorting. `prepare_current_freeze07.py` yêu cầu whole exact equality với genuine production `gate2_build_hashes()` và ordered `test_partition(ROOT)` trước khi tạo ROOT packet. Nếu không khớp thì dừng, không sort lại hoặc so subset để cho qua.

So với packet collection06 lịch sử177 members, map thêm6 nguồn và đổi14 nguồn, không bỏ nguồn. Thêm các file mastery-ready masking, selected resume và các test metadata CUDA/checkpoint. Danh sách chính xác nằm trong map, không là chỉ tiêu test PASS.

Collection12 chỉ đổi tên worker/output từ11. Đã so bytes với phép thay tên duy nhất. Tất cả guard, timer, profiler, resources, native shim identity và pywin32 namespace provenance giữ nguyên. Hai thư mục output12 và ROOT packet mới đều chưa tồn tại ở lúc handoff.

| File trong prep | SHA-256 |
| --- | --- |
| gate_source_snapshot07.json | 00f0e3afceccb7ae6e206d62efe21760451d4f55250e061d0ebb73951f198838 |
| prepare_current_freeze07.py | 5120088461cd27f742eee364ebe9d93c60a1616e79d5f925441cc9e40b94bff3 |
| gate_collection_worker12.py | de35c437e1e38e8dce101ba2ab04b9eb9c395c4caf7bbd65d334f6c5184a8cb2 |
| run_gate_collection12.py | 00e520cdf1f0de6c3f6389d319eec15553d63440c47027154b3e65767ba07818 |

Reuse nguyên bytes các file sau. Không clone Kernel, sửa refresh writer hoặc tạo thêm native launcher.

| File trong prep | SHA-256 |
| --- | --- |
| windows_current_gate_worker02.py | b59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374 |
| windows_current_gate_outer03.py | 4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e |
| prepare_windows_current_gate_packet04.py | 73bf611da9a0f0729fb52b8a9393d66de0bb577bca0c21b93e22168754e23bce |
| pywin32_namespace_record01.json | 318537f3d176fc396ebdc8fb660ffb320e62c4fb8545f7f7168e2512da12f625 |

Owned helper `scripts/research/windows_owned_worker.py` giữ SHA0dc8723170467e9ae73c4e233a357b9d584c66a8c183c478bdcff358fb0a95a1. Installed pytest JUnit mapper giữ SHA557b8978c66b8010fafc50ada4bf56333f9927f31b2b5909fe4c1a9df1a3c0f0. Old collection11 worker/outer được snapshot ghim để phát hiện thay đổi originals.

## Giới hạn và hành vi

Collection có whole60s cho ba fresh owned Jobs cộng cleanup/posthash, mỗi Job cleanup3s, admission4GiB trước library imports, free floor1GiB và peak mỗi process3GiB. Worker chặn test bodies, optimizer/model constructors/backward/solver/teacher/data/CUDA execution. Library imports thực hiện module tops sau GO. Group remaining có thể import actual Torch CPU, NumPy, Pandas và sklearn để collection, không chạy NN/solver body. Các nhóm pure giữ purity cũ.

Collection giữ root-first project namespace, pywin32 RECORD proof15files, literal bounded Windows metadata command, TEMP/TMP/TMPDIR và tempfile cache scoped vào owned outputs, explicit pytest log trong owned path và không terminal reporter. Không thêm ngoại lệ từ các lỗi MainC khác vào controller này. Giữ các attempt cũ và dừng khi guard từ chối.

Full Gate giữ native580s, owned tối đa600s gồm cleanup3s và outer630s. Admission4GiB, free floor1GiB, peak mỗi process3GiB không đổi. Default không publish. Outer kiểm actual accepted collection, exact per-group/merged physical JUnit identities,0FES, source/lock/upstream trước–sau, resources/Job0 và bytes global pointer. Các tham số này là giới hạn software checks, không quyền training hoặc CUDA.

## ROOT commands sau review

Các `<...>` bắt buộc được ROOT thay bằng tham chiếu hoặc SHA actual. Không ghi placeholder thành receipt. Tất cả path được viết tuyệt đối ở nơi helper `safe()` yêu cầu.

### 1. Review cú pháp và freeze metadata

ROOT kiểm AST ba file mới bằng stdlib trước invocation. Chưa có AST execution từ agent. Sau đó chạy helper dưới đây. Helper chỉ import definitions nhẹ và kiểm canonical map, không gọi `refresh()` hoặc collection.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/prepare_current_freeze07.py --helper-sha256 5120088461cd27f742eee364ebe9d93c60a1616e79d5f925441cc9e40b94bff3 --snapshot-sha256 00f0e3afceccb7ae6e206d62efe21760451d4f55250e061d0ebb73951f198838 --collection-worker-sha256 de35c437e1e38e8dce101ba2ab04b9eb9c395c4caf7bbd65d334f6c5184a8cb2 --collection-outer-sha256 00e520cdf1f0de6c3f6389d319eec15553d63440c47027154b3e65767ba07818 --root-freeze-reference <ROOT_SOURCE_REVIEW_REFERENCE> --output D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_collection07_packet.ROOT.json
```

### 2. Actual collect-only

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gate_collection12.py --packet D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_collection07_packet.ROOT.json --packet-sha256 <ACTUAL_FROZEN_PACKET_SHA> --worker-sha256 de35c437e1e38e8dce101ba2ab04b9eb9c395c4caf7bbd65d334f6c5184a8cb2 --approval-reference <ROOT_COLLECTION_REVIEW_REFERENCE>
```

Future actual final chỉ xuất hiện tại `gate-collection12-outer/final.json`. Status bắt buộc `ACCEPTED_COLLECTION_ONLY_NOT_GATE_PASS`, ba child results/owned receipts, source trước–sau,0bodies và Job0. ROOT kiểm timer/resource/postwrite markers trước khi dùng tiếp. Collection accepted không tự cho phép full dispatch.

### 3. Reuse genuine full-Gate packet preparer

Chỉ sau collection accepted và ROOT review full population/import/body work. Dùng schema2 report hiện có như candidate. Helper sau ghim actual report path, ROOT packet SHA sẽ ghim bytes. Không đổi report hoặc fabricate runtime mới.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/prepare_windows_current_gate_packet04.py --worker-sha256 b59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374 --outer-sha256 4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e --runtime-report D:/Dev/KLTN/artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json --collection-result D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate-collection12-outer/final.json --collection-result-sha256 <ACTUAL_ACCEPTED_COLLECTION_FINAL_SHA> --collection-input D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_collection07_packet.ROOT.json --collection-input-sha256 <ACTUAL_FROZEN_PACKET_SHA> --output D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_packet06.ROOT.json --root-review-reference <ROOT_ACCEPTED_COLLECTION_AND_FULL_SUITE_REVIEW>
```

### 4. Full dispatch riêng sau review

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_outer03.py --packet D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_packet06.ROOT.json --packet-sha256 <ACTUAL_FULL_PACKET_SHA> --worker-sha256 b59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374 --outer-sha256 4722088dadf1dc3e45203bb29c242e22d5d54bd66b4141f46b2ab8df28f64f3e --run-id win-current-gate-20261110-06 --approval-reference <ROOT_FULL_GATE_REVIEW_REFERENCE>
```

Không chạy full command khi chỉ mới có source snapshot hoặc khi collection không accepted. Không thêm `--publish-current`. Kết quả report/log/JUnit mới chỉ được lập index riêng sau actual outer accepted và public reader/preflight validation. Không đổi old report/index/pointer.

## Genuine preflight và runtime reuse

`windows_current_gate_outer03.py` dòng117–123 và đoạn try sau dòng140 gọi actual `authorization.preflight(AKTConfig(), project_root=ROOT, runtime_report_path=<packet runtime>, lock_file=<packet lock>)` trước native CLI. Nó thực hiện original upstream validation và runtime/lock matching, không yêu cầu Gate cũ để chạy Gate mới. Refresh writer còn verify upstream trước/sau full suite. Không sửa validator, origin, Git filters hoặc normalizer.

Candidate runtime schema2 SHA3fdddca8d9a39cf80e597cb6dd02701a3c619d64fc0f7ddadb1b6fb885ecd20b đã rehash, basename có177 nhưng không chứng minh source map177 hiện hành. Report này ghim runtime/upstream/lock/interpreter/device. Chỉ genuine preflight thành công mới xác minh reuse phù hợp. Nếu không khớp, giữ failure và xin ROOT review actual `scripts/akt/check_runtime.py` mới, không chỉnh bytes report cũ. Windows EOL proof a0307845fbd04ff1b7e52dea821ed9159462005876c4facfdd18be62c40ca6fd và lock3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a đã rehash. Giữ exact reviewed process Git config và cleanup/env restoration của existing wrapper.

Current cold299/native18, GKT model/trainer/checkpoint acceptance là bằng chứng riêng. Chúng không thay full Gate, không cấp actual selected training, không mở Junyi Task14/Holdout/CV/cloud. Chưa tuyên bố current Gate hoặc GRAPH29 public parity đạt.
