# Sửa hẹp identity shim, chưa chạy

Nguồn actual: `gate-collection02/stdlib/shim-ancestry-observation.json`,
SHA`8d85185b72fe39331451fc318d4bc672f4661028e75d587d46c66bff8dd4112d`.
`exact_parent=true`, `creation_order=true`, `exact_venv_entry=false`.
psutil ghi `\Dev\KLTN\.venv\Scripts\python.exe`, thiếu drive, còn entry
đúng là `D:\Dev\KLTN\.venv\Scripts\python.exe`. Đây là nguyên nhân predicate
đã được chứng minh; không phải lỗi timestamp và không phải import denial.
Receipt outer02 ghi1.6557151s; ROOT báo terminal1.6587846s, hai phạm vi khác nhau.
Trial01/02 và packet154sources/69modules giữ nguyên.

03 thay riêng authority của image bằng `Kernel.token` nguyên bản helper:
`QueryFullProcessImageNameW` +GetProcessId +GetProcessTimes. Process handle chỉ
quyền query0x1000; Job handle chỉ query0x4, không assign/terminate/kill mới.
Giữ điều kiện psutil PPID và thứ tự creation time; thêm native PID chính xác,
full entry có drive khớp nguyên vẹn, integer FILETIME giữa parent/worker,
hai token cùng handle bất biến và shim thuộc exact named Job đã GO.
Mọi query handles phải close, lỗi close từ chối trước collection. Không prefix
`D:`, không chấp nhận suffix/path giống tên, không tolerance thời gian.

Output mới `gate-collection03`, `gate-collection03-outer`; cùng packet SHA
`bacc6e49d14d244396b7be03cf68c62daefa8c14adf056b1f0c5cde8b8f1ed90`.
Helper0dc872... giữ nguyên, cùng60s whole/4GiB admission/1GiB floor/3GiB process;
mọi import/body/fit/optimizer/data/CUDA guard khác không đổi.

Chuẩn bị8 unittest methods pure: positive native identity khi psutil path thiếu
drive; wrong drive/path/PID, FILETIME drift/outside bounds, wrong Job, và
PPID/time-order cũ vẫn bắt buộc. Không Kernel/Job/Popen/collection được gọi bởi
test; import worker definitions không gọi main. **Agent chưa chạy test/AST**.
ROOT review nguồn+hash rồi mới quyết định pure checks hoặc collection03.

Lệnh gợi ý ROOT review (chưa chạy):
`& .\.venv\Scripts\python.exe -B artifacts/akt/local-tests/akt-research-runner-20261108-01/test_gate_collection_shim03.py`

CLI outer03 giữ các flags bắt buộc `--packet`, `--packet-sha256`,
`--worker-sha256`, `--approval-reference`; chỉ đổi tên script và worker SHA.
Collection vẫn không là GatePASS hoặc chứng cứ đã chạy test bodies.
