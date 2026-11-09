# Main CUDA Batch C — collection, harness failures và RAM admission06–10

Ngày09/11/2026. Hồ sơ vận hành tiếp nối bundle01–05đã đóng, giữ các lượt mới riêng. Đã thu được population221metadata test IDs và chạy đủ221test bodies ở lượt08, nhưng kết quả168PASS/53FAIL. Chưa nghiệm thu MainC, native checkpoint hoặc CUDA. Một manifest completed của hồ sơ này chỉ xác nhận lưu bằng chứng, không đổi verdict của các operation.

Vị trí canonical dự kiến `research_tracking/reports/akt_main_batchc_metadata_attempts_06_10_20261109.md`. ROOT công bố bằng bản copy đúng SHA đã review. Báo cáo và archiver này được chuẩn bị source-only, không chạy lại tests, solver, simulator, training hoặc Git.

## Diễn tiến và các đơn vị đếm

| Operation | Điều thực xảy ra | Child stored seconds | Outer stored seconds |
|---|---|---:|---:|
| collection06 | REJECTED,155partial IDs; hai collection errors,0test bodies | 4,401990599988494 | 4,97425590001512 |
| collection07 | ACCEPTED collection221IDs,17new/204prior,0test bodies | 1,740816800040193 | 2,187701200018637 |
| tests07 | REJECTED sau85bodies; JUnit86cases gồm85PASS và1internalerror | 34,391415099962614 | 35,17485970002599 |
| collection08 | ACCEPTED cùng221IDs,0test bodies | 1,7119705000077374 | 2,1511639999807812 |
| tests08 | REJECTED,221bodies/221JUnitcases,168PASS/53FAIL/0error/0skip | 35,905265900015365 | 36,5096584999701 |
| collection09 | NO_GO RAM trước launch, chưa child/Job | Không có | Receipt không lưu elapsed |
| collection10 | ACCEPTED cùng221IDs,0test bodies; warmup platform mới đã được thực gọi | 2,041468999988865 | Xem raw outer, không suy từ child |
| tests10 | NO_GO RAM trước launch, chưa child/Job | Không có | Receipt không lưu elapsed |

Các thời gian ở bảng là scope lưu trong receipt, không cộng các scope lồng nhau. ROOT còn quan sát terminal tests07 là35,188362giây và tests08 là36,517482giây. Hai terminal observations được giữ dưới dạng ghi chú điều phối ở đây, không dựng raw terminal log riêng khi chưa có file như vậy. Collection chỉ lập danh sách test, không được đổi221IDs thành221PASS.155partial IDs của06không là population được nghiệm thu.

## 06 — dependency source chưa nằm trong read contract

Read guard chặn `src/knowledge_tracing/research_selection.py` trong import chain của hai module Main. Đây là đường source thật đã được dùng bởi `research_admission`, không phải test body hoặc model fit. Raw06ghi hai denial cùng target và hai collection errors. Packet06có33project bindings/10runtime bindings. Nguồn07thêm đúng ba project dependencies selection/runner/lifecycle thành36, giữ guard và exact source pins. Collection07đạt population221và deselect đúng một native-import case theo contract metadata.

## 07 — harness Path.open va chạm với negative fixture

Tests07đã chạy85bodies trước khi đi vào negative fixture monkeypatch `Path.open` ở source line418. Harness dùng chính phương thức đang bị patch để phục vụ đường đọc/ghi nội bộ, dẫn tới JUnit internal error và population chưa chạy hết. Raw JUnit86cases/0failures/1error không phải221PASS, cũng không chứng minh85test bodies có production defect. `pytest_exit_code=3` và outer REJECTED được giữ nguyên.

Nguồn08giữ các thao tác I/O cần thiết bằng binding đã chốt trước monkeypatch. Nó còn từ chối optional Pytest current-symlink trong owned temporary area bằng `PermissionError` trước OS call. Đây là từ chối thao tác tạo link, không tạo symlink rồi xóa để lách guard. Assertions và testcase population giữ nguyên.

## 08 — đủ population nhưng53failures cùng đường metadata Windows

Tests08chạy đủ221bodies. JUnit ghi53failures, không error/skip, nên168cases còn lại PASS. ROOT đã đọc cả53trace và xác định cùng first observed failure chain `inspect_runtime → platform.platform → _syscmd_ver → NUL` bị read guard chặn. Raw JUnit được giữ để đối chiếu. Đây là chẩn đoán của ROOT từ traces; nó không tự chứng minh mọi test sẽ đạt sau khi sửa harness, hoặc loại trừ lỗi khác chưa đi tới.

