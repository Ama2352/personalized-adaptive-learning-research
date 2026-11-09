# Rà soát độc lập đề xuất RAM metadata14

Ngày09/11/2026. Chỉ đọc nguồn, SHA và receipt đã có. Chưa tạo controller14, sửa guard, đo RAM mới hoặc chạy Python/import/test/Git.

## Kết luận có điều kiện

Có cơ sở để ROOT chọn profile14 cho đúng workload metadata221ca hiện hành. Đây là hiệu chỉnh chính sách admission và available floor có phiên bản mới. Khác profile12, lần này floor thực sự giảm từ1536MiB xuống1024MiB. Cần ghi quyết định này công khai trong packet/receipt mới, giữ kết quả NO_GO cũ theo giới hạn lúc chạy.

Các fixture đã rà chỉ tạo metadata hữu hạn, fake modules và công cụ giả. Peak worker128MiB vẫn là giới hạn chặt phải kiểm và từ chối khi vượt. Chưa có cơ sở chứng nhận trước rằng mọi nhánh của221PASS nằm dưới128MiB. Với giới hạn đó và các điều kiện bên dưới, không thấy blocker nguồn buộc phải giữ admission1664MiB cho riêng workload này. ROOT vẫn phải xem available RAM thực tại thời điểm launch.

| Đại lượng | Profile12–13 | Đề xuất14 |
|---|---|---|
| Maximum worker RSS/high-water |128MiB =134.217.728B|128MiB =134.217.728B|
| Minimum available tại hooks |1536MiB =1.610.612.736B|1024MiB =1.073.741.824B|
| Prelaunch admission |1664MiB =1.744.830.464B|1280MiB =1.342.177.280B|

Admission14 gồm floor1024MiB, reserve worker128MiB và margin128MiB cho phần phát sinh launcher/metadata. Margin cuối là lựa chọn chính sách thận trọng cho lượt kiểm này, chưa có phép đo tổng process family xác nhận nó đủ trong mọi tình huống. Outer đã tồn tại tại lúc lấy available snapshot. Những ứng dụng khác vẫn có thể làm available giảm sau admission.

Receipt tests13 có available1.646.731.264B, hơn ngưỡng đề xuất304.553.984B, tức hơn256MiB. ROOT thông báo current available1.717.841.920B, hơn ngưỡng375.664.640B. Đây là đối chiếu số đã được cung cấp và receipt cũ, chưa phải RAM admission mới của lượt14.

## Bốn file và giới hạn cấp phát từ nguồn

Population từ `batchc_metadata13_packet.json` là88+67+57+9=221ordered physical IDs. Đúng một node `tests/akt/test_runtime.py::test_native_akt_import_cpu` bị loại. Những con số dưới đây mô tả cấu trúc fixture, chưa phải upper bound byte toàn interpreter/Pytest.

| File và số ID | Cấp phát thực đã thấy | Giới hạn và điểm cần giữ |
|---|---|---|
|`test_research_execution.py`,88|`files()` lines84–170 tạo84dict item cho28concepts×3difficulty, plan10development+1final, ba manifest và ba role byte strings ngắn. Role population8/1/1 và3events/learner nằm trong metadata. Một protocol được sao chép từ nguồn đã ghim. JSON, hash và authorization nhỏ được tạo lại mỗi fixture.|Không gọi collector hoặc giải mã actual corpus. Literal2GiB RSS,8MiB checkpoint và4MiB dữ liệu là caps trong dataclass. Ba role files cố ý chứa chuỗi fixture không phải ObservableTrajectory. Không có mảng theo các caps đó.|
|`test_runtime.py`,67|`isolated_runtime_fixture()` lines184–215 tạo hai `ModuleType` cho Torch/NumPy, một source text ngắn, lock text và runtime dict. Các lock cases dùng một hoặc vài install entries/URLs. Fixture CUDA chỉ sửa report/profile metadata.|`torch.device` và availability ở đây là callable giả. Node import native thật được loại chính xác. Public packaging có thể import để kiểm tag/lock, vẫn cần nằm trong footprint thực của process. Giữ guard actual scientific imports.|
|`test_research_main_execution.py`,57|`make_case()` lines108–129 tạo typed spec, context/limits JSON, graph input rỗng và hashes64ký tự. Auth cases ghi JSON fixture. `linux_gate_metadata()` lines308–321 ghi writer text và report giả nhỏ.|Read limits1/4MiB, checkpoint8MiB, output64MiB và profile128/256MiB chỉ là giá trị metadata. `_metadata`, `_corpus`, native evidence được stub tại các cases cần dữ liệu. Không có nhánh được phép mở actual corpus hoặc tạo backend.|
|`test_research_selected_runner.py`,9|Epoch fake dùng hai target slots và một entry string. Prediction fake có một window2positions, một OOV và3truth rows. Save fake chỉ tạo thư mục trống. Constructor tests tạo tối đa hai container/tuple nhỏ; boundary dùng đúng hai sample dict.|`tools.np`, `tools.pd`, `tools.torch`, Adam và graph adapter đều là `SimpleNamespace`/callable giả. Không tensor, dataframe thực, weights hay optimizer state thực. Các ledger/calls lists tăng theo số lời gọi hữu hạn trong từng case.|

