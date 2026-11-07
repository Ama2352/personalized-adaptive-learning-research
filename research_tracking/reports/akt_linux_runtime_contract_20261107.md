# AKT: contract runtime Windows/Linux — kiểm kỹ thuật CPU

Đợt GPU06 ngày 07–08/11/2026; tên file giữ run date 20261107. Kết quả phạm vi này: executable/prefix và runtime report được bind theo Windows/Linux, **63 targeted tests pass**. Đây là contract/preflight engineering; chưa provision Linux/CUDA, chưa full Linux worker, không chạy model training, GPU, cloud, realdata, Holdout hoặc Development benchmark.

## Nguồn và phạm vi thay đổi

Đối chiếu `scripts/akt/check_runtime.py`, `src/knowledge_tracing/akt/authorization.py`, test runtime/preflight hiện có và [bằng chứng actual Colab](../../artifacts/akt/colab/actual-cuda-verification-20261107.json). Colab trước đó dùng inherited packages và synthetic probe riêng; synthetic PASS không làm origin/lock/main-worker guards tự hợp lệ.

Thay đổi trực tiếp chỉ ở hai source files trên và `tests/akt/test_runtime.py`. `tests/akt/test_authorization.py` không tồn tại; các regression preflight mới nằm trong test runtime. Parent sửa riêng fixture `tests/akt/test_runner.py::test_preflight_verifies_gate1_without_opening_dataset` để bỏ đường dẫn Windows hardcode và emit report schema2. Không đổi config phases, architecture, splits, authorization scopes hoặc guards về dataset/execution caps.

## Contract đã chốt

`validate_runtime_interpreter(environment, *, executable, prefix, platform_id)` dùng entry `.venv/Scripts/python.exe` với `win32`, `.venv/bin/python` với `linux`; platform khác bị từ chối. Actual `sys.executable` phải là absolute lexical entry path đúng venv; actual `sys.prefix` phải resolve về expected venv. Không resolve symlink của executable khi so entry: Linux venv Python có thể trỏ tới binary nền, nhưng chạy thẳng binary nền với prefix/report giả khớp vẫn bị từ chối.

`inspect_runtime` nhận `project_root`, `lock_file` explicit. Default lock lấy theo project_root, không luôn lấy ROOT Windows ban đầu. Report mới có:

| Field | Ràng buộc preflight schema2 |
|---|---|
| `runtime_schema_version` | Integer đúng 2; không nhận bool, float hoặc version khác. |
| `platform_id` | String đúng actual `sys.platform`. |
| `python` | Absolute lexical path đúng expected entry và actual executable đã kiểm. |
| `python_prefix`, `project_root`, `lock_file` | Absolute paths resolve đúng venv/root/lock caller đã chọn. |
| `source`, `lock_sha256` | Đúng pinned source identity và SHA-256 của lock hiện tại; sai kiểu hoặc drift bị từ chối. |
| `torch_origin`, `numpy_origin` | Bắt buộc là absolute paths resolve bên trong venv. Inherited/global origins không được nhận. |
| `device`, `cuda_available` | Report device phải đúng config device; availability phải bool. Config CUDA yêu cầu report availability đúng True. CPU execution mode vẫn hợp lệ trên runtime có CUDA nếu report device='cpu'. |

Probe vẫn đo actual Torch/NumPy origins trong `inspect_runtime`; strict guard này được giữ. Preflight không import Torch/NumPy: nó kiểm recorded origins, runtime/source/lock/report bindings và actual interpreter/prefix. Thay wheel/binary hoặc môi trường sau khi tạo report chưa được khóa bằng image digest trong gói này; không gọi đây là complete runtime attestation.

Windows legacy report không có `runtime_schema_version` vẫn được đọc khi các bindings cũ còn hợp lệ. Recorded origins/device/CUDA flags nếu có vẫn bị kiểm, report legacy Linux/partial schema2 không được chấp nhận. Minimal legacy CPU fixture được giữ tương thích; nó không cấp quyền dùng CPU report cho config CUDA. Linux bắt buộc fresh schema2 report có đủ metadata; không sửa report Windows lịch sử thành report Linux.

CLI thêm `--lock-file <existing-lock>` cho runtime inspection. Output vẫn qua trusted ROOT/output guard, không thêm tùy chọn đổi trusted project root trên CLI. API có thể dùng explicit project_root cho runtime context/fixtures; CLI resolution/write-lock mode và wheel validators giữ nguyên. Không tạo/cài/resolve dependency lock Linux trong đợt này.

## Kiểm thực tế và failures được giữ

Máy chạy thực là Windows với `.venv/Scripts/python.exe`; Linux trong các tests là **module-local sys/metadata fixtures**, không actual Linux execution. Không đổi `os.name` toàn cục. Symlink entry được giả lập bằng resolve của đúng Path, không tạo symlink cần đặc quyền Windows.

