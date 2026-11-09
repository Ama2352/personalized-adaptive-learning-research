# Full cached CPU09 — lượt02 dừng trước terminal replay

Ngày 09/11/2026. Verdict giữ nguyên `REJECTED_KEEP_NEW_FULL_OPERATION_NO_RETRY`. Shim `.venv` trả3221225786 (`0xC000013A`); chưa lưu exit code trực tiếp của actual worker. Không có reservation, parity hoặc truth output. Lượt này chưa cung cấp kết quả mastery mới.

## Allocation và bằng chứng thực có

D41 cho phép một workload GAM mới với whole300/worker270/owned285giây, cleanup reserve5giây, family RSS512MiB và RAM khả dụng1536MiB. Nguồn policy/evaluator, query/P parity và điều kiện freeze trước truth giữ nguyên. Trần dự kiến120policies/14.400events chưa phải số đã thực hiện. D41 không thay allocation AKT checkpoint04 hoặc cấp quyền GPU, fullCV/Holdout. Nguồn quyết định là `docs/thesis_recovery/09_DECISION_REGISTER.md`, mục D41; archive tham chiếu phiên bản tài liệu bằng SHA, không copy toàn sổ quyết định.

| Phần | Quan sát được |
|---|---|
| Terminal outer | Bị từ chối, thời gian trước receipt3.1149093999993056giây trên whole300 |
| Owned helper | GO đã phát, actual worker đã thuộc Job trước GO; helper elapsed2.7761847972869873giây |
| Return code |3221225786 của Popen `.venv` shim PID45776; actual worker PID14104 chưa có direct exit-code receipt |
| Cleanup | Job active trước cleanup0/sau cleanup0, handles đóng, cleanup accepted; không tự retry |
| Resource monitor | Peak family quan sát126898176B, minimum available2556096512B, errors rỗng, terminated_owned_job=False |
| Hai file worker | `pure_checks.json` có5 manufactured helper checks; `native_metadata.json` đóng pha sạch,1 literal Windows `cmd /c ver`,0 blocked attempts |
| Phần còn thiếu | Không reservation, result/failure terminal của worker, pretruth readouts, parity, policy observers, truth sidecar hoặc groups |

Năm helper checks không phải tổng call counts của worker. Constructors/updates giữ `UNKNOWN_WITHOUT_TERMINAL_NATIVE_RECEIPT` như kiểm hậu kỳ của Root. Không gán120policies,14.400updates hoặc0updates thành kết quả thực đo của lượt02. Monitor là lấy mẫu, chưa chứng minh mọi sự kiện bộ nhớ hoặc nguồn phát sinh termination.

## Phân loại mã và giới hạn chẩn đoán

Microsoft đặt tên mã `0xC000013A` là `STATUS_CONTROL_C_EXIT`. Việc nhận diện mã không xác định ai hoặc thành phần nào đã phát sinh sự kiện trong lượt này. Root không ghi nhận thao tác dừng/Ctrl+C của user. Không gán nguyên nhân cho user, conhost, metadata, NumPy/Pandas hoặc hạ tầng từ tên mã. [Microsoft NTSTATUS](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)

Source helper `windows_owned_worker.py` dòng400 lấy `process.returncode`, tức shim Popen. Cleanup ở412 gọi TerminateJobObject với code1 sau khi đã lưu trạng thái trước cleanup. Resource monitor cũng dùng code1 nếu chính nó terminate Job, nhưng receipt lần này ghi terminated=False/errors rỗng. Vì vậy hai nhánh cleanup/resource được ghi nhận không chứng minh nguồn của mã trước cleanup.

`native_metadata.json` chứng minh helper metadata đã hoàn tất. Accepted pilot03 dùng cùng helper, cùng literal command và cũng có conhost trong startup tree. Chỉ sự hiện diện conhost hoặc metadata không đủ để kết luận nguyên nhân.

Khoảng chưa định vị nằm sau write/readback metadata tại worker198 và trước reservation292, gồm thiết lập allowlist/audit, NumPy/Pandas imports và kiểm cache/source. Không có durable phase markers để tách các bước đó. Source đặt factories sau reservation nhưng thiếu native terminal counts, nên vẫn giữ accounting UNKNOWN theo postcheck. Chưa có bằng chứng normal Python exception đã được ghi vào failure receipt.

## Source integrity sau khi dừng

Root đã chạy riêng `verify_cpu09_full02_terminal01.py`, xác nhận57 source/input identities cùng hai file worker còn lại. Postcheck SHA là `3a603fb78477388b779cd9f4af1b5b57d8fd1aeefd25f06b580577adef05b8f2`, outer final SHA `9327a58214dab1574516a539d422d9337db85e4bfd06ada8d4f72f2f63360ebe`.

Đây là hậu kiểm source/file sau termination, không phải native admission hoặc scientific acceptance. Raw outer `source_input_after={}` và `outputs={}` được giữ nguyên vì fail-fast tại kiểm owned terminal; không backfill raw receipt. Archive giữ11 file raw, ba frozen source/contract, Root review và hai file hậu kiểm.57 inputs chỉ được tham chiếu hash, không nhân đôi cache hoặc parse lại nội dung gzip.

## Nếu Root duyệt một giả thuyết chẩn đoán mới

Có thể thêm một phase JSONL rất nhỏ, fsync trước/sau NumPy, Pandas và cache validation; cùng đọc exit code qua các owned handles đã xác minh trước cleanup, phân biệt shim/actual worker/conhost. Đó chỉ là đề xuất source instrumentation để review tiếp. Không thêm global profiler, thay console flags/signal handler, nới guards hoặc tự chạy lại trong hồ sơ này.

Lưu evidence hoàn tất chỉ chứng nhận bảo toàn failure. Không có native mastery result mới, independentN mới, CI, causal learning-benefit hoặc model fit trong lượt02 hoặc closure.
