# Gate phần mềm Windows hiện tại: bản chuẩn bị riêng, chưa thực thi

Ngày09/11/2026. Đây là chuẩn bị kỹ thuật để ROOT review; không phải quyền chạy, kết quả collection, GatePASS hoặc quyền nghiên cứu/GPU. Không đổi production, pointer, bộ đóng cũ hoặc hồ sơ export từng bị chặn.

## Population và nguồn

`gate_source_snapshot04.json` là snapshot metadata đọc/hash filesystem, chưa import Python: **177 native build paths /81 test modules**; so packet03 lịch sử154/69 là23thêm,2đổi,0bỏ. Hai file đổi là `scripts/akt/build_colab_bundle.py` và `tests/akt/test_colab_bundle.py`. Không có số test case mới: `collected_case_count=null`.

Ba partition giữ đúng native `refresh_gate2.test_partition`:1module stdlib,6module no-torch,74module remaining. Đây là số module, không phải số ca PASS. Snapshot giữ toàn bộ map, delta, Windowslock và upstream4. Năm tài liệu21/22/23/26/allocation được bind bằng map riêng; không sửa native build glob để đưa chúng vào Gate schema cũ. Population chỉ là membership của native Gate hiện có, không chứng nhận mọi file repository hay Linux/CUDA.

`prepare_current_freeze04.py` yêu cầu ROOT review reference và snapshotSHA riêng, đối chiếu lại cả canonical `gate2_build_hashes()`/`test_partition()` lẫn mirror trước/sau, rồi mới ghi packet mới exclusive. Không nhận số case hoặc kết quả PASS. Định danh nguồn không tự cấp quyền execution.

## Collection10: lần chạy sau review, tối đa60giây toàn bộ

`gate_collection_worker10.py` và `run_gate_collection10.py` kế thừa09 đã review: ba fresh processes theo thứ tự native, không warm/reuse/split; owned helper0dc/GO, native shim PID+FILETIME+image, pywin32 namespace RECORD318537, ROOT-first và childnamespace đúng, before/after maps, monitor, profiler và audit giữ nguyên. Admission4GiB; floor1GiB; mỗi process RSS/peak tối đa3GiB quan sát hợp tác.60giây gồm launch/ba nhóm/cleanup/posthash, không reset theo nhóm, không tự retry/tăng cap.

Thay đổi riêng: output10; năm supportdocs hash trước/sau; `runtime-temp` riêng từng nhóm với TEMP/TMP/TMPDIR và cache `tempfile.tempdir` được lưu/khôi phục; logging pytest trỏ `pytest-file.log` trong owned output, terminal reporter vẫn tắt. Không mở rộng NUL alias/write guard. Helper giữ CUDAhidden/thread2 và bỏ PYTHONPATH/HOME/startup trước GO.

Imports thực thi module tops; collector chỉ cấm test bodies/model constructors/backward/optimizer step/solver fit/teacher/data/CUDA execution cùng runtest protocol. Nhóm remaining được import Torch CPU và framework có thể tạo tensor metadata khi import: **không có bằng chứng universal tensor-constructor0**, cũng không có NN global workload từ collection. Nhóm stdlib/no-torch giữ purity cũ. Chỉ actual collection thành công mới có exact nodeIDs, module coverage và số case. Nếu hết60giây hoặc import/nguồn/resource/cleanup sai thì giữ failure, dừng.

Lệnh đề xuất ROOT chạy sau review (tại repository, bằng entry .venv; chưa chạy):

```powershell
$p = 'D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01'
& D:/Dev/KLTN/.venv/Scripts/python.exe -B "$p/prepare_current_freeze04.py" --snapshot-sha256 3ff306b319f31ceb225453d8256f254a5bf03be4fdf84f75381942086102f2d8 --collection-outer-sha256 4e6e43d36bbf0f09fa575ba0959566689cad02dd4540f78a2f7f2c75d0a0d18e --root-freeze-reference '<ROOT_REVIEW_REFERENCE>' --output "$p/gate_collection04_packet.ROOT.json"
# ROOT kiểm tra packet/readback và chốt SHA từ actual file trước bước sau.
& D:/Dev/KLTN/.venv/Scripts/python.exe -B "$p/run_gate_collection10.py" --packet "$p/gate_collection04_packet.ROOT.json" --packet-sha256 '<ACTUAL_ROOT_PACKET_SHA>' --worker-sha256 915cc64060fcbe6b35663566311c13b11fcca8e39c2e2b2ed205a12d6634271d --approval-reference '<ROOT_COLLECTION_REVIEW_REFERENCE>'
```

