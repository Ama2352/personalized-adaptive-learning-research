# Reader02 — chẩn đoán source, chưa retry

Root actual terminalRC1, toolwall1,5539638s. Giữ nguyên sourcecontroller02 `0caef109…`, stdout81B (chỉ thông báo1collectionerror), stderr0B, JUnit38B chỉ XML declaration và12sourcepins trước=sau khớp. Cumulative charge mới29,56646766238098/90s, gồm28,01250386238098s của trial01UNKNOWN. Không có test counts hợp lệ/receipt02; không gọi0PASS hoặc47PASS.

**Bug controller xác định từ source:** `run_pure02.py` bắt exception của pytest vào biến `error`, nhưng không persist ngay; `finally` gọi `ET.parse` không guard. Với XML38B, ParseError làm mất receipt và trace/code gốc. Không thể suy exception ban đầu từ lỗi XML cuối. Không sửa rawJUnit cũ.

**Giả thuyết collection, chưa xác nhận:** controller thay class `subprocess.Popen` toàn cục bằng function raising trước import NumPy/pandas/pytest. Điều này có thể làm hỏng class/type/import contracts hoặc chặn metadata process. JUnit plugin actual installed `.venv/Lib/site-packages/_pytest/junitxml.py:647–674` ghi XML declaration trước `platform.node()`; Python3.13 `platform.node` đi qua uname/Windows metadata, có fallback `_syscmd_ver` dùng subprocess. Đây chỉ chứng minh path có thể lỗi sau declaration, không xác định collectionerror02 hoặc chứng minh Popen đã được gọi. Không cache/fake platform metadata để làm xanh test.

## Diff nhỏ đề xuất, chờ root review trước execute

Tạo controller03 riêng, không sửa02/reader/test. Giữ same-process `.venv`/Timer55/newcall60/cumulative90. Giữ noTorch/no teacher, fixture handmade. Thay global Popen function bằng audit hook chỉ chặn event `subprocess.Popen` ngay trước launch, giữ nguyên class semantics. Hook ghi operation/caller stack, không argv/env/credentials. Vì hook process-wide không remove, chỉ dùng trong process kiểm thử này.

Hook `pytest_collectreport`/`pytest_internalerror` persist traceback gốc độc quyền khi xảy ra, boundedtext. Persist `pytest_outcome.json` (code hoặc original exception) trước parseXML; parseXML độc lập try/except, giữ XMLerror như receiptfield và vẫn ghi countsnull/FAILED. Sourceposthash/persistence lỗi cũng không được mask traceback gốc. Không sửa pytest/stdlib/pandas source, không mở childprocess nếu audit hook bị gọi. Nếu vẫn fail, giữ lỗi có trace rồi STOP để review, không retry tự động hoặc reset ledger.
