# GRAPH29 cold299 — derivative04 source-only

Chỉ chuẩn bị ba files, không Python/import/AST/collection/test/native/Git hoặc canonical edits. Source03 và actual collection/test03 failures giữ nguyên. ROOT actual test03 đã chạy299bodies,298PASS/1FAIL/0error/skip; không299PASS. Sole failure là mock writer không canonicalize Path trước JSON, chưa tới intended history-write OSError. ROOT sửa đúng helper thành put(canonical(payload)); production run.json đã canonicalize.

| File | SHA-256 |
|---|---|
| check_graph29_metadata04.py | b13c6d8f32863c6eb5a535d19c1dc12ea93eadce8efefac511ccebe47e60a832 |
| run_graph29_metadata04.py | 7b4f96deca6338b9a5dc7a9ca11c7cfbf86dc5d7c1fe6493b09fee83bd3d4f62 |
| graph29_metadata04_packet.json | 2241fe727bbc68f8ba94bfe571208b9bc0528137dcf4c2c3a12ecb42d420963d |

Common pin duy nhất đổi là tests/akt/test_research_selected_resume.py, từ7d363fbc… sang `aec0c914c6d96d791b2df916e8a7fcab75a4d54bc4dec6c138d242ec284d30bb`. Hai own script paths/pins đổi03→04. Mọi non-source_pins field của packet04 bằng packet03 khi so toàn giá trị JSON, gồm299ordered IDs,3exact exclusions,38subset, runtime11, resource caps/readonly guards. Actual44source và11runtime SHA khớp. Worker chỉ đổi own packet filename, outer chỉ đổi own worker/packet filenames; không bỏ testcase/assertion hoặc nới guard.

Giữ explicit --attempt hai ASCII digits, không auto chọn namespace/retry/overwrite. Proposed --attempt 04 tạo collection04/tests04, g29c04/g29t04; tất cả ABSENT khi freeze. Tests04 cần external actual collection04 outerSHA và cùng packet/runtime/source, không dùng collection03 sau đổi test pin. Whole collect20/owned17/worker13 và tests120/owned115/worker110/cleanup3, worker128MiB/free1GiB/admit1280MiB giữ nguyên.

ROOT command dùng .venv/Scripts/python.exe -B với run_graph29_metadata04.py, --mode collect --attempt 04, packetSHA2241fe…/workerSHAb13c6d…/controllerSHA7b4f96… và actual approval-reference. Sau actual collection04 review mới --mode tests cùngattempt04 và --collection-sha256 actual04 outerSHA. Không có SHA accepted result giả trong files.

Native07 không sửa theo chỉ thị ROOT. Test pin của nó hiện stale, chưa dispatch và không được dùng như current. Chỉ refresh native dependency sau cold04 actual PASS/source freeze. Metadata04 expected299 không là actual PASS, native/GPU/fit hoặc current Gate authority.

Preserved03 worker aeeaed2f94a5cb3dcbd1dbf6a5b68034ef828b56f0b97eb543e8bc4d4442f97d, outer71c30bbe71eeb2345a29eebf1a5b7e3f1efc25cadfc3b5a6b5ef18bf351c2941, packetfaa0b50a56c071374b30a4fa43ff498131dad15c21d16df9df02192397f8363e. Old candidate02 test7d363… và raw03 failures tiếp tục do ROOT giữ nguyên, không relabel.
