# Sửa fixture nền tảng cho ba lỗi Colab ngày 07/11/2026

Đây là kiểm kỹ thuật synthetic, không phải kết quả nghiên cứu hay benchmark. Phạm vi chỉ gồm `tests/akt/test_runner.py` và `tests/akt/test_runtime.py`; không sửa runner/runtime production, validator, dependency, dữ liệu hoặc artifact BKT. Không chạy GPU, cloud, realdata, Holdout, Development benchmark hay full Gate2.

## Nguồn và nguyên nhân

Nguồn actual Colab: [log CPU](../runs/colab-mcp-preflight-20261107-01/colab-cpu-tests.log), [JUnit](../runs/colab-mcp-preflight-20261107-01/colab-cpu-tests.xml) và [diagnostic JSON](../runs/colab-mcp-preflight-20261107-01/cpu-portability-failure-20261107.json). Run lịch sử có 450 cases: 435 pass, 7 failures, 8 errors; log có thêm 2 deselected. Ba failures trong phạm vi này là:

| Test cũ | Nguyên nhân đối chiếu production |
|---|---|
| `test_json_writer_retries_a_transient_windows_replace_denial` | Fixture phát sinh `winerror=5` nhưng không giả lập `runner.os.name='nt'`. Linux đúng chính sách không retry, nên lỗi được truyền ngay. |
| `test_json_writer_propagates_persistent_denial_and_cleans_temp` | Cùng thiếu điều kiện Windows; Linux gọi replace một lần, trong khi assertion mong năm lần theo chính sách Windows. |
| `test_lock_accepts_percent_encoded_wheel_name` | Fixture dùng wheel `cp313-cp313-win_amd64`, nhưng `write_lock_from_report` lấy compatible tags từ môi trường Linux thực. Validator đúng chính sách từ chối wheel không tương thích. |

Nguồn chính sách: [_write_json](../../src/knowledge_tracing/akt/runner.py) chỉ retry trên Windows, với `winerror` thuộc `{5,32,33}` và bốn delays `(0.05,0.1,0.2,0.4)`; [write_lock_from_report](../../scripts/akt/check_runtime.py) giải mã tên wheel bằng `unquote`, kiểm name/version/tags/SHA-256, host và direct requirements.

## Thay đổi và điều được chứng minh

- Test JSON thay riêng tham chiếu `runner.os` bằng `SimpleNamespace` có platform giả lập và các hàm `getpid`, `fsync`, `replace`. Không sửa `os.name` toàn cục, nên pathlib và pytest vẫn dùng host thật. File tạm, fsync, cleanup và replace thành công vẫn sử dụng filesystem thật trong vùng test.
- Mỗi lỗi Windows `5`, `32`, `33` có transient case: hai lần replace, sleep đúng `0.05`, JSON mới được ghi và không còn temp. Persistent case: năm lần replace, đủ bốn delays, lỗi đúng mã được truyền, JSON cũ còn nguyên, không còn temp.
- POSIX với `winerror` absent hoặc `5/32/33` chỉ replace một lần và không sleep. Windows với `winerror` absent hoặc `87` cũng không retry. Mọi nhánh này giữ nguyên đối tượng lỗi, JSON cũ và cleanup temp.
- Test wheel giả lập `pip._vendor.packaging.tags.sys_tags` bằng `Tag` cụ thể: encoded wheel được nhận khi compatible Windows hoặc Linux. Assertion kiểm chính xác cả URL còn `%2B` và hash trong lock. Cặp Windows wheel/Linux runtime và Linux wheel/Windows runtime vẫn bị validator chặn trước khi tạo lock.
- Không thêm skip/xfail hay loại failure để coi suite đã đạt. Kiểm phụ cận vẫn xác nhận hash, URL, host, direct requirement và output-path guard.

Ba node IDs lỗi lịch sử nay mở rộng thành 8 cases; thêm 8 cases ranh giới (6 JSON và 2 incompatible-wheel). Tổng số cases tăng 13 so với nguồn cũ. Bộ targeted còn gồm atomic-write và 4 test lock/CLI phụ cận, thành 21 cases.

## Thực thi local và bằng chứng

Máy thực: Windows 11 build `26200`, Python `3.13.5`, pip `25.1.1`, interpreter duy nhất `.venv/Scripts/python.exe`. Mọi lượt dưới 120 giây. Output dùng thư mục mới, không ghi đè lịch sử.

| Lượt | Kết quả thực | Log / JUnit |
|---|---|---|
| `parallel-platform-20261107-01` | Exit 2; collection error `ModuleNotFoundError: knowledge_tracing`; 5 deselected, không có pass. Thiếu `PYTHONPATH=src`, chưa phải lỗi fixture. Giữ nguyên evidence. | [log](../../artifacts/akt/local-tests/parallel-platform-20261107-01/pytest.log), [JUnit](../../artifacts/akt/local-tests/parallel-platform-20261107-01/pytest.xml) |
| `parallel-platform-20261107-02` | Exit 0; 21 passed, 29 deselected trong 25.71s. Filter targeted `json_writer or lock_` chỉ chọn phạm vi được giao và test phụ cận. | [log](../../artifacts/akt/local-tests/parallel-platform-20261107-02/pytest.log), [JUnit](../../artifacts/akt/local-tests/parallel-platform-20261107-02/pytest.xml) |
| `parallel-platform-20261107-03` | Exit 0; 21 passed trong 8.35s; JUnit: 21 tests, 0 failures, 0 errors, 0 skipped. Chọn 10 node IDs tường minh, không deselect. | [log](../../artifacts/akt/local-tests/parallel-platform-20261107-03/pytest.log), [JUnit](../../artifacts/akt/local-tests/parallel-platform-20261107-03/pytest.xml) |

