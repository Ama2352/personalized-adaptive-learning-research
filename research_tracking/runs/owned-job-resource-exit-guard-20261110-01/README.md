# Guard tài nguyên owned Job · bằng chứng vận hành

Bundle giữ một failure A1 trước model output, hai probe Git read-only và chín canary WinAPI chế tạo. Không chạy lại model, probe, tests hoặc Git khi đóng gói. Các request/worker GKT và request A1 tương lai không được lấy vào bundle. Source guard03 là bản private đã freeze, chưa sửa canonical Kernel.token và không tự cấp quyền native retry.

## Phân biệt ba quan sát

Lượt A1 failure01 dừng bởi PermissionError WinError5 trong bộ đo RAM. Outer rejected, worker exit125, owned cleanup đạt và Job0. Resource-failure không có traceback xác định API hoặc PID gây lỗi. Native output directory của chính allocation01 không tồn tại trước/sau archive, config/source được ghim để kiểm ranh giới. Reservation40updates là trần, không được đọc thành actual updates. Lượt này không tạo NN model output theo control-flow của source, nhưng các probe sau chưa chứng minh nguyên nhân WinError5.

Resource probe02 có bốn Git children thật, từng handle đã signaled Wait0/exit0, creation-only identity trước/sau khớp. Raw hiện ghi cả4/4 lời gọi old Kernel.token sau exit gặp WinError31 tại QueryFullProcessImageNameW. Cờ old_WinError5_reproduced=False KHÔNG có nghĩa mọi old token đều chạy được. Giữ nguyên raw lỗi31 và không gọi nó là lỗi5 ban đầu.

Membership probe Root01 cũng có4/4 old token WinError31 sau Wait0; IsProcessInJob trả True ở cả4 handle đã exit. Đây là quan sát hữu hạn, không khẳng định IsProcessInJob luôn thành công sau mọi exit. Cả hai probe accepted theo outer, Job0 và handle cleanup đạt. Thời gian outer lưu nằm trong observed-facts.json, tách khỏi quan sát terminal của Root nếu có.

## Guard và giới hạn

Guard RAM dùng query-limited cùng synchronize trên exact handle. Chỉ WaitForSingleObject trả WAIT_OBJECT_0 mới nhận trạng thái đã kết thúc. Live/unknown/WAIT_FAILED và PID/creation mismatch vẫn bị từ chối. PermissionError chỉ được ghi nhận như race kết thúc nếu chính handle đó đã được xác nhận signaled. Đóng góp RSS hiện tại bằng0 của member đã exit không phải historical peak0. RAM là telemetry lấy mẫu, không hard OS quota hoặc bằng chứng không thể có peak giữa samples.

Chín canary thực tế đạt0FES trong0,3629403giây/cap5, không heavy imports. Giữ failure controller01 trước dispatch vì sai tên file pin, controller02 và logs đã chạy. Probe01 chỉ là source review bị yêu cầu sửa cleanup trước dispatch, không một lượt actual probe thất bại. Source01/packet/outer được giữ riêng. Probe02 đã bổ sung perchild cleanup tiếp tục khi lỗi, receipt giữ primary/cleanup riêng và timer dừng.

Tài liệu API Microsoft đã đối chiếu cho quyền handle và trạng thái wait. Đây là mô tả API, không thay actual owned probe.

- [WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).
- [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes).

Nguồn/sourcepins nhỏ được copy với inventory trước/copy/sau và manifest readback. Canonical helper cùng các bundle nền chỉ tham chiếu SHA, không nhân đôi runtime/dependency/corpus/model. Manifest completed xác nhận archive vận hành, không nghiệm thu Main fitted model, CUDA, matrix hoặc RQ.
