# AKT: cài đặt cô lập và audit CPU trên Linux — 08/11/2026

**Venv Linux hiện có đã qua một audit riêng về 44 distributions và 8 CPU imports; chưa có Linux full Gate, CUDA, image hoặc nghiệm thu main-worker.** Hai controller cài đặt ban đầu vẫn giữ trạng thái `FAILED_RETAIN_PARTIAL_NO_RETRY`. Audit được chấp nhận sau đó chỉ đọc venv đã cài, không cài lại, không chạy pip hoặc mô hình.

Bằng chứng nằm trong [bundle kết hợp](../runs/akt-linux-isolated-install-20261108-01/README.md). Báo cáo [dependency resolution](akt_linux_dependency_resolution_20261108.md) và [addendum](akt_linux_dependency_resolution_20261108_addendum.md) trước đó vẫn là snapshot metadata closure, không được sửa thành installation proof. Phần việc này không dùng realdata/Holdout, không đổi phương pháp nghiên cứu hoặc cấp ngân sách compute mới.

## 1. Ba sự kiện, ba kết luận riêng

| Sự kiện thực tế | Kết quả và thời gian | Phạm vi kết luận |
|---|---|---|
| Install attempt01 | **FAILED**, 0,382591 giây; `probe-before=0`, `base-pip-before=1`; chưa có process `pip-install` | Guard đọc cấu hình pip không tương thích cấu trúc API nested; target còn rỗng theo probe. Không gọi lượt này là installation thành công |
| Install attempt02 | **FAILED**, 398,913576 giây; `pip-install=0`, `pip-check=0`, `distribution-origins=1` | Pip install report chọn đúng 44 distributions/URLs/hashes; stdout pip check là `No broken requirements found.`. Controller dừng ở kiểm metadata; bước CPU-import của controller chưa chạy |
| Audit sự kiện thứ ba, alias **audit03** | **ACCEPTED CPU audit**, 23,361957 giây/90 giây, 1 child, cleanup/resource accepted | Remote directory thực vẫn tên `post-install-audit01`. Kiểm riêng 44 distributions, mọi RECORD-file origin trong venv, 8 imports và 1 CPU scalar. `install_calls=pip_calls=network_calls=gpu_model_steps=optimizer_steps=modal_calls=0` trong audit |

Raw được giữ **11 + 20 + 7 = 38 tệp**, tính cả ba transport manifests; mỗi lượt có alias riêng trong bundle. Source thực thi lần lượt có SHA `28927535…`, `021dcbe8…`, `dd7738bf…`. Audit03 không sửa hoặc nâng trạng thái kết quả02. Trường `packages_installed` trong failed result02 không có giá trị44; kết luận về selection được lấy từ pip install report và child exit0, rồi đối chiếu independently với 44 distributions hiện có trong audit.

Môi trường target là CPython3.13.18/Linux x86_64/glibc2.39, interpreter `/content/KLTN_GPU08_20261108_01/.venv/bin/python`, prefix đúng `.venv`, `include-system-site-packages=false`. Target ban đầu được tạo `--without-pip`; base pip26.2.2 điều khiển target bằng `--python`. Không cài pip vào Python global hoặc target để vượt qua lỗi kiểm.

## 2. Failure01: sửa cách đọc API, giữ điều kiện cấu hình nghiêm ngặt

Guard đầu tiên giả định `Configuration.items()` trả flat key/value và yêu cầu suffix `config-file`. Probe read-only26.2.2 thực tế ghi đúng một nested item: `':env:' -> {':env:.config-file': '/dev/null'}`; chỉ có biến `PIP_CONFIG_FILE`, giá trị bằng `os.devnull`. Đây là lỗi giả định hình dạng private API, không phải bằng chứng index/target ngoài dự kiến.

Source02 chỉ chấp nhận hai hình dạng chính xác: flat `{':env:.config-file': devnull}` hoặc nested như probe. Nó yêu cầu đúng một `PIP_CONFIG_FILE=devnull`; từ chối duplicate, section/key/type khác, index/target và suffix giả như `global.config-file`. Không flatten cấu hình tùy ý hoặc bỏ guard. Lỗi01, stderr, child sources và kết quả FAILED được giữ nguyên.

Synthetic unit checks dùng original guard AST trong harness: **28 cases = 18 pass, 6 fail, 4 errors**; corrected guard **28 pass**. Các errors/failures của harness là kiểm hình dạng/strictness, không phải 10 lỗi installation độc lập. **6 cleanup mocks** xác nhận không signal lại historical PGID, từ chối controller PGID và lỗi cleanup chặn acceptance. Không actual pip/network/model trong các unit checks này.