Lượt 01 dùng lệnh pytest như lượt 02 bên dưới nhưng chưa đặt `PYTHONPATH`, cùng output/basetemp ở `parallel-platform-20261107-01`. Lượt 02:

```powershell
$env:PYTHONPATH = 'src'
& .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=artifacts/akt/local-tests/parallel-platform-20261107-02/pytest-temp --junitxml=artifacts/akt/local-tests/parallel-platform-20261107-02/pytest.xml tests/akt/test_runner.py tests/akt/test_runtime.py -k 'json_writer or lock_' *> artifacts/akt/local-tests/parallel-platform-20261107-02/pytest.log
```

Lệnh xác nhận cuối (03), chạy từ repository root:

```powershell
$env:PYTHONPATH = 'src'
& .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=artifacts/akt/local-tests/parallel-platform-20261107-03/pytest-temp --junitxml=artifacts/akt/local-tests/parallel-platform-20261107-03/pytest.xml tests/akt/test_runner.py::test_json_writer_atomically_replaces_existing_json tests/akt/test_runner.py::test_json_writer_retries_a_transient_windows_replace_denial tests/akt/test_runner.py::test_json_writer_propagates_persistent_denial_and_cleans_temp tests/akt/test_runner.py::test_json_writer_does_not_retry_non_transient_replace_denial tests/akt/test_runtime.py::test_lock_report_requires_wheel_hashes_and_exact_urls tests/akt/test_runtime.py::test_lock_accepts_percent_encoded_wheel_name tests/akt/test_runtime.py::test_lock_rejects_percent_encoded_wheel_for_incompatible_platform tests/akt/test_runtime.py::test_lock_rejects_untrusted_wheel_host tests/akt/test_runtime.py::test_lock_rejects_report_missing_direct_requirement tests/akt/test_runtime.py::test_cli_writes_only_to_approved_lock_path *> artifacts/akt/local-tests/parallel-platform-20261107-03/pytest.log
```

`git diff --check -- tests/akt/test_runner.py tests/akt/test_runtime.py` exit 0; chỉ cảnh báo Git có thể chuyển LF sang CRLF.

## SHA-256 tại lúc kiểm tra

Inventory trước khi archive/copy; parent cần đối chiếu lại sau archive. Không chuyển artifact trong tiểu tác vụ này.

| File | SHA-256 |
|---|---|
| `tests/akt/test_runner.py` | `a2523287d0576b648139c6a4d589b3e80b773404bae6824c2b34752fdccc0386` |
| `tests/akt/test_runtime.py` | `5df59d195bc2f895451488a2d41cba6a77a4f834e801e4a2b970fc2a0c9fec3a` |
| `src/knowledge_tracing/akt/runner.py` | `af139ee7a48e3100108d5177e4145a2056745d51ea8b95ce618639b8f561cc4f` |
| `scripts/akt/check_runtime.py` | `53d99fdb19163f7f37b7f98d9d2bd1a86273a2fdc1db52ce3742de34f84a7b00` |
| `parallel-platform-20261107-01/pytest.log` | `e952f5d65a87481cdcffef8aaf6f05827f21571c07b4e07befb89e85497b93ba` |
| `parallel-platform-20261107-01/pytest.xml` | `dfc785839e33f0884f6ecd6e8d93bc1b38222596973714655c970fa2bd9a746f` |
| `parallel-platform-20261107-02/pytest.log` | `d343c4e18d9a35982424c68d09958f26af044429330b7382312155865fb40acf` |
| `parallel-platform-20261107-02/pytest.xml` | `ec4a8e173cea522b9b4a80cf276ad9de41476cf0f98015615552f93b3d69afb7` |
| `parallel-platform-20261107-03/pytest.log` | `fe270c374e7e34967cc982431ef06b2354be069acd10444616d8b5706f888acb` |
| `parallel-platform-20261107-03/pytest.xml` | `bf46fa2301a003676fbfe95decdd09560c5e7bd9d6ddf539e0a27c4bcbe2ca67` |

Các đường dẫn `parallel-platform-*` trong bảng SHA nằm dưới `artifacts/akt/local-tests/`.

## Giới hạn và việc tích hợp còn lại

21 pass local Windows với platform/tags giả lập **không chứng minh actual Linux hoặc Colab đã pass**. Cần parent tích hợp thay đổi DuckDB, đóng gói kit nguồn mới và chạy lại CPU suite trên Colab; không được đổi trạng thái thất bại của run lịch sử. Không giả lập kernel/filesystem Windows/Linux hoàn chỉnh; chỉ kiểm đúng các đầu vào platform policy mà production đang sử dụng. Native sharing denial được fault-inject bằng `PermissionError`, không tạo tiến trình bên ngoài khóa file.

Mười hai lỗi DuckDB thuộc phạm vi agent khác; không có kết luận đã sửa trong báo cáo này. Full Gate2, Colab CPU rerun và mọi GPU/model run đều chưa chạy ở tiểu tác vụ này. Parent chịu trách nhiệm mục lục báo cáo, run bundle/manifest tổng hợp và Git; tiểu tác vụ không add/commit/push.
