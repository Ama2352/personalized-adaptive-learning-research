# Main CUDA BatchC — nghiệm thu metadata trên Windows

Ngày09/11/2026. Phạm vi là bốn test modules qua entrypoints canonical sau khi ROOT áp dụng bốn production files và bốn test files của BatchC. Lượt15 đã đạt đủ221physical JUnit cases,221protocol entries và221test bodies,0failures/errors/skips. Nguồn37bindings và11runtime anchors giữ nguyên trước/sau; env/sys/Path.open được khôi phục, actual scientific modules không còn trong process, denied events rỗng và owned Job kết thúc0processes/cleanup accepted.

## Diễn tiến và kết quả

| Lượt | Collection | Tests | Phạm vi kết luận |
|---|---|---|---|
|14|Accepted221ordered IDs,0body|220PASS/1FAIL/0ERROR/0SKIP,đủ221bodies|Read guard thiếu đúng readonly `requirements-akt.lock.txt`; lượt vẫn REJECTED.|
|15|Accepted cùng221ordered IDs,0body|221PASS/0FAIL/0ERROR/0SKIP|MainC metadata VERIFIED trong fixture scope đã chạy.|

Lượt14 ghi actual denied path tại `test_probe_does_not_write_bytecode_into_upstream_checkout` → `inspect_runtime` → `sha256_file`. ROOT chuẩn bị namespace15 và thêm đúng lock SHA `3e721fdb49543ad0888cf02a863826ebc6144c0d1dd670f2490ebcc0d69b8c0a` vào readonly source/input bindings. Không đổi production, test assertions, population hoặc guard protected/source writes. Bindings tăng36→37 do đầu vào lock. Hai own controller paths/hashes đổi theo namespace.

Population gồm88cases `test_research_execution.py`,67cases `test_runtime.py`,57cases `test_research_main_execution.py`,9cases `test_research_selected_runner.py`. Giữ đúng một exclusion `tests/akt/test_runtime.py::test_native_akt_import_cpu` cho allocation framework thật riêng. Collection kiểm thứ tự và identities trước khi chạy body; nó không cung cấp test PASS riêng để cộng thêm vào221.

## Tài nguyên và vận hành

ROOT duyệt profile metadata mới worker128MiB, minimum available1024MiB, admission1280MiB. Review độc lập được giữ nguyên SHA `f00431adbb9e66d6ce5af81efdd041805af871918453c18a868db5b632bf43b0`. Đây là quyết định hiệu chỉnh workload metadata có phiên bản. Các verdict cũ và giới hạn native/model/GPU giữ theo hồ sơ từng lượt.

| Đại lượng | Tests14 | Tests15 |
|---|---|---|
|Worker elapsed|19,826694299990777s|29,959714199998416s|
|Stored outer elapsed|20,321745999972336s|30,586347200034652s|
|Observed peak worker RSS/high-water|59.785.216B|55.996.416B|
|Observed minimum available|1.671.376.896B|1.374.326.784B|
|Resource samples|1115|1116|

ROOT terminal15 là30,5950877s, khác mốc stored outer do ranh giới đo. Tests dùng whole120s/owned115s/worker110s/cleanup3s/postreserve5s. Collection dùng20/17/13s/cleanup3s. Worker hook samples và Windows high-water là kiểm cooperative, chưa là hard OS/family memory quota. Lượt15 chặn183optional Pytest current-symlink attempts trước khi OS tạo link. Fixture aliases vẫn được kiểm bằng monkeypatch; hồ sơ không nhận các symlink bị chặn là links thực đã tạo.

Metadata Windows dùng helper đã ghim với lệnh hệ thống giới hạn và raw receipt riêng. Các Torch/NumPy/CUDA/Adam trong fixture là modules hoặc callable giả. Actual Torch/NumPy/Pandas imports, subprocess sau bootstrap, network/cloud và dữ liệu bảo vệ bị guard chặn. Không có forward/backward, optimizer hoặc workload mô hình/CUDA trong các lượt này.

## Nguồn và hồ sơ được giữ

Actual accepted outer15 nằm tại `artifacts/akt/local-tests/akt-research-runner-20261108-01/batchc-metadata-tests15-owned/final.json`, SHA `de4415589065d635396fd23e711a3891233af37534249ec22dc521b40c79b836`. Child result SHA `18e89106598a1d0c4ea8e6ca8156d5f16e19ad9e2fb5f20266ef94c83282469c`. Failed outer14 SHA `7684ad3f4e87c3c561323d5b902f9af7628a8839439fb141eded595599e9c913` và child SHA `0ed5d06227b763ffb6c5cbf9136baec89556d0ba2a208c3ce24d7bee782bac15` vẫn giữ nguyên.

Bundle dự kiến `akt-main-cuda-metadata-engineering-20261109-01` giữ toàn bộ raw flat của collection/tests14–15, sáu controller/packet, hai ROOT preparers, review resource, ROOT apply review/receipt, ba inventories candidate/before-copy và tám source/test snapshots canonical đúng byte đã kiểm. Source/runtime khác được tham chiếu bằng SHA từ packets/receipts, không sao chép dependencies, cache, corpus, dataset hoặc checkpoints. Inventory được ghim trước copy và kiểm lại source/copy/source-after. Báo cáo này là candidate chờ ROOT dry-review/closure, chưa có manifest closure mới tại lúc viết.

Các bundle01–05,06–10,11–13 được tham chiếu manifest lần lượt `25ca4b701886e188447d6275887d9ed72f26fe5936cafc734dface16f25dff57`, `412da03714d2381745b75082c0abda41a7dc1b48503119ac7f367b2391a9594d`, `a7cc60d85b1acd851c6a73f3d5155cfc8ec92eb618ff629ade4d644b52d20cb1`. Không sửa, gộp verdict hoặc sao chép lại các bundles đó.

## Phần còn thiếu

Nghiệm thu này xác nhận metadata contract và CPU wire compatibility trong fixtures đã chọn. Hồi quy native CPU checkpoint BatchB trên current source chưa được xác nhận; packet04 cũ chưa chạy và đã stale. Current software Gate chưa được refresh cho batch mới. Linux/CUDA runtime, CUDA forward/backward/Adam/checkpoint roundtrip và GPU execution chưa được kiểm trong hồ sơ này. Full producer resume vẫn là gap riêng đã ghi nhận. Các kết quả221ca không tạo execution grant, selected fit, refit/calibration authority hoặc kết luận RQ mới.
