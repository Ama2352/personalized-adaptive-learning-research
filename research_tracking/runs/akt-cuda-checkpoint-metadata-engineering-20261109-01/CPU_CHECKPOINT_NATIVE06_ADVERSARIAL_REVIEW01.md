# Rà soát nguồn đối kháng checkpoint native06

Ngày09/11/2026. Chỉ đọc source/packet/fixtures, không import, chạy test/native/Git hoặc đổi file đã freeze. Phạm vi gồm worker06 `54723442f8a2a67c91c94d42003f5a7967f84936a3f961db9845c306d06e1f55`, outer06 `5867c91c24902a76ef0d63030be0a8b6eb44168a103d49359ef3b122a3b1a97f`, packet06 `afb3ad71b6e633662ee9b0b33d41fd4a1b2f0cdf23f391d4f7877a273a74789d` và native test `332c48af10eb983433117fe994a92fccf628866e04fb24f83390a5e6ce11045e`.

## Verdict nguồn

Không tìm thấy blocker xác định làm false-accept resource failure, zero-sample run, PID reuse hoặc partial native ledger trong phạm vi nguồn đã rà. Controller có thể từ chối bảo thủ khi process chết giữa các WinAPI queries hoặc monitor không dừng kịp. Phần query family WinAPI mới chưa được chạy; đây là static scoped review, chưa là nghiệm thu native06. RAM admission4GiB vẫn là điều kiện bắt buộc trước launch. ROOT thông báo M03 đã đạt38metadata riêng, native06 chưa dispatch.

## Monitor và process identity

- Worker lines213–262 mở query handle của đúng Job từ `worker_gate`, kiểm current process thuộc Job rồi lấy PID list class3 trong buffer tối đa16. Query API failure/overflow hoặc `listed != assigned`, số0, số vượt16, duplicate PID hay thiếu actual worker đều gây rejection. Buffer có header hai DWORD và mảng uintptr tương ứng ctypes trên Windows.
- Mỗi OpenProcess dùng query-limited rights, không quyền terminate. Nếu PID được tái sử dụng ngoài Job thì `IsProcessInJob` từ chối; native token và psutil creation time còn được đối chiếu trước memory read. `finally` đóng handle kể cả khi membership/identity fail. Monitor không đăng ký PID đó vào leases hoặc tự kill PID. Cleanup vẫn do helper0dc với owned handles ban đầu.
- OpenProcess thất bại chỉ được bỏ qua nếu `pid_exists` lúc kiểm làFalse. `psutil.NoSuchProcess` trong sample cũng được ghi `exited_during_sample`. AccessDenied, WinAPI lỗi khác, token mismatch hoặc membership lạ không được nuốt. Một process thoát giữa QueryFullProcessImageName/GetProcessTimes và psutil có thể làm cả lượt reject, đây là rủi ro vận hành chưa đo. Không đề xuất nới exception khi chưa có receipt lỗi cụ thể.
- Snapshot sum chỉ gồm các process còn đo được trong named Job. Conhost/shim/cmd/Git nếu còn sống và trong Job được tính; process thoát trước sample không có RSS tại sample đó. Outer ROOT process đứng ngoài Job. Tổng sampled RSS có thể đếm shared pages nhiều lần, chưa là unique physical memory hoặc hard memory quota. Peak worker `peak_wset` được giữ riêng để phát hiện peak worker giữa hooks.

## Zero samples và thread lỗi

`memory()` chạy đồng bộ tại line262 trước metadata/Torch imports, và chạy lại sau fixture/native proof tại line433. Nếu initial call lỗi trước increment hoặc trước guard, `original_error` được ghi và acceptance đòiNone nên không thể đạt. Nếu thành công, samples đã tăng, minimum available có giá trị và maximum Job process count ít nhất1. Outer lines112–115 yêu cầu process count≥1 và so actual minimum available≥2GiB; None sẽ bị từ chối. Chưa có đường nguồn hợp lệ cho zero-sample acceptance, dù outer không có assertion riêng `samples>0`.

Monitor thread lấy mẫu khoảng0,1s. Exception bất kỳ tại sample được thêm vào `monitor_errors`, cố ghi `resource-failure.json`, rồi `os._exit(125)` trongfinally. Ngay cả ghi failure file lỗi, child vẫn exit125; outer không thể chấp nhận RC đó. Đây có thể làm inner final không tồn tại, nhưng helper/outer giữ raw receipt và không suy0native calls khi không có final.