Rà bốn file không thấy allocation kiểu `bytearray`, vòng lặp theo số MiB/GiB hoặc monkeypatch trực tiếp `psutil.Process`, `psutil.virtual_memory`, `memory_info`. Điều này hỗ trợ chọn profile thử nghiệm128MiB, chưa thiết lập worst-case byte bound của assertion rewriting, import packaging, JSON, traceback và toàn bộ221cases trong một interpreter. Pytest có thể giữ reports giữa các case; tmp directories tồn tại trên đĩa không đồng nghĩa giữ mọi object trong RAM.

## Monkeypatch và độ tin cậy phép đo

- `test_research_execution.py` lines201/353/418 thay `Path.open`, lines312/417/424 thay alias predicates, lines342–344 thay `time.monotonic`/`time.time`. Worker13 đã giữ ba callable clock trước test, `PATH_OPEN` trước fixture và dùng nó cho event/hash/log. Cách này xử lý xung đột logging đã quan sát07. Giữ final `Path.open is PATH_OPEN` và khôi phục sys/env bắt buộc.
- `test_runtime.py` lines148–169 thay actual `sys.prefix`, `sys.executable`, `dont_write_bytecode`; lines192–210 thay module-local sys và fake modules; các CLI cases thay `sys.argv`. Worker cần tiếp tục kiểm exact sys tuple sau pytest và cold scientific modules sau teardown. Chỉ kiểm source SHA không đủ cho phần này.
- `test_research_main_execution.py` thay `_resource` ở một negative case line204, `_hash_file`/`_corpus`/native evidence ở các metadata cases và module-local `main.sys` cho Linux fixtures. Đây là functions của code được kiểm, không phải resource closure `check()` của worker. Giữ process object của worker và psutil thật riêng. Nguồn hiện tại không sửa psutil hoặc process method đó.
- `test_research_selected_runner.py` thay lazy tools/state/population/BCE bằng fakes và khôi phục Python random trong `finally`. Ledger giả không được dùng như counter NN thực. Các optional Pytest symlink attempts vẫn bị chặn trước OS bằng PermissionError đúng caller/basetemp; thay RAM không thêm quyền tạo link.

## Bằng chứng đo và giới hạn

Tests08 có221protocol entries/221bodies,168PASS/53FAIL/0ERROR/0SKIP,1113samples, peak64.675.840B =61,6796875MiB. Khoảng tới128MiB còn69.541.888B. ROOT đã phân loại53trace là harness NUL/platform metadata failure. Lượt08 vẫn REJECTED và chưa đo footprint các nhánh hoàn tất sau điểm lỗi. Nhánh đạt có thể chạy lâu hơn hoặc cấp phát khác; tracebacks cũng có overhead riêng.

Tests07 chỉ85bodies và peak55.885.824B. Collection12/13 chỉ chứng minh import/collection221IDs,0bodies. Các phép đo GKT khác không được dùng để suy bound cho MainC.