Warmup thực trước đó chỉ gọi `platform.uname` và `platform.processor`. Khi fixture gọi `inspect_runtime`, `platform.platform` còn cần metadata Windows nên đi đến `cmd /c "ver"`/NUL sau metadata phase. Không sửa production runtime inspector hoặc giả phiên bản hệ điều hành. Negative fixtures tiếp tục dùng payload metadata/mock thuộc phạm vi tests, không model thật.

Raw08ghi183optional-symlink attempts bị từ chối trước OS. Danh sách denial chỉ giữ tối đa tám records đầu, nên không dùng độ dài8để nói chỉ tám sự kiện đã xảy ra. `Path.open`, environment và sys state được phục hồi, source36/runtime11trước/sau cùng SHA, scientific modules vắng mặt cuối lượt, owned cleanup đạt/Job active0. Đây vẫn là REJECTED metadata test operation.

## 09 và10 — warmup thật, admission RAM tách từng operation

Nguồn09thêm `platform.platform()` vào cùng phase metadata Windows thật, giữ executable literal `cmd.exe /c "ver"` đã ghim và helper-call ceiling≤3. Phase đóng trước import/test audit; không mở thêm Popen/network sau phase. Không hardcode OS fields hoặc thay `platform.uname` bằng mock. Helper source giữ riêng các định nghĩa khác của file gốc, nhưng worker metadata chỉ gọi entrypoint metadata đã pin.

Collection09NO_GO khi available1.838.166.016B dưới prelaunch cushion2.147.483.648B. Chưa có child, native_metadata, source-after hoặc owned Job receipt cho09. Vì vậy09riêng lẻ chưa kiểm runtime warmup.

Sau một kiểm RAM mới được ROOT chấp thuận, derivative10đổi namespace và chạy collection. Raw `native_metadata.json` của10ghi public APIs uname/processor/platform, hai actual helper cmd-ver calls, hostname không được lưu, phase_closed=true và `platform_cache_after_close_equal=true`. Receipt kiểm helper source09, source36/runtime11không đổi,221IDsgiống07/08,0body, cleanup/Job0. Điều này xác nhận warmup trong collection10, chưa xác nhận full tests với warmup mới.

Admission của tests10là phép kiểm RAM mới riêng. Available2.122.240.000B dưới cùng floor2.147.483.648B nên NO_GO trước launch, không tự retry. Không dùng collection10PASS để gán verdict cho tests10chưa chạy. Không hạ floor hoặc kế thừa Job/source-after của collection10cho tests10.

## Phạm vi tài nguyên và quyền

Worker RSS≤512MiB và cooperative free-RAM floor1536MiB giữ theo các packets. Outer prelaunch cushion2GiB là điều kiện admission riêng. Nguồn07tests dùng cap45giây whole,08/09/10tests dùng120giây whole sau quan sát thời gian của07; trần mới không reset hoặc biến lỗi07thành timeout. Elapsed của các operation cũ được giữ nguyên.

Native metadata có các process hệ thống giới hạn, còn owned launcher tạo child riêng. Không gọi đây là0processes. Body tests ở đây là metadata/mock fixtures, không native neural forward/backward, optimizer hoặc corpus fit. Các receipts giữ đúng scope hook sampling, không tuyên bố hard continuous RSS quota. Current software Gate vẫn stale sau MainC source changes. Actual Linux/CUDA/native checkpoint acceptance và full-producer complete-epoch resume vẫn thiếu.

## Lưu trữ và bước tiếp

Bundle mới dự kiến `akt-main-batchc-metadata-attempts-06-10-20261109-01`, giữ toàn bộ raw files trực tiếp của tám operations, worker/outer/packet06–10, preparer09/10, helper09, report và copy inventories. Không copy runtime-temp/cache trees, dependency bytes, corpus hoặc full production source. Source/runtime identities của từng packet/receipt được xuất làm reference metadata. Source có hash không có nghĩa code nhánh09/10tests đã được chạy.

Bundle01–05manifest SHA `25ca4b701886e188447d6275887d9ed72f26fe5936cafc734dface16f25dff57` giữ nguyên và chỉ được reference. Các Root reviews chuẩn bị hiện tìm thấy được pin theo đúng phạm vi; không tạo một review09hoặc raw terminal transcript mới để lấp hồ sơ. [Hồ sơ cũ](../runs/akt-main-batchc-metadata-attempts-20261109-01/README.md), [hồ sơ06–10](../runs/akt-main-batchc-metadata-attempts-06-10-20261109-01/README.md).

Bước tiếp cần ROOT review current RAM/source/allocation rồi quyết định một tests operation mới riêng. Không có automatic retry từ closure này. Chưa MainC verified, GPU ready, model fitted nghiên cứu hoặc RQ completion.