| Lượt | Kết quả thực | Nguyên nhân/phạm vi |
|---|---|---|
| `parallel-linux-runtime-20261107-01` | 53 passed, 1 failed; 2.76s, exit 1 | Native CPU import bị Git dubious ownership ở upstream. Không sửa source hoặc global Git config để vượt lỗi. |
| `parallel-linux-runtime-20261107-02` | 62 passed, 1 failed; 11.59s, exit 1 | CLI fixture thay runtime_module.sys nhưng argparse dùng sys.argv thật; fixture bị nhận argv của pytest. Production parser không sai. |
| `parallel-linux-runtime-20261107-03` | **63 passed**, 10.91s, exit 0; 0 failures/errors/skipped/deselected | Chạy toàn bộ test_runtime và parent-owned preflight node. Sửa fixture sys.argv và thêm safe.directory đúng upstream ở environment của riêng process. |

Mỗi lượt dưới 120 giây. [Trial01 log/XML](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-01/pytest.log), [trial01 JUnit](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-01/pytest.xml); [trial02 log](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-02/pytest.log), [trial02 JUnit](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-02/pytest.xml); [final log](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/pytest.log), [final JUnit](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/pytest.xml).

Các kiểm mới phủ: Windows/Linux executable và prefix, custom root/lock, strict schema types, stale actual source/lock, unsupported platform, device/availability, legacy compatibility, inherited Torch/NumPy từ chối ở cả inspect/preflight, CLI explicit lock và lightweight preflight không import heavy modules. Native CPU import dùng source thật chỉ import/provenance, không instantiate/train model hoặc mở dữ liệu learner.

Sau targeted suite, metadata-only `preflight(AKTConfig())` trên report Windows legacy `artifacts/akt/preflight/runtime-v2.json` trả **ready**, không sửa report đó. [Receipt](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/legacy-windows-preflight.json) giữ runtime report SHA, lock SHA và upstream commit. Không coi receipt này là execution authorization.

## Lệnh kiểm

Lượt 01 dùng cùng pytest arguments nhưng chỉ test_runtime, output/basetemp ở `parallel-linux-runtime-20261107-01`, chưa có process-scoped safe.directory. Lượt 02/03 có cả preflight node và safe.directory. Exact final command từ repository root:

```powershell
$env:PYTHONPATH = 'src'
$gitConfigOffset = if ($env:GIT_CONFIG_COUNT) { [int]$env:GIT_CONFIG_COUNT } else { 0 }
[Environment]::SetEnvironmentVariable("GIT_CONFIG_KEY_$gitConfigOffset", 'safe.directory', 'Process')
[Environment]::SetEnvironmentVariable("GIT_CONFIG_VALUE_$gitConfigOffset", 'D:/Dev/KLTN/artifacts/akt/dependencies/upstream', 'Process')
$env:GIT_CONFIG_COUNT = [string]($gitConfigOffset + 1)
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp=artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/pytest-temp --junitxml=artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/pytest.xml tests/akt/test_runtime.py tests/akt/test_runner.py::test_preflight_verifies_gate1_without_opening_dataset *> artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/pytest.log
```

Lượt 02 đổi suffix03 thành02 và dùng source fixture trước một dòng sửa argv. Process-scoped Git setting chỉ cho phép đọc upstream đã pin; không gọi git config, add, commit hoặc push, không đổi config toàn máy.

## Evidence và giới hạn bàn giao

[Handoff inventory](../../artifacts/akt/local-tests/parallel-linux-runtime-20261107-03/handoff-inventory.json) giữ SHA-256 nguồn/tests/report/logs/XML/receipt và mapping snapshots. Bốn source/test snapshots cuối khớp SHA trước/sau copy. Hai source fixture trung gian được dựng lại từ final test source bằng các patch đã biết, **không có pre-run SHA certificate**: trial02 bỏ một dòng argv; trial01 bỏ tiếp tám cases bổ sung sau lượt01. Chúng chỉ giúp chẩn đoán failure; final source mới là snapshot dùng cho proof63pass. Metadata reconstruction nêu rõ giới hạn, không gán final snapshot ngược vào intermediate runs.

Source/tests đã freeze trước parent Gate16; report/evidence được viết ngoài Gate2 inputs. Parent phụ trách full Gate16, combined archive/index/map/Git. Không đóng bundle riêng hoặc sửa bundle đã đóng trong tiểu tác vụ này.

**GPU06 còn một phần chưa làm:** main runner vẫn có constants/default wiring cho `requirements-akt.lock.txt` và `runtime-v2.json`; chưa nối explicit Linux/CUDA lock/report vào worker/authorization identity end-to-end. Smoke/pilot phase vẫn CPU-only theo config hiện hành. Chưa có immutable Linux/CUDA image/install proof, package-code attestation, actual Linux regression, GPU phase/caps, data-worker lifecycle, selection/refit/export trên CUDA, Modal Volume durability hoặc representative throughput. Không biến Colab inherited mode thành main-worker accepted mode bằng thay đổi này; không claim full Linux/CUDA worker ready hoặc Gate4 từ targeted63pass.