Worker13 lines87–93 lấy `max(memory.rss, memory.peak_wset)` và available tại hooks trước protocol/body, lúc report và sau pytest. Windows high-water có thể phát hiện peak giữa hooks khi tiến trình còn sống và hook sau chạy. Available chỉ được lấy mẫu; vượt RSS có thể đã xảy ra trước khi bị từ chối. Đây là guard cooperative của worker, chưa phải hard OS memory quota, continuous free-RAM monitor hoặc family RSS cap. Owned Job bảo đảm ownership/cleanup, không tự bổ sung memory quota.

## Điều kiện áp dụng14

1. ROOT quyết định profile mới và tạo namespace/controller/packet mới. Cùng runtime11/source36 và221IDs, chỉ đổi own controller hashes khi rename/cập nhật resource fields. Giữ actual collection SHA mới cùng source trước tests, mọi source/runtime pre/post và exact one-node exclusion.
2. Worker và outer cùng kiểm peak≤134.217.728B, minimum available≥1.073.741.824B, samples>0. Admission≥1.342.177.280B kiểm trước owned launch. Packet ghi ba số rõ, không gọi đây là profile12 unchanged.
3. Giữ tests120whole/115owned/110worker, cleanup3s và postreserve5s; collection20/17/13 giữ nguyên. Không thay assertion, population hoặc quyền import/read/write/process/cloud/CUDA. Metadata Windows thật vẫn chỉ chạy bootstrap đã ghim; sau đó subprocess bị cấm.
4. Chỉ chấp nhận exact221JUnit identities,221protocol/body,0failures/errors/skips, pytest RC0, không denied events, sources/runtime ổn định, sys/env/path/module restoration và Job0 cleanup đầy đủ. Collection hoặc một phần PASS chưa đủ nghiệm thu MainC.
5. Peak/floor vượt, timeout hay passing branch dùng quá128MiB phải REJECTED và giữ raw. Không tự tăng cap, retry hoặc bỏ case để đạt. Tài nguyên model/native/checkpoint/Gate/GPU cần profile riêng đã duyệt; review này không cấp quyền chạy các workload đó.

## SHA nguồn đối chiếu

Các path P tương đối với `artifacts/akt/local-tests/akt-research-runner-20261108-01/`.

| Nguồn | SHA-256 |
|---|---|
|`tests/akt/test_research_execution.py`|53827d176cf372181486622ef45b4d1d9f89ef9f67ece0644c965dcec77fb453|
|`tests/akt/test_runtime.py`|780bc3d45b0b36b162a33fd095713c74e7599e601b2ab700b7162a3d241460f1|
|`tests/akt/test_research_main_execution.py`|3a02dc6a873d5a57970992b96b964fc7957a194c6b0445f7ebc33923a1dcb215|
|`tests/akt/test_research_selected_runner.py`|699a33e1ac4a7dc05cb6673940e0eb70f33b7e6a7619103fac28cf411e74a3b4|
|P `check_batchc_metadata13.py`|8169c83ad32e75df4aa4ce5b2b60e11eaff685d829a89b01d103857ab32fa7b0|
|P `run_batchc_metadata13.py`|32d7bc270e596f57db9c0ce1dfc6ce474069979ed842a990ca9ec6b0be2e4d26|
|P `batchc-metadata-tests08/result.json`|2158794a5d6a74dd1461f8d7c05da8dd52133a0f227bbd348600e2aeba46c6a8|
|P `batchc-metadata-tests13-owned/final.json`|f7c0daf984acf0659aa8a0d68ba5f36359389ed512cc72b87f5a117774c95e79|
|P `BATCHC_METADATA_RESOURCE_PROFILE12_REVIEW01.md`|304287c010ba2c6279a702583f71a104c73d40f2f7a6fe412c2d37d1378c2f18|

Các run01–13 và closed manifests tiếp tục giữ nguyên. Đây là review nguồn của một đề xuất vận hành mới, chưa có lượt14 thực chạy.
