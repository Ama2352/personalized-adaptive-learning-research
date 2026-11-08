# Collection04: bỏ terminal emission trùng, chưa thực thi

03 actual bị reject: ROOT terminal53.99765s, outer stored53.9911401s/60.
Stdlib19 và no-torch271 được chấp nhận riêng; **không** coi290 là toàn suite.
Remaining worker RC124, owned40.7451856s, cleanup accepted/Job0, không result.
`remaining/collection.log`99036B kết thúc giữa danh sách node IDs; guard identity
native03 đã qua. Không retry cùng hypothesis ancestry hoặc tăng cap.

Source cài đặt `.venv/Lib/site-packages/_pytest/terminal.py` SHA
`28c4a9ebca0243385b154f47ecb83b18a1df415e0b912ebd97079c5ea0036459`:
lines905–924 gọi `_printcollecteditems(session.items)` trong collection_finish;
927–938 với `-q` lặp toàn bộ items và `_tw.line(item.nodeid)`. `-qq` vẫn lặp
toàn bộ IDs rồi in count mỗi module. Đây là bằng chứng chi phí reporting lặp
được thực hiện sau khi items đã tồn tại; **không** chứng minh bao nhiêu giây đã
dành cho reporting, hoặc final collection đã hoàn tất/trả RC0.

04 chỉ đổi pytest argv từ `--collect-only -q` sang
`--collect-only -p no:terminal`, giữ `-o addopts= -p no:cacheprovider`.
Bỏ `-q` vì option này được terminal plugin đăng ký (terminal.py137/177).
Collector vẫn lấy nodeids từ session.items, collection_reports/RC và cấm
runtest protocol; sessionstart kiểm actual terminal/terminalreporter không có.
Outer cũng yêu cầu field observed `terminal_reporter_disabled=true`.
Source config.get_verbosity dùng default0 khi không có verbose; logging.py
775–812 xử lý reporter absent và collectonly; cacheprovider đã disabled.

Mọi profile/audit/body/fit/nativeidentity/resource guard khác nguyên vẹn.
Vẫn60s whole,4GiB admission/1GiB floor/3GiB mỗi process,3fresh groups,
packet154sources/69modules SHA`bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90`.
New outputs `gate-collection04` và `gate-collection04-outer`, no retry,
không reuse warmed group hoặc nhận outputs290 của03 vào04.

Chưa chạy AST/tests/collection04. Pure8PASS trước đó thuộc03 identity fixtures,
không relabel thành kiểm04. ROOT review exact diff rồi mới quyết định dispatch;
nếu04 thất bại, giữ receipts, không lặp vô hạn hoặc bỏ guards để đạt60s.
Collection accepted vẫn không là fullGatePASS.
