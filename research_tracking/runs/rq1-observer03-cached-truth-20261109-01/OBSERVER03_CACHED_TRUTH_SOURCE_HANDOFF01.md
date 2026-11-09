# Bàn giao nguồn cho witness latent120 của observer03

Nguồn đã chốt theo hợp đồng Root `RQ1_OBSERVER03_CACHED_TRUTH_CONTRACT01.md` SHA0b776908063d5e8bccce9b7bb4d55fbd43b3edb3d131816c2b000ba8809734d6. Chưa chạy Python, compile, import, unit tests hoặc phân tích cache. Agent chỉ so SHA/size opaque và đọc metadata/source. Không giải nén oracle hoặc tổng hợp truth ở bước này.

## Files cố định trong cùng P

| File | SHA-256 |
| --- | --- |
| analyze_observer03_cached_truth01.py | 586c06c39d023c465b3a408360de65decbb6793200adea54f84af72c1c3f75f4 |
| test_observer03_cached_truth01.py | 40e2baa9b12448ccb8d257a7b6a32876f4cd6ddb49148f7cab588645abf257d8 |
| run_observer03_cached_truth01.py | 3e28dd3f9b9ea7131797595a9c6c7875745dbb1b1f95c5cc9b6a935c462df868 |
| observer03_cached_truth01_packet.json | e387f9925154d464ee7d566bf88a014dd4d7a88872cc2f035d25a4ef9e01595a |

P là artifacts/akt/local-tests/akt-research-runner-20261108-01. Packet có8source/runtime pins và21input pins. PowerShell đối chiếu toàn bộ SHA/size đã khớp, bốn output namespaces chưa tồn tại. Không canonical source hoặc Gate discovery nào được chỉnh.

## Phép tính và nghiệm thu

Analyzer giữ ngưỡng native theta>=1250.0 AND stored pi<=.55, latent theta_before>=1250.0 bằng so sánh inclusive binary64, không làm tròn hoặc epsilon. ON được dùng một lần, OFF kiểm khoa học readouts và initial/final state giống hệt. Literal predicates được tính lại trước ghép. Dự báo phải khớp từng bit, selected concept/question/difficulty phải trùng bank, clock UTC6h/72h phải đúng từng bước.

Chỉ source stdlib đã ghim8590381c được compile vào module definitions riêng và gọi topology/validate_manifest/trace_rows/validate_trace. Không gọi entrypoint hoặc downstream analyses cũ. Giữ đủ14400rows/120histories/CRC trước chọn đúng key21000/PG/False/False. Outer pilot accepted/Job0/sourcepost/env và actual owned receipt/ON-OFF hashes phải khớp. Raw world theta chỉ được dùng như simulator-defined latent criterion cho120queried concepts trước current learning.

Pure có8physical unittest methods, gồm inclusive1250/.55 và nextafter, cả4cells/zero cells/suppression, missing/duplicate/extra/order, wrong key/bool alias, full query/Pbit/clock, OFF-ON/state drift, finite/predicate failures và duplicate JSON. Toàn bộ là fixture dựng tay, không mở research rows. Các negative loops nằm trong subTests, không gọi chúng là thêm independent tests.

Cached child xuất đúng joined120.json, summary.json, validation.json và result.json. Summary có native M×latent và theta gate×latent mỗi bảng4ô, giữ0, cùng uncertainty suppression theo latent false/true. Không chọn metric theo dấu. Pure child giữ unittest.log và result.json. Kết quả chưa có số liệu thật.

## Hai lệnh đề xuất cho ROOT sau review

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_observer03_cached_truth01.py --phase pure --packet-sha256 e387f9925154d464ee7d566bf88a014dd4d7a88872cc2f035d25a4ef9e01595a
```

Sau actual pure8 được nghiệm thu cùng packet và không late rejection, ROOT mới xem xét một lệnh cached.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_observer03_cached_truth01.py --phase cached --packet-sha256 e387f9925154d464ee7d566bf88a014dd4d7a88872cc2f035d25a4ef9e01595a
```

Pure whole8/owned6 gồm cleanup1/worker4/final reserve2. Cached whole15/owned13 gồm cleanup2/worker9/final reserve2. Đây là hai allocation riêng, không dự báo runtime. Worker có hard timer, outer đo cùng whole clock qua readback/cleanup/final receipt, giữ postwrite rejection nếu trễ. Không tự retry.

Prelaunch available RAM1GiB, worker sampled highwater256MiB/free512MiB. Memory query dùng ctypes Windows thật, không import psutil/scientific packages trong analyzer. Scope RAM là worker highwater và system free samples, không claim quota cứng hoặc sampled whole Job RSS. Owned helper0dc kiểm startup/cleanup/Job0 như trước.

Compressed cache1MiB, decoded8MiB, line8192B, full14400rows. Child tổng896KiB, owned trước final64KiB, final64KiB giữ tổng output acceptance1MiB. Stdout/stderr mỗi file32768B. Audit chặn model/scientific imports, process/network phát sinh và các vùng bảo vệ. Các phép đọc runtime stdlib vẫn cần cho Python, không gọi đây là OS sandbox. Source/input SHA trước/sau và output fsync/readback thật đều bắt buộc.

Chỉ một history PG/gOFF/λ0 với120thời điểm lặp. OFF không tăng mẫu, không so graph, không calibration hoặc human-mastery truth. Không thêm GAM/world/NN hoặc scientific RNG draws. Nhánh full RQDIAG23 vẫn thiếu, không được dùng partial outputs thất bại. Sau handoff này source giữ nguyên cho ROOT review và quyết định dispatch.