## 3. Failure02: metadata vendored khác distribution gốc

Source02 dùng `str(f).endswith('.dist-info/METADATA')` trên mọi RECORD entry. Actual read-only diagnostic thấy **44 distributions đều có đúng một top-level METADATA**; riêng setuptools84.2.1 có **13** matches ở mọi độ sâu: một `setuptools-84.2.1.dist-info/METADATA` và **12** metadata vendored, gồm `setuptools/_vendor/autocommand-2.2.2.dist-info/METADATA`, `backports.tarfile-1.2.0` và `importlib_metadata-8.7.1`. Vì vậy assertion `len(metadata)==1` thất bại dù các vendored metadata không phải 12 distributions ngoài selection.

Audit mới chọn đúng đường dẫn RECORD có **hai thành phần**: `<name>.dist-info/METADATA`. Nó vẫn kiểm **mọi** RECORD-file origin ở trong venv, kể cả nested files và scripts; không bỏ nested files khỏi kiểm origin. Root metadata phải nằm trực tiếp dưới purelib, có đúng một candidate, tồn tại và có header Name/Version đúng distribution đã pin. Missing/multiple root, nested-only hoặc root/file escape đều bị từ chối.

Same synthetic path tests trên all-depth matcher cũ: **11 pass/5 fail trên16**; root matcher mới: **16 pass**. Sau sửa cleanup, chạy lại16 cases vẫn pass và **7 cleanup/structure checks** pass. Các tests dùng synthetic paths và virtual process objects, không đọc interactions, không tạo venv/cài package hoặc chạy mô hình.

Bản audit trước review `ab3c524f…` chưa chạy remote, được giữ riêng. Review phát hiện cleanup nằm sau post-child parse/hash/workspace scan; source cuối chuyển cleanup vào child `finally` ngay, có handled flag dùng chung và outer fallback không signal lại PGID đã xử lý. Mọi signal/reap failure chặn PASS. Deadline được hậu kiểm sau cleanup/hash/resource checks để không nhận kết quả quá90giây chỉ vì child exit0. Không dựng một actual remote failure cho bản audit chưa chạy.

## 4. Audit CPU đã chứng minh điều gì?

| Kiểm thực tế | Kết quả |
|---|---|
| Selection | 44 distributions = 29 root pins + 14 NVIDIA packages + Triton3.3.1; exact versions/URLs/SHA trong resolver report và install report khớp |
| Torch build | `2.7.1+cu126`; `torch.version.cuda='12.6'` là build metadata |
| Venv/origins | Actual executable/prefix đúng target; 44 distribution metadata origins và mọi RECORD-file origin qua guard trong venv; không external distribution origins |
| Top-level metadata | Exact44 names/versions; SHA của từng root METADATA và file counts ghi trong raw stdout/result; setuptools nested ignored count12 |
| CPU imports | Torch2.7.1+cu126, NumPy2.5.4, pandas3.0.6, DuckDB1.5.6, scikit-learn1.9.1, SciPy1.18.1, psutil7.2.2, pytest9.1.1; từng module origin nằm trong venv |
| CPU scalar | Một `torch.zeros(1, device='cpu')`, kiểm giá trị0; 0 optimizer/model steps |
| CUDA | `cuda.is_initialized()` false trước/sau scalar; không gọi `is_available()` hoặc query device, không CUDA kernels |
| Audit budget | 23,361957 giây, one child return0, cleanup accepted; peak workspace **quan sát**5.652.041.728bytes, khoảng5,26GiB |
| Source/input binding | Source audit được hash trước/sau; bind resolver report/lock, actual failed02 result/output manifest, pip-install report, pip-check stdout, executed02 source và venv cfg |

Install02 có budget600giây/20GiB workspace/min30GiB free; peak quan sát8.681.422.848bytes, khoảng8,09GiB. Audit riêng90giây giữ workspace20GiB/min30GiB free. Các cap storage là **cooperative observation**, có thể overshoot; không hard filesystem quota, network-byte limit hoặc toàn bộ peak RAM. Hai peak khác nhau phản ánh workspace tại hai thời điểm, không đo kích thước download hay tuyên bố đã dọn toàn host.

Pip đã thực thi `--require-hashes --no-deps --no-index --only-binary=:all:` theo 44 direct wheel URLs, không fallback resolve/install thêm. Điều này cùng install report là bằng chứng hash enforcement của pip; **không** phải một retained wheelhouse đã được hash độc lập hoặc một image digest. Audit hash metadata files và kiểm paths, không full installed-byte/RECORD-content attestation cho mọi binary, không chứng minh mọi global filesystem byte không đổi.