Khi kết thúc, worker stop/join0,5s. Nếu thread còn sống thì query handle không bị đóng khi thread đang dùng; `job_query_handle_closed` giữFalse và `monitor_stopped` False, khiến verdict reject. Khi dừng được thì close Job query handle có kiểm lỗi; worker và outer cùng đòi closedTrue. Query handle không kill-on-close riêng; helper tiếp tục kiểm actual Job0/Popen handle closed. Mẫu không liên tục và rejection sau allocation chưa ngăn được mọi transient pressure trước sample, đã được ghi rõ trong profile.

## Ledger thật và nghiệm thu

Test source lines178–347 tạo một shared module fixture. Năm singleton cases đầu, tám malformed-state parameters, một zero-gradient case và hai absent/empty parameters tạo đúng16IDs. Plugin worker lines416–425 kiểm actual mapped16IDs trước fixture bodies và counters phải0 lúc collection hoàn tất. Outer kiểm lại actual JUnit16unique/0FES và exact counters started=body-returned=packet caps.

| Công việc | Actual workload được nguồn yêu cầu |
|---|---|
|Constructors|2adapters/backbones/wrappers/gates,2Adam|
|Training|Complete E1 gồm2batches×24targets, rồi một24target control continuation và một24target restored continuation. Tổng4backward/4clip/4Adam bodies/96optimized target exposures.|
|Inference|2parity forwards×24target slots,48slots ngoài training.|
|Forwards tổng|6Architecture forwards. Không gọi4updates là4epoch.|
|Serialization|7saves,8CPU weights_only loads,1successful model restore và1successful Adam restore.|
|Negatives|Sáu authenticated malformed checkpoint payloads phải reject trước mutators; tám optimizer-state cases và hai absent/empty cases kiểm in-memory state. Không thêm optimizer updates.|

Target observations phải gồm đúng bốn `{reserved=24,returned=24}`. E1 proof phải48targets/8windows/2batches/2steps, continuation control/restored cùng cumulative3bodies và explicit không completeE2. Native state/Adam SHA parity cùng trực tiếp ba RNG và toàn bộ modes phải đạt. Không có yêu cầu mọi tensor tham gia mọi step; participation/None/zeroTensor semantics giữ như source checkpoint.

## Runtime, thời gian và nguồn

Outer yêu cầu current M03 accepted outer với external ROOT SHA và exact reviewed packet03 SHA; đây là prerequisite metadata. Sau đó kiểm current MainC15 nguồn tám files, actual4GiB admission, rồi mới `run_owned`. Source76bindings/runtime12 trong packet06 được kiểm trước/sau. Đây là selected source/runtime anchors, chưa phải toàn bộ installed-site byte attestation hoặc fresh Gate.

Native observers vẫn gọi genuine upstream loader hai rounds, mỗi round10fixed read-only Git commands. Process-scoped fsmonitorFalse/exact safe.directory/autocrlfTrue cùng thread/CUDA-hidden/TEMP variables được khôi phục ở worker. Method observer57a kiểm final baselines, gồm inheritance restoration đã sửa trước đây. Test fixture không monkeypatch psutil hoặc clock API; nó thay mutator instances trong negative restore và default dtype cófinally. Worker cũng kiểm/khôi phục dtype và thread count độc lập.

Whole120/owned116/cleanup3/outer reserve4, worker110 và native-work100 là các tầng cùng một operation. Worker timer dùng remaining110 từ start; native counter wrappers kiểm100 trước/sau mỗi body. Budget trong `train_epoch` vẫn60. Late inner/outer postwrite có rejection sidecar vàRC1. Chưa có runtime forecast rằng mọi checks sẽ xong trong reserve. ROOT phải yêu cầu terminalRC0 và không có postwrite rejection, không dựa riêng status string đã ghi trước deadline check.

M03 actual38metadata receipt do ROOT thông báo SHA `0ca581457e7b0268f295ab363c30926f4c02e01b20ea0d759ef92b012cbe96d6`. Receipt này không thay native06 execution. Native CPU same-process checkpoint roundtrip, fresh-OS-process proof, full producer resume, current software Gate, CUDA và paid training là các scope riêng.
