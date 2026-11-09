# Rà soát độc lập profile RAM cho metadata12

Ngày09/11/2026. Chỉ đọc nguồn và receipt hiện có; chưa tạo12, sửa guard, đo RAM mới hoặc chạy Python/import/test/Git.

## Kết luận trong phạm vi metadata

ROOT có cơ sở áp dụng đề xuất như một profile tài nguyên metadata riêng, có phiên bản và provenance rõ. Worker cap mới chặt hơn, available floor giữ nguyên, còn admission được tính lại theo reserve worker đã chọn. Điều này phù hợp với workload221physical test IDs dùng fake scientific modules và guard real imports hiện có. Cần giữ đầy đủ điều kiện nghiệm thu bên dưới. Những profile native/checkpoint/full Gate/GPU có workload khác tiếp tục dùng giới hạn đã duyệt riêng.

| Đại lượng | Profile11 | Đề xuất12 |
|---|---|---|
| Maximum worker RSS/peak |512MiB =536.870.912B|128MiB =134.217.728B|
| Minimum available RAM tại hooks |1536MiB =1.610.612.736B|1536MiB =1.610.612.736B|
| Prelaunch admission |2048MiB =2.147.483.648B|1664MiB =1.744.830.464B|

Phép tính admission được khai báo là floor1536MiB cộng reserve worker128MiB, thay reserve512MiB trước đó. Đây là chính sách admission cho một lượt metadata mới. Giữ nguyên kết quả NO_GO trước đó theo profile của từng lượt.

## Cơ sở đo và hạn chế

Receipt08 ghi221protocol entries và221test bodies, peak64.675.840B, tức61,6796875MiB, với1113resource samples. Khoảng từ peak đã quan sát tới128MiB là69.541.888B. Tuy nhiên08 vẫn REJECTED với221JUnit cases/53FAIL/0ERROR/0SKIP. Số đo là bằng chứng footprint của workload thực đã đi qua; nó chưa là chứng nhận footprint của một lượt221PASS. Các nhánh lỗi có thể dừng sớm một phần logic hoặc phát sinh overhead traceback, nên chiều khác biệt bộ nhớ của lượt đạt chưa được đo.

Receipt07 chỉ đi qua85bodies, peak55.885.824B và432samples; giữ phạm vi partial của nó. Lượt11 NO_GO tại available2.140.545.024B dưới admission2GiB, chưa tạo child. Ba receipt cung cấp cơ sở hiệu chỉnh giả thuyết tài nguyên, không cung cấp thêm kết quả kiểm chức năng.

Source11 dùng `max(memory.rss, memory.peak_wset)` nếu Windows cung cấp peak_wset. High-water này có thể ghi nhận peak xảy ra giữa hai hooks khi tiến trình còn sống và hook sau còn chạy. Available RAM chỉ được lấy ở hooks. Guard phát hiện sau allocation tại thời điểm kiểm, chưa phải giới hạn allocator/OS hoặc đo liên tục. Profile đang đo actual worker, chưa phải tổng family của shim/conhost/outer. Available đo trước launch đã bao gồm outer đang tồn tại; reserve128MiB chưa chứng minh đủ mọi overhead child phụ hoặc biến động từ ứng dụng khác. Floor tại hooks vẫn cần từ chối lượt nếu RAM giảm.

Rà nguồn bốn module cho thấy các giá trị1/2GiB resource budget và128/256MiB CUDA profile trong fixtures là metadata được kiểm. Chúng không tự cấp phát lượng RAM/VRAM đó. Các fixtures còn tạo đối tượng JSON, bank/role manifests, source/config identity và các module fake trong vùng owned; import Python, assertion rewriting, log/JUnit và các nhánh hợp lệ mới vẫn có thể đổi footprint. Không tìm thấy monkeypatch trực tiếp `psutil.Process` hoặc `psutil.virtual_memory` trong phạm vi bốn file đã rà. Controller giữ live process object riêng và prebound clocks/Path.open cho logging. Đây vẫn là kiểm nguồn có phạm vi.

## Điều kiện ROOT cần ghim nếu áp dụng

1. Tạo worker/outer/packet12 ở đường dẫn mới. Worker kiểm high-water≤134.217.728B và available≥1.610.612.736B tại đúng các hooks hiện có. Outer cũng kiểm hai số này trong child receipt. Packet resource fields khớp cả hai controller; admission≥1.744.830.464B được ghi vào receipt.
2. Giữ36project source bindings,11runtime anchors, actual221orderedIDs và đúng một node native import đã loại. Recollect12 với source mới trước tests và ghim actual collection SHA; các source/test nguyên gốc, clocks, owned Job, import/IO/native/CUDA guards giữ nguyên.
3. Giữ collection20/17/13s, tests120/115/110s, cleanup3s và outer postreserve5s như allocation đã duyệt. Thay đổi RAM không mở ngân sách research/model hoặc reset lịch sử lượt trước.
4. Mọi peak hoặc floor vi phạm, timeout, partial population, failure/error/skip, source drift hay cleanup lỗi vẫn REJECTED. Nếu128MiB không đủ thì giữ receipt và cần một quyết định profile khác có bằng chứng mới; không tự mở rộng cap hoặc retry.
5. Ghi `COOPERATIVE_WORKER_HOOK_SAMPLES` và giới hạn Windows high-water rõ ràng. Chỉ metadata221ca được xét trong profile này. Các số fixture/test và literal CUDA budget chưa phải bằng chứng CUDA forward/backward, checkpoint device roundtrip hoặc readiness huấn luyện có phí.

## Nguồn đã đối chiếu

Các đường dẫn dưới tương đối với `artifacts/akt/local-tests/akt-research-runner-20261108-01/`.

| Nguồn | SHA-256 |
|---|---|
|batchc-metadata-tests08/result.json|2158794a5d6a74dd1461f8d7c05da8dd52133a0f227bbd348600e2aeba46c6a8|
|batchc-metadata-tests07/result.json|4391595723a426159d5a9a2d6b493c17df6b19035a29f39a970e6908c1bac514|
|batchc-metadata-collection11-owned/final.json|18e6b18c39b69a167e7e1024bb68662c1dabbe81d0ae60b000516c47c8f6b993|
|check_batchc_metadata11.py|24295b4035558f39d51556d62108414558a224200e6b80472f4633f20f054bc5|
|run_batchc_metadata11.py|272592f8d5757549f6af82b1f708b0f5304ca985b2e7cd058330ad0ee0319851|
|batchc_metadata11_packet.json|4580a6c87bc482a98be6fb17517fa3fc4be5c8a7c291ca311215ef1ac25b9ec5|

Các điểm thực thi hiện hành là worker11 lines87–93 và outer11 lines65–68,105–106. Rà fixture chỉ đọc `tests/akt/test_research_execution.py`, `test_runtime.py`, `test_research_main_execution.py`, `test_research_selected_runner.py`. ROOT vẫn là bên quyết định áp dụng và chạy profile mới.