## 5. Windows Gate22 và những acceptance còn thiếu

Bundle giữ bốn snapshot của **Windows Gate22**: report, log, JUnit XML và current pointer. Actual **768 pass, 0 failures/errors/skips**, elapsed **477,7091635 giây <=540**, interpreter `D:\Dev\KLTN\.venv\Scripts\python.exe`; report SHA `f2f702408adb2162b0102aaca80eac1b1acd59ebec56a2fb77d8b1a358b276cd`. Tên run có chữ `linux-tooling` vì kiểm thay đổi tooling phục vụ Linux; host thực tế vẫn Windows. Không gọi kết quả đó là Linux full Gate hoặc chạy lại Gate trong lần archive này. Bundle tooling44 outputs trước đó giữ nguyên.

Các điều kiện sau **chưa được hoàn thành**:

1. **Actual Linux full software Gate:** đưa đúng source/test/dependency identity vào project Linux và chạy bounded CPU suite thực tế, report/JUnit/source hashes/exact Linux lock, cùng final reader. 44 package imports không thay được toàn suite; không dùng current Windows pointer làm proof Linux.
2. **Linux main-worker lifecycle:** source/Gate/runtime/context/authorization bind đầy đủ, synthetic prepare-only inputs được duyệt, loader→train→validation→checkpoint reload/export/resume, watchdog/caps và negative guards. Audit CPU scalar không là một training step hoặc Gate4.
3. **CUDA/image:** runtime GPU được cấp phép riêng, actual driver/device/architecture, schema2/requested device/strict origins/Linux lock; immutable image/base digest và recovery/storage nếu dùng môi trường đích. Build metadata CUDA12.6 và14 NVIDIA distributions không chứng minh T4/CUDA execution. Proof kitv12 Torch2.14.1+cu130 trước đó không chứng nhận profile2.7.1+cu126.
4. **Throughput/cost forecast:** đo end-to-end main-worker CPU/GPU pipeline, gồm data loading/validation/export/inference; dự báo thời gian/credits sau khi có measurements. Không suy chi phí huấn luyện từ398,9giây cài wheel hoặc23,4giây audit. Không Modal/GPU/cloud charge mới hoặc đổi financial allocation trong stage này.

Đây là tiến độ kỹ thuật về môi trường CPU, không baseline evaluation, không hiệu quả RQ1/RQ2/S04/S05 hoặc quyết định final methodology.

## 6. Chuỗi SHA và phạm vi archive

| Artifact thực tế | SHA-256 |
|---|---|
| Executed install01 source | `28927535b16b66167e4c71a42a406d9a1c138b388806df093434cba6c0010a87` |
| Executed install02 source | `021dcbe8a4a4a994d56572eb0ac76743c9a1bb3854cb56ca205da7017cb1a21f` |
| Executed separate audit source | `dd7738bfe06032ffaea6a921619767fd659e626ff53ee5a2a7203fb33f885132` |
| Actual install02 pip report | `a689302643eef8b3e6699a074ad6421933086195430614d88de81cc2b34a54ce` |
| Actual failed02 result | `2ce1bb8efceb4baccab106565280b1a987a9989fcc2116ef4f803687f08b3918` |
| Separate accepted audit result | `dd3b18c2ef7fd2f109077395e77a7f7243fd35a0cdc68dd7045f8233de71f966` |
| Audit transport manifest | `bc507522307f7fb52448553c941ec85d8401b53ba91b82cd3d4fb32e9f7d62ce` |
| Audit transfer ZIP, reference only | `a6231c9f20a7830b8cb20ea7bbf9207888c176add5026a89079f4419e8750fa3` |

Offline helper mới xác minh các raw SHA/size, report equality44, actual stdout/result/source bindings, diagnostics, Windows report/log/JUnit/pointer hashes và aliases. Chỉ đọc artifacts có sẵn; không remote, pip/install, GPU hoặc model. Bundle giữ raw38files, failure logs, test/source/RED-GREEN/cleanup receipts, metadata diagnostic, report và copy SHA inventories trước/sau. Output cap tăng60→80 **chỉ cho archive** để giữ thêm audit03 và WindowsGate22, không tăng cap execution/compute. Actual counts/SHA/force-add paths nằm trong manifest/inventories của bundle.

Không copy venv, caches, wheels, ZIP/chunks, full private MCP responses hoặc credentials. Sources export/receive chỉ là local snapshots của transport tooling; receipt hashes không được diễn giải thành remote cryptographic signatures. Old resolution/proposal/tooling bundles không được sửa hoặc thay thế. Root index/state/Git do parent xử lý riêng.
