# GKT normal-entry03 — apply source có kiểm và test dự kiến

09/11/2026. Chưa áp canonical, import/compile/test hoặc Git trong lượt agent chuẩn bị này. Root đã cho phép thêm lazy package initializer để normal import data không kéo Torch. Không đổi core/config/numerical recipe hoặc engineering caps.

## Ba payload và helper

| Payload dưới P | Target canonical | SHA |
|---|---|---|
| gkt_research_data_candidate01.py | src/knowledge_tracing/gkt/research_data.py |1650509a3e0baaf91504355e67d4c1857ac2e020071d8f7463ea53887ac65873|
| gkt_research_data_canonical_test03_final.py | tests/gkt/test_research_data.py |e426e42e82c34319ed04214c2248656b08c94e60eaf52579188a22650de41b89|
| gkt_research_package_init03.py | src/knowledge_tracing/gkt/__init__.py |80fd45e6176831f00be7496b1549d3a98485d6b1addd26113130e3c1fcd7fd3f|

Helper `apply_gkt_research_data03.py` SHA `d04071c61064f5b7974ed623247f43de0eabab3751058f5e1581fc740a15ea45`. Default dry kiểm payload bytes/syntax, source targets chưa có, old initializer90c9 và core/config không đổi. Không execute source body. `--apply` tạo P/gkt-research-data-apply03 độc quyền, ghi inventory trước copy, snapshot raw initializer/readback rồi ghi đúng ba targets; receipt afterSHA, giữ failure/partial nếu có. Không auto overwrite hai file mới/retry/rollback hoặc sửa old artifacts.

Initializer giữ config eagerly, đúng danh sách7exports cũ,5core exports qua __getattr__ và cache sau lookup; tên không public raises AttributeError. Normal kernel caller vẫn nhận cùng actual core functions/classes khi sử dụng. Không fake package hoặc sys.modules để bypass Torch khi import data.

Test payload normal import `knowledge_tracing.gkt.research_data`, classGKTResearchDataTests.17data methods giữ logic của candidate02. Ba methods mới kiểm exact __all__/config identity, unknown name, lazy cache với explicit temporary stub core. Stub được restore cùng package attrs/sys.modules, chỉ unit dispatch proof, không native kernel proof. Payload17-case cũ86473903 vẫn giữ dưới P để truy vết trước bổ sung3cases.

## Wrapper và packet03

`run_gkt_research_data_normal03.py` SHA `57389885199cdb33cd440323d14799947feef3daaff5e2ec63a34bf8998a6efe`.
`gkt_research_data_normal03_packet.json` SHA `89ba3b5c4e61f6896061a30e842946ddb9f723a58ff4c7029777a0d2c3276d5d`.

Exact20 expected IDs gồm17data+3package methods, không21 hoặc repeat old17 thành34. Discovery chỉ tests/gkt/test_research_data.py. Candidate logical source key vẫn gkt/research_data.py, runtime lookup là canonical module.29source/history/config pins gồm actual initializer/config/core và canonical payload bytes; allocation chỉ qua sau actual apply khớp exactfuturepins. Không coi prepared targetSHA là đã áp.

Giữ whole30/owned24/worker20/cleanup3; prelaunch2GiB, familyRSS512MiB/free1536MiB, monitor0.1s và check mỗi case; no Torch/model/cloud/process/network/protected corpus/Holdout. NumPy data dependency được cho phép. ActualWinAPI display fixture có restore, no metadata subprocess. Job cleanup/handle/GO/returncode/sourceprepost/currentlogicalsourceidentity vẫn bắt buộc.

## Lịch sử nghiệm thu và giới hạn

Candidate01 actual16PASS/1ERROR,4.383052825927734s/30,Job0. Không sửa receipt hay gán lỗi này cho module data. Candidate02 đã kiểm negative tại genuine public boundary, actual17PASS/0FES, outer stored2.330407900037244s; Root báo terminal2.3605s là scope timing khác. Raw outer42f75a5055fb5f4ee45f67f24a834db507956357a5eb4fb130807c5529ec9ccd, worker5be419689816d4b8622da7a87e1c357a97f8e243d63525b62ae9f6fc090606c6. Normal03 mới có nguồn, chưa kết quả.

Review độc lập605fdc53 giữ nguyên phạm vi. Shared sidecar trường thật `ResearchScoringTarget.trained_item` chỉ nói current-item train support, không bằng GKT full-prefix eligible. Future exporter phải lấy actual input.eligible/support_reason, giữ null/historyunsupported toàn population. Typed fixture có SHA giả không corpus publication/84support/fit attestation.

Root sau review có thể chạy dry, rồi apply, rồi test03 bằng ba lệnh tương ứng. Không tự động nối lệnh để cấp dispatch từ dry result.

`.venv/Scripts/python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/apply_gkt_research_data03.py`

`.venv/Scripts/python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/apply_gkt_research_data03.py --apply`

`.venv/Scripts/python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_gkt_research_data_normal03.py --packet-sha256 89ba3b5c4e61f6896061a30e842946ddb9f723a58ff4c7029777a0d2c3276d5d`
