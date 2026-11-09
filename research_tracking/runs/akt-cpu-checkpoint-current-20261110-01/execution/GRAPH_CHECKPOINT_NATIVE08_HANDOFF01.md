# Native checkpoint08 — bàn giao nguồn

Bản 08 chỉ cập nhật namespace chạy riêng, một SHA test hiện hành và bằng chứng cold299 thật. Bản 07 giữ nguyên. Chưa khởi động worker hoặc thực hiện test/native từ bộ 08.

## Nguồn đã đóng băng

| File trong cùng thư mục | SHA-256 |
|---|---|
| check_graph_checkpoint_native08.py | e5c713c0ce18a7be34745a1c664bdc325d4b9030db86935b2c4d678dfea5e1dc |
| run_graph_checkpoint_native08.py | c95ee5cb0a4e7c707eda33a797ac5420fc24f3b40dc90fb5662c8be918e0dbf2 |
| graph_checkpoint_native08_allocation.json | 7fac9d95c6e25307e2352c349235af7b063c870531a787d0fec250caa319dea3 |

Pin canonical duy nhất thay đổi là tests/akt/test_research_selected_resume.py, từ 7d363fbc100263b577243bcc6b4fe98a4b0d499cdb89796e09dcadf28d4e393d sang aec0c914c6d96d791b2df916e8a7fcab75a4d54bc4dec6c138d242ec284d30bb. Hai pin harness chuyển từ 07 sang 08. Không sửa model hoặc test canonical.

## Bằng chứng bắt buộc trước khi chạy

- Actual tests06 có 299 bodies, 0 failures/errors/skips, tập checkpoint38 đúng và Job0. Receipt SHA 9d29efe4f37f10d6674918be83c24cbd8e0c92477949804f4e0e3683768b96a8.
- Collection06 có 0 test bodies, SHA f91f3ba802056ffc562342122a9d54d9d51394e6352d30025bff4f0b504ac913.
- Cả hai dùng graph29_metadata04_packet.json SHA 2241fe727bbc68f8ba94bfe571208b9bc0528137dcf4c2c3a12ecb42d420963d. Tên packet03 cũ không được dùng làm bằng chứng cho attempt06.
- Worker và outer đều yêu cầu SHA receipt do ROOT truyền bằng đối số bằng SHA đã ghim trong allocation, attempt06 và SHA collection đúng. Các kiểm source/runtime trước–sau, 299 IDs, 38 subset, ba deselections và owned cleanup giữ nguyên.

Đã đối chiếu SHA hiện hành bằng PowerShell. Native allocation có 78 source pins và 12 runtime pins. Metadata packet có 44 source pins và 11 runtime pins. Không phát hiện drift. Đã chạy stdlib ast.parse trên đúng hai file mới bằng .venv với -I -S -B. Hai AST hợp lệ, không import hoặc thực thi worker. Các thư mục output08/owned08/gcn08 còn vắng lúc kiểm. Không có bằng chứng native08 từ việc kiểm nguồn này.

## Hạn mức giữ nguyên

18 fixtures gồm 16 checkpoint và 2 stopper. Trần 2 adapter/backbone/wrapper/gate/Adam constructors, 6 forward, 4 backward/clip/Adam/adapter steps, 96 training target exposures, 7 save và 8 load. Hai stopper thêm 4 constructors và 8 observe, không thêm NN hoặc serialization. Whole120s, owned tối đa116s gồm cleanup3s, child110s, native100s. Admission4GiB, worker và exact owned Job family1GiB, available floor2GiB. Không actual corpus, CUDA, research fit hoặc lifecycle-resume claim.

## Lệnh ROOT duy nhất sau review

```powershell
& .venv/Scripts/python.exe -I -B artifacts/akt/local-tests/akt-research-runner-20261108-01/run_graph_checkpoint_native08.py 7fac9d95c6e25307e2352c349235af7b063c870531a787d0fec250caa319dea3 9d29efe4f37f10d6674918be83c24cbd8e0c92477949804f4e0e3683768b96a8
```

Lệnh trên chưa được thực thi. Output mới chỉ được tạo cho attempt08 khi ROOT quyết định chạy. Không tự retry.
