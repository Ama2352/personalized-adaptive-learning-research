# Sửa derivative population của Gate — 10/11/2026

SOURCE-ONLY. Chưa chạy Python, AST, packet preparer, test, native hoặc Git trong lượt sửa này. ROOT cần review ba scripts, kiểm AST rồi chạy metadata preparation riêng.

## Failure giữ nguyên

Handoff trước kết luận native harness đã hoàn toàn parameterized là sai. `windows_current_gate_worker02.py` dòng68–69 còn yêu cầu exact177 build members/81 modules. ROOT đã chạy preparer04. Nó ghi provisional `windows_current_gate_packet06.ROOT.json`, rồi thất bại trong `worker.load_collection()` ở guard này. Thông tin trace lấy từ ROOT handoff, không tạo raw stderr thay thế.

Packet06 bị từ chối vẫn ở nguyên path, SHA8e8ffca01f926657b5f0f01a9706c48043e8ab5cfa8335505fabb512fd6920a2. Không dùng nó để chạy Gate. Không có native job từ preparation thất bại này. Handoff cũ được bảo toàn, note này sửa kết luận kỹ thuật đó.

Actual collection12 đã accepted1913 physical IDs,0 bodies,19/274/1620 theo ba nhóm,85 modules,183 source members và ba Job0. Final SHA b435f2f245074af5ae9f5273f575905dc438787fae856d68e02cf9949ffa4c2f. ROOT source packet07 SHA26e9e91ef6a8dc9e5f610853b5423f4163a56894bf5bc3d399cc57630d7baa59. Các bytes này được rehash, không sửa hoặc rerun collection.

## Diff duy nhất

- Worker02→03 thay guard exact177/81 bằng exact183/85 và sửa cùng diagnostic string. Đây vẫn là guard ghim population được ROOT duyệt.
- Outer03→04 chỉ đổi file ref worker02 thành worker03.
- Preparer04→05 chỉ đổi file refs worker02/outer03 thành worker03/outer04.

Đã rà ba scripts cho literal177/81 và các tên worker/outer cũ. Không còn guard population cũ. Numeric caps, semantic checks và mọi phần còn lại khớp originals sau đúng các phép thay trên. Inventory trước–sau nằm tại `gate_population_derivative07_inventory.json`, SHA2671f445a8bd22fcecb9f57b7ab02c0e5d6f6dfd277e796c0232b60cec932cac. Originals và provisional packet06 giữ nguyên.

| New source | SHA-256 |
| --- | --- |
| windows_current_gate_worker03.py | ba0f288de881eb17a315eda844753f9dc7f8363b43bb012957509b620602d729 |
| windows_current_gate_outer04.py | 0fb3c15e940f2425ef4599d2329a2675a50c9436a0a2c1cacc1bc674b0555a3d |
| prepare_windows_current_gate_packet05.py | 7965b12672f4bbbd02b4d9735ec279cbd83bfcd49b2eed4ca1fe372d11f9da58 |

Giữ native580/owned600 gồm cleanup3/outer630, admission4GiB, available floor1GiB/peak mỗi process3GiB, actual ownership trước GO, private process Git settings, exact collection→JUnit identities và no-publish. Không thay production Gate writer hoặc map183. Existingcollection12 còn hợp lệ cho derivative này vì scripts trong prep nằm ngoài production build map.

## Metadata command để ROOT review

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/prepare_windows_current_gate_packet05.py --worker-sha256 ba0f288de881eb17a315eda844753f9dc7f8363b43bb012957509b620602d729 --outer-sha256 0fb3c15e940f2425ef4599d2329a2675a50c9436a0a2c1cacc1bc674b0555a3d --runtime-report D:/Dev/KLTN/artifacts/akt/preflight/runtime-schema2-main177-20261109-01.json --collection-result D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate-collection12-outer/final.json --collection-result-sha256 b435f2f245074af5ae9f5273f575905dc438787fae856d68e02cf9949ffa4c2f --collection-input D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/gate_collection07_packet.ROOT.json --collection-input-sha256 26e9e91ef6a8dc9e5f610853b5423f4163a56894bf5bc3d399cc57630d7baa59 --output D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_packet07.ROOT.json --root-review-reference <ROOT_REVIEW_REFERENCE>
```

Chỉ sau metadata actual thành công và ROOT kiểm full packet mới cân nhắc command sau. Không chạy bằng provisional packet06.

```powershell
.\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_outer04.py --packet D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01/windows_current_gate_packet07.ROOT.json --packet-sha256 <ACTUAL_VALIDATED_PACKET07_SHA> --worker-sha256 ba0f288de881eb17a315eda844753f9dc7f8363b43bb012957509b620602d729 --outer-sha256 0fb3c15e940f2425ef4599d2329a2675a50c9436a0a2c1cacc1bc674b0555a3d --run-id win-current-gate-20261110-07 --approval-reference <ROOT_FULL_GATE_REVIEW_REFERENCE>
```

Packet07/output native07 hiện chưa tồn tại. Không claim metadata preparation mới, current Gate hoặc full suite PASS từ source correction này.
