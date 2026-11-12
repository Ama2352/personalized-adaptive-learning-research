# Watchdog local cho App Modal đã được cấp ngân sách

## Phạm vi đã hoàn thành

Gói ngày12/11/2026 bổ sung helper thuần standard library tại `experiments/akt/modal_budget_guard.py` và23ca kiểm tại `tests/akt/test_modal_budget_guard.py`. Không gọi API cloud, tạo App, cấp GPU hoặc chi credits trong gói kiểm này.

Guard dùng deadline monotonic tính từ trước `app.run`, bao gồm thời gian startup và thực thi. Thread riêng gửi lệnh dừng khi hết thời gian, kể cả main thread đang chờ kết quả hoặc khởi động App. Khi context hoàn tất hay ném lỗi, guard luôn yêu cầu dừng App đã ràng buộc. Tên App phải đúng `kltn-akt-<run-id>`, ID phải đúng định dạng Modal. Provider pending chỉ lấy ID từ chính object App của lượt đang tạo, rồi ghim ID cụ thể trước callback dừng.

Lệnh dừng mặc định là subprocess riêng chạy bằng Python của controller, với argv cố định và timeout15giây. Callback không xác nhận được, thiếu serverID hoặc hết thời gian chờ xác nhận dẫn tới `ModalStopUnconfirmed`. Log giữ lỗi và lượt kế tiếp phải kiểm trạng thái trước khi cấp thêm tài nguyên. Hỏng nơi lưu diagnostics vẫn kích hoạt callback dừng. File diagnostics có sẵn được giữ nguyên và guard ghi hồ sơ lỗi vào file mới.

## Kết quả kiểm

- `tests01.log/xml` ghi20ca đạt.
- `tests02.log/xml` ghi21ca đạt, bổ sung giữ diagnostics cũ và fresh-process import.
- `tests03.log/xml` ghi23ca đạt, gồm watchdog dừng trong lúc App context đang startup và thiếu ID được ghi là chưa xác nhận.
- Fresh import không nạp Torch. Tests dùng callback giả, có kiểm thành công, exception, deadline, stop lỗi, stop treo, lỗi ghi log và subprocess timeout. Không suy hiệu lực server từ callback giả.

## Cách nối vào controller

Tạo deadline trước context cloud. Guard phải bọc ngoài `app.run` để chặn cả startup. `app.name` và `app.app_id` lấy từ object App vừa tạo cho đúng run.

```python
deadline = ModalRunDeadline(800)
binding = PendingOwnedModalApp(RUN, app.name, lambda: app.app_id)
with ModalAppBudgetGuard(
    binding,
    deadline,
    stop_app=stop_owned_app_cli,
    diagnostic_path=native / 'app-budget-guard.json',
) as guard:
    with modal.enable_output(), app.run(environment_name='main'):
        guard.remaining()
        call = function.spawn(inputs)
        receipt = call.get(timeout=guard.remaining())
        # Ghi receipt trước khi thoát để giữ kết quả worker đã trả về.
# App stop đã được acknowledgement. Kiểm trạng thái server rồi tải artifact.
```

Controller vẫn phải kiểm allocation người dùng, giá tài nguyên, số GPU/container, thời gian runtime và dự phòng chi phí. Dự toán cần cộng thời gian gửi/dợi lệnh dừng15–20giây vào envelope của job. Deadline local chỉ bắt đầu yêu cầu dừng ở mốc đã chốt. Máy ngủ/tắt hoặc mất mạng làm guard local không bảo đảm remote đã dừng. Cần kiểm App state sau acknowledgement trước lượt trả phí mới. Helper không cấp quyền hoặc tự thay số credits.

## Nguồn API

Modal xác định `App.stop()` dừng containers/sandboxes và chặn input mới. `FunctionCall.cancel(terminate_containers=True)` hủy input cùng container, còn timeout của `get()` giới hạn thời gian chờ phía client. Helper dùng lệnh dừng đúng App để bao phủ startup crashloop. [Modal App](https://modal.com/docs/sdk/py/latest/App), [Modal FunctionCall](https://modal.com/docs/sdk/py/latest/FunctionCall)

SDK local đã được inspect tại `sdk-api-inspection.json`. Source packager cần đưa chính xác file helper vào bundle trước Gate Linux mới, vì tests hiện đọc file dưới `experiments/akt/`.

## Đã nối ba entrypoint trả phí

Đã tích hợp vào `modal_junyi_engineering.py`, `modal_graph_selected.py` và `modal_a0_gpu_pilot.py`. Guard bọc ngoài `app.run`, deadline tạo trước định nghĩa/provision image/App/Volume, `call.get` lấy thời gian còn lại. Junyi và Main60 dùng800giây, pilot A0 nhỏ dùng380giây. Cộng20giây chờ acknowledgement vẫn nằm trong timeout840/420giây cũ. Helper import nằm trong local entrypoint để worker remote không cần import dependency điều phối.

`controller-before.json` và ba snapshot `*_before_guard.py` giữ nguồn trước thay đổi. `controller-integration.json` ghim nguồn sau thay đổi và kết quả kiểm AST. Scientific workers, cấu hình GPU/CPU/RAM, allocation và đường dẫn artifact được đối chiếu AST và giữ nguyên. Resolver ROOT của graph controller dùng chuỗi `.parent` an toàn khi module nằm ở đường dẫn nông, cùng giá trị ở repository.

`verify_entrypoints.py` kiểm guard nesting, timeout và các worker/cloud calls. `controller-verification02.log` cùng `standalone-import.log` xác nhận cả ba module import được ở vị trí `/root/<module>.py`, không nạp helper hoặc Torch. Lượt kiểm AST đầu dùng bộ lọc `get` quá rộng nên bắt cả dictionary lookup, đã sửa bộ lọc chính xác `call.get`; log đầu giữ tại `controller-verification.log`.

Chưa dispatch để kiểm dừng App thực trên Modal. Trước run kế tiếp, nhánh chính cần nghiệm thu Gate đúng source và kiểm allocation đã cấp. Tests callback giả chỉ chứng minh cơ chế local và đường điều khiển.

Bundle mở để nhánh chính nghiệm thu.

## Xử lý idempotent khi App đã kết thúc

Lượt Gate CPU thực do nhánh chính chạy đã phát hiện CLI `app stop` trả code1 với thông báo App đã dừng. Callback hiện kiểm trạng thái độc lập bằng `app list --json` sau lỗi CLI. Chỉ một bản ghi đúng App ID, state `stopped` và tasks0 mới xác nhận thành công. App đang chạy, thiếu ID, còn task hoặc lỗi truy vấn tiếp tục báo chưa xác nhận.

Hai subprocess dùng chung deadline monotonic15giây. `tests04.log/xml` ghi28ca đạt. Ca thời gian giả lập dùng6giây cho lệnh dừng rồi xác nhận timeout còn9giây cho truy vấn. Tests giả giữ nguyên log trước, không gọi cloud trong gói sửa này.


## Nghiệm thu nhánh chính

Bundle đóng sau rà soát nhánh chính. Kiểm CUDA thực và nguồn Linux hiện hành được theo dõi tiếp ở `research_tracking/runs/junyi-gpu-optimization-20261112-01/`. Kết quả ở đây là bằng chứng engineering theo phạm vi từng phép kiểm.
