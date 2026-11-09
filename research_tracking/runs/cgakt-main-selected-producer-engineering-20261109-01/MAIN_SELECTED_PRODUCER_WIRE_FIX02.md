# Revision02: chỉ sửa expected JSON trong test

ROOT đã chạy attempt01: raw JUnit/worker-result ghi16tests,15PASS/1FAIL/0errors/0skip; pytest1.21s. Terminal ROOT báo5.236512999981642s/60. Outer `counts=null` vì từ chối returncode1 trước khi đọc worker counts; **không phải0test hoặc0case đã chạy**. Job cleanup accepted/active0, raw source/runtime before=after, denied/scientific imports đều rỗng. Không NN/corpus/actual authorization/Gate.

Failure duy nhất tại assertion `got==value`: `auth_value` chứa `asdict(MainGitProfile).upstream_files_sha256` là tuple-of-tuples, còn auth đọc từ file JSON là list-of-lists. Các caps khác là scalar/object, không có tuple field khác; log xác nhận chỉ `caps` khác,10top-level fields giống. Không có output chứng minh assertion `matched==identity` cũ đã chạy vì short-circuit; revision02 kiểm tra nó độc lập.

Test mới đọc đúng auth fixture bytes trở lại thành wire object rồi so **toàn bộ** `got==wire==canonical(value)`, exact full caps và identity. Giữ negative caps drift và mọi exact schema/field check. Không thay production guard902018… hoặc runnerfcaa0c…, không nới quyền, không actual grant từ mocks.

Trước sửa đã snapshot9smallinputs (bốn source/test, controller01, packet01, old inventory/handoff và manufactured auth fixture); `pre-main-selected-wire-fix02/inventory-before.json` cùng `copy-verification.json` ghi pre/copy/postSHA và immutable raw01 pointers. Không sửa/move raw01/TMP01 hay giả raw log mới.

Controller02 chỉ thay exclusive namespace/packet/TMP (`msr02`) và ghi prior charged5.236512999981642s trong final receipt; cùng16cases/whole60/worker50/cleanup3/finalization2/RSS1GiB/free2GiB và guard semantics. Maximum cộng hai allocation65.23651299998164s, không xoá chi phí01. Chưa execute/import/test revision02; ROOT review/dispatch riêng.

Đây là test wire-representation correction, không config/hyperparameter/methodology hoặc production auth change.16fixtures nếu đạt vẫn chỉ là software orchestration, không actual main fit/required9/Gate acceptance.