Các placeholder bắt buộc do ROOT cung cấp, không phải receipt giả. `gate-collection10`/`gate-collection10-outer` phải vắng mặt. Chưa chạy AST/import canary hoặc collection trong nhánh chuẩn bị này.

## Full Gate: derivative02, chỉ sau actual collection và review ROOT

`windows_current_gate_worker02.py`/`windows_current_gate_outer02.py` giữ native CLI thật, ownership và JUnit mapping utility đã ghim. Native timeout580; owned tối đa600 gồm cleanup3; outer630, active≤615, admission4GiB/floor1GiB/RSS3GiB mỗi process. Output exclusive, không publish/currentpointer; trước/sau pointerbytes được bảo toàn và mọi thay đổi bất ngờ đều reject. Không có rollback thủ công thành PASS.

`prepare_windows_current_gate_packet03.py` nhận actual collection-input/result bằng path+SHA ROOT cung cấp. Nó nạp actual ba childresults/Job receipts, ánh xạ toàn bộ nodeIDs qua installed pytest utility với collision check, ghi/readback packet mới. Worker yêu cầu177/81 và supportdocs giống collection; **không còn hardcoded1418/836 hoặc154/69**. Full Gate so executed group+merged JUnit identities với actual collection, không suy expected count từ kết quả vừa chạy. `runtime-temp` của native child được truyền xuống ba pytest processes, khôi phục env/cache trước receipt.

Lệnh metadata tiếp theo chỉ chuẩn bị sau khi actual10 tồn tại; các tham số input/resultSHA và ROOTreview phải lấy từ file thật. Sau đó ROOT mới review packet và quyết định lệnh outer02, không dispatch tự động:

```powershell
& D:/Dev/KLTN/.venv/Scripts/python.exe -B "$p/prepare_windows_current_gate_packet03.py" --worker-sha256 b59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374 --outer-sha256 2d08b32c4356e8096624b9e95f9f78685548d6003335efbeef8021321a648819 --runtime-report D:/Dev/KLTN/artifacts/akt/preflight/runtime-v2.json --collection-result "$p/gate-collection10-outer/final.json" --collection-result-sha256 '<ACTUAL_FINAL_SHA>' --collection-input "$p/gate_collection04_packet.ROOT.json" --collection-input-sha256 '<ACTUAL_INPUT_SHA>' --output "$p/windows_current_gate_packet04.ROOT.json" --root-review-reference '<ROOT_ACCEPTED_COLLECTION_REVIEW_REFERENCE>'
& D:/Dev/KLTN/.venv/Scripts/python.exe -B "$p/windows_current_gate_outer02.py" --packet "$p/windows_current_gate_packet04.ROOT.json" --packet-sha256 '<ACTUAL_FULL_PACKET_SHA>' --worker-sha256 b59becc9c2af31d10cf20a4afc17a05946a1e9acdd989114d30bcbfb3dc3b374 --outer-sha256 2d08b32c4356e8096624b9e95f9f78685548d6003335efbeef8021321a648819 --run-id win-current-gate-20261109-04 --approval-reference '<ROOT_FULL_GATE_REVIEW_REFERENCE>'
```

Runtime-v2 chỉ tái dùng nếu native preflight còn nhận đúng prefix/origins/source/upstream/lock; không dùng Gate cũ để admit Gate mới, không sửa report runtime để ép hợp lệ. Không bắt tái runtime hoặc standaloneGit calls nếu validator hợp lệ cho cache/module hiện hành.

## Điều cần review trước full Gate, không đoán caps

Các test mới có shared fixture/method wrappers và modulecache. Các native counts từ model25, optimizer1, checkpoint16 là allocation độc lập trước đây; không cộng thành cap toàn suite. Collection cung cấp module graph/top-level potential calls/imported sources và actual zero-body counters, **không đo runtime số forwards/backwards/Adam của test bodies**. ROOT cần chốt bounded fixture workload/admission cho full Gate sau exact collection và review overlap; derivative vẫn dùng original finite wall/RAM guards, không tự tuyên bố operation-count proof. Nếu580giây không đủ thì giữ failure và dừng, không tự nới.

Gate03 lịch sử1418PASS/154 giữ nguyên, pointer9e768 vẫn lịch sử và stale với177current paths. `CURRENT_GATE_REFRESH_GAP01.md` f38af8 và toàn bộ inventory01–04 đã freeze không bị sửa. Không ZIPbuild/sourceexport/network/Colab/GPU/teacher/actualcorpus trong preparation này; full software Gate sau này chỉ synthetic fixtures theo suite, không fit research hay cấp chi phí.
