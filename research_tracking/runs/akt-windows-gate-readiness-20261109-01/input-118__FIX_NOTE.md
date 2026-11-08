# Rút riêng scratch ancestor của Gate, chưa kiểm thực thi

FullGate02 ROOT terminalRC1/291.5909478s/630; all1418executed,1415PASS+3FAIL,
0ERROR/0SKIP. Owned cleanupJob0, source154 trước/sau không đổi. Giữ nguyên raw.

`path_evidence.json` được rút trực tiếp từ JUnit còn nguyên SHA
890ec25fc74b59928bd1041501a15d21137b117241bf52f4f662cdd16910e234.
Hai CLIrecovery fail ở COPY path262chars; pilotcompleted264chars. `.pending`
parents211/211/213chars tồn tại khi kiểm metadata bằng PowerShell/.NET; filename
chưa tồn tại. Sourceprediction.py149/227 gọi Python mkdir trướcCOPY162 và
traceback đã tớiCOPY, không cùng bug thiếu UUID parent trước đây. Không có
livePython/DuckDB probe mới; native error không tự chứng minh thresholdMAX_PATH.

Đổi scratch từ gate2-<runid>-<uuid32> thành gate2-<uuid32>, giữ exclusive root và
3group names. Actual runid28chars gây thêm29chars, bỏ ancestor này cho các path
giả định233/233/235chars. Đây là giảm path inflation không cần thiết của Gate;
chưa chứng minh actual DuckDBexport sẽ pass. Không đổi prediction.py/serialization,
actualproject behaviour, publicCLIrunID/report/log/XML names hoặc targetcoverage.
Không thu nhỏ riêng recovery/pilot fixtures để che điều kiện Gate hiện hành.

Snapshot trước thay đổi nguyên byte: refresh8cd02e93250301f3c2e0e35b98ca495a4a79faebe237edbd837d923df3a93dcc;
test e3911ec7a6cf0cf7dfd87159aa1861a21e18b80fef42044a5b4d09aa1d26e108.
`before.json` ghi SHA trước copy, nguồn và snapshot được rehash so khớp sau copy.

Mở rộng đúng regression TempPathFactory hiện có, không thêm/deselect test:
runID hợp lệ80chars, scratchprefix phải gate2-+32hex (38chars) bất kể runID;
report/log/XML vẫn giữ fullrunID; realTempPathFactory/3physicalgroups/payload
readback và marker các nhóm trước còn nguyên. Trước API có quyền rm_rf vẫn
kiểm abs/ownedfakeproject/absentbase, không đụng oldscratch hoặc artifacthistorical.

Agent chưa chạy AST/tests/native/Git. ROOT review/sourcepins rồi chuẩn bị bounded
focusedmodule77, newsourcefreeze+newcollection trước fullGate mới. Current
focuseddriver01/collection08/fullGate02 packet giữ nguyên, sourcepins đã stale;
không sửa raw hoặc tự chạy lại/tăngcaps. Chưa có PASS cho fixlayout.
