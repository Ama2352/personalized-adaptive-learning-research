# Discovery stdlib trước T4 — nguồn offline đã freeze

08/11/2026. Chỉ đọc source/ABI/venv/package metadata; không cài đặt, model, device query, GPU/Modal hoặc chọn hardware. Chưa dispatch discovery qua MCP trong bằng chứng local này. Bộ cài CPU v3 SHA `5781815a7996689d0c824303ca30aa03e51fcfe183c8d9f70e805ae11ce8fa83` và production sources không đổi; Linux bundle194 đã đóng giữ nguyên.

## Hợp đồng và giới hạn

`discovery.py` dùng trusted project `/content/KLTN_GPU08_20261108_01`; metadata staging độc quyền ở `/content/KLTN_GPU10_DISCOVERY_20261108_01/<attempt>`. Không bootstrap project, tạo venv hoặc sửa source. Profile SHA `0944dc50b1840c35d6085e5faa888b3d3370849e59077ea68e9a2397009b8228` chứa161source hashes, bốn upstream source hashes,44versions/14NVIDIA và lock60dad. Host ABI đọc từ **actual Linux raw** `actual-abi-probe02-result.json` SHA `84f2393ae6a45de1a868410eed25b3be413e1928f2bea5f469010d3e18431f4b`, không lấy ABI Windows. Cả host/target actual ABI02 khớp; source01 ABI request chưa thực thi không thay bằng actual proof.

Controller và target chạy `-I -S -B` để tránh `.pth/sitecustomize` chạy trước probe. Trên CPython3.13, receipt giữ **actual no-site prefix `/usr`**, không giả `sys.prefix` thành venv. Lexical venv entry phải resolve cùng current base interpreter; cfg phải loại system sites. Metadata/origin fingerprints được đọc bằng stdlib/PathFinder tại explicit purelib, không import package. **Normal-startup venv prefix/site-hook validation còn cần phase audit riêng.** Điều này thay cho giả định normal startup trong plan ban đầu, không nới actual worker origin guard.

Các verdict: cold root/venv absent, cold venv empty, `WARM_CANDIDATE_REQUIRES_AUDIT`, hoặc `STOP_PARTIAL_OR_IDENTITY_MISMATCH`. Warm candidate không là approval reuse/install hay GPU ready: chưa kiểm actual wheel compatible tags, toàn bộ RECORD origins, CPU imports, CUDA driver/T4/sm75 hoặc allocator. Không tuyên bố full installed-site-byte attestation hay persistence parity qua hardware switch.

Source deadline28s để chừa cleanup/final receipt trong acceptance30s; target có một process group và cleanup once trước parse output. Wrapper timeout30s/reap grace2s, source/project/profile pre/post SHA và no-overwrite staging; quá budget/cleanup failure phải giữ STOP. Thời gian cleanup/OS filesystem là cooperative; không gọi đây là OS hard wall/quota.

**Giới hạn launcher/target:** `run_probe` tạo target session/process-group riêng. `launcher.cleanup_accepted` chỉ nghiệm thu launcher group, không bao trùm target. Khi nhận actual result, parent phải kiểm thêm `result.child.cleanup_accepted` cùng RC0 và source/project hashes; không suy launcher cleanup là đủ. Nếu outer kill xảy ra trước inner finally, có khả năng target còn orphan; bộ này chưa chứng minh global cleanup trên failure/recovery đó. Chỉ scope stdlib read-only, không GPU/model. Không dùng wrapper này thay native watchdog cho paid/model phase.

## Kiểm synthetic đã chạy

Lệnh1: `.venv\Scripts\python.exe -B artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/t4-discovery01/run_tests01.py`.

Trial01 **timeout60.043531s**, không JUnit hoàn chỉnh, giữ log/source/test/profile snapshots. Không suy final counts từ partial dots. Windows I/O tạo161file mỗi fixture quá chậm; không sửa guard hoặc nới assertion để đi tiếp.

Lệnh2: `.venv\Scripts\python.exe -B artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/t4-discovery01/run_tests02.py`.

Trial02 **40 PASS,0failure/error/skip**, XML54.225s, controller57.7544649s; cumulative **117.7979959s≤120**. Dùng một readonly161-file fixture chung; các target snapshot cases lặp dùng source-byte adapter để giảm I/O. Warm-positive và source-change/missing/lock cases vẫn đi filesystem thật. Bao gồm exact CLI parser với năm missing-required-flag negatives, ABI/path/origin/partial/type/SHA/deadline guards, probe AST no-heavy-import/device-query. Không chạy operation main/target child/model trong suite;0optimizer/network/install/GPU. Không thêm tests sau cumulative này. Năm inputs (source/test/profile/v3/actualABI) hash trước/sau bằng nhau.

Source freeze SHA `c176c85ad5e93c6daf229f9f7f884b277aa11c1ae99a259389059292784d0b75`; test SHA `48d942ff6b0c1a6519872b22146b666256530a9334ca8fb516d0ffcf956879a6`.

## Request đã chuẩn bị, chưa dispatch

Lệnh: `.venv\Scripts\python.exe -B artifacts/akt/colab/gpu09-cpu-worker-kit-20261108-01/t4-discovery01/prepare_request01.py`.

Sinh `request-add-cpu-discovery01.json` **26.362 byte**, SHA `56866449b24559273b59f2c7d4460520cb054dd8a4525f6aa1834b71cd7318fd`; cell SHA `cfa750cdf49006550115bf3f6b296f569dfc052776c19989b920ec2c9195d6ce`. Producer chỉ AST/definition/profile/argv parse; không gọi main hoặc remote. `request-contract01.json` ghi exact argv, source/profile pins và staging. Request dùng compressed source/profile có SHA/bounded decompression; JSON reply≤48.000byte, inline exact result text chỉ khi toàn reply nằm dưới cap, nếu lớn chỉ trả path/hash để retrieve text bounded. Không whole binary/base64600k, không WSS limit change. Parent review wrapper trước dispatch; không tự retry nếu bridge timeout hay stage đã tồn tại.

`cell_sha256` trong contract là hash UTF-8 của **code string thực gửi trong request**. Bản file `cpu-discovery01-cell.py` được writer Windows lưu CRLF nên có file SHA khác `dfd3e184a9d1882f3b5e47b4ba65686d5fc8131ba0071bc6cfebe32dc6cb427e`; không dùng hash file này thay hash request code. Operation source/profile payload vẫn giữ exact raw bytes/SHA đã freeze ở trên.
