# Điều chỉnh thứ tự packet nguồn Gate

ROOT đã chạy helper04 và dừng trước khi tạo packet. Diagnostic `root_gate_freeze04_metadata_diagnostic01.json`, SHAfe568bca3187f9d9f7336c3cd788bc25f3fb89d78dfe0409a6ce6f69d0bd67bb, ghi `build_equal=true`, `groups_equal=false`. Toàn bộ177source hashes và membership81modules khớp. Bốn vị trí khác trong remaining là5/6 và53/54, tương ứng context/context_recovery và edge_confidence/artifact. Nguyên nhân là PowerShell culture sort và Python native ordinal sort khác nhau.

`gate_source_snapshot05.json` lấy nguyên ba orderedgroups từ actual diagnostic ROOT. Snapshot05 bind SHA của diagnostic và snapshot04. Các maps nguồn, lock, upstream4, supportdocs5 và delta giữ nguyên giá trị. `prepare_current_freeze05.py` yêu cầu exact orderedgroups bằng actual diagnostic, rồi so toàn bộ canonical build map và native partition một lần nữa. Helper dùng exact lists, strings và order. Bản04 được giữ để truy vết failure.

Snapshot05 SHA743c715d2bc711b169d32277443f1c88cd6fdf8954b09dc523fb2860f02afa4d. Helper05 SHA68c87893921321f60ae4cbd4d949bdc0955a50d45a0c5f99c1656d5d765758a8. Collection worker10/outer10 và fullGate worker02/outer02/packetpreparer03 giữ các pins trong derivative04. Toàn bộ tài nguyên và tiêu chí acceptance của derivative04 tiếp tục áp dụng. Số ca mới chờ actual collection.

Lệnh metadata đề xuất để ROOT review và chạy

```powershell
$p = 'D:/Dev/KLTN/artifacts/akt/local-tests/akt-research-runner-20261108-01'
& D:/Dev/KLTN/.venv/Scripts/python.exe -B "$p/prepare_current_freeze05.py" --snapshot-sha256 743c715d2bc711b169d32277443f1c88cd6fdf8954b09dc523fb2860f02afa4d --collection-outer-sha256 4e6e43d36bbf0f09fa575ba0959566689cad02dd4540f78a2f7f2c75d0a0d18e --root-freeze-reference '<ROOT_REVIEW_REFERENCE>' --output "$p/gate_collection05_packet.ROOT.json"
```

Sau readback và review packet, ROOT có thể dùng collection10 command trong derivative04 với đường dẫn input05 và SHA lấy từ actual file mới. Packetpreparer03 cũng nhận input05 qua tham số. Các receipt collection10 và Gate mới chờ thực thi theo quyết định ROOT.
