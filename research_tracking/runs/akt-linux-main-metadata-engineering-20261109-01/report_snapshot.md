# Linux CPU provenance của Main và profile môi trường trong Gate

Ngày09/11/2026. Đây là kiểm kỹ thuật metadata/tmpFS chạy trên **Windows**, chuẩn bị nhánh Linux CPU. Chưa chạy Main, Git provenance, runtime hoặc software Gate mới trên Linux trong gói này.

## Thay đổi đã kiểm

Bốn file production/test của batch được giữ trong bundle. `MainLinuxGitProfile` tách khỏi profile Windows, yêu cầu actual physical Git binary/SHA, process environment đóng, source proof đã pin, ba raw-LF source hashes, runtime/lock và original public validators. Nhánh Windows giữ class, environment và các kiểm tra EOL hiện hành. `authorization.py` và `provenance.py` không sửa.

Gate writer thêm `execution_profile` gồm đúng sáu trường `schema_version`, `platform_id`, `project_root`, `python`, `python_prefix`, `writer_sha256`, lấy từ tiến trình writer. Writer phải thuộc current build map. Sau genuine public Gate reader, nhánh Main Linux đọc lại đúng report đã bind SHA và kiểm profile khớp actual Linux process/runtime/root/interpreter cùng current writer/build. Report thiếu profile hoặc mang profile Windows bị nhánh Linux từ chối. Public reader Windows vẫn hỗ trợ report lịch sử theo schema cũ.

Các LF hashes trong code là expected CRLF→LF tính read-only từ ba source bytes Windows đã pin. Chúng chưa là quan sát source trên Linux. Source proof Linux thực tế chưa được tạo trong gói này.

## Hai lượt ROOT đã chạy

| Lượt | Tests vật lý | PASS | FAIL | ERROR/SKIP | Thời gian wrapper lưu | Cap |
|---|---:|---:|---:|---:|---:|---:|
| 01, REJECTED |154|140|14|0/0|5.927186899993103s|30s|
| 02, ACCEPTED_154_METADATA_REGRESSIONS |154|154|0|0/0|3.710097400005907s|30s|

Cả hai JUnit có cùng154identities duy nhất, gồm51ca `test_research_main_execution` và103ca `test_gate2_refresh`. Các source hashes trước/sau mỗi lượt bằng nhau. Đây là hai lần chạy lại cùng population sau một sửa fixture, không308kiểm tra độc lập hoặc bằng chứng nghiên cứu mới. Hai khoảng wrapper lưu cộng khoảng9.6372843s, không phải thời gian đo CPU hay RSS. Mỗi wrapper khai báo cap30s riêng.

Lượt01 thất bại vì fixture đặt expected `build_hashes` vào dictionary `observed` ngay khi setup. Sáu ca invalid lock, bảy ca missing pure module và một ca empty remaining group đã nhận đúng exception trước child, nhưng assertion `not observed` thấy metadata setup này. Bản sửa chỉ chuyển expected map sang `_fixture_build_hashes` riêng. Các assertion từ chối sớm và pointer-byte equality được giữ nguyên. Hai file production và test Main không đổi giữa01/02. Raw140PASS/14FAIL, old fixture bytes và cả hai wrappers được giữ để đối chiếu.

## Phạm vi của 154ca

Fixtures kiểm class/profile/env metadata, cross-platform/unsafe-path/stale source proof, closed schemas, report reread hash, writer/build/runtime bindings, additive Gate payload và compatibility của legacy public reader. Các test Gate dùng child giả cùng tmpFS; có ca gọi implementation TempPathFactory thật để kiểm nested basetemp. Các positives metadata không tạo `MainSelectedExecution` hoặc xác nhận máy Linux thực tế. Public imports có thể nạp NumPy qua dependencies hiện hành.

Hai wrappers dùng repository `.venv`, pytest child với timeout30s, CUDA hidden, thread2 và pytest plugin autoload disabled. Chúng giữ stdout/stderr/JUnit/result cùng source hashes. Gói này không có owned Job tree-empty receipt, polling RAM/VRAM, peak-RSS measurements hoặc profiler toàn process để chứng nhận các số đếm model/optimizer bằng0. Không suy các loại bằng chứng đó từ154PASS hoặc từ thư mục tên Linux.

## Bằng chứng và phiên bản nguồn

Bundle dự kiến `akt-linux-main-metadata-engineering-20261109-01` giữ các raw text nhỏ, hai wrappers, bốn source cuối, bốn bản trước implementation, old fixture đã chạy01, hai inventory và first-source handoff. Các bản snapshot lặp lại byte-identical được tham chiếu bằng SHA thay vì copy nhiều lần. Inventory closure kiểm SHA trước copy, bản copy và source sau copy. Không đưa pytest-temp, runtime/dependency bytes, corpus hoặc outputs không liên quan vào bundle.

Final source pins được ghi đầy đủ trong `copy_inventory.json` và manifest. Các tiền tố để nhận diện nhanh gồm Main73bbacc8, testMainf7ed9b4d, Gate writered87ee74, testGate9c345614. Bản Gate fixture chạy01 là8f15c3d4. Plan02 được duyệt làd256e5d6; snapshot inventory trước implementation làc33c8a49 và trước fixture fix là89060211.

## Giới hạn còn lại

Actual Linux source proof, Git binary/checkout, schema2 CPU runtime, current-source Linux Gate, ROOT-owned authorization và dispatch vẫn cần được tạo/kiểm trên máy đích. Chưa có CUDA NN/checkpoint, full selected fit, calibration/refit hoặc quyền chi cloud trong gói này. Gate05 lịch sử giữ nguyên nhưng không attests bốn source bytes mới; source binding hiện tại làm Gate đó stale cho batch mới. Cần refresh software Gate ở batch đóng băng sau, không đổi nhãn hoặc sửa bằng chứng Gate05.

Report này được chuẩn bị sau actual02. Trạng thái đóng bundle chỉ được xác nhận bởi manifest do ROOT tạo sau dry review, không bởi nội dung draft này.
